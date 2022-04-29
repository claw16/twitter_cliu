from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import models
from likes.models import Like
from utils.time_helpers import utc_now
# from comments.models import Comment


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

    def __str__(self):
        # print(tweet instance)
        return f'{self.created_at} {self.user}: {self.content}'
