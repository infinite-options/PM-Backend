
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
            sql = '''
                SELECT p.*, owner_first_name, owner_last_name, owner_phone_number, owner_email
                FROM properties p LEFT JOIN ownerProfileInfo o ON p.owner_id = o.owner_id
                WHERE p.manager_id = %(manager_id)s
            '''
            args = {
                'manager_id': user['user_uid']
            }
            response = db.execute(sql, args)
        return response
