from django.conf import settings
from friendships.models import Friendship
from newsfeeds.models import NewsFeed
from newsfeeds.services import NewsFeedService
from testing.testcases import TestCase
from utils.paginations import EndlessPagination

NEWSFEEDS_URL = '/api/newsfeeds/'
POST_TWEET_URL = '/api/tweets/'
FOLLOW_URL = '/api/friendships{}/follow/'


class NewsFeedApiTests(TestCase):
    def setUp(self):
        self.clear_cache()
        self.make_up_friendships()

    def test_list(self):
        # 需要登陆
        response = self.anonymous_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 403)
        # 不能用POST
        response = self.ann_client.post(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 405)
        # 没有人发过tweet
        response = self.ann_client.get(NEWSFEEDS_URL)
        self.assertEqual(len(response.data['results']), 0)
        # 自己发了一条tweet后
        self.ann_client.post(POST_TWEET_URL, {'content': 'Hello World'})
        response = self.ann_client.get(NEWSFEEDS_URL)
        self.assertEqual(len(response.data['results']), 1)
        # 关注其他人后可以看到别人的tweet
        Friendship.objects.create(
            from_user=self.ann,
            to_user=self.bob
        )
        response = self.bob_client.post(POST_TWEET_URL, {'content': 'Hello World'})
        posted_tweet_id = response.data['id']
        response = self.ann_client.get(NEWSFEEDS_URL)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['tweet']['id'], posted_tweet_id)

    def test_pagination(self):
        page_size = EndlessPagination.page_size
        followed_user = self.create_user('followed')
        newsfeeds = []
        for _ in range(page_size * 2):
            tweet = self.create_tweet(followed_user)
            newsfeed = self.create_newsfeed(user=self.ann, tweet=tweet)
            newsfeeds.append(newsfeed)

        newsfeeds = newsfeeds[::-1]

        # pull the first page
        response = self.ann_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.data['has_next_page'], True)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['results'][0]['id'], newsfeeds[0].id)
        self.assertEqual(response.data['results'][1]['id'], newsfeeds[1].id)
        self.assertEqual(response.data['results'][page_size - 1]['id'], newsfeeds[page_size - 1].id)

        # pull the second page
        response = self.ann_client.get(NEWSFEEDS_URL, {
            'created_at__lt': newsfeeds[page_size - 1].created_at,
        })
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['results'][0]['id'], newsfeeds[page_size].id)
        self.assertEqual(response.data['results'][1]['id'], newsfeeds[page_size + 1].id)
        self.assertEqual(response.data['results'][page_size - 1]['id'], newsfeeds[2 * page_size - 1].id)

        # pull the lastest newsfeeds
        response = self.ann_client.get(
            NEWSFEEDS_URL,
            {'created_at__gt': newsfeeds[0].created_at},
        )
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), 0)

        tweet = self.create_tweet(followed_user)
        new_newsfeed = self.create_newsfeed(self.ann, tweet)

        response = self.ann_client.get(
            NEWSFEEDS_URL,
            {'created_at__gt': newsfeeds[0].created_at},
        )
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], new_newsfeed.id)

    def test_user_cache(self):
        # 测试当我们修改了 profile 之后，这个修改可以反映在所有相关的元素上
        # newsfeed -> tweet -> user -> profile
        profile = self.bob.profile
        profile.nickname = 'bob_nickname'
        profile.save()

        self.assertEqual(self.ann.username, 'ann')
        self.create_newsfeed(self.bob, self.create_tweet(self.ann))
        self.create_newsfeed(self.bob, self.create_tweet(self.bob))

        response = self.bob_client.get(NEWSFEEDS_URL)
        results = response.data['results']
        self.assertEqual(results[0]['tweet']['user']['username'], 'bob')
        self.assertEqual(results[0]['tweet']['user']['nickname'], 'bob_nickname')
        self.assertEqual(results[1]['tweet']['user']['username'], 'ann')

        self.ann.username = 'new_ann'
        self.ann.save()
        profile.nickname = 'new_bob_nickname'
        profile.save()

        response = self.bob_client.get(NEWSFEEDS_URL)
        results = response.data['results']
        self.assertEqual(results[0]['tweet']['user']['username'], 'bob')
        self.assertEqual(results[0]['tweet']['user']['nickname'], 'new_bob_nickname')
        self.assertEqual(results[1]['tweet']['user']['username'], 'new_ann')

    def test_tweet_cache(self):
        tweet = self.create_tweet(self.ann, 'content1')
        self.create_newsfeed(self.bob, tweet)
        response = self.bob_client.get(NEWSFEEDS_URL)
        results = response.data['results']
        self.assertEqual(results[0]['tweet']['user']['username'], 'ann')

        # update username
        self.ann.username = 'new_ann'
        self.ann.save()
        response = self.bob_client.get(NEWSFEEDS_URL)
        results = response.data['results']
        self.assertEqual(results[0]['tweet']['user']['username'], 'new_ann')

        # update content
        tweet.content = 'new_content'
        tweet.save()
        response = self.bob_client.get(NEWSFEEDS_URL)
        results = response.data['results']
        self.assertEqual(results[0]['tweet']['content'], 'new_content')

    def _paginate_to_get_newsfeeds(self, client):
        # paginate until the end
        response = client.get(NEWSFEEDS_URL)
        results = response.data['results']
        while response.data['has_next_page']:
            created_at__lt = response.data['results'][-1]['created_at']
            response = client.get(NEWSFEEDS_URL, {'created_at__lt': created_at__lt})
            results.extend(response.data['results'])
        return results

    def test_redis_list_limit(self):
        list_limit = settings.REDIS_LIST_LENGTH_LIMIT
        page_size = 20
        users = [self.create_user(f'user{i}') for i in range(5)]
        newsfeeds = []
        for i in range(list_limit + page_size):
            tweet = self.create_tweet(user=users[i % 5], content=f'feed{i}')
            feed = self.create_newsfeed(self.ann, tweet)
            newsfeeds.append(feed)
        newsfeeds = newsfeeds[::-1]

        # only cached list_limit objects
        cached_newsfeeds = NewsFeedService.get_cached_newsfeeds(self.ann.id)
        self.assertEqual(len(cached_newsfeeds), list_limit)
        queryset = NewsFeed.objects.filter(user=self.ann)
        self.assertEqual(queryset.count(), list_limit + page_size)

        results = self._paginate_to_get_newsfeeds(self.ann_client)
        for i in range(list_limit + page_size):
            self.assertEqual(newsfeeds[i].id, results[i]['id'])

        # a followed user creates a new tweet
        self.create_friendship(self.ann, self.bob)
        new_tweet = self.create_tweet(self.bob, 'a new tweet')
        NewsFeedService.fanout_to_followers(new_tweet)

        def _test_newsfeeds_after_new_feed_pushed():
            results = self._paginate_to_get_newsfeeds(self.ann_client)
            self.assertEqual(len(results), list_limit + page_size + 1)
            self.assertEqual(results[0]['tweet']['id'], new_tweet.id)
            for i in range(list_limit + page_size):
                self.assertEqual(newsfeeds[i].id, results[i + 1]['id'])

        _test_newsfeeds_after_new_feed_pushed()

        # mock cache expired
        _test_newsfeeds_after_new_feed_pushed()
