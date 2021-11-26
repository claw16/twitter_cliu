from accounts.api.serializers import UserSerializer
from django.contrib.auth.models import User
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ModelViewSet: provides a form that allows user to POST new user/password
    ReadOnlyModelViewSet: read user views only
    """

    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)  # Why list -> tuple?


class AccountViewSet(viewsets.ViewSet):
    """
    API endpoint that allows user registration, login, log out,
    and view login status.
    """
    @action(methods=["GET"], detail=False)
    def login_status(self, request: Request) -> Response:
        data = {'has_logged_in': request.user.is_authenticated}
        # If we try to get login_status without login, we are marked as
        # an anonymous user
        if request.user.is_authenticated:
            # User UserSerializer to interpret request.user object
            data['user'] = UserSerializer(request.user).data
            """
            Example: 
            request.user: admin
            
            UserSerializer(request.user): 
            UserSerializer(<SimpleLazyObject: <User: admin>>):
            username = CharField(help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, validators=[<django.contrib.auth.validators.UnicodeUsernameValidator object>, <UniqueValidator(queryset=User.objects.all())>])
            email = EmailField(allow_blank=True, label='Email address', max_length=254, required=False)
            password = CharField(max_length=128)
            
            data: 
            {
                'username': 'admin', 
                'email': 'admin@jiuzhang.com', 
                'password': 'pbkdf2_sha256$216000$8nSnXKkNnFRn$9k5dyUoCfKHkKLOM8u4Nuo+/sQ1DOksDgpraV7u9F18='}
            """
        return Response(data)

