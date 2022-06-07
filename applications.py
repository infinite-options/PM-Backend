from flask import request, current_app
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from data import connect
import json

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
            fields = ['property_uid', 'message']
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
                print('response', response, len(response['result']))
                if len(response['result']) > 1:
                    newApplication['application_status'] = 'ACCEPTED'
                else:
                    response = db.execute(
                        """SELECT * FROM pm.applications WHERE application_status='ACCEPTED' AND property_uid = \'"""
                        + newApplication['property_uid']
                        + """\' """)
                    print('response', response['result'])

                    if len(response['result']) > 0:
                        # tenants = response['result'][0]['tenant_id']
                        # print('tenants1', tenants)
                        # if '[' in tenants:
                        #     print('tenants2', tenants)
                        #     tenants = json.loads(tenants)
                        #     print('tenants3', tenants)
                        # print('tenants4', tenants)
                        # if type(tenants) == str:
                        #     tenants = [tenants]
                        #     print('tenants5', tenants)
                        # print('tenant_id', tenants)
                        newApplication['application_status'] = 'RENTED'
                        for response in response['result']:
                            pk = {
                                'application_uid': response['application_uid']
                            }
                            response = db.update(
                                'applications', pk, newApplication)
                    res = db.execute(
                        """SELECT * FROM pm.rentals r LEFT JOIN leaseTenants lt ON lt.linked_rental_uid = r.rental_uid   WHERE r.rental_status='PROCESSING' AND r.rental_property_id = \'"""
                        + newApplication['property_uid']
                        + """\' """)
                    print('res', res, len(res['result']))
                    tenants = res['result'][0]['linked_tenant_id']
                    print('tenants1', tenants)
                    if '[' in tenants:
                        print('tenants2', tenants)
                        tenants = json.loads(tenants)
                        print('tenants3', tenants)
                    print('tenants4', tenants)
                    if type(tenants) == str:
                        tenants = [tenants]
                        print('tenants5', tenants)
                    print('tenant_id', tenants)
                    if len(res['result']) > 0:
                        for res in res['result']:
                            print('res', res)
                            # creating purchases
                            rentPayments = json.loads(res['rent_payments'])
                            for payment in rentPayments:
                                if payment['frequency'] == 'Monthly':
                                    charge_date = date.fromisoformat(
                                        res['lease_start'])
                                    lease_end = date.fromisoformat(
                                        res['lease_end'])
                                    print('charge_date', type(charge_date),
                                          charge_date.isoformat())
                                    while charge_date < lease_end:
                                        charge_month = charge_date.strftime(
                                            '%B')
                                        if(payment['fee_name'] == 'Rent'):
                                            purchaseResponse = newPurchase(
                                                linked_bill_id=None,
                                                pur_property_id=res['rental_property_id'],
                                                payer=json.dumps(tenants),
                                                receiver=res['rental_property_id'],
                                                purchase_type='RENT',
                                                description=payment['fee_name'],
                                                amount_due=payment['charge'],
                                                purchase_notes=charge_month,
                                                purchase_date=charge_date.isoformat(),
                                                purchase_frequency=payment['frequency'],
                                                next_payment=charge_date.replace(
                                                    day=1)
                                            )
                                        else:
                                            purchaseResponse = newPurchase(
                                                linked_bill_id=None,
                                                pur_property_id=res['rental_property_id'],
                                                payer=json.dumps(tenants),
                                                receiver=res['rental_property_id'],
                                                purchase_type='EXTRA CHARGES',
                                                description=payment['fee_name'],
                                                amount_due=payment['charge'],
                                                purchase_notes=charge_month,
                                                purchase_date=charge_date.isoformat(),
                                                purchase_frequency=payment['frequency'],
                                                next_payment=charge_date.replace(
                                                    day=1)
                                            )
                                        charge_date += relativedelta(months=1)
                                else:
                                    print('lease_start', type(
                                        res['lease_start']))
                                    charge_date = date.fromisoformat(
                                        res['lease_start'])
                                    lease_end = date.fromisoformat(
                                        res['lease_end'])
                                    print('charge_date', type(charge_date),
                                          charge_date.isoformat())

                                    charge_month = charge_date.strftime(
                                        '%B')
                                    if(payment['fee_name'] == 'Rent'):
                                        purchaseResponse = newPurchase(
                                            linked_bill_id=None,
                                            pur_property_id=res['rental_property_id'],
                                            payer=json.dumps(tenants),
                                            receiver=res['rental_property_id'],
                                            purchase_type='RENT',
                                            description=payment['fee_name'],
                                            amount_due=payment['charge'],
                                            purchase_notes=charge_month,
                                            purchase_date=res['lease_start'],
                                            purchase_frequency=payment['frequency'],
                                            next_payment=date.fromisoformat(
                                                res['lease_start']).replace(day=1)
                                        )

                                    else:

                                        purchaseResponse = newPurchase(
                                            linked_bill_id=None,
                                            pur_property_id=res['rental_property_id'],
                                            payer=json.dumps(tenants),
                                            receiver=res['rental_property_id'],
                                            purchase_type='EXTRA CHARGES',
                                            description=payment['fee_name'],
                                            amount_due=payment['charge'],
                                            purchase_notes=charge_month,
                                            purchase_date=res['lease_start'],
                                            purchase_frequency=payment['frequency'],
                                            next_payment=date.fromisoformat(
                                                res['lease_start']).replace(day=1)
                                        )
                            pk1 = {
                                'rental_uid': res['rental_uid']}
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
                    print('res', res, len(res['result']))
                    if len(res['result']) > 0:
                        for res in res['result']:
                            print('res', res['rental_uid'])
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
