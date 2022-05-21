from testing.testcases import TestCase


class CommentModelTests(TestCase):
    def setUp(self):
        self.clear_cache()
        self.user = self.create_user('ann')
        self.tweet = self.create_tweet(self.user)
        self.comment = self.create_comment(self.user, self.tweet)

    def test_comment(self):
        self.assertNotEqual(self.comment.__str__(), None)

    def test_like_set(self):
        first_like = self.create_like(self.user, self.comment)
        self.assertEqual(len(self.comment.like_set), 1)

        second_like = self.create_like(self.user, self.comment)
        self.assertEqual(len(self.comment.like_set), 1)

        self.bob = self.create_user('bob')
        self.create_like(self.bob, self.comment)
        self.assertEqual(len(self.comment.like_set), 2)

        likes = self.comment.like_set
        self.assertEqual(likes[0].user, self.bob)
        self.assertEqual(likes[1].user, self.user)
