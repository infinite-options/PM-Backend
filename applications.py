from flask import request, current_app
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
import boto3
from data import connect, uploadImage, s3
import json

from text_to_num import alpha2digit
from purchases import newPurchase
from datetime import date, timedelta, datetime
import calendar
from calendar import monthrange
from dateutil.relativedelta import relativedelta


def updateDocuments(documents, application_uid):
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
    bucket.objects.filter(Prefix=f'applications/{application_uid}/').delete()
    docs = []
    for i, doc in enumerate(documents):

        filename = f'doc_{i}'
        key = f'applications/{application_uid}/{filename}'
        # print(type(doc['file']))
        link = uploadImage(doc['file'], key, content[i])
        # print('link', link)
        doc['link'] = link
        del doc['file']
        docs.append(doc)
    return docs


def days_in_month(dt): return monthrange(
    dt.year, dt.month)[1]


def next_weekday(d, weekday):
    # d being the start date
    days_ahead = weekday - d.weekday()
    print(weekday, d, d.weekday())
    print(days_ahead)
    # if days_ahead <= d:

    if days_ahead < 0:  # Target day already happened this week
        days_ahead += 7

    print(days_ahead, d + timedelta(days_ahead))

    return d + timedelta(days_ahead)


def date_for_weekday(day: int, start_date):
    #  today = date.today()
    # weekday returns the offsets 0-6
    # If you need 1-7, use isoweekday
    weekday = start_date.weekday()
    return start_date + timedelta(days=day - weekday)


def next_weekday_biweekly(d, weekday):
    days_ahead = weekday - d.weekday()
    print(weekday, d, d.weekday())
    print(days_ahead)
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 14
    print(days_ahead, d + timedelta(days_ahead))
    return d + timedelta(days_ahead)


