from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from data import connect
import json


class BusinessProfileInfo(Resource):
    decorators = [jwt_required()]
    def get(self):
        response = {}
        user = get_jwt_identity()
        where = {'business_id': user['user_uid']}
        with connect() as db:
            response = db.select('businessProfileInfo', where)
        return response
    def post(self):
        response = {}
        user = get_jwt_identity()
        with connect() as db:
            data = request.get_json()
            fields = ['name', 'ein_number', 'paypal', 'apple_pay', 'zelle',
                'venmo', 'account_number', 'routing_number', 'services', 'contact']
            jsonFields = ['services', 'contact']
            newProfileInfo = {'business_id': user['user_uid']}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    if field in jsonFields:
                        newProfileInfo['business_'+field] = json.dumps(fieldValue)
                    else:
                        newProfileInfo['business_'+field] = fieldValue
            response = db.insert('businessProfileInfo', newProfileInfo)
        return response
