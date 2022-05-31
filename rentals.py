
from flask import request
from flask_restful import Resource

import boto3
from data import connect, uploadImage, s3
import json
from purchases import newPurchase
from datetime import date
from dateutil.relativedelta import relativedelta


def updateDocuments(documents, rental_uid):
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
    bucket.objects.filter(Prefix=f'rentals/{rental_uid}/').delete()
    for i, doc in enumerate(documents):
        filename = f'doc_{i}'
        key = f'rentals/{rental_uid}/{filename}'
        link = uploadImage(doc['file'], key)
        doc['link'] = link
        del doc['file']
    return documents


class Rentals(Resource):
    def get(self):
        filters = ['rental_uid', 'rental_property_id',
                   'tenant_id', 'rental_status']
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
            fields = ['rental_property_id', 'actual_rent', 'lease_start', 'lease_end',
                      'rent_payments', 'assigned_contacts', 'rental_status']
            newRental = {}
            for field in fields:
                newRental[field] = data.get(field)
            newRentalID = db.call('new_rental_id')['result'][0]['new_id']
            newRental['rental_uid'] = newRentalID
            # newRental['rental_status'] = 'ACTIVE'
            documents = json.loads(data.get('documents'))
            for i in range(len(documents)):
                filename = f'doc_{i}'
                file = request.files.get(filename)
                if file:
                    key = f'rentals/{newRentalID}/{filename}'
                    doc = uploadImage(file, key)
                    documents[i]['link'] = doc
                else:
                    break
            newRental['documents'] = json.dumps(documents)
            print('newRental', newRental)
            response = db.insert('rentals', newRental)
            # adding leaseTenants
            tenants = data.get('tenant_id')
            print('tenants1', tenants)
            if '[' in tenants:
                print('tenants2', tenants)
                tenants = json.loads(tenants)
                print('tenants3', tenants)
            print('tenants4', tenants)
            if type(tenants) == str:
                tenants = [tenants]
                print('tenants5', tenants)
            for tenant_id in tenants:
                print('tenants6', tenant_id)
                leaseTenant = {
                    'linked_rental_uid': newRentalID,
                    'linked_tenant_id': tenant_id
                }
                db.insert('leaseTenants', leaseTenant)
            # creating purchases
            rentPayments = json.loads(newRental['rent_payments'])
            # for payment in rentPayments:
            #     if payment['frequency'] == 'Monthly':
            #         charge_date = date.fromisoformat(newRental['lease_start'])
            #         lease_end = date.fromisoformat(newRental['lease_end'])
            #         print('charge_date', type(charge_date),
            #               charge_date.isoformat())
            #         while charge_date < lease_end:
            #             charge_month = charge_date.strftime('%B')
            #             if(payment['fee_name'] == 'Rent'):
            #                 purchaseResponse = newPurchase(
            #                     linked_purchase_id=None,
            #                     pur_property_id=newRental['rental_property_id'],
            #                     payer=json.dumps(tenants),
            #                     receiver=newRental['rental_property_id'],
            #                     purchase_type='RENT',
            #                     description=payment['fee_name'],
            #                     amount_due=payment['charge'],
            #                     purchase_notes=charge_month,
            #                     purchase_date=charge_date.isoformat(),
            #                     purchase_frequency=payment['frequency'],
            #                     next_payment=charge_date.replace(day=1)
            #                 )
            #             else:
            #                 purchaseResponse = newPurchase(
            #                     linked_purchase_id=None,
            #                     pur_property_id=newRental['rental_property_id'],
            #                     payer=json.dumps(tenants),
            #                     receiver=newRental['rental_property_id'],
            #                     purchase_type='EXTRA CHARGES',
            #                     description=payment['fee_name'],
            #                     amount_due=payment['charge'],
            #                     purchase_notes=charge_month,
            #                     purchase_date=charge_date.isoformat(),
            #                     purchase_frequency=payment['frequency'],
            #                     next_payment=charge_date.replace(day=1)
            #                 )
            #             charge_date += relativedelta(months=1)
            #     else:
            #         print('lease_start', type(newRental['lease_start']))
            #         if(payment['fee_name'] == 'Rent'):
            #             purchaseResponse = newPurchase(
            #                 linked_purchase_id=None,
            #                 pur_property_id=newRental['rental_property_id'],
            #                 payer=json.dumps(tenants),
            #                 receiver=newRental['rental_property_id'],
            #                 purchase_type='RENT',
            #                 description=payment['fee_name'],
            #                 amount_due=payment['charge'],
            #                 purchase_notes='',
            #                 purchase_date=newRental['lease_start'],
            #                 purchase_frequency=payment['frequency'],
            #                 next_payment=date.fromisoformat(
            #                     newRental['lease_start']).replace(day=1)
            #             )

            #         else:

            #             purchaseResponse = newPurchase(
            #                 linked_purchase_id=None,
            #                 pur_property_id=newRental['rental_property_id'],
            #                 payer=json.dumps(tenants),
            #                 receiver=newRental['rental_property_id'],
            #                 purchase_type='EXTRA CHARGES',
            #                 description=payment['fee_name'],
            #                 amount_due=payment['charge'],
            #                 purchase_notes='',
            #                 purchase_date=newRental['lease_start'],
            #                 purchase_frequency=payment['frequency'],
            #                 next_payment=date.fromisoformat(
            #                     newRental['lease_start']).replace(day=1)
            #             )
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
                    print('fieldvalue', fieldValue)
                if field == 'documents':
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
                    newRental['documents'] = json.dumps(documents)

            primaryKey = {'rental_uid': rental_uid}
            print('newRental', newRental)
            response = db.update('rentals', primaryKey, newRental)
        return response
