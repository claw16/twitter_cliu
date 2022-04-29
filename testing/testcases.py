from django.contrib.auth.models import User
from django.test import TestCase as DjangoTestCase
from friendships.models import Friendship
from rest_framework.test import APIClient
from tweets.models import Tweet
from comments.models import Comment
from likes.models import Like
from django.contrib.contenttypes.models import ContentType


class TestCase(DjangoTestCase):

    def create_user(self, username, email=None, password=None):
        if password is None:
            password = 'generic password'
        if email is None:
            email = f'{username}@mail.com'
        # can't user User.objects.create() because
        # password need encryption, username and email need normalization
        return User.objects.create_user(username, email, password)

    def create_tweet(self, user, content=None):
        if content is None:
            content = 'default tweet content'
        return Tweet.objects.create(user=user, content=content)

    def create_user_and_client(self):
        self.anonymous_client = APIClient()
        self.ann = self.create_user('ann')
        self.bob = self.create_user('bob')
        self.ann_client = APIClient()
        self.bob_client = APIClient()
        self.ann_client.force_authenticate(self.ann)
        self.bob_client.force_authenticate(self.bob)

    def make_up_friendships(self):
        if getattr(self, "ann", None) is None:
            self.create_user_and_client()
        # create followings and followers for bob
        for i in range(2):
            follower = self.create_user(f'bob_follower_{i}')
            Friendship.objects.create(from_user=follower, to_user=self.bob)
        for i in range(3):
            following = self.create_user(f'bob_following_{i}')
            Friendship.objects.create(from_user=self.bob, to_user=following)

    def create_comment(self, user, tweet, content=None):
        if content is None:
            content = 'This is a default Tweet content.'
        return Comment.objects.create(user=user, tweet=tweet, content=content)

    def create_like(self, user, target):
        # target is a comment or a tweet
        instance, _ = Like.objects.get_or_create(
            content_type=ContentType.objects.get_for_model(target.__class__),
            object_id=target.id,
            user=user,
        )
        return instance
