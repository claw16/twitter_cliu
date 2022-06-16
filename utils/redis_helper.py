from django.conf import settings
from utils.redis_client import RedisClient
from utils.redis_serializers import DjangoModelSerializer


# TODO: _load_objects_to_cache & push_objet, kind of duplicate?
class RedisHelper:
    @classmethod
    def _load_objects_to_cache(cls, key, objects):
        conn = RedisClient.get_connection()

        serialized_list = []
        # 最多只 cache REDIS_LIST_LENGTH_LIMIT 个 objects，超过的 objects 去 DB 取
        for obj in objects[:settings.REDIS_LIST_LENGTH_LIMIT]:
            serialized_data = DjangoModelSerializer.serialize(obj)
            serialized_list.append(serialized_data)

        if serialized_list:
            # *[1, 2, 3] -> 1, 2, 3, * 的作用就相当于是去除方括号[]
            conn.rpush(key, *serialized_list)
            # refresh expire time on each data update
            conn.expire(key, settings.REDIS_KEY_EXPIRE_TIME)

    @classmethod
    def load_objects(cls, key, queryset):
        conn = RedisClient.get_connection()

        # if key exists in cache, get and return - cache hit
        if conn.exists(key):
            serialized_list = conn.lrange(key, 0, -1)
            objects = []
            for serialized_data in serialized_list:
                deserialized_obj = DjangoModelSerializer.deserialize(serialized_data)
                objects.append(deserialized_obj)
            return objects

        # if key doesn't exist, push to cache and return list of obj from queryset - cache miss
        cls._load_objects_to_cache(key, queryset)
        # 转换为 list 的原因是保持返回类型的统一，因为存在 Redis 里的数据是 list 形式
        return list(queryset)

    @classmethod
    def push_object(cls, key, obj, queryset):
        conn = RedisClient.get_connection()
        # 如果不加这个 if 判断，假如说 key 不存在是因为 expired，直接 lpush 的话
        # 这个用户之前的帖子就没有存进 cache，就产生了数据丢失
        if not conn.exists(key):
            # 如果key不存在，直接从数据库里取，不走单个push的方法存入cache
            # 某用户的发帖 (key = user_tweets:{user_id}) 如果不在 Redis 里面
            # 可能是没存过，也可能是到期了，那就需要把这些帖子从数据库取出来(queryset)
            # 然后存入Redis
            cls._load_objects_to_cache(key, queryset)
            return
        # 如果 key 存在，那就把这次新发的帖子存入 key 对应的 list 的最左边
        serialized_data = DjangoModelSerializer.serialize(obj)
        conn.lpush(key, serialized_data)
        conn.ltrim(key, 0, settings.REDIS_LIST_LENGTH_LIMIT - 1)

    @classmethod
    def get_count_key(cls, obj, attr):
        # attr -> an attr name of a model, e.g. Tweet model's 'likes_count'
        return '{}.{}:{}'.format(obj.__class__.__name__, attr, obj.id)

    @classmethod
    def incr_count(cls, obj, attr):
        conn = RedisClient.get_connection()
        key = cls.get_count_key(obj, attr)
        # cache miss - back-fill cache from db
        # 这里不执行 +1 操作，因为在调用 incr_count() 之前已经完成了 +1
        if not conn.exists(key):
            obj.refresh_from_db()
            conn.set(key, getattr(obj, attr))
            conn.expire(key, settings.REDIS_KEY_EXPIRE_TIME)
            return getattr(obj, attr)
        # cache hit - return the value (after increment)
        return conn.incr(key)

    @classmethod
    def decr_count(cls, obj, attr):
        conn = RedisClient.get_connection()
        key = cls.get_count_key(obj, attr)
        # cache miss
        if not conn.exists(key):
            obj.refresh_from_db()
            conn.set(key, getattr(obj, attr))
            conn.expire(key, settings.REDIS_KEY_EXPIRE_TIME)
            return getattr(obj, attr)
        # cache hit
        return conn.decr(key)

    @classmethod
    def get_count(cls, obj, attr):
        conn = RedisClient.get_connection()
        key = cls.get_count_key(obj, attr)
        count = conn.get(key)
        # cache hit
        if count is not None:
            return int(count)  # TODO: why int?
        # cache miss
        obj.refresh_from_db()
        count = getattr(obj, attr)
        conn.set(key, count)
        return count