class Applications(Resource):
    decorators = [jwt_required(optional=True)]

    def get(self):
        response = {}
        filters = ['application_uid', 'property_uid', 'tenant_id']
        where = {}
        for filter in filters:
            filterValue = request.args.get(filter)
            if filterValue is not None:
                where[filter] = filterValue

        with connect() as db:

            if 'property_uid' in where:
                print('here', where['property_uid'], where)

                response = db.execute("""
                SELECT a.application_uid,application_date, a.message, a.application_status,a.adults,a.children, a.pets, a.vehicles, a.referred, a.documents, t.tenant_id,t.tenant_first_name,t.tenant_last_name,t.tenant_email,t.tenant_phone_number,t.tenant_ssn,t.tenant_current_salary,t.tenant_salary_frequency,t.tenant_current_job_title,t.tenant_current_job_company,t.tenant_drivers_license_number,t.tenant_drivers_license_state, p.*, r.*, b.*, pM.* FROM
                pm.applications a 
                LEFT JOIN pm.tenantProfileInfo t 
                ON a.tenant_id = t.tenant_id 
                LEFT JOIN pm.properties p 
                ON  p.property_uid = a.property_uid
                LEFT JOIN pm.rentals r 
                ON r.linked_application_id LIKE CONCAT('%', a.application_uid, '%') 
                LEFT JOIN pm.propertyManager pM 
                ON pM.linked_property_id = p.property_uid
                LEFT JOIN pm.businesses b 
                ON  pM.linked_business_id = b.business_uid
                WHERE pM.management_status = 'ACCEPTED' and a.property_uid=  \'""" + where['property_uid'] + """\'
                """)
                if len(response['result']) > 0:
                    print('here')
                    for application in response['result']:
                        print('application', application)
                        if application['rental_uid'] is not None:

                            print('rentals not none')
                            leaseTenants = db.execute("""
                            SELECT * FROM pm.leaseTenants lt
                            LEFT JOIN pm.applications a
                            ON lt.linked_tenant_id = a.tenant_id
                            LEFT JOIN  pm.tenantProfileInfo t 
                            ON lt.linked_tenant_id = t.tenant_id 
                            WHERE lt.linked_rental_uid = \'""" + application['rental_uid'] + """\'
                            AND a.property_uid =  \'""" + where['property_uid'] + """\'""")
                            print(leaseTenants['result'])
                            application['applicant_info'] = (
                                leaseTenants['result'])
                        else:
                            print('rental none')
                            leaseTenants = db.execute("""
                            SELECT * FROM pm.tenantProfileInfo t 
                            LEFT JOIN pm.applications a
                            ON t.tenant_id = a.tenant_id
                            WHERE t.tenant_id = \'""" + application['tenant_id'] + """\'
                            AND a.application_uid= \'""" + application['application_uid'] + """\'""")
                            print(leaseTenants['result'])
                            application['applicant_info'] = (
                                leaseTenants['result'])
            elif 'tenant_id' in where:
                response = db.execute("""
                SELECT application_uid, message,application_date, application_status,a.adults,a.children,  a.pets, a.vehicles, a.referred,a.documents, t.tenant_id,t.tenant_first_name,t.tenant_last_name,t.tenant_email,t.tenant_phone_number,t.tenant_ssn,t.tenant_current_salary,t.tenant_salary_frequency,t.tenant_current_job_title,t.tenant_current_job_company,t.tenant_drivers_license_number,t.tenant_drivers_license_state, p.*, r.*, b.*, pM.* FROM
                applications a 
                LEFT JOIN tenantProfileInfo t 
                ON a.tenant_id = t.tenant_id 
                LEFT JOIN properties p 
                ON a.property_uid = p.property_uid 
                LEFT JOIN rentals r 
                ON r.linked_application_id LIKE CONCAT('%', a.application_uid, '%')  
                LEFT JOIN pm.propertyManager pM ON pM.linked_property_id = p.property_uid
                LEFT JOIN pm.businesses b 
                ON b.business_uid = pM.linked_business_id
                WHERE pM.management_status = 'ACCEPTED' and a.tenant_id=  \'""" + where['tenant_id'] + """\'
                """)
                if len(response['result']) > 0:
                    print('here')
                    for application in response['result']:
                        if application['rental_uid'] is not None:
                            print('rentals not none',
                                  application['rental_uid'], application['application_uid'])

                            sql = """ SELECT * FROM pm.leaseTenants lt
                            LEFT JOIN pm.applications a
                            ON lt.linked_tenant_id = a.tenant_id
                            LEFT JOIN  pm.tenantProfileInfo t 
                            ON lt.linked_tenant_id = t.tenant_id 
                            WHERE lt.linked_rental_uid = \'""" + application['rental_uid'] + """\'
                            AND \'""" + application['linked_application_id'] + """\' LIKE CONCAT('%', application_uid, '%')  
                            AND a.property_uid = \'""" + application['rental_property_id'] + """\'"""
                            print(sql)

                            leaseTenants = db.execute("""
                            SELECT * FROM pm.leaseTenants lt
                            LEFT JOIN pm.applications a
                            ON lt.linked_tenant_id = a.tenant_id
                            LEFT JOIN  pm.tenantProfileInfo t 
                            ON lt.linked_tenant_id = t.tenant_id 
                            WHERE lt.linked_rental_uid = \'""" + application['rental_uid'] + """\'
                            AND \'""" + application['linked_application_id'] + """\' LIKE CONCAT('%', application_uid, '%') 
                            AND a.property_uid = \'""" + application['rental_property_id'] + """\'""")
                            print(len(leaseTenants['result']))
                            application['applicant_info'] = (
                                leaseTenants['result'])
                        else:
                            print(
                                'rental null', application['rental_uid'], application['application_uid'])
                            leaseTenants = db.execute("""
                            SELECT * FROM pm.tenantProfileInfo t 
                            LEFT JOIN pm.applications a
                            ON t.tenant_id = a.tenant_id
                            WHERE t.tenant_id = \'""" + application['tenant_id'] + """\'
                            AND application_uid =  \'""" + application['application_uid'] + """\'""")
                            print(len(leaseTenants['result']))
                            application['applicant_info'] = (
                                leaseTenants['result'])
            else:
                cols = 'application_uid, message, application_status,a.adults,a.children, a.pets, a.vehicles, a.referred,a.documents, t.tenant_id,t.tenant_first_name,t.tenant_last_name,t.tenant_email,t.tenant_phone_number,t.tenant_ssn,t.tenant_current_salary,t.tenant_salary_frequency,t.tenant_current_job_title,t.tenant_current_job_company,t.tenant_drivers_license_number,t.tenant_drivers_license_state, p.*, r.*, b.*, pM.*'
                tables = 'applications a LEFT JOIN tenantProfileInfo t ON a.tenant_id = t.tenant_id LEFT JOIN properties p ON a.property_uid = p.property_uid LEFT JOIN rentals r ON a.application_uid = r.linked_application_id LEFT JOIN pm.propertyManager pM ON pM.linked_property_id = p.property_uid LEFT JOIN pm.businesses b ON b.business_uid = pM.linked_business_id'
                response = db.select(cols=cols, tables=tables, where=where)
        return response

    def post(self):
        response = {}
        with connect() as db:
            data = request.json
            user = get_jwt_identity()
            if not user:
                return 401, response
            fields = ['property_uid', 'message',
                      'adults', 'children', 'pets', 'vehicles', 'referred']
            newApplication = {}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    newApplication[field] = fieldValue
            newApplicationID = db.call('new_application_id')[
                'result'][0]['new_id']

            newApplication['application_uid'] = newApplicationID
            print(newApplication)
            adults = (data.get('adults'))
            if len(adults) > 0:
                newApplication['adults'] = json.dumps(adults)
            children = (data.get('children'))
            if len(children) > 0:
                newApplication['children'] = json.dumps(children)
            pets = (data.get('pets'))
            if len(pets) > 0:
                newApplication['pets'] = json.dumps(pets)
            vehicles = (data.get('vehicles'))
            if len(vehicles) > 0:
                newApplication['vehicles'] = json.dumps(vehicles)
            referred = (data.get('referred'))
            if len(referred) > 0:
                newApplication['referred'] = json.dumps(referred)
            documents = (data.get('documents'))
            print(documents)
            for i, doc in enumerate(documents):
                filename = f'doc_{i}'
                file = request.files.get(filename)
                print(i, file)
                s3Link = doc.get('link')
                print(i, s3Link)
                if file:
                    doc['file'] = file
                elif s3Link:
                    doc['link'] = s3Link
                else:
                    break
            documents = updateDocuments(
                documents, newApplication['application_uid'])
            newApplication['documents'] = json.dumps(documents)
            # documents = (data.get('documents'))
            # newApplication['documents'] = json.dumps(documents)

            print('newApplication 1', newApplication)
            newApplication['tenant_id'] = user['tenant_id'][0]['tenant_id']
            newApplication['application_status'] = 'NEW'
            print('newApplication 2', newApplication)
            response = db.insert('applications', newApplication)
        return response

    def put(self):
        response = {}
        with connect() as db:
            data = request.json
            application_uid = data.get('application_uid')
            fields = ['message', 'application_status',
                      'property_uid', 'adults', 'children', 'pets', 'vehicles', "referred", "application_uid", "documents"]
            newApplication = {}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    newApplication[field] = fieldValue

            adults = (data.get('adults'))
            if adults is not None and len(adults) > 0:
                newApplication['adults'] = json.dumps(adults)
            children = (data.get('children'))
            if children is not None and len(children) > 0:
                newApplication['children'] = json.dumps(children)
            pets = (data.get('pets'))
            if pets is not None and len(pets) > 0:
                newApplication['pets'] = json.dumps(pets)
            vehicles = (data.get('vehicles'))
            if vehicles is not None and len(vehicles) > 0:
                newApplication['vehicles'] = json.dumps(vehicles)
            referred = (data.get('referred'))
            if referred is not None and len(referred) > 0:
                newApplication['referred'] = json.dumps(referred)
            documents = (data.get('documents'))
            print(documents)
            if documents is not None and len(documents) > 0:
                for i, doc in enumerate(documents):
                    filename = f'doc_{i}'
                    file = request.files.get(filename)
                    print(i, file)
                    s3Link = doc.get('link')
                    print(i, s3Link)
                    if file:
                        doc['file'] = file
                    elif s3Link:
                        doc['link'] = s3Link
                    else:
                        break
                documents = updateDocuments(
                    documents, application_uid)
                newApplication['documents'] = json.dumps(documents)
            # tenant approves lease aggreement
            if newApplication['application_status'] == 'RENTED':
                response = db.execute(
                    """SELECT * FROM pm.applications
                     WHERE application_status='FORWARDED' 
                     AND property_uid = \'""" + newApplication['property_uid'] + """\' """)
                # print('response', response, len(response['result']))
                if len(response['result']) > 1:
                    newApplication['application_status'] = 'ACCEPTED'
                else:
                    response = db.execute(
                        """SELECT * FROM pm.applications 
                        WHERE application_status='ACCEPTED' 
                        AND property_uid = \'""" + newApplication['property_uid'] + """\' """)
                    # print('response', response['result'])

                    if len(response['result']) > 0:
                        newApplication['application_status'] = 'RENTED'
                        for response in response['result']:
                            pk = {
                                'application_uid': response['application_uid']
                            }
                            response = db.update(
                                'applications', pk, newApplication)
                    # print(newApplication)
                    res = db.execute("""
                    SELECT  r.*, p.*, c.* , prop.*, 
                    GROUP_CONCAT(lt.linked_tenant_id) as `tenants`
                    FROM pm.rentals r
                    LEFT JOIN pm.leaseTenants lt
                    ON lt.linked_rental_uid = r.rental_uid
                    LEFT JOIN pm.propertyManager p
                    ON p.linked_property_id= r.rental_property_id
                    LEFT JOIN pm.properties prop
                    ON prop.property_uid = r.rental_property_id
                    LEFT JOIN pm.contracts c
                    ON c.property_uid = prop.property_uid
                    WHERE r.rental_status='PROCESSING'
                    AND (p.management_status = 'ACCEPTED' OR p.management_status='END EARLY' OR p.management_status='PM END EARLY' OR p.management_status='OWNER END EARLY')
                    AND r.rental_property_id = \'""" + newApplication['property_uid'] + """\' 
                    AND r.linked_application_id LIKE '%""" + newApplication['application_uid'] + """%'
                    AND c.contract_status = 'ACTIVE'
                    GROUP BY lt.linked_rental_uid; """)
                    # print('res', res, len(res['result']))

                    # print('tenants5', tenants)
                    # print('tenant_id', tenants)

                    tenants = res['result'][0]['tenants'].split(',')
                    print(tenants)
                    today = date.today()
                    start_date = date.fromisoformat(
                        res['result'][0]['lease_start'])
                    end_date = date.fromisoformat(
                        res['result'][0]['lease_end'])
                    rent = int(res['result'][0]['listed_rent'])
                    if len(res['result']) > 0:
                        # creating purchases
                        rentPayments = json.loads(
                            res['result'][0]['rent_payments'])
                        managementPayments = json.loads(
                            res['result'][0]['contract_fees'])

                    if len(res['result']) > 0:
                        # creating purchases
                        for payment in rentPayments:
                            print(payment)
                            # payment fee type $
                            if payment['fee_type'] == '$':
                                # payment fee purchase type Rent $
                                if(payment['fee_name'] == 'Rent'):
                                    print('payment fee purchase_type RENT')
                                    if payment['frequency'] == 'Weekly':
                                        print('payment frequency weekly $')
                                        # charge date-> when the payment is due to pay
                                        # charge_date = next_weekday(
                                        #     start_date, int(payment['due_by']))
                                        charge_date = date_for_weekday(
                                            int(payment['due_by']), start_date)
                                        charge_month = charge_date.strftime(
                                            '%B')
                                        # available date-> when the payment is available to pay
                                        if len(payment['available_topay']) == 0:
                                            available_date = charge_date
                                        else:
                                            available_date = charge_date - \
                                                timedelta(
                                                    days=int(payment['available_topay']))

                                        while available_date < today and charge_date < end_date:
                                            charge_month = charge_date.strftime(
                                                '%B')
                                            if charge_month == start_date.strftime('%B') and (charge_date-start_date).days < 7:
                                                daily_charge = int(
                                                    int(payment['charge']) / 7)
                                                print('daily_charge',
                                                      daily_charge)
                                                num_days_active = 7 - start_date.weekday()
                                                print('num_days_active',
                                                      num_days_active, start_date.weekday())
                                                charge = round(
                                                    num_days_active * daily_charge, 2)
                                                print('charge', charge)
                                            else:
                                                charge = int(
                                                    payment['charge'])
                                            purchaseResponse = newPurchase(
                                                linked_bill_id=None,
                                                pur_property_id=json.dumps(
                                                    [res['result'][0]['rental_property_id']]),
                                                payer=json.dumps(tenants),
                                                receiver=res['result'][0]['linked_business_id'],
                                                purchase_type='RENT',
                                                description=charge_month + ' ' +
                                                payment['fee_name'],
                                                # amount_due=prorated_charge,
                                                amount_due=charge,
                                                purchase_notes=charge_month,
                                                purchase_date=available_date,
                                                purchase_frequency=payment['frequency'],
                                                next_payment=charge_date
                                            )
                                            # manager payments weekly $ rent
                                            for mpayment in managementPayments:
                                                weeks_current_month = len(
                                                    calendar.monthcalendar(charge_date.year, int(charge_date.strftime("%m"))))
                                                print('mpayment fee type %')
                                                if mpayment['frequency'] == 'Weekly' and mpayment['fee_type'] == '%':
                                                    if mpayment['of'] == 'Gross Rent':

                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=weeks_current_month*(charge *
                                                                                            (1-mpayment['charge']/100)),
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                    # if net rent (listed rent-expenses)
                                                    else:

                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=weeks_current_month*((charge-mpayment['expense_amount'])*(
                                                                1-mpayment['charge']/100)),
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                elif mpayment['frequency'] == 'Biweekly' and mpayment['fee_type'] == '%':

                                                    # if gross rent (listed rent)
                                                    if mpayment['of'] == 'Gross Rent':

                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=(weeks_current_month/2) *
                                                            ((charge *
                                                                (1-mpayment['charge']/100)))/weeks_current_month/2,
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                    # if net rent (listed rent-expenses)
                                                    else:

                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=(weeks_current_month/2) *
                                                            ((charge-mpayment['expense_amount'])*(
                                                                1-mpayment['charge']/100))/weeks_current_month/2,
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )

                                                elif mpayment['frequency'] == 'Monthly' and mpayment['fee_type'] == '%':

                                                    # if gross rent (listed rent)
                                                    if mpayment['of'] == 'Gross Rent':
                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=(
                                                                charge*(1-int(mpayment['charge'])/100)),
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                        print(
                                                            purchaseResponse)

                                                    # if net rent (listed rent-expenses)
                                                    else:
                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=(
                                                                (charge-mpayment['expense_amount'])*(1-int(mpayment['charge'])/100)),
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                        print(
                                                            purchaseResponse)

                                                else:
                                                    print(
                                                        'payment frequency one-time %')

                                            charge_date += relativedelta(
                                                weeks=1)
                                            available_date += relativedelta(
                                                weeks=1)
                                    elif payment['frequency'] == 'Biweekly':
                                        print('payment frequency biweekly $')

                                        # charge_date = next_weekday_biweekly(
                                        #     start_date, int(payment['due_by']))
                                        charge_date = date_for_weekday(
                                            int(payment['due_by']), start_date)
                                        charge_month = charge_date.strftime(
                                            '%B')
                                        # available date-> when the payment is available to pay
                                        if len(payment['available_topay']) == 0:
                                            available_date = charge_date
                                        else:
                                            available_date = charge_date - \
                                                timedelta(
                                                    days=int(payment['available_topay']))

                                        while available_date < (today + relativedelta(
                                                weeks=2)) and charge_date < end_date:
                                            charge_month = charge_date.strftime(
                                                '%B')
                                            charge = int(
                                                payment['charge'])
                                            purchaseResponse = newPurchase(
                                                linked_bill_id=None,
                                                pur_property_id=json.dumps(
                                                    [res['result'][0]['rental_property_id']]),
                                                payer=json.dumps(tenants),
                                                receiver=res['result'][0]['linked_business_id'],
                                                purchase_type='RENT',
                                                description=charge_month + ' ' +
                                                payment['fee_name'],
                                                # amount_due=prorated_charge,
                                                amount_due=charge,
                                                purchase_notes=charge_month,
                                                purchase_date=available_date,
                                                purchase_frequency=payment['frequency'],
                                                next_payment=charge_date
                                            )
                                            # manager payments biweekly $ rent
                                            for mpayment in managementPayments:
                                                weeks_current_month = len(
                                                    calendar.monthcalendar(charge_date.year, int(charge_date.strftime("%m"))))
                                                print('mpayment fee type %')
                                                if mpayment['frequency'] == 'Weekly' and mpayment['fee_type'] == '%':
                                                    if mpayment['of'] == 'Gross Rent':

                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=weeks_current_month*(charge *
                                                                                            (1-mpayment['charge']/100)),
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                    # if net rent (listed rent-expenses)
                                                    else:

                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=weeks_current_month*((charge-mpayment['expense_amount'])*(
                                                                1-mpayment['charge']/100)),
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                elif mpayment['frequency'] == 'Biweekly' and mpayment['fee_type'] == '%':

                                                    # if gross rent (listed rent)
                                                    if mpayment['of'] == 'Gross Rent':

                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=(weeks_current_month/2) *
                                                            ((charge *
                                                                (1-mpayment['charge']/100)))/weeks_current_month/2,
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                    # if net rent (listed rent-expenses)
                                                    else:

                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=(weeks_current_month/2) *
                                                            ((charge-mpayment['expense_amount'])*(
                                                                1-mpayment['charge']/100))/weeks_current_month/2,
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )

                                                elif mpayment['frequency'] == 'Monthly' and mpayment['fee_type'] == '%':

                                                    # if gross rent (listed rent)
                                                    if mpayment['of'] == 'Gross Rent':
                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=(
                                                                charge*(1-int(mpayment['charge'])/100)),
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                        print(
                                                            purchaseResponse)

                                                    # if net rent (listed rent-expenses)
                                                    else:
                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=(
                                                                (charge-mpayment['expense_amount'])*(1-int(mpayment['charge'])/100)),
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                        print(
                                                            purchaseResponse)

                                                else:
                                                    print(
                                                        'payment frequency one-time %')

                                            charge_date += relativedelta(
                                                weeks=2)
                                            available_date += relativedelta(
                                                weeks=2)
                                    elif payment['frequency'] == 'Monthly':
                                        print('payment frequency monthly $')
                                        # charge date
                                        charge_date = (start_date.replace(
                                            day=int(payment['due_by'])))
                                        charge_month = charge_date.strftime(
                                            '%B')
                                        # available date-> when the payment is available to pay
                                        if len(payment['available_topay']) == 0:
                                            available_date = charge_date
                                        else:
                                            available_date = charge_date - \
                                                timedelta(
                                                    days=int(payment['available_topay']))
                                        while available_date < today and charge_date < end_date:
                                            charge_month = charge_date.strftime(
                                                '%B')
                                            if charge_month == start_date.strftime(
                                                    '%B') and start_date.strftime('%d') != '01':
                                                # prorate first month
                                                print('days_in_month(charge_date)', days_in_month(
                                                    charge_date))
                                                daily_charge_begin = int(
                                                    int(payment['charge']) / days_in_month(charge_date))
                                                num_days_active_begin = days_in_month(
                                                    charge_date) - start_date.day + 1
                                                charge = round(
                                                    num_days_active_begin * daily_charge_begin, 2)

                                            else:
                                                charge = int(payment['charge'])

                                            purchaseResponse = newPurchase(
                                                linked_bill_id=None,
                                                pur_property_id=json.dumps(
                                                    [res['result'][0]['rental_property_id']]),
                                                payer=json.dumps(tenants),
                                                receiver=res['result'][0]['linked_business_id'],
                                                purchase_type='RENT',
                                                description=charge_month +
                                                ' ' + payment['fee_name'],
                                                # amount_due=prorated_charge_begin,
                                                amount_due=charge,
                                                purchase_notes=charge_month,
                                                purchase_date=available_date,
                                                purchase_frequency=payment['frequency'],
                                                next_payment=charge_date
                                            )
                                            # manager payments weekly $ rent
                                            for mpayment in managementPayments:
                                                weeks_current_month = len(
                                                    calendar.monthcalendar(charge_date.year, int(charge_date.strftime("%m"))))
                                                print('mpayment fee type %')
                                                if mpayment['frequency'] == 'Weekly' and mpayment['fee_type'] == '%':
                                                    if mpayment['of'] == 'Gross Rent':

                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=weeks_current_month*(charge *
                                                                                            (1-mpayment['charge']/100)),
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                    # if net rent (listed rent-expenses)
                                                    else:

                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=weeks_current_month*((charge-mpayment['expense_amount'])*(
                                                                1-mpayment['charge']/100)),
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                elif mpayment['frequency'] == 'Biweekly' and mpayment['fee_type'] == '%':

                                                    # if gross rent (listed rent)
                                                    if mpayment['of'] == 'Gross Rent':

                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=(weeks_current_month/2) *
                                                            ((charge *
                                                                (1-mpayment['charge']/100)))/weeks_current_month/2,
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                    # if net rent (listed rent-expenses)
                                                    else:

                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=(weeks_current_month/2) *
                                                            ((charge-mpayment['expense_amount'])*(
                                                                1-mpayment['charge']/100))/weeks_current_month/2,
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )

                                                elif mpayment['frequency'] == 'Monthly' and mpayment['fee_type'] == '%':

                                                    # if gross rent (listed rent)
                                                    if mpayment['of'] == 'Gross Rent':
                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=(
                                                                charge*(1-int(mpayment['charge'])/100)),
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                        print(
                                                            purchaseResponse)

                                                    # if net rent (listed rent-expenses)
                                                    else:
                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=(
                                                                (charge-mpayment['expense_amount'])*(1-int(mpayment['charge'])/100)),
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                        print(
                                                            purchaseResponse)

                                                else:
                                                    print(
                                                        'payment frequency one-time %')

                                            charge_date += relativedelta(
                                                months=1)
                                            available_date += relativedelta(
                                                months=1)
                                    elif payment['frequency'] == 'Annually':
                                        print('payment frequency annually $')
                                        charge_date = (start_date.replace(
                                            day=int(payment['due_by'])))
                                        charge_month = charge_date.strftime(
                                            '%B')
                                        # available date-> when the payment is available to pay
                                        if len(payment['available_topay']) == 0:
                                            available_date = charge_date
                                        else:
                                            available_date = charge_date - \
                                                timedelta(
                                                    days=int(payment['available_topay']))
                                        charge = int(payment['charge'])
                                        purchaseResponse = newPurchase(
                                            linked_bill_id=None,
                                            pur_property_id=json.dumps(
                                                [res['result'][0]['rental_property_id']]),
                                            payer=json.dumps(tenants),
                                            receiver=res['result'][0]['linked_business_id'],
                                            purchase_type='RENT',
                                            description=payment['fee_name'] + ' ' + charge_date.strftime(
                                                '%Y'),
                                            amount_due=charge,
                                            purchase_notes=charge_month,
                                            purchase_date=available_date,
                                            purchase_frequency=payment['frequency'],
                                            next_payment=charge_date
                                        )
                                        # manager payments weekly $ rent
                                        for mpayment in managementPayments:
                                            weeks_current_month = len(
                                                calendar.monthcalendar(charge_date.year, int(charge_date.strftime("%m"))))
                                            print('mpayment fee type %')
                                            if mpayment['frequency'] == 'Weekly' and mpayment['fee_type'] == '%':
                                                if mpayment['of'] == 'Gross Rent':

                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [res['result'][0]['property_uid']]),
                                                        payer=json.dumps(
                                                            [res['result'][0]['business_uid']]),
                                                        receiver=res['result'][0]['owner_id'],
                                                        purchase_type='OWNER PAYMENT',
                                                        description=payment['fee_name'] + ' ' + charge_date.strftime(
                                                            '%Y'),
                                                        amount_due=weeks_current_month*(charge *
                                                                                        (1-mpayment['charge']/100)),
                                                        purchase_notes=charge_month,
                                                        purchase_date=available_date,
                                                        purchase_frequency=mpayment['frequency'],
                                                        next_payment=charge_date
                                                    )
                                                # if net rent (listed rent-expenses)
                                                else:

                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [res['result'][0]['property_uid']]),
                                                        payer=json.dumps(
                                                            [res['result'][0]['business_uid']]),
                                                        receiver=res['result'][0]['owner_id'],
                                                        purchase_type='OWNER PAYMENT',
                                                        description=payment['fee_name'] + ' ' + charge_date.strftime(
                                                            '%Y'),
                                                        amount_due=weeks_current_month*((charge-mpayment['expense_amount'])*(
                                                            1-mpayment['charge']/100)),
                                                        purchase_notes=charge_month,
                                                        purchase_date=available_date,
                                                        purchase_frequency=mpayment['frequency'],
                                                        next_payment=charge_date
                                                    )
                                            elif mpayment['frequency'] == 'Biweekly' and mpayment['fee_type'] == '%':

                                                # if gross rent (listed rent)
                                                if mpayment['of'] == 'Gross Rent':

                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [res['result'][0]['property_uid']]),
                                                        payer=json.dumps(
                                                            [res['result'][0]['business_uid']]),
                                                        receiver=res['result'][0]['owner_id'],
                                                        purchase_type='OWNER PAYMENT',
                                                        description=payment['fee_name'] + ' ' + charge_date.strftime(
                                                            '%Y'),
                                                        amount_due=(weeks_current_month/2) *
                                                        ((charge *
                                                            (1-mpayment['charge']/100)))/weeks_current_month/2,
                                                        purchase_notes=charge_month,
                                                        purchase_date=available_date,
                                                        purchase_frequency=mpayment['frequency'],
                                                        next_payment=charge_date
                                                    )
                                                # if net rent (listed rent-expenses)
                                                else:

                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [res['result'][0]['property_uid']]),
                                                        payer=json.dumps(
                                                            [res['result'][0]['business_uid']]),
                                                        receiver=res['result'][0]['owner_id'],
                                                        purchase_type='OWNER PAYMENT',
                                                        description=payment['fee_name'] + ' ' + charge_date.strftime(
                                                            '%Y'),
                                                        amount_due=(weeks_current_month/2) *
                                                        ((charge-mpayment['expense_amount'])*(
                                                            1-mpayment['charge']/100))/weeks_current_month/2,
                                                        purchase_notes=charge_month,
                                                        purchase_date=available_date,
                                                        purchase_frequency=mpayment['frequency'],
                                                        next_payment=charge_date
                                                    )

                                            elif mpayment['frequency'] == 'Monthly' and mpayment['fee_type'] == '%':

                                                # if gross rent (listed rent)
                                                if mpayment['of'] == 'Gross Rent':
                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [res['result'][0]['property_uid']]),
                                                        payer=json.dumps(
                                                            [res['result'][0]['business_uid']]),
                                                        receiver=res['result'][0]['owner_id'],
                                                        purchase_type='OWNER PAYMENT',
                                                        description=payment['fee_name'] + ' ' + charge_date.strftime(
                                                            '%Y'),
                                                        amount_due=(
                                                            charge*(1-int(mpayment['charge'])/100)),
                                                        purchase_notes=charge_month,
                                                        purchase_date=available_date,
                                                        purchase_frequency=mpayment['frequency'],
                                                        next_payment=charge_date
                                                    )
                                                    print(
                                                        purchaseResponse)

                                                # if net rent (listed rent-expenses)
                                                else:
                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [res['result'][0]['property_uid']]),
                                                        payer=json.dumps(
                                                            [res['result'][0]['business_uid']]),
                                                        receiver=res['result'][0]['owner_id'],
                                                        purchase_type='OWNER PAYMENT',
                                                        description=payment['fee_name'] + ' ' + charge_date.strftime(
                                                            '%Y'),
                                                        amount_due=(
                                                            (charge-mpayment['expense_amount'])*(1-int(mpayment['charge'])/100)),
                                                        purchase_notes=charge_month,
                                                        purchase_date=available_date,
                                                        purchase_frequency=mpayment['frequency'],
                                                        next_payment=charge_date
                                                    )
                                                    print(
                                                        purchaseResponse)

                                            else:
                                                print(
                                                    'payment frequency one-time %')
                                    else:
                                        print('payment frequency one-time $')
                                        charge_date = (start_date.replace(
                                            day=int(payment['due_by'])))
                                        charge_month = charge_date.strftime(
                                            '%B')
                                        # available date-> when the payment is available to pay
                                        if len(payment['available_topay']) == 0:
                                            available_date = charge_date
                                        else:
                                            available_date = charge_date - \
                                                timedelta(
                                                    days=int(payment['available_topay']))
                                        charge = int(payment['charge'])
                                        purchaseResponse = newPurchase(
                                            linked_bill_id=None,
                                            pur_property_id=json.dumps(
                                                [res['result'][0]['rental_property_id']]),
                                            payer=json.dumps(tenants),
                                            receiver=res['result'][0]['linked_business_id'],
                                            purchase_type='RENT',
                                            description=payment['fee_name'],
                                            amount_due=charge,
                                            purchase_notes=charge_month,
                                            purchase_date=available_date,
                                            purchase_frequency=payment['frequency'],
                                            next_payment=charge_date
                                        )
                                        # manager payments weekly $ rent
                                        for mpayment in managementPayments:
                                            weeks_current_month = len(
                                                calendar.monthcalendar(charge_date.year, int(charge_date.strftime("%m"))))
                                            print('mpayment fee type %')
                                            if mpayment['frequency'] == 'Weekly' and mpayment['fee_type'] == '%':
                                                if mpayment['of'] == 'Gross Rent':

                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [res['result'][0]['property_uid']]),
                                                        payer=json.dumps(
                                                            [res['result'][0]['business_uid']]),
                                                        receiver=res['result'][0]['owner_id'],
                                                        purchase_type='OWNER PAYMENT',
                                                        description=payment['fee_name'],
                                                        amount_due=weeks_current_month*(charge *
                                                                                        (1-mpayment['charge']/100)),
                                                        purchase_notes=charge_month,
                                                        purchase_date=available_date,
                                                        purchase_frequency=mpayment['frequency'],
                                                        next_payment=charge_date
                                                    )
                                                # if net rent (listed rent-expenses)
                                                else:

                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [res['result'][0]['property_uid']]),
                                                        payer=json.dumps(
                                                            [res['result'][0]['business_uid']]),
                                                        receiver=res['result'][0]['owner_id'],
                                                        purchase_type='OWNER PAYMENT',
                                                        description=payment['fee_name'],
                                                        amount_due=weeks_current_month*((charge-mpayment['expense_amount'])*(
                                                            1-mpayment['charge']/100)),
                                                        purchase_notes=charge_month,
                                                        purchase_date=available_date,
                                                        purchase_frequency=mpayment['frequency'],
                                                        next_payment=charge_date
                                                    )
                                            elif mpayment['frequency'] == 'Biweekly' and mpayment['fee_type'] == '%':

                                                # if gross rent (listed rent)
                                                if mpayment['of'] == 'Gross Rent':

                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [res['result'][0]['property_uid']]),
                                                        payer=json.dumps(
                                                            [res['result'][0]['business_uid']]),
                                                        receiver=res['result'][0]['owner_id'],
                                                        purchase_type='OWNER PAYMENT',
                                                        description=payment['fee_name'],
                                                        amount_due=(weeks_current_month/2) *
                                                        ((charge *
                                                            (1-mpayment['charge']/100)))/weeks_current_month/2,
                                                        purchase_notes=charge_month,
                                                        purchase_date=available_date,
                                                        purchase_frequency=mpayment['frequency'],
                                                        next_payment=charge_date
                                                    )
                                                # if net rent (listed rent-expenses)
                                                else:

                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [res['result'][0]['property_uid']]),
                                                        payer=json.dumps(
                                                            [res['result'][0]['business_uid']]),
                                                        receiver=res['result'][0]['owner_id'],
                                                        purchase_type='OWNER PAYMENT',
                                                        description=payment['fee_name'],
                                                        amount_due=(weeks_current_month/2) *
                                                        ((charge-mpayment['expense_amount'])*(
                                                            1-mpayment['charge']/100))/weeks_current_month/2,
                                                        purchase_notes=charge_month,
                                                        purchase_date=available_date,
                                                        purchase_frequency=mpayment['frequency'],
                                                        next_payment=charge_date
                                                    )

                                            elif mpayment['frequency'] == 'Monthly' and mpayment['fee_type'] == '%':

                                                # if gross rent (listed rent)
                                                if mpayment['of'] == 'Gross Rent':
                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [res['result'][0]['property_uid']]),
                                                        payer=json.dumps(
                                                            [res['result'][0]['business_uid']]),
                                                        receiver=res['result'][0]['owner_id'],
                                                        purchase_type='OWNER PAYMENT',
                                                        description=payment['fee_name'],
                                                        amount_due=(
                                                            charge*(1-int(mpayment['charge'])/100)),
                                                        purchase_notes=charge_month,
                                                        purchase_date=available_date,
                                                        purchase_frequency=mpayment['frequency'],
                                                        next_payment=charge_date
                                                    )
                                                    print(
                                                        purchaseResponse)

                                                # if net rent (listed rent-expenses)
                                                else:
                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [res['result'][0]['property_uid']]),
                                                        payer=json.dumps(
                                                            [res['result'][0]['business_uid']]),
                                                        receiver=res['result'][0]['owner_id'],
                                                        purchase_type='OWNER PAYMENT',
                                                        description=payment['fee_name'],
                                                        amount_due=(
                                                            (charge-mpayment['expense_amount'])*(1-int(mpayment['charge'])/100)),
                                                        purchase_notes=charge_month,
                                                        purchase_date=available_date,
                                                        purchase_frequency=mpayment['frequency'],
                                                        next_payment=charge_date
                                                    )
                                                    print(
                                                        purchaseResponse)

                                            else:
                                                print(
                                                    'payment frequency one-time %')

                                 # payment fee frequency is move out $
                                elif payment['frequency'] == 'Move-Out Charge':
                                    print(
                                        'payment fee purchase_type Move-Out Charge ')

                                    print('skip')
                                # payment fee frequency is move in $
                                elif payment['frequency'] == 'Move-in Charge':
                                    print(
                                        'payment fee purchase_type MOVE IN')
                                    charge_date = (start_date.replace(
                                        day=int(payment['due_by'])))
                                    charge_month = charge_date.strftime(
                                        '%B')
                                    # available date-> when the payment is available to pay
                                    if len(payment['available_topay']) == 0:
                                        available_date = charge_date
                                    else:
                                        available_date = charge_date - \
                                            timedelta(
                                                days=int(payment['available_topay']))
                                    charge = int(payment['charge'])
                                    purchaseResponse = newPurchase(
                                        linked_bill_id=None,
                                        pur_property_id=json.dumps(
                                            [res['result'][0]['rental_property_id']]),
                                        payer=json.dumps(tenants),
                                        receiver=res['result'][0]['linked_business_id'],
                                        purchase_type='EXTRA CHARGES',
                                        description=payment['fee_name'],
                                        amount_due=payment['charge'],
                                        purchase_notes=charge_month,
                                        purchase_date=available_date,
                                        purchase_frequency=payment['frequency'],
                                        next_payment=charge_date
                                    )
                                    # manager payments weekly $ rent
                                    for mpayment in managementPayments:
                                        weeks_current_month = len(
                                            calendar.monthcalendar(charge_date.year, int(charge_date.strftime("%m"))))
                                        print('mpayment fee type %')
                                        if mpayment['frequency'] == 'Weekly' and mpayment['fee_type'] == '%':
                                            if mpayment['of'] == 'Gross Rent':

                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [res['result'][0]['property_uid']]),
                                                    payer=json.dumps(
                                                        [res['result'][0]['business_uid']]),
                                                    receiver=res['result'][0]['owner_id'],
                                                    purchase_type='OWNER PAYMENT',
                                                    description=payment['fee_name'],
                                                    amount_due=weeks_current_month*(charge *
                                                                                    (1-mpayment['charge']/100)),
                                                    purchase_notes=charge_month,
                                                    purchase_date=available_date,
                                                    purchase_frequency=mpayment['frequency'],
                                                    next_payment=charge_date
                                                )
                                            # if net rent (listed rent-expenses)
                                            else:

                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [res['result'][0]['property_uid']]),
                                                    payer=json.dumps(
                                                        [res['result'][0]['business_uid']]),
                                                    receiver=res['result'][0]['owner_id'],
                                                    purchase_type='OWNER PAYMENT',
                                                    description=payment['fee_name'],
                                                    amount_due=weeks_current_month*((charge-mpayment['expense_amount'])*(
                                                        1-mpayment['charge']/100)),
                                                    purchase_notes=charge_month,
                                                    purchase_date=available_date,
                                                    purchase_frequency=mpayment['frequency'],
                                                    next_payment=charge_date
                                                )
                                        elif mpayment['frequency'] == 'Biweekly' and mpayment['fee_type'] == '%':

                                            # if gross rent (listed rent)
                                            if mpayment['of'] == 'Gross Rent':

                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [res['result'][0]['property_uid']]),
                                                    payer=json.dumps(
                                                        [res['result'][0]['business_uid']]),
                                                    receiver=res['result'][0]['owner_id'],
                                                    purchase_type='OWNER PAYMENT',
                                                    description=payment['fee_name'],
                                                    amount_due=(weeks_current_month/2) *
                                                    ((charge *
                                                        (1-mpayment['charge']/100)))/weeks_current_month/2,
                                                    purchase_notes=charge_month,
                                                    purchase_date=available_date,
                                                    purchase_frequency=mpayment['frequency'],
                                                    next_payment=charge_date
                                                )
                                            # if net rent (listed rent-expenses)
                                            else:

                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [res['result'][0]['property_uid']]),
                                                    payer=json.dumps(
                                                        [res['result'][0]['business_uid']]),
                                                    receiver=res['result'][0]['owner_id'],
                                                    purchase_type='OWNER PAYMENT',
                                                    description=payment['fee_name'],
                                                    amount_due=(weeks_current_month/2) *
                                                    ((charge-mpayment['expense_amount'])*(
                                                        1-mpayment['charge']/100))/weeks_current_month/2,
                                                    purchase_notes=charge_month,
                                                    purchase_date=available_date,
                                                    purchase_frequency=mpayment['frequency'],
                                                    next_payment=charge_date
                                                )

                                        elif mpayment['frequency'] == 'Monthly' and mpayment['fee_type'] == '%':

                                            # if gross rent (listed rent)
                                            if mpayment['of'] == 'Gross Rent':
                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [res['result'][0]['property_uid']]),
                                                    payer=json.dumps(
                                                        [res['result'][0]['business_uid']]),
                                                    receiver=res['result'][0]['owner_id'],
                                                    purchase_type='OWNER PAYMENT',
                                                    description=payment['fee_name'],
                                                    amount_due=(
                                                        charge*(1-int(mpayment['charge'])/100)),
                                                    purchase_notes=charge_month,
                                                    purchase_date=available_date,
                                                    purchase_frequency=mpayment['frequency'],
                                                    next_payment=charge_date
                                                )
                                                print(
                                                    purchaseResponse)

                                            # if net rent (listed rent-expenses)
                                            else:
                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [res['result'][0]['property_uid']]),
                                                    payer=json.dumps(
                                                        [res['result'][0]['business_uid']]),
                                                    receiver=res['result'][0]['owner_id'],
                                                    purchase_type='OWNER PAYMENT',
                                                    description=payment['fee_name'],
                                                    amount_due=(
                                                        (charge-mpayment['expense_amount'])*(1-int(mpayment['charge'])/100)),
                                                    purchase_notes=charge_month,
                                                    purchase_date=available_date,
                                                    purchase_frequency=mpayment['frequency'],
                                                    next_payment=charge_date
                                                )
                                                print(
                                                    purchaseResponse)
                                        elif mpayment['frequency'] == 'Move-in Charge' and mpayment['fee_type'] == '%':

                                            # if gross rent (listed rent)
                                            if mpayment['of'] == 'Gross Rent':
                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [res['result'][0]['property_uid']]),
                                                    payer=json.dumps(
                                                        [res['result'][0]['business_uid']]),
                                                    receiver=res['result'][0]['owner_id'],
                                                    purchase_type='OWNER PAYMENT',
                                                    description=payment['fee_name'],
                                                    amount_due=(
                                                        charge*(1-int(mpayment['charge'])/100)),
                                                    purchase_notes=charge_month,
                                                    purchase_date=available_date,
                                                    purchase_frequency=mpayment['frequency'],
                                                    next_payment=charge_date
                                                )
                                                print(
                                                    purchaseResponse)

                                            # if net rent (listed rent-expenses)
                                            else:
                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [res['result'][0]['property_uid']]),
                                                    payer=json.dumps(
                                                        [res['result'][0]['business_uid']]),
                                                    receiver=res['result'][0]['owner_id'],
                                                    purchase_type='OWNER PAYMENT',
                                                    description=payment['fee_name'],
                                                    amount_due=(
                                                        (charge-mpayment['expense_amount'])*(1-int(mpayment['charge'])/100)),
                                                    purchase_notes=charge_month,
                                                    purchase_date=available_date,
                                                    purchase_frequency=mpayment['frequency'],
                                                    next_payment=charge_date
                                                )
                                                print(
                                                    purchaseResponse)
                                        elif mpayment['frequency'] == 'Move-in Charge' and mpayment['fee_type'] == '$':
                                            # if gross rent (listed rent)
                                            if mpayment['of'] == 'Gross Rent':
                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [res['result'][0]['property_uid']]),
                                                    payer=json.dumps(
                                                        [res['result'][0]['business_uid']]),
                                                    receiver=res['result'][0]['owner_id'],
                                                    purchase_type='OWNER PAYMENT',
                                                    description=payment['fee_name'],
                                                    amount_due=int(
                                                        mpayment['charge']),
                                                    purchase_notes=charge_month,
                                                    purchase_date=available_date,
                                                    purchase_frequency=mpayment['frequency'],
                                                    next_payment=charge_date
                                                )
                                                print(
                                                    purchaseResponse)
                                        else:
                                            print(
                                                'payment frequency one-time %')

                                # payment fee purchase type Extra Charges $
                                else:
                                    print(
                                        'payment fee purchase_type EXTRA CHARGES')
                                    if payment['frequency'] == 'Weekly':
                                        print('payment frequency weekly $')

                                        # charge date-> when the payment is due to pay
                                        # charge_date = next_weekday(
                                        #     start_date, int(payment['due_by']))

                                        charge_date = date_for_weekday(
                                            int(payment['due_by']), start_date)
                                        charge_month = charge_date.strftime(
                                            '%B')
                                        # available date-> when the payment is available to pay
                                        if len(payment['available_topay']) == 0:
                                            available_date = charge_date
                                        else:
                                            available_date = charge_date - \
                                                timedelta(
                                                    days=int(payment['available_topay']))
                                        while available_date < (today + relativedelta(
                                                weeks=1)) and charge_date < end_date:
                                            charge_month = charge_date.strftime(
                                                '%B')
                                            if charge_month == start_date.strftime('%B') and (charge_date-start_date).days < 7:
                                                daily_charge = int(
                                                    int(payment['charge']) / 7)
                                                print('daily_charge',
                                                      daily_charge)
                                                num_days_active = 7 - start_date.weekday()
                                                print('num_days_active',
                                                      num_days_active)
                                                charge = round(
                                                    num_days_active * daily_charge, 2)
                                                print('charge', charge)
                                            else:
                                                charge = int(
                                                    payment['charge'])
                                            purchaseResponse = newPurchase(
                                                linked_bill_id=None,
                                                pur_property_id=json.dumps(
                                                    [res['result'][0]['rental_property_id']]),
                                                payer=json.dumps(tenants),
                                                receiver=res['result'][0]['linked_business_id'],
                                                purchase_type='EXTRA CHARGES',
                                                description=charge_month + ' ' +
                                                payment['fee_name'],
                                                amount_due=charge,
                                                purchase_notes=charge_month,
                                                purchase_date=available_date,
                                                purchase_frequency=payment['frequency'],
                                                next_payment=charge_date
                                            )
                                            # manager payments weekly $ rent
                                            for mpayment in managementPayments:
                                                weeks_current_month = len(
                                                    calendar.monthcalendar(charge_date.year, int(charge_date.strftime("%m"))))
                                                print('mpayment fee type %')
                                                if mpayment['frequency'] == 'Weekly' and mpayment['fee_type'] == '%':
                                                    if mpayment['of'] == 'Gross Rent':

                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=weeks_current_month*(charge *
                                                                                            (1-mpayment['charge']/100)),
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                    # if net rent (listed rent-expenses)
                                                    else:

                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=weeks_current_month*((charge-mpayment['expense_amount'])*(
                                                                1-mpayment['charge']/100)),
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                elif mpayment['frequency'] == 'Biweekly' and mpayment['fee_type'] == '%':

                                                    # if gross rent (listed rent)
                                                    if mpayment['of'] == 'Gross Rent':

                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=(weeks_current_month/2) *
                                                            ((charge *
                                                                (1-mpayment['charge']/100)))/weeks_current_month/2,
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                    # if net rent (listed rent-expenses)
                                                    else:

                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=(weeks_current_month/2) *
                                                            ((charge-mpayment['expense_amount'])*(
                                                                1-mpayment['charge']/100))/weeks_current_month/2,
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )

                                                elif mpayment['frequency'] == 'Monthly' and mpayment['fee_type'] == '%':

                                                    # if gross rent (listed rent)
                                                    if mpayment['of'] == 'Gross Rent':
                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=(
                                                                charge*(1-int(mpayment['charge'])/100)),
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                        print(
                                                            purchaseResponse)

                                                    # if net rent (listed rent-expenses)
                                                    else:
                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=(
                                                                (charge-mpayment['expense_amount'])*(1-int(mpayment['charge'])/100)),
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                        print(
                                                            purchaseResponse)

                                                else:
                                                    print(
                                                        'payment frequency one-time %')

                                            charge_date += relativedelta(
                                                weeks=1)
                                            available_date += relativedelta(
                                                weeks=1)
                                    elif payment['frequency'] == 'Biweekly':
                                        print('payment frequency biweekly $')
                                        # charge_date = next_weekday_biweekly(
                                        #     start_date, int(payment['due_by']))
                                        charge_date = date_for_weekday(
                                            int(payment['due_by']), start_date)
                                        charge_month = charge_date.strftime(
                                            '%B')
                                        # available date-> when the payment is available to pay
                                        if len(payment['available_topay']) == 0:
                                            available_date = charge_date
                                        else:
                                            available_date = charge_date - \
                                                timedelta(
                                                    days=int(payment['available_topay']))
                                        while available_date < (today + relativedelta(
                                                weeks=2)) and charge_date < end_date:
                                            charge_month = charge_date.strftime(
                                                '%B')
                                            charge = int(
                                                payment['charge'])
                                            purchaseResponse = newPurchase(
                                                linked_bill_id=None,
                                                pur_property_id=json.dumps(
                                                    [res['result'][0]['rental_property_id']]),
                                                payer=json.dumps(tenants),
                                                receiver=res['result'][0]['linked_business_id'],
                                                purchase_type='EXTRA CHARGES',
                                                description=charge_month + ' ' +
                                                payment['fee_name'],
                                                # amount_due=prorated_charge,
                                                amount_due=charge,
                                                purchase_notes=charge_month,
                                                purchase_date=available_date,
                                                purchase_frequency=payment['frequency'],
                                                next_payment=charge_date
                                            )
                                            # manager payments weekly $ rent
                                            for mpayment in managementPayments:
                                                weeks_current_month = len(
                                                    calendar.monthcalendar(charge_date.year, int(charge_date.strftime("%m"))))
                                                print('mpayment fee type %')
                                                if mpayment['frequency'] == 'Weekly' and mpayment['fee_type'] == '%':
                                                    if mpayment['of'] == 'Gross Rent':

                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=weeks_current_month*(charge *
                                                                                            (1-mpayment['charge']/100)),
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                    # if net rent (listed rent-expenses)
                                                    else:

                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=weeks_current_month*((charge-mpayment['expense_amount'])*(
                                                                1-mpayment['charge']/100)),
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                elif mpayment['frequency'] == 'Biweekly' and mpayment['fee_type'] == '%':

                                                    # if gross rent (listed rent)
                                                    if mpayment['of'] == 'Gross Rent':

                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=(weeks_current_month/2) *
                                                            ((charge *
                                                                (1-mpayment['charge']/100)))/weeks_current_month/2,
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                    # if net rent (listed rent-expenses)
                                                    else:

                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=(weeks_current_month/2) *
                                                            ((charge-mpayment['expense_amount'])*(
                                                                1-mpayment['charge']/100))/weeks_current_month/2,
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )

                                                elif mpayment['frequency'] == 'Monthly' and mpayment['fee_type'] == '%':

                                                    # if gross rent (listed rent)
                                                    if mpayment['of'] == 'Gross Rent':
                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=(
                                                                charge*(1-int(mpayment['charge'])/100)),
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                        print(
                                                            purchaseResponse)

                                                    # if net rent (listed rent-expenses)
                                                    else:
                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=(
                                                                (charge-mpayment['expense_amount'])*(1-int(mpayment['charge'])/100)),
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                        print(
                                                            purchaseResponse)

                                                else:
                                                    print(
                                                        'payment frequency one-time %')

                                            charge_date += relativedelta(
                                                weeks=2)
                                            available_date += relativedelta(
                                                weeks=2)
                                            print(charge_date)
                                            print(available_date)
                                            print(today+relativedelta(
                                                weeks=2))
                                    elif payment['frequency'] == 'Monthly':
                                        print('payment frequency monthly $')
                                        # charge date
                                        charge_date = (start_date.replace(
                                            day=int(payment['due_by'])))
                                        charge_month = charge_date.strftime(
                                            '%B')
                                        # available date-> when the payment is available to pay
                                        if len(payment['available_topay']) == 0:
                                            available_date = charge_date
                                        else:
                                            available_date = charge_date - \
                                                timedelta(
                                                    days=int(payment['available_topay']))
                                        while available_date < today and charge_date < end_date:
                                            charge_month = charge_date.strftime(
                                                '%B')
                                            if charge_month == start_date.strftime(
                                                    '%B') and start_date.strftime('%d') != '01':
                                                # prorate first month
                                                print('days_in_month(charge_date)', days_in_month(
                                                    charge_date))
                                                daily_charge_begin = int(
                                                    int(payment['charge']) / days_in_month(charge_date))
                                                num_days_active_begin = days_in_month(
                                                    charge_date) - start_date.day + 1
                                                charge = round(
                                                    num_days_active_begin * daily_charge_begin, 2)

                                            else:
                                                charge = int(payment['charge'])
                                            purchaseResponse = newPurchase(
                                                linked_bill_id=None,
                                                pur_property_id=json.dumps(
                                                    [res['result'][0]['rental_property_id']]),
                                                payer=json.dumps(tenants),
                                                receiver=res['result'][0]['linked_business_id'],
                                                purchase_type='EXTRA CHARGES',
                                                description=charge_month +
                                                ' ' + payment['fee_name'],
                                                amount_due=charge,
                                                purchase_notes=charge_month,
                                                purchase_date=available_date,
                                                purchase_frequency=payment['frequency'],
                                                next_payment=charge_date
                                            )
                                            # manager payments weekly $ rent
                                            for mpayment in managementPayments:
                                                weeks_current_month = len(
                                                    calendar.monthcalendar(charge_date.year, int(charge_date.strftime("%m"))))
                                                print('mpayment fee type %')
                                                if mpayment['frequency'] == 'Weekly' and mpayment['fee_type'] == '%':
                                                    if mpayment['of'] == 'Gross Rent':

                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=weeks_current_month*(charge *
                                                                                            (1-mpayment['charge']/100)),
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                    # if net rent (listed rent-expenses)
                                                    else:

                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=weeks_current_month*((charge-mpayment['expense_amount'])*(
                                                                1-mpayment['charge']/100)),
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                elif mpayment['frequency'] == 'Biweekly' and mpayment['fee_type'] == '%':

                                                    # if gross rent (listed rent)
                                                    if mpayment['of'] == 'Gross Rent':

                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=(weeks_current_month/2) *
                                                            ((charge *
                                                                (1-mpayment['charge']/100)))/weeks_current_month/2,
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                    # if net rent (listed rent-expenses)
                                                    else:

                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=(weeks_current_month/2) *
                                                            ((charge-mpayment['expense_amount'])*(
                                                                1-mpayment['charge']/100))/weeks_current_month/2,
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )

                                                elif mpayment['frequency'] == 'Monthly' and mpayment['fee_type'] == '%':

                                                    # if gross rent (listed rent)
                                                    if mpayment['of'] == 'Gross Rent':
                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=(
                                                                charge*(1-int(mpayment['charge'])/100)),
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                        print(
                                                            purchaseResponse)

                                                    # if net rent (listed rent-expenses)
                                                    else:
                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=(
                                                                (charge-mpayment['expense_amount'])*(1-int(mpayment['charge'])/100)),
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                        print(
                                                            purchaseResponse)

                                                else:
                                                    print(
                                                        'payment frequency one-time %')

                                            charge_date += relativedelta(
                                                months=1)
                                            available_date += relativedelta(
                                                months=1)
                                    elif payment['frequency'] == 'Annually':
                                        print('payment frequency annually $')
                                        charge_date = (start_date.replace(
                                            day=int(payment['due_by'])))
                                        charge_month = charge_date.strftime(
                                            '%B')
                                        print('charge_date', charge_date)
                                        # available date-> when the payment is available to pay
                                        if len(payment['available_topay']) == 0:
                                            available_date = charge_date
                                        else:
                                            available_date = charge_date - \
                                                timedelta(
                                                    days=int(payment['available_topay']))
                                        charge = int(payment['charge'])
                                        purchaseResponse = newPurchase(
                                            linked_bill_id=None,
                                            pur_property_id=json.dumps(
                                                [res['result'][0]['rental_property_id']]),
                                            payer=json.dumps(tenants),
                                            receiver=res['result'][0]['linked_business_id'],
                                            purchase_type='EXTRA CHARGES',
                                            description=payment['fee_name'] + ' ' + charge_date.strftime(
                                                '%Y'),
                                            amount_due=charge,
                                            purchase_notes=charge_month,
                                            purchase_date=available_date,
                                            purchase_frequency=payment['frequency'],
                                            next_payment=charge_date
                                        )
                                        # manager payments weekly $ rent
                                        for mpayment in managementPayments:
                                            weeks_current_month = len(
                                                calendar.monthcalendar(charge_date.year, int(charge_date.strftime("%m"))))
                                            print('mpayment fee type %')
                                            if mpayment['frequency'] == 'Weekly' and mpayment['fee_type'] == '%':
                                                if mpayment['of'] == 'Gross Rent':

                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [res['result'][0]['property_uid']]),
                                                        payer=json.dumps(
                                                            [res['result'][0]['business_uid']]),
                                                        receiver=res['result'][0]['owner_id'],
                                                        purchase_type='OWNER PAYMENT',
                                                        description=payment['fee_name'] + ' ' + charge_date.strftime(
                                                            '%Y'),
                                                        amount_due=weeks_current_month*(charge *
                                                                                        (1-mpayment['charge']/100)),
                                                        purchase_notes=charge_month,
                                                        purchase_date=available_date,
                                                        purchase_frequency=mpayment['frequency'],
                                                        next_payment=charge_date
                                                    )
                                                # if net rent (listed rent-expenses)
                                                else:

                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [res['result'][0]['property_uid']]),
                                                        payer=json.dumps(
                                                            [res['result'][0]['business_uid']]),
                                                        receiver=res['result'][0]['owner_id'],
                                                        purchase_type='OWNER PAYMENT',
                                                        description=payment['fee_name'] + ' ' + charge_date.strftime(
                                                            '%Y'),
                                                        amount_due=weeks_current_month*((charge-mpayment['expense_amount'])*(
                                                            1-mpayment['charge']/100)),
                                                        purchase_notes=charge_month,
                                                        purchase_date=available_date,
                                                        purchase_frequency=mpayment['frequency'],
                                                        next_payment=charge_date
                                                    )
                                            elif mpayment['frequency'] == 'Biweekly' and mpayment['fee_type'] == '%':

                                                # if gross rent (listed rent)
                                                if mpayment['of'] == 'Gross Rent':

                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [res['result'][0]['property_uid']]),
                                                        payer=json.dumps(
                                                            [res['result'][0]['business_uid']]),
                                                        receiver=res['result'][0]['owner_id'],
                                                        purchase_type='OWNER PAYMENT',
                                                        description=payment['fee_name'] + ' ' + charge_date.strftime(
                                                            '%Y'),
                                                        amount_due=(weeks_current_month/2) *
                                                        ((charge *
                                                            (1-mpayment['charge']/100)))/weeks_current_month/2,
                                                        purchase_notes=charge_month,
                                                        purchase_date=available_date,
                                                        purchase_frequency=mpayment['frequency'],
                                                        next_payment=charge_date
                                                    )
                                                # if net rent (listed rent-expenses)
                                                else:

                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [res['result'][0]['property_uid']]),
                                                        payer=json.dumps(
                                                            [res['result'][0]['business_uid']]),
                                                        receiver=res['result'][0]['owner_id'],
                                                        purchase_type='OWNER PAYMENT',
                                                        description=payment['fee_name'] + ' ' + charge_date.strftime(
                                                            '%Y'),
                                                        amount_due=(weeks_current_month/2) *
                                                        ((charge-mpayment['expense_amount'])*(
                                                            1-mpayment['charge']/100))/weeks_current_month/2,
                                                        purchase_notes=charge_month,
                                                        purchase_date=available_date,
                                                        purchase_frequency=mpayment['frequency'],
                                                        next_payment=charge_date
                                                    )

                                            elif mpayment['frequency'] == 'Monthly' and mpayment['fee_type'] == '%':

                                                # if gross rent (listed rent)
                                                if mpayment['of'] == 'Gross Rent':
                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [res['result'][0]['property_uid']]),
                                                        payer=json.dumps(
                                                            [res['result'][0]['business_uid']]),
                                                        receiver=res['result'][0]['owner_id'],
                                                        purchase_type='OWNER PAYMENT',
                                                        description=payment['fee_name'] + ' ' + charge_date.strftime(
                                                            '%Y'),
                                                        amount_due=(
                                                            charge*(1-int(mpayment['charge'])/100)),
                                                        purchase_notes=charge_month,
                                                        purchase_date=available_date,
                                                        purchase_frequency=mpayment['frequency'],
                                                        next_payment=charge_date
                                                    )
                                                    print(
                                                        purchaseResponse)

                                                # if net rent (listed rent-expenses)
                                                else:
                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [res['result'][0]['property_uid']]),
                                                        payer=json.dumps(
                                                            [res['result'][0]['business_uid']]),
                                                        receiver=res['result'][0]['owner_id'],
                                                        purchase_type='OWNER PAYMENT',
                                                        description=payment['fee_name'] + ' ' + charge_date.strftime(
                                                            '%Y'),
                                                        amount_due=(
                                                            (charge-mpayment['expense_amount'])*(1-int(mpayment['charge'])/100)),
                                                        purchase_notes=charge_month,
                                                        purchase_date=available_date,
                                                        purchase_frequency=mpayment['frequency'],
                                                        next_payment=charge_date
                                                    )
                                                    print(
                                                        purchaseResponse)

                                            else:
                                                print(
                                                    'payment frequency one-time %')
                                    else:
                                        print('payment frequency one-time $')
                                        charge_date = start_date.replace(
                                            day=1)
                                        charge_month = (
                                            charge_date).strftime('%B')
                                        # available date-> when the payment is available to pay
                                        if len(payment['available_topay']) == 0:
                                            available_date = charge_date
                                        else:
                                            available_date = charge_date - \
                                                timedelta(
                                                    days=int(payment['available_topay']))
                                        charge = int(payment['charge'])

                                        purchaseResponse = newPurchase(
                                            linked_bill_id=None,
                                            pur_property_id=json.dumps(
                                                [res['result'][0]['rental_property_id']]),
                                            payer=json.dumps(tenants),
                                            receiver=res['result'][0]['linked_business_id'],
                                            purchase_type='EXTRA CHARGES',
                                            description=payment['fee_name'],
                                            amount_due=charge,
                                            purchase_notes=charge_month,
                                            purchase_date=available_date,
                                            purchase_frequency=payment['frequency'],
                                            next_payment=charge_date
                                        )
                                        # manager payments weekly $ rent
                                        if payment['fee_name'] != 'Deposit':
                                            for mpayment in managementPayments:
                                                weeks_current_month = len(
                                                    calendar.monthcalendar(charge_date.year, int(charge_date.strftime("%m"))))
                                                print('mpayment fee type %')
                                                if mpayment['frequency'] == 'Weekly' and mpayment['fee_type'] == '%':
                                                    if mpayment['of'] == 'Gross Rent':

                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=payment['fee_name'],
                                                            amount_due=weeks_current_month*(charge *
                                                                                            (1-mpayment['charge']/100)),
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                    # if net rent (listed rent-expenses)
                                                    else:

                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=payment['fee_name'],
                                                            amount_due=weeks_current_month*((charge-mpayment['expense_amount'])*(
                                                                1-mpayment['charge']/100)),
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                elif mpayment['frequency'] == 'Biweekly' and mpayment['fee_type'] == '%':

                                                    # if gross rent (listed rent)
                                                    if mpayment['of'] == 'Gross Rent':

                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=payment['fee_name'],
                                                            amount_due=(weeks_current_month/2) *
                                                            ((charge *
                                                                (1-mpayment['charge']/100)))/weeks_current_month/2,
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                    # if net rent (listed rent-expenses)
                                                    else:

                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=payment['fee_name'],
                                                            amount_due=(weeks_current_month/2) *
                                                            ((charge-mpayment['expense_amount'])*(
                                                                1-mpayment['charge']/100))/weeks_current_month/2,
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )

                                                elif mpayment['frequency'] == 'Monthly' and mpayment['fee_type'] == '%':

                                                    # if gross rent (listed rent)
                                                    if mpayment['of'] == 'Gross Rent':
                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=payment['fee_name'],
                                                            amount_due=(
                                                                charge*(1-int(mpayment['charge'])/100)),
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                        print(
                                                            purchaseResponse)

                                                    # if net rent (listed rent-expenses)
                                                    else:
                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=payment['fee_name'],
                                                            amount_due=(
                                                                (charge-mpayment['expense_amount'])*(1-int(mpayment['charge'])/100)),
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                        print(
                                                            purchaseResponse)

                                                else:
                                                    print(
                                                        'payment frequency one-time %')

                            # payment fee type %
                            else:
                                # payment fee frequency is move out %
                                if payment['frequency'] == 'Move-Out Charge':
                                    print(
                                        'payment fee purchase_type Move-Out Charge ')
                            # payment fee frequency is move in %
                                elif payment['frequency'] == 'Move-in Charge':
                                    print(
                                        'payment fee purchase_type EXTRA CHARGES')
                                    charge_date = start_date.replace(
                                        day=1)
                                    charge_month = (charge_date).strftime('%B')
                                    # available date-> when the payment is available to pay
                                    if len(payment['available_topay']) == 0:
                                        available_date = charge_date
                                    else:
                                        available_date = charge_date - \
                                            timedelta(
                                                days=int(payment['available_topay']))
                                    charge = int(payment['charge'])
                                    purchaseResponse = newPurchase(
                                        linked_bill_id=None,
                                        pur_property_id=json.dumps(
                                            [res['result'][0]['rental_property_id']]),
                                        payer=json.dumps(tenants),
                                        receiver=res['result'][0]['linked_business_id'],
                                        purchase_type='EXTRA CHARGES',
                                        description=payment['fee_name'],
                                        amount_due=(charge * int(rent))/100,
                                        purchase_notes=charge_month,
                                        purchase_date=available_date,
                                        purchase_frequency=payment['frequency'],
                                        next_payment=charge_date
                                    )  # manager payments weekly $ rent
                                    for mpayment in managementPayments:
                                        weeks_current_month = len(
                                            calendar.monthcalendar(charge_date.year, int(charge_date.strftime("%m"))))
                                        print('mpayment fee type %')
                                        if mpayment['frequency'] == 'Weekly' and mpayment['fee_type'] == '%':
                                            if mpayment['of'] == 'Gross Rent':

                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [res['result'][0]['property_uid']]),
                                                    payer=json.dumps(
                                                        [res['result'][0]['business_uid']]),
                                                    receiver=res['result'][0]['owner_id'],
                                                    purchase_type='OWNER PAYMENT',
                                                    description=payment['fee_name'],
                                                    amount_due=weeks_current_month*(charge *
                                                                                    (1-mpayment['charge']/100)),
                                                    purchase_notes=charge_month,
                                                    purchase_date=available_date,
                                                    purchase_frequency=mpayment['frequency'],
                                                    next_payment=charge_date
                                                )
                                            # if net rent (listed rent-expenses)
                                            else:

                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [res['result'][0]['property_uid']]),
                                                    payer=json.dumps(
                                                        [res['result'][0]['business_uid']]),
                                                    receiver=res['result'][0]['owner_id'],
                                                    purchase_type='OWNER PAYMENT',
                                                    description=payment['fee_name'],
                                                    amount_due=weeks_current_month*((charge-mpayment['expense_amount'])*(
                                                        1-mpayment['charge']/100)),
                                                    purchase_notes=charge_month,
                                                    purchase_date=available_date,
                                                    purchase_frequency=mpayment['frequency'],
                                                    next_payment=charge_date
                                                )
                                        elif mpayment['frequency'] == 'Biweekly' and mpayment['fee_type'] == '%':

                                            # if gross rent (listed rent)
                                            if mpayment['of'] == 'Gross Rent':

                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [res['result'][0]['property_uid']]),
                                                    payer=json.dumps(
                                                        [res['result'][0]['business_uid']]),
                                                    receiver=res['result'][0]['owner_id'],
                                                    purchase_type='OWNER PAYMENT',
                                                    description=payment['fee_name'],
                                                    amount_due=(weeks_current_month/2) *
                                                    ((charge *
                                                        (1-mpayment['charge']/100)))/weeks_current_month/2,
                                                    purchase_notes=charge_month,
                                                    purchase_date=available_date,
                                                    purchase_frequency=mpayment['frequency'],
                                                    next_payment=charge_date
                                                )
                                            # if net rent (listed rent-expenses)
                                            else:

                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [res['result'][0]['property_uid']]),
                                                    payer=json.dumps(
                                                        [res['result'][0]['business_uid']]),
                                                    receiver=res['result'][0]['owner_id'],
                                                    purchase_type='OWNER PAYMENT',
                                                    description=payment['fee_name'],
                                                    amount_due=(weeks_current_month/2) *
                                                    ((charge-mpayment['expense_amount'])*(
                                                        1-mpayment['charge']/100))/weeks_current_month/2,
                                                    purchase_notes=charge_month,
                                                    purchase_date=available_date,
                                                    purchase_frequency=mpayment['frequency'],
                                                    next_payment=charge_date
                                                )

                                        elif mpayment['frequency'] == 'Monthly' and mpayment['fee_type'] == '%':

                                            # if gross rent (listed rent)
                                            if mpayment['of'] == 'Gross Rent':
                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [res['result'][0]['property_uid']]),
                                                    payer=json.dumps(
                                                        [res['result'][0]['business_uid']]),
                                                    receiver=res['result'][0]['owner_id'],
                                                    purchase_type='OWNER PAYMENT',
                                                    description=payment['fee_name'],
                                                    amount_due=(
                                                        charge*(1-int(mpayment['charge'])/100)),
                                                    purchase_notes=charge_month,
                                                    purchase_date=available_date,
                                                    purchase_frequency=mpayment['frequency'],
                                                    next_payment=charge_date
                                                )
                                                print(
                                                    purchaseResponse)

                                            # if net rent (listed rent-expenses)
                                            else:
                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [res['result'][0]['property_uid']]),
                                                    payer=json.dumps(
                                                        [res['result'][0]['business_uid']]),
                                                    receiver=res['result'][0]['owner_id'],
                                                    purchase_type='OWNER PAYMENT',
                                                    description=payment['fee_name'],
                                                    amount_due=(
                                                        (charge-mpayment['expense_amount'])*(1-int(mpayment['charge'])/100)),
                                                    purchase_notes=charge_month,
                                                    purchase_date=available_date,
                                                    purchase_frequency=mpayment['frequency'],
                                                    next_payment=charge_date
                                                )
                                                print(
                                                    purchaseResponse)
                                        elif mpayment['frequency'] == 'Move-in Charge' and mpayment['fee_type'] == '%':

                                            # if gross rent (listed rent)
                                            if mpayment['of'] == 'Gross Rent':
                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [res['result'][0]['property_uid']]),
                                                    payer=json.dumps(
                                                        [res['result'][0]['business_uid']]),
                                                    receiver=res['result'][0]['owner_id'],
                                                    purchase_type='OWNER PAYMENT',
                                                    description=payment['fee_name'],
                                                    amount_due=(
                                                        charge*(1-int(mpayment['charge'])/100)),
                                                    purchase_notes=charge_month,
                                                    purchase_date=available_date,
                                                    purchase_frequency=mpayment['frequency'],
                                                    next_payment=charge_date
                                                )
                                                print(
                                                    purchaseResponse)

                                            # if net rent (listed rent-expenses)
                                            else:
                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [res['result'][0]['property_uid']]),
                                                    payer=json.dumps(
                                                        [res['result'][0]['business_uid']]),
                                                    receiver=res['result'][0]['owner_id'],
                                                    purchase_type='OWNER PAYMENT',
                                                    description=payment['fee_name'],
                                                    amount_due=(
                                                        (charge-mpayment['expense_amount'])*(1-int(mpayment['charge'])/100)),
                                                    purchase_notes=charge_month,
                                                    purchase_date=available_date,
                                                    purchase_frequency=mpayment['frequency'],
                                                    next_payment=charge_date
                                                )
                                                print(
                                                    purchaseResponse)
                                        elif mpayment['frequency'] == 'Move-in Charge' and mpayment['fee_type'] == '$':
                                            # if gross rent (listed rent)
                                            if mpayment['of'] == 'Gross Rent':
                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [res['result'][0]['property_uid']]),
                                                    payer=json.dumps(
                                                        [res['result'][0]['business_uid']]),
                                                    receiver=res['result'][0]['owner_id'],
                                                    purchase_type='OWNER PAYMENT',
                                                    description=payment['fee_name'],
                                                    amount_due=int(
                                                        mpayment['charge']),
                                                    purchase_notes=charge_month,
                                                    purchase_date=available_date,
                                                    purchase_frequency=mpayment['frequency'],
                                                    next_payment=charge_date
                                                )
                                                print(
                                                    purchaseResponse)
                                        else:
                                            print(
                                                'payment frequency one-time %')

                            # payment fee purchase type Extra Charges %
                                else:
                                    print(
                                        'payment fee purchase_type EXTRA CHARGES')
                                    rent = int(res['result'][0]['listed_rent'])
                                    if payment['frequency'] == 'Weekly':
                                        print('payment frequency weekly %')
                                        # charge_date = next_weekday(
                                        #     start_date, int(payment['due_by']))
                                        charge_date = date_for_weekday(
                                            int(payment['due_by']), start_date)
                                        charge_month = charge_date.strftime(
                                            '%B')
                                        # available date-> when the payment is available to pay
                                        if len(payment['available_topay']) == 0:
                                            available_date = charge_date
                                        else:
                                            available_date = charge_date - \
                                                timedelta(
                                                    days=int(payment['available_topay']))

                                        while available_date < today and charge_date < end_date:
                                            charge_month = charge_date.strftime(
                                                '%B')
                                            if charge_month == start_date.strftime('%B') and (charge_date-start_date).days < 7:
                                                daily_charge = int(
                                                    int(
                                                        payment['charge'] * int(rent))/100 / 7)
                                                print('daily_charge',
                                                      daily_charge)
                                                num_days_active = 7 - start_date.weekday()
                                                print('num_days_active',
                                                      num_days_active)
                                                charge = round(
                                                    num_days_active * daily_charge, 2)
                                                print('charge', charge)
                                            else:
                                                charge = int(
                                                    payment['charge'] * int(rent))/100
                                            purchaseResponse = newPurchase(
                                                linked_bill_id=None,
                                                pur_property_id=json.dumps(
                                                    [res['result'][0]['rental_property_id']]),
                                                payer=json.dumps(tenants),
                                                receiver=res['result'][0]['linked_business_id'],
                                                purchase_type='EXTRA CHARGES',
                                                description=charge_month + ' ' +
                                                payment['fee_name'],
                                                # amount_due=prorated_charge,
                                                amount_due=charge,
                                                purchase_notes=charge_month,
                                                purchase_date=available_date,
                                                purchase_frequency=payment['frequency'],
                                                next_payment=charge_date
                                            )  # manager payments weekly $ rent
                                            for mpayment in managementPayments:
                                                weeks_current_month = len(
                                                    calendar.monthcalendar(charge_date.year, int(charge_date.strftime("%m"))))
                                                print('mpayment fee type %')
                                                if mpayment['frequency'] == 'Weekly' and mpayment['fee_type'] == '%':
                                                    if mpayment['of'] == 'Gross Rent':

                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=weeks_current_month*(charge *
                                                                                            (1-mpayment['charge']/100)),
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                    # if net rent (listed rent-expenses)
                                                    else:

                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=weeks_current_month*((charge-mpayment['expense_amount'])*(
                                                                1-mpayment['charge']/100)),
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                elif mpayment['frequency'] == 'Biweekly' and mpayment['fee_type'] == '%':

                                                    # if gross rent (listed rent)
                                                    if mpayment['of'] == 'Gross Rent':

                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=(weeks_current_month/2) *
                                                            ((charge *
                                                                (1-mpayment['charge']/100)))/weeks_current_month/2,
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                    # if net rent (listed rent-expenses)
                                                    else:

                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=(weeks_current_month/2) *
                                                            ((charge-mpayment['expense_amount'])*(
                                                                1-mpayment['charge']/100))/weeks_current_month/2,
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )

                                                elif mpayment['frequency'] == 'Monthly' and mpayment['fee_type'] == '%':

                                                    # if gross rent (listed rent)
                                                    if mpayment['of'] == 'Gross Rent':
                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=(
                                                                charge*(1-int(mpayment['charge'])/100)),
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                        print(
                                                            purchaseResponse)

                                                    # if net rent (listed rent-expenses)
                                                    else:
                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=(
                                                                (charge-mpayment['expense_amount'])*(1-int(mpayment['charge'])/100)),
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                        print(
                                                            purchaseResponse)

                                                else:
                                                    print(
                                                        'payment frequency one-time %')

                                            charge_date += relativedelta(
                                                weeks=1)
                                            available_date += relativedelta(
                                                weeks=1)
                                    elif payment['frequency'] == 'Biweekly':
                                        print('payment frequency biweekly %')
                                        # charge_date = next_weekday_biweekly(
                                        #     start_date, int(payment['due_by']))
                                        charge_date = date_for_weekday(
                                            int(payment['due_by']), start_date)
                                        charge_month = charge_date.strftime(
                                            '%B')
                                        # available date-> when the payment is available to pay
                                        if len(payment['available_topay']) == 0:
                                            available_date = charge_date
                                        else:
                                            available_date = charge_date - \
                                                timedelta(
                                                    days=int(payment['available_topay']))

                                        while available_date < (today + relativedelta(
                                                weeks=2)) and charge_date < end_date:
                                            charge_month = charge_date.strftime(
                                                '%B')
                                            charge = int(
                                                payment['charge'] * int(rent))/100,
                                            purchaseResponse = newPurchase(
                                                linked_bill_id=None,
                                                pur_property_id=json.dumps(
                                                    [res['result'][0]['rental_property_id']]),
                                                payer=json.dumps(tenants),
                                                receiver=res['result'][0]['linked_business_id'],
                                                purchase_type='EXTRA CHARGES',
                                                description=charge_month + ' ' +
                                                payment['fee_name'],
                                                # amount_due=prorated_charge,
                                                amount_due=charge,
                                                purchase_notes=charge_month,
                                                purchase_date=available_date,
                                                purchase_frequency=payment['frequency'],
                                                next_payment=charge_date
                                            )  # manager payments biweekly $ rent
                                            for mpayment in managementPayments:
                                                weeks_current_month = len(
                                                    calendar.monthcalendar(charge_date.year, int(charge_date.strftime("%m"))))
                                                print('mpayment fee type %')
                                                if mpayment['frequency'] == 'Weekly' and mpayment['fee_type'] == '%':
                                                    if mpayment['of'] == 'Gross Rent':

                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=weeks_current_month*(charge *
                                                                                            (1-mpayment['charge']/100)),
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                    # if net rent (listed rent-expenses)
                                                    else:

                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=weeks_current_month*((charge-mpayment['expense_amount'])*(
                                                                1-mpayment['charge']/100)),
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                elif mpayment['frequency'] == 'Biweekly' and mpayment['fee_type'] == '%':

                                                    # if gross rent (listed rent)
                                                    if mpayment['of'] == 'Gross Rent':

                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=(weeks_current_month/2) *
                                                            ((charge *
                                                                (1-mpayment['charge']/100)))/weeks_current_month/2,
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                    # if net rent (listed rent-expenses)
                                                    else:

                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=(weeks_current_month/2) *
                                                            ((charge-mpayment['expense_amount'])*(
                                                                1-mpayment['charge']/100))/weeks_current_month/2,
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )

                                                elif mpayment['frequency'] == 'Monthly' and mpayment['fee_type'] == '%':

                                                    # if gross rent (listed rent)
                                                    if mpayment['of'] == 'Gross Rent':
                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=(
                                                                charge*(1-int(mpayment['charge'])/100)),
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                        print(
                                                            purchaseResponse)

                                                    # if net rent (listed rent-expenses)
                                                    else:
                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=(
                                                                (charge-mpayment['expense_amount'])*(1-int(mpayment['charge'])/100)),
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                        print(
                                                            purchaseResponse)

                                                else:
                                                    print(
                                                        'payment frequency one-time %')

                                            charge_date += relativedelta(
                                                weeks=2)
                                            available_date += relativedelta(
                                                weeks=2)
                                    elif payment['frequency'] == 'Monthly':
                                        print('payment frequency monthly %')
                                        charge_date = (start_date.replace(
                                            day=int(payment['due_by'])))
                                        charge_month = charge_date.strftime(
                                            '%B')
                                        # available date-> when the payment is available to pay
                                        if len(payment['available_topay']) == 0:
                                            available_date = charge_date
                                        else:
                                            available_date = charge_date - \
                                                timedelta(
                                                    days=int(payment['available_topay']))

                                        while available_date < today and charge_date < end_date:
                                            charge_month = charge_date.strftime(
                                                '%B')

                                            if charge_month == start_date.strftime(
                                                    '%B') and start_date.strftime('%d') != '01':
                                                # prorate first month
                                                print('days_in_month(charge_date)', days_in_month(
                                                    charge_date))
                                                daily_charge_begin = int(
                                                    (
                                                        int(payment['charge']) * int(rent))/100 / days_in_month(charge_date))
                                                num_days_active_begin = days_in_month(
                                                    charge_date) - start_date.day + 1
                                                charge = round(
                                                    num_days_active_begin * daily_charge_begin, 2)

                                            else:
                                                charge = (
                                                    int(payment['charge']) * int(rent))/100
                                            purchaseResponse = newPurchase(
                                                linked_bill_id=None,
                                                pur_property_id=json.dumps(
                                                    [res['result'][0]['rental_property_id']]),
                                                payer=json.dumps(tenants),
                                                receiver=res['result'][0]['linked_business_id'],
                                                purchase_type='EXTRA CHARGES',
                                                description=charge_month + ' ' +
                                                payment['fee_name'],
                                                amount_due=charge,
                                                purchase_notes=charge_month,
                                                purchase_date=available_date,
                                                purchase_frequency=payment['frequency'],
                                                next_payment=charge_date
                                            )  # manager payments weekly $ rent
                                            for mpayment in managementPayments:
                                                weeks_current_month = len(
                                                    calendar.monthcalendar(charge_date.year, int(charge_date.strftime("%m"))))
                                                print('mpayment fee type %')
                                                if mpayment['frequency'] == 'Weekly' and mpayment['fee_type'] == '%':
                                                    if mpayment['of'] == 'Gross Rent':

                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=weeks_current_month*(charge *
                                                                                            (1-mpayment['charge']/100)),
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                    # if net rent (listed rent-expenses)
                                                    else:

                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=weeks_current_month*((charge-mpayment['expense_amount'])*(
                                                                1-mpayment['charge']/100)),
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                elif mpayment['frequency'] == 'Biweekly' and mpayment['fee_type'] == '%':

                                                    # if gross rent (listed rent)
                                                    if mpayment['of'] == 'Gross Rent':

                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=(weeks_current_month/2) *
                                                            ((charge *
                                                                (1-mpayment['charge']/100)))/weeks_current_month/2,
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                    # if net rent (listed rent-expenses)
                                                    else:

                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=(weeks_current_month/2) *
                                                            ((charge-mpayment['expense_amount'])*(
                                                                1-mpayment['charge']/100))/weeks_current_month/2,
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )

                                                elif mpayment['frequency'] == 'Monthly' and mpayment['fee_type'] == '%':

                                                    # if gross rent (listed rent)
                                                    if mpayment['of'] == 'Gross Rent':
                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=(
                                                                charge*(1-int(mpayment['charge'])/100)),
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                        print(
                                                            purchaseResponse)

                                                    # if net rent (listed rent-expenses)
                                                    else:
                                                        purchaseResponse = newPurchase(
                                                            linked_bill_id=None,
                                                            pur_property_id=json.dumps(
                                                                [res['result'][0]['property_uid']]),
                                                            payer=json.dumps(
                                                                [res['result'][0]['business_uid']]),
                                                            receiver=res['result'][0]['owner_id'],
                                                            purchase_type='OWNER PAYMENT',
                                                            description=charge_month + ' ' +
                                                            payment['fee_name'],
                                                            amount_due=(
                                                                (charge-mpayment['expense_amount'])*(1-int(mpayment['charge'])/100)),
                                                            purchase_notes=charge_month,
                                                            purchase_date=available_date,
                                                            purchase_frequency=mpayment['frequency'],
                                                            next_payment=charge_date
                                                        )
                                                        print(
                                                            purchaseResponse)

                                                else:
                                                    print(
                                                        'payment frequency one-time %')

                                            charge_date += relativedelta(
                                                months=1)
                                            available_date += relativedelta(
                                                months=1)
                                    elif payment['frequency'] == 'Annually':
                                        print('payment frequency annually %')
                                        charge_date = (start_date.replace(
                                            day=int(payment['due_by'])))
                                        charge_month = charge_date.strftime(
                                            '%B')
                                        # available date-> when the payment is available to pay
                                        if len(payment['available_topay']) == 0:
                                            available_date = charge_date
                                        else:
                                            available_date = charge_date - \
                                                timedelta(
                                                    days=int(payment['available_topay']))
                                        charge = (
                                            int(payment['charge']) * int(rent))/100
                                        purchaseResponse = newPurchase(
                                            linked_bill_id=None,
                                            pur_property_id=json.dumps(
                                                [res['result'][0]['rental_property_id']]),
                                            payer=json.dumps(tenants),
                                            receiver=res['result'][0]['linked_business_id'],
                                            purchase_type='EXTRA CHARGES',
                                            description=payment['fee_name'] + ' ' + charge_date.strftime(
                                                '%Y'),
                                            amount_due=charge,
                                            purchase_notes=charge_month,
                                            purchase_date=available_date,
                                            purchase_frequency=payment['frequency'],
                                            next_payment=charge_date
                                        )  # manager payments weekly $ rent
                                        for mpayment in managementPayments:
                                            weeks_current_month = len(
                                                calendar.monthcalendar(charge_date.year, int(charge_date.strftime("%m"))))
                                            print('mpayment fee type %')
                                            if mpayment['frequency'] == 'Weekly' and mpayment['fee_type'] == '%':
                                                if mpayment['of'] == 'Gross Rent':

                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [res['result'][0]['property_uid']]),
                                                        payer=json.dumps(
                                                            [res['result'][0]['business_uid']]),
                                                        receiver=res['result'][0]['owner_id'],
                                                        purchase_type='OWNER PAYMENT',
                                                        description=payment['fee_name'] + ' ' + charge_date.strftime(
                                                            '%Y'),
                                                        amount_due=weeks_current_month*(charge *
                                                                                        (1-mpayment['charge']/100)),
                                                        purchase_notes=charge_month,
                                                        purchase_date=available_date,
                                                        purchase_frequency=mpayment['frequency'],
                                                        next_payment=charge_date
                                                    )
                                                # if net rent (listed rent-expenses)
                                                else:

                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [res['result'][0]['property_uid']]),
                                                        payer=json.dumps(
                                                            [res['result'][0]['business_uid']]),
                                                        receiver=res['result'][0]['owner_id'],
                                                        purchase_type='OWNER PAYMENT',
                                                        description=payment['fee_name'] + ' ' + charge_date.strftime(
                                                            '%Y'),
                                                        amount_due=weeks_current_month*((charge-mpayment['expense_amount'])*(
                                                            1-mpayment['charge']/100)),
                                                        purchase_notes=charge_month,
                                                        purchase_date=available_date,
                                                        purchase_frequency=mpayment['frequency'],
                                                        next_payment=charge_date
                                                    )
                                            elif mpayment['frequency'] == 'Biweekly' and mpayment['fee_type'] == '%':

                                                # if gross rent (listed rent)
                                                if mpayment['of'] == 'Gross Rent':

                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [res['result'][0]['property_uid']]),
                                                        payer=json.dumps(
                                                            [res['result'][0]['business_uid']]),
                                                        receiver=res['result'][0]['owner_id'],
                                                        purchase_type='OWNER PAYMENT',
                                                        description=payment['fee_name'] + ' ' + charge_date.strftime(
                                                            '%Y'),
                                                        amount_due=(weeks_current_month/2) *
                                                        ((charge *
                                                            (1-mpayment['charge']/100)))/weeks_current_month/2,
                                                        purchase_notes=charge_month,
                                                        purchase_date=available_date,
                                                        purchase_frequency=mpayment['frequency'],
                                                        next_payment=charge_date
                                                    )
                                                # if net rent (listed rent-expenses)
                                                else:

                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [res['result'][0]['property_uid']]),
                                                        payer=json.dumps(
                                                            [res['result'][0]['business_uid']]),
                                                        receiver=res['result'][0]['owner_id'],
                                                        purchase_type='OWNER PAYMENT',
                                                        description=payment['fee_name'] + ' ' + charge_date.strftime(
                                                            '%Y'),
                                                        amount_due=(weeks_current_month/2) *
                                                        ((charge-mpayment['expense_amount'])*(
                                                            1-mpayment['charge']/100))/weeks_current_month/2,
                                                        purchase_notes=charge_month,
                                                        purchase_date=available_date,
                                                        purchase_frequency=mpayment['frequency'],
                                                        next_payment=charge_date
                                                    )

                                            elif mpayment['frequency'] == 'Monthly' and mpayment['fee_type'] == '%':

                                                # if gross rent (listed rent)
                                                if mpayment['of'] == 'Gross Rent':
                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [res['result'][0]['property_uid']]),
                                                        payer=json.dumps(
                                                            [res['result'][0]['business_uid']]),
                                                        receiver=res['result'][0]['owner_id'],
                                                        purchase_type='OWNER PAYMENT',
                                                        description=payment['fee_name'] + ' ' + charge_date.strftime(
                                                            '%Y'),
                                                        amount_due=(
                                                            charge*(1-int(mpayment['charge'])/100)),
                                                        purchase_notes=charge_month,
                                                        purchase_date=available_date,
                                                        purchase_frequency=mpayment['frequency'],
                                                        next_payment=charge_date
                                                    )
                                                    print(
                                                        purchaseResponse)

                                                # if net rent (listed rent-expenses)
                                                else:
                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [res['result'][0]['property_uid']]),
                                                        payer=json.dumps(
                                                            [res['result'][0]['business_uid']]),
                                                        receiver=res['result'][0]['owner_id'],
                                                        purchase_type='OWNER PAYMENT',
                                                        description=payment['fee_name'] + ' ' + charge_date.strftime(
                                                            '%Y'),
                                                        amount_due=(
                                                            (charge-mpayment['expense_amount'])*(1-int(mpayment['charge'])/100)),
                                                        purchase_notes=charge_month,
                                                        purchase_date=available_date,
                                                        purchase_frequency=mpayment['frequency'],
                                                        next_payment=charge_date
                                                    )
                                                    print(
                                                        purchaseResponse)

                                            else:
                                                print(
                                                    'payment frequency one-time %')
                                    else:
                                        print('payment frequency one-time %')
                                        charge_date = start_date.replace(
                                            day=1)
                                        charge_month = (
                                            charge_date).strftime('%B')
                                        # available date-> when the payment is available to pay
                                        if len(payment['available_topay']) == 0:
                                            available_date = charge_date
                                        else:
                                            available_date = charge_date - \
                                                timedelta(
                                                    days=int(payment['available_topay']))
                                        charge = (
                                            int(payment['charge']) * int(rent))/100
                                        purchaseResponse = newPurchase(
                                            linked_bill_id=None,
                                            pur_property_id=json.dumps(
                                                [res['result'][0]['rental_property_id']]),
                                            payer=json.dumps(tenants),
                                            receiver=res['result'][0]['linked_business_id'],
                                            purchase_type='EXTRA CHARGES',
                                            description=payment['fee_name'],
                                            amount_due=(
                                                int(payment['charge']) * int(rent))/100,
                                            purchase_notes=charge_month,
                                            purchase_date=available_date,
                                            purchase_frequency=payment['frequency'],
                                            next_payment=charge_date
                                        )  # manager payments weekly $ rent
                                        for mpayment in managementPayments:
                                            weeks_current_month = len(
                                                calendar.monthcalendar(charge_date.year, int(charge_date.strftime("%m"))))
                                            print('mpayment fee type %')
                                            if mpayment['frequency'] == 'Weekly' and mpayment['fee_type'] == '%':
                                                if mpayment['of'] == 'Gross Rent':

                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [res['result'][0]['property_uid']]),
                                                        payer=json.dumps(
                                                            [res['result'][0]['business_uid']]),
                                                        receiver=res['result'][0]['owner_id'],
                                                        purchase_type='OWNER PAYMENT',
                                                        description=payment['fee_name'],
                                                        amount_due=weeks_current_month*(charge *
                                                                                        (1-mpayment['charge']/100)),
                                                        purchase_notes=charge_month,
                                                        purchase_date=available_date,
                                                        purchase_frequency=mpayment['frequency'],
                                                        next_payment=charge_date
                                                    )
                                                # if net rent (listed rent-expenses)
                                                else:

                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [res['result'][0]['property_uid']]),
                                                        payer=json.dumps(
                                                            [res['result'][0]['business_uid']]),
                                                        receiver=res['result'][0]['owner_id'],
                                                        purchase_type='OWNER PAYMENT',
                                                        description=payment['fee_name'],
                                                        amount_due=weeks_current_month*((charge-mpayment['expense_amount'])*(
                                                            1-mpayment['charge']/100)),
                                                        purchase_notes=charge_month,
                                                        purchase_date=available_date,
                                                        purchase_frequency=mpayment['frequency'],
                                                        next_payment=charge_date
                                                    )
                                            elif mpayment['frequency'] == 'Biweekly' and mpayment['fee_type'] == '%':

                                                # if gross rent (listed rent)
                                                if mpayment['of'] == 'Gross Rent':

                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [res['result'][0]['property_uid']]),
                                                        payer=json.dumps(
                                                            [res['result'][0]['business_uid']]),
                                                        receiver=res['result'][0]['owner_id'],
                                                        purchase_type='OWNER PAYMENT',
                                                        description=payment['fee_name'],
                                                        amount_due=(weeks_current_month/2) *
                                                        ((charge *
                                                            (1-mpayment['charge']/100)))/weeks_current_month/2,
                                                        purchase_notes=charge_month,
                                                        purchase_date=available_date,
                                                        purchase_frequency=mpayment['frequency'],
                                                        next_payment=charge_date
                                                    )
                                                # if net rent (listed rent-expenses)
                                                else:

                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [res['result'][0]['property_uid']]),
                                                        payer=json.dumps(
                                                            [res['result'][0]['business_uid']]),
                                                        receiver=res['result'][0]['owner_id'],
                                                        purchase_type='OWNER PAYMENT',
                                                        description=payment['fee_name'],
                                                        amount_due=(weeks_current_month/2) *
                                                        ((charge-mpayment['expense_amount'])*(
                                                            1-mpayment['charge']/100))/weeks_current_month/2,
                                                        purchase_notes=charge_month,
                                                        purchase_date=available_date,
                                                        purchase_frequency=mpayment['frequency'],
                                                        next_payment=charge_date
                                                    )

                                            elif mpayment['frequency'] == 'Monthly' and mpayment['fee_type'] == '%':

                                                # if gross rent (listed rent)
                                                if mpayment['of'] == 'Gross Rent':
                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [res['result'][0]['property_uid']]),
                                                        payer=json.dumps(
                                                            [res['result'][0]['business_uid']]),
                                                        receiver=res['result'][0]['owner_id'],
                                                        purchase_type='OWNER PAYMENT',
                                                        description=payment['fee_name'],
                                                        amount_due=(
                                                            charge*(1-int(mpayment['charge'])/100)),
                                                        purchase_notes=charge_month,
                                                        purchase_date=available_date,
                                                        purchase_frequency=mpayment['frequency'],
                                                        next_payment=charge_date
                                                    )
                                                    print(
                                                        purchaseResponse)

                                                # if net rent (listed rent-expenses)
                                                else:
                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [res['result'][0]['property_uid']]),
                                                        payer=json.dumps(
                                                            [res['result'][0]['business_uid']]),
                                                        receiver=res['result'][0]['owner_id'],
                                                        purchase_type='OWNER PAYMENT',
                                                        description=payment['fee_name'],
                                                        amount_due=(
                                                            (charge-mpayment['expense_amount'])*(1-int(mpayment['charge'])/100)),
                                                        purchase_notes=charge_month,
                                                        purchase_date=available_date,
                                                        purchase_frequency=mpayment['frequency'],
                                                        next_payment=charge_date
                                                    )
                                                    print(
                                                        purchaseResponse)

                                            else:
                                                print(
                                                    'payment frequency one-time %')

                        pk1 = {
                            'rental_uid': res['result'][0]['rental_uid']}
                        newRental = {
                            'rental_status': 'ACTIVE'}
                        print('rental', pk1, newRental)
                        #  uncomment later
                        res = db.update(
                            'rentals', pk1, newRental)
                    resRej = db.execute(
                        """SELECT * FROM pm.applications WHERE application_status='NEW' AND property_uid = \'"""
                        + newApplication['property_uid']
                        + """\' """)
                    # print('resRej', resRej, len(resRej['result']))
                    if len(resRej['result']) > 0:

                        for resRej in resRej['result']:
                            pk = {
                                'application_uid': resRej['application_uid']
                            }
                            rejApplication = {
                                'application_status': 'REJECTED',
                                'property_uid': resRej['property_uid'], 'application_uid': resRej['application_uid']
                            }
                            # uncomment later
                            resRej = db.update(
                                'applications', pk, rejApplication)
            # tenant refuses lease aggreement
            elif newApplication['application_status'] == 'REFUSED':
                print('here tenant refused')
                response = db.execute(
                    """SELECT * FROM pm.applications WHERE application_status='FORWARDED' AND property_uid = \'"""
                    + newApplication['property_uid']
                    + """\' """)
                # print('response', response, len(response['result']))
                if len(response['result']) > 1:
                    newApplication['application_status'] = 'REFUSED'
                    response = db.execute(
                        """UPDATE pm.applications
                            SET
                            application_status=\'""" + newApplication['application_status'] + """\'
                            WHERE
                            application_status='FORWARDED' 
                            AND property_uid = \'""" + newApplication['property_uid'] + """\' """)

                    res = db.execute(
                        """SELECT * 
                        FROM pm.rentals
                        WHERE rental_status='PROCESSING' 
                        AND rental_property_id = \'""" + newApplication['property_uid'] + """\' 
                        AND linked_application_id LIKE '%""" + newApplication['application_uid'] + """%' """)
                    print('res', res, len(res['result']))
                    if len(res['result']) > 0:
                        for res in res['result']:
                            # print('res', res['rental_uid'])
                            pk1 = {
                                'rental_uid': res['rental_uid']}
                            newRental = {
                                'rental_status': 'REFUSED'}
                            res = db.update(
                                'rentals', pk1, newRental)
                else:
                    newApplication['application_status'] = 'REFUSED'
                    res = db.execute(
                        """SELECT * 
                        FROM pm.rentals
                        WHERE rental_status='PROCESSING' 
                        AND rental_property_id = \'""" + newApplication['property_uid'] + """\' 
                        AND linked_application_id LIKE '%""" + newApplication['application_uid'] + """%' """)
                    print('res', res, len(res['result']))
                    if len(res['result']) > 0:
                        for res in res['result']:
                            # print('res', res['rental_uid'])
                            pk1 = {
                                'rental_uid': res['rental_uid']}
                            newRental = {
                                'rental_status': 'REFUSED'}
                            res = db.update(
                                'rentals', pk1, newRental)

            #     recipient = 'zacharywolfflind@gmail.com'
            #     subject = 'Application Accepted'
            #     body = 'Your application for the apartment has been accepted'
            #     current_app.sendEmail(recipient, subject, body)
            primaryKey = {
                'application_uid': data.get('application_uid')
            }
            print('newAppl', newApplication, primaryKey)
            #  uncomment later
            response = db.update('applications', primaryKey, newApplication)
        return response


