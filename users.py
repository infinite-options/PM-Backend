
from flask import request
from flask_restful import Resource

from data import connect
from security import createSalt, createHash, createTokens

def getUserByEmail(email):
    with connect() as db:
        result = db.select('users', {'email': email})
        if len(result['result']) > 0:
            return result['result'][0]

def createUser(firstName, lastName, phoneNumber, email, password, role):
    with connect() as db:
        newUserID = db.call('new_user_id')['result'][0]['new_id']
        passwordSalt = createSalt()
        passwordHash = createHash(password, passwordSalt)
        newUser = {
            'user_uid': newUserID,
            'first_name': firstName,
            'last_name': lastName,
            'phone_number': phoneNumber,
            'email': email,
            'password_salt': passwordSalt,
            'password_hash': passwordHash,
            'role': role
        }
        response = db.insert('users', newUser)
        return newUser

class Login(Resource):
    def post(self):
        response = {}
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        user = getUserByEmail(email)
        if user:
            passwordSalt = user['password_salt']
            passwordHash = createHash(password, passwordSalt)
            if passwordHash == user['password_hash']:
                response['message'] = 'Login successful'
                response['code'] = 200
                response['result'] = createTokens(user)
            else:
                response['message'] = 'Incorrect password'
                response['code'] = 401
        else:
            response['message'] = 'Email not found'
            response['code'] = 404
        return response

class Users(Resource):
    def get(self):
        response = {}
        filters = ['user_uid', 'email', 'role']
        where = {}
        for filter in filters:
            filterValue = request.args.get(filter)
            if filterValue is not None:
                where[filter] = filterValue
        with connect() as db:
            response = db.select('users', where)
        return response
    def post(self):
        response = {}
        data = request.get_json()
        firstName = data.get('first_name')
        lastName = data.get('last_name')
        phoneNumber = data.get('phone_number')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role')
        user = getUserByEmail(email)
        if user:
            response['message'] = 'Email taken'
            response['code'] = 409
        else:
            user = createUser(firstName, lastName, phoneNumber, email, password, role)
            response['message'] = 'Signup success'
            response['code'] = 200
            response['result'] = createTokens(user)
        return response
