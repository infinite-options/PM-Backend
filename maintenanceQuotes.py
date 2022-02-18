
from flask import request
from flask_restful import Resource

from data import connect
import json
from datetime import datetime

class MaintenanceQuotes(Resource):
    def get(self):
        response = {}
        filters = ['maintenance_quote_uid', 'maintenance_request_uid', 'business_uid', 'status']
        where = {}
        for filter in filters:
            filterValue = request.args.get(filter)
            if filterValue is not None:
                where[filter] = filterValue
        with connect() as db:
            response = db.select('maintenanceQuotes', where)
        return response

    def post(self):
        response = {}
        with connect() as db:
            data = request.json
            fields = ['maintenance_request_uid', 'business_uid']
            newQuote = {}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    newQuote[field] = fieldValue
            newQuoteID = db.call('new_quote_id')['result'][0]['new_id']
            newQuote['maintenance_quote_uid'] = newQuoteID
            newQuote['status'] = 'REQUEST'
            response = db.insert('maintenanceQuotes', newQuote)
        return response

    def put(self):
        response = {}
        with connect() as db:
            data = request.json
            fields = ['services_expenses', 'earliest_availability', 'event_type', 'notes', 'status']
            jsonFields = ['services_expenses']
            newQuote = {}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    if field in jsonFields:
                        newQuote[field] = json.dumps(fieldValue)
                    else:
                        newQuote[field] = fieldValue
            primaryKey = {
                'maintenance_quote_uid': data.get('maintenance_quote_uid')
            }
            response = db.update('maintenanceQuotes', primaryKey, newQuote)
        return response