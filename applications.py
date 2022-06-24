import resource
from flask import request, current_app
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from data import connect
import json

from text_to_num import alpha2digit
from purchases import newPurchase
from datetime import date, timedelta, datetime
from calendar import monthrange
from dateutil.relativedelta import relativedelta


def days_in_month(dt): return monthrange(
    dt.year, dt.month)[1]


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


class Applications(Resource):
    decorators = [jwt_required(optional=True)]

    def get(self):
        response = {}
        filters = ['application_uid', 'property_uid', 'tenant_id']
        where = {}
        for filter in filters:
            filterValue = request.args.get(filter)
            if filterValue is not None:
                where[f'a.{filter}'] = filterValue
        with connect() as db:
            sql = 'SELECT  FROM applications a LEFT JOIN tenantProfileInfo t ON a.tenant_id = t.tenant_id LEFT JOIN properties p ON a.property_uid = p.property_uid LEFT JOIN rentals r ON a.property_uid = r.rental_property_id'
            cols = 'application_uid, message, application_status, t.*, p.*, r.*'
            tables = 'applications a LEFT JOIN tenantProfileInfo t ON a.tenant_id = t.tenant_id LEFT JOIN properties p ON a.property_uid = p.property_uid LEFT JOIN rentals r ON a.property_uid = r.rental_property_id'
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
                      'adult_occupants', 'children_occupants']
            newApplication = {}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    newApplication[field] = fieldValue
            newApplicationID = db.call('new_application_id')[
                'result'][0]['new_id']
            newApplication['application_uid'] = newApplicationID
            newApplication['tenant_id'] = user['user_uid']
            newApplication['application_status'] = 'NEW'
            response = db.insert('applications', newApplication)
        return response

    def put(self):
        response = {}
        with connect() as db:
            data = request.json
            fields = ['message', 'application_status',
                      'property_uid', 'adult_occupants', 'children_occupants']
            newApplication = {}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    newApplication[field] = fieldValue
            if newApplication['application_status'] == 'RENTED':
                response = db.execute(
                    """SELECT * FROM pm.applications WHERE application_status='FORWARDED' AND property_uid = \'"""
                    + newApplication['property_uid']
                    + """\' """)
                # print('response', response, len(response['result']))
                if len(response['result']) > 1:
                    newApplication['application_status'] = 'ACCEPTED'
                else:
                    response = db.execute(
                        """SELECT * FROM pm.applications WHERE application_status='ACCEPTED' AND property_uid = \'"""
                        + newApplication['property_uid']
                        + """\' """)
                    print('response', response['result'])

                    if len(response['result']) > 0:
                        newApplication['application_status'] = 'RENTED'
                        for response in response['result']:
                            pk = {
                                'application_uid': response['application_uid']
                            }
                            response = db.update(
                                'applications', pk, newApplication)
                    res = db.execute("""SELECT
                                        r.*,
                                        p.*,
                                        GROUP_CONCAT(lt.linked_tenant_id) as `tenants`
                                        FROM pm.rentals r
                                        LEFT JOIN pm.leaseTenants lt
                                        ON lt.linked_rental_uid = r.rental_uid
                                        LEFT JOIN pm.propertyManager p
                                        ON p.linked_property_id= r.rental_property_id
                                        WHERE r.rental_status='PROCESSING'
                                        AND p.management_status = 'ACCEPTED'
                                        AND r.rental_property_id = \'""" + newApplication['property_uid'] + """\'
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
                    due_date = start_date.replace(
                        day=int(res['result'][0]['due_by']))
                    if len(res['result']) > 0:

                        # creating purchases
                        rentPayments = json.loads(
                            res['result'][0]['rent_payments'])
                        for payment in rentPayments:
                            print(payment)
                            if(payment['fee_name'] == 'Rent'):
                                print('payment fee purchase_type RENT')
                                if payment['frequency'] == 'Weekly':
                                    print('payment frequency weekly $')
                                    charge_month = start_date.strftime('%B')
                                    # charge_date = next_weekday(start_date, 4)
                                    charge_date = start_date
                                    # print('charge_date', charge_date)
                                    daily_charge = round(
                                        int(payment['charge']) / days_in_month(start_date), 2)
                                    num_days_active = days_in_month(
                                        start_date) - start_date.day
                                    prorated_charge = num_days_active * daily_charge
                                    purchaseResponse = newPurchase(
                                        linked_bill_id=None,
                                        pur_property_id=res['result'][0]['rental_property_id'],
                                        payer=json.dumps(tenants),
                                        receiver=res['result'][0]['linked_business_id'],
                                        purchase_type='RENT',
                                        description=payment['fee_name'],
                                        amount_due=prorated_charge,
                                        purchase_notes=charge_month,
                                        purchase_date=start_date,
                                        purchase_frequency=payment['frequency'],
                                        next_payment=charge_date
                                    )
                                elif payment['frequency'] == 'Biweekly':
                                    print('payment frequency biweekly $')
                                    charge_month = start_date.strftime('%B')
                                    # charge_date = next_weekday_biweekly(
                                    #     start_date, 4)
                                    charge_date = start_date
                                    # print('charge_date', charge_date)
                                    daily_charge = round(
                                        int(payment['charge']) / days_in_month(start_date), 2)
                                    num_days_active = days_in_month(
                                        start_date) - start_date.day
                                    prorated_charge = num_days_active * daily_charge
                                    purchaseResponse = newPurchase(
                                        linked_bill_id=None,
                                        pur_property_id=res['result'][0]['rental_property_id'],
                                        payer=json.dumps(tenants),
                                        receiver=res['result'][0]['linked_business_id'],
                                        purchase_type='RENT',
                                        description=payment['fee_name'],
                                        amount_due=prorated_charge,
                                        purchase_notes=charge_month,
                                        purchase_date=start_date,
                                        purchase_frequency=payment['frequency'],
                                        next_payment=charge_date
                                    )
                                elif payment['frequency'] == 'Monthly':
                                    print('payment frequency monthly $')
                                    charge_date = start_date

                                    # prorate first month
                                    daily_charge_begin = round(
                                        int(payment['charge']) / days_in_month(start_date), 2)
                                    num_days_active_begin = days_in_month(
                                        start_date) - start_date.day
                                    prorated_charge_begin = num_days_active_begin * daily_charge_begin

                                    # prorate last month
                                    daily_charge_end = round(
                                        int(payment['charge']) / days_in_month(end_date), 2)
                                    num_days_active_end = end_date.day
                                    prorated_charge_end = num_days_active_end * daily_charge_end

                                    while due_date < end_date:
                                        charge_month = due_date.strftime(
                                            '%B')
                                        print(due_date, charge_date,
                                              charge_month)
                                        # charge_date = start_date.replace(
                                        #     day=days_in_month(start_date))

                                        if today.month == due_date.month:
                                            print(
                                                'here today.moth == due_date.month', due_date, today)
                                            purchaseResponse = newPurchase(
                                                linked_bill_id=None,
                                                pur_property_id=res['result'][0]['rental_property_id'],
                                                payer=json.dumps(tenants),
                                                receiver=res['result'][0]['linked_business_id'],
                                                purchase_type='RENT',
                                                description=payment['fee_name'],
                                                amount_due=prorated_charge_begin,
                                                purchase_notes=charge_month,
                                                purchase_date=start_date,
                                                purchase_frequency=payment['frequency'],
                                                next_payment=charge_date
                                            )
                                        elif end_date.month == due_date.month:
                                            print(
                                                'here end_date.moth == due_date.month', due_date, end_date)
                                            purchaseResponse = newPurchase(
                                                linked_bill_id=None,
                                                pur_property_id=res['result'][0]['rental_property_id'],
                                                payer=json.dumps(tenants),
                                                receiver=res['result'][0]['linked_business_id'],
                                                purchase_type='RENT',
                                                description=payment['fee_name'],
                                                amount_due=prorated_charge_end,
                                                purchase_notes=charge_month,
                                                purchase_date=start_date,
                                                purchase_frequency=payment['frequency'],
                                                next_payment=due_date
                                            )
                                        else:
                                            print(
                                                'here everything in between', due_date, end_date)
                                            purchaseResponse = newPurchase(
                                                linked_bill_id=None,
                                                pur_property_id=res['result'][0]['rental_property_id'],
                                                payer=json.dumps(tenants),
                                                receiver=res['result'][0]['linked_business_id'],
                                                purchase_type='RENT',
                                                description=payment['fee_name'],
                                                amount_due=payment['charge'],
                                                purchase_notes=charge_month,
                                                purchase_date=start_date,
                                                purchase_frequency=payment['frequency'],
                                                next_payment=due_date
                                            )
                                        due_date += relativedelta(months=1)

                                elif payment['frequency'] == 'Annually':
                                    print('payment frequency annually $')
                                    charge_month = (start_date).strftime('%B')
                                    # charge_date = start_date.replace(
                                    #     day=1) + relativedelta(months=1)
                                    charge_date = start_date
                                    purchaseResponse = newPurchase(
                                        linked_bill_id=None,
                                        pur_property_id=res['result'][0]['rental_property_id'],
                                        payer=json.dumps(tenants),
                                        receiver=res['result'][0]['linked_business_id'],
                                        purchase_type='RENT',
                                        description=payment['fee_name'],
                                        amount_due=payment['charge'],
                                        purchase_notes=charge_month,
                                        purchase_date=start_date,
                                        purchase_frequency=payment['frequency'],
                                        next_payment=charge_date
                                    )
                                else:
                                    print('payment frequency one-time $')
                                    charge_month = (start_date).strftime('%B')
                                    # charge_date = start_date.replace(
                                    #     day=1) + relativedelta(months=1)
                                    charge_date = start_date
                                    purchaseResponse = newPurchase(
                                        linked_bill_id=None,
                                        pur_property_id=res['result'][0]['rental_property_id'],
                                        payer=json.dumps(tenants),
                                        receiver=res['result'][0]['linked_business_id'],
                                        purchase_type='RENT',
                                        description=payment['fee_name'],
                                        amount_due=payment['charge'],
                                        purchase_notes=charge_month,
                                        purchase_date=start_date,
                                        purchase_frequency=payment['frequency'],
                                        next_payment=charge_date
                                    )
                            else:
                                print('payment fee purchase_type EXTRA CHARGES')
                                if payment['frequency'] == 'Weekly':
                                    print('payment frequency weekly $')
                                    charge_month = start_date.strftime('%B')
                                    # charge_date = next_weekday(start_date, 4)
                                    charge_date = start_date
                                    # print('charge_date', charge_date)
                                    daily_charge = round(
                                        int(payment['charge']) / days_in_month(start_date), 2)
                                    num_days_active = days_in_month(
                                        start_date) - start_date.day
                                    prorated_charge = num_days_active * daily_charge
                                    purchaseResponse = newPurchase(
                                        linked_bill_id=None,
                                        pur_property_id=res['result'][0]['rental_property_id'],
                                        payer=json.dumps(tenants),
                                        receiver=res['result'][0]['linked_business_id'],
                                        purchase_type='EXTRA CHARGES',
                                        description=payment['fee_name'],
                                        amount_due=prorated_charge,
                                        purchase_notes=charge_month,
                                        purchase_date=start_date,
                                        purchase_frequency=payment['frequency'],
                                        next_payment=charge_date
                                    )
                                elif payment['frequency'] == 'Biweekly':
                                    print('payment frequency biweekly $')
                                    charge_month = start_date.strftime('%B')
                                    # charge_date = next_weekday_biweekly(
                                    #     start_date, 4)
                                    charge_date = start_date
                                    # print('charge_date', charge_date)
                                    daily_charge = round(
                                        int(payment['charge']) / days_in_month(start_date), 2)
                                    num_days_active = days_in_month(
                                        start_date) - start_date.day
                                    prorated_charge = num_days_active * daily_charge
                                    purchaseResponse = newPurchase(
                                        linked_bill_id=None,
                                        pur_property_id=res['result'][0]['rental_property_id'],
                                        payer=json.dumps(tenants),
                                        receiver=res['result'][0]['linked_business_id'],
                                        purchase_type='EXTRA CHARGES',
                                        description=payment['fee_name'],
                                        amount_due=prorated_charge,
                                        purchase_notes=charge_month,
                                        purchase_date=start_date,
                                        purchase_frequency=payment['frequency'],
                                        next_payment=charge_date
                                    )
                                elif payment['frequency'] == 'Monthly':
                                    print('payment frequency monthly $')
                                    charge_date = start_date
                                    print(today.month)
                                    daily_charge = round(
                                        int(payment['charge']) / days_in_month(start_date), 2)
                                    num_days_active = days_in_month(
                                        start_date) - start_date.day
                                    prorated_charge = num_days_active * daily_charge
                                    while charge_date < end_date:
                                        charge_month = due_date.strftime(
                                            '%B')
                                        # charge_date = start_date.replace(
                                        #     day=days_in_month(start_date))

                                        if today.month == due_date.month:
                                            purchaseResponse = newPurchase(
                                                linked_bill_id=None,
                                                pur_property_id=res['result'][0]['rental_property_id'],
                                                payer=json.dumps(tenants),
                                                receiver=res['result'][0]['linked_business_id'],
                                                purchase_type='EXTRA CHARGES',
                                                description=payment['fee_name'],
                                                amount_due=prorated_charge,
                                                purchase_notes=charge_month,
                                                purchase_date=start_date,
                                                purchase_frequency=payment['frequency'],
                                                next_payment=charge_date
                                            )
                                        else:
                                            purchaseResponse = newPurchase(
                                                linked_bill_id=None,
                                                pur_property_id=res['result'][0]['rental_property_id'],
                                                payer=json.dumps(tenants),
                                                receiver=res['result'][0]['linked_business_id'],
                                                purchase_type='EXTRA CHARGES',
                                                description=payment['fee_name'],
                                                amount_due=payment['charge'],
                                                purchase_notes=charge_month,
                                                purchase_date=start_date,
                                                purchase_frequency=payment['frequency'],
                                                next_payment=due_date
                                            )
                                        charge_date += relativedelta(months=1)
                                        due_date += relativedelta(months=1)
                                elif payment['frequency'] == 'Annually':
                                    print('payment frequency annually $')
                                    charge_month = (start_date).strftime('%B')
                                    # charge_date = start_date.replace(
                                    #     day=1) + relativedelta(months=1)
                                    charge_date = start_date
                                    purchaseResponse = newPurchase(
                                        linked_bill_id=None,
                                        pur_property_id=res['result'][0]['rental_property_id'],
                                        payer=json.dumps(tenants),
                                        receiver=res['result'][0]['linked_business_id'],
                                        purchase_type='EXTRA CHARGES',
                                        description=payment['fee_name'],
                                        amount_due=payment['charge'],
                                        purchase_notes=charge_month,
                                        purchase_date=start_date,
                                        purchase_frequency=payment['frequency'],
                                        next_payment=charge_date
                                    )
                                else:
                                    print('payment frequency one-time $')
                                    charge_month = (start_date).strftime('%B')
                                    # charge_date = start_date.replace(
                                    #     day=1) + relativedelta(months=1)
                                    charge_date = start_date
                                    purchaseResponse = newPurchase(
                                        linked_bill_id=None,
                                        pur_property_id=res['result'][0]['rental_property_id'],
                                        payer=json.dumps(tenants),
                                        receiver=res['result'][0]['linked_business_id'],
                                        purchase_type='EXTRA CHARGES',
                                        description=payment['fee_name'],
                                        amount_due=payment['charge'],
                                        purchase_notes=charge_month,
                                        purchase_date=start_date,
                                        purchase_frequency=payment['frequency'],
                                        next_payment=charge_date
                                    )

                        pk1 = {
                            'rental_uid': res['result'][0]['rental_uid']}
                        newRental = {
                            'rental_status': 'ACTIVE'}
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
                            resRej = db.update(
                                'applications', pk, rejApplication)
            elif newApplication['application_status'] == 'REFUSED':
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
                        """SELECT * FROM pm.rentals WHERE rental_status='PROCESSING' AND rental_property_id = \'"""
                        + newApplication['property_uid']
                        + """\' """)
                    # print('res', res, len(res['result']))
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

            #     recipient = 'zacharywolfflind@gmail.com'
            #     subject = 'Application Accepted'
            #     body = 'Your application for the apartment has been accepted'
            #     current_app.sendEmail(recipient, subject, body)
            primaryKey = {
                'application_uid': data.get('application_uid')
            }
            # print('newAppl', newApplication)
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
                        updateApp['application_status'] = 'ENDED'
                        for multiEndRes in multiEndRes['result']:
                            pk = {
                                'application_uid': multiEndRes['application_uid']
                            }
                            multiEnd = db.update('applications', pk, updateApp)
                    # set the other to ENDED
                    pmEndRes = db.execute(
                        """SELECT * FROM pm.applications WHERE application_status ='PM END EARLY' AND property_uid = \'"""
                        + updateApp['property_uid']
                        + """\' """)
                    print(pmEndRes)
                    if len(pmEndRes['result']) > 0:
                        updateApp['application_status'] = 'ENDED'
                        pk = {
                            'application_uid': pmEndRes['result'][0]['application_uid']
                        }
                        response = db.update('applications', pk, updateApp)
                    # rental_status gets set to TERMINATED and lease_end updated to early_end_date
                    res = db.execute("""SELECT
                                            r.*,
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
                        'pur_property_id': updateApp['property_uid']
                    }
                    pur_response = db.delete("""DELETE FROM pm.purchases WHERE pur_property_id = \'""" + updateApp['property_uid'] + """\'
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
                        updateApp['application_status'] = 'ENDED'
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
                    'pur_property_id': updateApp['property_uid']
                }
                pur_response = db.delete("""DELETE FROM pm.purchases WHERE pur_property_id = \'""" + updateApp['property_uid'] + """\'
                                                AND (MONTH(purchase_date) > MONTH(now()) AND YEAR(purchase_date) = YEAR(now()) OR YEAR(purchase_date) > YEAR(now()))
                                                AND purchase_status ="UNPAID"
                                                AND (purchase_type= "RENT" OR purchase_type= "EXTRA CHARGES")""")
            else:
                print('refused')
                # if pm refuses to end the lease early, application_status set back to RENTED
                refResPM = db.execute("""SELECT * 
                                        FROM pm.applications 
                                        WHERE (application_status ='TENANT END EARLY' OR application_status ='TENANT END REQUESTED')
                                        AND property_uid = \'""" + updateApp['property_uid'] + """\' """)
                if len(refResPM['result']) > 0:
                    for refRes in refResPM['result']:
                        pk = {
                            'application_uid': refRes['application_uid']
                        }
                        updateRefRes = {
                            'application_status': 'RENTED'
                        }
                        response = db.update('applications', pk, updateRefRes)
                # if tenant refuses to end the lease early, application_status set back to RENTED
                refResTenant = db.execute("""SELECT * 
                                        FROM pm.applications 
                                        WHERE (application_status ='PM END EARLY' OR application_status ='END ACCEPTED')
                                        AND property_uid = \'""" + updateApp['property_uid'] + """\' """)
                print('refrestenant', refResTenant['result'])
                if len(refResTenant['result']) > 0:
                    for refRes in refResTenant['result']:
                        pk = {
                            'application_uid': refRes['application_uid']
                        }
                        updateRefRes = {
                            'application_status': 'RENTED'
                        }
                        response = db.update('applications', pk, updateRefRes)

        return response
