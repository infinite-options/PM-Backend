import resource
from flask import request, current_app
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from data import connect
import json

from text_to_num import alpha2digit
from purchases import newPurchase
from datetime import date
from dateutil.relativedelta import relativedelta


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
                    if len(res['result']) > 0:

                        # creating purchases
                        rentPayments = json.loads(
                            res['result'][0]['rent_payments'])
                        for payment in rentPayments:
                            if payment['frequency'] == 'Monthly':

                                charge_date = date.fromisoformat(
                                    res['result'][0]['lease_start'])
                                due_date = charge_date.replace(
                                    day=int(res['result'][0]['due_by']))
                                lease_end = date.fromisoformat(
                                    res['result'][0]['lease_end'])
                                # print('charge_date', type(charge_date),
                                #       charge_date.isoformat())
                                while charge_date < lease_end:
                                    charge_month = charge_date.strftime(
                                        '%B')
                                    if(payment['fee_name'] == 'Rent'):
                                        purchaseResponse = newPurchase(
                                            linked_bill_id=None,
                                            pur_property_id=res['result'][0]['rental_property_id'],
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
                                            pur_property_id=res['result'][0]['rental_property_id'],
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
                                    res['result'][0]['lease_start'])
                                due_date = date.fromisoformat(
                                    res['result'][0]['lease_start']).replace(
                                    day=int(res['result'][0]['due_by']))
                                lease_end = date.fromisoformat(
                                    res['result'][0]['lease_end'])
                                # print('charge_date', type(charge_date),
                                #       charge_date.isoformat())

                                charge_month = charge_date.strftime(
                                    '%B')
                                if(payment['fee_name'] == 'Rent'):
                                    purchaseResponse = newPurchase(
                                        linked_bill_id=None,
                                        pur_property_id=res['result'][0]['rental_property_id'],
                                        payer=json.dumps(tenants),
                                        receiver=res['result'][0]['linked_business_id'],
                                        purchase_type='RENT',
                                        description=payment['fee_name'],
                                        amount_due=payment['charge'],
                                        purchase_notes=charge_month,
                                        purchase_date=res['result'][0]['lease_start'],
                                        purchase_frequency=payment['frequency'],
                                        next_payment=due_date
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
                                        purchase_date=res['result'][0]['lease_start'],
                                        purchase_frequency=payment['frequency'],
                                        next_payment=due_date
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
                      'property_uid', 'application_uid']
            updateApp = {}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    updateApp[field] = fieldValue
            # pm wants to end the lease early, in case of multiple tenants both will get set to PM END EARLY
            if updateApp['application_status'] == 'PM END EARLY':
                print('end early pm')
                appRes = db.execute(
                    """SELECT * FROM pm.applications WHERE application_status='RENTED' AND property_uid = \'"""
                    + updateApp['property_uid']
                    + """\' """)
                if len(appRes['result']) > 0:
                    for application in appRes['result']:
                        print(application)
                        updateApp = {
                            'application_status': 'PM END EARLY',
                        }
                        pk = {
                            'application_uid': application['application_uid']}
                        response = db.update('applications', pk, updateApp)
             # tenant wants to end the lease early, in case of multiple tenants only given application_uid will get set to TENANT END EARLY
            elif updateApp['application_status'] == 'TENANT END EARLY':
                print('end early tenant')
                updateApp['application_status'] = 'TENANT END EARLY'
                pk = {
                    'application_uid': updateApp['application_uid']}
                response = db.update('applications', pk, updateApp)

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
                        'rental_status': 'TERMINATED'}
                    res = db.update(
                        'rentals', pk1, newRental)
                    pur_pk = {
                        'pur_property_id': updateApp['property_uid']
                    }
                    pur_response = db.delete("""DELETE FROM pm.purchases WHERE pur_property_id = \'""" + updateApp['property_uid'] + """\'
                                                    AND (MONTH(purchase_date) > MONTH(now()) AND YEAR(purchase_date) = YEAR(now()) OR YEAR(purchase_date) > YEAR(now()))
                                                    AND purchase_status ="UNPAID"
                                                    AND (purchase_type= "RENT" OR purchase_type= "EXTRA CHARGES")""")
            # if PM approves the lease ending
            else:
                response = db.execute(
                    """SELECT * FROM pm.applications WHERE (application_status='TENANT END EARLY' OR application_status='RENTED') AND property_uid = \'"""
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
                        """SELECT * FROM pm.applications WHERE application_status ='TENANT END EARLY' AND property_uid = \'"""
                        + updateApp['property_uid']
                        + """\' """)
                    print(pmEndRes)
                    if len(pmEndRes['result']) > 0:
                        updateApp['application_status'] = 'ENDED'
                        pk = {
                            'application_uid': pmEndRes['result'][0]['application_uid']
                        }
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
                    pk1 = {
                        'rental_uid': res['result'][0]['rental_uid']}
                    newRental = {
                        'rental_status': 'TERMINATED'}
                    res = db.update(
                        'rentals', pk1, newRental)
                    pur_pk = {
                        'pur_property_id': updateApp['property_uid']
                    }
                    pur_response = db.delete("""DELETE FROM pm.purchases WHERE pur_property_id = \'""" + updateApp['property_uid'] + """\'
                                                    AND (MONTH(purchase_date) > MONTH(now()) AND YEAR(purchase_date) = YEAR(now()) OR YEAR(purchase_date) > YEAR(now()))
                                                    AND purchase_status ="UNPAID"
                                                    AND (purchase_type= "RENT" OR purchase_type= "EXTRA CHARGES")""")

        return response
