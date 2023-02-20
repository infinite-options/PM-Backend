from flask import request
from flask_restful import Resource

import boto3
from data import connect, uploadImage, s3
import json
from purchases import newPurchase
from datetime import date, timedelta, datetime
import calendar
from calendar import monthrange
from dateutil.relativedelta import relativedelta
from text_to_num import alpha2digit


def next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    return d + timedelta(days_ahead)


def next_weekday_biweekly(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 14
    return d + timedelta(days_ahead)


def updateDocuments(documents, rental_uid):
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
    bucket.objects.filter(Prefix=f'rentals/{rental_uid}/').delete()
    docs = []
    for i, doc in enumerate(documents):

        filename = f'doc_{i}'
        key = f'rentals/{rental_uid}/{filename}'
        # print(type(doc['file']))
        link = uploadImage(doc['file'], key, content[i])
        # print('link', link)
        doc['link'] = link
        del doc['file']
        docs.append(doc)
    return docs


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
            fields = ['rental_property_id', 'linked_application_id', 'actual_rent', 'lease_start', 'lease_end',
                      'rent_payments', 'assigned_contacts', 'rental_status', 'available_topay', 'due_by', 'late_by', 'late_fee', 'perDay_late_fee', 'adults', 'children', 'pets', 'vehicles', 'referred', "effective_date"]
            newRental = {}
            for field in fields:
                newRental[field] = data.get(field)

            newRentalID = db.call('new_rental_id')['result'][0]['new_id']
            newRental['rental_uid'] = newRentalID

            # newRental['rental_status'] = 'ACTIVE'
            print('newRental', newRental)
            documents = json.loads(data.get('documents'))
            for i in range(len(documents)):
                filename = f'doc_{i}'
                file = request.files.get(filename)
                if file:
                    key = f'rentals/{newRentalID}/{filename}'
                    doc = uploadImage(file, key, '')
                    documents[i]['link'] = doc
                else:
                    break
            newRental['documents'] = json.dumps(documents)
            print('newRental', newRental)
            response = db.insert('rentals', newRental)
            print(response)
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
            fields = ['rental_property_id', 'actual_rent', 'lease_start', 'lease_end',
                      'rent_payments', 'assigned_contacts', 'rental_status', 'available_topay', 'due_by', 'late_by', 'late_fee', 'perDay_late_fee', 'pets', 'vehicles', 'referred', 'adults', 'children', "effective_date"]
            newRental = {}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    newRental[field] = fieldValue
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


class UpdateActiveLease(Resource):
    def put(self):
        data = request.json
        with connect() as db:
            rental_pk = {
                'rental_uid': data['rental_uid']
            }
            # print(data)
            fields = ['linked_application_id', 'rental_property_id', 'actual_rent', 'lease_start', 'lease_end',
                      'rent_payments', 'assigned_contacts', 'rental_status', 'available_topay', 'due_by', 'late_by', 'late_fee', 'perDay_late_fee', 'pets', 'vehicles', 'referred', 'adults', 'children', 'effective_date']
            updatedRental = {}
            newApplication = {}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    updatedRental[field] = fieldValue
            linked_application_id = (data.get('linked_application_id'))
            if linked_application_id is not None and len(linked_application_id) > 0:
                updatedRental['linked_application_id'] = json.dumps(
                    [linked_application_id])
            rent_payments = (data.get('rent_payments'))
            if rent_payments is not None and len(rent_payments) > 0:
                updatedRental['rent_payments'] = json.dumps(rent_payments)

            assigned_contacts = (data.get('assigned_contacts'))
            if assigned_contacts is not None and len(assigned_contacts) > 0:
                updatedRental['assigned_contacts'] = json.dumps(
                    assigned_contacts)

            adults = (data.get('adults'))
            if adults is not None and len(adults) > 0:
                updatedRental['adults'] = json.dumps(adults)

            children = (data.get('children'))
            if children is not None and len(children) > 0:
                updatedRental['children'] = json.dumps(children)
            pets = (data.get('pets'))
            if pets is not None and len(pets) > 0:
                updatedRental['pets'] = json.dumps(pets)
            vehicles = (data.get('vehicles'))
            if vehicles is not None and len(vehicles) > 0:
                updatedRental['vehicles'] = json.dumps(vehicles)
            referred = (data.get('referred'))
            if referred is not None and len(referred) > 0:
                updatedRental['referred'] = json.dumps(referred)
            documents = (data.get('documents'))
            if documents is not None and len(documents) > 0:
                updatedRental['documents'] = json.dumps(documents)
            # print(updatedRental)
            if updatedRental['rental_status'] == 'ACTIVE':
                # newApplication['application_status'] = 'RENTED'
                # pk = {
                #     'application_uid': data['linked_application_id']
                # }
                # response = db.update(
                #     'applications', pk, newApplication)
                getRentInfo = db.execute("""
                SELECT  r.*, p.*,
                GROUP_CONCAT(lt.linked_tenant_id) as `tenants`,c.* ,prop.*
                FROM pm.rentals r
                LEFT JOIN pm.properties prop
                ON prop.property_uid = r.rental_property_id
                LEFT JOIN pm.leaseTenants lt
                ON lt.linked_rental_uid = r.rental_uid
                LEFT JOIN pm.propertyManager p
                ON p.linked_property_id= r.rental_property_id
                LEFT JOIN pm.contracts c
                ON c.property_uid = prop.property_uid
                WHERE r.rental_status='ACTIVE'
                AND c.contract_status = 'ACTIVE'
                AND (p.management_status = 'ACCEPTED' OR p.management_status='END EARLY' OR p.management_status='PM END EARLY' OR p.management_status='OWNER END EARLY')
                AND r.rental_uid = \'""" + data['rental_uid'] + """\' 
                AND r.linked_application_id LIKE '%""" + updatedRental['linked_application_id'] + """%'
                GROUP BY lt.linked_rental_uid;""")
                print(getRentInfo)
                if len(getRentInfo['result']) > 0:

                    for i in range(len(getRentInfo['result'])):
                        getRentInfo['result'][i]['expense_amount'] = 0
                        purRes = db.execute("""
                        SELECT * FROM purchases pur
                        WHERE pur.pur_property_id= \'""" + getRentInfo['result'][i]['property_uid'] + """\'
                        AND (pur.purchase_type = 'UTILITY' OR pur.purchase_type = 'MAINTENANCE' OR pur.purchase_type = 'REPAIRS') """)
                        getRentInfo['result'][i]['expenses'] = list(
                            purRes['result'])
                        if len(purRes['result']) > 0:
                            for ore in range(len(purRes['result'])):
                                getRentInfo['result'][i]['expense_amount'] = getRentInfo['result'][i]['expense_amount'] + int(
                                    purRes['result'][ore]['amount_due'])
                tenants = getRentInfo['result'][0]['tenants']
                if '[' in tenants:
                    tenants = json.loads(tenants)
                if type(tenants) == str:
                    tenants = [tenants]
                # print(tenants)
                today = date.today()
                start_date = date.fromisoformat(
                    getRentInfo['result'][0]['lease_start'])
                end_date = date.fromisoformat(
                    getRentInfo['result'][0]['lease_start'])
                effective_date = date.fromisoformat(
                    getRentInfo['result'][0]['effective_date'])

                # print('today', today)
                # print('start_date', start_date)
                # print('effective_date', effective_date)

                if len(getRentInfo['result']) > 0:
                    # creating purchases
                    rentPayments = json.loads(
                        getRentInfo['result'][0]['rent_payments'])
                    managementPayments = json.loads(
                        getRentInfo['result'][0]['contract_fees'])
                    # effective date in future

                    if effective_date > today:
                        print('effective date > today')
                        for payment in rentPayments:
                            due_date = (datetime.now().replace(
                                day=int(payment['due_by']))).date()
                            # print(due_date)
                            if len(payment['available_topay']) == 0:
                                available_date = due_date
                                # print('available_date',
                                #   available_date)
                            else:
                                available_date = due_date - \
                                    timedelta(
                                        days=int(payment['available_topay']))
                            # print(available_date)
                            # available to pay in future, dont do anything
                            if available_date > today:
                                print('available to pay > today, dont do anything')
                            # available to pay in past, check if anything unpaid
                            elif available_date <= today and due_date > today:
                                print('available date in past, due date in future')
                                # if anything unpaid, delete and add new
                                pur_response = db.execute("""
                                SELECT * FROM pm.purchases
                                WHERE pur_property_id LIKE '%""" + getRentInfo['result'][0]['rental_property_id'] + """%'
                                AND (purchase_type = "EXTRA CHARGES" OR purchase_type = "RENT")
                                AND description = \'""" + payment['fee_name'] + """\'  """)
                                if len(pur_response['result']) > 0:
                                    for purchase in pur_response['result']:
                                        if(purchase['purchase_status'] == 'UNPAID' and purchase['purchase_date'] <= getRentInfo['result'][0]['effective_date'] and purchase['next_payment'] > getRentInfo['result'][0]['effective_date']):
                                            # print('in purchase', purchase)
                                            purchaseResponse = newPurchase(
                                                linked_bill_id=None,
                                                pur_property_id=json.dumps(
                                                    [getRentInfo['result'][0]['rental_property_id']]),
                                                payer=purchase['payer'],
                                                receiver=purchase['receiver'],
                                                purchase_type=purchase['purchase_type'],
                                                description=purchase['description'],
                                                amount_due=payment['charge'],
                                                purchase_notes=purchase['purchase_notes'],
                                                purchase_date=effective_date.isoformat(),
                                                purchase_frequency=purchase['purchase_frequency'],
                                                next_payment=due_date
                                            )
                                            pur_response = db.delete("""
                                DELETE FROM pm.purchases
                                WHERE purchase_uid = \'""" + purchase['purchase_uid'] + """\'""")
                            else:
                                print('available date in past, due date in past')
                    else:
                        print('effective date < today')

                        unpaidPurchases = db.execute("""
                            SELECT * FROM pm.purchases
                            WHERE pur_property_id LIKE '%""" + getRentInfo['result'][0]['rental_property_id'] + """%'
                            AND DATE(purchase_date) >= DATE(\'""" + getRentInfo['result'][0]['effective_date'] + """\')
                            AND (purchase_type ='RENT' OR purchase_type='EXTRA CHARGES')
                            AND purchase_status ="UNPAID" """)
                        unpaidEntries = []
                        if len(unpaidPurchases['result']) > 0:

                            for unpaid in unpaidPurchases['result']:
                                if(any(unpaid['description'] == payment['fee_name'] for payment in rentPayments)):
                                    print('do nothing')
                                else:
                                    print(unpaid['description'])
                                    unpaidEntries.append(unpaid)

                        # delete older purchases no longer added
                        for unpaid in unpaidEntries:
                            delUnpaid = db.execute(
                                """DELETE FROM pm.purchases WHERE purchase_uid = \'""" + unpaid['purchase_uid'] + """\'""")
                        for payment in rentPayments:
                            newEntries = []
                            paidEntries = []
                            filteredEntries = []
                            print('payment fee name:', payment['fee_name'])
                            # delete older unpaid purchase records

                            due_date = (start_date.replace(
                                day=int(payment['due_by'])) + relativedelta(months=1))

                            if len(payment['available_topay']) == 0:
                                available_date = due_date
                            else:
                                available_date = due_date - \
                                    timedelta(
                                        days=int(payment['available_topay']))

                            print('effective date:', effective_date)
                            print('due date:', due_date)
                            print('available date:', available_date)

                            charge_date = (effective_date).strftime(
                                '%Y-%m-%d %H:%M:%S')
                            effective_date_str = datetime.strptime(
                                charge_date, '%Y-%m-%d %H:%M:%S').date()
                            due_date = effective_date_str.replace(
                                day=int(payment['due_by']))
                            if len(payment['available_topay']) == 0:
                                available_date = due_date

                            else:
                                available_date = due_date - \
                                    timedelta(
                                        days=int(payment['available_topay']))

                            if payment['frequency'] == 'Weekly':
                                print('weekly')
                                due_date = next_weekday(
                                    effective_date_str,  int(payment['due_by']))
                                if len(payment['available_topay']) == 0:
                                    available_date = due_date
                                else:
                                    available_date = due_date - \
                                        timedelta(
                                            days=int(payment['available_topay']))
                                while due_date < today:
                                    # if(available_date > effective_date or (available_date < effective_date and due_date > effective_date)):
                                    if(due_date >= effective_date):
                                        newPurchase = {
                                            "linked_bill_id": None,
                                            "pur_property_id": json.dumps(
                                                [getRentInfo['result'][0]['rental_property_id']]),
                                            "payer": json.dumps(tenants),
                                            "receiver": getRentInfo['result'][0]['linked_business_id'],
                                            "purchase_type": 'RENT' if payment['fee_name'] == 'Rent' else 'EXTRA CHARGES',
                                            "description": payment['fee_name'],
                                            "amount_due": payment['charge'],
                                            "amount_paid": 0,
                                            "purchase_notes": due_date.strftime(
                                                '%B'),
                                            "purchase_date": effective_date.isoformat(),
                                            "purchase_frequency": payment['frequency'],
                                            "next_payment": due_date,
                                            "purchase_status": 'UNPAID'
                                        }
                                        newEntries.append(newPurchase)

                                        if(payment['fee_name'] == 'Rent'):
                                            rent = int(payment['charge'])
                                            for mpayment in managementPayments:
                                                weeks_current_month = len(
                                                    calendar.monthcalendar(due_date.year, int(due_date.strftime("%m"))))
                                                if mpayment['frequency'] == 'Weekly' and mpayment['fee_type'] == '%':
                                                    if mpayment['of'] == 'Gross Rent':
                                                        newPurchase = {
                                                            "linked_bill_id": None,
                                                            "pur_property_id": json.dumps(
                                                                [getRentInfo['result'][0]['property_uid']]),
                                                            "payer": json.dumps(
                                                                [getRentInfo['result'][0]['business_uid']]),
                                                            "receiver": getRentInfo['result'][0]['owner_id'],
                                                            "purchase_type": 'OWNER PAYMENT RENT',
                                                            "description": 'Rent',
                                                            "amount_due": (rent *
                                                                           (1-int(mpayment['charge'])/100)),
                                                            "amount_paid": 0,
                                                            "purchase_notes": due_date.strftime(
                                                                '%B'),
                                                            "purchase_date": effective_date.isoformat(),
                                                            "purchase_frequency": mpayment['frequency'],
                                                            "next_payment": due_date,
                                                            "purchase_status": 'UNPAID'
                                                        }
                                                        newEntries.append(
                                                            newPurchase)

                                                    # if net rent (listed rent-expenses)
                                                    else:
                                                        newPurchase = {
                                                            "linked_bill_id": None,
                                                            "pur_property_id": json.dumps(
                                                                [getRentInfo['result'][0]['property_uid']]),
                                                            "payer": json.dumps(
                                                                [getRentInfo['result'][0]['business_uid']]),
                                                            "receiver": getRentInfo['result'][0]['owner_id'],
                                                            "purchase_type": 'OWNER PAYMENT RENT',
                                                            "description": 'Rent',
                                                            "amount_due": ((rent-mpayment['expense_amount'])*(
                                                                1-int(mpayment['charge'])/100)),
                                                            "amount_paid": 0,
                                                            "purchase_notes": due_date.strftime(
                                                                '%B'),
                                                            "purchase_date": effective_date.isoformat(),
                                                            "purchase_frequency": mpayment['frequency'],
                                                            "next_payment": due_date,
                                                            "purchase_status": 'UNPAID'
                                                        }
                                                        newEntries.append(
                                                            newPurchase)

                                                elif mpayment['frequency'] == 'Biweekly' and mpayment['fee_type'] == '%':
                                                    if mpayment['of'] == 'Gross Rent':
                                                        newPurchase = {
                                                            "linked_bill_id": None,
                                                            "pur_property_id": json.dumps(
                                                                [getRentInfo['result'][0]['property_uid']]),
                                                            "payer": json.dumps(
                                                                [getRentInfo['result'][0]['business_uid']]),
                                                            "receiver": getRentInfo['result'][0]['owner_id'],
                                                            "purchase_type": 'OWNER PAYMENT RENT',
                                                            "description": 'Rent',
                                                            "amount_due": ((rent *
                                                                            (1-int(mpayment['charge'])/100)))/weeks_current_month/2,
                                                            "amount_paid": 0,
                                                            "purchase_notes": due_date.strftime(
                                                                '%B'),
                                                            "purchase_date": effective_date.isoformat(),
                                                            "purchase_frequency": mpayment['frequency'],
                                                            "next_payment": due_date,
                                                            "purchase_status": 'UNPAID'
                                                        }
                                                        newEntries.append(
                                                            newPurchase)

                                                    # if net rent (listed rent-expenses)
                                                    else:
                                                        newPurchase = {
                                                            "linked_bill_id": None,
                                                            "pur_property_id": json.dumps(
                                                                [getRentInfo['result'][0]['property_uid']]),
                                                            "payer": json.dumps(
                                                                [getRentInfo['result'][0]['business_uid']]),
                                                            "receiver": getRentInfo['result'][0]['owner_id'],
                                                            "purchase_type": 'OWNER PAYMENT RENT',
                                                            "description": 'Rent',
                                                            "amount_due": ((rent-mpayment['expense_amount'])*(
                                                                1-int(mpayment['charge'])/100))/weeks_current_month/2,
                                                            "amount_paid": 0,
                                                            "purchase_notes": due_date.strftime(
                                                                '%B'),
                                                            "purchase_date": effective_date.isoformat(),
                                                            "purchase_frequency": mpayment['frequency'],
                                                            "next_payment": due_date,
                                                            "purchase_status": 'UNPAID'
                                                        }
                                                        newEntries.append(
                                                            newPurchase)

                                                elif mpayment['frequency'] == 'Monthly' and mpayment['fee_type'] == '%':
                                                    if mpayment['of'] == 'Gross Rent':
                                                        newPurchase = {
                                                            "linked_bill_id": None,
                                                            "pur_property_id": json.dumps(
                                                                [getRentInfo['result'][0]['property_uid']]),
                                                            "payer": json.dumps(
                                                                [getRentInfo['result'][0]['business_uid']]),
                                                            "receiver": getRentInfo['result'][0]['owner_id'],
                                                            "purchase_type": 'OWNER PAYMENT RENT',
                                                            "description": 'Rent',
                                                            "amount_due": ((rent *
                                                                            (1-int(mpayment['charge'])/100)))/weeks_current_month,
                                                            "amount_paid": 0,
                                                            "purchase_notes": due_date.strftime(
                                                                '%B'),
                                                            "purchase_date": effective_date.isoformat(),
                                                            "purchase_frequency": mpayment['frequency'],
                                                            "next_payment": due_date,
                                                            "purchase_status": 'UNPAID'
                                                        }
                                                        newEntries.append(
                                                            newPurchase)

                                                    # if net rent (listed rent-expenses)
                                                    else:
                                                        newPurchase = {
                                                            "linked_bill_id": None,
                                                            "pur_property_id": json.dumps(
                                                                [getRentInfo['result'][0]['property_uid']]),
                                                            "payer": json.dumps(
                                                                [getRentInfo['result'][0]['business_uid']]),
                                                            "receiver": getRentInfo['result'][0]['owner_id'],
                                                            "purchase_type": 'OWNER PAYMENT RENT',
                                                            "description": 'Rent',
                                                            "amount_due": ((rent-mpayment['expense_amount'])*(
                                                                1-int(mpayment['charge'])/100))/weeks_current_month,
                                                            "amount_paid": 0,
                                                            "purchase_notes": due_date.strftime(
                                                                '%B'),
                                                            "purchase_date": effective_date.isoformat(),
                                                            "purchase_frequency": mpayment['frequency'],
                                                            "next_payment": due_date,
                                                            "purchase_status": 'UNPAID'
                                                        }
                                                        newEntries.append(
                                                            newPurchase)

                                                else:
                                                    print(
                                                        'payment frequency one-time %')
                                    due_date += relativedelta(weeks=1)
                            elif payment['frequency'] == 'Biweekly':
                                print('biweekly')
                                due_date = next_weekday_biweekly(
                                    effective_date_str,  int(payment['due_by']))
                                if len(payment['available_topay']) == 0:
                                    available_date = due_date
                                else:
                                    available_date = due_date - \
                                        timedelta(
                                            days=int(payment['available_topay']))

                                while due_date < today:
                                    # if(available_date > effective_date or (available_date < effective_date and due_date > effective_date)):
                                    if(due_date >= effective_date):
                                        newPurchase = {
                                            "linked_bill_id": None,
                                            "pur_property_id": json.dumps(
                                                [getRentInfo['result'][0]['rental_property_id']]),
                                            "payer": json.dumps(tenants),
                                            "receiver": getRentInfo['result'][0]['linked_business_id'],
                                            "purchase_type": 'RENT' if payment['fee_name'] == 'Rent' else 'EXTRA CHARGES',
                                            "description": payment['fee_name'],
                                            "amount_due": payment['charge'],
                                            "amount_paid": 0,
                                            "purchase_notes": due_date.strftime(
                                                '%B'),
                                            "purchase_date": effective_date.isoformat(),
                                            "purchase_frequency": payment['frequency'],
                                            "next_payment": due_date,
                                            "purchase_status": 'UNPAID'
                                        }
                                        newEntries.append(
                                            newPurchase)

                                        if(payment['fee_name'] == 'Rent'):
                                            rent = int(payment['charge'])
                                            for mpayment in managementPayments:
                                                weeks_current_month = len(
                                                    calendar.monthcalendar(due_date.year, int(due_date.strftime("%m"))))
                                                if mpayment['frequency'] == 'Weekly' and mpayment['fee_type'] == '%':
                                                    if mpayment['of'] == 'Gross Rent':
                                                        newPurchase = {
                                                            "linked_bill_id": None,
                                                            "pur_property_id": json.dumps(
                                                                [getRentInfo['result'][0]['property_uid']]),
                                                            "payer": json.dumps(
                                                                [getRentInfo['result'][0]['business_uid']]),
                                                            "receiver": getRentInfo['result'][0]['owner_id'],
                                                            "purchase_type": 'OWNER PAYMENT RENT',
                                                            "description": 'Rent',
                                                            "amount_due": 2*(rent *
                                                                             (1-int(mpayment['charge'])/100)),
                                                            "amount_paid": 0,
                                                            "purchase_notes": due_date.strftime(
                                                                '%B'),
                                                            "purchase_date": effective_date.isoformat(),
                                                            "purchase_frequency": mpayment['frequency'],
                                                            "next_payment": due_date,
                                                            "purchase_status": 'UNPAID'
                                                        }
                                                        newEntries.append(
                                                            newPurchase)

                                                    # if net rent (listed rent-expenses)
                                                    else:
                                                        newPurchase = {
                                                            "linked_bill_id": None,
                                                            "pur_property_id": json.dumps(
                                                                [getRentInfo['result'][0]['property_uid']]),
                                                            "payer": json.dumps(
                                                                [getRentInfo['result'][0]['business_uid']]),
                                                            "receiver": getRentInfo['result'][0]['owner_id'],
                                                            "purchase_type": 'OWNER PAYMENT RENT',
                                                            "description": 'Rent',
                                                            "amount_due": 2*((rent-mpayment['expense_amount'])*(
                                                                1-int(mpayment['charge'])/100)),
                                                            "amount_paid": 0,
                                                            "purchase_notes": due_date.strftime(
                                                                '%B'),
                                                            "purchase_date": effective_date.isoformat(),
                                                            "purchase_frequency": mpayment['frequency'],
                                                            "next_payment": due_date,
                                                            "purchase_status": 'UNPAID'
                                                        }
                                                        newEntries.append(
                                                            newPurchase)

                                                elif mpayment['frequency'] == 'Biweekly' and mpayment['fee_type'] == '%':
                                                    if mpayment['of'] == 'Gross Rent':
                                                        newPurchase = {
                                                            "linked_bill_id": None,
                                                            "pur_property_id": json.dumps(
                                                                [getRentInfo['result'][0]['property_uid']]),
                                                            "payer": json.dumps(
                                                                [getRentInfo['result'][0]['business_uid']]),
                                                            "receiver": getRentInfo['result'][0]['owner_id'],
                                                            "purchase_type": 'OWNER PAYMENT RENT',
                                                            "description": 'Rent',
                                                            "amount_due": weeks_current_month/2*(rent *
                                                                                                 (1-int(mpayment['charge'])/100)),
                                                            "amount_paid": 0,
                                                            "purchase_notes": due_date.strftime(
                                                                '%B'),
                                                            "purchase_date": effective_date.isoformat(),
                                                            "purchase_frequency": mpayment['frequency'],
                                                            "next_payment": due_date,
                                                            "purchase_status": 'UNPAID'
                                                        }
                                                        newEntries.append(
                                                            newPurchase)

                                                    # if net rent (listed rent-expenses)
                                                    else:
                                                        newPurchase = {
                                                            "linked_bill_id": None,
                                                            "pur_property_id": json.dumps(
                                                                [getRentInfo['result'][0]['property_uid']]),
                                                            "payer": json.dumps(
                                                                [getRentInfo['result'][0]['business_uid']]),
                                                            "receiver": getRentInfo['result'][0]['owner_id'],
                                                            "purchase_type": 'OWNER PAYMENT RENT',
                                                            "description": 'Rent',
                                                            "amount_due": weeks_current_month/2*((rent-mpayment['expense_amount'])*(
                                                                1-int(mpayment['charge'])/100)),
                                                            "amount_paid": 0,
                                                            "purchase_notes": due_date.strftime(
                                                                '%B'),
                                                            "purchase_date": effective_date.isoformat(),
                                                            "purchase_frequency": mpayment['frequency'],
                                                            "next_payment": due_date,
                                                            "purchase_status": 'UNPAID'
                                                        }
                                                        newEntries.append(
                                                            newPurchase)

                                                elif mpayment['frequency'] == 'Monthly' and mpayment['fee_type'] == '%':
                                                    if mpayment['of'] == 'Gross Rent':
                                                        newPurchase = {
                                                            "linked_bill_id": None,
                                                            "pur_property_id": json.dumps(
                                                                [getRentInfo['result'][0]['property_uid']]),
                                                            "payer": json.dumps(
                                                                [getRentInfo['result'][0]['business_uid']]),
                                                            "receiver": getRentInfo['result'][0]['owner_id'],
                                                            "purchase_type": 'OWNER PAYMENT RENT',
                                                            "description": 'Rent',
                                                            "amount_due": (rent *
                                                                           (1-int(mpayment['charge'])/100))/(weeks_current_month/2),
                                                            "amount_paid": 0,
                                                            "purchase_notes": due_date.strftime(
                                                                '%B'),
                                                            "purchase_date": effective_date.isoformat(),
                                                            "purchase_frequency": mpayment['frequency'],
                                                            "next_payment": due_date,
                                                            "purchase_status": 'UNPAID'
                                                        }
                                                        newEntries.append(
                                                            newPurchase)

                                                    # if net rent (listed rent-expenses)
                                                    else:
                                                        newPurchase = {
                                                            "linked_bill_id": None,
                                                            "pur_property_id": json.dumps(
                                                                [getRentInfo['result'][0]['property_uid']]),
                                                            "payer": json.dumps(
                                                                [getRentInfo['result'][0]['business_uid']]),
                                                            "receiver": getRentInfo['result'][0]['owner_id'],
                                                            "purchase_type": 'OWNER PAYMENT RENT',
                                                            "description": 'Rent',
                                                            "amount_due": ((rent-mpayment['expense_amount'])*(
                                                                1-int(mpayment['charge'])/100))/(weeks_current_month/2),
                                                            "amount_paid": 0,
                                                            "purchase_notes": due_date.strftime(
                                                                '%B'),
                                                            "purchase_date": effective_date.isoformat(),
                                                            "purchase_frequency": mpayment['frequency'],
                                                            "next_payment": due_date,
                                                            "purchase_status": 'UNPAID'
                                                        }
                                                        newEntries.append(
                                                            newPurchase)

                                                else:
                                                    print(
                                                        'payment frequency one-time %')
                                    due_date += relativedelta(weeks=2)
                            elif payment['frequency'] == 'Monthly':
                                print('monthly')
                                while due_date < today:
                                    # if(available_date > effective_date or (available_date < effective_date and due_date > effective_date)):
                                    if(due_date >= effective_date):

                                        newPurchase = {
                                            "linked_bill_id": None,
                                            "pur_property_id": json.dumps(
                                                [getRentInfo['result'][0]['rental_property_id']]),
                                            "payer": json.dumps(tenants),
                                            "receiver": getRentInfo['result'][0]['linked_business_id'],
                                            "purchase_type": 'RENT' if payment['fee_name'] == 'Rent' else 'EXTRA CHARGES',
                                            "description": payment['fee_name'],
                                            "amount_due": payment['charge'],
                                            "amount_paid": 0,
                                            "purchase_notes": due_date.strftime(
                                                '%B'),
                                            "purchase_date": effective_date.isoformat(),
                                            "purchase_frequency": payment['frequency'],
                                            "next_payment": due_date,
                                            "purchase_status": 'UNPAID'
                                        }
                                        newEntries.append(
                                            newPurchase)
                                        if(payment['fee_name'] == 'Rent'):
                                            rent = int(payment['charge'])

                                            for mpayment in managementPayments:

                                                weeks_current_month = len(
                                                    calendar.monthcalendar(due_date.year, int(due_date.strftime("%m"))))
                                                if mpayment['frequency'] == 'Weekly' and mpayment['fee_type'] == '%':
                                                    if mpayment['of'] == 'Gross Rent':
                                                        newPurchase = {
                                                            "linked_bill_id": None,
                                                            "pur_property_id": json.dumps(
                                                                [getRentInfo['result'][0]['property_uid']]),
                                                            "payer": json.dumps(
                                                                [getRentInfo['result'][0]['business_uid']]),
                                                            "receiver": getRentInfo['result'][0]['owner_id'],
                                                            "purchase_type": 'OWNER PAYMENT RENT',
                                                            "description": 'Rent',
                                                            "amount_due": weeks_current_month * (rent *
                                                                                                 (1-int(mpayment['charge'])/100)),
                                                            "amount_paid": 0,
                                                            "purchase_notes": due_date.strftime(
                                                                '%B'),
                                                            "purchase_date": effective_date.isoformat(),
                                                            "purchase_frequency": mpayment['frequency'],
                                                            "next_payment": due_date,
                                                            "purchase_status": 'UNPAID'
                                                        }
                                                        newEntries.append(
                                                            newPurchase)

                                                    # if net rent (listed rent-expenses)
                                                    else:
                                                        newPurchase = {
                                                            "linked_bill_id": None,
                                                            "pur_property_id": json.dumps(
                                                                [getRentInfo['result'][0]['property_uid']]),
                                                            "payer": json.dumps(
                                                                [getRentInfo['result'][0]['business_uid']]),
                                                            "receiver": getRentInfo['result'][0]['owner_id'],
                                                            "purchase_type": 'OWNER PAYMENT RENT',
                                                            "description": 'Rent',
                                                            "amount_due": weeks_current_month * ((rent-mpayment['expense_amount'])*(
                                                                1-int(mpayment['charge'])/100)),
                                                            "amount_paid": 0,
                                                            "purchase_notes": due_date.strftime(
                                                                '%B'),
                                                            "purchase_date": effective_date.isoformat(),
                                                            "purchase_frequency": mpayment['frequency'],
                                                            "next_payment": due_date,
                                                            "purchase_status": 'UNPAID'
                                                        }
                                                        newEntries.append(
                                                            newPurchase)
                                                elif mpayment['frequency'] == 'Biweekly' and mpayment['fee_type'] == '%':

                                                    if mpayment['of'] == 'Gross Rent':
                                                        newPurchase = {
                                                            "linked_bill_id": None,
                                                            "pur_property_id": json.dumps(
                                                                [getRentInfo['result'][0]['property_uid']]),
                                                            "payer": json.dumps(
                                                                [getRentInfo['result'][0]['business_uid']]),
                                                            "receiver": getRentInfo['result'][0]['owner_id'],
                                                            "purchase_type": 'OWNER PAYMENT RENT',
                                                            "description": 'Rent',
                                                            "amount_due": weeks_current_month/2 * (rent *
                                                                                                   (1-int(mpayment['charge'])/100)),
                                                            "amount_paid": 0,
                                                            "purchase_notes": due_date.strftime(
                                                                '%B'),
                                                            "purchase_date": effective_date.isoformat(),
                                                            "purchase_frequency": mpayment['frequency'],
                                                            "next_payment": due_date,
                                                            "purchase_status": 'UNPAID'
                                                        }
                                                        newEntries.append(
                                                            newPurchase)

                                                    # if net rent (listed rent-expenses)
                                                    else:
                                                        newPurchase = {
                                                            "linked_bill_id": None,
                                                            "pur_property_id": json.dumps(
                                                                [getRentInfo['result'][0]['property_uid']]),
                                                            "payer": json.dumps(
                                                                [getRentInfo['result'][0]['business_uid']]),
                                                            "receiver": getRentInfo['result'][0]['owner_id'],
                                                            "purchase_type": 'OWNER PAYMENT RENT',
                                                            "description": 'Rent',
                                                            "amount_due": weeks_current_month/2 * ((rent-mpayment['expense_amount'])*(
                                                                1-int(mpayment['charge'])/100)),
                                                            "amount_paid": 0,
                                                            "purchase_notes": due_date.strftime(
                                                                '%B'),
                                                            "purchase_date": effective_date.isoformat(),
                                                            "purchase_frequency": mpayment['frequency'],
                                                            "next_payment": due_date,
                                                            "purchase_status": 'UNPAID'
                                                        }
                                                        newEntries.append(
                                                            newPurchase)
                                                elif mpayment['frequency'] == 'Monthly' and mpayment['fee_type'] == '%':

                                                    # if gross rent (listed rent)
                                                    if mpayment['of'] == 'Gross Rent':
                                                        newPurchase = {
                                                            "linked_bill_id": None,
                                                            "pur_property_id": json.dumps(
                                                                [getRentInfo['result'][0]['property_uid']]),
                                                            "payer": json.dumps(
                                                                [getRentInfo['result'][0]['business_uid']]),
                                                            "receiver": getRentInfo['result'][0]['owner_id'],
                                                            "purchase_type": 'OWNER PAYMENT RENT',
                                                            "description": 'Rent',
                                                            "amount_due": (rent *
                                                                           (1-int(mpayment['charge'])/100)),
                                                            "amount_paid": 0,
                                                            "purchase_notes": due_date.strftime(
                                                                '%B'),
                                                            "purchase_date": effective_date.isoformat(),
                                                            "purchase_frequency": mpayment['frequency'],
                                                            "next_payment": due_date,
                                                            "purchase_status": 'UNPAID'
                                                        }
                                                        newEntries.append(
                                                            newPurchase)

                                                    # if net rent (listed rent-expenses)
                                                    else:
                                                        newPurchase = {
                                                            "linked_bill_id": None,
                                                            "pur_property_id": json.dumps(
                                                                [getRentInfo['result'][0]['property_uid']]),
                                                            "payer": json.dumps(
                                                                [getRentInfo['result'][0]['business_uid']]),
                                                            "receiver": getRentInfo['result'][0]['owner_id'],
                                                            "purchase_type": 'OWNER PAYMENT RENT',
                                                            "description": 'Rent',
                                                            "amount_due": ((rent-mpayment['expense_amount'])*(
                                                                1-int(mpayment['charge'])/100)),
                                                            "amount_paid": 0,
                                                            "purchase_notes": due_date.strftime(
                                                                '%B'),
                                                            "purchase_date": effective_date.isoformat(),
                                                            "purchase_frequency": mpayment['frequency'],
                                                            "next_payment": due_date,
                                                            "purchase_status": 'UNPAID'
                                                        }
                                                        newEntries.append(
                                                            newPurchase)

                                                else:
                                                    print(
                                                        'payment frequency one-time %')

                                    due_date += relativedelta(months=1)
                            elif payment['frequency'] == 'Annually':

                                print('annually')

                                newPurchase = {
                                    "linked_bill_id": None,
                                    "pur_property_id": json.dumps(
                                        [getRentInfo['result'][0]['rental_property_id']]),
                                    "payer": json.dumps(tenants),
                                    "receiver": getRentInfo['result'][0]['linked_business_id'],
                                    "purchase_type": 'RENT' if payment['fee_name'] == 'Rent' else 'EXTRA CHARGES',
                                    "description": payment['fee_name'],
                                    "amount_due": payment['charge'],
                                    "amount_paid": 0,
                                    "purchase_notes": due_date.strftime(
                                        '%B'),
                                    "purchase_date": effective_date.isoformat(),
                                    "purchase_frequency": payment['frequency'],
                                    "next_payment": due_date,
                                    "purchase_status": 'UNPAID'
                                }
                                newEntries.append(
                                    newPurchase)

                            elif payment['frequency'] == 'Move-Out Charge':
                                print('move-out')
                                print('no need to add')
                            elif payment['frequency'] == 'Move-In Charge':
                                print('move in')
                                due_date = start_date
                                if len(payment['available_topay']) == 0:
                                    charge_date = due_date
                                else:
                                    charge_date = due_date - \
                                        timedelta(
                                            days=int(payment['available_topay']))

                                newPurchase = {
                                    "linked_bill_id": None,
                                    "pur_property_id": json.dumps(
                                        [getRentInfo['result'][0]['rental_property_id']]),
                                    "payer": json.dumps(tenants),
                                    "receiver": getRentInfo['result'][0]['linked_business_id'],
                                    "purchase_type": 'RENT' if payment['fee_name'] == 'Rent' else 'EXTRA CHARGES',
                                    "description": payment['fee_name'],
                                    "amount_due": payment['charge'],
                                    "amount_paid": 0,
                                    "purchase_notes": due_date.strftime(
                                        '%B'),
                                    "purchase_date": effective_date.isoformat(),
                                    "purchase_frequency": payment['frequency'],
                                    "next_payment": due_date,
                                    "purchase_status": 'UNPAID'
                                }
                                newEntries.append(
                                    newPurchase)

                            else:
                                print('one-time', due_date)
                                # if(available_date > effective_date or (available_date < effective_date and due_date >= effective_date)):
                                if(due_date >= effective_date):
                                    newPurchase = {
                                        "linked_bill_id": None,
                                        "pur_property_id": json.dumps(
                                            [getRentInfo['result'][0]['rental_property_id']]),
                                        "payer": json.dumps(tenants),
                                        "receiver": getRentInfo['result'][0]['linked_business_id'],
                                        "purchase_type": 'RENT' if payment['fee_name'] == 'Rent' else 'EXTRA CHARGES',
                                        "description": payment['fee_name'],
                                        "amount_due": payment['charge'],
                                        "amount_paid": 0,
                                        "purchase_notes": due_date.strftime(
                                            '%B'),
                                        "purchase_date": effective_date.isoformat(),
                                        "purchase_frequency": payment['frequency'],
                                        "next_payment": due_date,
                                        "purchase_status": 'UNPAID'
                                    }
                                    newEntries.append(
                                        newPurchase)
                            print('newEntries',
                                  payment['fee_name'], len(newEntries), newEntries)
                            # delete older unpaid purchase records
                            delPurchases = db.delete("""
                                DELETE FROM pm.purchases
                                WHERE pur_property_id LIKE '%""" + getRentInfo['result'][0]['rental_property_id'] + """%'
                                AND DATE(purchase_date) >= DATE(\'""" + getRentInfo['result'][0]['effective_date'] + """\')
                                AND purchase_status ="UNPAID"
                                AND description = \'""" + payment['fee_name'] + """\'  """)
                            # delete older unpaid owner payment purchase records
                            delOwnerPurchases = db.delete("""
                                DELETE FROM pm.purchases
                                WHERE pur_property_id LIKE '%""" + getRentInfo['result'][0]['rental_property_id'] + """%'
                                AND DATE(purchase_date) >= DATE(\'""" + getRentInfo['result'][0]['effective_date'] + """\')
                                AND purchase_status ="UNPAID"
                                AND purchase_type = 'OWNER PAYMENT RENT' AND description = 'Rent'  """)
                            # find paid purchases after the effective date
                            paidPurchases = db.execute("""
                                SELECT * FROM pm.purchases
                                WHERE pur_property_id LIKE '%""" + getRentInfo['result'][0]['rental_property_id'] + """%'
                                -- AND DATE(purchase_date) > DATE(\'""" + getRentInfo['result'][0]['effective_date'] + """\')
                                AND purchase_status ="PAID"
                                AND description = \'""" + payment['fee_name'] + """\'  """)
                            # if paid purchases, store in paidEntries
                            if len(paidPurchases['result']) > 0:
                                paidEntries = list(paidPurchases['result'])
                            print('paidEntries',
                                  payment['fee_name'], len(paidEntries),  paidEntries)
                            # if paid purchases, filter through new purchases with same property_id, payer,description and month
                            if len(paidPurchases['result']) > 0:
                                for paid in paidEntries:
                                    for new in newEntries:
                                        # if same purchase found, remove from newEntries list
                                        if(paid['pur_property_id'] == new['pur_property_id'] and paid['payer'] == new['payer'] and paid['description'] == new['description'] and paid['purchase_notes'] == new['purchase_notes']):
                                            newEntries.remove(new)
                                        elif(paid['pur_property_id'] == new['pur_property_id'] and paid['payer'] == new['payer'] and paid['description'] == new['description'] and paid['purchase_frequency'] == 'One-time' and new['purchase_frequency'] == 'One-time'):
                                            newEntries.remove(new)
                                        else:
                                            print('do nothing')

                            # set the updated newEntries list as filteredList and enter the info into the database
                            filteredEntries = newEntries
                            for filtered in filteredEntries:
                                newPurchaseID = db.call('new_purchase_id')[
                                    'result'][0]['new_id']
                                filtered['purchase_uid'] = newPurchaseID
                                response = db.insert('purchases', filtered)

                            print('filteredEntries',
                                  payment['fee_name'], len(filteredEntries), filteredEntries)

            response = db.update("rentals", rental_pk, updatedRental)

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
            appRes = db.execute(
                """SELECT * FROM pm.applications WHERE application_status='RENTED' AND property_uid = \'"""
                + rentalUpdate['rental_property_id']
                + """\' """)
            if len(appRes['result']) > 0:
                for application in appRes['result']:
                    print(application)
                    updateApp = {
                        'application_status': 'ENDED',
                    }
                    pk = {
                        'application_uid': application['application_uid']}
                    appResponse = db.update('applications', pk, updateApp)
            pur_pk = {
                'pur_property_id': json.dumps([rentalUpdate['rental_property_id']])
            }
            pur_response = db.delete("""DELETE FROM pm.purchases WHERE pur_property_id LIKE '%""" + rentalUpdate['rental_property_id'] + """%'
                                            AND (MONTH(purchase_date) > MONTH(now()) AND YEAR(purchase_date) = YEAR(now()) OR YEAR(purchase_date) > YEAR(now()))
                                            AND purchase_status ="UNPAID"
                                            AND (purchase_type= "RENT" OR purchase_type= "EXTRA CHARGES")""")
            # pur_response = db.delete('purchases', pur_pk,  )
            print(pur_response)

        return response


class ExtendLease(Resource):
    def post(self):
        response = {}
        with connect() as db:
            data = request.form
            fields = ['rental_property_id', 'linked_application_id', 'actual_rent', 'lease_start', 'lease_end',
                      'rent_payments', 'assigned_contacts', 'rental_status', 'available_topay', 'due_by', 'late_by', 'late_fee', 'perDay_late_fee', 'pets', 'vehicles', 'referred', 'adults', 'children', 'effective_date']
            newRental = {}
            for field in fields:
                newRental[field] = data.get(field)

            newRentalID = db.call('new_rental_id')['result'][0]['new_id']
            newRental['rental_uid'] = newRentalID

            documents = json.loads(data.get('documents'))
            for i in range(len(documents)):
                filename = f'doc_{i}'
                file = request.files.get(filename)
                if file:
                    key = f'rentals/{newRentalID}/{filename}'
                    doc = uploadImage(file, key, '')
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

            # response = db.execute("""SELECT * FROM pm.applications WHERE application_status='LEASE EXTENSION' AND property_uid = \'"""
            #                       + newRental['rental_property_id']
            #                       + """\' """)
            # newApplication = {'application_status': 'RENTED'}
            # for response in response['result']:
            #     pk = {
            #         'application_uid': response['application_uid']
            #     }
            #     response = db.update(
            #         'applications', pk, newApplication)

            # primaryKeyA = {
            #     'application_uid': data.get('application_uid')
            # }
            # # print('newAppl', newApplication)
            # response = db.update(
            #     'applications', primaryKeyA, newApplication)
        return response

    def put(self):
        response = {}
        with connect() as db:
            data = request.json
            fields = ['rental_uid', 'linked_application_id', 'rental_property_id', 'tenant_id', 'actual_rent', 'lease_start', 'lease_end',
                      'rent_payments', 'assigned_contacts', 'rental_status', 'available_topay', 'due_by', 'late_by', 'late_fee', 'perDay_late_fee', 'application_uid', 'property_uid',
                      'message', 'application_status']
            newRental = {}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    newRental[field] = fieldValue
                    # print('fieldvalue', fieldValue)
                # print(field, fieldValue)
                # print(newRental)
                if field == 'application_status' and fieldValue != None:
                    print('if field application status')
                    # set application_status to LEASE EXTENSION
                    if newRental['application_status'] == 'LEASE EXTENSION':
                        # print('tenant requesting to extend Lease')
                        # print(newRental)
                        response = db.execute(
                            """SELECT * FROM pm.applications 
                            WHERE (application_status='RENTED' OR application_status='TENANT LEASE EXTENSION') 
                            AND property_uid = \'""" + newRental['property_uid'] + """\' """)
                        print('response', response, len(response['result']))
                        if len(response['result']) > 1:
                            newRental['application_status'] = 'LEASE EXTENSION REQUESTED'
                        else:
                            newRental['application_status'] = 'LEASE EXTENSION'
                            pk = {
                                'application_uid': response['result'][0]['application_uid']
                            }
                            response = db.update(
                                'applications', pk, newRental)
                            # response = db.execute(
                            #     """SELECT * FROM pm.applications WHERE application_status='LEASE EXTENSION REQUESTED' AND property_uid = \'"""
                            #     + newRental['property_uid']
                            #     + """\' """)
                            # # print('response', response['result'])

                            # if len(response['result']) > 0:
                            #     newRental['application_status'] = 'LEASE EXTENSION'
                            #     for response in response['result']:
                            #         pk = {
                            #             'application_uid': response['application_uid']
                            #         }
                            #         response = db.update(
                            #             'applications', pk, newRental)
                    elif newRental['application_status'] == 'TENANT LEASE EXTENSION':
                        # print('tenant requesting to extend Lease')
                        # print(newRental)
                        response = db.execute(
                            """SELECT * FROM pm.applications WHERE application_status='RENTED' AND property_uid = \'"""
                            + newRental['property_uid']
                            + """\' """)
                        print('response', response, len(response['result']))
                        if len(response['result']) > 1:
                            newRental['application_status'] = 'TENANT LEASE EXTENSION REQUESTED'
                        else:
                            newRental['application_status'] = 'TENANT LEASE EXTENSION'
                            pk = {
                                'application_uid': response['result'][0]['application_uid']
                            }
                            response = db.update(
                                'applications', pk, newRental)
                            # response = db.execute(
                            #     """SELECT * FROM pm.applications WHERE application_status='LEASE EXTENSION REQUESTED' AND property_uid = \'"""
                            #     + newRental['property_uid']
                            #     + """\' """)
                            # # print('response', response['result'])

                            # if len(response['result']) > 0:
                            #     newRental['application_status'] = 'LEASE EXTENSION'
                            #     for response in response['result']:
                            #         pk = {
                            #             'application_uid': response['application_uid']
                            #         }
                            #         response = db.update(
                            #             'applications', pk, newRental)
                    # set application_status back to RENTED
                    elif newRental['application_status'] == 'REFUSED':
                        # print('pm rejected to extend lease')
                        response = db.execute(
                            """SELECT * FROM pm.applications WHERE (application_status='LEASE EXTENSION REQUESTED' OR application_status='LEASE EXTENSION')  AND property_uid = \'"""
                            + newRental['property_uid']
                            + """\' """)
                        newRental['application_status'] = 'RENTED'
                        for response in response['result']:
                            pk = {
                                'application_uid': response['application_uid']
                            }
                            response = db.update(
                                'applications', pk, newRental)

                    else:
                        primaryKeyA = {
                            'application_uid': data.get('application_uid')
                        }
                        updateApp = {
                            'application_status': newRental['application_status'],
                            'message': newRental['message']
                        }
                        # print('newAppl', newApplication)
                        response = db.update(
                            'applications', primaryKeyA, updateApp)
            # print(hasattr(newRental, 'rental_uid'))
            # print('rental_uid' in newRental)
            if 'rental_uid' in newRental:
                # print('here', newRental)
                primaryKey = {'rental_uid': newRental['rental_uid']}
                newRental = {
                    'rental_status': 'TENANT APPROVED'}
                # print('newRental', newRental)

                response = db.update('rentals', primaryKey, newRental)

        return response


class ExtendLeaseCRON_CLASS(Resource):
    def get(self):
        with connect() as db:
            response = {'message': 'Successfully committed SQL query',
                        'code': 200}
            leaseResponse = db.execute("""
            SELECT r.*, GROUP_CONCAT(lt.linked_tenant_id) as `tenants`
            FROM pm.rentals r
            LEFT JOIN leaseTenants lt
            ON lt.linked_rental_uid = r.rental_uid
            WHERE r.rental_property_id IN (SELECT *
            FROM (SELECT r.rental_property_id
                FROM pm.rentals
                GROUP BY r.rental_property_id
                HAVING COUNT(r.rental_property_id) > 1)
            AS a)
            AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED')
            GROUP BY lt.linked_rental_uid; """)
            today_datetime = datetime.now()
            today = datetime.strftime(today_datetime, '%Y-%m-%d')
            oldLease = ''
            newLease = ''
            if len(leaseResponse['result']) > 0:
                for res in leaseResponse['result']:
                    if res['rental_status'] == 'ACTIVE':
                        oldLease = res
                    else:
                        newLease = res
            print('oldLease', oldLease)
            print('newLease', newLease)
            if newLease['lease_start'] == today:
                print('here')
                if datetime.strptime(oldLease['lease_end'], '%Y-%m-%d') > datetime.strptime(today, '%Y-%m-%d'):
                    pur_response = db.delete("""
                    DELETE FROM pm.purchases WHERE pur_property_id LIKE '%""" + oldLease['rental_property_id'] + """%'
                    AND (MONTH(purchase_date) > MONTH(now()) AND YEAR(purchase_date) = YEAR(now()) OR YEAR(purchase_date) > YEAR(now()))
                    AND purchase_status ="UNPAID"
                    AND (purchase_type= "RENT" OR purchase_type= "EXTRA CHARGES")""")
                pk = {
                    'rental_uid': oldLease['rental_uid']
                }
                oldLeaseUpdate = {
                    'rental_status': 'EXPIRED'
                }
                oldLeaseUpdateRes = db.update(
                    'rentals', pk, oldLeaseUpdate)

                # adding leaseTenants
                tenants = newLease['tenants']
                print('tenants1', tenants)
                if '[' in tenants:
                    print('tenants2', tenants)
                    tenants = json.loads(tenants)
                    print('tenants3', tenants)
                print('tenants4', tenants)
                if type(tenants) == str:
                    tenants = [tenants]
                    print('tenants5', tenants)
                print(tenants)
                # creating purchases
                rentPayments = json.loads(newLease['rent_payments'])
                res = db.execute("""
                SELECT r.*, p.*, GROUP_CONCAT(lt.linked_tenant_id) as `tenants`
                FROM pm.rentals r
                LEFT JOIN pm.leaseTenants lt
                ON lt.linked_rental_uid = r.rental_uid
                LEFT JOIN pm.propertyManager p
                ON p.linked_property_id= r.rental_property_id
                WHERE r.rental_status='TENANT APPROVED'
                AND (p.management_status = 'ACCEPTED' OR p.management_status='END EARLY' OR p.management_status='PM END EARLY' OR p.management_status='OWNER END EARLY')   
                AND r.rental_property_id = \'""" + newLease['rental_property_id'] + """\'
                GROUP BY lt.linked_rental_uid; """)
                for payment in rentPayments:
                    if payment['frequency'] == 'Monthly':

                        charge_date = date.fromisoformat(
                            newLease['lease_start'])
                        due_date = charge_date.replace(
                            day=int(newLease['due_by']))
                        lease_end = date.fromisoformat(
                            newLease['lease_end'])
                        # print('charge_date', type(charge_date),
                        #       charge_date.isoformat())
                        while charge_date < lease_end:
                            charge_month = charge_date.strftime(
                                '%B')
                            if(payment['fee_name'] == 'Rent'):
                                purchaseResponse = newPurchase(
                                    linked_bill_id=None,
                                    pur_property_id=json.dumps(
                                        [newLease['rental_property_id']]),
                                    payer=json.dumps(tenants),
                                    receiver=res['result'][0]['linked_business_id'],
                                    purchase_type='RENT',
                                    description=payment['fee_name'],
                                    amount_due=payment['charge'],
                                    purchase_notes=charge_month,
                                    purchase_date=charge_date.isoformat(),
                                    purchase_frequency=payment['frequency'],
                                    next_payment=due_date
                                )
                            else:
                                purchaseResponse = newPurchase(
                                    linked_bill_id=None,
                                    pur_property_id=json.dumps(
                                        [newLease['rental_property_id']]),
                                    payer=json.dumps(tenants),
                                    receiver=res['result'][0]['linked_business_id'],
                                    purchase_type='EXTRA CHARGES',
                                    description=payment['fee_name'],
                                    amount_due=payment['charge'],
                                    purchase_notes=charge_month,
                                    purchase_date=charge_date.isoformat(),
                                    purchase_frequency=payment['frequency'],
                                    next_payment=due_date
                                )
                            charge_date += relativedelta(months=1)
                            due_date += relativedelta(months=1)
                    else:
                        # print('lease_start', type(
                        #     res['result'][0]['lease_start']))

                        charge_date = date.fromisoformat(
                            newLease['lease_start'])
                        due_date = date.fromisoformat(
                            newLease['lease_start']).replace(
                            day=int(newLease['due_by']))
                        lease_end = date.fromisoformat(
                            newLease['lease_end'])
                        # print('charge_date', type(charge_date),
                        #       charge_date.isoformat())

                        charge_month = charge_date.strftime(
                            '%B')
                        if(payment['fee_name'] == 'Rent'):
                            purchaseResponse = newPurchase(
                                linked_bill_id=None,
                                pur_property_id=json.dumps(
                                    [newLease['rental_property_id']]),
                                payer=json.dumps(tenants),
                                receiver=res['result'][0]['linked_business_id'],
                                purchase_type='RENT',
                                description=payment['fee_name'],
                                amount_due=payment['charge'],
                                purchase_notes=charge_month,
                                purchase_date=newLease['lease_start'],
                                purchase_frequency=payment['frequency'],
                                next_payment=due_date
                            )

                        else:

                            purchaseResponse = newPurchase(
                                linked_bill_id=None,
                                pur_property_id=json.dumps(
                                    [newLease['rental_property_id']]),
                                payer=json.dumps(tenants),
                                receiver=res['result'][0]['linked_business_id'],
                                purchase_type='EXTRA CHARGES',
                                description=payment['fee_name'],
                                amount_due=payment['charge'],
                                purchase_notes=charge_month,
                                purchase_date=newLease['lease_start'],
                                purchase_frequency=payment['frequency'],
                                next_payment=due_date
                            )
                pkNL = {
                    'rental_uid': newLease['rental_uid']
                }
                newLeaseUpdate = {
                    'rental_status': 'ACTIVE'
                }
                response = db.update(
                    'rentals', pkNL, newLeaseUpdate)
        return response


def ExtendLeaseCRON():
    print("In ExtendLeaseCRON")
    from purchases import newPurchase
    from datetime import date, datetime

    with connect() as db:
        print("In Extend Lease CRON Function")
        response = {'message': 'Successfully committed SQL query',
                    'code': 200}
        leaseResponse = db.execute("""SELECT r.*, GROUP_CONCAT(lt.linked_tenant_id) as `tenants`
        FROM pm.rentals r
        LEFT JOIN leaseTenants lt
        ON lt.linked_rental_uid = r.rental_uid
        WHERE r.rental_property_id IN (SELECT *
        FROM (SELECT r.rental_property_id
            FROM pm.rentals
            GROUP BY r.rental_property_id
            HAVING COUNT(r.rental_property_id) > 1)
        AS a)
        AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED')
        GROUP BY lt.linked_rental_uid; """)
        today_datetime = datetime.now()
        today = datetime.strftime(today_datetime, '%Y-%m-%d')
        oldLease = ''
        newLease = ''
        if len(leaseResponse['result']) > 0:
            for res in leaseResponse['result']:
                if res['rental_status'] == 'ACTIVE':
                    oldLease = res
                else:
                    newLease = res
        print('oldLease', oldLease)
        print('newLease', newLease)
        if newLease['lease_start'] == today:
            print('here')
            if datetime.strptime(oldLease['lease_end'], '%Y-%m-%d') > datetime.strptime(today, '%Y-%m-%d'):
                pur_response = db.delete("""
                DELETE FROM pm.purchases WHERE pur_property_id LIKE '%""" + oldLease['rental_property_id'] + """%'
                AND (MONTH(purchase_date) > MONTH(now()) AND YEAR(purchase_date) = YEAR(now()) OR YEAR(purchase_date) > YEAR(now()))
                AND purchase_status ="UNPAID"
                AND (purchase_type= "RENT" OR purchase_type= "EXTRA CHARGES")""")
            pk = {
                'rental_uid': oldLease['rental_uid']
            }
            oldLeaseUpdate = {
                'rental_status': 'EXPIRED'
            }
            oldLeaseUpdateRes = db.update(
                'rentals', pk, oldLeaseUpdate)

            # adding leaseTenants
            tenants = newLease['tenants']
            print('tenants1', tenants)
            if '[' in tenants:
                print('tenants2', tenants)
                tenants = json.loads(tenants)
                print('tenants3', tenants)
            print('tenants4', tenants)
            if type(tenants) == str:
                tenants = [tenants]
                print('tenants5', tenants)
            print(tenants)
            # creating purchases
            rentPayments = json.loads(newLease['rent_payments'])
            res = db.execute("""SELECT r.*, p.*, GROUP_CONCAT(lt.linked_tenant_id) as `tenants`
            FROM pm.rentals r
            LEFT JOIN pm.leaseTenants lt
            ON lt.linked_rental_uid = r.rental_uid
            LEFT JOIN pm.propertyManager p
            ON p.linked_property_id= r.rental_property_id
            WHERE r.rental_status='TENANT APPROVED'
            AND (p.management_status = 'ACCEPTED' OR p.management_status='END EARLY' OR p.management_status='PM END EARLY' OR p.management_status='OWNER END EARLY')  
            AND r.rental_property_id = \'""" + newLease['rental_property_id'] + """\'
            GROUP BY lt.linked_rental_uid; """)
            for payment in rentPayments:
                if payment['frequency'] == 'Monthly':

                    charge_date = date.fromisoformat(
                        newLease['lease_start'])
                    due_date = charge_date.replace(
                        day=int(newLease['due_by']))
                    lease_end = date.fromisoformat(
                        newLease['lease_end'])
                    # print('charge_date', type(charge_date),
                    #       charge_date.isoformat())
                    while charge_date < lease_end:
                        charge_month = charge_date.strftime(
                            '%B')
                        if(payment['fee_name'] == 'Rent'):
                            purchaseResponse = newPurchase(
                                linked_bill_id=None,
                                pur_property_id=json.dumps(
                                    [newLease['rental_property_id']]),
                                payer=json.dumps(tenants),
                                receiver=res['result'][0]['linked_business_id'],
                                purchase_type='RENT',
                                description=payment['fee_name'],
                                amount_due=payment['charge'],
                                purchase_notes=charge_month,
                                purchase_date=charge_date.isoformat(),
                                purchase_frequency=payment['frequency'],
                                next_payment=due_date
                            )
                        else:
                            purchaseResponse = newPurchase(
                                linked_bill_id=None,
                                pur_property_id=json.dumps(
                                    [newLease['rental_property_id']]),
                                payer=json.dumps(tenants),
                                receiver=res['result'][0]['linked_business_id'],
                                purchase_type='EXTRA CHARGES',
                                description=payment['fee_name'],
                                amount_due=payment['charge'],
                                purchase_notes=charge_month,
                                purchase_date=charge_date.isoformat(),
                                purchase_frequency=payment['frequency'],
                                next_payment=due_date
                            )
                        charge_date += relativedelta(months=1)
                        due_date += relativedelta(months=1)
                else:
                    # print('lease_start', type(
                    #     res['result'][0]['lease_start']))

                    charge_date = date.fromisoformat(
                        newLease['lease_start'])
                    due_date = date.fromisoformat(
                        newLease['lease_start']).replace(
                        day=int(newLease['due_by']))
                    lease_end = date.fromisoformat(
                        newLease['lease_end'])
                    # print('charge_date', type(charge_date),
                    #       charge_date.isoformat())

                    charge_month = charge_date.strftime(
                        '%B')
                    if(payment['fee_name'] == 'Rent'):
                        purchaseResponse = newPurchase(
                            linked_bill_id=None,
                            pur_property_id=json.dumps(
                                [newLease['rental_property_id']]),
                            payer=json.dumps(tenants),
                            receiver=res['result'][0]['linked_business_id'],
                            purchase_type='RENT',
                            description=payment['fee_name'],
                            amount_due=payment['charge'],
                            purchase_notes=charge_month,
                            purchase_date=newLease['lease_start'],
                            purchase_frequency=payment['frequency'],
                            next_payment=due_date
                        )

                    else:

                        purchaseResponse = newPurchase(
                            linked_bill_id=None,
                            pur_property_id=json.dumps(
                                [newLease['rental_property_id']]),
                            payer=json.dumps(tenants),
                            receiver=res['result'][0]['linked_business_id'],
                            purchase_type='EXTRA CHARGES',
                            description=payment['fee_name'],
                            amount_due=payment['charge'],
                            purchase_notes=charge_month,
                            purchase_date=newLease['lease_start'],
                            purchase_frequency=payment['frequency'],
                            next_payment=due_date
                        )
            pkNL = {
                'rental_uid': newLease['rental_uid']
            }
            newLeaseUpdate = {
                'rental_status': 'ACTIVE'
            }
            response = db.update(
                'rentals', pkNL, newLeaseUpdate)
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
                                    AND (p.management_status = 'ACCEPTED' OR p.management_status='END EARLY' OR p.management_status='PM END EARLY' OR p.management_status='OWNER END EARLY')  ; """)

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
                                pur_property_id=json.dumps(
                                    [response['result'][i]['rental_property_id']]),
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
                                AND (p.management_status = 'ACCEPTED' OR p.management_status='END EARLY' OR p.management_status='PM END EARLY' OR p.management_status='OWNER END EARLY')  ; """)

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
                            pur_property_id=json.dumps(
                                [response['result'][i]['rental_property_id']]),
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
            response = db.execute("""
            SELECT r.*, lt.*, p.*, GROUP_CONCAT(lt.linked_tenant_id) as `tenants`, c.*,prop.* 
            FROM pm.rentals r 
            LEFT JOIN pm.properties prop
            ON prop.property_uid = r.rental_property_id
            LEFT JOIN pm.leaseTenants lt 
            ON lt.linked_rental_uid = r.rental_uid
            LEFT JOIN pm.propertyManager p 
            ON p.linked_property_id = r.rental_property_id
            LEFT JOIN pm.contracts c
            ON c.property_uid = p.linked_property_id
            WHERE r.lease_start < DATE_FORMAT(NOW(), "%Y-%m-%d")
            AND r.lease_end > DATE_FORMAT(NOW(), "%Y-%m-%d")
            AND r.rental_status='ACTIVE' 
            AND c.contract_status = 'ACTIVE'
            AND (p.management_status = 'ACCEPTED' OR p.management_status='END EARLY' OR p.management_status='PM END EARLY' OR p.management_status='OWNER END EARLY')
            GROUP BY lt.linked_rental_uid  ; """)
            if len(response['result']) > 0:
                for i in range(len(response['result'])):
                    response['result'][i]['expense_amount'] = 0
                    purRes = db.execute("""
                    SELECT * FROM purchases pur
                    WHERE pur.pur_property_id= \'""" + response['result'][i]['property_uid'] + """\'
                    AND (pur.purchase_type = 'UTILITY' OR pur.purchase_type = 'MAINTENANCE' OR pur.purchase_type = 'REPAIRS') """)
                    response['result'][i]['expenses'] = list(
                        purRes['result'])
                    if len(purRes['result']) > 0:
                        for ore in range(len(purRes['result'])):
                            response['result'][i]['expense_amount'] = response['result'][i]['expense_amount'] + int(
                                purRes['result'][ore]['amount_due'])
            if len(response['result']) > 0:
                for lease in response['result']:
                    # today date
                    today_date = date.today()
                    tenants = lease['tenants']
                    tenantPayments = json.loads(lease['rent_payments'])

                    managementPayments = json.loads(lease['contract_fees'])
                    # get unpaid rent for the current month from purchases
                    res = db.execute("""
                    SELECT *
                    FROM pm.purchases p
                    WHERE p.purchase_status='UNPAID' 
                    AND (p.purchase_type='RENT' OR p.purchase_type='EXTRA CHARGES')
                    AND p.purchase_notes= \'""" + today_date.strftime('%B') + """\' 
                    AND p.pur_property_id LIKE '%""" + lease['rental_property_id'] + """%'; """)
                    # getting all the expenses and calculating the expense amount

                    if len(res['result']) > 0:
                        for unpaid in res['result']:
                            for payment in tenantPayments:
                                # if fee name matches the current unpaid purchase, calculate the late date n fee
                                if payment['fee_name'] == unpaid['description']:
                                    # calculate rent due date
                                    due_date = today_date.replace(
                                        day=int(payment['due_by']))
                                    print('due_date', due_date)
                                    # calculate the date rent will be late
                                    late_date = due_date + \
                                        relativedelta(
                                            days=int(payment['late_by']))
                                    print('late date',
                                          payment['late_by'], late_date)
                                    # if late date == today's date enter late fee info in the payments
                                    if late_date == today_date:
                                        print(today_date, late_date)

                                        purchaseResponse = newPurchase(
                                            linked_bill_id=None,
                                            pur_property_id=json.dumps(
                                                [lease['rental_property_id']]),
                                            payer=json.dumps([tenants]),
                                            receiver=lease['linked_business_id'],
                                            purchase_type='LATE FEE',
                                            description=unpaid['description'],
                                            amount_due=lease['late_fee'],
                                            purchase_notes=today_date.strftime(
                                                '%B'),
                                            purchase_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                            purchase_frequency='One-time',
                                            next_payment=today_date.isoformat()
                                        )

                                        for payment in managementPayments:
                                            weeks_current_month = len(
                                                calendar.monthcalendar(today_date.year, int(today_date.strftime("%m"))))

                                            if payment['frequency'] == 'Weekly' and payment['fee_type'] == '%':
                                                if payment['of'] == 'Gross Rent':

                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [lease['property_uid']]),
                                                        payer=json.dumps(
                                                            [lease['business_uid']]),
                                                        receiver=lease['owner_id'],
                                                        purchase_type='OWNER PAYMENT LATE FEE',
                                                        description=unpaid['description'] +
                                                        ' Late fee',
                                                        amount_due=weeks_current_month*(lease['late_fee'] *
                                                                                        (1-payment['charge']/100)),
                                                        purchase_notes=today_date.strftime(
                                                            '%B'),
                                                        purchase_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                        purchase_frequency=payment['frequency'],
                                                        next_payment=due_date
                                                    )
                                                # if net rent (listed rent-expenses)
                                                else:

                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [lease['property_uid']]),
                                                        payer=json.dumps(
                                                            [lease['business_uid']]),
                                                        receiver=lease['owner_id'],
                                                        purchase_type='OWNER PAYMENT LATE FEE',
                                                        description=unpaid['description'] +
                                                        ' Late fee',
                                                        amount_due=weeks_current_month*((lease['late_fee']-payment['expense_amount'])*(
                                                            1-payment['charge']/100)),
                                                        purchase_notes=today_date.strftime(
                                                            '%B'),
                                                        purchase_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                        purchase_frequency=payment['frequency'],
                                                        next_payment=due_date
                                                    )
                                            elif payment['frequency'] == 'Biweekly' and payment['fee_type'] == '%':

                                                # if gross rent (listed rent)
                                                if payment['of'] == 'Gross Rent':

                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [lease['property_uid']]),
                                                        payer=json.dumps(
                                                            [lease['business_uid']]),
                                                        receiver=lease['owner_id'],
                                                        purchase_type='OWNER PAYMENT LATE FEE',
                                                        description=unpaid['description'] +
                                                        ' Late fee',
                                                        amount_due=weeks_current_month/2*((lease['late_fee'] *
                                                                                           (1-payment['charge']/100)))/weeks_current_month/2,
                                                        purchase_notes=today_date.strftime(
                                                            '%B'),
                                                        purchase_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                        purchase_frequency=payment['frequency'],
                                                        next_payment=due_date
                                                    )
                                                # if net rent (listed rent-expenses)
                                                else:

                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [lease['property_uid']]),
                                                        payer=json.dumps(
                                                            [lease['business_uid']]),
                                                        receiver=lease['owner_id'],
                                                        purchase_type='OWNER PAYMENT LATE FEE',
                                                        description=unpaid['description'] +
                                                        ' Late fee',
                                                        amount_due=weeks_current_month/2*((lease['late_fee']-payment['expense_amount'])*(
                                                            1-payment['charge']/100))/weeks_current_month/2,
                                                        purchase_notes=today_date.strftime(
                                                            '%B'),
                                                        purchase_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                        purchase_frequency=payment['frequency'],
                                                        next_payment=due_date
                                                    )
                                            elif payment['frequency'] == 'Monthly' and payment['fee_type'] == '%':

                                                # if gross rent (listed rent)
                                                if payment['of'] == 'Gross Rent':
                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [lease['property_uid']]),
                                                        payer=json.dumps(
                                                            [lease['business_uid']]),
                                                        receiver=lease['owner_id'],
                                                        purchase_type='OWNER PAYMENT LATE FEE',
                                                        description=unpaid['description'] +
                                                        ' Late fee',
                                                        amount_due=(
                                                            lease['late_fee']*(1-int(payment['charge'])/100)),
                                                        purchase_notes=today_date.strftime(
                                                            '%B'),
                                                        purchase_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                        purchase_frequency=payment['frequency'],
                                                        next_payment=due_date
                                                    )
                                                    print(
                                                        purchaseResponse)

                                                # if net rent (listed rent-expenses)
                                                else:
                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [lease['property_uid']]),
                                                        payer=json.dumps(
                                                            [lease['business_uid']]),
                                                        receiver=lease['owner_id'],
                                                        purchase_type='OWNER PAYMENT LATE FEE',
                                                        description=unpaid['description'] +
                                                        ' Late fee',
                                                        amount_due=(
                                                            (lease['late_fee']-payment['expense_amount'])*(1-int(payment['charge'])/100)),
                                                        purchase_notes=today_date.strftime(
                                                            '%B'),
                                                        purchase_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                        purchase_frequency=payment['frequency'],
                                                        next_payment=due_date
                                                    )
                                                    print(
                                                        purchaseResponse)

                                            else:
                                                print(
                                                    'payment frequency one-time %')

        return purchaseResponse


