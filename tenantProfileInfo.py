from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from data import connect
import json


class TenantProfileInfo(Resource):
    decorators = [jwt_required()]
    def get(self):
        response = {}
        user = get_jwt_identity()
        where = {'tenant_id': user['user_uid']}
        with connect() as db:
            response = db.select('tenantProfileInfo', where)
        return response
    def post(self):
        response = {}
        user = get_jwt_identity()
        with connect() as db:
            data = request.get_json()
            fields = ['first_name', 'last_name', 'ssn', 'current_salary', 'current_job_title',
                'current_job_company', 'drivers_license_number', 'current_address', 'previous_addresses']
            jsonFields = ['current_address', 'previous_addresses']
            newProfileInfo = {'tenant_id': user['user_uid']}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    if field in jsonFields:
                        newProfileInfo['tenant_'+field] = json.dumps(fieldValue)
                    else:
                        newProfileInfo['tenant_'+field] = fieldValue
            response = db.insert('tenantProfileInfo', newProfileInfo)
        return response
    def put(self):
        response = {}
        user = get_jwt_identity()
        with connect() as db:
            data = request.get_json()
            fields = ['first_name', 'last_name', 'ssn', 'current_salary', 'current_job_title',
                'current_job_company', 'drivers_license_number', 'current_address', 'previous_addresses']
            jsonFields = ['current_address', 'previous_addresses']
            newProfileInfo = {}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    if field in jsonFields:
                        newProfileInfo['tenant_'+field] = json.dumps(fieldValue)
                    else:
                        newProfileInfo['tenant_'+field] = fieldValue
            primaryKey = {'tenant_id': user['user_uid']}
            response = db.update('tenantProfileInfo', primaryKey, newProfileInfo)
        return response
