from django.conf import settings
from django.core.cache import caches
from django.db import models

cache = caches['testing'] if getattr(settings, 'TESTING', False) else caches['default']


class MemcachedHelper:
    @classmethod
    def get_key(cls, model_class: models.Model, object_id):
        return f'{model_class.__name__}:{object_id}'

    @classmethod
    def get_object_through_cache(cls, model_class: models.Model, object_id):
        key = cls.get_key(model_class, object_id)
        # cache hit
        obj = cache.get(key)
        if obj is not None:
            return obj

        # cache miss, search db
        obj = model_class.objects.get(id=object_id)
        # using default expire time
        cache.set(key, obj)
        return obj

    @classmethod
    def invalidate_cached_object(cls, model_class: models.Model, object_id):
        key = cls.get_key(model_class, object_id)
        cache.delete(key)
