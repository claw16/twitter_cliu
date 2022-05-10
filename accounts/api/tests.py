from accounts.models import UserProfile
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APIClient
from testing.testcases import TestCase

LOGIN_STATUS_URL = '/api/accounts/login_status/'
LOGIN_URL = '/api/accounts/login/'
LOGOUT_URL = '/api/accounts/logout/'
SIGNUP_URL = '/api/accounts/signup/'
USER_PROFILE_DETAIL_URL = '/api/profiles/{}/'


class AccountApiTests(TestCase):

    def setUp(self) -> None:
        # This function will be called while every test function is executed
        self.client = APIClient()
        self.user = self.create_user(
            username='admin',
            email='admin@jiuzhang.com',
            password='correct password',
        )

    def test_login(self):
        # login should be a post request, test whether it handles a get request properly
        response = self.client.get(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password',
        })
        self.assertEqual(response.status_code, 405)

        # test wrong username
        response = self.client.post(LOGIN_URL, {
            'username': "bad_user",
            'password': 'correct password',
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['errors']['username'][0], 'User does not exist')

        # test wrong password
        response = self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'incorrect password',
        })
        self.assertEqual(response.status_code, 400)

        # test logging status before login
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], False)

        # test correct username and password with post request
        response = self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password',
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.data['user'], None)
        self.assertEqual(response.data['user']['id'], self.user.id)

        # test logging status after login
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)

    def test_logout(self):
        # login first
        response = self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password',
        })
        self.assertEqual(response.status_code, 200)

        # test a get request
        response = self.client.get(LOGOUT_URL)
        self.assertEqual(response.status_code, 405)

        # logout
        response = self.client.post(LOGOUT_URL)
        self.assertEqual(response.status_code, 200)

        # verify that we have successfully logged out
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['has_logged_in'], False)

    def test_signup(self):
        data = {
            'username': 'someone',
            'email': 'someone@jiuzhang.com',
            'password': 'some password',
        }

        # test get request
        response = self.client.get(SIGNUP_URL)
        self.assertEqual(response.status_code, 405)

        # test a short username
        response = self.client.post(SIGNUP_URL, {
            'username': 's',
            'email': 'short@gmail.com',
            'password': 'apassword',
        })
        self.assertEqual(response.status_code, 400)

        # test a long username
        response = self.client.post(SIGNUP_URL, {
            'username': 'this_user_name_is_super_long',
            'email': 'short@gmail.com',
            'password': 'apassword',
        })
        self.assertEqual(response.status_code, 400)

        # test an invalid email
        response = self.client.post(SIGNUP_URL, {
            'username': 'someone',
            'email': 'not an email',
            'password': 'apassword',
        })
        self.assertEqual(response.status_code, 400)

        # test a short password
        response = self.client.post(SIGNUP_URL, {
            'username': 'someone',
            'email': 'someone@jiuzhang.com',
            'password': 'pw',
        })
        self.assertEqual(response.status_code, 400)

        # test a long password
        response = self.client.post(SIGNUP_URL, {
            'username': 'someone',
            'email': 'someone@jiuzhang.com',
            'password': 'this is a super long password',
        })
        self.assertEqual(response.status_code, 400)

        # test login status before signup
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], False)

        # test a good signup
        response = self.client.post(SIGNUP_URL, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['username'], 'someone')

        # test create user profile
        user_id = response.data['user']['id']
        profile = UserProfile.objects.filter(user_id=user_id).first()
        self.assertNotEqual(profile, None)

        # test login status after signup
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)


class UserProfileApiTests(TestCase):
    def setUp(self):
        self.create_user_and_client()

    def test_update(self):
        ann_profile = self.ann.profile
        ann_profile.nickname = 'old_nickname'
        ann_profile.save()
        url = USER_PROFILE_DETAIL_URL.format(ann_profile.id)

        self.assertEqual(ann_profile.avatar, None)

        # anonymous user cannot update profile
        response = self.anonymous_client.put(url, {
            'nickname': 'anonymous',
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], 'Authentication credentials were not provided.')

        # test profile can only be modified by the profile owner
        response = self.bob_client.put(url, {
            'nickname': 'bob nickname',
        })
        self.assertEqual(ann_profile.nickname, 'old_nickname')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], 'You do not have the permission to access this object')

        # update nickname
        response = response = self.ann_client.put(url, {
            'nickname': 'new_nickname',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ann_profile.refresh_from_db()
        self.assertEqual(ann_profile.nickname, 'new_nickname')

        # update avatar
        response = self.ann_client.put(url, {
            'avatar': SimpleUploadedFile(
                name='my-avatar.jpg',
                content=str.encode('a fake img'),  # content requires a byte type
                content_type='image/jpeg',
            ),
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('my-avatar' in response.data['avatar'], True)
        ann_profile.refresh_from_db()
        self.assertIsNotNone(ann_profile.avatar)
