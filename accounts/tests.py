from testing.testcases import TestCase
from accounts.models import UserProfile


class UserProfileTests(TestCase):
    def setUp(self):
        self.clear_cache()

    def test_profile_property(self):
        ann = self.create_user('ann')
        self.assertEqual(UserProfile.objects.count(), 0)
        ann_profile = ann.profile
        self.assertEqual(isinstance(ann_profile, UserProfile), True)
        self.assertEqual(UserProfile.objects.count(), 1)
