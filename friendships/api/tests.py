from friendships.api.paginations import FriendshipPagination
from friendships.models import Friendship
from rest_framework import status
from testing.testcases import TestCase


FOLLOW_URL = '/api/friendships/{}/follow/'
UNFOLLOW_URL = '/api/friendships/{}/unfollow/'
FOLLOWERS_URL = '/api/friendships/{}/followers/'
FOLLOWINGS_URL = '/api/friendships/{}/followings/'


class FriendshipApiTests(TestCase):
    def setUp(self) -> None:
        self.make_up_friendships()
        self.max_page_size = FriendshipPagination.max_page_size
        self.page_size = FriendshipPagination.page_size

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
        # follow a non-existing user
        response = self.ann_client.post(FOLLOW_URL.format(111))
        self.assertEqual(response.status_code, 404)
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
        self.assertEqual(len(response.data['results']), 3)
        ts0 = response.data['results'][0]['created_at']
        ts1 = response.data['results'][1]['created_at']
        ts2 = response.data['results'][2]['created_at']
        self.assertEqual(ts0 > ts1 > ts2, True)
        self.assertEqual(
            response.data['results'][0]['user']['username'],
            'bob_following_2'
        )
        self.assertEqual(
            response.data['results'][1]['user']['username'],
            'bob_following_1'
        )
        self.assertEqual(
            response.data['results'][2]['user']['username'],
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
        self.assertEqual(len(response.data['results']), 2)
        # 确保按时间倒序
        ts0 = response.data['results'][0]['created_at']
        ts1 = response.data['results'][1]['created_at']
        self.assertEqual(ts0 > ts1, True)
        self.assertEqual(
            response.data['results'][0]['user']['username'],
            'bob_follower_1'
        )
        self.assertEqual(
            response.data['results'][1]['user']['username'],
            'bob_follower_0'
        )

    def test_following_pagination(self):
        for i in range(self.page_size * 2):
            following = self.create_user(f'ann_following_{i}')
            Friendship.objects.create(from_user=self.ann, to_user=following)
            if following.id % 2 == 0:
                Friendship.objects.create(from_user=self.bob, to_user=following)

        url = FOLLOWINGS_URL.format(self.ann.id)
        self._test_friendship_pagination(url)

        # anonymous user can view however he can't follow
        response = self.anonymous_client.get(url, {'page': 1})
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], False)

        # Bob has followed users with even id
        response = self.bob_client.get(url, {'page': 1})
        for result in response.data['results']:
            has_followed = result['user']['id'] % 2 == 0
            self.assertEqual(result['has_followed'], has_followed)

        # Ann has followed all her following users
        response = self.ann_client.get(url, {'page': 1})
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], True)

    def test_follower_pagination(self):
        # create 2 * page_size users, all follow Ann, Bob follows half of them
        for i in range(self.page_size * 2):
            follower = self.create_user(f'ann_follower_{i}')
            Friendship.objects.create(from_user=follower, to_user=self.ann)
            if follower.id % 2 == 0:
                Friendship.objects.create(from_user=self.bob, to_user=follower)

        url = FOLLOWERS_URL.format(self.ann.id)
        self._test_friendship_pagination(url)

        # anonymous user can view the list, however he can't follow anyone
        response = self.anonymous_client.get(url, {'page': 1})
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], False)

        # Bob has followed users with even id
        response = self.bob_client.get(url, {'page': 1})
        for result in response.data['results']:
            has_followed = result['user']['id'] % 2 == 0
            self.assertEqual(result['has_followed'], has_followed)


    def _test_friendship_pagination(self, url):
        response = self.anonymous_client.get(url, {'page': 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), self.page_size)
        self.assertEqual(response.data['total_pages'], 2)
        self.assertEqual(response.data['total_results'], self.page_size * 2)
        self.assertEqual(response.data['page_number'], 1)
        self.assertEqual(response.data['has_next_page'], True)

        response = self.anonymous_client.get(url, {'page': 2})
        self.assertEqual(len(response.data['results']), self.page_size)
        self.assertEqual(response.data['total_pages'], 2)
        self.assertEqual(response.data['total_results'], self.page_size * 2)
        self.assertEqual(response.data['page_number'], 2)
        self.assertEqual(response.data['has_next_page'], False)

        response = self.anonymous_client.get(url, {'page': 3})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # test customized page_size cannot exceed max_page_size
        response = self.anonymous_client.get(url, {'page': 1, 'size': self.max_page_size + 1})
        self.assertEqual(len(response.data['results']), self.max_page_size)
        self.assertEqual(response.data['total_pages'], 2)
        self.assertEqual(response.data['total_results'], self.page_size * 2)
        self.assertEqual(response.data['page_number'], 1)
        self.assertEqual(response.data['has_next_page'], True)

        # test a valid customized page size
        response = self.anonymous_client.get(url, {'page': 1, 'size': 2})
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['total_pages'], self.page_size)
        self.assertEqual(response.data['total_results'], self.page_size * 2)
        self.assertEqual(response.data['page_number'], 1)
        self.assertEqual(response.data['has_next_page'], True)
