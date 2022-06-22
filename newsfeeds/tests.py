from newsfeeds.models import NewsFeed
from newsfeeds.services import NewsFeedService
from newsfeeds.tasks import fanout_newsfeeds_main_task
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


class NewsFeedTaskTests(TestCase):
    def setUp(self):
        self.clear_cache()
        self.create_user_and_client()

    def test_fanout_main_task(self):
        tweet = self.create_tweet(self.ann, 'tweet 1')
        self.create_friendship(self.bob, self.ann)
        msg = fanout_newsfeeds_main_task(tweet.id, self.ann.id)
        self.assertEqual(msg, '1 newsfeeds going to fanout, 1 batches created.')
        # 1 for ann herself, 1 for fanout
        self.assertEqual(1 + 1, NewsFeed.objects.count())
        ann_cached_list = NewsFeedService.get_cached_newsfeeds(self.ann.id)
        self.assertEqual(len(ann_cached_list), 1)
        bob_cached_list = NewsFeedService.get_cached_newsfeeds(self.bob.id)
        self.assertEqual(len(bob_cached_list), 1)

        for i in range(2):
            user = self.create_user(f"user_{i}")
            self.create_friendship(user, self.ann)
        tweet = self.create_tweet(self.ann, 'tweet 2')
        msg = fanout_newsfeeds_main_task(tweet.id, self.ann.id)
        self.assertEqual(msg, '3 newsfeeds going to fanout, 1 batches created.')
        # 1 for ann herself, 3 for fanout = 4, 2 for 'tweet 1'
        self.assertEqual(4 + 2, NewsFeed.objects.count())
        ann_cached_list = NewsFeedService.get_cached_newsfeeds(self.ann.id)
        self.assertEqual(len(ann_cached_list), 2)
        bob_cached_list = NewsFeedService.get_cached_newsfeeds(self.bob.id)
        self.assertEqual(len(bob_cached_list), 2)

        user = self.create_user('another user')
        self.create_friendship(user, self.ann)
        tweet = self.create_tweet(self.ann, 'tweet 3')
        msg = fanout_newsfeeds_main_task(tweet.id, self.ann.id)
        # Ann has 4 followers, batch size = 3, so 1 batch has 3 followers, another batch has 1 follower
        self.assertEqual(msg, '4 newsfeeds going to fanout, 2 batches created.')
        # Had 6 newsfeeds already, now 4 to fanout and 1 for ann herself, 11 in total
        self.assertEqual(8 + 3, NewsFeed.objects.count())  # TODO: why 8 + 3
        ann_cached_list = NewsFeedService.get_cached_newsfeeds(self.ann.id)
        self.assertEqual(len(ann_cached_list), 3)
        bob_cached_list = NewsFeedService.get_cached_newsfeeds(self.bob.id)
        self.assertEqual(len(bob_cached_list), 3)