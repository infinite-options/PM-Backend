
from flask import request
from flask_restful import Resource

from data import connect
from users import getUserByEmail, createUser
from security import createTokens

class UserSocialLogin(Resource):
    def get(self, email):
        response = {}
        with connect() as db:
            user = getUserByEmail(email)
            if user:
                user_unique_id = user.get('user_uid')
                google_auth_token = user.get('google_auth_token')
                response['result'] = user_unique_id, google_auth_token
                response['message'] = 'Correct Email'
            else:
                response['result'] = False
                response['message'] = 'Email ID doesnt exist'
        return response

class UserSocialSignup(Resource):
    def post(self):
        response = {}
        with connect() as db:
            data = request.get_json(force=True)

            email = data.get('email')
            phoneNumber = data.get('phone_number')
            firstName = data.get('first_name')
            lastName = data.get('last_name')
            role = data.get('role')
            google_auth_token = data.get('google_auth_token')
            google_refresh_token = data.get('google_refresh_token')
            social_id = data.get('social_id')
            access_expires_in = data.get('access_expires_in')
            password = data.get('password')
            user = getUserByEmail(email)
            if user:
                response['message'] = 'User already exists'
            else:
                user = createUser(firstName, lastName, phoneNumber, email, password, role,
                    google_auth_token, google_refresh_token, social_id, access_expires_in)
                response['message'] = 'Signup success'
                response['code'] = 200
                response['result'] = createTokens(user)
                # newUserID = db.call('new_user_id')['result'][0]['new_id']
                # newUser['user_uid'] = newUserID
                # db.insert('users', newUser)
                # response['message'] = 'successful'
                # response['result'] = newUserID
        return response