class EndEarly(Resource):
    def put(self):
        response = {}
        with connect() as db:
            data = request.json
            fields = ['message', 'application_status',
                      'property_uid', 'application_uid', 'early_end_date']
            updateApp = {}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    updateApp[field] = fieldValue
            # pm wants to end the lease early,
            # in case of multiple or single tenants application_status will get set to PM END EARLY
            # print(updateApp)
            if updateApp['application_status'] == 'PM END EARLY':
                print('end early pm')
                appRes = db.execute(
                    """SELECT *
                        FROM pm.applications a
                        LEFT JOIN pm.rentals r
                        ON r.rental_property_id = a.property_uid
                        WHERE a.application_status='RENTED'
                        AND a.property_uid = \'""" + updateApp['property_uid'] + """\'
                        AND r.rental_status = 'ACTIVE'; """)
                if len(appRes['result']) > 0:
                    for application in appRes['result']:
                        print(application)
                        updateA = {
                            'application_status': 'PM END EARLY',
                            'message': updateApp['message']
                        }
                        pk = {
                            'application_uid': application['application_uid']}
                        response = db.update('applications', pk, updateA)
                        print('updateApp', updateApp)
                        # updates early_end_date in Rentals
                        pkR = {
                            'rental_uid': application['rental_uid']}
                        updateRen = {
                            'early_end_date': updateApp['early_end_date'],
                        }
                        print(pkR, updateRen)
                        response = db.update('rentals', pkR, updateRen)
             # tenant wants to end the lease early,
            elif updateApp['application_status'] == 'TENANT END EARLY':
                print('end early tenant')
                appRes = db.execute(
                    """SELECT *
                        FROM pm.applications a
                        LEFT JOIN pm.rentals r
                        ON r.rental_property_id = a.property_uid
                        WHERE a.application_status='RENTED' 
                        AND a.property_uid = \'""" + updateApp['property_uid'] + """\'
                        AND r.rental_status = 'ACTIVE'; """)
                # in case of multiple tenants only given application_uid's application_status will get set to TENANT END REQUESTED, other stays RENTED
                if len(appRes['result']) > 1:
                    for application in appRes['result']:
                        if application['application_uid'] == updateApp['application_uid']:
                            updateA = {
                                'application_status': 'TENANT END REQUESTED',
                                'message': updateApp['message']
                            }
                            pk = {
                                'application_uid': application['application_uid']}
                            response = db.update('applications', pk, updateA)
                            print('updateApp', updateApp)
                            # updates early_end_date in Rentals
                            pkR = {
                                'rental_uid': application['rental_uid']}
                            updateRen = {
                                'early_end_date': updateApp['early_end_date'],
                            }
                            print(pkR, updateRen)
                            response = db.update('rentals', pkR, updateRen)
                # in case of multiple tenants or single tenant, both application_status will now be set to TENANT END EARLY
                else:
                    endRes = db.execute(
                        """SELECT * FROM pm.applications WHERE application_status='TENANT END REQUESTED' AND property_uid = \'"""
                        + updateApp['property_uid']
                        + """\' """)
                    print('response', endRes, len(endRes['result']))
                    if len(endRes['result']) > 0:
                        print('here')
                        for endR in endRes['result']:
                            updateA = {
                                'application_status': 'TENANT END EARLY',

                            }
                            pk = {
                                'application_uid': endR['application_uid']}
                            response = db.update('applications', pk, updateA)
                    for application in appRes['result']:
                        print(application)
                        updateA = {
                            'application_status': 'TENANT END EARLY',
                            'message': updateApp['message']
                        }
                        pk = {
                            'application_uid': application['application_uid']}
                        response = db.update('applications', pk, updateA)
                        print('updateApp', updateApp)
                        # updates early_end_date in Rentals
                        pkR = {
                            'rental_uid': application['rental_uid']}
                        updateRen = {
                            'early_end_date': updateApp['early_end_date'],
                        }
                        print(pkR, updateRen)
                        response = db.update('rentals', pkR, updateRen)
            # tenant approves to end the lease early
            elif updateApp['application_status'] == 'TENANT ENDED':
                response = db.execute(
                    """SELECT * FROM pm.applications WHERE application_status='PM END EARLY' AND property_uid = \'"""
                    + updateApp['property_uid']
                    + """\' """)
                print('response', response, len(response['result']))
                # in case of multiple tenants, set the one to END ACCEPTED and wait for the other to respond
                if len(response['result']) > 1:
                    updateApp['application_status'] = 'END ACCEPTED'
                    pk = {
                        'application_uid': updateApp['application_uid']}
                    response = db.update('applications', pk, updateApp)
                # in case of no multiple tenants, this will set as ENDED, or n case of multiple tenants, both will get set as ENDED
                else:
                    multiEndRes = db.execute(
                        """SELECT * FROM pm.applications WHERE application_status='END ACCEPTED' AND property_uid = \'"""
                        + updateApp['property_uid']
                        + """\' """)
                    print('multiEndRes', multiEndRes['result'])
                    # multiple tenants set ENDED from END ACCEPTED
                    if len(multiEndRes['result']) > 0:
                        updateApp['application_status'] = 'ENDED EARLY'
                        for multiEndRes in multiEndRes['result']:
                            pk = {
                                'application_uid': multiEndRes['application_uid']
                            }
                            multiEnd = db.update('applications', pk, updateApp)
                    # set the other to ENDED
                    pmEndRes = db.execute("""
                    SELECT * FROM pm.applications
                    WHERE application_status ='PM END EARLY' AND property_uid = \'""" + updateApp['property_uid'] + """\' """)
                    print(pmEndRes)
                    if len(pmEndRes['result']) > 0:
                        updateApp['application_status'] = 'ENDED EARLY'
                        pk = {
                            'application_uid': pmEndRes['result'][0]['application_uid']
                        }
                        response = db.update('applications', pk, updateApp)
                    # rental_status gets set to TERMINATED and lease_end updated to early_end_date
                    res = db.execute("""
                    SELECT r.*,
                    GROUP_CONCAT(lt.linked_tenant_id) as `tenants`
                    FROM pm.rentals r
                    LEFT JOIN pm.leaseTenants lt
                    ON lt.linked_rental_uid = r.rental_uid
                    WHERE r.rental_status='ACTIVE'
                    AND r.rental_property_id = \'""" + updateApp['property_uid'] + """\'
                    GROUP BY lt.linked_rental_uid; """)
                    pk1 = {
                        'rental_uid': res['result'][0]['rental_uid']}
                    newRental = {
                        'rental_status': 'TERMINATED',
                        'lease_end':  res['result'][0]['early_end_date']}
                    res = db.update(
                        'rentals', pk1, newRental)
                    # deletes any future rent payments or charges for that property
                    pur_pk = {
                        'pur_property_id': json.dumps([updateApp['property_uid']])
                    }
                    pur_response = db.delete("""DELETE FROM pm.purchases WHERE pur_property_id LIKE '%""" + updateApp['property_uid'] + """%'
                                                    AND (MONTH(purchase_date) > MONTH(now()) AND YEAR(purchase_date) = YEAR(now()) OR YEAR(purchase_date) > YEAR(now()))
                                                    AND purchase_status ="UNPAID"
                                                    AND (purchase_type= "RENT" OR purchase_type= "EXTRA CHARGES")""")
            # if PM approves the lease ending
            elif updateApp['application_status'] == 'PM ENDED':
                # the application_status gets sets to ENDED and rental_status gets set to TERMINATED
                pmEndRes = db.execute(
                    """SELECT * FROM pm.applications WHERE application_status ='TENANT END EARLY' AND property_uid = \'"""
                    + updateApp['property_uid']
                    + """\' """)
                print(pmEndRes)
                if len(pmEndRes['result']) > 0:
                    for endRes in pmEndRes['result']:
                        pk = {
                            'application_uid': endRes['application_uid']
                        }
                        updateApp['application_status'] = 'ENDED EARLY'
                        response = db.update('applications', pk, updateApp)

                res = db.execute("""SELECT
                                        r.*,
                                        GROUP_CONCAT(lt.linked_tenant_id) as `tenants`
                                        FROM pm.rentals r
                                        LEFT JOIN pm.leaseTenants lt
                                        ON lt.linked_rental_uid = r.rental_uid
                                        WHERE r.rental_status='ACTIVE'
                                        AND r.rental_property_id = \'""" + updateApp['property_uid'] + """\'
                                        GROUP BY lt.linked_rental_uid; """)
                # rental_status gets set to TERMINATED and lease_end updated to early_end_date
                pk1 = {
                    'rental_uid': res['result'][0]['rental_uid']}
                newRental = {
                    'rental_status': 'TERMINATED',
                    'lease_end':  res['result'][0]['early_end_date']}
                res = db.update(
                    'rentals', pk1, newRental)

                # deletes any future rent payments or charges for that property
                pur_pk = {
                    'pur_property_id': json.dumps([updateApp['property_uid']])
                }
                pur_response = db.delete("""DELETE FROM pm.purchases WHERE pur_property_id LIKE '%""" + updateApp['property_uid'] + """%'
                                                AND (MONTH(purchase_date) > MONTH(now()) AND YEAR(purchase_date) = YEAR(now()) OR YEAR(purchase_date) > YEAR(now()))
                                                AND purchase_status ="UNPAID"
                                                AND (purchase_type= "RENT" OR purchase_type= "EXTRA CHARGES")""")
            else:
                print('refused')
                # if pm refuses to end the lease early, application_status set back to RENTED, clear early end date, srt message back to previous
                refResPM = db.execute("""
                SELECT * FROM pm.applications 
                WHERE (application_status ='TENANT END EARLY' OR application_status ='TENANT END REQUESTED')
                AND property_uid = \'""" + updateApp['property_uid'] + """\' """)
                if len(refResPM['result']) > 0:
                    for refRes in refResPM['result']:
                        pk = {
                            'application_uid': refRes['application_uid']
                        }
                        updateRefRes = {
                            'application_status': 'RENTED',
                            'message': 'Lease details forwarded for review'
                        }
                        response = db.update('applications', pk, updateRefRes)
                rentalPM = db.execute("""
                SELECT * FROM pm.rentals 
                WHERE rental_status = 'ACTIVE'
                AND rental_property_id = \'""" + updateApp['property_uid'] + """\' """)
                if len(rentalPM['result']) > 0:
                    for rental in rentalPM['result']:
                        pk = {
                            'rental_uid': rental['rental_uid']
                        }
                        updateRental = {
                            'early_end_date': 'Lease details forwarded for review'
                        }
                        response = db.update('rentals', pk, updateRental)
                # if tenant refuses to end the lease early, application_status set back to RENTED, clear early end date, srt message back to previous
                refResTenant = db.execute("""
                SELECT *  FROM pm.applications 
                WHERE (application_status ='PM END EARLY' OR application_status ='END ACCEPTED')
                AND property_uid = \'""" + updateApp['property_uid'] + """\' """)
                print('refrestenant', refResTenant['result'])
                if len(refResTenant['result']) > 0:
                    for refRes in refResTenant['result']:
                        pk = {
                            'application_uid': refRes['application_uid']
                        }
                        updateRefRes = {
                            'application_status': 'RENTED',
                            'message': 'Lease details forwarded for review'
                        }
                        response = db.update('applications', pk, updateRefRes)
                rentalTenant = db.execute("""
                SELECT * FROM pm.rentals 
                WHERE rental_status = 'ACTIVE'
                AND rental_property_id = \'""" + updateApp['property_uid'] + """\' """)
                if len(rentalTenant['result']) > 0:
                    for rental in rentalTenant['result']:
                        pk = {
                            'rental_uid': rental['rental_uid']
                        }
                        updateRental = {
                            'early_end_date': ''
                        }
                        response = db.update('rentals', pk, updateRental)

        return response


