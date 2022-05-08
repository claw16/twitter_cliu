from django.contrib.auth.models import User
from rest_framework import exceptions, serializers


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # Not working if put 'url' in fields
        fields = ('id', 'username', 'email', 'password')


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class SignupSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=20, min_length=6)
    password = serializers.CharField(max_length=20, min_length=6)
    email = serializers.EmailField()

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def validate(self, attrs):
        if User.objects.filter(username=attrs.get('username').lower()).exists():
            raise exceptions.ValidationError({
                'username': ['This username has been occupied.']
            })
        if User.objects.filter(email=attrs.get('email').lower()).exists():
            raise exceptions.ValidationError({
                'email': ['This email has been occupied.']
            })
        return attrs

    def create(self, validated_data):
        username = validated_data.get('username').lower()
        email = validated_data.get('email').lower()
        password = validated_data.get('password')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
        )
        # Create UserProfile object
        user.profile
        return user
