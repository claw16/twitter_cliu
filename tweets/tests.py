from datetime import timedelta
from testing.testcases import TestCase
from tweets.constants import TweetPhotoStatus
from tweets.models import TweetPhoto
from utils.redis_serializers import DjangoModelSerializer
from utils.redis_client import RedisClient
from utils.time_helpers import utc_now


class TweetTests(TestCase):
    def setUp(self):
        self.clear_cache()
        self.ann = self.create_user('ann')
        self.tweet = self.create_tweet(self.ann, 'hello')

    def test_hour_to_now(self):
        self.tweet.created_at = utc_now() - timedelta(hours=10)
        self.tweet.save()
        self.assertEqual(self.tweet.hours_to_now, 10)

    def test_like_set(self):
        self.assertEqual(self.tweet.like_set.count(), 0)
        self.create_like(self.ann, self.tweet)
        self.assertEqual(self.tweet.like_set.count(), 1)

        self.create_like(self.ann, self.tweet)
        self.assertEqual(self.tweet.like_set.count(), 1)

        self.create_like(self.create_user('bob'), self.tweet)
        self.assertEqual(self.tweet.like_set.count(), 2)

    def test_create_photo(self):
        # create a photo data object
        photo = TweetPhoto.objects.create(
            tweet=self.tweet,
            user=self.ann,
        )
        self.assertEqual(photo.user, self.ann)
        self.assertEqual(photo.status, TweetPhotoStatus.PENDING)
        self.assertEqual(self.tweet.tweetphoto_set.count(), 1)

    def test_cache_tweet_in_redis(self):
        tweet = self.create_tweet(self.ann)
        serialized_data = DjangoModelSerializer.serialize(tweet)
        conn = RedisClient.get_connection()
        conn.set(f"tweet:{tweet.id}", serialized_data)
        data = conn.get("tweet:notfound")
        self.assertEqual(data, None)

        data = conn.get(f"tweet:{tweet.id}")
        deserialized_data = DjangoModelSerializer.deserialize(data)
        # 虽然这里的 tweet 和 deserialized_data 指向的不是同一个内存地址，
        # Django 的测试机制还是会去比较这两个 objects 的内容
        self.assertEqual(tweet, deserialized_data)
