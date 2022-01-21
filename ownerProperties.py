
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from data import connect
import json

class OwnerProperties(Resource):
    decorators = [jwt_required()]
    def get(self):
        response = {}
        user = get_jwt_identity()
        with connect() as db:
            sql = '''
                SELECT p.*, manager_first_name, manager_last_name, manager_phone_number, manager_email
                FROM properties p LEFT JOIN managerProfileInfo m ON p.manager_id = m.manager_id
                WHERE p.owner_id = %(owner_id)s
            '''
            args = {
                'owner_id': user['user_uid']
            }
            response = db.execute(sql, args)
        return response
