from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APIClient
from testing.testcases import TestCase
from tweets.models import Tweet, TweetPhoto
from utils.paginations import EndlessPagination

# `/` is required otherwise --> 303 redirect
# /api/tweets/?user_id=id/ -> list user's tweets
TWEET_LIST_API = '/api/tweets/'
TWEET_CREATE_API = '/api/tweets/'
# /api/tweets/tweet_id/ -> list a tweet with id == tweet id
TWEET_RETRIEVE_API = '/api/tweets/{}/'


class TweetApiTests(TestCase):

    def setUp(self):
        self.anonymous_client = APIClient()

        self.user1 = self.create_user('user1', 'user1@jiuzhang.com')
        self.tweets1 = [self.create_tweet(self.user1) for _ in range(3)]
        self.user1_client = APIClient()
        self.user1_client.force_authenticate(self.user1)

        self.user2 = self.create_user('user2', 'user2@jiuzhang.com')
        self.tweets2 = [self.create_tweet(self.user2) for _ in range(2)]

    def test_list_api(self):
        # if not user_id, 400
        response = self.anonymous_client.get(TWEET_LIST_API)
        self.assertEqual(response.status_code, 400)

        # an anonymous user can view tweets
        response = self.anonymous_client.get(TWEET_LIST_API, {'user_id': self.user1.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 3)
        response = self.anonymous_client.get(TWEET_LIST_API, {'user_id': self.user2.id})
        self.assertEqual(len(response.data['results']), 2)

        # test tweets orders, 新创建的在前面
        self.assertEqual(response.data['results'][0]['id'], self.tweets2[1].id)
        self.assertEqual(response.data['results'][1]['id'], self.tweets2[0].id)

    def test_create_api(self):
        # must log in before creating
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

    def test_create_with_files(self):
        # post a tweet without 'files' in request data
        response = self.user1_client.post(TWEET_CREATE_API, {
            'content': 'a selfie',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TweetPhoto.objects.count(), 0)

        # upload empty file list
        response = self.user1_client.post(TWEET_CREATE_API, {
            'content': 'a selfie',
            'files': [],
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TweetPhoto.objects.count(), 0)

        # upload a single file
        file = SimpleUploadedFile(
            name='selfie.jpg',
            content=str.encode('a fake img'),
            content_type='image/jpeg',
        )
        response = self.user1_client.post(TWEET_CREATE_API, {
            'content': 'a selfie',
            'files': [file],
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TweetPhoto.objects.count(), 1)

        # upload multi photos
        files = [SimpleUploadedFile(
            name=f'selfie{i}.jpg',
            content=str.encode(f'selfie {i}'),
            content_type='image/jpeg',
        ) for i in range(2)]
        response = self.user1_client.post(TWEET_CREATE_API, {
            'content': '2 selfies',
            'files': files,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TweetPhoto.objects.count(), 3)

        # make sure photo urls are included by using retrieve api
        retrieve_url = TWEET_RETRIEVE_API.format(response.data['id'])
        response = self.user1_client.get(retrieve_url)
        self.assertEqual(len(response.data['photo_urls']), 2)
        self.assertEqual('selfie0' in response.data['photo_urls'][0], True)
        self.assertEqual('selfie1' in response.data['photo_urls'][1], True)
        # test again using list api
        response = self.anonymous_client.get(TWEET_LIST_API, {'user_id': self.user1.id})
        self.assertEqual(len(response.data['results'][0]['photo_urls']), 2)
        self.assertEqual('selfie0' in response.data['results'][0]['photo_urls'][0], True)
        self.assertEqual('selfie1' in response.data['results'][0]['photo_urls'][1], True)

        # upload more photos than the limit
        files = [SimpleUploadedFile(
            name=f'selfie{i}.jpg',
            content=str.encode(f'selfie {i}'),
            content_type='image/jpeg',
        ) for i in range(10)]
        response = self.user1_client.post(TWEET_CREATE_API, {
            'content': '10 selfies',
            'files': files,
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(TweetPhoto.objects.count(), 3)

    def test_retrieve(self):
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

    def test_endless_pagination(self):
        page_size = EndlessPagination.page_size

        # created page_size * 2 tweets, we have created self.tweet1 in setUp
        for i in range(page_size * 2 - len(self.tweets1)):
            self.tweets1.append(self.create_tweet(self.user1, f'tweet_{i}'))

        tweets = self.tweets1[::-1]

        # pull the first page
        response = self.user1_client.get(TWEET_LIST_API, {'user_id': self.user1.id})
        self.assertEqual(response.data['has_next_page'], True)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['results'][0]['id'], tweets[0].id)
        self.assertEqual(response.data['results'][1]['id'], tweets[1].id)
        self.assertEqual(response.data['results'][page_size - 1]['id'], tweets[page_size - 1].id)

        # pull the second page
        response = self.user1_client.get(TWEET_LIST_API, {
            'user_id': self.user1.id,
            'created_at__lt': tweets[page_size - 1].created_at,
        })
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['results'][0]['id'], tweets[page_size].id)
        self.assertEqual(response.data['results'][1]['id'], tweets[page_size + 1].id)
        self.assertEqual(response.data['results'][page_size - 1]['id'], tweets[2 * page_size - 1].id)

        # pull the latest newsfeeds
        response = self.user1_client.get(TWEET_LIST_API, {
            'created_at__gt': tweets[0].created_at,
            'user_id': self.user1.id,
        })
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), 0)

        new_tweet = self.create_tweet(self.user1, 'a new tweet comes in')

        response = self.user1_client.get(TWEET_LIST_API, {
            'created_at__gt': tweets[0].created_at,
            'user_id': self.user1.id,
        })
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], new_tweet.id)
