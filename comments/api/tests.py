from comments.models import Comment
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from testing.testcases import TestCase


COMMENT_URL = '/api/comments/'
TWEET_LIST_API = '/api/tweets/'
TWEET_DETAIL_API = '/api/tweets/{}/'
NEWSFEED_LIST_API = '/api/newsfeeds/'


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

    def test_destroy(self):
        comment = self.create_comment(self.ann, self.tweet)
        url = '{}{}/'.format(COMMENT_URL, comment.id)

        # 匿名无法删除
        response = self.anonymous_client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 非本人无法删除
        response = self.bob_client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 本人可以删除
        count = Comment.objects.count()
        response = self.ann_client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(count - 1, Comment.objects.count())

    def test_update(self):
        comment = self.create_comment(self.ann, self.tweet, 'before')
        another_tweet = self.create_tweet(self.bob)
        url = '{}{}/'.format(COMMENT_URL, comment.id)

        # 使用put的情况下
        # 匿名不可更新
        response = self.anonymous_client.put(url, {'content': 'after'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 非本人不可更新
        response = self.bob_client.put(url, {'content': 'after'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        comment.refresh_from_db()
        self.assertNotEqual(comment.content, 'after')

        # 不能更新除了 content 之外的内容，静默处理，只更新 content
        before_updated_at = comment.updated_at
        before_created_at = comment.created_at
        now = timezone.now()
        response = self.ann_client.put(
            url,
            {
                'content': 'after',  # 只有content会被更新
                'user_id': self.bob.id,
                'tweet_id': another_tweet.id,
                'created_at': now,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        comment.refresh_from_db()
        self.assertEqual(comment.content, 'after')
        self.assertEqual(comment.user, self.ann)
        self.assertEqual(comment.tweet, self.tweet)
        self.assertEqual(comment.created_at, before_created_at)
        self.assertNotEqual(comment.created_at, now)
        self.assertTrue(comment.updated_at > before_updated_at, True)

    def test_list(self):
        # 必须带 tweet_id
        response = self.anonymous_client.get(COMMENT_URL)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # 带上 tweet_id 可以访问
        # 一开始没有评论
        response = self.anonymous_client.get(COMMENT_URL, {
            'tweet_id': self.tweet.id,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['comments']), 0)

        # 评论按照时间顺序排序
        self.create_comment(self.ann, self.tweet, '1')
        self.create_comment(self.bob, self.tweet, '2')
        self.create_comment(self.bob, self.create_tweet(self.bob), '3')
        response = self.anonymous_client.get(COMMENT_URL, {
            'tweet_id': self.tweet.id,
        })
        self.assertEqual(len(response.data['comments']), 2)
        self.assertEqual(response.data['comments'][0]['content'], '1')
        self.assertEqual(response.data['comments'][1]['content'], '2')

        # 同时踢动 user_id 和 tweet_id 只有 tweet_id 会在 filter 中生效
        response = self.anonymous_client.get(COMMENT_URL, {
            'tweet_id': self.tweet.id,
            'user_id': self.ann.id,
        })
        self.assertEqual(len(response.data['comments']), 2)

    def test_comment_count(self):
        # test tweet detail API
        tweet = self.create_tweet(self.ann)
        url = TWEET_DETAIL_API.format(tweet.id)
        response = self.ann_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['comments_count'], 0)

        # test tweet list api
        self.create_comment(self.ann, tweet)
        response = self.bob_client.get(TWEET_LIST_API, {'user_id': self.ann.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['tweets'][0]['comments_count'], 1)

        # test newsfeed list api
        self.create_comment(self.bob, tweet)
        self.create_newsfeed(self.bob, tweet)
        response = self.bob_client.get(NEWSFEED_LIST_API)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['newsfeeds'][0]['tweet']['comments_count'], 2)
