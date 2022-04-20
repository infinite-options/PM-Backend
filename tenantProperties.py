
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from data import connect
import json


class TenantProperties(Resource):
    decorators = [jwt_required()]

    def get(self):
        response = {}
        user = get_jwt_identity()
        with connect() as db:
            # where = {
            #     'tenant_id': user['user_uid']
            # }
            response = db.execute("""SELECT * FROM pm.propertyInfo WHERE rental_status = 'ACTIVE' AND management_status <> 'REJECTED' AND tenant_id = \'"""
                                  + user['user_uid']
                                  + """\'""")
            # response = db.select(
            #     "propertyInfo WHERE rental_status= 'ACTIVE'", where)
        return response
