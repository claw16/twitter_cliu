from newsfeeds.services import NewsFeedService
from testing.testcases import TestCase
from twitter.cache import USER_NEWSFEEDS_PATTERN
from utils.redis_client import RedisClient


class NewsFeedServiceTests(TestCase):
    def setUp(self):
        self.clear_cache()
        self.ann = self.create_user('ann')
        self.bob = self.create_user('bob')

    def test_get_user_newsfeeds(self):
        newsfeed_ids = []
        for i in range(3):
            tweet = self.create_tweet(self.bob)
            newsfeed = self.create_newsfeed(self.ann, tweet)
            newsfeed_ids.append(newsfeed.id)
        newsfeed_ids = newsfeed_ids[::-1]

        # cache miss
        newsfeeds = NewsFeedService.get_cached_newsfeeds(self.ann.id)
        self.assertEqual([f.id for f in newsfeeds], newsfeed_ids)

        # cache hit
        newsfeeds = NewsFeedService.get_cached_newsfeeds(self.ann.id)
        self.assertEqual([f.id for f in newsfeeds], newsfeed_ids)

        # cache update
        tweet = self.create_tweet(self.ann)
        new_newsfeed = self.create_newsfeed(self.ann, tweet)
        newsfeeds = NewsFeedService.get_cached_newsfeeds(self.ann.id)
        newsfeed_ids.insert(0, new_newsfeed.id)
        self.assertEqual([f.id for f in newsfeeds], newsfeed_ids)

    def test_create_new_newsfeed_before_get_cached_newsfeeds(self):
        feed1 = self.create_newsfeed(self.ann, self.create_tweet(self.ann))
        conn = RedisClient.get_connection()
        key = USER_NEWSFEEDS_PATTERN.format(user_id=self.ann.id)
        self.assertEqual(conn.exists(key), True)
        RedisClient.clear()
        self.assertEqual(conn.exists(key), False)
        feed2 = self.create_newsfeed(self.ann, self.create_tweet(self.ann))
        self.assertEqual(conn.exists(key), True)

        feeds = NewsFeedService.get_cached_newsfeeds(self.ann.id)
        self.assertEqual([f.id for f in feeds], [feed2.id, feed1.id])
