
from flask import request
from flask_restful import Resource

import boto3
from data import connect, uploadImage, s3
import json

def updateDocuments(docFiles, contract_uid):
    for filename in docFiles:
        if type(docFiles[filename]) == str:
            bucket = 'io-pm'
            key = docFiles[filename].split('/io-pm/')[1]
            data = s3.get_object(
                Bucket=bucket,
                Key=key
            )
            docFiles[filename] = data['Body']
    s3Resource = boto3.resource('s3')
    bucket = s3Resource.Bucket('io-pm')
    bucket.objects.filter(Prefix=f'contracts/{contract_uid}/').delete()
    documents = []
    for i in range(len(docFiles.keys())):
        filename = f'doc_{i}'
        key = f'contracts/{contract_uid}/{filename}'
        doc = uploadImage(docFiles[filename], key)
        documents.append(doc)
    return documents

class Contracts(Resource):
    def get(self):
        filters = ['contract_uid', 'property_uid', 'business_uid']
        where = {}
        for filter in filters:
            filterValue = request.args.get(filter)
            if filterValue is not None:
                where[filter] = filterValue
        with connect() as db:
            response = db.select('contracts', where)
        return response

    def post(self):
        response = {}
        with connect() as db:
            data = request.form
            fields = ['property_uid', 'business_uid', 'start_date', 'end_date', 'contract_fees',
                'assigned_contacts']
            newContract = {}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    newContract[field] = fieldValue
            newContractID = db.call('new_contract_id')['result'][0]['new_id']
            newContract['contract_uid'] = newContractID
            documents = []
            i = 0
            while True:
                filename = f'doc_{i}'
                file = request.files.get(filename)
                if file:
                    key = f'contracts/{newContractID}/{filename}'
                    doc = uploadImage(file, key)
                    documents.append(doc)
                else:
                    break
                i += 1
            newContract['documents'] = json.dumps(documents)
            print(newContract)
            response = db.insert('contracts', newContract)
        return response

    def put(self):
        response = {}
        with connect() as db:
            data = request.form
            contract_uid = data.get('contract_uid')
            fields = ['start_date', 'end_date', 'contract_fees', 'assigned_contacts']
            newContract = {}
            for field in fields:
                newContract[field] = data.get(field)
            i = 0
            docFiles = {}
            while True:
                filename = f'doc_{i}'
                file = request.files.get(filename)
                s3Link = data.get(filename)
                if file:
                    docFiles[filename] = file
                elif s3Link:
                    docFiles[filename] = s3Link
                else:
                    break
                i += 1
            documents = updateDocuments(docFiles, contract_uid)
            newContract['documents'] = json.dumps(documents)
            primaryKey = {'contract_uid': contract_uid}
            response = db.update('contracts', primaryKey, newContract)
        return response
