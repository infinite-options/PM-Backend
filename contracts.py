
from flask import request
from flask_restful import Resource

import boto3
from data import connect, uploadImage, s3
import json


def updateDocuments(documents, contract_uid):
    print(documents)
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
    bucket.objects.filter(Prefix=f'contracts/{contract_uid}/').delete()
    print(documents)
    docs = []
    for i, doc in enumerate(documents):
        filename = f'doc_{i}'
        key = f'contracts/{contract_uid}/{filename}'
        link = uploadImage(doc['file'], key)
        doc['link'] = link
        del doc['file']
        docs.append(doc)
    return docs


class Contracts(Resource):
    def get(self):
        filters = ['contract_uid', 'property_uid',
                   'business_uid', 'contract_name']
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
                      'assigned_contacts', 'contract_name', 'contract_status']
            newContract = {}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    newContract[field] = fieldValue
            newContractID = db.call('new_contract_id')['result'][0]['new_id']
            newContract['contract_uid'] = newContractID
            documents = json.loads(data.get('documents'))
            for i in range(len(documents)):
                filename = f'doc_{i}'
                file = request.files.get(filename)
                if file:
                    key = f'contracts/{newContractID}/{filename}'
                    doc = uploadImage(file, key)
                    documents[i]['link'] = doc
                else:
                    break
            newContract['documents'] = json.dumps(documents)
            print(newContract)
            response = db.insert('contracts', newContract)
        return response

    def put(self):
        response = {}
        with connect() as db:
            data = request.form
            contract_uid = data.get('contract_uid')
            fields = ['start_date', 'end_date',
                      'contract_fees', 'assigned_contacts', 'contract_name', 'contract_status']
            newContract = {}
            for field in fields:
                newContract[field] = data.get(field)
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
            documents = updateDocuments(documents, contract_uid)
            newContract['documents'] = json.dumps(documents)
            primaryKey = {'contract_uid': contract_uid}
            response = db.update('contracts', primaryKey, newContract)
        return response
