from notifications.models import Notification
from rest_framework import status
from testing.testcases import TestCase


COMMENT_URL = '/api/comments/'
LIKE_URL = '/api/likes/'
NOTIFICATION_URL = '/api/notifications/'
UNREAD_COUNT_URL = '/api/notifications/unread-count/'
READ_ALL_URL = '/api/notifications/mark-all-as-read/'


class NotificationsTests(TestCase):
    def setUp(self):
        self.create_user_and_client()
        self.bob_tweet = self.create_tweet(self.bob)

    def test_comment_create_api_trigger_notification(self):
        self.assertEqual(Notification.objects.count(), 0)
        self.ann_client.post(COMMENT_URL, {
            'tweet_id': self.bob_tweet.id,
            'content': 'a ha',
        })
        self.assertEqual(Notification.objects.count(), 1)

    def test_like_create_api_trigger_notification(self):
        self.assertEqual(Notification.objects.count(), 0)
        self.ann_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': self.bob_tweet.id,
        })
        self.assertEqual(Notification.objects.count(), 1)


class NotificationApiTests(TestCase):
    def setUp(self):
        self.create_user_and_client()
        self.ann_tweet = self.create_tweet(self.ann)

    def test_unread_count(self):
        self.bob_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': self.ann_tweet.id,
        })

        response = self.ann_client.get(UNREAD_COUNT_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['unread_count'], 1)

        comment = self.create_comment(self.ann, self.ann_tweet)
        self.bob_client.post(LIKE_URL, {
            'content_type': 'comment',
            'object_id': comment.id,
        })
        response = self.ann_client.get(UNREAD_COUNT_URL)
        self.assertEqual(response.data['unread_count'], 2)

    def test_mark_all_as_read(self):
        self.bob_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': self.ann_tweet.id,
        })
        comment = self.create_comment(self.ann, self.ann_tweet)
        self.bob_client.post(LIKE_URL, {
            'content_type': 'comment',
            'object_id': comment.id,
        })

        response = self.ann_client.get(UNREAD_COUNT_URL)
        self.assertEqual(response.data['unread_count'], 2)
        response = self.bob_client.get(UNREAD_COUNT_URL)
        self.assertEqual(response.data['unread_count'], 0)

        # anonymous is forbidden
        response = self.anonymous_client.get(NOTIFICATION_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # bob doesn't have any notification
        response = self.bob_client.get(NOTIFICATION_URL)
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # ann sees 2 notifications
        response = self.ann_client.get(NOTIFICATION_URL)
        self.assertEqual(response.data['count'], 2)

        # mark one as read and one is left
        notification = self.ann.notifications.first()  # TODO: User.notifications?
        notification.unread = False
        notification.save()
        response = self.ann_client.get(NOTIFICATION_URL)
        self.assertEqual(response.data['count'], 2)
        response = self.ann_client.get(NOTIFICATION_URL, {'unread': True})
        self.assertEqual(response.data['count'], 1)
        response = self.ann_client.get(NOTIFICATION_URL, {'unread': False})
        self.assertEqual(response.data['count'], 1)

        self.bob_client.post(READ_ALL_URL)
        response = self.ann_client.get(NOTIFICATION_URL, {'unread': True})
        self.assertEqual(response.data['count'], 1)
        self.ann_client.post(READ_ALL_URL)
        response = self.ann_client.get(NOTIFICATION_URL, {'unread': True})
        self.assertEqual(response.data['count'], 0)

    def test_update(self):
        self.bob_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': self.ann_tweet.id,
        })
        comment = self.create_comment(self.ann, self.ann_tweet)
        self.bob_client.post(LIKE_URL, {
            'content_type': 'comment',
            'object_id': comment.id,
        })
        notification = self.ann.notifications.first()
        url = '/api/notifications/{}/'.format(notification.id)

        # post is not allowed
        response = self.ann_client.post(url, {'unread': False})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # anonymous is not allowed
        response = self.anonymous_client.put(url, {'unread': False})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # notification status cannot be modified by another user
        response = self.bob_client.put(url, {'unread': False})
        # 404 not 403 because the queryset is filtered based on current login user
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # a good mark-as-read
        response = self.ann_client.put(url, {'unread': False})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.ann_client.get(UNREAD_COUNT_URL)
        self.assertEqual(response.data['unread_count'], 1)

        # mark it as unread again
        self.ann_client.put(url, {'unread': True})
        response = self.ann_client.get(UNREAD_COUNT_URL)
        self.assertEqual(response.data['unread_count'], 2)

        # 'unread' is required
        response = self.ann_client.put(url, {'verb': 'verb'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # not allow to modify other info except 'unread'
        response = self.ann_client.put(url, {'unread': True, 'verb': 'a new verb'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        notification.refresh_from_db()
        self.assertNotEqual(notification.verb, 'a new verb')