class TenantRentalEnd_CLASS(Resource):
    def get(self):
        with connect() as db:
            response = db.execute("""SELECT *
                                    FROM pm.rentals r
                                    LEFT JOIN
                                    pm.applications a
                                    ON a.property_uid = r.rental_property_id
                                    WHERE r.rental_status='ACTIVE'
                                    AND r.lease_end = DATE_FORMAT(NOW(), "%Y-%m-%d")
                                    AND (a.application_status= 'RENTED' OR a.application_status= 'END EARLY'); """)
            print(response['result'], len(response['result']))
            if len(response['result']) > 0:
                for i in range(len(response['result'])):
                    applicationUpdate = {
                        'application_status': 'ENDED',
                    }
                    applicationPK = {
                        'application_uid': response['result'][i]['application_uid']
                    }
                    applicationresponse = db.update(
                        'applications', applicationPK, applicationUpdate)
                    if response['result'][i]['application_status'] == 'END EARLY':

                        rentalsUpdate = {
                            'rental_status': 'TERMINATED'
                        }
                        rentalsPK = {
                            'rental_uid': response['result'][i]['rental_uid']
                        }
                        rentalsresponse = db.update(
                            'rentals', rentalsPK, rentalsUpdate)
                    else:
                        rentalsUpdate = {
                            'rental_status': 'EXPIRED'
                        }
                        rentalsPK = {
                            'rental_uid': response['result'][i]['rental_uid']
                        }
                        rentalsresponse = db.update(
                            'rentals', rentalsPK, rentalsUpdate)
        return rentalsresponse


