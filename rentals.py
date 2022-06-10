
from flask import request
from flask_restful import Resource

import boto3
from data import connect, uploadImage, s3
import json
from purchases import newPurchase
from datetime import date, datetime
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
                      'rent_payments', 'assigned_contacts', 'rental_status', 'due_by', 'late_by', 'late_fee', 'perDay_late_fee', 'adult_occupants', 'children_occupants']
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
                                    LEFT JOIN
                                    pm.propertyManager p 
                                    ON p.linked_property_id = r.rental_property_id
                                    WHERE r.lease_end < DATE_FORMAT(NOW(), "%Y-%m-%d")
                                    OR r.lease_end = DATE_FORMAT(NOW(), "%Y-%m-%d")
                                    AND r.rental_status='ACTIVE'
                                    AND p.management_status= 'ACCEPTED'; """)

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

                            charge_date = date.today()
                            due_date = charge_date.replace(
                                day=int(response['result'][i]['due_by']))
                            charge_month = charge_date.strftime(
                                '%B')
                            print(charge_date, charge_month)
                            purchaseResponse = newPurchase(
                                linked_bill_id=None,
                                pur_property_id=response['result'][i]['rental_property_id'],
                                payer=json.dumps(tenants),
                                receiver=response['result'][i]['linked_business_id'],
                                purchase_type='RENT',
                                description=payment[r]['fee_name'],
                                amount_due=payment[r]['charge'],
                                purchase_notes=charge_month,
                                purchase_date=charge_date.isoformat(),
                                purchase_frequency=payment[r]['frequency'],
                                next_payment=due_date
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
                                LEFT JOIN
                                pm.propertyManager p 
                                ON p.linked_property_id = r.rental_property_id
                                WHERE r.lease_end < DATE_FORMAT(NOW(), "%Y-%m-%d")
                                OR r.lease_end = DATE_FORMAT(NOW(), "%Y-%m-%d")
                                AND r.rental_status='ACTIVE' 
                                AND p.management_status= 'ACCEPTED'; """)

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

                        charge_date = date.today()
                        due_date = charge_date.replace(
                            day=int(response['result'][i]['due_by']))
                        charge_month = charge_date.strftime(
                            '%B')
                        print(charge_date, charge_month)
                        purchaseResponse = newPurchase(
                            linked_bill_id=None,
                            pur_property_id=response['result'][i]['rental_property_id'],
                            payer=json.dumps(tenants),
                            receiver=response['result'][i]['linked_business_id'],
                            purchase_type='RENT',
                            description=payment[r]['fee_name'],
                            amount_due=payment[r]['charge'],
                            purchase_notes=charge_month,
                            purchase_date=charge_date.isoformat(),
                            purchase_frequency=payment[r]['frequency'],
                            next_payment=due_date
                        )

    return purchaseResponse


class LateFee_CLASS(Resource):
    def get(self):

        with connect() as db:
            purchaseResponse = {'message': 'Successfully committed SQL query',
                                'code': 200}
            response = db.execute("""SELECT * 
                                    FROM pm.rentals r 
                                    LEFT JOIN
                                    pm.leaseTenants lt 
                                    ON lt.linked_rental_uid = r.rental_uid
                                    LEFT JOIN
                                    pm.propertyManager p 
                                    ON p.linked_property_id = r.rental_property_id
                                    WHERE r.lease_start < DATE_FORMAT(NOW(), "%Y-%m-%d")
                                    AND r.lease_end > DATE_FORMAT(NOW(), "%Y-%m-%d")
                                    AND r.rental_status='ACTIVE' 
                                    AND p.management_status= 'ACCEPTED'; """)

            if len(response['result']) > 0:
                for i in range(len(response['result'])):
                    # today date
                    today_date = date.today()
                    # convert due_by to due_date
                    print('')
                    # calculate rent due date
                    due_date = today_date.replace(
                        day=int(response['result'][i]['due_by']))
                    print('due_date', due_date)
                    # calculate the date rent will be late
                    late_date = due_date + \
                        relativedelta(
                            days=int(response['result'][i]['late_by']))
                    print(response['result'][i]['late_by'], late_date)
                    # get unpaid rent for the current month from purchases
                    res = db.execute("""SELECT *
                                    FROM pm.purchases p
                                    WHERE p.purchase_status='UNPAID' 
                                    AND p.purchase_type='RENT' 
                                    AND p.purchase_notes= \'""" + today_date.strftime('%B') + """\' 
                                    AND p.pur_property_id = \'""" + response['result'][i]['rental_property_id'] + """\'; """)

                    if len(res['result']) > 0:
                        for j in range(len(res['result'])):
                            # if late date == today's date enter late fee info in the payments
                            if late_date == today_date:
                                print(today_date, late_date)

                                purchaseResponse = newPurchase(
                                    linked_bill_id=None,
                                    pur_property_id=response['result'][i]['rental_property_id'],
                                    payer=response['result'][i]['linked_tenant_id'],
                                    receiver=response['result'][i]['linked_business_id'],
                                    purchase_type='EXTRA CHARGES',
                                    description='Late Fee',
                                    amount_due=response['result'][i]['late_fee'],
                                    purchase_notes=today_date.strftime('%B'),
                                    purchase_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    purchase_frequency='One-time',
                                    next_payment=today_date.isoformat()
                                )

        return purchaseResponse


