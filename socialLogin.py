
from flask import request
from flask_restful import Resource

from data import connect
from users import getUserByEmail

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
            fields = ['email', 'first_name', 'last_name', 'time_zone', 'google_auth_token',
                'social_id', 'google_refresh_token', 'access_expires_in', 'role']
            newUser = {}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    newUser[field] = fieldValue
            user = getUserByEmail(newUser['email'])
            if user:
                response['message'] = 'User already exists'
            else:
                newUserID = db.call('new_user_id')['result'][0]['new_id']
                newUser['user_uid'] = newUserID
                db.insert('users', newUser)
                response['message'] = 'successful'
                response['result'] = newUserID
        return response