def TenantRentalEnd_CRON():

    print('In TenantRentalEnd_CRON')
    with connect() as db:

        print("In Manager Contract End CRON Function")
        response = db.execute("""SELECT *
                                FROM pm.contracts c
                                LEFT JOIN
                                pm.propertyManager p
                                ON p.linked_property_id = c.property_uid
                                WHERE c.contract_status='ACTIVE'
                                AND c.end_date = DATE_FORMAT(NOW(), "%Y-%m-%d")
                                AND p.management_status= 'ACCEPTED' OR p.management_status='END EARLY'; """)
        print(response['result'], len(response['result']))
        if len(response['result']) > 0:
            for i in range(len(response['result'])):
                contractUpdate = {
                    'contract_status': 'INACTIVE',
                }
                contractPK = {
                    'contract_uid': response['result'][i]['contract_uid']
                }
                contractresponse = db.update(
                    'contracts', contractPK, contractUpdate)
                if response['result'][i]['management_status'] == 'END EARLY':

                    propertyManagerUpdate = {
                        'management_status': 'TERMINATED'
                    }
                    propertyManagerPK = {
                        'linked_property_id': response['result'][i]['property_uid'],
                        'linked_business_id': response['result'][i]['linked_business_id']
                    }
                    propertyManagerresponse = db.update(
                        'propertyManager', propertyManagerPK, propertyManagerUpdate)
                else:
                    propertyManagerUpdate = {
                        'management_status': 'EXPIRED'
                    }
                    propertyManagerPK = {
                        'linked_property_id': response['result'][i]['property_uid'],
                        'linked_business_id': response['result'][i]['linked_business_id']
                    }
                    propertyManagerresponse = db.update(
                        'propertyManager', propertyManagerPK, propertyManagerUpdate)
    return propertyManagerresponse
