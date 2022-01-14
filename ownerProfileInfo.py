from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from data import connect
import json


class OwnerProfileInfo(Resource):
    decorators = [jwt_required()]
    def get(self):
        response = {}
        user = get_jwt_identity()
        where = {'owner_id': user['user_uid']}
        with connect() as db:
            response = db.select('ownerProfileInfo', where)
        return response
    def post(self):
        response = {}
        user = get_jwt_identity()
        with connect() as db:
            data = request.get_json()
            fields = ['first_name', 'last_name', 'phone_number', 'email', 'ein_number', 'ssn',
                'paypal', 'apple_pay', 'zelle', 'venmo', 'account_number', 'routing_number']
            newProfileInfo = {'owner_id': user['user_uid']}
            for field in fields:
                newProfileInfo['owner_'+field] = data.get(field)
            response = db.insert('ownerProfileInfo', newProfileInfo)
        return response
