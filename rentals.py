
from flask import request
from flask_restful import Resource

import boto3
from data import connect, uploadImage, s3
import json
from purchases import newPurchase
from datetime import date
from dateutil.relativedelta import relativedelta
from text_to_num import alpha2digit


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
                      'rent_payments', 'assigned_contacts', 'rental_status', 'due_by', 'late_by', 'late_fee', 'perDay_late_fee']
            newRental = {}
            for field in fields:
                newRental[field] = data.get(field)
                if field == 'due_by':
                    print(alpha2digit(data.get(field), 'en'))
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

        return response

    def put(self):
        response = {}
        with connect() as db:
            data = request.form
            rental_uid = data.get('rental_uid')
            fields = ['rental_property_id', 'tenant_id', 'actual_rent', 'lease_start', 'lease_end',
                      'rent_payments', 'assigned_contacts', 'rental_status', 'due_by', 'late_by' 'late_fee', 'perDay_late_fee']
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


class EndLease(Resource):
    def put(self):
        data = request.json
        fields = ['rental_uid', 'rental_status', 'rental_property_id']
        with connect() as db:
            rentalUpdate = {}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    rentalUpdate[field] = fieldValue
            rental_pk = {
                'rental_uid': rentalUpdate['rental_uid']
            }
            response = db.update('rentals', rental_pk, rentalUpdate)
            print(rentalUpdate['rental_property_id'])
            pur_pk = {
                'pur_property_id': rentalUpdate['rental_property_id']
            }
            pur_response = db.delete("""DELETE FROM pm.purchases WHERE pur_property_id = \'""" + rentalUpdate['rental_property_id'] + """\'
                                            AND (MONTH(purchase_date) > MONTH(now()) AND YEAR(purchase_date) = YEAR(now()) OR YEAR(purchase_date) > YEAR(now())) 
                                            AND purchase_status ="UNPAID"
                                            AND (purchase_type= "RENT" OR purchase_type= "EXTRA CHARGES")""")
            # pur_response = db.delete('purchases', pur_pk,  )
            print(pur_response)

        return response


class LeasetoMonth_CLASS(Resource):
    def get(self):

        with connect() as db:
            response = db.execute("""SELECT * 
                                    FROM pm.rentals r 
                                    LEFT JOIN
                                    pm.leaseTenants lt 
                                    ON lt.linked_rental_uid = r.rental_uid
                                    WHERE r.lease_end < DATE_FORMAT(NOW(), "%Y-%m-%d") 
                                    OR r.lease_end = DATE_FORMAT(NOW(), "%Y-%m-%d") 
                                    AND r.rental_status='ACTIVE'; """)

            if len(response['result']) > 0:
                for i in range(len(response['result'])):
                    print(response['result'][i]['rental_uid'])

                    pk = {
                        'rental_uid': response['result'][i]['rental_uid']}
                    updateLeaseEnd = {
                        'lease_end': (date.fromisoformat(
                            response['result'][i]['lease_end']) + relativedelta(months=1)).isoformat()}
                    print(pk, updateLeaseEnd)
                    res = db.update('rentals', pk, updateLeaseEnd)
                    print(res)
                    # res = db.execute("""UPDATE pm.rentals SET lease_end = DATE_ADD(lease_end, INTERVAL 1 MONTH) WHERE rental_uid = \'""" +
                    #                  response['result'][i]['rental_uid'] + """\';""")

                    tenants = response['result'][0]['linked_tenant_id']
                    # print('tenants1', tenants)
                    if '[' in tenants:
                        # print('tenants2', tenants)
                        tenants = json.loads(tenants)
                        # print('tenants3', tenants)
                    # print('tenants4', tenants)
                    if type(tenants) == str:
                        tenants = [tenants]
                        # print('tenants5', tenants)
                    print('tenant_id', tenants)
                    payment = json.loads(
                        response['result'][i]['rent_payments'])
                    print(payment, len(payment))

                    for r in range(len(payment)):
                        if payment[r]['fee_name'] == 'Rent':
                            print('RENT', payment[r]['fee_name'])
                            payment_date = alpha2digit(
                                response['result'][i]['due_by'], 'en')[:-2]
                            charge_date = date.today()
                            charge_month = charge_date.strftime(
                                '%B')
                            print(charge_date, charge_month)
                            purchaseResponse = newPurchase(
                                linked_bill_id=None,
                                pur_property_id=response['result'][i]['rental_property_id'],
                                payer=json.dumps(tenants),
                                receiver=response['result'][i]['rental_property_id'],
                                purchase_type='RENT',
                                description=payment[r]['fee_name'],
                                amount_due=payment[r]['charge'],
                                purchase_notes=charge_month,
                                purchase_date=charge_date.isoformat(),
                                purchase_frequency=payment[r]['frequency'],
                                next_payment=charge_date.replace(
                                    day=int(payment_date))
                            )

        return purchaseResponse


