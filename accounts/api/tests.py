from accounts.models import UserProfile
from rest_framework.test import APIClient
from testing.testcases import TestCase


LOGIN_STATUS_URL = '/api/accounts/login_status/'
LOGIN_URL = '/api/accounts/login/'
LOGOUT_URL = '/api/accounts/logout/'
SIGNUP_URL = '/api/accounts/signup/'


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
        self.assertEqual(response.data['user']['email'], self.user.email)

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
        self.assertEqual(response.data['user']['email'], 'someone@jiuzhang.com')

        # test create user profile
        user_id = response.data['user']['id']
        profile = UserProfile.objects.filter(user_id=user_id).first()
        self.assertNotEqual(profile, None)

        # test login status after signup
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)
