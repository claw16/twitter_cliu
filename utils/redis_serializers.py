from django.core import serializers
from utils.json_encoder import JSONEncoder


class DjangoModelSerializer:
    @classmethod
    def serialize(cls, instance):
        # by default, Django's serializers need a list or a queryset,
        # i.e. we need to put the instance into a list
        return serializers.serialize('json', [instance], cls=JSONEncoder)

    @classmethod
    def deserialize(cls, serialized_data):
        # 需要加 .object 来得到原始的 model 类型的 object 数据，要不然得到的数据并不是一个
        # ORM 的 object，而是一个 DeserializedObject 的类型
        return list(serializers.deserialize('json', serialized_data))[0].object
