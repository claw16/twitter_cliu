from accounts.services import UserService
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import models
from likes.models import Like
from tweets.constants import TweetPhotoStatus, TWEET_PHOTO_STATUS_CHOICES
from utils.time_helpers import utc_now


class Tweet(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        help_text="who posts this tweet",
    )
    content = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # 这个联合索引可以方便地找出某个user发的所有的帖子
        index_together = (('user', 'created_at'),)
        ordering = ('user', '-created_at')

    @property
    def hours_to_now(self):
        # datetime.now 不带时区信息，需要加上utc的时区信息
        return (utc_now() - self.created_at).seconds // 3600

    # 在 Tweet 中获得对应的 comments
    # @property
    # def comments(self):
    #     return self.comment_set.all()
    #     return Comment.objects.filter(tweet=self)

    @property
    def like_set(self):
        return Like.objects.filter(
            content_type=ContentType.objects.get_for_model(Tweet),
            object_id=self.id,
        ).order_by('-created_at')

    @property
    def cached_user(self):
        return UserService.get_user_through_cache(self.user_id)

    def __str__(self):
        # print(tweet instance)
        return f'{self.created_at} {self.user}: {self.content}'


class TweetPhoto(models.Model):
    # which tweet is the photo posted
    tweet = models.ForeignKey(Tweet, on_delete=models.SET_NULL, null=True)

    # who uploaded this photo. This info can be obtained from tweet, but this redundant info
    # has benefits: 1. say someone usually posts illegal photos, new photos from this user
    # can easily be marked and need further review. 2. if we need to ban all photos of a user,
    # we can quickly filter via this model.
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    # photo file
    file = models.FileField()
    order = models.IntegerField(default=0)

    # photo status for review purpose
    status = models.IntegerField(
        default=TweetPhotoStatus.PENDING,
        choices=TWEET_PHOTO_STATUS_CHOICES,
    )

    # soft delete - while a photo is being deleted, it'll be marked as deleted, but it's really
    # deleted afterwards using async tasks for efficiency purpose
    has_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        index_together = (
            ('user', 'created_at'),
            ('has_deleted', 'created_at'),
            ('status', 'created_at'),
            ('tweet', 'order'),
        )

    def __str__(self):
        return f'{self.tweet_id}: {self.file}'
