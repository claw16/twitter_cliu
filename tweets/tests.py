from testing.testcases import TestCase
from datetime import timedelta
from utils.time_helpers import utc_now


# Create your tests here.
class TweetTests(TestCase):
    def setUp(self):
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
