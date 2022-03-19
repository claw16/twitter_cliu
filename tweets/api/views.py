from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from tweets.api.serializers import TweetSerializer, TweetCreateSerializer
from tweets.models import Tweet


class TweetViewSet(viewsets.GenericViewSet,
                   viewsets.mixins.CreateModelMixin,
                   viewsets.mixins.ListModelMixin,):
    """
    API endpoint that allows users to create and list tweets
    """
    queryset = Tweet.objects.all()
    serializer_class = TweetCreateSerializer

    def get_permissions(self):
        if self.action == 'list':
            return [AllowAny()]
        return [IsAuthenticated()]

    def list(self, request, *args, **kwargs):
        """
        Re-write list method, only list `user_id`'s tweets
        """
        if 'user_id' not in request.query_params:
            return Response('missing user_id', status=400)

        # SQL statement:
        # select * from twitter_tweets
        # where user_id = xxx
        # order by created_at desc
        # this SQL query uses indexing (user, -created_at)
        # indexing only (user) is not sufficient
        tweets = Tweet.objects.filter(
            user_id=request.query_params['user_id']
        ).order_by('-created_at')
        serializer = TweetSerializer(tweets, many=True)
        # JSON responses are commonly used, instead of lists
        return Response({'tweets': serializer.data})

    def create(self, request, *args, **kwargs):
        """
        Re-write create method to use current login user
        as the default user
        """
        serializer = TweetCreateSerializer(
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
        return Response(TweetSerializer(tweet).data, status=201)
