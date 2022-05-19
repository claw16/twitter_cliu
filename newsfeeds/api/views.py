from newsfeeds.api.serializers import NewsFeedSerializer
from newsfeeds.models import NewsFeed
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utils.paginations import EndlessPagination


class NewsFeedViewSet(viewsets.GenericViewSet):
    permission_classes = (IsAuthenticated,)
    pagination_class = EndlessPagination

    def get_queryset(self):
        # 自定义queryset，因为newsfeed的查看是有权限的
        # 只能看user=当前登陆用户的newsfeed
        # 也可以是self.request.user.newsfeed_set.all()
        # 但是一般最好还是按照Newsfeed.objects.filter的方式写，更情绪直观
        return NewsFeed.objects.filter(user=self.request.user)

    def list(self, request):
        queryset = self.paginate_queryset(self.get_queryset())
        serializer = NewsFeedSerializer(
            queryset,
            context={'request': request},
            many=True,
        )
        return self.get_paginated_response(serializer.data)