def LateFee():
    print("In Late Fee")
    from purchases import newPurchase
    from datetime import date, datetime
    from dateutil.relativedelta import relativedelta

    with connect() as db:
        print("In Late Fee CRON Function")
        purchaseResponse = {'message': 'Successfully committed SQL query',
                            'code': 200}
        response = db.execute("""SELECT * 
                                FROM pm.rentals r 
                                LEFT JOIN
                                pm.leaseTenants lt 
                                ON lt.linked_rental_uid = r.rental_uid
                                LEFT JOIN
                                pm.propertyManager p 
                                ON p.linked_property_id = r.rental_property_id
                                WHERE r.lease_start < DATE_FORMAT(NOW(), "%Y-%m-%d")
                                AND r.lease_end > DATE_FORMAT(NOW(), "%Y-%m-%d")
                                AND r.rental_status='ACTIVE' 
                                AND p.management_status= 'ACCEPTED'; """)

        if len(response['result']) > 0:
            for i in range(len(response['result'])):
                # today date
                today_date = date.today()
                # convert due_by to due_date
                print(response['result'][i])

                # calculate rent due date
                due_date = today_date.replace(
                    day=int(response['result'][i]['due_by']))
                print('due_date', due_date)
                # calculate the date rent will be late
                late_date = due_date + \
                    relativedelta(
                        days=int(response['result'][i]['late_by']))
                print(response['result'][i]['late_by'], late_date)
                # get unpaid rent for the current month from purchases
                res = db.execute("""SELECT *
                                FROM pm.purchases p
                                WHERE p.purchase_status='UNPAID' 
                                AND p.purchase_type='RENT' 
                                AND p.purchase_notes= \'""" + today_date.strftime('%B') + """\' 
                                AND p.pur_property_id = \'""" + response['result'][i]['rental_property_id'] + """\'; """)

                if len(res['result']) > 0:
                    for j in range(len(res['result'])):
                        # if late date == today's date enter late fee info in the payments
                        if late_date == today_date:
                            print(today_date, late_date)

                            purchaseResponse = newPurchase(
                                linked_bill_id=None,
                                pur_property_id=response['result'][i]['rental_property_id'],
                                payer=response['result'][i]['linked_tenant_id'],
                                receiver=response['result'][i]['linked_business_id'],
                                purchase_type='EXTRA CHARGES',
                                description='Late Fee',
                                amount_due=response['result'][i]['late_fee'],
                                purchase_notes=today_date.strftime('%B'),
                                purchase_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                purchase_frequency='One-time',
                                next_payment=today_date.isoformat()
                            )

    return purchaseResponse


