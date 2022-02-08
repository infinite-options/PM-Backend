
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from data import connect
import json

class ManagerProperties(Resource):
    decorators = [jwt_required()]
    def get(self):
        response = {}
        user = get_jwt_identity()
        with connect() as db:
            response = db.select('employees', where={
                'user_uid': user['user_uid']
            })
            business_uid = response['result'][0]['business_uid']
            response = db.select('propertyInfo', where={
                'manager_id': business_uid
            })
        return response
