
from flask import request
from flask_restful import Resource

from data import connect
import json
from datetime import datetime

class Businesses(Resource):
    def get(self):
        response = {}
        filters = ['business_uid', 'business_type', 'business_name']
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
            fields = ['type', 'name', 'phone_number', 'email', 'ein_number', 'services_fees']
            jsonFields = ['services_fees']
            newBusiness = {}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    if field in jsonFields:
                        newBusiness[f'business_{field}'] = json.dumps(fieldValue)
                    else:
                        newBusiness[f'business_{field}'] = fieldValue
            newBusinessID = db.call('new_business_id')['result'][0]['new_id']
            newBusiness['business_uid'] = newBusinessID
            response = db.insert('businesses', newBusiness)
        return response

    def put(self):
        response = {}
        with connect() as db:
            data = request.json
            fields = ['type', 'name', 'phone_number', 'email', 'ein_number', 'services_fees']
            jsonFields = ['services_fees']
            newBusiness = {}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    if field in jsonFields:
                        newBusiness[f'business_{field}'] = json.dumps(fieldValue)
                    else:
                        newBusiness[f'business_{field}'] = fieldValue
            primaryKey = {
                'business_uid': data.get('business_uid')
            }
            response = db.update('businesses', primaryKey, newBusiness)
        return response
