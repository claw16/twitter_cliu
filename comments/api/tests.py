from testing.testcases import TestCase
from rest_framework import status


COMMENT_URL = '/api/comments/'


class CommentApiTests(TestCase):
    def setUp(self):
        self.make_up_friendships()
        self.tweet = self.create_tweet(self.ann)

    def test_create(self):
        # anonymous users cannot create comments
        response = self.anonymous_client.post(COMMENT_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # tweet_id and content must be included
        response = self.ann_client.post(COMMENT_URL)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.ann_client.post(COMMENT_URL, {'tweet_id': self.tweet.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.ann_client.post(COMMENT_URL, {'content': '1'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # content len < 140
        response = self.ann_client.post(COMMENT_URL, {'content': '1' * 141, 'tweet_id': self.tweet.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual('content' in response.data['errors'], True)

        # a good comment
        response = self.ann_client.post(
            COMMENT_URL,
            {
                'content': '1',
                'tweet_id': self.tweet.id,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user']['id'], self.ann.id)
        self.assertEqual(response.data['tweet_id'], self.tweet.id)
        self.assertEqual(response.data['content'], '1')
