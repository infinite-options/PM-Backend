

from flask import request, current_app
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from data import connect
import json
from datetime import datetime

class Applications(Resource):
    decorators = [jwt_required(optional=True)]
    def get(self):
        response = {}
        filters = ['application_uid', 'property_uid', 'tenant_id']
        where = {}
        for filter in filters:
            filterValue = request.args.get(filter)
            if filterValue is not None:
                where[filter] = filterValue
        with connect() as db:
            response = db.select('applications', where)
        return response

    def post(self):
        response = {}
        with connect() as db:
            data = request.json
            user = get_jwt_identity()
            if not user:
                return 401, response
            fields = ['property_uid', 'message']
            newApplication = {}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    newApplication[field] = fieldValue
            newApplicationID = db.call('new_application_id')['result'][0]['new_id']
            newApplication['application_uid'] = newApplicationID
            newApplication['tenant_id'] = user['user_uid']
            newApplication['application_status'] = 'NEW'
            response = db.insert('applications', newApplication)
        return response

    def put(self):
        response = {}
        with connect() as db:
            data = request.json
            fields = ['message', 'application_status']
            newApplication = {}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    newApplication[field] = fieldValue
            # if newApplication['application_status'] == 'ACCEPTED':
            #     recipient = 'zacharywolfflind@gmail.com'
            #     subject = 'Application Accepted'
            #     body = 'Your application for the apartment has been accepted'
            #     current_app.sendEmail(recipient, subject, body)
            primaryKey = {
                'application_uid': data.get('application_uid')
            }
            response = db.update('applications', primaryKey, newApplication)
        return response
