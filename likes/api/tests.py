from testing.testcases import TestCase
from rest_framework import status


LIKE_BASE_URL = '/api/likes/'
LIKE_CANCEL_URL = '/api/likes/cancel/'
COMMENT_LIST_API = '/api/comments/'
TWEET_LIST_API = '/api/tweets/'
TWEET_DETAIL_API = '/api/tweets/{}/'
NEWSFEED_LIST_API = '/api/newsfeeds/'


class LikeApiTests(TestCase):
    def setUp(self):
        self.create_user_and_client()

    def test_tweet_likes(self):
        tweet = self.create_tweet(self.ann)
        data = {'content_type': 'tweet', 'object_id': tweet.id}

        # anonymous is not allowed
        response = self.anonymous_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # get is not allowed
        response = self.ann_client.get(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # post
        response = self.ann_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(tweet.like_set.count(), 1)

        # duplicate likes
        self.ann_client.post(LIKE_BASE_URL, data)
        self.assertEqual(tweet.like_set.count(), 1)
        self.bob_client.post(LIKE_BASE_URL, data)
        self.assertEqual(tweet.like_set.count(), 2)

        likes = tweet.like_set
        self.assertEqual(likes[0].user, self.bob)
        self.assertEqual(likes[1].user, self.ann)

    def test_comment_likes(self):
        tweet = self.create_tweet(self.ann)
        comment = self.create_comment(self.bob, tweet)
        data = {'content_type': 'comment', 'object_id': comment.id}

        # anonymous is not allowed
        response = self.anonymous_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # get is not allowed
        response = self.ann_client.get(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # wrong content_type
        response = self.ann_client.post(LIKE_BASE_URL, {
            'content_type': 'wrong_type',
            'object_id': comment.id,
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual('content_type' in response.data['errors'], True)

        # wrong object id
        response = self.ann_client.post(LIKE_BASE_URL, {
            'content_type': 'comment',
            'object_id': -1,
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual('object_id' in response.data['errors'], True)

        # post
        response = self.ann_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(comment.like_set.count(), 1)

        # duplicate likes
        self.ann_client.post(LIKE_BASE_URL, data)
        self.assertEqual(comment.like_set.count(), 1)
        self.bob_client.post(LIKE_BASE_URL, data)
        self.assertEqual(comment.like_set.count(), 2)

        likes = comment.like_set
        self.assertEqual(likes[0].user, self.bob)
        self.assertEqual(likes[1].user, self.ann)

    def test_cancel(self):
        # create likes for a tweet and a comment
        tweet = self.create_tweet(self.ann)
        comment = self.create_comment(self.bob, tweet, 'bob left a comment')
        like_tweet_data = {'content_type': 'tweet', 'object_id': tweet.id}
        like_comment_data = {'content_type': 'comment', 'object_id': comment.id}
        self.ann_client.post(LIKE_BASE_URL, like_tweet_data)
        self.bob_client.post(LIKE_BASE_URL, like_comment_data)
        self.assertEqual(tweet.like_set.count(), 1)
        self.assertEqual(comment.like_set.count(), 1)

        # login required
        response = self.anonymous_client.post(LIKE_CANCEL_URL, like_tweet_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # get is not allowed
        response = self.ann_client.get(LIKE_CANCEL_URL, like_tweet_data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # wrong content type
        response = self.ann_client.post(LIKE_CANCEL_URL, {
            'content_type': 'wrong',
            'object_id': tweet.id,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual('content_type' in response.data['errors'], True)

        # wrong object id
        response = self.ann_client.post(LIKE_CANCEL_URL, {
            'content_type': 'tweet',
            'object_id': -1,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual('object_id' in response.data['errors'], True)

        # bob hasn't liked the tweet before
        response = self.bob_client.post(LIKE_CANCEL_URL, like_tweet_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(tweet.like_set.count(), 1)
        self.assertEqual(comment.like_set.count(), 1)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(response.data['deleted'], 0)

        # ann cancelled the tweet's like
        response = self.ann_client.post(LIKE_CANCEL_URL, like_tweet_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(tweet.like_set.count(), 0)
        self.assertEqual(comment.like_set.count(), 1)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(response.data['deleted'], 1)

        # ann hasn't liked comment before
        response = self.ann_client.post(LIKE_CANCEL_URL, like_comment_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(tweet.like_set.count(), 0)
        self.assertEqual(comment.like_set.count(), 1)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(response.data['deleted'], 0)

        # bob cancelled the comment's like
        response = self.bob_client.post(LIKE_CANCEL_URL, like_comment_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(tweet.like_set.count(), 0)
        self.assertEqual(comment.like_set.count(), 0)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(response.data['deleted'], 1)

    def test_likes_in_comments_api(self):
        tweet = self.create_tweet(self.ann)
        comment = self.create_comment(self.ann, tweet)

        # test anonymous
        response = self.anonymous_client.get(COMMENT_LIST_API, {'tweet_id': tweet.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['comments'][0]['has_liked'], False)
        self.assertEqual(response.data['comments'][0]['likes_count'], 0)

        # test comments list api
        response = self.bob_client.get(COMMENT_LIST_API, {'tweet_id': tweet.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['comments'][0]['has_liked'], False)
        self.assertEqual(response.data['comments'][0]['likes_count'], 0)
        self.create_like(self.bob, comment)
        response = self.bob_client.get(COMMENT_LIST_API, {'tweet_id': tweet.id})
        self.assertEqual(response.data['comments'][0]['has_liked'], True)
        self.assertEqual(response.data['comments'][0]['likes_count'], 1)

        # test tweet detail api
        self.create_like(self.ann, comment)
        url = TWEET_DETAIL_API.format(tweet.id)
        response = self.bob_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['comments'][0]['has_liked'], True)
        self.assertEqual(response.data['comments'][0]['likes_count'], 2)

    def test_likes_in_tweets_api(self):
        tweet = self.create_tweet(self.ann)

        # test tweet detail api
        url = TWEET_DETAIL_API.format(tweet.id)
        response = self.bob_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['has_liked'], False)
        self.assertEqual(response.data['likes_count'], 0)
        self.create_like(self.bob, tweet)
        response = self.bob_client.get(url)
        self.assertEqual(response.data['has_liked'], True)
        self.assertEqual(response.data['likes_count'], 1)

        # test tweets list api
        response = self.bob_client.get(TWEET_LIST_API, {'user_id': self.ann.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['has_liked'], True)
        self.assertEqual(response.data['results'][0]['likes_count'], 1)

        # test newsfeeds list api
        self.create_like(self.ann, tweet)
        self.create_newsfeed(self.bob, tweet)
        response = self.bob_client.get(NEWSFEED_LIST_API)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['newsfeeds'][0]['tweet']['has_liked'], True)
        self.assertEqual(response.data['newsfeeds'][0]['tweet']['likes_count'], 2)

        # test likes details
        url = TWEET_DETAIL_API.format(tweet.id)
        response = self.bob_client.get(url)
        self.assertEqual(len(response.data['likes']), 2)
        self.assertEqual(response.data['likes'][0]['user']['id'], self.ann.id)
        self.assertEqual(response.data['likes'][1]['user']['id'], self.bob.id)
