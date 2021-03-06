
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from matplotlib.style import available

from data import connect
import json
from datetime import date, timedelta, datetime
from calendar import monthrange
from dateutil.relativedelta import relativedelta
from purchases import newPurchase, updatePurchase


class Payments(Resource):
    def get(self):
        response = {}
        filters = [
            'payment_uid',
            'pay_purchase_id'
        ]
        where = {}
        for filter in filters:
            filterValue = request.args.get(filter)
            if filterValue is not None:
                where[filter] = filterValue
        with connect() as db:
            response = db.select('payments', where)
        return response

    def post(self):
        response = {}
        with connect() as db:
            data = request.get_json()
            fields = [
                'pay_purchase_id',
                'amount',
                'payment_notes',
                'charge_id',
                'payment_type'
            ]
            newPayment = {}
            for field in fields:
                newPayment[field] = data.get(field)
            newPaymentID = db.call('new_payment_id')['result'][0]['new_id']
            newPayment['payment_uid'] = newPaymentID
            response = db.insert('payments', newPayment)
            purchaseResponse = db.select('purchases', {
                'purchase_uid': newPayment['pay_purchase_id']
            })
            linkedPurchase = purchaseResponse['result'][0]
            linkedPurchase['amount_paid'] += newPayment['amount']
            if linkedPurchase['amount_paid'] >= linkedPurchase['amount_due']:
                linkedPurchase['purchase_status'] = 'PAID'
            updatePurchase(linkedPurchase)
        return response


class UserPayments(Resource):
    decorators = [jwt_required()]

    def get(self):
        response = {}
        user = get_jwt_identity()
        with connect() as db:
            print(user['user_uid'])
            user_id = user['user_uid']
            filters = ['pur_property_id']
            response = db.execute("""
                SELECT * FROM payments p1 LEFT JOIN purchases p2 ON pay_purchase_id = purchase_uid
                WHERE p2.payer LIKE '%""" + user_id + """%'
            """)
            # response = db.execute(sql, args)
        return response


class OwnerPayments(Resource):

    def get(self):
        response = {}
        filters = ['owner_id']
        where = {}
        with connect() as db:
            for filter in filters:
                filterValue = request.args.get(filter)
                if filterValue is not None:
                    where[filter] = filterValue
                # response = db.execute("""
                #     SELECT p1.*, p2.*
                #     FROM payments p1
                #     LEFT JOIN purchases p2
                #     ON pay_purchase_id = purchase_uid
                #     LEFT JOIN properties p
                #     ON p.property_uid = p2.pur_property_id
                #     WHERE p2.payer = '[\"""" + filterValue + """\"]'
                #     AND p.owner_id=   \'""" + filterValue + """\'
                # """)
                response = db.execute("""
                    SELECT * FROM payments p1 LEFT JOIN purchases p2 ON pay_purchase_id = purchase_uid
                    WHERE p2.payer LIKE '%""" + filterValue + """%'
                """)
                # response = db.execute(sql, args)
        return response


class ManagerPayments(Resource):

    def get(self):
        response = {}
        filters = ['manager_id']
        where = {}
        with connect() as db:
            for filter in filters:
                filterValue = request.args.get(filter)
                if filterValue is not None:
                    where[filter] = filterValue

                response = db.execute("""
                    SELECT * FROM payments p1 LEFT JOIN purchases p2 ON pay_purchase_id = purchase_uid
                    WHERE p2.payer LIKE '%""" + filterValue + """%'
                """)
                # response = db.execute(sql, args)
        return response


def diff_month(d1, d2):
    return (d1.year - d2.year) * 12 + d1.month - d2.month


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


