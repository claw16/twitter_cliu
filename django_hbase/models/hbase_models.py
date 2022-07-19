from django.conf import settings
from django_hbase.models import HBaseField, IntegerField, TimestampField
from django_hbase.client import HBaseClient


class BadRowKeyError(Exception):
    pass


class EmptyColumnError(Exception):
    pass


class HBaseModel:

    class Meta:
        table_name = None
        row_key = ()

    @classmethod
    def create(cls, **kwargs):
        instance = cls(**kwargs)
        instance.save()
        return instance

    @classmethod
    def serialize_row_data(cls, data):
        row_data = {}
        field_hash = cls.get_field_hash()
        for key, field in field_hash.items():
            if not field.column_family:
                continue
            column_key = f'{field.column_family}:{key}'
            column_value = data.get(key)
            if column_value is None:
                continue
            row_data[column_key] = cls.serialize_field(field, column_value)
        return row_data

    def save(self):
        row_data = self.serialize_row_data(self.__dict__)
        # 如果 row_data 为空，即没有任何 column key values 需要存储 hbase 会直接不存
        # 这个 row_key， 因此我们可以 raise 一个 exception 提醒调用者，避免储存空值
        if len(row_data) == 0:
            raise EmptyColumnError()
        table = self.get_table()
        table.put(self.row_key, row_data)

    @classmethod
    def serialize_field(cls, field, value):
        value = str(value)
        if isinstance(field, IntegerField):
            # 因为排序规则是按照字典序排序，那么就可能出现 1 10 2 这样的排序
            # 解决办法：固定 int 的位数为 16 位 （8的倍数更容易利用空间），不足为补0
            # value = str(value)
            # while len(value) < 16:
            #     value = '0' + value
            value = value.zfill(16)
        if field.reverse:
            value = value[::-1]
        return value

    @classmethod
    def deserialize_field(cls, key, value):
        field = cls.get_field_hash()[key]
        if field.reverse:
            value = value[::-1]
        if field.field_type in [IntegerField.field_type, TimestampField.field_type]:
            return int(value)
        return value

    @classmethod
    def serialize_row_key(cls, data):
        """
        serialize dict to bytes (not str)
        {key1: val1} -> b"val1"
        {key1: val1, key2:val2} -> b"val1:val2"
        {key1: val1, key2:val2, key3:val3} -> b"val1:val2:val3"
        Note: ORDER MATTERS!
        """
        field_hash = cls.get_field_hash()  # get all HBaseField fields from the model
        values = []
        for key, field in field_hash.items():
            if field.column_family:  # ignore column keys
                continue
            value = data.get(key)
            if value is None:
                raise BadRowKeyError(f"{key} is missing in row key")
            value = cls.serialize_field(field, value)
            if ':' in value:
                raise BadRowKeyError(f"{key} should not contain ':' in value: {value}")
            values.append(value)
        return bytes(':'.join(values), encoding='utf-8')

    @classmethod
    def deserialize_row_key(cls, row_key):
        """
        "val1" -> {'key1': val1, 'key2': None, 'key3': None}
        "val1:val2" -> {'key1': val1, 'key2': val2, 'key3': None}
        "val1:val2:val3" -> {'key1': val1, 'key2': val2, 'key3': val3}
        """
        data = {}
        if isinstance(row_key, bytes):
            row_key = row_key.decode('utf-8')

        # val1:val2 -> val1:val2: - 方便每次 find(':')都能找到一个val
        row_key += ':'
        for key in cls.Meta.row_key:
            index = row_key.find(':')
            if index == -1:
                break
            data[key] = cls.deserialize_field(key, row_key[:index])
            row_key = row_key[index + 1:]

        # TODO: row_key.split(':') ?
        # for key, rk in zip(cls.Meta.row_key, row_key.split(':')):
        #     data[key] = cls.deserialize_field(key, rk)
        return data

    @classmethod
    def init_from_row(cls, row_key, row_data):
        if not row_data:
            return None
        data = cls.deserialize_row_key(row_key)
        for column_key, column_value in row_data.items():
            # remove column family
            column_key = column_key.decode('utf-8')
            key = column_key[column_key.find(':') + 1:]
            data[key] = cls.deserialize_field(key, column_value)
        return cls(**data)

    @classmethod
    def get_table_name(cls):
        if not cls.Meta.table_name:
            raise NotImplementedError('Missing table_name in HBaseModel meta class.')
        if settings.TESTING:
            return f'test_{cls.Meta.table_name}'
        return cls.Meta.table_name

    @classmethod
    def get_table(cls):
        conn = HBaseClient.get_connection()
        return conn.table(cls.get_table_name())

    @classmethod
    def drop_table(cls):
        if not settings.TESTING:
            raise Exception('You can only drop tables in unit tests.')
        conn = HBaseClient.get_connection()
        # delete_table() will drop a table if exists, otherwise do nothing
        conn.delete_table(cls.get_table_name(), True)

    @classmethod
    def create_table(cls):
        if not settings.TESTING:
            raise Exception('You can only create tables in unit tests.')
        conn = HBaseClient.get_connection()
        # conn.tables() returns a list of table names in bytes format,
        # e.g. [b'test_tweets'], however our table name is str 'test_tweets',
        # consequently if we don't decode the bytes, 'test_tweets' in [b'test_tweets']
        # will return False.
        tables = [table.decode('utf-8') for table in conn.tables()]
        if cls.get_table_name() in tables:  # if the table exists, we don't duplicate it
            return
        column_families = {
            field.column_family: dict()
            for key, field in cls.get_field_hash().items()
            if field.column_family is not None
        }
        conn.create_table(cls.get_table_name(), column_families)

    @property
    def row_key(self):
        return self.serialize_row_key(self.__dict__)

    @classmethod
    def get_field_hash(cls):
        """
        Traverse an HBaseModel's attributes, get all the HBaseField ones.
        Example - HBaseFollower:
            field_bash = {
                'to_user_id': models.IntegerField(reverse=True),
                'created_at': models.TimestampField()
                'from_user_id': models.IntegerField(column_family='cf')
            }
        """
        field_hash = {}
        for field in cls.__dict__:
            field_obj = getattr(cls, field)
            if isinstance(field_obj, HBaseField):
                field_hash[field] = field_obj
        return field_hash

    def __init__(self, **kwargs):
        for key, field in self.get_field_hash().items():
            value = kwargs.get(key)
            setattr(self, key, value)

    @classmethod
    def get(cls, **kwargs):
        row_key = cls.serialize_row_key(kwargs)
        table = cls.get_table()
        row = table.row(row_key)
        return cls.init_from_row(row_key, row)