class PerDay_LateFee_CLASS(Resource):
    def get(self):
        updateLF = {'message': 'Successfully committed SQL query',
                    'code': 200}
        with connect() as db:
            response = db.execute("""SELECT * 
                                    FROM pm.rentals r 
                                    LEFT JOIN
                                    pm.leaseTenants lt 
                                    ON lt.linked_rental_uid = r.rental_uid
                                    LEFT JOIN
                                    pm.propertyManager p 
                                    ON p.linked_property_id = r.rental_property_id
                                    WHERE r.lease_start < DATE_FORMAT(NOW(), "%Y-%m-%d")
                                    AND r.lease_end > DATE_FORMAT(NOW(), "%Y-%m-%d")
                                    AND r.rental_status='ACTIVE' 
                                    AND p.management_status= 'ACCEPTED'; """)

            if len(response['result']) > 0:
                for i in range(len(response['result'])):
                    # today date
                    today_date = date.today()
                    # convert due_by to due_date
                    print(response['result'][i])

                    # calculate rent due date
                    due_date = today_date.replace(
                        day=int(response['result'][i]['due_by']))
                    # print('due_date', payment_date, due_date)
                    # calculate the date rent will be late
                    late_date = due_date + \
                        relativedelta(
                            days=int(response['result'][i]['late_by']))
                    # print(response['result'][i]['late_by'], late_date)
                    # get unpaid rent for the current month from purchases
                    res = db.execute("""SELECT *
                                    FROM pm.purchases p
                                    WHERE p.purchase_status='UNPAID' 
                                    AND p.purchase_type='RENT' 
                                    AND p.purchase_notes= \'""" + today_date.strftime('%B') + """\' 
                                    AND p.pur_property_id = \'""" + response['result'][i]['rental_property_id'] + """\'; """)

                    if len(res['result']) > 0:
                        for j in range(len(res['result'])):
                            if response['result'][i]['perDay_late_fee'] == 0:
                                print('Do nothing')
                            else:
                                latePurResponse = db.execute("""SELECT *
                                                                FROM pm.purchases p
                                                                WHERE p.pur_property_id = \'""" + response['result'][i]['rental_property_id'] + """\'
                                                                AND p.purchase_notes = \'""" + date.today().strftime('%B') + """\'
                                                                AND p.description = 'Late Fee'
                                                                AND p.purchase_status='UNPAID'; """)

                                if len(latePurResponse['result']) > 0:
                                    for k in range(len(latePurResponse['result'])):
                                        pk = {
                                            "purchase_uid": latePurResponse['result'][k]['purchase_uid']
                                        }
                                        print(pk)
                                        updateLateFee = {
                                            "amount_due": int(latePurResponse['result'][k]['amount_due']) + int(response['result'][i]['perDay_late_fee']),
                                            "purchase_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                        }
                                        updateLF = db.update(
                                            'purchases', pk, updateLateFee)
                                else:
                                    print('do nothing')

        return updateLF


def PerDay_LateFee():
    print("In Per day Late Fee")
    from datetime import date, datetime
    from dateutil.relativedelta import relativedelta

    with connect() as db:
        print("In per day late fee CRON Function")
        updateLF = {'message': 'Successfully committed SQL query',
                    'code': 200}
        with connect() as db:
            response = db.execute("""SELECT * 
                                    FROM pm.rentals r 
                                    LEFT JOIN
                                    pm.leaseTenants lt 
                                    ON lt.linked_rental_uid = r.rental_uid
                                    LEFT JOIN
                                    pm.propertyManager p 
                                    ON p.linked_property_id = r.rental_property_id
                                    WHERE r.lease_start < DATE_FORMAT(NOW(), "%Y-%m-%d")
                                    AND r.lease_end > DATE_FORMAT(NOW(), "%Y-%m-%d")
                                    AND r.rental_status='ACTIVE' 
                                    AND p.management_status= 'ACCEPTED'; """)

            if len(response['result']) > 0:
                for i in range(len(response['result'])):
                    # today date
                    today_date = date.today()
                    # convert due_by to due_date
                    print(response['result'][i])

                    # calculate rent due date
                    due_date = today_date.replace(
                        day=int(response['result'][i]['due_by']))
                    # print('due_date', payment_date, due_date)
                    # calculate the date rent will be late
                    late_date = due_date + \
                        relativedelta(
                            days=int(response['result'][i]['late_by']))
                    # print(response['result'][i]['late_by'], late_date)
                    # get unpaid rent for the current month from purchases
                    res = db.execute("""SELECT *
                                    FROM pm.purchases p
                                    WHERE p.purchase_status='UNPAID' 
                                    AND p.purchase_type='RENT' 
                                    AND p.purchase_notes= \'""" + today_date.strftime('%B') + """\' 
                                    AND p.pur_property_id = \'""" + response['result'][i]['rental_property_id'] + """\'; """)

                    if len(res['result']) > 0:
                        for j in range(len(res['result'])):
                            if response['result'][i]['perDay_late_fee'] == 0:
                                print('Do nothing')
                            else:
                                latePurResponse = db.execute("""SELECT *
                                                                FROM pm.purchases p
                                                                WHERE p.pur_property_id = \'""" + response['result'][i]['rental_property_id'] + """\'
                                                                AND p.purchase_notes = \'""" + date.today().strftime('%B') + """\'
                                                                AND p.description = 'Late Fee'
                                                                AND p.purchase_status='UNPAID'; """)

                                if len(latePurResponse['result']) > 0:
                                    for k in range(len(latePurResponse['result'])):
                                        pk = {
                                            "purchase_uid": latePurResponse['result'][k]['purchase_uid']
                                        }
                                        print(pk)
                                        updateLateFee = {
                                            "amount_due": int(latePurResponse['result'][k]['amount_due']) + int(response['result'][i]['perDay_late_fee']),
                                            "purchase_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                        }
                                        updateLF = db.update(
                                            'purchases', pk, updateLateFee)
                                else:
                                    print('do nothing')

        return updateLF