class TenantPayments_CLASS(Resource):
    def get(self):
        response = {}
        with connect() as db:
            payments = []
            response = db.execute("""SELECT r.*, prop.*, propM.*, 
                                    GROUP_CONCAT(lt.linked_tenant_id) as `tenants` 
                                    FROM rentals r
                                    LEFT JOIN
                                    pm.properties prop
                                    ON prop.property_uid = r.rental_property_id
                                    LEFT JOIN pm.leaseTenants lt
                                    ON lt.linked_rental_uid = r.rental_uid
                                    LEFT JOIN
                                    pm.propertyManager propM
                                    ON propM.linked_property_id = r.rental_property_id
                                    WHERE r.rental_status = 'ACTIVE'
                                    GROUP BY lt.linked_rental_uid;  """)

            # getting all the previous rental payments
            if len(response['result']) > 0:
                for i in range(len(response['result'])):
                    response['result'][i]['expense_amount'] = 0
                    purRes = db.execute("""SELECT * FROM purchases pur
                                           WHERE pur.pur_property_id LIKE '%""" + response['result'][i]['property_uid'] + """%'
                                           AND pur.purchase_type = 'RENT' OR pur.purchase_type= 'EXTRA CHARGES' """)
                    print('purRes', purRes['result'])
                    response['result'][i]['prevPurchases'] = list(
                        purRes['result'])
            if len(response['result']) > 0:
                # creating purchases
                rentPayments = json.loads(
                    response['result'][0]['rent_payments'])
                for payment in rentPayments:
                    if(payment['fee_name'] == 'Rent'):
                        rent = payment['charge']

            if len(response['result']) > 0:
                # today's date
                today = date.today()
                for lease in response['result']:
                    # creating purchases
                    tenantPayments = json.loads(lease['rent_payments'])
                    payer = response['result'][0]['tenants'].split(',')
                    payer = json.dumps(payer)
                    for payment in tenantPayments:
                        # if fee_type is $, put the charge amount directly
                        if payment['fee_type'] == '$':
                            print('payment fee type $')
                            if(payment['fee_name'] == 'Rent'):
                                print('payment fee purchase_type RENT')
                                if payment['frequency'] == 'Weekly':
                                    print('payment frequency weekly $')
                                    lease_start = date.fromisoformat(
                                        lease['lease_start'])
                                    lease_end = date.fromisoformat(
                                        lease['lease_end'])
                                    # check if today's date is before lease end
                                    if today < lease_end:
                                        # get previous purchases
                                        if lease['prevPurchases'] != []:
                                            prevPurchaseDate = datetime.strptime(
                                                lease['prevPurchases'][-1]['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                        # set charge date as friday of every week
                                            due_date = next_weekday(
                                                prevPurchaseDate,  int(payment['due_by']))
                                            if len(payment['available_topay']) == 0:
                                                charge_date = due_date
                                            else:
                                                charge_date = due_date - \
                                                    timedelta(
                                                        days=int(payment['available_topay']))
                                            charge_month = due_date.strftime(
                                                '%B')
                                            print('due_date',
                                                  due_date, charge_month, charge_date)
                                            # if charge date == today then enter the monthly fee
                                            if charge_date == today:
                                                print(
                                                    'enter the fee to purchases')

                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [lease['property_uid']]),
                                                    payer=payer,
                                                    receiver=lease['linked_business_id'],
                                                    purchase_type='RENT',
                                                    description=payment['fee_name'],
                                                    amount_due=payment['charge'],
                                                    purchase_notes=charge_month,
                                                    purchase_date=lease['lease_start'],
                                                    purchase_frequency=payment['frequency'],
                                                    next_payment=due_date
                                                )
                                elif payment['frequency'] == 'Biweekly':
                                    print('payment frequency biweekly $')
                                    lease_start = date.fromisoformat(
                                        lease['lease_start'])
                                    lease_end = date.fromisoformat(
                                        lease['lease_end'])
                                    # check if today's date is before lease end
                                    if today < lease_end:
                                        # get previous purchases
                                        if lease['prevPurchases'] != []:
                                            prevPurchaseDate = datetime.strptime(
                                                lease['prevPurchases'][-1]['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                        # set charge date as friday of every 2 week
                                            due_date = next_weekday_biweekly(
                                                prevPurchaseDate,  int(payment['due_by']))
                                            if len(payment['available_topay']) == 0:
                                                charge_date = due_date
                                            else:
                                                charge_date = due_date - \
                                                    timedelta(
                                                        days=int(payment['available_topay']))
                                            charge_month = due_date.strftime(
                                                '%B')
                                            print('due_date',
                                                  due_date, charge_month, charge_date)
                                            # if charge date == today then enter the monthly fee
                                            if charge_date == today:
                                                print(
                                                    'enter the fee to purchases')

                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [lease['property_uid']]),
                                                    payer=payer,
                                                    receiver=lease['linked_business_id'],
                                                    purchase_type='RENT',
                                                    description=payment['fee_name'],
                                                    amount_due=payment['charge'],
                                                    purchase_notes=charge_month,
                                                    purchase_date=lease['lease_start'],
                                                    purchase_frequency=payment['frequency'],
                                                    next_payment=due_date
                                                )
                                elif payment['frequency'] == 'Monthly':
                                    print('payment frequency monthly $')
                                    lease_start = date.fromisoformat(
                                        lease['lease_start'])
                                    lease_end = date.fromisoformat(
                                        lease['lease_end'])
                                    # check if today's date is before lease end
                                    if today < lease_end:
                                        # get previous purchases
                                        if lease['prevPurchases'] != []:
                                            prevPurchaseDate = datetime.strptime(
                                                lease['prevPurchases'][-1]['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                            # set charge date as first of every month
                                            print(
                                                (payment['available_topay']))
                                            due_date = prevPurchaseDate.replace(
                                                day=int(payment['due_by'])) + relativedelta(months=1)
                                            if len(payment['available_topay']) == 0:
                                                charge_date = due_date
                                            else:
                                                charge_date = due_date - \
                                                    timedelta(
                                                        days=int(payment['available_topay']))

                                            charge_month = due_date.strftime(
                                                '%B')
                                            print('due_date',
                                                  due_date, charge_month, charge_date)
                                            # prorate last month
                                            daily_charge_end = round(
                                                int(payment['charge']) / days_in_month(lease_end), 2)
                                            num_days_active_end = lease_end.day
                                            prorated_charge_end = num_days_active_end * daily_charge_end
                                            # if charge date == today then enter the monthly fee
                                            if charge_date == today:
                                                print(
                                                    'enter the fee to purchases')

                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [lease['property_uid']]),
                                                    payer=payer,
                                                    receiver=lease['linked_business_id'],
                                                    purchase_type='RENT',
                                                    description=payment['fee_name'],
                                                    amount_due=payment['charge'],
                                                    purchase_notes=charge_month,
                                                    purchase_date=lease['lease_start'],
                                                    purchase_frequency=payment['frequency'],
                                                    next_payment=due_date
                                                )
                                            elif lease_end.month == charge_date.month and lease_end.year == charge_date.year:
                                                print(
                                                    'here end_date.moth == due_date.month', due_date, lease_end, charge_date)
                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [lease['property_uid']]),
                                                    payer=payer,
                                                    receiver=lease['linked_business_id'],
                                                    purchase_type='RENT',
                                                    description=payment['fee_name'],
                                                    amount_due=prorated_charge_end,
                                                    purchase_notes=charge_month,
                                                    purchase_date=lease['lease_start'],
                                                    purchase_frequency=payment['frequency'],
                                                    next_payment=due_date
                                                )
                                            else:
                                                print("do nothing")

                                elif payment['frequency'] == 'Annually':
                                    print('payment frequency annually $')
                                    lease_start = date.fromisoformat(
                                        lease['lease_start'])
                                    lease_end = date.fromisoformat(
                                        lease['lease_end'])
                                    # calculate the lease length
                                    diff = diff_month(lease_end, lease_start)
                                    # check if lease is at least an year long and today's date is before the lease ends
                                    if diff > 12 and today < lease_end:
                                        print('lease longer than 1 year')
                                        # create a charge date for 1 year from start date
                                        due_date = lease_start.replace(
                                            day=int(payment['due_by'])) + relativedelta(months=12)
                                        if len(payment['available_topay']) == 0:
                                            charge_date = due_date
                                        else:
                                            charge_date = due_date - \
                                                timedelta(
                                                    days=int(payment['available_topay']))
                                        charge_month = due_date.strftime(
                                            '%B')
                                        # check if today's date == the charge date
                                        if today == charge_date:
                                            # if yes, then enter the annual fees to the purchases table
                                            print('enter the fee to purchases')

                                            purchaseResponse = newPurchase(
                                                linked_bill_id=None,
                                                pur_property_id=json.dumps(
                                                    [lease['property_uid']]),
                                                payer=payer,
                                                receiver=lease['linked_business_id'],
                                                purchase_type='RENT',
                                                description=payment['fee_name'],
                                                amount_due=payment['charge'],
                                                purchase_notes=charge_month,
                                                purchase_date=lease['lease_start'],
                                                purchase_frequency=payment['frequency'],
                                                next_payment=due_date
                                            )
                                else:
                                    print('payment frequency one-time $')
                            elif payment['frequency'] == 'Move-Out Charge':
                                print(
                                    'payment fee purchase_type Move-Out Charge ')

                                print('payment frequency one-time $')
                                if today < lease_end:
                                    # get previous purchases
                                    if lease['prevPurchases'] != []:
                                        prevPurchaseDate = datetime.strptime(
                                            lease['prevPurchases'][-1]['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                        charge_month = (
                                            lease_end).strftime('%B')

                                        due_date = lease_end
                                        if len(payment['available_topay']) == 0:
                                            charge_date = due_date
                                        else:
                                            charge_date = due_date - \
                                                timedelta(
                                                    days=int(payment['available_topay']))
                                        if charge_date == today:
                                            print(
                                                'enter the fee to purchases')
                                            purchaseResponse = newPurchase(
                                                linked_bill_id=None,
                                                pur_property_id=json.dumps(
                                                    [lease['property_uid']]),
                                                payer=payer,
                                                receiver=lease['linked_business_id'],
                                                purchase_type='EXTRA CHARGES',
                                                description=payment['fee_name'],
                                                amount_due=payment['charge'],
                                                purchase_notes=charge_month,
                                                purchase_date=lease_start,
                                                purchase_frequency=payment['frequency'],
                                                next_payment=due_date
                                            )

                            elif payment['frequency'] == 'Move-in Charge':
                                print(
                                    'payment fee purchase_type EXTRA CHARGES')
                                print('skip')

                            else:
                                print(
                                    'payment fee purchase_type EXTRA CHARGES')
                                if payment['frequency'] == 'Weekly':
                                    print('payment frequency weekly $')
                                    lease_start = date.fromisoformat(
                                        lease['lease_start'])
                                    lease_end = date.fromisoformat(
                                        lease['lease_end'])
                                    # check if today's date is before lease end
                                    if today < lease_end:
                                        # get previous purchases
                                        if lease['prevPurchases'] != []:
                                            prevPurchaseDate = datetime.strptime(
                                                lease['prevPurchases'][-1]['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                        # set charge date as friday of every week
                                            due_date = next_weekday(
                                                prevPurchaseDate,  int(payment['due_by']))
                                            if len(payment['available_topay']) == 0:
                                                charge_date = due_date
                                            else:
                                                charge_date = due_date - \
                                                    timedelta(
                                                        days=int(payment['available_topay']))
                                            charge_month = due_date.strftime(
                                                '%B')
                                            print('due_date',
                                                  due_date, charge_month, charge_date)
                                            # if charge date == today then enter the monthly fee
                                            if charge_date == today:
                                                print(
                                                    'enter the fee to purchases')

                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [lease['property_uid']]),
                                                    payer=payer,
                                                    receiver=lease['linked_business_id'],
                                                    purchase_type='EXTRA CHARGES',
                                                    description=payment['fee_name'],
                                                    amount_due=payment['charge'],
                                                    purchase_notes=charge_month,
                                                    purchase_date=lease['lease_start'],
                                                    purchase_frequency=payment['frequency'],
                                                    next_payment=due_date
                                                )
                                elif payment['frequency'] == 'Biweekly':
                                    print('payment frequency biweekly $')
                                    lease_start = date.fromisoformat(
                                        lease['lease_start'])
                                    lease_end = date.fromisoformat(
                                        lease['lease_end'])
                                    # check if today's date is before lease end
                                    if today < lease_end:
                                        # get previous purchases
                                        if lease['prevPurchases'] != []:
                                            prevPurchaseDate = datetime.strptime(
                                                lease['prevPurchases'][-1]['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                        # set charge date as friday of every 2 week
                                            due_date = next_weekday_biweekly(
                                                prevPurchaseDate,  int(payment['due_by']))
                                            if len(payment['available_topay']) == 0:
                                                charge_date = due_date
                                            else:
                                                charge_date = due_date - \
                                                    timedelta(
                                                        days=int(payment['available_topay']))
                                            charge_month = due_date.strftime(
                                                '%B')
                                            print('due_date',
                                                  due_date, charge_month, charge_date)
                                            # if charge date == today then enter the monthly fee
                                            if charge_date == today:
                                                print(
                                                    'enter the fee to purchases')

                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [lease['property_uid']]),
                                                    payer=payer,
                                                    receiver=lease['linked_business_id'],
                                                    purchase_type='EXTRA CHARGES',
                                                    description=payment['fee_name'],
                                                    amount_due=payment['charge'],
                                                    purchase_notes=charge_month,
                                                    purchase_date=lease['lease_start'],
                                                    purchase_frequency=payment['frequency'],
                                                    next_payment=due_date
                                                )
                                elif payment['frequency'] == 'Monthly':
                                    print('payment frequency monthly $')
                                    lease_start = date.fromisoformat(
                                        lease['lease_start'])
                                    lease_end = date.fromisoformat(
                                        lease['lease_end'])
                                    # check if today's date is before lease end
                                    if today < lease_end:
                                        # get previous purchases
                                        if lease['prevPurchases'] != []:
                                            prevPurchaseDate = datetime.strptime(
                                                lease['prevPurchases'][-1]['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                            # set charge date as first of every month
                                            due_date = prevPurchaseDate.replace(
                                                day=int(payment['due_by'])) + relativedelta(months=1)
                                            if len(payment['available_topay']) == 0:
                                                charge_date = due_date
                                            else:
                                                charge_date = due_date - \
                                                    timedelta(
                                                        days=int(payment['available_topay']))
                                            charge_month = due_date.strftime(
                                                '%B')
                                            print('due_date',
                                                  due_date, charge_month, charge_date)
                                            # if charge date == today then enter the monthly fee
                                            if charge_date == today:
                                                print(
                                                    'enter the fee to purchases')

                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [lease['property_uid']]),
                                                    payer=payer,
                                                    receiver=lease['linked_business_id'],
                                                    purchase_type='EXTRA CHARGES',
                                                    description=payment['fee_name'],
                                                    amount_due=payment['charge'],
                                                    purchase_notes=charge_month,
                                                    purchase_date=lease['lease_start'],
                                                    purchase_frequency=payment['frequency'],
                                                    next_payment=due_date
                                                )

                                elif payment['frequency'] == 'Annually':
                                    print('payment frequency annually $')
                                    lease_start = date.fromisoformat(
                                        lease['lease_start'])
                                    lease_end = date.fromisoformat(
                                        lease['lease_end'])
                                    # calculate the lease length
                                    diff = diff_month(lease_end, lease_start)
                                    # check if lease is at least an year long and today's date is before the lease ends
                                    if diff > 12 and today < lease_end:
                                        print('lease longer than 1 year')
                                        # create a charge date for 1 year from start date
                                        due_date = lease_start.replace(
                                            day=int(payment['due_by'])) + relativedelta(months=12)
                                        if len(payment['available_topay']) == 0:
                                            charge_date = due_date
                                        else:
                                            charge_date = due_date - \
                                                timedelta(
                                                    days=int(payment['available_topay']))
                                        charge_month = due_date.strftime(
                                            '%B')
                                        # check if today's date == the charge date
                                        if today == charge_date:
                                            # if yes, then enter the annual fees to the purchases table
                                            print('enter the fee to purchases')

                                            purchaseResponse = newPurchase(
                                                linked_bill_id=None,
                                                pur_property_id=json.dumps(
                                                    [lease['property_uid']]),
                                                payer=payer,
                                                receiver=lease['linked_business_id'],
                                                purchase_type='EXTRA CHARGES',
                                                description=payment['fee_name'],
                                                amount_due=payment['charge'],
                                                purchase_notes=charge_month,
                                                purchase_date=lease['lease_start'],
                                                purchase_frequency=payment['frequency'],
                                                next_payment=due_date
                                            )
                                else:
                                    print('payment frequency one-time $')
                        # if fee_type is %, we check for the gross rent or net and calculate the charge according to that
                        else:
                            print('payment fee type %')
                            if(payment['fee_name'] == 'Rent'):
                                print('payment fee purchase_type RENT')
                                if payment['frequency'] == 'Weekly':
                                    print('payment frequency weekly %')
                                    lease_start = date.fromisoformat(
                                        lease['lease_start'])
                                    lease_end = date.fromisoformat(
                                        lease['lease_end'])
                                    # check if today's date is before lease end
                                    if today < lease_end:
                                        # get previous purchases
                                        if lease['prevPurchases'] != []:
                                            prevPurchaseDate = datetime.strptime(
                                                lease['prevPurchases'][-1]['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                            # set charge date as friday of every week
                                            due_date = next_weekday(
                                                prevPurchaseDate,  int(payment['due_by']))
                                            if len(payment['available_topay']) == 0:
                                                charge_date = due_date
                                            else:
                                                charge_date = due_date - \
                                                    timedelta(
                                                        days=int(payment['available_topay']))
                                            charge_month = due_date.strftime(
                                                '%B')
                                            print('due_date',
                                                  due_date, charge_month, charge_date)
                                            # if charge date == today then enter the monthly fee
                                            if charge_date == today:
                                                print(
                                                    'enter the fee to purchases')
                                                # if yes, then enter the monthly fees to the purchases table
                                                print(
                                                    'enter the fee to purchases')
                                                # if gross rent (listed rent)
                                                if payment['of'] == 'Gross Rent':
                                                    print('payment of gross rent', (
                                                        int(payment['charge']) * int(rent))/100)
                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [lease['property_uid']]),
                                                        payer=payer,
                                                        receiver=lease['linked_business_id'],
                                                        purchase_type='RENT',
                                                        description=payment['fee_name'],
                                                        amount_due=(
                                                            int(payment['charge']) * int(rent))/100,
                                                        purchase_notes=charge_month,
                                                        purchase_date=lease['lease_start'],
                                                        purchase_frequency=payment['frequency'],
                                                        next_payment=due_date
                                                    )
                                                # if net rent (listed rent-expenses)
                                                else:
                                                    print('payment of net rent', (
                                                        int(payment['charge']) * (int(rent)))/100)
                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [lease['property_uid']]),
                                                        payer=payer,
                                                        receiver=lease['linked_business_id'],
                                                        purchase_type='RENT',
                                                        description=payment['fee_name'],
                                                        amount_due=(
                                                            int(payment['charge']) * (int(rent)))/100,
                                                        purchase_notes=charge_month,
                                                        purchase_date=lease['lease_start'],
                                                        purchase_frequency=payment['frequency'],
                                                        next_payment=due_date
                                                    )
                                elif payment['frequency'] == 'Bwieekly':
                                    print('payment frequency biweekly %')
                                    lease_start = date.fromisoformat(
                                        lease['lease_start'])
                                    lease_end = date.fromisoformat(
                                        lease['lease_end'])
                                    # check if today's date is before lease end
                                    if today < lease_end:
                                        # get previous purchases
                                        if lease['prevPurchases'] != []:
                                            prevPurchaseDate = datetime.strptime(
                                                lease['prevPurchases'][-1]['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                            # set charge date as friday every two weeks
                                            due_date = next_weekday_biweekly(
                                                prevPurchaseDate,  int(payment['due_by']))
                                            if len(payment['available_topay']) == 0:
                                                charge_date = due_date
                                            else:
                                                charge_date = due_date - \
                                                    timedelta(
                                                        days=int(payment['available_topay']))
                                            charge_month = due_date.strftime(
                                                '%B')
                                            print('due_date',
                                                  due_date, charge_month, charge_date)
                                            # if charge date == today then enter the monthly fee
                                            if charge_date == today:
                                                print(
                                                    'enter the fee to purchases')
                                                # if yes, then enter the monthly fees to the purchases table
                                                print(
                                                    'enter the fee to purchases')
                                                # if gross rent (listed rent)
                                                if payment['of'] == 'Gross Rent':
                                                    print('payment of gross rent', (
                                                        int(payment['charge']) * int(rent))/100)
                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [lease['property_uid']]),
                                                        payer=payer,
                                                        receiver=lease['linked_business_id'],
                                                        purchase_type='RENT',
                                                        description=payment['fee_name'],
                                                        amount_due=(
                                                            int(payment['charge']) * int(rent))/100,
                                                        purchase_notes=charge_month,
                                                        purchase_date=lease['lease_start'],
                                                        purchase_frequency=payment['frequency'],
                                                        next_payment=due_date
                                                    )
                                                # if net rent (listed rent-expenses)
                                                else:
                                                    print('payment of net rent', (
                                                        int(payment['charge']) * (int(rent)))/100)
                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [lease['property_uid']]),
                                                        payer=payer,
                                                        receiver=lease['linked_business_id'],
                                                        purchase_type='RENT',
                                                        description=payment['fee_name'],
                                                        amount_due=(
                                                            int(payment['charge']) * (int(rent)))/100,
                                                        purchase_notes=charge_month,
                                                        purchase_date=lease['lease_start'],
                                                        purchase_frequency=payment['frequency'],
                                                        next_payment=due_date
                                                    )
                                elif payment['frequency'] == 'Monthly':
                                    print('payment frequency monthly %')
                                    lease_start = date.fromisoformat(
                                        lease['lease_start'])
                                    lease_end = date.fromisoformat(
                                        lease['lease_end'])
                                    # check if today's date is before lease end
                                    if today < lease_end:
                                        # get previous purchases
                                        if lease['prevPurchases'] != []:
                                            prevPurchaseDate = datetime.strptime(
                                                lease['prevPurchases'][-1]['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                            # set charge date as first of every month
                                            due_date = prevPurchaseDate.replace(
                                                day=int(payment['due_by'])) + relativedelta(months=1)
                                            if len(payment['available_topay']) == 0:
                                                charge_date = due_date
                                            else:
                                                charge_date = due_date - \
                                                    timedelta(
                                                        days=int(payment['available_topay']))
                                            charge_month = due_date.strftime(
                                                '%B')
                                            print('due_date',
                                                  due_date, charge_month, charge_date)
                                            # if charge date == today then enter the monthly fee
                                            if charge_date == today:
                                                print(
                                                    'enter the fee to purchases')
                                                # if yes, then enter the monthly fees to the purchases table
                                                print(
                                                    'enter the fee to purchases')
                                                # if gross rent (listed rent)
                                                if payment['of'] == 'Gross Rent':
                                                    print('payment of gross rent', (
                                                        int(payment['charge']) * int(rent))/100)
                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [lease['property_uid']]),
                                                        payer=payer,
                                                        receiver=lease['linked_business_id'],
                                                        purchase_type='RENT',
                                                        description=payment['fee_name'],
                                                        amount_due=(
                                                            int(payment['charge']) * int(rent))/100,
                                                        purchase_notes=charge_month,
                                                        purchase_date=lease['lease_start'],
                                                        purchase_frequency=payment['frequency'],
                                                        next_payment=due_date
                                                    )
                                                # if net rent (listed rent-expenses)
                                                else:
                                                    print('payment of net rent', (
                                                        int(payment['charge']) * (int(rent)))/100)
                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [lease['property_uid']]),
                                                        payer=payer,
                                                        receiver=lease['linked_business_id'],
                                                        purchase_type='RENT',
                                                        description=payment['fee_name'],
                                                        amount_due=(
                                                            int(payment['charge']) * (int(rent)))/100,
                                                        purchase_notes=charge_month,
                                                        purchase_date=lease['lease_start'],
                                                        purchase_frequency=payment['frequency'],
                                                        next_payment=due_date
                                                    )
                                elif payment['frequency'] == 'Annually':
                                    print('payment frequency annually %')
                                    lease_start = date.fromisoformat(
                                        lease['lease_start'])
                                    lease_end = date.fromisoformat(
                                        lease['lease_end'])
                                    # calculate the lease length
                                    diff = diff_month(lease_end, lease_start)
                                    # check if lease is at least an year long and today's date is before the lease ends
                                    if diff > 12 and today < lease_end:
                                        print('lease longer than 1 year')
                                        # create a charge date for 1 year from start date
                                        due_date = lease_start.replace(
                                            day=int(payment['due_by'])) + relativedelta(months=12)
                                        if len(payment['available_topay']) == 0:
                                            charge_date = due_date
                                        else:
                                            charge_date = due_date - \
                                                timedelta(
                                                    days=int(payment['available_topay']))
                                        charge_month = due_date.strftime(
                                            '%B')
                                        # check if today's date == the charge date
                                        if today == charge_date:
                                            # if yes, then enter the annual fees to the purchases table
                                            print('enter the fee to purchases')
                                            # if gross rent (listed rent)
                                            if payment['of'] == 'Gross Rent':
                                                print('payment of gross rent', (
                                                    int(payment['charge']) * int(rent))/100)
                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [lease['property_uid']]),
                                                    payer=payer,
                                                    receiver=lease['linked_business_id'],
                                                    purchase_type='RENT',
                                                    description=payment['fee_name'],
                                                    amount_due=(
                                                        int(payment['charge']) * int(rent))/100,
                                                    purchase_notes=charge_month,
                                                    purchase_date=lease['lease_start'],
                                                    purchase_frequency=payment['frequency'],
                                                    next_payment=due_date
                                                )
                                            # if net rent (listed rent-expenses)
                                            else:
                                                print('payment of net rent', (
                                                    int(payment['charge']) * (int(rent)))/100)
                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [lease['property_uid']]),
                                                    payer=payer,
                                                    receiver=lease['linked_business_id'],
                                                    purchase_type='RENT',
                                                    description=payment['fee_name'],
                                                    amount_due=(
                                                        int(payment['charge']) * (int(rent)))/100,
                                                    purchase_notes=charge_month,
                                                    purchase_date=lease['lease_start'],
                                                    purchase_frequency=payment['frequency'],
                                                    next_payment=due_date
                                                )
                                else:
                                    print('payment frequency one-time %')

                            elif payment['frequency'] == 'Move-Out Charge':
                                print(
                                    'payment fee purchase_type Move-Out Charge ')

                                print('payment frequency one-time $')
                                if today < lease_end:
                                    # get previous purchases
                                    if lease['prevPurchases'] != []:
                                        prevPurchaseDate = datetime.strptime(
                                            lease['prevPurchases'][-1]['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                        charge_month = (
                                            lease_end).strftime('%B')
                                        # due_date = lease_start.replace(
                                        #     day=int(payment['due_by'])) + relativedelta(months=1)

                                        due_date = lease_end
                                        if len(payment['available_topay']) == 0:
                                            charge_date = due_date
                                        else:
                                            charge_date = due_date - \
                                                timedelta(
                                                    days=int(payment['available_topay']))
                                        if charge_date == today:
                                            print(
                                                'enter the fee to purchases')
                                            purchaseResponse = newPurchase(
                                                linked_bill_id=None,
                                                pur_property_id=json.dumps(
                                                    [lease['property_uid']]),
                                                payer=payer,
                                                receiver=lease['linked_business_id'],
                                                purchase_type='EXTRA CHARGES',
                                                description=payment['fee_name'],
                                                amount_due=(
                                                    int(payment['charge']) * (int(rent)))/100,
                                                purchase_notes=charge_month,
                                                purchase_date=lease_start,
                                                purchase_frequency=payment['frequency'],
                                                next_payment=due_date
                                            )

                            elif payment['frequency'] == 'Move-in Charge':
                                print(
                                    'payment fee purchase_type EXTRA CHARGES')
                                print('skip')

                            else:
                                print(
                                    'payment fee purchase_type EXTRA CHARGES')
                                if payment['frequency'] == 'Weekly':
                                    print('payment frequency weekly %')
                                    lease_start = date.fromisoformat(
                                        lease['lease_start'])
                                    lease_end = date.fromisoformat(
                                        lease['lease_end'])
                                    # check if today's date is before lease end
                                    if today < lease_end:
                                        # get previous purchases
                                        if lease['prevPurchases'] != []:
                                            prevPurchaseDate = datetime.strptime(
                                                lease['prevPurchases'][-1]['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                            # set charge date as friday of every week
                                            due_date = next_weekday(
                                                prevPurchaseDate,  int(payment['due_by']))
                                            if len(payment['available_topay']) == 0:
                                                charge_date = due_date
                                            else:
                                                charge_date = due_date - \
                                                    timedelta(
                                                        days=int(payment['available_topay']))
                                            charge_month = due_date.strftime(
                                                '%B')
                                            print('due_date',
                                                  due_date, charge_month, charge_date)
                                            # if charge date == today then enter the monthly fee
                                            if charge_date == today:
                                                print(
                                                    'enter the fee to purchases')
                                                # if yes, then enter the monthly fees to the purchases table
                                                print(
                                                    'enter the fee to purchases')
                                                # if gross rent (listed rent)
                                                if payment['of'] == 'Gross Rent':
                                                    print('payment of gross rent', (
                                                        int(payment['charge']) * int(rent))/100)
                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [lease['property_uid']]),
                                                        payer=payer,
                                                        receiver=lease['linked_business_id'],
                                                        purchase_type='EXTRA CHARGES',
                                                        description=payment['fee_name'],
                                                        amount_due=(
                                                            int(payment['charge']) * int(rent))/100,
                                                        purchase_notes=charge_month,
                                                        purchase_date=lease['lease_start'],
                                                        purchase_frequency=payment['frequency'],
                                                        next_payment=due_date
                                                    )
                                                # if net rent (listed rent-expenses)
                                                else:
                                                    print('payment of net rent', (
                                                        int(payment['charge']) * (int(rent)))/100)
                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [lease['property_uid']]),
                                                        payer=payer,
                                                        receiver=lease['linked_business_id'],
                                                        purchase_type='EXTRA CHARGES',
                                                        description=payment['fee_name'],
                                                        amount_due=(
                                                            int(payment['charge']) * (int(rent)))/100,
                                                        purchase_notes=charge_month,
                                                        purchase_date=lease['lease_start'],
                                                        purchase_frequency=payment['frequency'],
                                                        next_payment=due_date
                                                    )
                                elif payment['frequency'] == 'Bwieekly':
                                    print('payment frequency biweekly %')
                                    lease_start = date.fromisoformat(
                                        lease['lease_start'])
                                    lease_end = date.fromisoformat(
                                        lease['lease_end'])
                                    # check if today's date is before lease end
                                    if today < lease_end:
                                        # get previous purchases
                                        if lease['prevPurchases'] != []:
                                            prevPurchaseDate = datetime.strptime(
                                                lease['prevPurchases'][-1]['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                            # set charge date as friday every two weeks
                                            due_date = next_weekday_biweekly(
                                                prevPurchaseDate,  int(payment['due_by']))
                                            if len(payment['available_topay']) == 0:
                                                charge_date = due_date
                                            else:
                                                charge_date = due_date - \
                                                    timedelta(
                                                        days=int(payment['available_topay']))
                                            charge_month = due_date.strftime(
                                                '%B')
                                            print('due_date',
                                                  due_date, charge_month, charge_date)
                                            # if charge date == today then enter the monthly fee
                                            if charge_date == today:
                                                print(
                                                    'enter the fee to purchases')
                                                # if yes, then enter the monthly fees to the purchases table
                                                print(
                                                    'enter the fee to purchases')
                                                # if gross rent (listed rent)
                                                if payment['of'] == 'Gross Rent':
                                                    print('payment of gross rent', (
                                                        int(payment['charge']) * int(rent))/100)
                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [lease['property_uid']]),
                                                        payer=payer,
                                                        receiver=lease['linked_business_id'],
                                                        purchase_type='EXTRA CHARGES',
                                                        description=payment['fee_name'],
                                                        amount_due=(
                                                            int(payment['charge']) * int(rent))/100,
                                                        purchase_notes=charge_month,
                                                        purchase_date=lease['lease_start'],
                                                        purchase_frequency=payment['frequency'],
                                                        next_payment=due_date
                                                    )
                                                # if net rent (listed rent-expenses)
                                                else:
                                                    print('payment of net rent', (
                                                        int(payment['charge']) * (int(rent)))/100)
                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [lease['property_uid']]),
                                                        payer=payer,
                                                        receiver=lease['linked_business_id'],
                                                        purchase_type='EXTRA CHARGES',
                                                        description=payment['fee_name'],
                                                        amount_due=(
                                                            int(payment['charge']) * (int(rent)))/100,
                                                        purchase_notes=charge_month,
                                                        purchase_date=lease['lease_start'],
                                                        purchase_frequency=payment['frequency'],
                                                        next_payment=due_date
                                                    )
                                elif payment['frequency'] == 'Monthly':
                                    print('payment frequency monthly %')
                                    lease_start = date.fromisoformat(
                                        lease['lease_start'])
                                    lease_end = date.fromisoformat(
                                        lease['lease_end'])
                                    # check if today's date is before lease end
                                    if today < lease_end:
                                        # get previous purchases
                                        if lease['prevPurchases'] != []:
                                            prevPurchaseDate = datetime.strptime(
                                                lease['prevPurchases'][-1]['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                            # set charge date as first of every month
                                            due_date = prevPurchaseDate.replace(
                                                day=int(payment['due_by'])) + relativedelta(months=1)
                                            if len(payment['available_topay']) == 0:
                                                charge_date = due_date
                                            else:
                                                charge_date = due_date - \
                                                    timedelta(
                                                        days=int(payment['available_topay']))
                                            charge_month = due_date.strftime(
                                                '%B')
                                            print('due_date',
                                                  due_date, charge_month, charge_date)
                                            # if charge date == today then enter the monthly fee
                                            if charge_date == today:
                                                print(
                                                    'enter the fee to purchases')
                                                # if yes, then enter the monthly fees to the purchases table
                                                print(
                                                    'enter the fee to purchases')
                                                # if gross rent (listed rent)
                                                if payment['of'] == 'Gross Rent':
                                                    print('payment of gross rent', (
                                                        int(payment['charge']) * int(rent))/100)
                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [lease['property_uid']]),
                                                        payer=payer,
                                                        receiver=lease['linked_business_id'],
                                                        purchase_type='EXTRA CHARGES',
                                                        description=payment['fee_name'],
                                                        amount_due=(
                                                            int(payment['charge']) * int(rent))/100,
                                                        purchase_notes=charge_month,
                                                        purchase_date=lease['lease_start'],
                                                        purchase_frequency=payment['frequency'],
                                                        next_payment=due_date
                                                    )
                                                # if net rent (listed rent-expenses)
                                                else:
                                                    print('payment of net rent', (
                                                        int(payment['charge']) * (int(rent)))/100)
                                                    purchaseResponse = newPurchase(
                                                        linked_bill_id=None,
                                                        pur_property_id=json.dumps(
                                                            [lease['property_uid']]),
                                                        payer=payer,
                                                        receiver=lease['linked_business_id'],
                                                        purchase_type='EXTRA CHARGES',
                                                        description=payment['fee_name'],
                                                        amount_due=(
                                                            int(payment['charge']) * (int(rent)))/100,
                                                        purchase_notes=charge_month,
                                                        purchase_date=lease['lease_start'],
                                                        purchase_frequency=payment['frequency'],
                                                        next_payment=due_date
                                                    )
                                elif payment['frequency'] == 'Annually':
                                    print('payment frequency annually %')
                                    lease_start = date.fromisoformat(
                                        lease['lease_start'])
                                    lease_end = date.fromisoformat(
                                        lease['lease_end'])
                                    # calculate the lease length
                                    diff = diff_month(lease_end, lease_start)
                                    # check if lease is at least an year long and today's date is before the lease ends
                                    if diff > 12 and today < lease_end:
                                        print('lease longer than 1 year')
                                        # create a charge date for 1 year from start date
                                        due_date = lease_start.replace(
                                            day=int(payment['due_by'])) + relativedelta(months=12)
                                        if len(payment['available_topay']) == 0:
                                            charge_date = due_date
                                        else:
                                            charge_date = due_date - \
                                                timedelta(
                                                    days=int(payment['available_topay']))
                                        charge_month = due_date.strftime(
                                            '%B')
                                        # check if today's date == the charge date
                                        if today == charge_date:
                                            # if yes, then enter the annual fees to the purchases table
                                            print('enter the fee to purchases')
                                            # if gross rent (listed rent)
                                            if payment['of'] == 'Gross Rent':
                                                print('payment of gross rent', (
                                                    int(payment['charge']) * int(rent))/100)
                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [lease['property_uid']]),
                                                    payer=payer,
                                                    receiver=lease['linked_business_id'],
                                                    purchase_type='EXTRA CHARGES',
                                                    description=payment['fee_name'],
                                                    amount_due=(
                                                        int(payment['charge']) * int(rent))/100,
                                                    purchase_notes=charge_month,
                                                    purchase_date=lease['lease_start'],
                                                    purchase_frequency=payment['frequency'],
                                                    next_payment=due_date
                                                )
                                            # if net rent (listed rent-expenses)
                                            else:
                                                print('payment of net rent', (
                                                    int(payment['charge']) * (int(rent)))/100)
                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [lease['property_uid']]),
                                                    payer=payer,
                                                    receiver=lease['linked_business_id'],
                                                    purchase_type='EXTRA CHARGES',
                                                    description=payment['fee_name'],
                                                    amount_due=(
                                                        int(payment['charge']) * (int(rent)))/100,
                                                    purchase_notes=charge_month,
                                                    purchase_date=lease['lease_start'],
                                                    purchase_frequency=payment['frequency'],
                                                    next_payment=due_date
                                                )
                                else:
                                    print('payment frequency one-time %')
        return response


