from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from tweets.api.serializers import (
    TweetSerializer,
    TweetSerializerForCreate,
    TweetSerializerForDetail
)
from tweets.models import Tweet
from newsfeeds.services import NewsFeedService
from utils.decorators import required_params
from utils.paginations import EndlessPagination


class TweetViewSet(viewsets.GenericViewSet):
    """
    API endpoint that allows users to create and list tweets
    """
    queryset = Tweet.objects.all()
    serializer_class = TweetSerializerForCreate
    pagination_class = EndlessPagination

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    @required_params(params=['user_id'])
    def list(self, request, *args, **kwargs):
        """
        Re-write list method, only list `user_id`'s tweets
        """
        # if 'user_id' not in request.query_params:
        #     return Response('missing user_id', status=400)

        # SQL statement:
        # select * from twitter_tweets
        # where user_id = xxx
        # order by created_at desc
        # this SQL query uses indexing (user, -created_at)
        # indexing only (user) is not sufficient
        tweets = Tweet.objects.filter(
            user_id=request.query_params['user_id']
        ).order_by('-created_at')
        tweets = self.paginate_queryset(tweets)
        serializer = TweetSerializer(
            tweets,
            many=True,
            context={'request': request},
        )
        # deprecated and replaced with paginated_response
        # # JSON responses are commonly used, instead of lists
        # return Response({'tweets': serializer.data})
        return self.get_paginated_response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        Re-write create method to use current login user
        as the default user
        """
        serializer = TweetSerializerForCreate(
            data=request.data,
            context={'request': request}
        )
        if not serializer.is_valid():  # must call is_valid() before save()
            return Response({
                'succeed': False,
                'message': "Please check input",
                'errors': serializer.errors,
            }, status=400)
        tweet = serializer.save()  # save to DB
        NewsFeedService.fanout_to_followers(tweet)
        return Response(TweetSerializer(tweet, context={'request': request}).data, status=201)

    def retrieve(self, request, *args, **kwargs):
        # <HOMEWORK 1> 通过某个query参数with_all_comments来决定是否需要带上所有comments
        # <HOMEWORK 2> 通过某个query参数with_preview_comments来决定是否带上前3条comments
        tweet = self.get_object()
        return Response(TweetSerializerForDetail(
            tweet,
            context={'request': request}).data,
        )
