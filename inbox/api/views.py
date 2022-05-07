from django_filters.rest_framework import DjangoFilterBackend
from inbox.api.serializers import NotificationSerializer
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from notifications.models import Notification


class NotificationViewSet(
    viewsets.GenericViewSet,
    viewsets.mixins.ListModelMixin,
):
    # ListModelMixin 中包含了 list() 方法用于列出 queryset
    serializer_class = NotificationSerializer
    permission_classes = (IsAuthenticated,)
    # 用来给 ListModelMixin 筛选 unread = True/False
    filterset_fields = ('unread',)

    def get_queryset(self):
        # return self.request.user.notifications.all()
        return Notification.objects.filter(recipient=self.request.user)

    # url_path 可以指定 api 的 URL 名字不和 function 名字相同，这里这么做是因为
    # 默认的 URL 规则是不用下划线的，而 Python function 名字又不能用 dash -
    # GET /api/notifications/unread-count/
    @action(methods=['GET'], detail=False, url_path='unread-count')
    def unread_count(self, request, *args, **kwargs):
        count = self.get_queryset().filter(unread=True).count()
        return Response({'unread_count': count}, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False, url_path='mark-all-as-read')
    def mark_all_as_read(self, request, *args, **kwargs):
        updated_count = self.get_queryset().filter(unread=True).update(unread=False)
        return Response({'marked_count': updated_count}, status=status.HTTP_200_OK)
