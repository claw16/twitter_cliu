from rest_framework.test import APIClient
from testing.testcases import TestCase
from tweets.models import Tweet


# `/` is required otherwise --> 303 redirect
TWEET_LIST_API = '/api/tweets/'
TWEET_CREATE_API = '/api/tweets/'
TWEET_RETRIEVE_API = '/api/tweets/{}/'


class TweetApiTests(TestCase):

    def setUp(self):
        self.anonymous_client = APIClient()

        self.user1 = self.create_user('user1', 'user1@jiuzhang.com')
        self.tweets1 = [self.create_tweet(self.user1) for i in range(3)]
        self.user1_client = APIClient()
        self.user1_client.force_authenticate(self.user1)

        self.user2 = self.create_user('user2', 'user2@jiuzhang.com')
        self.tweets2 = [self.create_tweet(self.user2) for i in range(2)]


    def test_list_api(self):
        # if not user_id, 400
        response = self.anonymous_client.get(TWEET_LIST_API)
        self.assertEqual(response.status_code, 400)

        # an anonymous user can view tweets
        response = self.anonymous_client.get(TWEET_LIST_API, {'user_id': self.user1.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['tweets']), 3)
        response = self.anonymous_client.get(TWEET_LIST_API, {'user_id': self.user2.id})
        self.assertEqual(len(response.data['tweets']), 2)

        # test tweets orders, 新创建的在前面
        self.assertEqual(response.data['tweets'][0]['id'], self.tweets2[1].id)
        self.assertEqual(response.data['tweets'][1]['id'], self.tweets2[0].id)


    def test_create_api(self):
        # must login before creating
        response = self.anonymous_client.post(TWEET_CREATE_API)
        self.assertEqual(response.status_code, 403)

        # content is required
        response = self.user1_client.post(TWEET_CREATE_API)
        self.assertEqual(response.status_code, 400)

        # test content length restrictions
        response = self.user1_client.post(TWEET_CREATE_API, {'content': '1'})
        self.assertEqual(response.status_code, 400)
        response = self.user1_client.post(TWEET_CREATE_API, {'content': '1' * 141})
        self.assertEqual(response.status_code, 400)

        # a good tweets
        tweets_count = Tweet.objects.count()
        response = self.user1_client.post(TWEET_CREATE_API, {
            'content': "hello world, this is a good tweet."
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['id'], self.user1.id)
        self.assertEqual(Tweet.objects.count(), tweets_count + 1)

    def test_retieve(self):
        # tweet with id=-1 doesn't exist
        url = TWEET_RETRIEVE_API.format(-1)
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 404)

        # 获取某个 tweet 的时候会把 comments 也得到
        tweet = self.create_tweet(self.user1)
        url = TWEET_RETRIEVE_API.format(tweet.id)
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['comments']), 0)

        self.create_comment(self.user2, tweet, 'holy crab')
        self.create_comment(self.user1, tweet, 'hmm..')
        # create a comment on a new tweet to make sure its comments won't be
        # obtained by retrieving the previous tweet
        self.create_comment(self.user1, self.create_tweet(self.user2), '...')
        response = self.anonymous_client.get(url)
        self.assertEqual(len(response.data['comments']), 2)

        # tweet contains user avatar and nickname now
        profile = self.user1.profile
        self.assertEqual(response.data['user']['nickname'], profile.nickname)
        self.assertEqual(response.data['user']['avatar_url'], None)