def LateFee():
    print("In Late Fee")
    from purchases import newPurchase
    from datetime import date, datetime
    from dateutil.relativedelta import relativedelta

    with connect() as db:
        purchaseResponse = {'message': 'Successfully committed SQL query',
                            'code': 200}
        response = db.execute("""
        SELECT r.*, lt.*, p.*, GROUP_CONCAT(lt.linked_tenant_id) as `tenants`, c.*,prop.*
        FROM pm.rentals r
        LEFT JOIN pm.properties prop
        ON prop.property_uid = r.rental_property_id
        LEFT JOIN pm.leaseTenants lt
        ON lt.linked_rental_uid = r.rental_uid
        LEFT JOIN pm.propertyManager p
        ON p.linked_property_id = r.rental_property_id
        LEFT JOIN pm.contracts c
        ON c.property_uid = p.linked_property_id
        WHERE r.lease_start < DATE_FORMAT(NOW(), "%Y-%m-%d")
        AND r.lease_end > DATE_FORMAT(NOW(), "%Y-%m-%d")
        AND r.rental_status='ACTIVE'
        AND c.contract_status = 'ACTIVE'
        AND (p.management_status = 'ACCEPTED' OR p.management_status='END EARLY' OR p.management_status='PM END EARLY' OR p.management_status='OWNER END EARLY')
        GROUP BY lt.linked_rental_uid  ; """)
        if len(response['result']) > 0:
            for i in range(len(response['result'])):
                response['result'][i]['expense_amount'] = 0
                purRes = db.execute("""
                SELECT * FROM purchases pur
                WHERE pur.pur_property_id= \'""" + response['result'][i]['property_uid'] + """\'
                AND (pur.purchase_type = 'UTILITY' OR pur.purchase_type = 'MAINTENANCE' OR pur.purchase_type = 'REPAIRS') """)
                response['result'][i]['expenses'] = list(
                    purRes['result'])
                if len(purRes['result']) > 0:
                    for ore in range(len(purRes['result'])):
                        response['result'][i]['expense_amount'] = response['result'][i]['expense_amount'] + int(
                            purRes['result'][ore]['amount_due'])
        if len(response['result']) > 0:
            for lease in response['result']:
                # today date
                today_date = date.today()
                tenants = lease['tenants']
                tenantPayments = json.loads(lease['rent_payments'])

                managementPayments = json.loads(lease['contract_fees'])
                # get unpaid rent for the current month from purchases
                res = db.execute("""
                SELECT *
                FROM pm.purchases p
                WHERE p.purchase_status='UNPAID'
                AND (p.purchase_type='RENT' OR p.purchase_type='EXTRA CHARGES')
                AND p.purchase_notes= \'""" + today_date.strftime('%B') + """\'
                AND p.pur_property_id LIKE '%""" + lease['rental_property_id'] + """%'; """)
                # getting all the expenses and calculating the expense amount

                if len(res['result']) > 0:
                    for unpaid in res['result']:
                        for payment in tenantPayments:
                            # if fee name matches the current unpaid purchase, calculate the late date n fee
                            if payment['fee_name'] == unpaid['description']:
                                # calculate rent due date
                                due_date = today_date.replace(
                                    day=int(payment['due_by']))
                                print('due_date', due_date)
                                # calculate the date rent will be late
                                late_date = due_date + \
                                    relativedelta(
                                        days=int(payment['late_by']))
                                print('late date',
                                      payment['late_by'], late_date)
                                # if late date == today's date enter late fee info in the payments
                                if late_date == today_date:
                                    print(today_date, late_date)

                                    purchaseResponse = newPurchase(
                                        linked_bill_id=None,
                                        pur_property_id=json.dumps(
                                            [lease['rental_property_id']]),
                                        payer=json.dumps([tenants]),
                                        receiver=lease['linked_business_id'],
                                        purchase_type='LATE FEE',
                                        description=unpaid['description'],
                                        amount_due=lease['late_fee'],
                                        purchase_notes=today_date.strftime(
                                            '%B'),
                                        purchase_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        purchase_frequency='One-time',
                                        next_payment=today_date.isoformat()
                                    )

                                    for payment in managementPayments:
                                        weeks_current_month = len(
                                            calendar.monthcalendar(today_date.year, int(today_date.strftime("%m"))))

                                        if payment['frequency'] == 'Weekly' and payment['fee_type'] == '%':
                                            if payment['of'] == 'Gross Rent':

                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [lease['property_uid']]),
                                                    payer=json.dumps(
                                                        [lease['business_uid']]),
                                                    receiver=lease['owner_id'],
                                                    purchase_type='OWNER PAYMENT LATE FEE',
                                                    description=unpaid['description'] +
                                                    ' Late fee',
                                                    amount_due=weeks_current_month*(lease['late_fee'] *
                                                                                    (1-payment['charge']/100)),
                                                    purchase_notes=today_date.strftime(
                                                        '%B'),
                                                    purchase_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                    purchase_frequency=payment['frequency'],
                                                    next_payment=due_date
                                                )
                                            # if net rent (listed rent-expenses)
                                            else:

                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [lease['property_uid']]),
                                                    payer=json.dumps(
                                                        [lease['business_uid']]),
                                                    receiver=lease['owner_id'],
                                                    purchase_type='OWNER PAYMENT LATE FEE',
                                                    description=unpaid['description'] +
                                                    ' Late fee',
                                                    amount_due=weeks_current_month*((lease['late_fee']-payment['expense_amount'])*(
                                                        1-payment['charge']/100)),
                                                    purchase_notes=today_date.strftime(
                                                        '%B'),
                                                    purchase_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                    purchase_frequency=payment['frequency'],
                                                    next_payment=due_date
                                                )
                                        elif payment['frequency'] == 'Biweekly' and payment['fee_type'] == '%':

                                            # if gross rent (listed rent)
                                            if payment['of'] == 'Gross Rent':

                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [lease['property_uid']]),
                                                    payer=json.dumps(
                                                        [lease['business_uid']]),
                                                    receiver=lease['owner_id'],
                                                    purchase_type='OWNER PAYMENT LATE FEE',
                                                    description=unpaid['description'] +
                                                    ' Late fee',
                                                    amount_due=weeks_current_month/2*((lease['late_fee'] *
                                                                                       (1-payment['charge']/100)))/weeks_current_month/2,
                                                    purchase_notes=today_date.strftime(
                                                        '%B'),
                                                    purchase_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                    purchase_frequency=payment['frequency'],
                                                    next_payment=due_date
                                                )
                                            # if net rent (listed rent-expenses)
                                            else:

                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [lease['property_uid']]),
                                                    payer=json.dumps(
                                                        [lease['business_uid']]),
                                                    receiver=lease['owner_id'],
                                                    purchase_type='OWNER PAYMENT LATE FEE',
                                                    description=unpaid['description'] +
                                                    ' Late fee',
                                                    amount_due=weeks_current_month/2*((lease['late_fee']-payment['expense_amount'])*(
                                                        1-payment['charge']/100))/weeks_current_month/2,
                                                    purchase_notes=today_date.strftime(
                                                        '%B'),
                                                    purchase_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                    purchase_frequency=payment['frequency'],
                                                    next_payment=due_date
                                                )
                                        elif payment['frequency'] == 'Monthly' and payment['fee_type'] == '%':

                                            # if gross rent (listed rent)
                                            if payment['of'] == 'Gross Rent':
                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [lease['property_uid']]),
                                                    payer=json.dumps(
                                                        [lease['business_uid']]),
                                                    receiver=lease['owner_id'],
                                                    purchase_type='OWNER PAYMENT LATE FEE',
                                                    description=unpaid['description'] +
                                                    ' Late fee',
                                                    amount_due=(
                                                        lease['late_fee']*(1-int(payment['charge'])/100)),
                                                    purchase_notes=today_date.strftime(
                                                        '%B'),
                                                    purchase_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                    purchase_frequency=payment['frequency'],
                                                    next_payment=due_date
                                                )
                                                print(
                                                    purchaseResponse)

                                            # if net rent (listed rent-expenses)
                                            else:
                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [lease['property_uid']]),
                                                    payer=json.dumps(
                                                        [lease['business_uid']]),
                                                    receiver=lease['owner_id'],
                                                    purchase_type='OWNER PAYMENT LATE FEE',
                                                    description=unpaid['description'] +
                                                    ' Late fee',
                                                    amount_due=(
                                                        (lease['late_fee']-payment['expense_amount'])*(1-int(payment['charge'])/100)),
                                                    purchase_notes=today_date.strftime(
                                                        '%B'),
                                                    purchase_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                    purchase_frequency=payment['frequency'],
                                                    next_payment=due_date
                                                )
                                                print(
                                                    purchaseResponse)

                                        else:
                                            print(
                                                'payment frequency one-time %')

        return purchaseResponse


