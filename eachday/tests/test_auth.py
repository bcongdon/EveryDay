import unittest
import json
from freezegun import freeze_time
from datetime import datetime, timedelta

from eachday.tests.base import BaseTestCase
from eachday.models import User, BlacklistToken
from eachday import db


class TestAuthRoutes(BaseTestCase):
    def test_registration(self):
        ''' Test for user registration '''
        response = self.client.post(
            '/register',
            data=json.dumps(dict(
                email='foo@bar.com',
                password='123456',
                name='joe'
            )),
            content_type='application/json'
        )
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['message'], 'Successfully registered.')
        self.assertIn('auth_token', data)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.status_code, 201)

    def test_registration_missing_fields(self):
        ''' Test for user registration with missing fields '''
        response = self.client.post(
            '/register',
            data=json.dumps(dict(
                email='foo@bar.com',
            )),
            content_type='application/json'
        )
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertIn('error', data)
        self.assertIn('password', data['error'])
        self.assertIn('name', data['error'])
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.status_code, 400)

    def test_registered_with_already_registered_user(self):
        ''' Test registration with already registered email'''
        user = User(
            email='foo@bar.com',
            password='test',
            name='joe'
        )
        db.session.add(user)
        db.session.commit()

        response = self.client.post(
            '/register',
            data=json.dumps(dict(
                email='foo@bar.com',
                password='123456',
                name='moe'
            )),
            content_type='application/json'
        )
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(
            data['error'], 'User already exists.')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.status_code, 400)

    def test_registered_user_login(self):
        ''' Test for login of registered-user login '''
        # user registration
        resp_register = self.client.post(
            '/register',
            data=json.dumps({
                'email': 'joe@gmail.com',
                'password': '123456',
                'name': 'joe'
            }),
            content_type='application/json',
        )
        data_register = json.loads(resp_register.data.decode())
        self.assertEqual(data_register['status'], 'success')
        self.assertEqual(
            data_register['message'], 'Successfully registered.'
        )
        self.assertIn('auth_token', data_register)
        self.assertEqual(resp_register.content_type, 'application/json')
        self.assertEqual(resp_register.status_code, 201)

        # registered user login
        response = self.client.post(
            '/login',
            data=json.dumps({
                'email': 'joe@gmail.com',
                'password': '123456'
            }),
            content_type='application/json'
        )
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['message'], 'Successfully logged in.')
        self.assertIn('auth_token', data_register)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.status_code, 200)

    def test_incorrect_password(self):
        ''' Test for login rejection of registered-user with bad password '''
        # user registration
        resp_register = self.client.post(
            '/register',
            data=json.dumps({
                'email': 'joe@gmail.com',
                'password': '123456',
                'name': 'joe'
            }),
            content_type='application/json',
        )
        data_register = json.loads(resp_register.data.decode())
        self.assertEqual(data_register['status'], 'success')
        self.assertEqual(
            data_register['message'], 'Successfully registered.'
        )
        self.assertIn('auth_token', data_register)
        self.assertEqual(resp_register.content_type, 'application/json')
        self.assertEqual(resp_register.status_code, 201)

        # login with bad password
        response = self.client.post(
            '/login',
            data=json.dumps({
                'email': 'joe@gmail.com',
                'password': 'invalid password'
            }),
            content_type='application/json'
        )
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['error'], 'Invalid login.')
        self.assertNotIn('auth_token', data)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.status_code, 401)

    def test_non_registered_user_login(self):
        ''' Test for login of non-registered user '''
        response = self.client.post(
            '/login',
            data=json.dumps({
                'email': 'joe@gmail.com',
                'password': '123456'
            }),
            content_type='application/json'
        )
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['error'], 'User does not exist.')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.status_code, 404)

    def test_logout_blacklist_token(self):
        ''' Test that logging out blacklists current token '''
        user = User(
            email='foo@bar.com',
            password='test',
            name='joe'
        )
        db.session.add(user)
        db.session.commit()
        auth_token = user.encode_auth_token(user.id).decode()

        response = self.client.post(
            '/logout',
            headers={
                'Authorization': 'Bearer ' + auth_token
            }
        )
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['message'], 'Successfully logged out')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.status_code, 200)

        blacklist = BlacklistToken.query.filter_by(token=auth_token).first()
        self.assertTrue(blacklist is not None)

    def test_blacklist_token_rejection(self):
        ''' Test that blacklisted auth tokens are rejected '''

        # Create user / auth_token
        user = User(
            email='foo@bar.com',
            password='test',
            name='joe'
        )
        db.session.add(user)
        db.session.commit()
        auth_token = user.encode_auth_token(user.id).decode()

        # Blacklist auth_token
        blacklist_token = BlacklistToken(token=auth_token)
        db.session.add(blacklist_token)
        db.session.commit()

        # Check to make sure that the blacklisted token cannot be used
        response = self.client.get(
            '/user',
            headers={
                'Authorization': 'Bearer ' + auth_token
            }
        )
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['error'],
                         'Token blacklisted. Please log in again.')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.status_code, 401)

    def test_invalid_token_rejection(self):
        ''' Test that using an invalid token gives correct error '''
        auth_token = 'not_an_auth_token ;)'

        response = self.client.get(
            '/user',
            headers={
                'Authorization': 'Bearer ' + auth_token
            }
        )
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['error'], 'Invalid token. Please log in again.')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.status_code, 401)

    def test_expired_token_rejection(self):
        ''' Test that using an expired token gives correct error '''
        with freeze_time(datetime.utcnow()) as frozen_datetime:
            user = User(
                email='foo@bar.com',
                password='test',
                name='joe'
            )
            db.session.add(user)
            db.session.commit()
            auth_token = user.encode_auth_token(user.id).decode()

            # Jump time to just after token has expired
            td = timedelta(days=1, seconds=1)
            frozen_datetime.move_to(datetime.utcnow() + td)

            response = self.client.get(
                '/user',
                headers={
                    'Authorization': 'Bearer ' + auth_token
                }
            )
            data = json.loads(response.data.decode())
            self.assertEqual(data['status'], 'error')
            self.assertEqual(
                data['error'], 'Signature expired. Please log in again.'
            )
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.status_code, 401)

if __name__ == '__main__':
    unittest.main()
