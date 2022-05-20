from django.conf import settings
from django.core.cache import caches
from friendships.models import Friendship
from twitter.cache import FOLLOWINGS_PATTERN

# cache = caches['testing'] if settings.TESTING else caches['default']
cache = caches['testing'] if getattr(settings, 'TESTING', False) else caches['default']


class FriendshipService(object):
    # 正确的写法一：使用prefetch_related，会自动执行成两条语句，用In Query查询，实际执行的
    # SQL查询和写法二是一样的，一共两条SQL queries
    @classmethod
    def get_followers(cls, user):
        friendships = Friendship.objects.filter(
            to_user=user,
        ).prefetch_related('from_user')
        return [friendship.from_user for friendship in friendships]

    # 正确的写法二，手动filter ID，使用IN Query 查询
    # friendships = Friendship.objects.filter(to_user=user)
    # follower_ids = [friendship.from_user_id for friendship in friendships]
    # followers = User.objects.filter(id__in=follower_ids)

    @classmethod
    def has_followed(cls, from_user, to_user):
        return Friendship.objects.filter(
            from_user=from_user,
            to_user=to_user,
        ).exists()

    @classmethod
    def get_following_user_id_set(cls, from_user_id):
        # followings:from_user_id
        key = FOLLOWINGS_PATTERN.format(user_id=from_user_id)
        user_id_set = cache.get(key)
        if user_id_set is not None:
            return user_id_set

        friendships = Friendship.objects.filter(from_user_id=from_user_id)
        user_id_set = set([
            fs.to_user_id for fs in friendships
        ])
        cache.set(key, user_id_set)
        return user_id_set

    # CREATE & DELETE friendship will call this method
    @classmethod
    def invalidate_following_cache(cls, from_user_id):
        # followings:from_user_id
        key = FOLLOWINGS_PATTERN.format(user_id=from_user_id)
        cache.delete(key)
