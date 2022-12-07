
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from data import connect
import json
from datetime import datetime


def getEmployeeBusinesses(user):
    response = {}
    with connect() as db:
        sql = '''
            SELECT b.business_uid, b.business_type, e.employee_role
            FROM employees e LEFT JOIN businesses b ON e.business_uid = b.business_uid
            WHERE user_uid = %(user_uid)s
        '''
        args = {
            'user_uid': user['user_uid']
        }
        response = db.execute(sql, args)
    return response


class Businesses(Resource):
    decorators = [jwt_required]

    def get(self):
        response = {}
        filters = ['business_uid', 'business_type',
                   'business_name', 'business_email']
        where = {}
        for filter in filters:
            filterValue = request.args.get(filter)
            if filterValue is not None:
                where[filter] = filterValue
        with connect() as db:
            response = db.select('businesses', where)
        return response

    def post(self):
        response = {}
        with connect() as db:
            data = request.json
            user = get_jwt_identity()
            if not user:
                return 401, response
            fields = ['type', 'name', 'phone_number', 'email', 'ein_number', 'services_fees', 'locations',
                      'paypal', 'apple_pay', 'zelle', 'venmo', 'account_number', 'routing_number']
            jsonFields = ['services_fees', 'locations']
            newBusiness = {}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    if field in jsonFields:
                        newBusiness[f'business_{field}'] = json.dumps(
                            fieldValue)
                    else:
                        newBusiness[f'business_{field}'] = fieldValue
            newBusinessID = db.call('new_business_id')['result'][0]['new_id']
            newBusiness['business_uid'] = newBusinessID

            response = db.insert('businesses', newBusiness)
            newEmployee = {
                'user_uid': user['user_uid'],
                'business_uid': newBusinessID,
                'employee_role': 'Owner',
                'employee_first_name': user['first_name'],
                'employee_last_name': user['last_name'],
                'employee_phone_number': user['phone_number'],
                'employee_email': user['email'],
                'employee_ssn': '',
                'employee_ein_number': '',
                'employee_status': 'ACTIVE',
                'employee_signedin': 'Owner',
            }
            newEmployeeID = db.call('new_employee_id')['result'][0]['new_id']
            newEmployee['employee_uid'] = newEmployeeID
            db.insert('employees', newEmployee)
        return response

    def put(self):
        response = {}
        with connect() as db:
            data = request.json
            fields = ['type', 'name', 'phone_number', 'email', 'ein_number', 'services_fees', 'locations',
                      'paypal', 'apple_pay', 'zelle', 'venmo', 'account_number', 'routing_number']
            jsonFields = ['services_fees', 'locations']
            newBusiness = {}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    if field in jsonFields:
                        newBusiness[f'business_{field}'] = json.dumps(
                            fieldValue)
                    else:
                        newBusiness[f'business_{field}'] = fieldValue
            primaryKey = {
                'business_uid': data.get('business_uid')
            }
            response = db.update('businesses', primaryKey, newBusiness)
        return response
