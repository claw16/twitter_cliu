from comments.models import Comment
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.cache import caches
from django.test import TestCase as DjangoTestCase
from django_hbase.models import HBaseModel
from friendships.models import Friendship
from likes.models import Like
from newsfeeds.models import NewsFeed
from rest_framework.test import APIClient
from tweets.models import Tweet
from utils.redis_client import RedisClient


class TestCase(DjangoTestCase):
    hbase_tables_created = False

    def setUp(self):
        self.clear_cache()
        try:
            self.hbase_tables_created = True
            for hbase_model_class in HBaseModel.__subclasses__():
                hbase_model_class.create_table()
        except Exception:
            self.tearDown()
            raise

    def tearDown(self):
        if not self.hbase_tables_created:
            return

        for hbase_model_class in HBaseModel.__subclasses__():
            hbase_model_class.drop_table()

    def clear_cache(self):
        RedisClient.clear()
        caches['testing'].clear()

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

    def create_newsfeed(self, user, tweet):
        return NewsFeed.objects.create(user=user, tweet=tweet)

    def create_friendship(self, from_user, to_user):
        return Friendship.objects.create(from_user=from_user, to_user=to_user)
