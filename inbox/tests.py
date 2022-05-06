from inbox.services import NotificationService
from notifications.models import Notification
from testing.testcases import TestCase


class NotificationServiceTests(TestCase):
    def setUp(self):
        self.create_user_and_client()
        self.ann_tweet = self.create_tweet(self.ann)

    def test_send_comment_notifications(self):
        # no notification if tweet user == comment user
        comment = self.create_comment(self.ann, self.ann_tweet)
        NotificationService.send_comment_notification(comment)
        self.assertEqual(Notification.objects.count(), 0)

        # send notification if tweet user != comment user
        comment = self.create_comment(self.bob, self.ann_tweet)
        NotificationService.send_comment_notification(comment)
        self.assertEqual(Notification.objects.count(), 1)

    def test_send_like_notifications(self):
        # no notification if tweet user == comment user
        like = self.create_like(self.ann, self.ann_tweet)
        NotificationService.send_like_notification(like)
        self.assertEqual(Notification.objects.count(), 0)

        # send notification if tweet user != comment user
        like = self.create_like(self.bob, self.ann_tweet)
        NotificationService.send_like_notification(like)
        self.assertEqual(Notification.objects.count(), 1)
