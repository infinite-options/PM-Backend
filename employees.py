
from flask import request
from flask_restful import Resource

from data import connect
import json
from datetime import datetime


class Employees(Resource):
    def get(self):
        response = {}
        filters = ['employee_uid', 'user_uid',
                   'business_uid', 'employee_role', 'employee_email']
        where = {}
        for filter in filters:
            filterValue = request.args.get(filter)
            if filterValue is not None:
                where[filter] = filterValue
        with connect() as db:
            response = db.select('employees', where)
        return response

    def post(self):
        response = {}
        with connect() as db:
            data = request.json
            fields = ['user_uid', 'business_uid', 'role', 'first_name', 'last_name',
                      'phone_number', 'email', 'ssn', 'ein_number']
            bareFields = ['user_uid', 'business_uid']
            newEmployee = {}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    if field in bareFields:
                        newEmployee[field] = fieldValue
                    else:
                        newEmployee[f'employee_{field}'] = fieldValue
            newEmployeeID = db.call('new_employee_id')['result'][0]['new_id']
            newEmployee['employee_uid'] = newEmployeeID
            newEmployee['employee_status'] = 'INACTIVE'
            newEmployee['employee_signedin'] = 'Employee'
            response = db.insert('employees', newEmployee)
        return response

    def put(self):
        response = {}
        with connect() as db:
            data = request.json
            fields = ['user_uid', 'business_uid', 'role', 'first_name',
                      'last_name', 'phone_number', 'email', 'ssn', 'ein_number']
            bareFields = ['user_uid', 'business_uid']
            newEmployee = {}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    if field in bareFields:
                        newEmployee[field] = fieldValue
                    else:
                        newEmployee[f'employee_{field}'] = fieldValue
            primaryKey = {
                'employee_uid': data.get('employee_uid')
            }
            response = db.update('employees', primaryKey, newEmployee)
        return response