class PerDay_LateFee_CLASS(Resource):
    def get(self):
        updateLF = {'message': 'Successfully committed SQL query',
                    'code': 200}
        with connect() as db:
            response = db.execute("""
            SELECT r.*, lt.*, p.*, GROUP_CONCAT(lt.linked_tenant_id) as `tenants`, c.*,prop.* 
            FROM pm.rentals r 
             LEFT JOIN pm.properties prop
            ON prop.property_uid = r.rental_property_id
            LEFT JOIN pm.leaseTenants lt 
            ON lt.linked_rental_uid = r.rental_uid
            LEFT JOIN pm.propertyManager p 
            ON p.linked_property_id = r.rental_property_id
            LEFT JOIN pm.contracts c
            ON c.property_uid = p.linked_property_id
            WHERE r.lease_start < DATE_FORMAT(NOW(), "%Y-%m-%d")
            AND r.lease_end > DATE_FORMAT(NOW(), "%Y-%m-%d")
            AND r.rental_status='ACTIVE' 
            AND c.contract_status = 'ACTIVE'
            AND (p.management_status = 'ACCEPTED' OR p.management_status='END EARLY' OR p.management_status='PM END EARLY' OR p.management_status='OWNER END EARLY')
            GROUP BY lt.linked_rental_uid  ; """)
            if len(response['result']) > 0:
                for i in range(len(response['result'])):
                    response['result'][i]['expense_amount'] = 0
                    purRes = db.execute("""
                    SELECT * FROM purchases pur
                    WHERE pur.pur_property_id= \'""" + response['result'][i]['property_uid'] + """\'
                    AND (pur.purchase_type = 'UTILITY' OR pur.purchase_type = 'MAINTENANCE' OR pur.purchase_type = 'REPAIRS') """)
                    response['result'][i]['expenses'] = list(
                        purRes['result'])
                    if len(purRes['result']) > 0:
                        for ore in range(len(purRes['result'])):
                            response['result'][i]['expense_amount'] = response['result'][i]['expense_amount'] + int(
                                purRes['result'][ore]['amount_due'])
            if len(response['result']) > 0:
                for lease in response['result']:
                    # today date
                    today_date = date.today()
                    # get tenant payments
                    tenantPayments = json.loads(lease['rent_payments'])
                    managementPayments = json.loads(lease['contract_fees'])
                    print(lease['rental_property_id'])
                    # get unpaid rent for the current month from purchases
                    res = db.execute("""
                    SELECT *
                    FROM pm.purchases p
                    WHERE p.purchase_status='UNPAID' 
                    AND (p.purchase_type='RENT' OR p.purchase_type= 'EXTRA CHARGES')
                    AND p.purchase_notes= \'""" + today_date.strftime('%B') + """\' 
                    AND p.pur_property_id LIKE '%""" + lease['rental_property_id'] + """%'; """)

                    if len(res['result']) > 0:
                        for unpaid in res['result']:
                            print(unpaid)
                            for payment in tenantPayments:
                                print(payment['fee_name'],
                                      unpaid['description'])
                                if payment['fee_name'] == unpaid['description']:
                                    if payment['perDay_late_fee'] == 0:
                                        print('Do nothing if 0')
                                    else:
                                        latePurResponse = db.execute("""
                                        SELECT *
                                        FROM pm.purchases p
                                        WHERE p.pur_property_id LIKE '%""" + lease['rental_property_id'] + """%'
                                        AND p.purchase_notes = \'""" + date.today().strftime('%B') + """\'
                                        AND p.purchase_type= 'LATE FEE'
                                        AND p.description = \'""" + unpaid['description'] + """\'
                                        AND p.purchase_status='UNPAID'; """)

                                        if len(latePurResponse['result']) > 0:
                                            for latePur in latePurResponse['result']:
                                                pk = {
                                                    "purchase_uid": latePur['purchase_uid']
                                                }
                                                print(pk)
                                                print(int(latePur['amount_due']), int(
                                                    payment['perDay_late_fee']))
                                                updateLateFee = {
                                                    "amount_due": int(latePur['amount_due']) + int(payment['perDay_late_fee']),
                                                    "purchase_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                                }
                                                print(updateLateFee)
                                                updateLF = db.update(
                                                    'purchases', pk, updateLateFee)
                                        else:
                                            print('do nothing')
                                        lateOwnerPurResponse = db.execute("""
                                        SELECT *
                                        FROM pm.purchases p
                                        WHERE p.pur_property_id LIKE '%""" + lease['rental_property_id'] + """%'
                                        AND p.purchase_notes = \'""" + date.today().strftime('%B') + """\'
                                        AND p.purchase_type= 'OWNER PAYMENT LATE FEE'
                                        AND p.description = \'""" + unpaid['description'] + ' Late fee' + """\' 
                                        AND p.purchase_status='UNPAID'; """)

                                        if len(lateOwnerPurResponse['result']) > 0:
                                            for latePur in lateOwnerPurResponse['result']:

                                                for mpayment in managementPayments:
                                                    weeks_current_month = len(
                                                        calendar.monthcalendar(today_date.year, int(today_date.strftime("%m"))))

                                                    if mpayment['frequency'] == 'Weekly' and mpayment['fee_type'] == '%':
                                                        if mpayment['of'] == 'Gross Rent':

                                                            pk = {
                                                                "purchase_uid": latePur['purchase_uid']
                                                            }
                                                            print(pk)
                                                            updateLateFee = {
                                                                "amount_due": weeks_current_month*(int(latePur['amount_due']) + int(payment['perDay_late_fee']) * (1-int(mpayment['charge'])/100)),
                                                                "purchase_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                                            }
                                                            print(
                                                                updateLateFee)
                                                            updateLF = db.update(
                                                                'purchases', pk, updateLateFee)
                                                        # if net rent (listed rent-expenses)
                                                        else:
                                                            pk = {
                                                                "purchase_uid": latePur['purchase_uid']
                                                            }
                                                            print(pk)
                                                            updateLateFee = {
                                                                "amount_due": weeks_current_month*((int(latePur['amount_due']) + int(payment['perDay_late_fee'])-payment['expense_amount']) * (1-int(mpayment['charge'])/100)),
                                                                "purchase_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                                            }
                                                            print(
                                                                updateLateFee)
                                                            updateLF = db.update(
                                                                'purchases', pk, updateLateFee)

                                                    elif mpayment['frequency'] == 'Biweekly' and mpayment['fee_type'] == '%':

                                                        # if gross rent (listed rent)
                                                        if mpayment['of'] == 'Gross Rent':
                                                            pk = {
                                                                "purchase_uid": latePur['purchase_uid']
                                                            }
                                                            print(pk)
                                                            updateLateFee = {
                                                                "amount_due": weeks_current_month/2*(int(latePur['amount_due']) + int(payment['perDay_late_fee']) * (1-int(mpayment['charge'])/100)),
                                                                "purchase_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                                            }
                                                            print(
                                                                updateLateFee)
                                                            updateLF = db.update(
                                                                'purchases', pk, updateLateFee)

                                                        # if net rent (listed rent-expenses)
                                                        else:
                                                            pk = {
                                                                "purchase_uid": latePur['purchase_uid']
                                                            }
                                                            print(pk)
                                                            updateLateFee = {
                                                                "amount_due":  weeks_current_month/2*((int(latePur['amount_due']) + int(payment['perDay_late_fee'])-payment['expense_amount']) * (1-int(mpayment['charge'])/100)),
                                                                "purchase_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                                            }
                                                            print(
                                                                updateLateFee)
                                                            updateLF = db.update(
                                                                'purchases', pk, updateLateFee)

                                                    elif mpayment['frequency'] == 'Monthly' and mpayment['fee_type'] == '%':

                                                        # if gross rent (listed rent)
                                                        if mpayment['of'] == 'Gross Rent':
                                                            pk = {
                                                                "purchase_uid": latePur['purchase_uid']
                                                            }
                                                            print(pk)
                                                            print(int(latePur['amount_due']), int(
                                                                payment['perDay_late_fee']))
                                                            updateLateFee = {
                                                                "amount_due": (int(latePur['amount_due']) + int(payment['perDay_late_fee']) * (1-int(mpayment['charge'])/100)),
                                                                "purchase_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                                            }
                                                            print(
                                                                updateLateFee)
                                                            updateLF = db.update(
                                                                'purchases', pk, updateLateFee)

                                                        # if net rent (listed rent-expenses)
                                                        else:
                                                            pk = {
                                                                "purchase_uid": latePur['purchase_uid']
                                                            }
                                                            print(pk)
                                                            updateLateFee = {
                                                                "amount_due":  ((int(latePur['amount_due']) + int(payment['perDay_late_fee'])-payment['expense_amount']) * (1-int(mpayment['charge'])/100)),
                                                                "purchase_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                                            }
                                                            print(
                                                                updateLateFee)
                                                            updateLF = db.update(
                                                                'purchases', pk, updateLateFee)

                                                    else:
                                                        print(
                                                            'payment frequency one-time %')

                                        else:
                                            print('do nothing')

        return updateLF


def PerDay_LateFee():
    print("In Per day Late Fee")
    from datetime import date, datetime
    from dateutil.relativedelta import relativedelta

    with connect() as db:
        response = db.execute("""
        SELECT r.*, lt.*, p.*, GROUP_CONCAT(lt.linked_tenant_id) as `tenants`, c.*,prop.*
        FROM pm.rentals r
            LEFT JOIN pm.properties prop
        ON prop.property_uid = r.rental_property_id
        LEFT JOIN pm.leaseTenants lt
        ON lt.linked_rental_uid = r.rental_uid
        LEFT JOIN pm.propertyManager p
        ON p.linked_property_id = r.rental_property_id
        LEFT JOIN pm.contracts c
        ON c.property_uid = p.linked_property_id
        WHERE r.lease_start < DATE_FORMAT(NOW(), "%Y-%m-%d")
        AND r.lease_end > DATE_FORMAT(NOW(), "%Y-%m-%d")
        AND r.rental_status='ACTIVE'
        AND c.contract_status = 'ACTIVE'
        AND (p.management_status = 'ACCEPTED' OR p.management_status='END EARLY' OR p.management_status='PM END EARLY' OR p.management_status='OWNER END EARLY')
        GROUP BY lt.linked_rental_uid  ; """)
        if len(response['result']) > 0:
            for i in range(len(response['result'])):
                response['result'][i]['expense_amount'] = 0
                purRes = db.execute("""
                SELECT * FROM purchases pur
                WHERE pur.pur_property_id= \'""" + response['result'][i]['property_uid'] + """\'
                AND (pur.purchase_type = 'UTILITY' OR pur.purchase_type = 'MAINTENANCE' OR pur.purchase_type = 'REPAIRS') """)
                response['result'][i]['expenses'] = list(
                    purRes['result'])
                if len(purRes['result']) > 0:
                    for ore in range(len(purRes['result'])):
                        response['result'][i]['expense_amount'] = response['result'][i]['expense_amount'] + int(
                            purRes['result'][ore]['amount_due'])
        if len(response['result']) > 0:
            for lease in response['result']:
                # today date
                today_date = date.today()
                # get tenant payments
                tenantPayments = json.loads(lease['rent_payments'])
                managementPayments = json.loads(lease['contract_fees'])
                print(lease['rental_property_id'])
                # get unpaid rent for the current month from purchases
                res = db.execute("""
                SELECT *
                FROM pm.purchases p
                WHERE p.purchase_status='UNPAID' 
                AND (p.purchase_type='RENT' OR p.purchase_type= 'EXTRA CHARGES')
                AND p.purchase_notes= \'""" + today_date.strftime('%B') + """\' 
                AND p.pur_property_id LIKE '%""" + lease['rental_property_id'] + """%'; """)

                if len(res['result']) > 0:
                    for unpaid in res['result']:
                        print(unpaid)
                        for payment in tenantPayments:
                            print(payment['fee_name'],
                                  unpaid['description'])
                            if payment['fee_name'] == unpaid['description']:
                                if payment['perDay_late_fee'] == 0:
                                    print('Do nothing if 0')
                                else:
                                    latePurResponse = db.execute("""
                                    SELECT *
                                    FROM pm.purchases p
                                    WHERE p.pur_property_id LIKE '%""" + lease['rental_property_id'] + """%'
                                    AND p.purchase_notes = \'""" + date.today().strftime('%B') + """\'
                                    AND p.purchase_type= 'LATE FEE'
                                    AND p.description = \'""" + unpaid['description'] + """\'
                                    AND p.purchase_status='UNPAID'; """)

                                    if len(latePurResponse['result']) > 0:
                                        for latePur in latePurResponse['result']:
                                            pk = {
                                                "purchase_uid": latePur['purchase_uid']
                                            }
                                            print(pk)
                                            print(int(latePur['amount_due']), int(
                                                payment['perDay_late_fee']))
                                            updateLateFee = {
                                                "amount_due": int(latePur['amount_due']) + int(payment['perDay_late_fee']),
                                                "purchase_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                            }
                                            print(updateLateFee)
                                            updateLF = db.update(
                                                'purchases', pk, updateLateFee)
                                    else:
                                        print('do nothing')
                                    lateOwnerPurResponse = db.execute("""
                                    SELECT *
                                    FROM pm.purchases p
                                    WHERE p.pur_property_id LIKE '%""" + lease['rental_property_id'] + """%'
                                    AND p.purchase_notes = \'""" + date.today().strftime('%B') + """\'
                                    AND p.purchase_type= 'OWNER PAYMENT LATE FEE'
                                    AND p.description = \'""" + unpaid['description'] + ' Late fee' + """\' 
                                    AND p.purchase_status='UNPAID'; """)

                                    if len(lateOwnerPurResponse['result']) > 0:
                                        for latePur in lateOwnerPurResponse['result']:

                                            for mpayment in managementPayments:
                                                weeks_current_month = len(
                                                    calendar.monthcalendar(today_date.year, int(today_date.strftime("%m"))))

                                                if mpayment['frequency'] == 'Weekly' and mpayment['fee_type'] == '%':
                                                    if mpayment['of'] == 'Gross Rent':

                                                        pk = {
                                                            "purchase_uid": latePur['purchase_uid']
                                                        }
                                                        print(pk)
                                                        updateLateFee = {
                                                            "amount_due": weeks_current_month*(int(latePur['amount_due']) + int(payment['perDay_late_fee']) * (1-int(mpayment['charge'])/100)),
                                                            "purchase_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                                        }
                                                        print(
                                                            updateLateFee)
                                                        updateLF = db.update(
                                                            'purchases', pk, updateLateFee)
                                                    # if net rent (listed rent-expenses)
                                                    else:
                                                        pk = {
                                                            "purchase_uid": latePur['purchase_uid']
                                                        }
                                                        print(pk)
                                                        updateLateFee = {
                                                            "amount_due": weeks_current_month*((int(latePur['amount_due']) + int(payment['perDay_late_fee'])-payment['expense_amount']) * (1-int(mpayment['charge'])/100)),
                                                            "purchase_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                                        }
                                                        print(
                                                            updateLateFee)
                                                        updateLF = db.update(
                                                            'purchases', pk, updateLateFee)

                                                elif mpayment['frequency'] == 'Biweekly' and mpayment['fee_type'] == '%':

                                                    # if gross rent (listed rent)
                                                    if mpayment['of'] == 'Gross Rent':
                                                        pk = {
                                                            "purchase_uid": latePur['purchase_uid']
                                                        }
                                                        print(pk)
                                                        updateLateFee = {
                                                            "amount_due": weeks_current_month/2*(int(latePur['amount_due']) + int(payment['perDay_late_fee']) * (1-int(mpayment['charge'])/100)),
                                                            "purchase_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                                        }
                                                        print(
                                                            updateLateFee)
                                                        updateLF = db.update(
                                                            'purchases', pk, updateLateFee)

                                                    # if net rent (listed rent-expenses)
                                                    else:
                                                        pk = {
                                                            "purchase_uid": latePur['purchase_uid']
                                                        }
                                                        print(pk)
                                                        updateLateFee = {
                                                            "amount_due":  weeks_current_month/2*((int(latePur['amount_due']) + int(payment['perDay_late_fee'])-payment['expense_amount']) * (1-int(mpayment['charge'])/100)),
                                                            "purchase_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                                        }
                                                        print(
                                                            updateLateFee)
                                                        updateLF = db.update(
                                                            'purchases', pk, updateLateFee)

                                                elif mpayment['frequency'] == 'Monthly' and mpayment['fee_type'] == '%':

                                                    # if gross rent (listed rent)
                                                    if mpayment['of'] == 'Gross Rent':
                                                        pk = {
                                                            "purchase_uid": latePur['purchase_uid']
                                                        }
                                                        print(pk)
                                                        print(int(latePur['amount_due']), int(
                                                            payment['perDay_late_fee']))
                                                        updateLateFee = {
                                                            "amount_due": (int(latePur['amount_due']) + int(payment['perDay_late_fee']) * (1-int(mpayment['charge'])/100)),
                                                            "purchase_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                                        }
                                                        print(
                                                            updateLateFee)
                                                        updateLF = db.update(
                                                            'purchases', pk, updateLateFee)

                                                    # if net rent (listed rent-expenses)
                                                    else:
                                                        pk = {
                                                            "purchase_uid": latePur['purchase_uid']
                                                        }
                                                        print(pk)
                                                        updateLateFee = {
                                                            "amount_due":  ((int(latePur['amount_due']) + int(payment['perDay_late_fee'])-payment['expense_amount']) * (1-int(mpayment['charge'])/100)),
                                                            "purchase_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                                        }
                                                        print(
                                                            updateLateFee)
                                                        updateLF = db.update(
                                                            'purchases', pk, updateLateFee)

                                                else:
                                                    print(
                                                        'payment frequency one-time %')

                                    else:
                                        print('do nothing')
