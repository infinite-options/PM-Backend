from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
import boto3
from data import connect, uploadImage, s3
from datetime import date
import json


def updateDocuments(documents, bill_uid):
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
    bucket.objects.filter(Prefix=f'bills/{bill_uid}/').delete()
    docs = []
    for i, doc in enumerate(documents):

        filename = f'doc_{i}'
        key = f'bills/{bill_uid}/{filename}'
        # print(type(doc['file']))
        link = uploadImage(doc['file'], key, content[i])
        # print('link', link)
        doc['link'] = link
        del doc['file']
        docs.append(doc)
    return docs


class Bills(Resource):

    def get(self):
        response = {}
        filters = ['bill_property_id', 'bill_created_by',
                   'bill_utility_type', 'bill_requested_from']
        where = {}
        for filter in filters:
            filterValue = request.args.get(filter)
            if filterValue is not None:
                where[f'a.{filter}'] = filterValue
        with connect() as db:
            sql = 'SELECT  FROM bills b LEFT JOIN purchases p ON b.bill_uid = p.linked_bill_id'
            cols = 'b.*, p.*'
            tables = 'bills b LEFT JOIN purchases p ON b.bill_uid = p.linked_bill_id'
            response = db.select(cols=cols, tables=tables, where=where)
        return response

    def post(self):
        response = {}
        with connect() as db:
            data = request.form
            fields = ['bill_created_by', 'bill_description',
                      'bill_utility_type', 'bill_algorithm', 'bill_requested_from']
            newBill = {}
            for field in fields:
                fieldValue = data.get(field)
                print(fields, fieldValue)
                if fieldValue:
                    newBill[field] = fieldValue
            newBillID = db.call('new_bill_id')['result'][0]['new_id']
            newBill['bill_uid'] = newBillID

            documents = json.loads(data.get('bill_docs'))
            print(documents)
            for i in range(len(documents)):
                filename = f'doc_{i}'

                file = request.files.get(filename)
                print(file)
                if file:
                    key = f'bills/{newBillID}/{filename}'
                    doc = uploadImage(file, key, '')
                    documents[i]['link'] = doc
                    print(doc, documents)
                else:
                    break
            newBill['bill_docs'] = json.dumps(documents)
            print('newBill', newBill)
            response = db.insert('bills', newBill)
            response['bill_uid'] = newBillID
        return response


class DeleteUtilities(Resource):
    def put(self):
        ann_response = {}
        with connect() as db:
            data = request.json
            a_id = {
                'bill_uid': data['bill_uid']
            }
            ann_response = db.delete(
                """DELETE FROM pm.bills WHERE bill_uid = \'""" + data['bill_uid'] + """\' """)
            pur_response = db.delete(
                """DELETE FROM pm.purchases WHERE linked_bill_id = \'""" + data['bill_uid'] + """\' """)
        return ann_response
