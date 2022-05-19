from friendships.models import Friendship


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
