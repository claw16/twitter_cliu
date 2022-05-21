from accounts.services import UserService
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save, pre_delete
from friendships.listeners import friendship_changed


class Friendship(models.Model):
    from_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='following_friendship_set',
    )
    '''
    related_name: for inverse query, e.g. user.following_friendship_set
    <==> friendship.object.filter(from_user=user)
    '''

    to_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='follower_friendship_set',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        index_together = (
            # query: get all users I'm following ordered by created_at
            ('from_user_id', 'created_at'),
            # query: get all my followers ordered by created_at
            ('to_user_id', 'created_at'),
        )
        # only 1 pair of `from_user - to_user` is allowed
        unique_together = (('from_user_id', 'to_user_id'),)

    def __str__(self):
        return f'{self.from_user_id} followed {self.to_user_id}'

    @property
    def cached_from_user(self):
        return UserService.get_user_through_cache(self.from_user_id)

    @property
    def cached_to_user(self):
        return UserService.get_user_through_cache(self.to_user_id)


# hook up with listeners to invalidate cache
pre_delete.connect(friendship_changed, sender=Friendship)
post_save.connect(friendship_changed, sender=Friendship)