def TenantPayments():
    print("In TenantPayments")
    from datetime import date, timedelta, datetime
    from dateutil.relativedelta import relativedelta
    from purchases import newPurchase

    with connect() as db:
        print("In Tenant Payments Function")
        response = {'message': 'Successfully committed SQL query',
                    'code': 200}
        payments = []
        response = db.execute("""SELECT r.*, prop.*, propM.*, 
                                GROUP_CONCAT(lt.linked_tenant_id) as `tenants` 
                                FROM rentals r
                                LEFT JOIN
                                pm.properties prop
                                ON prop.property_uid = r.rental_property_id
                                LEFT JOIN pm.leaseTenants lt
                                ON lt.linked_rental_uid = r.rental_uid
                                LEFT JOIN
                                pm.propertyManager propM
                                ON propM.linked_property_id = r.rental_property_id
                                WHERE r.rental_status = 'ACTIVE'
                                GROUP BY lt.linked_rental_uid;  """)

        # getting all the previous rental payments
        if len(response['result']) > 0:
            for i in range(len(response['result'])):
                response['result'][i]['expense_amount'] = 0
                purRes = db.execute("""SELECT * FROM purchases pur
                                        WHERE pur.pur_property_id LIKE '%""" + response['result'][i]['property_uid'] + """%'
                                        AND pur.purchase_type = 'RENT' OR pur.purchase_type= 'EXTRA CHARGES' """)
                print('purRes', purRes['result'])
                response['result'][i]['prevPurchases'] = list(
                    purRes['result'])
        if len(response['result']) > 0:
            # creating purchases
            rentPayments = json.loads(
                response['result'][0]['rent_payments'])
            for payment in rentPayments:
                if(payment['fee_name'] == 'Rent'):
                    rent = payment['charge']

        if len(response['result']) > 0:
            # today's date
            today = date.today()
            for lease in response['result']:
                # creating purchases
                tenantPayments = json.loads(lease['rent_payments'])
                payer = response['result'][0]['tenants'].split(',')
                payer = json.dumps(payer)
                for payment in tenantPayments:
                    # if fee_type is $, put the charge amount directly
                    if payment['fee_type'] == '$':
                        print('payment fee type $')
                        if(payment['fee_name'] == 'Rent'):
                            print('payment fee purchase_type RENT')
                            if payment['frequency'] == 'Weekly':
                                print('payment frequency weekly $')
                                lease_start = date.fromisoformat(
                                    lease['lease_start'])
                                lease_end = date.fromisoformat(
                                    lease['lease_end'])
                                # check if today's date is before lease end
                                if today < lease_end:
                                    # get previous purchases
                                    if lease['prevPurchases'] != []:
                                        prevPurchaseDate = datetime.strptime(
                                            lease['prevPurchases'][-1]['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                    # set charge date as friday of every week
                                        due_date = next_weekday(
                                            prevPurchaseDate,  int(payment['due_by']))
                                        if len(payment['available_topay']) == 0:
                                            charge_date = due_date
                                        else:
                                            charge_date = due_date - \
                                                timedelta(
                                                    days=int(payment['available_topay']))
                                        charge_month = due_date.strftime(
                                            '%B')
                                        print('due_date',
                                              due_date, charge_month, charge_date, charge_date)
                                        # if charge date == today then enter the monthly fee
                                        if charge_date == today:
                                            print(
                                                'enter the fee to purchases')

                                            purchaseResponse = newPurchase(
                                                linked_bill_id=None,
                                                pur_property_id=json.dumps(
                                                    [lease['property_uid']]),
                                                payer=payer,
                                                receiver=lease['linked_business_id'],
                                                purchase_type='RENT',
                                                description=payment['fee_name'],
                                                amount_due=payment['charge'],
                                                purchase_notes=charge_month,
                                                purchase_date=lease['lease_start'],
                                                purchase_frequency=payment['frequency'],
                                                next_payment=due_date
                                            )
                            elif payment['frequency'] == 'Biweekly':
                                print('payment frequency biweekly $')
                                lease_start = date.fromisoformat(
                                    lease['lease_start'])
                                lease_end = date.fromisoformat(
                                    lease['lease_end'])
                                # check if today's date is before lease end
                                if today < lease_end:
                                    # get previous purchases
                                    if lease['prevPurchases'] != []:
                                        prevPurchaseDate = datetime.strptime(
                                            lease['prevPurchases'][-1]['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                    # set charge date as friday of every 2 week
                                        due_date = next_weekday_biweekly(
                                            prevPurchaseDate,  int(payment['due_by']))
                                        if len(payment['available_topay']) == 0:
                                            charge_date = due_date
                                        else:
                                            charge_date = due_date - \
                                                timedelta(
                                                    days=int(payment['available_topay']))
                                        charge_month = due_date.strftime(
                                            '%B')
                                        print('due_date',
                                              due_date, charge_month, charge_date)
                                        # if charge date == today then enter the monthly fee
                                        if charge_date == today:
                                            print(
                                                'enter the fee to purchases')

                                            purchaseResponse = newPurchase(
                                                linked_bill_id=None,
                                                pur_property_id=json.dumps(
                                                    [lease['property_uid']]),
                                                payer=payer,
                                                receiver=lease['linked_business_id'],
                                                purchase_type='RENT',
                                                description=payment['fee_name'],
                                                amount_due=payment['charge'],
                                                purchase_notes=charge_month,
                                                purchase_date=lease['lease_start'],
                                                purchase_frequency=payment['frequency'],
                                                next_payment=due_date
                                            )
                            elif payment['frequency'] == 'Monthly':
                                print('payment frequency monthly $')
                                lease_start = date.fromisoformat(
                                    lease['lease_start'])
                                lease_end = date.fromisoformat(
                                    lease['lease_end'])
                                # check if today's date is before lease end
                                if today < lease_end:
                                    # get previous purchases
                                    if lease['prevPurchases'] != []:
                                        prevPurchaseDate = datetime.strptime(
                                            lease['prevPurchases'][-1]['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                        # set charge date as first of every month
                                        due_date = prevPurchaseDate.replace(
                                            day=int(payment['due_by'])) + relativedelta(months=1)
                                        if len(payment['available_topay']) == 0:
                                            charge_date = due_date
                                        else:
                                            charge_date = due_date - \
                                                timedelta(
                                                    days=int(payment['available_topay']))

                                        charge_month = due_date.strftime(
                                            '%B')
                                        print('due_date',
                                              due_date, charge_month, charge_date)
                                        # if charge date == today then enter the monthly fee
                                        if charge_date == today:
                                            print(
                                                'enter the fee to purchases')

                                            purchaseResponse = newPurchase(
                                                linked_bill_id=None,
                                                pur_property_id=json.dumps(
                                                    [lease['property_uid']]),
                                                payer=payer,
                                                receiver=lease['linked_business_id'],
                                                purchase_type='RENT',
                                                description=payment['fee_name'],
                                                amount_due=payment['charge'],
                                                purchase_notes=charge_month,
                                                purchase_date=lease['lease_start'],
                                                purchase_frequency=payment['frequency'],
                                                next_payment=due_date
                                            )

                            elif payment['frequency'] == 'Annually':
                                print('payment frequency annually $')
                                lease_start = date.fromisoformat(
                                    lease['lease_start'])
                                lease_end = date.fromisoformat(
                                    lease['lease_end'])
                                # calculate the lease length
                                diff = diff_month(lease_end, lease_start)
                                # check if lease is at least an year long and today's date is before the lease ends
                                if diff > 12 and today < lease_end:
                                    print('lease longer than 1 year')
                                    # create a charge date for 1 year from start date
                                    due_date = lease_start.replace(
                                        day=int(payment['due_by'])) + relativedelta(months=12)
                                    if len(payment['available_topay']) == 0:
                                        charge_date = due_date
                                    else:
                                        charge_date = due_date - \
                                            timedelta(
                                                days=int(payment['available_topay']))
                                    charge_month = due_date.strftime(
                                        '%B')
                                    # check if today's date == the charge date
                                    if today == charge_date:
                                        # if yes, then enter the annual fees to the purchases table
                                        print('enter the fee to purchases')

                                        purchaseResponse = newPurchase(
                                            linked_bill_id=None,
                                            pur_property_id=json.dumps(
                                                [lease['property_uid']]),
                                            payer=payer,
                                            receiver=lease['linked_business_id'],
                                            purchase_type='RENT',
                                            description=payment['fee_name'],
                                            amount_due=payment['charge'],
                                            purchase_notes=charge_month,
                                            purchase_date=lease['lease_start'],
                                            purchase_frequency=payment['frequency'],
                                            next_payment=due_date
                                        )
                            else:
                                print('payment frequency one-time $')
                        elif payment['frequency'] == 'Move-Out Charge':
                            print(
                                'payment fee purchase_type Move-Out Charge ')

                            print('payment frequency one-time $')
                            if today < lease_end:
                                # get previous purchases
                                if lease['prevPurchases'] != []:
                                    prevPurchaseDate = datetime.strptime(
                                        lease['prevPurchases'][-1]['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                    charge_month = (
                                        lease_end).strftime('%B')

                                    due_date = lease_end
                                    if len(payment['available_topay']) == 0:
                                        charge_date = due_date
                                    else:
                                        charge_date = due_date - \
                                            timedelta(
                                                days=int(payment['available_topay']))
                                    if charge_date == today:
                                        print(
                                            'enter the fee to purchases')
                                        purchaseResponse = newPurchase(
                                            linked_bill_id=None,
                                            pur_property_id=json.dumps(
                                                [lease['property_uid']]),
                                            payer=payer,
                                            receiver=lease['linked_business_id'],
                                            purchase_type='EXTRA CHARGES',
                                            description=payment['fee_name'],
                                            amount_due=payment['charge'],
                                            purchase_notes=charge_month,
                                            purchase_date=lease_start,
                                            purchase_frequency=payment['frequency'],
                                            next_payment=due_date
                                        )

                        elif payment['frequency'] == 'Move-in Charge':
                            print(
                                'payment fee purchase_type EXTRA CHARGES')
                            print('skip')

                        else:
                            print(
                                'payment fee purchase_type EXTRA CHARGES')
                            if payment['frequency'] == 'Weekly':
                                print('payment frequency weekly $')
                                lease_start = date.fromisoformat(
                                    lease['lease_start'])
                                lease_end = date.fromisoformat(
                                    lease['lease_end'])
                                # check if today's date is before lease end
                                if today < lease_end:
                                    # get previous purchases
                                    if lease['prevPurchases'] != []:
                                        prevPurchaseDate = datetime.strptime(
                                            lease['prevPurchases'][-1]['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                    # set charge date as friday of every week
                                        due_date = next_weekday(
                                            prevPurchaseDate,  int(payment['due_by']))
                                        if len(payment['available_topay']) == 0:
                                            charge_date = due_date
                                        else:
                                            charge_date = due_date - \
                                                timedelta(
                                                    days=int(payment['available_topay']))
                                        charge_month = due_date.strftime(
                                            '%B')
                                        print('due_date',
                                              due_date, charge_month, charge_date)
                                        # if charge date == today then enter the monthly fee
                                        if charge_date == today:
                                            print(
                                                'enter the fee to purchases')

                                            purchaseResponse = newPurchase(
                                                linked_bill_id=None,
                                                pur_property_id=json.dumps(
                                                    [lease['property_uid']]),
                                                payer=payer,
                                                receiver=lease['linked_business_id'],
                                                purchase_type='EXTRA CHARGES',
                                                description=payment['fee_name'],
                                                amount_due=payment['charge'],
                                                purchase_notes=charge_month,
                                                purchase_date=lease['lease_start'],
                                                purchase_frequency=payment['frequency'],
                                                next_payment=due_date
                                            )
                            elif payment['frequency'] == 'Biweekly':
                                print('payment frequency biweekly $')
                                lease_start = date.fromisoformat(
                                    lease['lease_start'])
                                lease_end = date.fromisoformat(
                                    lease['lease_end'])
                                # check if today's date is before lease end
                                if today < lease_end:
                                    # get previous purchases
                                    if lease['prevPurchases'] != []:
                                        prevPurchaseDate = datetime.strptime(
                                            lease['prevPurchases'][-1]['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                    # set charge date as friday of every 2 week
                                        due_date = next_weekday_biweekly(
                                            prevPurchaseDate,  int(payment['due_by']))
                                        if len(payment['available_topay']) == 0:
                                            charge_date = due_date
                                        else:
                                            charge_date = due_date - \
                                                timedelta(
                                                    days=int(payment['available_topay']))
                                        charge_month = due_date.strftime(
                                            '%B')
                                        print('due_date',
                                              due_date, charge_month, charge_date)
                                        # if charge date == today then enter the monthly fee
                                        if charge_date == today:
                                            print(
                                                'enter the fee to purchases')

                                            purchaseResponse = newPurchase(
                                                linked_bill_id=None,
                                                pur_property_id=json.dumps(
                                                    [lease['property_uid']]),
                                                payer=payer,
                                                receiver=lease['linked_business_id'],
                                                purchase_type='EXTRA CHARGES',
                                                description=payment['fee_name'],
                                                amount_due=payment['charge'],
                                                purchase_notes=charge_month,
                                                purchase_date=lease['lease_start'],
                                                purchase_frequency=payment['frequency'],
                                                next_payment=due_date
                                            )
                            elif payment['frequency'] == 'Monthly':
                                print('payment frequency monthly $')
                                lease_start = date.fromisoformat(
                                    lease['lease_start'])
                                lease_end = date.fromisoformat(
                                    lease['lease_end'])
                                # check if today's date is before lease end
                                if today < lease_end:
                                    # get previous purchases
                                    if lease['prevPurchases'] != []:
                                        prevPurchaseDate = datetime.strptime(
                                            lease['prevPurchases'][-1]['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                        # set charge date as first of every month
                                        due_date = prevPurchaseDate.replace(
                                            day=int(payment['due_by'])) + relativedelta(months=1)
                                        if len(payment['available_topay']) == 0:
                                            charge_date = due_date
                                        else:
                                            charge_date = due_date - \
                                                timedelta(
                                                    days=int(payment['available_topay']))
                                        charge_month = due_date.strftime(
                                            '%B')
                                        print('due_date',
                                              due_date, charge_month, charge_date)
                                        # if charge date == today then enter the monthly fee
                                        if charge_date == today:
                                            print(
                                                'enter the fee to purchases')

                                            purchaseResponse = newPurchase(
                                                linked_bill_id=None,
                                                pur_property_id=json.dumps(
                                                    [lease['property_uid']]),
                                                payer=payer,
                                                receiver=lease['linked_business_id'],
                                                purchase_type='EXTRA CHARGES',
                                                description=payment['fee_name'],
                                                amount_due=payment['charge'],
                                                purchase_notes=charge_month,
                                                purchase_date=lease['lease_start'],
                                                purchase_frequency=payment['frequency'],
                                                next_payment=due_date
                                            )

                            elif payment['frequency'] == 'Annually':
                                print('payment frequency annually $')
                                lease_start = date.fromisoformat(
                                    lease['lease_start'])
                                lease_end = date.fromisoformat(
                                    lease['lease_end'])
                                # calculate the lease length
                                diff = diff_month(lease_end, lease_start)
                                # check if lease is at least an year long and today's date is before the lease ends
                                if diff > 12 and today < lease_end:
                                    print('lease longer than 1 year')
                                    # create a charge date for 1 year from start date
                                    due_date = lease_start.replace(
                                        day=int(payment['due_by'])) + relativedelta(months=12)
                                    if len(payment['available_topay']) == 0:
                                        charge_date = due_date
                                    else:
                                        charge_date = due_date - \
                                            timedelta(
                                                days=int(payment['available_topay']))
                                    charge_month = due_date.strftime(
                                        '%B')
                                    # check if today's date == the charge date
                                    if today == charge_date:
                                        # if yes, then enter the annual fees to the purchases table
                                        print('enter the fee to purchases')

                                        purchaseResponse = newPurchase(
                                            linked_bill_id=None,
                                            pur_property_id=json.dumps(
                                                [lease['property_uid']]),
                                            payer=payer,
                                            receiver=lease['linked_business_id'],
                                            purchase_type='EXTRA CHARGES',
                                            description=payment['fee_name'],
                                            amount_due=payment['charge'],
                                            purchase_notes=charge_month,
                                            purchase_date=lease['lease_start'],
                                            purchase_frequency=payment['frequency'],
                                            next_payment=due_date
                                        )
                            else:
                                print('payment frequency one-time $')
                    # if fee_type is %, we check for the gross rent or net and calculate the charge according to that
                    else:
                        print('payment fee type %')
                        if(payment['fee_name'] == 'Rent'):
                            print('payment fee purchase_type RENT')
                            if payment['frequency'] == 'Weekly':
                                print('payment frequency weekly %')
                                lease_start = date.fromisoformat(
                                    lease['lease_start'])
                                lease_end = date.fromisoformat(
                                    lease['lease_end'])
                                # check if today's date is before lease end
                                if today < lease_end:
                                    # get previous purchases
                                    if lease['prevPurchases'] != []:
                                        prevPurchaseDate = datetime.strptime(
                                            lease['prevPurchases'][-1]['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                        # set charge date as friday of every week
                                        due_date = next_weekday(
                                            prevPurchaseDate,  int(payment['due_by']))
                                        if len(payment['available_topay']) == 0:
                                            charge_date = due_date
                                        else:
                                            charge_date = due_date - \
                                                timedelta(
                                                    days=int(payment['available_topay']))
                                        charge_month = due_date.strftime(
                                            '%B')
                                        print('due_date',
                                              due_date, charge_month, charge_date)
                                        # if charge date == today then enter the monthly fee
                                        if charge_date == today:
                                            print(
                                                'enter the fee to purchases')
                                            # if yes, then enter the monthly fees to the purchases table
                                            print(
                                                'enter the fee to purchases')
                                            # if gross rent (listed rent)
                                            if payment['of'] == 'Gross Rent':
                                                print('payment of gross rent', (
                                                    int(payment['charge']) * int(rent))/100)
                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [lease['property_uid']]),
                                                    payer=payer,
                                                    receiver=lease['linked_business_id'],
                                                    purchase_type='RENT',
                                                    description=payment['fee_name'],
                                                    amount_due=(
                                                        int(payment['charge']) * int(rent))/100,
                                                    purchase_notes=charge_month,
                                                    purchase_date=lease['lease_start'],
                                                    purchase_frequency=payment['frequency'],
                                                    next_payment=due_date
                                                )
                                            # if net rent (listed rent-expenses)
                                            else:
                                                print('payment of net rent', (
                                                    int(payment['charge']) * (int(rent)))/100)
                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [lease['property_uid']]),
                                                    payer=payer,
                                                    receiver=lease['linked_business_id'],
                                                    purchase_type='RENT',
                                                    description=payment['fee_name'],
                                                    amount_due=(
                                                        int(payment['charge']) * (int(rent)))/100,
                                                    purchase_notes=charge_month,
                                                    purchase_date=lease['lease_start'],
                                                    purchase_frequency=payment['frequency'],
                                                    next_payment=due_date
                                                )
                            elif payment['frequency'] == 'Bwieekly':
                                print('payment frequency biweekly %')
                                lease_start = date.fromisoformat(
                                    lease['lease_start'])
                                lease_end = date.fromisoformat(
                                    lease['lease_end'])
                                # check if today's date is before lease end
                                if today < lease_end:
                                    # get previous purchases
                                    if lease['prevPurchases'] != []:
                                        prevPurchaseDate = datetime.strptime(
                                            lease['prevPurchases'][-1]['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                        # set charge date as friday every two weeks
                                        due_date = next_weekday_biweekly(
                                            prevPurchaseDate,  int(payment['due_by']))
                                        if len(payment['available_topay']) == 0:
                                            charge_date = due_date
                                        else:
                                            charge_date = due_date - \
                                                timedelta(
                                                    days=int(payment['available_topay']))
                                        charge_month = due_date.strftime(
                                            '%B')
                                        print('due_date',
                                              due_date, charge_month, charge_date)
                                        # if charge date == today then enter the monthly fee
                                        if charge_date == today:
                                            print(
                                                'enter the fee to purchases')
                                            # if yes, then enter the monthly fees to the purchases table
                                            print(
                                                'enter the fee to purchases')
                                            # if gross rent (listed rent)
                                            if payment['of'] == 'Gross Rent':
                                                print('payment of gross rent', (
                                                    int(payment['charge']) * int(rent))/100)
                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [lease['property_uid']]),
                                                    payer=payer,
                                                    receiver=lease['linked_business_id'],
                                                    purchase_type='RENT',
                                                    description=payment['fee_name'],
                                                    amount_due=(
                                                        int(payment['charge']) * int(rent))/100,
                                                    purchase_notes=charge_month,
                                                    purchase_date=lease['lease_start'],
                                                    purchase_frequency=payment['frequency'],
                                                    next_payment=due_date
                                                )
                                            # if net rent (listed rent-expenses)
                                            else:
                                                print('payment of net rent', (
                                                    int(payment['charge']) * (int(rent)))/100)
                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [lease['property_uid']]),
                                                    payer=payer,
                                                    receiver=lease['linked_business_id'],
                                                    purchase_type='RENT',
                                                    description=payment['fee_name'],
                                                    amount_due=(
                                                        int(payment['charge']) * (int(rent)))/100,
                                                    purchase_notes=charge_month,
                                                    purchase_date=lease['lease_start'],
                                                    purchase_frequency=payment['frequency'],
                                                    next_payment=due_date
                                                )
                            elif payment['frequency'] == 'Monthly':
                                print('payment frequency monthly %')
                                lease_start = date.fromisoformat(
                                    lease['lease_start'])
                                lease_end = date.fromisoformat(
                                    lease['lease_end'])
                                # check if today's date is before lease end
                                if today < lease_end:
                                    # get previous purchases
                                    if lease['prevPurchases'] != []:
                                        prevPurchaseDate = datetime.strptime(
                                            lease['prevPurchases'][-1]['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                        # set charge date as first of every month
                                        due_date = prevPurchaseDate.replace(
                                            day=int(payment['due_by'])) + relativedelta(months=1)
                                        if len(payment['available_topay']) == 0:
                                            charge_date = due_date
                                        else:
                                            charge_date = due_date - \
                                                timedelta(
                                                    days=int(payment['available_topay']))
                                        charge_month = due_date.strftime(
                                            '%B')
                                        print('due_date',
                                              due_date, charge_month, charge_date)
                                        # if charge date == today then enter the monthly fee
                                        if charge_date == today:
                                            print(
                                                'enter the fee to purchases')
                                            # if yes, then enter the monthly fees to the purchases table
                                            print(
                                                'enter the fee to purchases')
                                            # if gross rent (listed rent)
                                            if payment['of'] == 'Gross Rent':
                                                print('payment of gross rent', (
                                                    int(payment['charge']) * int(rent))/100)
                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [lease['property_uid']]),
                                                    payer=payer,
                                                    receiver=lease['linked_business_id'],
                                                    purchase_type='RENT',
                                                    description=payment['fee_name'],
                                                    amount_due=(
                                                        int(payment['charge']) * int(rent))/100,
                                                    purchase_notes=charge_month,
                                                    purchase_date=lease['lease_start'],
                                                    purchase_frequency=payment['frequency'],
                                                    next_payment=due_date
                                                )
                                            # if net rent (listed rent-expenses)
                                            else:
                                                print('payment of net rent', (
                                                    int(payment['charge']) * (int(rent)))/100)
                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [lease['property_uid']]),
                                                    payer=payer,
                                                    receiver=lease['linked_business_id'],
                                                    purchase_type='RENT',
                                                    description=payment['fee_name'],
                                                    amount_due=(
                                                        int(payment['charge']) * (int(rent)))/100,
                                                    purchase_notes=charge_month,
                                                    purchase_date=lease['lease_start'],
                                                    purchase_frequency=payment['frequency'],
                                                    next_payment=due_date
                                                )
                            elif payment['frequency'] == 'Annually':
                                print('payment frequency annually %')
                                lease_start = date.fromisoformat(
                                    lease['lease_start'])
                                lease_end = date.fromisoformat(
                                    lease['lease_end'])
                                # calculate the lease length
                                diff = diff_month(lease_end, lease_start)
                                # check if lease is at least an year long and today's date is before the lease ends
                                if diff > 12 and today < lease_end:
                                    print('lease longer than 1 year')
                                    # create a charge date for 1 year from start date
                                    due_date = lease_start.replace(
                                        day=int(payment['due_by'])) + relativedelta(months=12)
                                    if len(payment['available_topay']) == 0:
                                        charge_date = due_date
                                    else:
                                        charge_date = due_date - \
                                            timedelta(
                                                days=int(payment['available_topay']))
                                    charge_month = due_date.strftime(
                                        '%B')
                                    # check if today's date == the charge date
                                    if today == charge_date:
                                        # if yes, then enter the annual fees to the purchases table
                                        print('enter the fee to purchases')
                                        # if gross rent (listed rent)
                                        if payment['of'] == 'Gross Rent':
                                            print('payment of gross rent', (
                                                int(payment['charge']) * int(rent))/100)
                                            purchaseResponse = newPurchase(
                                                linked_bill_id=None,
                                                pur_property_id=json.dumps(
                                                    [lease['property_uid']]),
                                                payer=payer,
                                                receiver=lease['linked_business_id'],
                                                purchase_type='RENT',
                                                description=payment['fee_name'],
                                                amount_due=(
                                                    int(payment['charge']) * int(rent))/100,
                                                purchase_notes=charge_month,
                                                purchase_date=lease['lease_start'],
                                                purchase_frequency=payment['frequency'],
                                                next_payment=due_date
                                            )
                                        # if net rent (listed rent-expenses)
                                        else:
                                            print('payment of net rent', (
                                                int(payment['charge']) * (int(rent)))/100)
                                            purchaseResponse = newPurchase(
                                                linked_bill_id=None,
                                                pur_property_id=json.dumps(
                                                    [lease['property_uid']]),
                                                payer=payer,
                                                receiver=lease['linked_business_id'],
                                                purchase_type='RENT',
                                                description=payment['fee_name'],
                                                amount_due=(
                                                    int(payment['charge']) * (int(rent)))/100,
                                                purchase_notes=charge_month,
                                                purchase_date=lease['lease_start'],
                                                purchase_frequency=payment['frequency'],
                                                next_payment=due_date
                                            )
                            else:
                                print('payment frequency one-time %')

                        elif payment['frequency'] == 'Move-Out Charge':
                            print(
                                'payment fee purchase_type Move-Out Charge ')

                            print('payment frequency one-time $')
                            if today < lease_end:
                                # get previous purchases
                                if lease['prevPurchases'] != []:
                                    prevPurchaseDate = datetime.strptime(
                                        lease['prevPurchases'][-1]['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                    charge_month = (
                                        lease_end).strftime('%B')
                                    # due_date = lease_start.replace(
                                    #     day=int(payment['due_by'])) + relativedelta(months=1)

                                    due_date = lease_end
                                    if len(payment['available_topay']) == 0:
                                        charge_date = due_date
                                    else:
                                        charge_date = due_date - \
                                            timedelta(
                                                days=int(payment['available_topay']))
                                    if charge_date == today:
                                        print(
                                            'enter the fee to purchases')
                                        purchaseResponse = newPurchase(
                                            linked_bill_id=None,
                                            pur_property_id=json.dumps(
                                                [lease['property_uid']]),
                                            payer=payer,
                                            receiver=lease['linked_business_id'],
                                            purchase_type='EXTRA CHARGES',
                                            description=payment['fee_name'],
                                            amount_due=(
                                                int(payment['charge']) * (int(rent)))/100,
                                            purchase_notes=charge_month,
                                            purchase_date=lease_start,
                                            purchase_frequency=payment['frequency'],
                                            next_payment=due_date
                                        )

                        elif payment['frequency'] == 'Move-in Charge':
                            print(
                                'payment fee purchase_type EXTRA CHARGES')
                            print('skip')

                        else:
                            print(
                                'payment fee purchase_type EXTRA CHARGES')
                            if payment['frequency'] == 'Weekly':
                                print('payment frequency weekly %')
                                lease_start = date.fromisoformat(
                                    lease['lease_start'])
                                lease_end = date.fromisoformat(
                                    lease['lease_end'])
                                # check if today's date is before lease end
                                if today < lease_end:
                                    # get previous purchases
                                    if lease['prevPurchases'] != []:
                                        prevPurchaseDate = datetime.strptime(
                                            lease['prevPurchases'][-1]['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                        # set charge date as friday of every week
                                        due_date = next_weekday(
                                            prevPurchaseDate,  int(payment['due_by']))
                                        if len(payment['available_topay']) == 0:
                                            charge_date = due_date
                                        else:
                                            charge_date = due_date - \
                                                timedelta(
                                                    days=int(payment['available_topay']))
                                        charge_month = due_date.strftime(
                                            '%B')
                                        print('due_date',
                                              due_date, charge_month, charge_date)
                                        # if charge date == today then enter the monthly fee
                                        if charge_date == today:
                                            print(
                                                'enter the fee to purchases')
                                            # if yes, then enter the monthly fees to the purchases table
                                            print(
                                                'enter the fee to purchases')
                                            # if gross rent (listed rent)
                                            if payment['of'] == 'Gross Rent':
                                                print('payment of gross rent', (
                                                    int(payment['charge']) * int(rent))/100)
                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [lease['property_uid']]),
                                                    payer=payer,
                                                    receiver=lease['linked_business_id'],
                                                    purchase_type='EXTRA CHARGES',
                                                    description=payment['fee_name'],
                                                    amount_due=(
                                                        int(payment['charge']) * int(rent))/100,
                                                    purchase_notes=charge_month,
                                                    purchase_date=lease['lease_start'],
                                                    purchase_frequency=payment['frequency'],
                                                    next_payment=due_date
                                                )
                                            # if net rent (listed rent-expenses)
                                            else:
                                                print('payment of net rent', (
                                                    int(payment['charge']) * (int(rent)))/100)
                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [lease['property_uid']]),
                                                    payer=payer,
                                                    receiver=lease['linked_business_id'],
                                                    purchase_type='EXTRA CHARGES',
                                                    description=payment['fee_name'],
                                                    amount_due=(
                                                        int(payment['charge']) * (int(rent)))/100,
                                                    purchase_notes=charge_month,
                                                    purchase_date=lease['lease_start'],
                                                    purchase_frequency=payment['frequency'],
                                                    next_payment=due_date
                                                )
                            elif payment['frequency'] == 'Bwieekly':
                                print('payment frequency biweekly %')
                                lease_start = date.fromisoformat(
                                    lease['lease_start'])
                                lease_end = date.fromisoformat(
                                    lease['lease_end'])
                                # check if today's date is before lease end
                                if today < lease_end:
                                    # get previous purchases
                                    if lease['prevPurchases'] != []:
                                        prevPurchaseDate = datetime.strptime(
                                            lease['prevPurchases'][-1]['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                        # set charge date as friday every two weeks
                                        due_date = next_weekday_biweekly(
                                            prevPurchaseDate,  int(payment['due_by']))
                                        if len(payment['available_topay']) == 0:
                                            charge_date = due_date
                                        else:
                                            charge_date = due_date - \
                                                timedelta(
                                                    days=int(payment['available_topay']))
                                        charge_month = due_date.strftime(
                                            '%B')
                                        print('due_date',
                                              due_date, charge_month, charge_date)
                                        # if charge date == today then enter the monthly fee
                                        if charge_date == today:
                                            print(
                                                'enter the fee to purchases')
                                            # if yes, then enter the monthly fees to the purchases table
                                            print(
                                                'enter the fee to purchases')
                                            # if gross rent (listed rent)
                                            if payment['of'] == 'Gross Rent':
                                                print('payment of gross rent', (
                                                    int(payment['charge']) * int(rent))/100)
                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [lease['property_uid']]),
                                                    payer=payer,
                                                    receiver=lease['linked_business_id'],
                                                    purchase_type='EXTRA CHARGES',
                                                    description=payment['fee_name'],
                                                    amount_due=(
                                                        int(payment['charge']) * int(rent))/100,
                                                    purchase_notes=charge_month,
                                                    purchase_date=lease['lease_start'],
                                                    purchase_frequency=payment['frequency'],
                                                    next_payment=due_date
                                                )
                                            # if net rent (listed rent-expenses)
                                            else:
                                                print('payment of net rent', (
                                                    int(payment['charge']) * (int(rent)))/100)
                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [lease['property_uid']]),
                                                    payer=payer,
                                                    receiver=lease['linked_business_id'],
                                                    purchase_type='EXTRA CHARGES',
                                                    description=payment['fee_name'],
                                                    amount_due=(
                                                        int(payment['charge']) * (int(rent)))/100,
                                                    purchase_notes=charge_month,
                                                    purchase_date=lease['lease_start'],
                                                    purchase_frequency=payment['frequency'],
                                                    next_payment=due_date
                                                )
                            elif payment['frequency'] == 'Monthly':
                                print('payment frequency monthly %')
                                lease_start = date.fromisoformat(
                                    lease['lease_start'])
                                lease_end = date.fromisoformat(
                                    lease['lease_end'])
                                # check if today's date is before lease end
                                if today < lease_end:
                                    # get previous purchases
                                    if lease['prevPurchases'] != []:
                                        prevPurchaseDate = datetime.strptime(
                                            lease['prevPurchases'][-1]['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                        # set charge date as first of every month
                                        due_date = prevPurchaseDate.replace(
                                            day=int(payment['due_by'])) + relativedelta(months=1)
                                        if len(payment['available_topay']) == 0:
                                            charge_date = due_date
                                        else:
                                            charge_date = due_date - \
                                                timedelta(
                                                    days=int(payment['available_topay']))
                                        charge_month = due_date.strftime(
                                            '%B')
                                        print('due_date',
                                              due_date, charge_month, charge_date)
                                        # if charge date == today then enter the monthly fee
                                        if charge_date == today:
                                            print(
                                                'enter the fee to purchases')
                                            # if yes, then enter the monthly fees to the purchases table
                                            print(
                                                'enter the fee to purchases')
                                            # if gross rent (listed rent)
                                            if payment['of'] == 'Gross Rent':
                                                print('payment of gross rent', (
                                                    int(payment['charge']) * int(rent))/100)
                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [lease['property_uid']]),
                                                    payer=payer,
                                                    receiver=lease['linked_business_id'],
                                                    purchase_type='EXTRA CHARGES',
                                                    description=payment['fee_name'],
                                                    amount_due=(
                                                        int(payment['charge']) * int(rent))/100,
                                                    purchase_notes=charge_month,
                                                    purchase_date=lease['lease_start'],
                                                    purchase_frequency=payment['frequency'],
                                                    next_payment=due_date
                                                )
                                            # if net rent (listed rent-expenses)
                                            else:
                                                print('payment of net rent', (
                                                    int(payment['charge']) * (int(rent)))/100)
                                                purchaseResponse = newPurchase(
                                                    linked_bill_id=None,
                                                    pur_property_id=json.dumps(
                                                        [lease['property_uid']]),
                                                    payer=payer,
                                                    receiver=lease['linked_business_id'],
                                                    purchase_type='EXTRA CHARGES',
                                                    description=payment['fee_name'],
                                                    amount_due=(
                                                        int(payment['charge']) * (int(rent)))/100,
                                                    purchase_notes=charge_month,
                                                    purchase_date=lease['lease_start'],
                                                    purchase_frequency=payment['frequency'],
                                                    next_payment=due_date
                                                )
                            elif payment['frequency'] == 'Annually':
                                print('payment frequency annually %')
                                lease_start = date.fromisoformat(
                                    lease['lease_start'])
                                lease_end = date.fromisoformat(
                                    lease['lease_end'])
                                # calculate the lease length
                                diff = diff_month(lease_end, lease_start)
                                # check if lease is at least an year long and today's date is before the lease ends
                                if diff > 12 and today < lease_end:
                                    print('lease longer than 1 year')
                                    # create a charge date for 1 year from start date
                                    due_date = lease_start.replace(
                                        day=int(payment['due_by'])) + relativedelta(months=12)
                                    if len(payment['available_topay']) == 0:
                                        charge_date = due_date
                                    else:
                                        charge_date = due_date - \
                                            timedelta(
                                                days=int(payment['available_topay']))
                                    charge_month = due_date.strftime(
                                        '%B')
                                    # check if today's date == the charge date
                                    if today == charge_date:
                                        # if yes, then enter the annual fees to the purchases table
                                        print('enter the fee to purchases')
                                        # if gross rent (listed rent)
                                        if payment['of'] == 'Gross Rent':
                                            print('payment of gross rent', (
                                                int(payment['charge']) * int(rent))/100)
                                            purchaseResponse = newPurchase(
                                                linked_bill_id=None,
                                                pur_property_id=json.dumps(
                                                    [lease['property_uid']]),
                                                payer=payer,
                                                receiver=lease['linked_business_id'],
                                                purchase_type='EXTRA CHARGES',
                                                description=payment['fee_name'],
                                                amount_due=(
                                                    int(payment['charge']) * int(rent))/100,
                                                purchase_notes=charge_month,
                                                purchase_date=lease['lease_start'],
                                                purchase_frequency=payment['frequency'],
                                                next_payment=due_date
                                            )
                                        # if net rent (listed rent-expenses)
                                        else:
                                            print('payment of net rent', (
                                                int(payment['charge']) * (int(rent)))/100)
                                            purchaseResponse = newPurchase(
                                                linked_bill_id=None,
                                                pur_property_id=json.dumps(
                                                    [lease['property_uid']]),
                                                payer=payer,
                                                receiver=lease['linked_business_id'],
                                                purchase_type='EXTRA CHARGES',
                                                description=payment['fee_name'],
                                                amount_due=(
                                                    int(payment['charge']) * (int(rent)))/100,
                                                purchase_notes=charge_month,
                                                purchase_date=lease['lease_start'],
                                                purchase_frequency=payment['frequency'],
                                                next_payment=due_date
                                            )
                            else:
                                print('payment frequency one-time %')
    return response
