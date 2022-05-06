
from flask import request
from flask_restful import Resource

from data import connect
import json
from datetime import datetime


def acceptQuote(quote_id):
    with connect() as db:
        response = db.select('maintenanceQuotes', where={
                             'maintenance_quote_uid': quote_id})
        quote = response['result'][0]
        requestKey = {
            'maintenance_request_uid': quote['linked_request_uid']
        }
        newRequest = {
            'assigned_business': quote['quote_business_uid']
        }
        requestUpdate = db.update(
            'maintenanceRequests', requestKey, newRequest)
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
        filters = ['maintenance_quote_uid', 'linked_request_uid',
                   'quote_business_uid', 'quote_status']
        where = {}
        for filter in filters:
            filterValue = request.args.get(filter)
            if filterValue is not None:
                where[filter] = filterValue
        with connect() as db:

            response = db.select('''
                maintenanceQuotes quote LEFT JOIN maintenanceRequests mr
                ON linked_request_uid = maintenance_request_uid
                LEFT JOIN businesses business 
                ON quote_business_uid = business_uid
                LEFT JOIN properties p
                ON p.property_uid = mr.property_uid
            ''', where)
            for i in range(len(response['result'])):
                pid = response['result'][i]['property_uid']
                property_res = db.execute("""SELECT 
                                                    pm.*, 
                                                    b.business_uid AS manager_id, 
                                                    b.business_name AS manager_business_name, 
                                                    b.business_email AS manager_email, 
                                                    b.business_phone_number AS manager_phone_number 
                                                    FROM pm.propertyManager pm 
                                                    LEFT JOIN businesses b 
                                                    ON b.business_uid = pm.linked_business_id 
                                                    WHERE pm.linked_property_id = \'""" + pid + """\'""")
                # print('property_res', property_res)
                response['result'][i]['property_manager'] = list(
                    property_res['result'])
                rental_res = db.execute("""SELECT
                                            r.rental_uid AS rental_uid,
                                            r.rental_property_id AS rental_property_id,
                                            r.rent_payments AS rent_payments,
                                            r.lease_start AS lease_start,
                                            r.lease_end AS lease_end,
                                            r.rental_status AS rental_status,
                                            tpi.tenant_id AS tenant_id,
                                            tpi.tenant_first_name AS tenant_first_name,
                                            tpi.tenant_last_name AS tenant_last_name,
                                            tpi.tenant_email AS tenant_email,
                                            tpi.tenant_phone_number AS tenant_phone_number
                                            FROM pm.rentals r
                                            LEFT JOIN pm.leaseTenants lt
                                            ON lt.linked_rental_uid = r.rental_uid
                                            LEFT JOIN pm.tenantProfileInfo tpi
                                            ON tpi.tenant_id = lt.linked_tenant_id
                                            WHERE r.rental_property_id = \'""" + pid + """\'""")
                response['result'][i]['rentalInfo'] = list(
                    rental_res['result'])
                if len(rental_res['result']) > 0:
                    response['result'][i]['rental_status'] = rental_res['result'][0]['rental_status']
                else:
                    response['result'][i]['rental_status'] = ""
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
            fields = ['services_expenses', 'earliest_availability',
                      'event_type', 'notes', 'quote_status']
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
