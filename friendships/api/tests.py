from friendships.models import Friendship
from testing.testcases import TestCase


FOLLOW_URL = '/api/friendships/{}/follow/'
UNFOLLOW_URL = '/api/friendships/{}/unfollow/'
FOLLOWERS_URL = '/api/friendships/{}/followers/'
FOLLOWINGS_URL = '/api/friendships/{}/followings/'


class FriendshipApiTests(TestCase):
    def setUp(self) -> None:
        self.make_up_friendships()

    def test_follow(self):
        url = FOLLOW_URL.format(self.ann.id)

        # 需要登陆才能follow
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 403)
        # follow is a POST request
        response = self.bob_client.get(url)
        self.assertEqual(response.status_code, 405)
        # cannot follow self
        response = self.ann_client.post(url)
        self.assertEqual(response.status_code, 400)
        # a good follow
        response = self.bob_client.post(url)
        self.assertEqual(response.status_code, 201)
        # duplicate follow
        response = self.bob_client.post(url)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['duplicate'], True)
        # follow back will be a separate record
        count = Friendship.objects.count()
        response = self.ann_client.post(FOLLOW_URL.format(self.bob.id))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Friendship.objects.count(), count + 1)

    def test_unfollow(self):
        url = UNFOLLOW_URL.format(self.ann.id)

        # 需要登陆才能follow
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 403)
        # follow is a POST request
        response = self.bob_client.get(url)
        self.assertEqual(response.status_code, 405)
        # cannot unfollow self
        response = self.ann_client.post(url)
        self.assertEqual(response.status_code, 400)
        # a good unfollow
        Friendship.objects.create(
            from_user=self.bob,
            to_user=self.ann
        )
        count = Friendship.objects.count()
        response = self.bob_client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Friendship.objects.count(), count - 1)
        self.assertEqual(response.data['deleted'], 1)
        # 未follow的情况下unfollow静默处理
        count = Friendship.objects.count()
        response = self.bob_client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Friendship.objects.count(), count)
        self.assertEqual(response.data['deleted'], 0)

    def test_followings(self):
        url = FOLLOWINGS_URL.format(self.bob.id)

        # POST is not allowed
        response = self.bob_client.post(url)
        self.assertEqual(response.status_code, 405)
        # GET is good
        response = self.bob_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['followings']), 3)
        ts0 = response.data['followings'][0]['created_at']
        ts1 = response.data['followings'][1]['created_at']
        ts2 = response.data['followings'][2]['created_at']
        self.assertEqual(ts0 > ts1 > ts2, True)
        self.assertEqual(
            response.data['followings'][0]['user']['username'],
            'bob_following_2'
        )
        self.assertEqual(
            response.data['followings'][1]['user']['username'],
            'bob_following_1'
        )
        self.assertEqual(
            response.data['followings'][2]['user']['username'],
            'bob_following_0'
        )

    def test_followers(self):
        url = FOLLOWERS_URL.format(self.bob.id)

        # POST is not allowed
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 405)
        # GET is good
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['followers']), 2)
        # 确保按时间倒序
        ts0 = response.data['followers'][0]['created_at']
        ts1 = response.data['followers'][1]['created_at']
        self.assertEqual(ts0 > ts1, True)
        self.assertEqual(
            response.data['followers'][0]['user']['username'],
            'bob_follower_1'
        )
        self.assertEqual(
            response.data['followers'][1]['user']['username'],
            'bob_follower_0'
        )
