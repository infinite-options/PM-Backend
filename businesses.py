
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

import boto3
from data import connect, uploadImage, s3
import json
from datetime import datetime


def updateDocuments(documents, business_uid):
    content = []
    for i, doc in enumerate(documents):
        # print('i, doc', i, doc)
        if 'link' in doc:
            # print('in if link in doc')
            bucket = 'io-pm'
            key = doc['link'].split('/io-pm/')[1]
            data = s3.get_object(
                Bucket=bucket,
                Key=key
            )
            doc['file'] = data['Body']
            content.append(data['ContentType'])
        else:
            content.append('')

    s3Resource = boto3.resource('s3')
    bucket = s3Resource.Bucket('io-pm')
    bucket.objects.filter(Prefix=f'businesses/{business_uid}/').delete()
    docs = []
    for i, doc in enumerate(documents):

        filename = f'doc_{i}'
        key = f'businesses/{business_uid}/{filename}'
        # print(type(doc['file']))
        link = uploadImage(doc['file'], key, content[i])
        # print('link', link)
        doc['link'] = link
        del doc['file']
        docs.append(doc)
    return docs


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
    decorators = [jwt_required(optional=True)]

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
            # data = request.json
            data = request.form
            user = get_jwt_identity()
            if not user:
                return 401, response
            fields = ['type', 'name', 'phone_number', 'email', 'ein_number', 'services_fees', 'locations',
                      'paypal', 'apple_pay', 'zelle', 'venmo', 'account_number', 'routing_number', 'services_fees', 'locations']
            # jsonFields = []
            newBusiness = {}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    # if field in jsonFields:
                    #     newBusiness[f'business_{field}'] = json.dumps(
                    #         fieldValue)
                    # else:
                    newBusiness[f'business_{field}'] = fieldValue
            newBusinessID = db.call('new_business_id')['result'][0]['new_id']
            newBusiness['business_uid'] = newBusinessID
            documents = json.loads(data.get('business_documents'))
            for i in range(len(documents)):
                filename = f'doc_{i}'
                file = request.files.get(filename)
                if file:
                    key = f'businesses/{newBusinessID}/{filename}'
                    doc = uploadImage(file, key, '')
                    documents[i]['link'] = doc
                else:
                    break
            newBusiness['business_documents'] = json.dumps(documents)
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
            # data = request.json
            data = request.form
            business_uid = data.get('business_uid')
            fields = ['type', 'name', 'phone_number', 'email', 'ein_number', 'services_fees', 'locations',
                      'paypal', 'apple_pay', 'zelle', 'venmo', 'account_number', 'routing_number', 'services_fees', 'locations']
            # jsonFields = []
            newBusiness = {}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    # if field in jsonFields:
                    #     newBusiness[f'business_{field}'] = json.dumps(
                    #         fieldValue)
                    # else:
                    newBusiness[f'business_{field}'] = fieldValue
            documents = json.loads(data.get('business_documents'))
            for i, doc in enumerate(documents):
                filename = f'doc_{i}'
                file = request.files.get(filename)
                s3Link = doc.get('link')
                if file:
                    doc['file'] = file
                elif s3Link:
                    doc['link'] = s3Link
                else:
                    break
            documents = updateDocuments(documents, business_uid)
            newBusiness['business_documents'] = json.dumps(documents)
            primaryKey = {
                'business_uid': data.get('business_uid')
            }
            response = db.update('businesses', primaryKey, newBusiness)
        return response
