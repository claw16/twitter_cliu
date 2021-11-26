from django.contrib.auth.models import User
from rest_framework import serializers
# paied attention, made some changes

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # Not working if put 'url' in fields
        fields = ['username', 'email', 'password']
