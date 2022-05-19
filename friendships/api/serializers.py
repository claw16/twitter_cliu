from accounts.api.serializers import UserSerializerForFriendship
from django.contrib.auth.models import User
from friendships.models import Friendship
from friendships.services import FriendshipService
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class FriendshipSerializerForCreate(serializers.ModelSerializer):
    from_user_id = serializers.IntegerField()
    to_user_id = serializers.IntegerField()

    class Meta:
        model = Friendship
        fields = ('from_user_id', 'to_user_id')

    def validate(self, attrs):
        # attrs是客户端传进来的，应该是同一种类型，所以可以直接比较
        if attrs['from_user_id'] == attrs['to_user_id']:
            raise ValidationError({
                'message': 'from_user_id and to_user_id should be different'
            })

        # 此处无论attrs['to_user_id']是int还是str，Django都能handle
        if not User.objects.filter(id=attrs['to_user_id']).exists():
            raise ValidationError({
                'message': 'You cannot follow a non-existing user.'
            })
        return attrs

    def create(self, validated_data):
        from_user_id = validated_data['from_user_id']
        to_user_id = validated_data['to_user_id']
        return Friendship.objects.create(
            from_user_id=from_user_id,
            to_user_id=to_user_id,
        )


# 可以通过 source=xxx 指定去访问每个 model instance 的 xxx 方法
# 即 model_instance.xxx 来获得数据
# 在这个例子中就是 Friendship.from_user
# https://www.django-rest-framework.org/api-guide/serializers/#specifying-fields-explicitly
class FollowerSerializer(serializers.ModelSerializer):
    user = UserSerializerForFriendship(source='from_user')
    created_at = serializers.DateTimeField()
    has_followed = serializers.SerializerMethodField()

    class Meta:
        model = Friendship
        fields = ('user', 'created_at', 'has_followed')

    def get_has_followed(self, obj):
        if self.context['request'].user.is_anonymous:
            return False
        # TODO: 这会对每个 object 执行一次 SQL 查询，速度慢。后续优化
        # TODO: why not obj.to_user ?
        return FriendshipService.has_followed(self.context['request'].user, obj.from_user)


class FollowingSerializer(serializers.ModelSerializer):
    user = UserSerializerForFriendship(source='to_user')
    created_at = serializers.DateTimeField()
    has_followed = serializers.SerializerMethodField()

    class Meta:
        model = Friendship
        fields = ('user', 'created_at', 'has_followed')

    def get_has_followed(self, obj):
        if self.context['request'].user.is_anonymous:
            return False
        # TODO: 这会对每个 object 执行一次 SQL 查询，速度慢。后续优化
        return FriendshipService.has_followed(self.context['request'].user, obj.to_user)
