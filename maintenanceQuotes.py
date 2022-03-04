
from flask import request
from flask_restful import Resource

from data import connect
import json
from datetime import datetime

def acceptQuote(quote_id):
    with connect() as db:
        response = db.select('maintenanceQuotes', where={'maintenance_quote_uid': quote_id})
        quote = response['result'][0]
        requestKey = {
            'maintenance_request_uid': quote['linked_request_uid']
        }
        newRequest = {
            'assigned_business': quote['quote_business_uid']
        }
        requestUpdate = db.update('maintenanceRequests', requestKey, newRequest)
        print(requestUpdate)
        quoteKey = {
            'linked_request_uid': quote['linked_request_uid']
        }
        newQuote = {
            'quote_status': 'WITHDRAWN'
        }
        quoteUpdate = db.update('maintenanceQuotes', quoteKey, newQuote)
        print(quoteUpdate)

class MaintenanceQuotes(Resource):
    def get(self):
        response = {}
        filters = ['maintenance_quote_uid', 'linked_request_uid', 'quote_business_uid', 'quote_status']
        where = {}
        for filter in filters:
            filterValue = request.args.get(filter)
            if filterValue is not None:
                where[filter] = filterValue
        with connect() as db:
            response = db.select('''
                maintenanceQuotes quote LEFT JOIN maintenanceRequests request
                ON linked_request_uid = maintenance_request_uid
                LEFT JOIN businesses business ON quote_business_uid = business_uid
            ''', where)
        return response

    def post(self):
        response = {}
        with connect() as db:
            data = request.json
            fields = ['linked_request_uid', 'quote_business_uid']
            newQuote = {}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    newQuote[field] = fieldValue
            requestKey = {
                'maintenance_request_uid': newQuote.get('linked_request_uid')
            }
            newStatus = {
                'request_status': 'PROCESSING'
            }
            db.update('maintenanceRequests', requestKey, newStatus)
            if type(newQuote['quote_business_uid']) is list:
                businesses = newQuote['quote_business_uid']
                for business_uid in businesses:
                    newQuoteID = db.call('new_quote_id')['result'][0]['new_id']
                    newQuote['maintenance_quote_uid'] = newQuoteID
                    newQuote['quote_business_uid'] = business_uid
                    newQuote['quote_status'] = 'REQUESTED'
                    response = db.insert('maintenanceQuotes', newQuote)
                    if response['code'] != 200:
                        return newResponse
            else:
                newQuoteID = db.call('new_quote_id')['result'][0]['new_id']
                newQuote['maintenance_quote_uid'] = newQuoteID
                newQuote['quote_status'] = 'REQUESTED'
                response = db.insert('maintenanceQuotes', newQuote)
        return response

    def put(self):
        response = {}
        with connect() as db:
            data = request.json
            fields = ['services_expenses', 'earliest_availability', 'event_type', 'notes', 'quote_status']
            jsonFields = ['services_expenses']
            newQuote = {}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    if field in jsonFields:
                        newQuote[field] = json.dumps(fieldValue)
                    else:
                        newQuote[field] = fieldValue
            if newQuote.get('quote_status') == 'ACCEPTED':
                acceptQuote(data.get('maintenance_quote_uid'))
            primaryKey = {
                'maintenance_quote_uid': data.get('maintenance_quote_uid')
            }
            response = db.update('maintenanceQuotes', primaryKey, newQuote)
        return response
