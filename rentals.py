
from flask import request
from flask_restful import Resource

import boto3
from data import connect, uploadImage, s3
import json
from purchases import newPurchase
from datetime import date
from dateutil.relativedelta import relativedelta

def updateDocuments(docFiles, rental_uid):
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
    bucket.objects.filter(Prefix=f'rentals/{rental_uid}/').delete()
    documents = []
    for i in range(len(docFiles.keys())):
        filename = f'doc_{i}'
        key = f'rentals/{rental_uid}/{filename}'
        doc = uploadImage(docFiles[filename], key)
        documents.append(doc)
    return documents

class Rentals(Resource):
    def get(self):
        filters = ['rental_uid', 'rental_property_id', 'tenant_id', 'rental_status']
        where = {}
        for filter in filters:
            filterValue = request.args.get(filter)
            if filterValue is not None:
                where[filter] = filterValue
        with connect() as db:
            response = db.select('rentals', where)
        return response

    def post(self):
        response = {}
        with connect() as db:
            data = request.form
            fields = ['rental_property_id', 'tenant_id', 'actual_rent', 'lease_start', 'lease_end',
                'rent_payments', 'assigned_contacts']
            newRental = {}
            for field in fields:
                newRental[field] = data.get(field)
            newRentalID = db.call('new_rental_id')['result'][0]['new_id']
            newRental['rental_uid'] = newRentalID
            newRental['rental_status'] = 'ACTIVE'
            documents = []
            i = 0
            while True:
                filename = f'doc_{i}'
                file = request.files.get(filename)
                if file:
                    key = f'rentals/{newRentalID}/{filename}'
                    doc = uploadImage(file, key)
                    documents.append(doc)
                else:
                    break
                i += 1
            newRental['documents'] = json.dumps(documents)
            print(newRental)
            response = db.insert('rentals', newRental)
            rentPayments = json.loads(newRental['rent_payments'])
            for payment in rentPayments:
                if payment['frequency'] == 'Monthly':
                    charge_date = date.fromisoformat(newRental['lease_start'])
                    lease_end = date.fromisoformat(newRental['lease_end'])
                    while charge_date < lease_end:
                        charge_month = charge_date.strftime('%B')
                        purchaseResponse = newPurchase(
                            linked_purchase_id=None,
                            pur_property_id=newRental['rental_property_id'],
                            payer=newRental['tenant_id'],
                            receiver=newRental['rental_property_id'],
                            purchase_type='RENT',
                            description=payment['fee_name'],
                            amount_due=payment['charge'],
                            purchase_notes=charge_month,
                            purchase_date=charge_date.isoformat(),
                            purchase_frequency=payment['frequency']
                        )
                        print(purchaseResponse)
                        charge_date += relativedelta(months=1)
                else:
                    purchaseResponse = newPurchase(
                        linked_purchase_id=None,
                        pur_property_id=newRental['rental_property_id'],
                        payer=newRental['tenant_id'],
                        receiver=newRental['rental_property_id'],
                        purchase_type='RENT',
                        description=payment['fee_name'],
                        amount_due=payment['charge'],
                        purchase_notes='',
                        purchase_date=newRental['lease_start'],
                        purchase_frequency=payment['frequency']
                    )
                    print(purchaseResponse)
        return response

    def put(self):
        response = {}
        with connect() as db:
            data = request.form
            rental_uid = data.get('rental_uid')
            fields = ['rental_property_id', 'tenant_id', 'actual_rent', 'lease_start', 'lease_end',
                'rent_payments', 'assigned_contacts', 'rental_status']
            newRental = {}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    newRental[field] = fieldValue
            i = 0
            docFiles = {}
            while True:
                filename = f'doc_{i}'
                file = request.files.get(filename)
                s3Link = data.get(filename)
                if file:
                    imageFiles[filename] = file
                elif s3Link:
                    imageFiles[filename] = s3Link
                else:
                    break
                i += 1
            documents = updateDocuments(docFiles, rental_uid)
            newRental['documents'] = json.dumps(documents)
            primaryKey = {'rental_uid': rental_uid}
            response = db.update('rentals', primaryKey, newRental)
        return response
