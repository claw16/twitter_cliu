from accounts.services import UserService
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class Like(models.Model):
    # https://docs.djangoproject.com/en/4.0/ref/contrib/contenttypes/
    object_id = models.PositiveIntegerField()  # comment_id or tweet_id
    # 一个通用的foreign key，通过content_type和object_id来确定一个comment_id或者tweet_id
    # content_type就对应了这个project里的某一个model
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # like.content_type 可以通过这里的 content_type 和 object_id 得到对应的 object
    # 也就是对应的 tweet 或者 comment
    # 这一项并不会真正的储存在表单中
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        # 在数据库层面确保不会创建多个 user-content_object 的 likes
        # 会创建一个 <user, content_type, object_id> 的索引
        # 同时具备查询某个user like了哪些不同的objects的功能。
        unique_together = (('user', 'content_type', 'object_id'),)
        index_together = (
            # 这个索引可以按时间排序某个content_object的所有likes
            ('content_type', 'object_id', 'created_at'),
            # 某个用户的对tweet/comment的likes按时间排列
            ('user', 'content_type', 'created_at'),
        )

    def __str__(self):
        return '{} - {} liked {} {}'.format(
            self.created_at,
            self.user,
            self.content_type,
            self.object_id,
        )

    @property
    def cached_user(self):
        return UserService.get_user_through_cache(self.user_id)
