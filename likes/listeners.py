from utils.redis_helper import RedisHelper


def incr_likes_count(sender, instance, created, **kwargs):
    from django.db.models import F

    if not created:
        return

    # Method 1:
    model_class = instance.content_type.model_class()  # Tweet or Comment class
    # SQL -> UPDATE likes_count = likes_count + 1 FROM table_name WHERE id=object_id;
    # 这句话会触发 MySQL 的行锁，保证数据的原子性
    model_class.objects.filter(id=instance.object_id).update(likes_count=F('likes_count') + 1)
    RedisHelper.incr_count(instance.content_object, 'likes_count')

    # Method 2:
    # model_object = instance.content_object
    # model_object.likes_count = F('likes_count') + 1
    # model_object.save()


def decr_likes_count(sender, instance, **kwargs):
    from django.db.models import F

    model_class = instance.content_type.model_class()
    model_class.objects.filter(id=instance.object_id).update(likes_count=F('likes_count') - 1)
    RedisHelper.decr_count(instance.content_object, 'likes_count')
