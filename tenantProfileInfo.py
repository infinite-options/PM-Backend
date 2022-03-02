from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from data import connect, uploadImage
import json

def updateDocuments(documents, tenant_id):
    for i, doc in enumerate(documents):
        if 'link' in doc:
            bucket = 'io-pm'
            key = doc['link'].split('/io-pm/')[1]
            data = s3.get_object(
                Bucket=bucket,
                Key=key
            )
            doc['file'] = data['Body']
    s3Resource = boto3.resource('s3')
    bucket = s3Resource.Bucket('io-pm')
    bucket.objects.filter(Prefix=f'tenants/{tenant_id}/').delete()
    for i, doc in enumerate(documents):
        filename = f'doc_{i}'
        key = f'tenants/{tenant_id}/{filename}'
        link = uploadImage(doc['file'], key)
        doc['link'] = link
        del doc['file']
    return documents

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
            data = request.form
            fields = ['first_name', 'last_name', 'ssn', 'current_salary', 'salary_frequency', 'current_job_title',
                'current_job_company', 'drivers_license_number', 'drivers_license_state', 'current_address', 'previous_address']
            jsonFields = ['current_address', 'previous_address']
            newProfileInfo = {'tenant_id': user['user_uid']}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    if field in jsonFields:
                        newProfileInfo['tenant_'+field] = json.dumps(fieldValue)
                    else:
                        newProfileInfo['tenant_'+field] = fieldValue
            documents = json.loads(data.get('documents'))
            for i in range(len(documents)):
                filename = f'doc_{i}'
                file = request.files.get(filename)
                if file:
                    key = f"tenants/{user['user_uid']}/{filename}"
                    doc = uploadImage(file, key)
                    documents[i]['link'] = doc
                else:
                    break
            newProfileInfo['documents'] = json.dumps(documents)
            response = db.insert('tenantProfileInfo', newProfileInfo)
        return response
    def put(self):
        response = {}
        user = get_jwt_identity()
        with connect() as db:
            data = request.get_json()
            fields = ['first_name', 'last_name', 'ssn', 'current_salary', 'salary_frequency', 'current_job_title',
                'current_job_company', 'drivers_license_number', 'drivers_license_state', 'current_address', 'previous_address']
            jsonFields = ['current_address', 'previous_address']
            newProfileInfo = {}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    if field in jsonFields:
                        newProfileInfo['tenant_'+field] = json.dumps(fieldValue)
                    else:
                        newProfileInfo['tenant_'+field] = fieldValue
            documents = json.loads(data.get('documents'))
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
            documents = updateDocuments(documents, rental_uid)
            newProfileInfo['documents'] = json.dumps(documents)
            primaryKey = {'tenant_id': user['user_uid']}
            response = db.update('tenantProfileInfo', primaryKey, newProfileInfo)
        return response