def LeasetoMonth():
    print("In LeaseToMonth")
    from purchases import newPurchase
    from datetime import date
    from dateutil.relativedelta import relativedelta

    with connect() as db:
        print("In Lease CRON Function")
        response = db.execute("""SELECT * 
                                FROM pm.rentals r 
                                LEFT JOIN
                                pm.leaseTenants lt 
                                ON lt.linked_rental_uid = r.rental_uid
                                WHERE r.lease_end < DATE_FORMAT(NOW(), "%Y-%m-%d") 
                                OR r.lease_end = DATE_FORMAT(NOW(), "%Y-%m-%d") 
                                AND r.rental_status='ACTIVE'; """)

        if len(response['result']) > 0:
            for i in range(len(response['result'])):
                print(i)
                pk = {
                    'rental_uid': response['result'][i]['rental_uid']}
                updateLeaseEnd = {
                    'lease_end': (date.fromisoformat(
                        response['result'][i]['lease_end']) + relativedelta(months=1)).isoformat()}
                print(pk, updateLeaseEnd)
                res = db.update('rentals', pk, updateLeaseEnd)
                print(res)

                tenants = response['result'][0]['linked_tenant_id']
                # print('tenants1', tenants)
                if '[' in tenants:
                    # print('tenants2', tenants)
                    tenants = json.loads(tenants)
                    # print('tenants3', tenants)
                # print('tenants4', tenants)
                if type(tenants) == str:
                    tenants = [tenants]
                    # print('tenants5', tenants)
                print('tenant_id', tenants)
                payment = json.loads(
                    response['result'][i]['rent_payments'])
                print(payment, len(payment))

                for r in range(len(payment)):
                    if payment[r]['fee_name'] == 'Rent':
                        print('RENT', payment[r]['fee_name'])
                        payment_date = alpha2digit(
                            response['result'][i]['due_by'], 'en')[:-2]
                        charge_date = date.today()
                        charge_month = charge_date.strftime(
                            '%B')
                        print(charge_date, charge_month)
                        purchaseResponse = newPurchase(
                            linked_bill_id=None,
                            pur_property_id=response['result'][i]['rental_property_id'],
                            payer=json.dumps(tenants),
                            receiver=response['result'][i]['rental_property_id'],
                            purchase_type='RENT',
                            description=payment[r]['fee_name'],
                            amount_due=payment[r]['charge'],
                            purchase_notes=charge_month,
                            purchase_date=charge_date.isoformat(),
                            purchase_frequency=payment[r]['frequency'],
                            next_payment=charge_date.replace(
                                day=int(payment_date))
                        )

    return purchaseResponse


class LateFee_CLASS(Resource):
    def get(self):

        with connect() as db:
            response = db.execute("""SELECT * 
                                    FROM pm.rentals r 
                                    LEFT JOIN
                                    pm.leaseTenants lt 
                                    ON lt.linked_rental_uid = r.rental_uid
                                    WHERE r.lease_end < DATE_FORMAT(NOW(), "%Y-%m-%d") 
                                    OR r.lease_end = DATE_FORMAT(NOW(), "%Y-%m-%d") 
                                    AND r.rental_status='ACTIVE'; """)

            if len(response['result']) > 0:
                for i in range(len(response['result'])):
                    print(response['result'][i]['rental_uid'])

                    pk = {
                        'rental_uid': response['result'][i]['rental_uid']}
                    updateLeaseEnd = {
                        'lease_end': (date.fromisoformat(
                            response['result'][i]['lease_end']) + relativedelta(months=1)).isoformat()}
                    print(pk, updateLeaseEnd)
                    res = db.update('rentals', pk, updateLeaseEnd)
                    print(res)
                    # res = db.execute("""UPDATE pm.rentals SET lease_end = DATE_ADD(lease_end, INTERVAL 1 MONTH) WHERE rental_uid = \'""" +
                    #                  response['result'][i]['rental_uid'] + """\';""")

                    tenants = response['result'][0]['linked_tenant_id']
                    # print('tenants1', tenants)
                    if '[' in tenants:
                        # print('tenants2', tenants)
                        tenants = json.loads(tenants)
                        # print('tenants3', tenants)
                    # print('tenants4', tenants)
                    if type(tenants) == str:
                        tenants = [tenants]
                        # print('tenants5', tenants)
                    print('tenant_id', tenants)
                    payment = json.loads(
                        response['result'][i]['rent_payments'])
                    print(payment, len(payment))

                    for r in range(len(payment)):
                        if payment[r]['fee_name'] == 'Rent':
                            print('RENT', payment[r]['fee_name'])
                            payment_date = alpha2digit(
                                response['result'][i]['due_by'], 'en')[:-2]
                            charge_date = date.today()
                            charge_month = charge_date.strftime(
                                '%B')
                            print(charge_date, charge_month)
                            purchaseResponse = newPurchase(
                                linked_bill_id=None,
                                pur_property_id=response['result'][i]['rental_property_id'],
                                payer=json.dumps(tenants),
                                receiver=response['result'][i]['rental_property_id'],
                                purchase_type='RENT',
                                description=payment[r]['fee_name'],
                                amount_due=payment[r]['charge'],
                                purchase_notes=charge_month,
                                purchase_date=charge_date.isoformat(),
                                purchase_frequency=payment[r]['frequency'],
                                next_payment=charge_date.replace(
                                    day=int(payment_date))
                            )

        return purchaseResponse
