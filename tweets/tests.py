from datetime import timedelta
from testing.testcases import TestCase
from tweets.constants import TweetPhotoStatus
from tweets.models import TweetPhoto
from tweets.serivces import TweetService
from twitter.cache import USER_TWEETS_PATTERN
from utils.redis_client import RedisClient
from utils.redis_serializers import DjangoModelSerializer
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


class TweetServiceTests(TestCase):
    def setUp(self):
        self.clear_cache()
        self.ann = self.create_user('ann')

    def test_get_user_tweets(self):
        tweets_ids = []
        for i in range(3):
            tweet = self.create_tweet(self.ann, f'tweet {i}')
            tweets_ids.append(tweet.id)
        tweets_ids = tweets_ids[::-1]

        RedisClient.clear()
        conn = RedisClient.get_connection()

        # cache miss
        tweets = TweetService.get_cached_tweets(self.ann.id)
        self.assertEqual([t.id for t in tweets], tweets_ids)

        # cache hit
        tweets = TweetService.get_cached_tweets(self.ann.id)
        self.assertEqual([t.id for t in tweets], tweets_ids)

        # cache updated
        new_tweet = self.create_tweet(self.ann, 'new tweet')
        tweets = TweetService.get_cached_tweets(self.ann.id)
        tweets_ids.insert(0, new_tweet.id)
        self.assertEqual([t.id for t in tweets], tweets_ids)

    def test_create_new_tweet_before_get_cached_tweets(self):
        tweet1 = self.create_tweet(self.ann, 'tweet1')
        key = USER_TWEETS_PATTERN.format(user_id=self.ann.id)
        conn = RedisClient.get_connection()
        self.assertEqual(conn.exists(key), True)
        RedisClient.clear()
        self.assertEqual(conn.exists(key), False)
        tweet2 = self.create_tweet(self.ann, 'tweet2')
        self.assertEqual(conn.exists(key), True)

        tweets = TweetService.get_cached_tweets(self.ann.id)
        self.assertEqual([t.id for t in tweets], [tweet2.id, tweet1.id])
