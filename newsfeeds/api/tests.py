from friendships.models import Friendship
from testing.testcases import TestCase


NEWSFEEDS_URL = '/api/newsfeeds/'
POST_TWEET_URL = '/api/tweets/'
FOLLOW_URL = '/api/friendships{}/follow/'


class NewsFeedApiTests(TestCase):
    def setUp(self):
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
        self.assertEqual(len(response.data['newsfeeds']), 0)
        # 自己发了一条tweet后
        self.ann_client.post(POST_TWEET_URL, {'content': 'Hello World'})
        response = self.ann_client.get(NEWSFEEDS_URL)
        self.assertEqual(len(response.data['newsfeeds']), 1)
        # 关注其他人后可以看到别人的tweet
        Friendship.objects.create(
            from_user=self.ann,
            to_user=self.bob
        )
        response = self.bob_client.post(POST_TWEET_URL, {'content': 'Hello World'})
        posted_tweet_id = response.data['id']
        response = self.ann_client.get(NEWSFEEDS_URL)
        self.assertEqual(len(response.data['newsfeeds']), 2)
        self.assertEqual(response.data['newsfeeds'][0]['tweet']['id'], posted_tweet_id)
