
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from data import connect
from datetime import date, timedelta, datetime
from calendar import monthrange
import json
from dateutil.relativedelta import relativedelta
from purchases import newPurchase


class ManagerProperties(Resource):
    decorators = [jwt_required()]

    def get(self):
        response = {}
        user = get_jwt_identity()
        with connect() as db:
            response = db.select('employees', where={
                'user_uid': user['user_uid']
            })
            if len(response['result'] == 0):
                return response
            business_uid = response['result'][0]['business_uid']
            response = db.select('propertyInfo', where={
                'manager_id': business_uid
            })
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


class ManagerContractFees_CLASS(Resource):
    def get(self):
        response = {}
        with connect() as db:
            payments = []
            response = db.execute("""SELECT * FROM contracts c
                                    LEFT JOIN
                                    pm.properties prop
                                    ON prop.property_uid = c.property_uid
                                    LEFT JOIN
                                    pm.propertyManager propM
                                    ON propM.linked_property_id = c.property_uid
                                    WHERE c.contract_status = 'ACTIVE' 
                                    AND propM.management_status = 'ACCEPTED'  """)

            # getting all the expenses and calculating the expense amount
            if len(response['result']) > 0:
                for i in range(len(response['result'])):
                    response['result'][i]['expense_amount'] = 0
                    purRes = db.execute("""SELECT * FROM purchases pur
                                           WHERE pur.pur_property_id= \'""" + response['result'][i]['property_uid'] + """\'
                                           AND (pur.purchase_type = 'UTILITY' OR pur.purchase_type = 'MAINTENANCE' OR pur.purchase_type = 'REPAIRS') """)
                    response['result'][i]['expenses'] = list(purRes['result'])
                    if len(purRes['result']) > 0:
                        for ore in range(len(purRes['result'])):
                            response['result'][i]['expense_amount'] = response['result'][i]['expense_amount'] + int(
                                purRes['result'][ore]['amount_due'])
             # getting all the previous management purchases
            if len(response['result']) > 0:
                for i in range(len(response['result'])):
                    response['result'][i]['expense_amount'] = 0
                    purRes = db.execute("""SELECT * FROM purchases pur
                                           WHERE pur.pur_property_id= \'""" + response['result'][i]['property_uid'] + """\'
                                           AND pur.purchase_type = 'MANAGEMENT' """)
                    response['result'][i]['prevPurchases'] = list(
                        purRes['result'])

            if len(response['result']) > 0:
                # today's date
                today = date.today()
                for contract in response['result']:
                    # creating purchases
                    managementPayments = json.loads(contract['contract_fees'])
                    payer = contract['owner_id']
                    if '[' in payer:
                        payer = json.loads(payer)
                    if type(payer) == str:
                        payer = [payer]
                    payer = json.dumps(payer)
                    for payment in managementPayments:
                        # if fee_type is $, put the charge amount directly
                        if payment['fee_type'] == '$':
                            print('payment fee type $')
                            if payment['frequency'] == 'Weekly':
                                print('payment frequency weekly $')
                                start_date = date.fromisoformat(
                                    contract['start_date'])
                                end_date = date.fromisoformat(
                                    contract['end_date'])
                                # check if today's date is before contract end
                                if today < end_date:
                                    # get previous purchases
                                    if contract['prevPurchases'] != []:
                                        prevPurchaseDate = datetime.strptime(
                                            contract['prevPurchases'][-1]['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                       # set charge date as friday of every week
                                        charge_date = next_weekday(
                                            prevPurchaseDate, 4)
                                        charge_month = charge_date.strftime(
                                            '%B')
                                        print('charge_date',
                                              charge_date, charge_month)
                                        # if charge date == today then enter the monthly fee
                                        if charge_date == today:
                                            print('enter the fee to purchases')

                                            purchaseResponse = newPurchase(
                                                linked_bill_id=None,
                                                pur_property_id=contract['property_uid'],
                                                payer=payer,
                                                receiver=contract['business_uid'],
                                                purchase_type='MANAGEMENT',
                                                description=payment['fee_name'],
                                                amount_due=payment['charge'],
                                                purchase_notes=charge_month,
                                                purchase_date=contract['start_date'],
                                                purchase_frequency=payment['frequency'],
                                                next_payment=charge_date
                                            )
                            elif payment['frequency'] == 'Bieekly':
                                print('payment frequency biweekly $')
                                start_date = date.fromisoformat(
                                    contract['start_date'])
                                end_date = date.fromisoformat(
                                    contract['end_date'])
                                # check if today's date is before contract end
                                if today < end_date:
                                    # get previous purchases
                                    if contract['prevPurchases'] != []:
                                        prevPurchaseDate = datetime.strptime(
                                            contract['prevPurchases'][-1]['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                       # set charge date as friday of every 2 week
                                        charge_date = next_weekday_biweekly(
                                            prevPurchaseDate, 4)
                                        charge_month = charge_date.strftime(
                                            '%B')
                                        print('charge_date',
                                              charge_date, charge_month)
                                        # if charge date == today then enter the monthly fee
                                        if charge_date == today:
                                            print('enter the fee to purchases')

                                            purchaseResponse = newPurchase(
                                                linked_bill_id=None,
                                                pur_property_id=contract['property_uid'],
                                                payer=payer,
                                                receiver=contract['business_uid'],
                                                purchase_type='MANAGEMENT',
                                                description=payment['fee_name'],
                                                amount_due=payment['charge'],
                                                purchase_notes=charge_month,
                                                purchase_date=contract['start_date'],
                                                purchase_frequency=payment['frequency'],
                                                next_payment=charge_date
                                            )
                            elif payment['frequency'] == 'Monthly':
                                print('payment frequency monthly $')
                                start_date = date.fromisoformat(
                                    contract['start_date'])
                                end_date = date.fromisoformat(
                                    contract['end_date'])
                                # check if today's date is before contract end
                                if today < end_date:
                                    # get previous purchases
                                    if contract['prevPurchases'] != []:
                                        prevPurchaseDate = datetime.strptime(
                                            contract['prevPurchases'][-1]['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                        # set charge date as first of every month
                                        charge_date = prevPurchaseDate.replace(
                                            day=1) + relativedelta(months=1)
                                        charge_month = charge_date.strftime(
                                            '%B')
                                        print('charge_date',
                                              charge_date, charge_month)
                                        # if charge date == today then enter the monthly fee
                                        if charge_date == today:
                                            print('enter the fee to purchases')

                                            purchaseResponse = newPurchase(
                                                linked_bill_id=None,
                                                pur_property_id=contract['property_uid'],
                                                payer=payer,
                                                receiver=contract['business_uid'],
                                                purchase_type='MANAGEMENT',
                                                description=payment['fee_name'],
                                                amount_due=payment['charge'],
                                                purchase_notes=charge_month,
                                                purchase_date=contract['start_date'],
                                                purchase_frequency=payment['frequency'],
                                                next_payment=charge_date
                                            )

                            elif payment['frequency'] == 'Annually':
                                print('payment frequency annually $')
                                start_date = date.fromisoformat(
                                    contract['start_date'])
                                end_date = date.fromisoformat(
                                    contract['end_date'])
                                # calculate the contract length
                                diff = diff_month(end_date, start_date)
                                # check if contract is at least an year long and today's date is before the lease ends
                                if diff > 12 and today < end_date:
                                    print('lease longer than 1 year')
                                    # create a charge date for 1 year from start date
                                    charge_date = start_date + \
                                        relativedelta(months=12)
                                    charge_month = charge_date.strftime('%B')
                                    # check if today's date == the charge date
                                    if today == charge_date:
                                        # if yes, then enter the annual fees to the purchases table
                                        print('enter the fee to purchases')

                                        purchaseResponse = newPurchase(
                                            linked_bill_id=None,
                                            pur_property_id=contract['property_uid'],
                                            payer=payer,
                                            receiver=contract['business_uid'],
                                            purchase_type='MANAGEMENT',
                                            description=payment['fee_name'],
                                            amount_due=payment['charge'],
                                            purchase_notes=charge_month,
                                            purchase_date=contract['start_date'],
                                            purchase_frequency=payment['frequency'],
                                            next_payment=charge_date
                                        )
                            else:
                                print('payment frequency one-time $')
                        # if fee_type is %, we check for the gross rent or net and calculate the charge according to that
                        else:
                            print('payment fee type %')
                            if payment['frequency'] == 'Weekly':
                                print('payment frequency weekly %')
                                start_date = date.fromisoformat(
                                    contract['start_date'])
                                end_date = date.fromisoformat(
                                    contract['end_date'])
                                # check if today's date is before contract end
                                if today < end_date:
                                    # get previous purchases
                                    if contract['prevPurchases'] != []:
                                        prevPurchaseDate = datetime.strptime(
                                            contract['prevPurchases'][-1]['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                        # set charge date as friday of every week
                                        charge_date = next_weekday(
                                            prevPurchaseDate, 4)
                                        charge_month = charge_date.strftime(
                                            '%B')
                                        print('charge_date',
                                              charge_date, charge_month)
                                        # if charge date == today then enter the monthly fee
                                        if charge_date == today:
                                            print('enter the fee to purchases')
                                            # if yes, then enter the monthly fees to the purchases table
                                        print('enter the fee to purchases')
                                        # if gross rent (listed rent)
                                        if payment['of'] == 'Gross Rent':
                                            print('payment of gross rent', (
                                                int(payment['charge']) * int(contract['listed_rent']))/100)
                                            purchaseResponse = newPurchase(
                                                linked_bill_id=None,
                                                pur_property_id=contract['property_uid'],
                                                payer=payer,
                                                receiver=contract['business_uid'],
                                                purchase_type='MANAGEMENT',
                                                description=payment['fee_name'],
                                                amount_due=(
                                                    int(payment['charge']) * int(contract['listed_rent']))/100,
                                                purchase_notes=charge_month,
                                                purchase_date=contract['start_date'],
                                                purchase_frequency=payment['frequency'],
                                                next_payment=charge_date
                                            )
                                        # if net rent (listed rent-expenses)
                                        else:
                                            print('payment of net rent', (
                                                int(payment['charge']) * (int(contract['listed_rent']) - contract['expense_amount']))/100)
                                            purchaseResponse = newPurchase(
                                                linked_bill_id=None,
                                                pur_property_id=contract['property_uid'],
                                                payer=payer,
                                                receiver=contract['business_uid'],
                                                purchase_type='MANAGEMENT',
                                                description=payment['fee_name'],
                                                amount_due=(
                                                    int(payment['charge']) * (int(contract['listed_rent']) - contract['expense_amount']))/100,
                                                purchase_notes=charge_month,
                                                purchase_date=contract['start_date'],
                                                purchase_frequency=payment['frequency'],
                                                next_payment=charge_date
                                            )
                            elif payment['frequency'] == 'Bieekly':
                                print('payment frequency biweekly %')
                                start_date = date.fromisoformat(
                                    contract['start_date'])
                                end_date = date.fromisoformat(
                                    contract['end_date'])
                                # check if today's date is before contract end
                                if today < end_date:
                                    # get previous purchases
                                    if contract['prevPurchases'] != []:
                                        prevPurchaseDate = datetime.strptime(
                                            contract['prevPurchases'][-1]['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                        # set charge date as friday every two weeks
                                        charge_date = next_weekday_biweekly(
                                            prevPurchaseDate, 4)
                                        charge_month = charge_date.strftime(
                                            '%B')
                                        print('charge_date',
                                              charge_date, charge_month)
                                        # if charge date == today then enter the monthly fee
                                        if charge_date == today:
                                            print('enter the fee to purchases')
                                            # if yes, then enter the monthly fees to the purchases table
                                        print('enter the fee to purchases')
                                        # if gross rent (listed rent)
                                        if payment['of'] == 'Gross Rent':
                                            print('payment of gross rent', (
                                                int(payment['charge']) * int(contract['listed_rent']))/100)
                                            purchaseResponse = newPurchase(
                                                linked_bill_id=None,
                                                pur_property_id=contract['property_uid'],
                                                payer=payer,
                                                receiver=contract['business_uid'],
                                                purchase_type='MANAGEMENT',
                                                description=payment['fee_name'],
                                                amount_due=(
                                                    int(payment['charge']) * int(contract['listed_rent']))/100,
                                                purchase_notes=charge_month,
                                                purchase_date=contract['start_date'],
                                                purchase_frequency=payment['frequency'],
                                                next_payment=charge_date
                                            )
                                        # if net rent (listed rent-expenses)
                                        else:
                                            print('payment of net rent', (
                                                int(payment['charge']) * (int(contract['listed_rent']) - contract['expense_amount']))/100)
                                            purchaseResponse = newPurchase(
                                                linked_bill_id=None,
                                                pur_property_id=contract['property_uid'],
                                                payer=payer,
                                                receiver=contract['business_uid'],
                                                purchase_type='MANAGEMENT',
                                                description=payment['fee_name'],
                                                amount_due=(
                                                    int(payment['charge']) * (int(contract['listed_rent']) - contract['expense_amount']))/100,
                                                purchase_notes=charge_month,
                                                purchase_date=contract['start_date'],
                                                purchase_frequency=payment['frequency'],
                                                next_payment=charge_date
                                            )
                            elif payment['frequency'] == 'Monthly':
                                print('payment frequency monthly %')
                                start_date = date.fromisoformat(
                                    contract['start_date'])
                                end_date = date.fromisoformat(
                                    contract['end_date'])
                                # check if today's date is before contract end
                                if today < end_date:
                                    # get previous purchases
                                    if contract['prevPurchases'] != []:
                                        prevPurchaseDate = datetime.strptime(
                                            contract['prevPurchases'][-1]['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                        # set charge date as first of every month
                                        charge_date = prevPurchaseDate.replace(
                                            day=1) + relativedelta(months=1)
                                        charge_month = charge_date.strftime(
                                            '%B')
                                        print('charge_date',
                                              charge_date, charge_month)
                                        # if charge date == today then enter the monthly fee
                                        if charge_date == today:
                                            print('enter the fee to purchases')
                                            # if yes, then enter the monthly fees to the purchases table
                                        print('enter the fee to purchases')
                                        # if gross rent (listed rent)
                                        if payment['of'] == 'Gross Rent':
                                            print('payment of gross rent', (
                                                int(payment['charge']) * int(contract['listed_rent']))/100)
                                            purchaseResponse = newPurchase(
                                                linked_bill_id=None,
                                                pur_property_id=contract['property_uid'],
                                                payer=payer,
                                                receiver=contract['business_uid'],
                                                purchase_type='MANAGEMENT',
                                                description=payment['fee_name'],
                                                amount_due=(
                                                    int(payment['charge']) * int(contract['listed_rent']))/100,
                                                purchase_notes=charge_month,
                                                purchase_date=contract['start_date'],
                                                purchase_frequency=payment['frequency'],
                                                next_payment=charge_date
                                            )
                                        # if net rent (listed rent-expenses)
                                        else:
                                            print('payment of net rent', (
                                                int(payment['charge']) * (int(contract['listed_rent']) - contract['expense_amount']))/100)
                                            purchaseResponse = newPurchase(
                                                linked_bill_id=None,
                                                pur_property_id=contract['property_uid'],
                                                payer=payer,
                                                receiver=contract['business_uid'],
                                                purchase_type='MANAGEMENT',
                                                description=payment['fee_name'],
                                                amount_due=(
                                                    int(payment['charge']) * (int(contract['listed_rent']) - contract['expense_amount']))/100,
                                                purchase_notes=charge_month,
                                                purchase_date=contract['start_date'],
                                                purchase_frequency=payment['frequency'],
                                                next_payment=charge_date
                                            )
                            elif payment['frequency'] == 'Annually':
                                print('payment frequency annually %')
                                start_date = date.fromisoformat(
                                    contract['start_date'])
                                end_date = date.fromisoformat(
                                    contract['end_date'])
                                # calculate the contract length
                                diff = diff_month(end_date, start_date)
                                # check if contract is at least an year long and today's date is before the lease ends
                                if diff > 12 and today < end_date:
                                    print('lease longer than 1 year')
                                    # create a charge date for 1 year from start date
                                    charge_date = start_date + \
                                        relativedelta(months=12)
                                    charge_month = charge_date.strftime('%B')
                                    # check if today's date == the charge date
                                    if today == charge_date:
                                        # if yes, then enter the annual fees to the purchases table
                                        print('enter the fee to purchases')
                                        # if gross rent (listed rent)
                                        if payment['of'] == 'Gross Rent':
                                            print('payment of gross rent', (
                                                int(payment['charge']) * int(contract['listed_rent']))/100)
                                            purchaseResponse = newPurchase(
                                                linked_bill_id=None,
                                                pur_property_id=contract['property_uid'],
                                                payer=payer,
                                                receiver=contract['business_uid'],
                                                purchase_type='MANAGEMENT',
                                                description=payment['fee_name'],
                                                amount_due=(
                                                    int(payment['charge']) * int(contract['listed_rent']))/100,
                                                purchase_notes=charge_month,
                                                purchase_date=contract['start_date'],
                                                purchase_frequency=payment['frequency'],
                                                next_payment=charge_date
                                            )
                                        # if net rent (listed rent-expenses)
                                        else:
                                            print('payment of net rent', (
                                                int(payment['charge']) * (int(contract['listed_rent']) - contract['expense_amount']))/100)
                                            purchaseResponse = newPurchase(
                                                linked_bill_id=None,
                                                pur_property_id=contract['property_uid'],
                                                payer=payer,
                                                receiver=contract['business_uid'],
                                                purchase_type='MANAGEMENT',
                                                description=payment['fee_name'],
                                                amount_due=(
                                                    int(payment['charge']) * (int(contract['listed_rent']) - contract['expense_amount']))/100,
                                                purchase_notes=charge_month,
                                                purchase_date=contract['start_date'],
                                                purchase_frequency=payment['frequency'],
                                                next_payment=charge_date
                                            )
                            else:
                                print('payment frequency one-time %')

        return response


def ManagerContractFees():
    print("In ManagerContractFees")
    from datetime import date, timedelta, datetime
    from dateutil.relativedelta import relativedelta
    from purchases import newPurchase

    with connect() as db:
        print("In Manager Contract Fees Function")
        response = {'message': 'Successfully committed SQL query',
                    'code': 200}
        payments = []
        response = db.execute("""SELECT * FROM contracts c
                                LEFT JOIN
                                pm.properties prop
                                ON prop.property_uid = c.property_uid
                                LEFT JOIN
                                pm.propertyManager propM
                                ON propM.linked_property_id = c.property_uid
                                WHERE c.contract_status = 'ACTIVE'
                                AND propM.management_status = 'ACCEPTED'  """)

        # getting all the expenses and calculating the expense amount
        if len(response['result']) > 0:
            for i in range(len(response['result'])):
                response['result'][i]['expense_amount'] = 0
                purRes = db.execute("""SELECT * FROM purchases pur
                                        WHERE pur.pur_property_id= \'""" + response['result'][i]['property_uid'] + """\'
                                        AND (pur.purchase_type = 'UTILITY' OR pur.purchase_type = 'MAINTENANCE' OR pur.purchase_type = 'REPAIRS') """)
                response['result'][i]['expenses'] = list(purRes['result'])
                if len(purRes['result']) > 0:
                    for ore in range(len(purRes['result'])):
                        response['result'][i]['expense_amount'] = response['result'][i]['expense_amount'] + int(
                            purRes['result'][ore]['amount_due'])
            # getting all the previous management purchases
        if len(response['result']) > 0:
            for i in range(len(response['result'])):
                response['result'][i]['expense_amount'] = 0
                purRes = db.execute("""SELECT * FROM purchases pur
                                        WHERE pur.pur_property_id= \'""" + response['result'][i]['property_uid'] + """\'
                                        AND pur.purchase_type = 'MANAGEMENT' """)
                response['result'][i]['prevPurchases'] = list(
                    purRes['result'])

        if len(response['result']) > 0:
            # today's date
            today = date.today()
            for contract in response['result']:
                # creating purchases
                managementPayments = json.loads(contract['contract_fees'])
                payer = contract['owner_id']
                if '[' in payer:
                    payer = json.loads(payer)
                if type(payer) == str:
                    payer = [payer]
                payer = json.dumps(payer)
                for payment in managementPayments:
                    # if fee_type is $, put the charge amount directly
                    if payment['fee_type'] == '$':
                        print('payment fee type $')
                        if payment['frequency'] == 'Weekly':
                            print('payment frequency weekly $')
                            start_date = date.fromisoformat(
                                contract['start_date'])
                            end_date = date.fromisoformat(
                                contract['end_date'])
                            # check if today's date is before contract end
                            if today < end_date:
                                # get previous purchases
                                if contract['prevPurchases'] != []:
                                    prevPurchaseDate = datetime.strptime(
                                        contract['prevPurchases'][-1]['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                    # set charge date as friday of every week
                                    charge_date = next_weekday(
                                        prevPurchaseDate, 4)
                                    charge_month = charge_date.strftime(
                                        '%B')
                                    print('charge_date',
                                          charge_date, charge_month)
                                    # if charge date == today then enter the monthly fee
                                    if charge_date == today:
                                        print('enter the fee to purchases')

                                        purchaseResponse = newPurchase(
                                            linked_bill_id=None,
                                            pur_property_id=contract['property_uid'],
                                            payer=payer,
                                            receiver=contract['business_uid'],
                                            purchase_type='MANAGEMENT',
                                            description=payment['fee_name'],
                                            amount_due=payment['charge'],
                                            purchase_notes=charge_month,
                                            purchase_date=contract['start_date'],
                                            purchase_frequency=payment['frequency'],
                                            next_payment=charge_date
                                        )
                        elif payment['frequency'] == 'Bieekly':
                            print('payment frequency biweekly $')
                            start_date = date.fromisoformat(
                                contract['start_date'])
                            end_date = date.fromisoformat(
                                contract['end_date'])
                            # check if today's date is before contract end
                            if today < end_date:
                                # get previous purchases
                                if contract['prevPurchases'] != []:
                                    prevPurchaseDate = datetime.strptime(
                                        contract['prevPurchases'][-1]['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                    # set charge date as friday of every 2 week
                                    charge_date = next_weekday_biweekly(
                                        prevPurchaseDate, 4)
                                    charge_month = charge_date.strftime(
                                        '%B')
                                    print('charge_date',
                                          charge_date, charge_month)
                                    # if charge date == today then enter the monthly fee
                                    if charge_date == today:
                                        print('enter the fee to purchases')

                                        purchaseResponse = newPurchase(
                                            linked_bill_id=None,
                                            pur_property_id=contract['property_uid'],
                                            payer=payer,
                                            receiver=contract['business_uid'],
                                            purchase_type='MANAGEMENT',
                                            description=payment['fee_name'],
                                            amount_due=payment['charge'],
                                            purchase_notes=charge_month,
                                            purchase_date=contract['start_date'],
                                            purchase_frequency=payment['frequency'],
                                            next_payment=charge_date
                                        )
                        elif payment['frequency'] == 'Monthly':
                            print('payment frequency monthly $')
                            start_date = date.fromisoformat(
                                contract['start_date'])
                            end_date = date.fromisoformat(
                                contract['end_date'])
                            # check if today's date is before contract end
                            if today < end_date:
                                # get previous purchases
                                if contract['prevPurchases'] != []:
                                    prevPurchaseDate = datetime.strptime(
                                        contract['prevPurchases'][-1]['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                    # set charge date as first of every month
                                    charge_date = prevPurchaseDate.replace(
                                        day=1) + relativedelta(months=1)
                                    charge_month = charge_date.strftime(
                                        '%B')
                                    print('charge_date',
                                          charge_date, charge_month)
                                    # if charge date == today then enter the monthly fee
                                    if charge_date == today:
                                        print('enter the fee to purchases')

                                        purchaseResponse = newPurchase(
                                            linked_bill_id=None,
                                            pur_property_id=contract['property_uid'],
                                            payer=payer,
                                            receiver=contract['business_uid'],
                                            purchase_type='MANAGEMENT',
                                            description=payment['fee_name'],
                                            amount_due=payment['charge'],
                                            purchase_notes=charge_month,
                                            purchase_date=contract['start_date'],
                                            purchase_frequency=payment['frequency'],
                                            next_payment=charge_date
                                        )

                        elif payment['frequency'] == 'Annually':
                            print('payment frequency annually $')
                            start_date = date.fromisoformat(
                                contract['start_date'])
                            end_date = date.fromisoformat(
                                contract['end_date'])
                            # calculate the contract length
                            diff = diff_month(end_date, start_date)
                            # check if contract is at least an year long and today's date is before the lease ends
                            if diff > 12 and today < end_date:
                                print('lease longer than 1 year')
                                # create a charge date for 1 year from start date
                                charge_date = start_date + \
                                    relativedelta(months=12)
                                charge_month = charge_date.strftime('%B')
                                # check if today's date == the charge date
                                if today == charge_date:
                                    # if yes, then enter the annual fees to the purchases table
                                    print('enter the fee to purchases')

                                    purchaseResponse = newPurchase(
                                        linked_bill_id=None,
                                        pur_property_id=contract['property_uid'],
                                        payer=payer,
                                        receiver=contract['business_uid'],
                                        purchase_type='MANAGEMENT',
                                        description=payment['fee_name'],
                                        amount_due=payment['charge'],
                                        purchase_notes=charge_month,
                                        purchase_date=contract['start_date'],
                                        purchase_frequency=payment['frequency'],
                                        next_payment=charge_date
                                    )
                        else:
                            print('payment frequency one-time $')
                    # if fee_type is %, we check for the gross rent or net and calculate the charge according to that
                    else:
                        print('payment fee type %')
                        if payment['frequency'] == 'Weekly':
                            print('payment frequency weekly %')
                            start_date = date.fromisoformat(
                                contract['start_date'])
                            end_date = date.fromisoformat(
                                contract['end_date'])
                            # check if today's date is before contract end
                            if today < end_date:
                                # get previous purchases
                                if contract['prevPurchases'] != []:
                                    prevPurchaseDate = datetime.strptime(
                                        contract['prevPurchases'][-1]['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                    # set charge date as friday of every week
                                    charge_date = next_weekday(
                                        prevPurchaseDate, 4)
                                    charge_month = charge_date.strftime(
                                        '%B')
                                    print('charge_date',
                                          charge_date, charge_month)
                                    # if charge date == today then enter the monthly fee
                                    if charge_date == today:
                                        print('enter the fee to purchases')
                                        # if yes, then enter the monthly fees to the purchases table
                                    print('enter the fee to purchases')
                                    # if gross rent (listed rent)
                                    if payment['of'] == 'Gross Rent':
                                        print('payment of gross rent', (
                                            int(payment['charge']) * int(contract['listed_rent']))/100)
                                        purchaseResponse = newPurchase(
                                            linked_bill_id=None,
                                            pur_property_id=contract['property_uid'],
                                            payer=payer,
                                            receiver=contract['business_uid'],
                                            purchase_type='MANAGEMENT',
                                            description=payment['fee_name'],
                                            amount_due=(
                                                int(payment['charge']) * int(contract['listed_rent']))/100,
                                            purchase_notes=charge_month,
                                            purchase_date=contract['start_date'],
                                            purchase_frequency=payment['frequency'],
                                            next_payment=charge_date
                                        )
                                    # if net rent (listed rent-expenses)
                                    else:
                                        print('payment of net rent', (
                                            int(payment['charge']) * (int(contract['listed_rent']) - contract['expense_amount']))/100)
                                        purchaseResponse = newPurchase(
                                            linked_bill_id=None,
                                            pur_property_id=contract['property_uid'],
                                            payer=payer,
                                            receiver=contract['business_uid'],
                                            purchase_type='MANAGEMENT',
                                            description=payment['fee_name'],
                                            amount_due=(
                                                int(payment['charge']) * (int(contract['listed_rent']) - contract['expense_amount']))/100,
                                            purchase_notes=charge_month,
                                            purchase_date=contract['start_date'],
                                            purchase_frequency=payment['frequency'],
                                            next_payment=charge_date
                                        )
                        elif payment['frequency'] == 'Bieekly':
                            print('payment frequency biweekly %')
                            start_date = date.fromisoformat(
                                contract['start_date'])
                            end_date = date.fromisoformat(
                                contract['end_date'])
                            # check if today's date is before contract end
                            if today < end_date:
                                # get previous purchases
                                if contract['prevPurchases'] != []:
                                    prevPurchaseDate = datetime.strptime(
                                        contract['prevPurchases'][-1]['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                    # set charge date as friday every two weeks
                                    charge_date = next_weekday_biweekly(
                                        prevPurchaseDate, 4)
                                    charge_month = charge_date.strftime(
                                        '%B')
                                    print('charge_date',
                                          charge_date, charge_month)
                                    # if charge date == today then enter the monthly fee
                                    if charge_date == today:
                                        print('enter the fee to purchases')
                                        # if yes, then enter the monthly fees to the purchases table
                                    print('enter the fee to purchases')
                                    # if gross rent (listed rent)
                                    if payment['of'] == 'Gross Rent':
                                        print('payment of gross rent', (
                                            int(payment['charge']) * int(contract['listed_rent']))/100)
                                        purchaseResponse = newPurchase(
                                            linked_bill_id=None,
                                            pur_property_id=contract['property_uid'],
                                            payer=payer,
                                            receiver=contract['business_uid'],
                                            purchase_type='MANAGEMENT',
                                            description=payment['fee_name'],
                                            amount_due=(
                                                int(payment['charge']) * int(contract['listed_rent']))/100,
                                            purchase_notes=charge_month,
                                            purchase_date=contract['start_date'],
                                            purchase_frequency=payment['frequency'],
                                            next_payment=charge_date
                                        )
                                    # if net rent (listed rent-expenses)
                                    else:
                                        print('payment of net rent', (
                                            int(payment['charge']) * (int(contract['listed_rent']) - contract['expense_amount']))/100)
                                        purchaseResponse = newPurchase(
                                            linked_bill_id=None,
                                            pur_property_id=contract['property_uid'],
                                            payer=payer,
                                            receiver=contract['business_uid'],
                                            purchase_type='MANAGEMENT',
                                            description=payment['fee_name'],
                                            amount_due=(
                                                int(payment['charge']) * (int(contract['listed_rent']) - contract['expense_amount']))/100,
                                            purchase_notes=charge_month,
                                            purchase_date=contract['start_date'],
                                            purchase_frequency=payment['frequency'],
                                            next_payment=charge_date
                                        )
                        elif payment['frequency'] == 'Monthly':
                            print('payment frequency monthly %')
                            start_date = date.fromisoformat(
                                contract['start_date'])
                            end_date = date.fromisoformat(
                                contract['end_date'])
                            # check if today's date is before contract end
                            if today < end_date:
                                # get previous purchases
                                if contract['prevPurchases'] != []:
                                    prevPurchaseDate = datetime.strptime(
                                        contract['prevPurchases'][-1]['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                    # set charge date as first of every month
                                    charge_date = prevPurchaseDate.replace(
                                        day=1) + relativedelta(months=1)
                                    charge_month = charge_date.strftime(
                                        '%B')
                                    print('charge_date',
                                          charge_date, charge_month)
                                    # if charge date == today then enter the monthly fee
                                    if charge_date == today:
                                        print('enter the fee to purchases')
                                        # if yes, then enter the monthly fees to the purchases table
                                    print('enter the fee to purchases')
                                    # if gross rent (listed rent)
                                    if payment['of'] == 'Gross Rent':
                                        print('payment of gross rent', (
                                            int(payment['charge']) * int(contract['listed_rent']))/100)
                                        purchaseResponse = newPurchase(
                                            linked_bill_id=None,
                                            pur_property_id=contract['property_uid'],
                                            payer=payer,
                                            receiver=contract['business_uid'],
                                            purchase_type='MANAGEMENT',
                                            description=payment['fee_name'],
                                            amount_due=(
                                                int(payment['charge']) * int(contract['listed_rent']))/100,
                                            purchase_notes=charge_month,
                                            purchase_date=contract['start_date'],
                                            purchase_frequency=payment['frequency'],
                                            next_payment=charge_date
                                        )
                                    # if net rent (listed rent-expenses)
                                    else:
                                        print('payment of net rent', (
                                            int(payment['charge']) * (int(contract['listed_rent']) - contract['expense_amount']))/100)
                                        purchaseResponse = newPurchase(
                                            linked_bill_id=None,
                                            pur_property_id=contract['property_uid'],
                                            payer=payer,
                                            receiver=contract['business_uid'],
                                            purchase_type='MANAGEMENT',
                                            description=payment['fee_name'],
                                            amount_due=(
                                                int(payment['charge']) * (int(contract['listed_rent']) - contract['expense_amount']))/100,
                                            purchase_notes=charge_month,
                                            purchase_date=contract['start_date'],
                                            purchase_frequency=payment['frequency'],
                                            next_payment=charge_date
                                        )
                        elif payment['frequency'] == 'Annually':
                            print('payment frequency annually %')
                            start_date = date.fromisoformat(
                                contract['start_date'])
                            end_date = date.fromisoformat(
                                contract['end_date'])
                            # calculate the contract length
                            diff = diff_month(end_date, start_date)
                            # check if contract is at least an year long and today's date is before the lease ends
                            if diff > 12 and today < end_date:
                                print('lease longer than 1 year')
                                # create a charge date for 1 year from start date
                                charge_date = start_date + \
                                    relativedelta(months=12)
                                charge_month = charge_date.strftime('%B')
                                # check if today's date == the charge date
                                if today == charge_date:
                                    # if yes, then enter the annual fees to the purchases table
                                    print('enter the fee to purchases')
                                    # if gross rent (listed rent)
                                    if payment['of'] == 'Gross Rent':
                                        print('payment of gross rent', (
                                            int(payment['charge']) * int(contract['listed_rent']))/100)
                                        purchaseResponse = newPurchase(
                                            linked_bill_id=None,
                                            pur_property_id=contract['property_uid'],
                                            payer=payer,
                                            receiver=contract['business_uid'],
                                            purchase_type='MANAGEMENT',
                                            description=payment['fee_name'],
                                            amount_due=(
                                                int(payment['charge']) * int(contract['listed_rent']))/100,
                                            purchase_notes=charge_month,
                                            purchase_date=contract['start_date'],
                                            purchase_frequency=payment['frequency'],
                                            next_payment=charge_date
                                        )
                                    # if net rent (listed rent-expenses)
                                    else:
                                        print('payment of net rent', (
                                            int(payment['charge']) * (int(contract['listed_rent']) - contract['expense_amount']))/100)
                                        purchaseResponse = newPurchase(
                                            linked_bill_id=None,
                                            pur_property_id=contract['property_uid'],
                                            payer=payer,
                                            receiver=contract['business_uid'],
                                            purchase_type='MANAGEMENT',
                                            description=payment['fee_name'],
                                            amount_due=(
                                                int(payment['charge']) * (int(contract['listed_rent']) - contract['expense_amount']))/100,
                                            purchase_notes=charge_month,
                                            purchase_date=contract['start_date'],
                                            purchase_frequency=payment['frequency'],
                                            next_payment=charge_date
                                        )
                        else:
                            print('payment frequency one-time %')

    return response
