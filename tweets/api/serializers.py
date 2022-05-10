from accounts.api.serializers import UserSerializerForTweet
from comments.api.serializers import CommentSerializer
from likes.api.serializers import LikeSerializer
from likes.services import LikeService
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from tweets.constants import TWEET_PHOTO_UPLOAD_LIMIT
from tweets.models import Tweet
from tweets.serivces import TweetService


class TweetSerializer(serializers.ModelSerializer):
    user = UserSerializerForTweet()
    comments_count = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    has_liked = serializers.SerializerMethodField()
    photo_urls = serializers.SerializerMethodField()

    class Meta:
        model = Tweet
        fields = (
            'id',
            'user',
            'created_at',
            'content',
            'comments_count',
            'likes_count',
            'has_liked',
            'photo_urls',
        )

    def get_likes_count(self, obj):
        return obj.like_set.count()

    def get_comments_count(self, obj):
        return obj.comment_set.count()

    def get_has_liked(self, obj):
        return LikeService.has_liked(self.context['request'].user, obj)

    def get_photo_urls(self, obj):
        photo_urls = []
        # order_by('order'), this 'order' is TweetPhoto.order
        for photo in obj.tweetphoto_set.all().order_by('order'):
            # photo -> TweetPhoto, -> has file property -> FileField()
            # has url property, so we can use photo.file.url
            photo_urls.append(photo.file.url)
        return photo_urls


class TweetSerializerForCreate(serializers.ModelSerializer):
    content = serializers.CharField(min_length=6, max_length=140)
    # ListField 要求客户端以列表形式POST进来，列表里面元素的类型由child来指定
    # ListField也支持max/min length的限制，也可以用它来限制图片上传limit
    files = serializers.ListField(
        child=serializers.FileField(),
        allow_empty=True,  # 列表可以是空的，没有元素
        required=False,  # 前端可以不传 files 这个列表
    )

    class Meta:
        model = Tweet
        fields = ('content', 'files',)

    def validate(self, attrs):
        # 为什么不把这个验证放在前端？后端验证的坏处是，用户已经选择好了照片，发送了request
        # 然后才得到这个错误，浪费时间
        if len(attrs.get('files', [])) > TWEET_PHOTO_UPLOAD_LIMIT:
            raise ValidationError({
                'message': f'You can upload {TWEET_PHOTO_UPLOAD_LIMIT} photos at most',
            })
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        content = validated_data['content']
        tweet = Tweet.objects.create(user=user, content=content)
        if validated_data.get('files'):
            TweetService.create_photo_from_files(
                tweet=tweet,
                files=validated_data['files'],
            )
        return tweet


# Tweet + comments + likes + photos
class TweetSerializerForDetail(TweetSerializer):
    # user = UserSerializer()
    comments = CommentSerializer(source='comment_set', many=True)
    likes = LikeSerializer(source='like_set', many=True)

    class Meta:
        model = Tweet
        fields = (
            'id',
            'user',
            'comments',
            'created_at',
            'content',
            'likes',
            'comments',
            'likes_count',
            'comments_count',
            'has_liked',
            'photo_urls',  # from TweetSerializer
        )

    # <HOMEWORK> 用 serializers.SerializerMethodField 的方式实现 comments 的获取
    # comments = serializers.SerializerMethodField()
    # get_comments 需要返回已经序列化过的数据
    # def get_comments(self, obj):  # obj -> Tweet
    #     return CommentSerializer(obj.comment_set.all(), many=True).data
