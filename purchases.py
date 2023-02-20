
from flask import request
from flask_restful import Resource

from data import connect
from datetime import date, datetime, timedelta
from calendar import monthrange
from dateutil.relativedelta import relativedelta
import json


def newPurchase(linked_bill_id, pur_property_id, payer, receiver, purchase_type,
                description, amount_due, purchase_notes, purchase_date, purchase_frequency, next_payment):
    response = {}
    print('in new purchase')
    with connect() as db:
        print('in new purchase')
        newPurchase = {
            "linked_bill_id": linked_bill_id,
            "pur_property_id": pur_property_id,
            "payer": payer,
            "receiver": receiver,
            "purchase_type": purchase_type,
            "description": description,
            "amount_due": amount_due,
            "purchase_notes": purchase_notes,
            "purchase_date": purchase_date,
            "purchase_frequency": purchase_frequency,
            "next_payment": next_payment
        }
        print(newPurchase)
        newPurchaseID = db.call('new_purchase_id')['result'][0]['new_id']
        newPurchase['amount_paid'] = 0
        newPurchase['purchase_uid'] = newPurchaseID
        newPurchase['purchase_status'] = 'UNPAID'
        print(newPurchase)
        response = db.insert('purchases', newPurchase)
    return response


def updatePurchase(newPurchase):
    response = {}
    with connect() as db:
        primaryKey = {
            'purchase_uid': newPurchase['purchase_uid']
        }
        response = db.update('purchases', primaryKey, newPurchase)
    return response


class Purchases(Resource):
    def get(self):
        response = {}
        filters = [
            'purchase_uid',
            'linked_bill_id',
            'pur_property_id',
            'payer',
            'receiver'
        ]
        where = {}
        for filter in filters:
            filterValue = request.args.get(filter)
            if filterValue is not None:
                where[filter] = filterValue
        with connect() as db:
            response = db.select('purchases', where)
        return response

    def post(self):

        # return newPurchase(

        response = {}
        print('in new purchase')
        data = request.get_json()
        print(data)
        linked_bill_id = data.get('linked_bill_id')
        pur_property_id = json.dumps(data.get('pur_property_id'))
        payer = json.dumps(data.get('payer'))
        receiver = data.get('receiver')
        purchase_type = data.get('purchase_type')
        description = data.get('description')
        amount_due = data.get('amount_due')
        purchase_notes = data.get('purchase_notes')
        purchase_date = data.get('purchase_date')
        purchase_frequency = data.get('purchase_frequency')
        next_payment = data.get('next_payment')

        with connect() as db:
            print('in new purchase')
            if next_payment != "0000-00-00 00:00:00":
                print('do nothing date provided')
            else:
                print((pur_property_id.split("\"")))
                sql = """SELECT *
                        FROM pm.rentals r
                        LEFT JOIN pm.properties p
                        ON p.property_uid = r.rental_property_id
                        WHERE r.rental_property_id LIKE '%""" + pur_property_id.split("\"")[1] + """%'
                        AND r.rental_status = 'ACTIVE';"""
                print('rentalRes',  sql)

                rentalRes = db.execute("""SELECT *
                                            FROM pm.rentals r
                                            LEFT JOIN pm.properties p
                                            ON p.property_uid = r.rental_property_id
                                            WHERE r.rental_property_id LIKE '%""" + pur_property_id.split("\"")[1] + """%'
                                            AND r.rental_status = 'ACTIVE';""")

                propertyRes = db.execute("""SELECT *
                                        FROM properties
                                        WHERE property_uid  LIKE '%""" + pur_property_id.split("\"")[1] + """%' """)
                print('rentalRes', (propertyRes['result']))
                def days_in_month(dt): return monthrange(
                    dt.year, dt.month)[1]
                today = date.today()
                if len(rentalRes['result']) > 0:
                    print('tenants exist')
                    if today < today.replace(day=int(rentalRes['result'][0]['due_by'])):
                        payment_date = today.replace(
                            day=int(rentalRes['result'][0]['due_by']))
                        print(payment_date)
                        next_payment = datetime.strftime(
                            payment_date, '%Y-%m-%d %H:%M:%S')
                    else:
                        payment_date = today.replace(
                            day=int(rentalRes['result'][0]['due_by'])) + timedelta(days_in_month(today))
                        print(payment_date)
                        next_payment = datetime.strftime(
                            payment_date, '%Y-%m-%d %H:%M:%S')
                else:
                    payer = propertyRes['result'][0]['owner_id']
                    if '[' in payer:
                        payer = json.loads(payer)
                    if type(payer) == str:
                        payer = [payer]
                    payer = json.dumps(payer)
                    print(payer)

                    first_day = today.replace(
                        day=1) + timedelta(days_in_month(today))
                    print(first_day)
                    next_payment = datetime.strftime(
                        first_day, '%Y-%m-%d %H:%M:%S')

            newPurchase = {
                "linked_bill_id": linked_bill_id,
                "pur_property_id": (pur_property_id),
                "payer": payer,
                "receiver": receiver,
                "purchase_type": purchase_type,
                "description": description,
                "amount_due": amount_due,
                "purchase_notes": purchase_notes,
                "purchase_date": purchase_date,
                "purchase_frequency": purchase_frequency,
                "next_payment": next_payment
            }
            print(newPurchase)
            newPurchaseID = db.call('new_purchase_id')['result'][0]['new_id']
            newPurchase['amount_paid'] = 0
            newPurchase['purchase_uid'] = newPurchaseID
            newPurchase['purchase_status'] = 'UNPAID'
            # print(newPurchase)

            response = db.insert('purchases', newPurchase)
            response['purchase_uid'] = newPurchaseID
        return response


class CreateExpenses(Resource):

    def post(self):

        data = request.get_json()
        print('data', data)

        with connect() as db:
            if data['next_payment'] != "0000-00-00 00:00:00":
                print('do nothing date provided')
            else:
                print((data['pur_property_id'].split("\"")))
                sql = """SELECT *
                        FROM pm.rentals r
                        LEFT JOIN pm.properties p
                        ON p.property_uid = r.rental_property_id
                        WHERE r.rental_property_id LIKE '%""" + data['pur_property_id'].split("\"")[1] + """%'
                        AND r.rental_status = 'ACTIVE';"""
                print('rentalRes',  sql)

                rentalRes = db.execute("""SELECT *
                                            FROM pm.rentals r
                                            LEFT JOIN pm.properties p
                                            ON p.property_uid = r.rental_property_id
                                            WHERE r.rental_property_id LIKE '%""" + data['pur_property_id'].split("\"")[1] + """%'
                                            AND r.rental_status = 'ACTIVE';""")

                propertyRes = db.execute("""SELECT *
                                        FROM properties
                                        WHERE property_uid  LIKE '%""" + data['pur_property_id'].split("\"")[1] + """%' """)
                print('rentalRes', (propertyRes['result']))

                def days_in_month(dt): return monthrange(
                    dt.year, dt.month)[1]
                today = date.today()
                if len(rentalRes['result']) > 0:
                    print('tenants exist')
                    if today < today.replace(day=int(rentalRes['result'][0]['due_by'])):
                        payment_date = today.replace(
                            day=int(rentalRes['result'][0]['due_by']))
                        print(payment_date)
                        data['next_payment'] = datetime.strftime(
                            payment_date, '%Y-%m-%d %H:%M:%S')
                    else:
                        payment_date = today.replace(
                            day=int(rentalRes['result'][0]['due_by'])) + timedelta(days_in_month(today))
                        print(payment_date)
                        data['next_payment'] = datetime.strftime(
                            payment_date, '%Y-%m-%d %H:%M:%S')
                else:
                    payer = propertyRes['result'][0]['owner_id']
                    if '[' in payer:
                        payer = json.loads(payer)
                    if type(payer) == str:
                        payer = [payer]
                    payer = json.dumps(payer)
                    print(payer)

                    first_day = today.replace(
                        day=1) + timedelta(days_in_month(today))
                    print(first_day)
                    data['next_payment'] = datetime.strftime(
                        first_day, '%Y-%m-%d %H:%M:%S')
            if data['payer'] == 'TENANT':
                if data['splitPercentManager'] != '0' and data['splitPercentOwner'] != '0':
                    if data['purchase_frequency'] == 'Monthly':
                        print('here monthly')
                        charge_date = date.today()
                        next_payment = date.fromisoformat(data['next_payment'])
                        print('here monthly', next_payment)
                        charge_month = charge_date.strftime('%B')

                        print('in new purchase')

                        if data['purchase_status'] == 'PAID':
                            amount_paid = data['amount_due']
                        else:
                            amount_paid = 0
                        newPurchase = {
                            "linked_bill_id": None,
                            "pur_property_id": json.dumps([data['pur_property_id']]),
                            "payer": json.dumps([data.get('payerID')]),
                            "receiver": data['managerID'],
                            "purchase_type": data['purchase_type'].upper(),
                            "description": data['description'],
                            "amount_due": data['amount_due'],
                            "amount_paid": amount_paid,
                            "purchase_notes": charge_month,
                            "purchase_date": charge_date,
                            "purchase_frequency": data["purchase_frequency"],
                            "payment_frequency": data["payment_frequency"],
                            "next_payment": data["next_payment"]
                        }
                        newPurchaseID = db.call('new_purchase_id')[
                            'result'][0]['new_id']

                        newPurchase['purchase_uid'] = newPurchaseID
                        newPurchase['purchase_status'] = data['purchase_status']
                        response = db.insert('purchases', newPurchase)

                        charge_date += relativedelta(months=1)
                        amount_due = int(data["amount_due"]) * \
                            (int(data['splitPercentOwner'])/100)
                        if data['purchase_status'] == 'PAID':
                            amount_paid = amount_due
                        else:
                            amount_paid = 0
                        newPurchase = {
                            "linked_bill_id": None,
                            "pur_property_id": json.dumps([data['pur_property_id']]),
                            "payer": json.dumps([data.get('managerID')]),
                            "receiver": data['ownerID'],
                            "purchase_type": 'OWNER PAYMENT' + ' ' + data['purchase_type'].upper(),
                            "description": data['description'],
                            "amount_due": amount_due,
                            "amount_paid": amount_paid,
                            "purchase_notes": charge_month,
                            "purchase_date": charge_date,
                            "purchase_frequency": data["purchase_frequency"],
                            "payment_frequency": data["payment_frequency"],
                            "next_payment": data["next_payment"]
                        }
                        newPurchaseID = db.call('new_purchase_id')[
                            'result'][0]['new_id']

                        newPurchase['purchase_uid'] = newPurchaseID
                        newPurchase['purchase_status'] = data['purchase_status']
                        responseOwner = db.insert('purchases', newPurchase)

                        charge_date += relativedelta(months=1)

                    elif data['purchase_frequency'] == 'Annually':
                        print('here annually')
                        charge_date = date.today()
                        next_payment = date.fromisoformat(data['next_payment'])

                        charge_month = charge_date.strftime('%B')

                        print('in new purchase')
                        if data['purchase_status'] == 'PAID':
                            amount_paid = data['amount_due']
                        else:
                            amount_paid = 0
                        newPurchase = {
                            "linked_bill_id": None,
                            "pur_property_id": json.dumps([data['pur_property_id']]),
                            "payer": json.dumps([data.get('payerID')]),
                            "receiver": data['managerID'],
                            "purchase_type": data['purchase_type'].upper(),
                            "description": data['description'],
                            "amount_due": data['amount_due'],
                            "amount_paid": amount_paid,
                            "purchase_notes": charge_month,
                            "purchase_date": charge_date,
                            "purchase_frequency": data["purchase_frequency"],
                            "payment_frequency": data["payment_frequency"],
                            "next_payment": data["next_payment"]
                        }
                        newPurchaseID = db.call('new_purchase_id')[
                            'result'][0]['new_id']

                        newPurchase['purchase_uid'] = newPurchaseID
                        newPurchase['purchase_status'] = data['purchase_status']
                        response = db.insert('purchases', newPurchase)

                        charge_date += relativedelta(months=12)

                        amount_due = int(data["amount_due"]) * \
                            (int(data['splitPercentOwner'])/100)
                        if data['purchase_status'] == 'PAID':
                            amount_paid = amount_due
                        else:
                            amount_paid = 0
                        newPurchase = {
                            "linked_bill_id": None,
                            "pur_property_id": json.dumps([data['pur_property_id']]),
                            "payer": json.dumps([data.get('managerID')]),
                            "receiver": data['ownerID'],
                            "purchase_type": 'OWNER PAYMENT' + ' ' + data['purchase_type'].upper(),
                            "description": data['description'],
                            "amount_due": amount_due,
                            "amount_paid": amount_paid,
                            "purchase_notes": charge_month,
                            "purchase_date": charge_date,
                            "purchase_frequency": data["purchase_frequency"],
                            "payment_frequency": data["payment_frequency"],
                            "next_payment": data["next_payment"]
                        }
                        newPurchaseID = db.call('new_purchase_id')[
                            'result'][0]['new_id']

                        newPurchase['purchase_uid'] = newPurchaseID
                        newPurchase['purchase_status'] = data['purchase_status']
                        responseOwner = db.insert('purchases', newPurchase)

                        charge_date += relativedelta(months=12)
                        # return purchaseResponse
                    else:
                        print('here one-time')
                        charge_date = date.fromisoformat(data['next_payment'])
                        charge_month = charge_date.strftime('%B')

                        print('in new purchase')

                        if data['purchase_status'] == 'PAID':
                            amount_paid = data['amount_due']
                        else:
                            amount_paid = 0
                        newPurchase = {
                            "linked_bill_id": None,
                            "pur_property_id": json.dumps([data['pur_property_id']]),
                            "payer": json.dumps([data.get('payerID')]),
                            "receiver": data['managerID'],
                            "purchase_type": data['purchase_type'].upper(),
                            "description": data['description'],
                            "amount_due": data["amount_due"],
                            "amount_paid": amount_paid,
                            "purchase_notes": charge_month,
                            "purchase_date": charge_date,
                            "purchase_frequency": data["purchase_frequency"],
                            "payment_frequency": data["payment_frequency"],
                            "next_payment": data["next_payment"]
                        }
                        newPurchaseID = db.call('new_purchase_id')[
                            'result'][0]['new_id']
                        newPurchase['purchase_uid'] = newPurchaseID
                        newPurchase['purchase_status'] = data['purchase_status']
                        response = db.insert('purchases', newPurchase)

                        amount_due = int(data["amount_due"]) * \
                            (int(data['splitPercentOwner'])/100)
                        if data['purchase_status'] == 'PAID':
                            amount_paid = amount_due
                        else:
                            amount_paid = 0
                        newPurchase = {
                            "linked_bill_id": None,
                            "pur_property_id": json.dumps([data['pur_property_id']]),
                            "payer": json.dumps([data.get('managerID')]),
                            "receiver": data['ownerID'],
                            "purchase_type": 'OWNER PAYMENT' + ' ' + data['purchase_type'].upper(),
                            "description": data['description'],
                            "amount_due": amount_due,
                            "amount_paid": amount_paid,
                            "purchase_notes": charge_month,
                            "purchase_date": charge_date,
                            "purchase_frequency": data["purchase_frequency"],
                            "payment_frequency": data["payment_frequency"],
                            "next_payment": data["next_payment"]
                        }
                        newPurchaseID = db.call('new_purchase_id')[
                            'result'][0]['new_id']
                        newPurchase['purchase_uid'] = newPurchaseID
                        newPurchase['purchase_status'] = data['purchase_status']

                        responseOwner = db.insert('purchases', newPurchase)
                elif (data['splitPercentManager']) != '0' and data['splitPercentOwner'] == '0':
                    if data['purchase_frequency'] == 'Monthly':
                        print('here monthly')
                        charge_date = date.today()
                        next_payment = date.fromisoformat(data['next_payment'])
                        print('here monthly', next_payment)
                        charge_month = charge_date.strftime('%B')

                        print('in new purchase')

                        if data['purchase_status'] == 'PAID':
                            amount_paid = data['amount_due']
                        else:
                            amount_paid = 0
                        newPurchase = {
                            "linked_bill_id": None,
                            "pur_property_id": json.dumps([data['pur_property_id']]),
                            "payer": json.dumps([data.get('payerID')]),
                            "receiver": data['managerID'],
                            "purchase_type": data['purchase_type'].upper(),
                            "description": data['description'],
                            "amount_due": data['amount_due'],
                            "amount_paid": amount_paid,
                            "purchase_notes": charge_month,
                            "purchase_date": charge_date,
                            "purchase_frequency": data["purchase_frequency"],
                            "payment_frequency": data["payment_frequency"],
                            "next_payment": data["next_payment"]
                        }
                        newPurchaseID = db.call('new_purchase_id')[
                            'result'][0]['new_id']

                        newPurchase['purchase_uid'] = newPurchaseID
                        newPurchase['purchase_status'] = data['purchase_status']
                        response = db.insert('purchases', newPurchase)

                    elif data['purchase_frequency'] == 'Annually':
                        print('here annually')
                        charge_date = date.today()
                        next_payment = date.fromisoformat(data['next_payment'])

                        charge_month = charge_date.strftime('%B')

                        print('in new purchase')

                        if data['purchase_status'] == 'PAID':
                            amount_paid = data['amount_due']
                        else:
                            amount_paid = 0
                        newPurchase = {
                            "linked_bill_id": None,
                            "pur_property_id": json.dumps([data['pur_property_id']]),
                            "payer": json.dumps([data.get('payerID')]),
                            "receiver": data['managerID'],
                            "purchase_type": data['purchase_type'].upper(),
                            "description": data['description'],
                            "amount_due": data['amount_due'],
                            "amount_paid": amount_paid,
                            "purchase_notes": charge_month,
                            "purchase_date": charge_date,
                            "purchase_frequency": data["purchase_frequency"],
                            "payment_frequency": data["payment_frequency"],
                            "next_payment": data["next_payment"]
                        }
                        newPurchaseID = db.call('new_purchase_id')[
                            'result'][0]['new_id']

                        newPurchase['purchase_uid'] = newPurchaseID
                        newPurchase['purchase_status'] = data['purchase_status']
                        response = db.insert('purchases', newPurchase)

                        charge_date += relativedelta(months=12)

                    else:
                        print('here one-time')
                        charge_date = date.fromisoformat(data['next_payment'])
                        charge_month = charge_date.strftime('%B')

                        print('in new purchase')

                        if data['purchase_status'] == 'PAID':
                            amount_paid = data['amount_due']
                        else:
                            amount_paid = 0
                        newPurchase = {
                            "linked_bill_id": None,
                            "pur_property_id": json.dumps([data['pur_property_id']]),
                            "payer": json.dumps([data.get('payerID')]),
                            "receiver": data['managerID'],
                            "purchase_type": data['purchase_type'].upper(),
                            "description": data['description'],
                            "amount_due": data["amount_due"],
                            "amount_paid": amount_paid,
                            "purchase_notes": charge_month,
                            "purchase_date": charge_date,
                            "purchase_frequency": data["purchase_frequency"],
                            "payment_frequency": data["payment_frequency"],
                            "next_payment": data["next_payment"]
                        }
                        newPurchaseID = db.call('new_purchase_id')[
                            'result'][0]['new_id']
                        newPurchase['purchase_uid'] = newPurchaseID
                        newPurchase['purchase_status'] = data['purchase_status']
                        response = db.insert('purchases', newPurchase)

                elif data['splitPercentOwner'] != '0' and data['splitPercentManager'] == '0':
                    if data['purchase_frequency'] == 'Monthly':
                        print('here monthly')
                        charge_date = date.today()
                        next_payment = date.fromisoformat(data['next_payment'])
                        print('here monthly', next_payment)
                        while charge_date <= next_payment:
                            charge_month = charge_date.strftime('%B')

                            print('in new purchase')
                            if data['purchase_status'] == 'PAID':
                                amount_paid = data['amount_due']
                            else:
                                amount_paid = 0
                            newPurchase = {
                                "linked_bill_id": None,
                                "pur_property_id": json.dumps([data['pur_property_id']]),
                                "payer": json.dumps([data.get('payerID')]),
                                "receiver": data['managerID'],
                                "purchase_type": data['purchase_type'].upper(),
                                "description": data['description'],
                                "amount_due": data["amount_due"],
                                "amount_paid": amount_paid,
                                "purchase_notes": charge_month,
                                "purchase_date": charge_date,
                                "purchase_frequency": data["purchase_frequency"],
                                "payment_frequency": data["payment_frequency"],
                                "next_payment": data["next_payment"]
                            }
                            newPurchaseID = db.call('new_purchase_id')[
                                'result'][0]['new_id']

                            newPurchase['purchase_uid'] = newPurchaseID
                            newPurchase['purchase_status'] = data['purchase_status']
                            response = db.insert('purchases', newPurchase)

                            charge_date += relativedelta(months=1)

                            newPurchase = {
                                "linked_bill_id": None,
                                "pur_property_id": json.dumps([data['pur_property_id']]),
                                "payer": json.dumps([data.get('managerID')]),
                                "receiver": data['ownerID'],
                                "purchase_type": 'OWNER PAYMENT' + ' ' + data['purchase_type'].upper(),
                                "description": data['description'],
                                "amount_due": data["amount_due"],
                                "amount_paid": amount_paid,
                                "purchase_notes": charge_month,
                                "purchase_date": charge_date,
                                "purchase_frequency": data["purchase_frequency"],
                                "payment_frequency": data["payment_frequency"],
                                "next_payment": data["next_payment"]
                            }
                            newPurchaseID = db.call('new_purchase_id')[
                                'result'][0]['new_id']

                            newPurchase['purchase_uid'] = newPurchaseID
                            newPurchase['purchase_status'] = data['purchase_status']
                            response = db.insert('purchases', newPurchase)

                            charge_date += relativedelta(months=1)

                    elif data['purchase_frequency'] == 'Annually':
                        print('here annually')
                        charge_date = date.today()
                        next_payment = date.fromisoformat(data['next_payment'])
                        while charge_date <= next_payment:
                            charge_month = charge_date.strftime('%B')

                            print('in new purchase')
                            if data['purchase_status'] == 'PAID':
                                amount_paid = data['amount_due']
                            else:
                                amount_paid = 0
                            newPurchase = {
                                "linked_bill_id": None,
                                "pur_property_id": json.dumps([data['pur_property_id']]),
                                "payer": json.dumps([data.get('payerID')]),
                                "receiver": data['managerID'],
                                "purchase_type": data['purchase_type'].upper(),
                                "description": data['description'],
                                "amount_due": data["amount_due"],
                                "amount_paid": amount_paid,
                                "purchase_notes": charge_month,
                                "purchase_date": charge_date,
                                "purchase_frequency": data["purchase_frequency"],
                                "payment_frequency": data["payment_frequency"],
                                "next_payment": data["next_payment"]
                            }
                            newPurchaseID = db.call('new_purchase_id')[
                                'result'][0]['new_id']

                            newPurchase['purchase_uid'] = newPurchaseID
                            newPurchase['purchase_status'] = data['purchase_status']
                            response = db.insert('purchases', newPurchase)

                            charge_date += relativedelta(months=12)

                            newPurchase = {
                                "linked_bill_id": None,
                                "pur_property_id": json.dumps([data['pur_property_id']]),
                                "payer": json.dumps([data.get('managerID')]),
                                "receiver": data['ownerID'],
                                "purchase_type": 'OWNER PAYMENT' + ' ' + data['purchase_type'].upper(),
                                "description": data['description'],
                                "amount_due": data["amount_due"],
                                "amount_paid": amount_paid,
                                "purchase_notes": charge_month,
                                "purchase_date": charge_date,
                                "purchase_frequency": data["purchase_frequency"],
                                "payment_frequency": data["payment_frequency"],
                                "next_payment": data["next_payment"]
                            }
                            newPurchaseID = db.call('new_purchase_id')[
                                'result'][0]['new_id']

                            newPurchase['purchase_uid'] = newPurchaseID
                            newPurchase['purchase_status'] = data['purchase_status']
                            response = db.insert('purchases', newPurchase)

                            charge_date += relativedelta(months=12)
                            # return purchaseResponse
                    else:
                        print('here one-time')
                        charge_date = date.fromisoformat(data['next_payment'])
                        charge_month = charge_date.strftime('%B')

                        print('in new purchase')
                        if data['purchase_status'] == 'PAID':
                            amount_paid = data['amount_due']
                        else:
                            amount_paid = 0
                        newPurchase = {
                            "linked_bill_id": None,
                            "pur_property_id": json.dumps([data['pur_property_id']]),
                            "payer": json.dumps([data.get('payerID')]),
                            "receiver": data['managerID'],
                            "purchase_type": data['purchase_type'].upper(),
                            "description": data['description'],
                            "amount_due": data["amount_due"],
                            "amount_paid": amount_paid,
                            "purchase_notes": charge_month,
                            "purchase_date": charge_date,
                            "purchase_frequency": data["purchase_frequency"],
                            "payment_frequency": data["payment_frequency"],
                            "next_payment": data["next_payment"]
                        }
                        newPurchaseID = db.call('new_purchase_id')[
                            'result'][0]['new_id']
                        newPurchase['purchase_uid'] = newPurchaseID
                        newPurchase['purchase_status'] = data['purchase_status']
                        response = db.insert('purchases', newPurchase)

                        newPurchase = {
                            "linked_bill_id": None,
                            "pur_property_id": json.dumps([data['pur_property_id']]),
                            "payer": json.dumps([data.get('managerID')]),
                            "receiver": data['ownerID'],
                            "purchase_type": 'OWNER PAYMENT' + ' ' + data['purchase_type'].upper(),
                            "description": data['description'],
                            "amount_due": data["amount_due"],
                            "amount_paid": amount_paid,
                            "purchase_notes": charge_month,
                            "purchase_date": charge_date,
                            "purchase_frequency": data["purchase_frequency"],
                            "payment_frequency": data["payment_frequency"],
                            "next_payment": data["next_payment"]
                        }
                        newPurchaseID = db.call('new_purchase_id')[
                            'result'][0]['new_id']
                        newPurchase['purchase_uid'] = newPurchaseID
                        newPurchase['purchase_status'] = data['purchase_status']
                        response = db.insert('purchases', newPurchase)
                else:
                    print('do nothing')
            elif data['payer'] == 'PROPERTY MANAGER':
                if data['splitPercentTenant'] != '0' and data['splitPercentOwner'] != '0':
                    if data['purchase_frequency'] == 'Monthly':
                        print('here monthly')
                        charge_date = date.today()
                        next_payment = date.fromisoformat(data['next_payment'])
                        print('here monthly', next_payment)
                        charge_month = charge_date.strftime('%B')

                        print('in new purchase')
                        amount_due = int(data["amount_due"]) * \
                            (int(data['splitPercentTenant'])/100)
                        if data['purchase_status'] == 'PAID':
                            amount_paid = amount_due
                        else:
                            amount_paid = 0
                        newPurchase = {
                            "linked_bill_id": None,
                            "pur_property_id": json.dumps([data['pur_property_id']]),
                            "payer": json.dumps([data.get('payerID')]),
                            "receiver": data['tenantID'],
                            "purchase_type": data['purchase_type'].upper(),
                            "description": data['description'],
                            "amount_due": amount_due,
                            "amount_paid": amount_paid,
                            "purchase_notes": charge_month,
                            "purchase_date": charge_date,
                            "purchase_frequency": data["purchase_frequency"],
                            "payment_frequency": data["payment_frequency"],
                            "next_payment": data["next_payment"]
                        }
                        newPurchaseID = db.call('new_purchase_id')[
                            'result'][0]['new_id']

                        newPurchase['purchase_uid'] = newPurchaseID
                        newPurchase['purchase_status'] = data['purchase_status']
                        response = db.insert('purchases', newPurchase)

                        charge_date += relativedelta(months=1)
                        amount_due = int(data["amount_due"]) * \
                            (int(data['splitPercentOwner'])/100)
                        if data['purchase_status'] == 'PAID':
                            amount_paid = amount_due
                        else:
                            amount_paid = 0
                        newPurchase = {
                            "linked_bill_id": None,
                            "pur_property_id": json.dumps([data['pur_property_id']]),
                            "payer": json.dumps([data.get('payerID')]),
                            "receiver": data['ownerID'],
                            "purchase_type": data['purchase_type'].upper(),
                            "description": data['description'],
                            "amount_due": amount_due,
                            "amount_paid": amount_paid,
                            "purchase_notes": charge_month,
                            "purchase_date": charge_date,
                            "purchase_frequency": data["purchase_frequency"],
                            "payment_frequency": data["payment_frequency"],
                            "next_payment": data["next_payment"]
                        }
                        newPurchaseID = db.call('new_purchase_id')[
                            'result'][0]['new_id']

                        newPurchase['purchase_uid'] = newPurchaseID
                        newPurchase['purchase_status'] = data['purchase_status']
                        responseOwner = db.insert('purchases', newPurchase)

                        charge_date += relativedelta(months=1)

                    elif data['purchase_frequency'] == 'Annually':
                        print('here annually')
                        charge_date = date.today()
                        next_payment = date.fromisoformat(data['next_payment'])

                        charge_month = charge_date.strftime('%B')

                        print('in new purchase')
                        amount_due = int(data["amount_due"]) * \
                            (int(data['splitPercentTenant'])/100)
                        if data['purchase_status'] == 'PAID':
                            amount_paid = amount_due
                        else:
                            amount_paid = 0
                        newPurchase = {
                            "linked_bill_id": None,
                            "pur_property_id": json.dumps([data['pur_property_id']]),
                            "payer": json.dumps([data.get('payerID')]),
                            "receiver": data['tenantID'],
                            "purchase_type": data['purchase_type'].upper(),
                            "description": data['description'],
                            "amount_due": amount_due,
                            "amount_paid": amount_paid,
                            "purchase_notes": charge_month,
                            "purchase_date": charge_date,
                            "purchase_frequency": data["purchase_frequency"],
                            "payment_frequency": data["payment_frequency"],
                            "next_payment": data["next_payment"]
                        }
                        newPurchaseID = db.call('new_purchase_id')[
                            'result'][0]['new_id']

                        newPurchase['purchase_uid'] = newPurchaseID
                        newPurchase['purchase_status'] = data['purchase_status']
                        response = db.insert('purchases', newPurchase)

                        charge_date += relativedelta(months=12)

                        amount_due = int(data["amount_due"]) * \
                            (int(data['splitPercentOwner'])/100)
                        if data['purchase_status'] == 'PAID':
                            amount_paid = amount_due
                        else:
                            amount_paid = 0
                        newPurchase = {
                            "linked_bill_id": None,
                            "pur_property_id": json.dumps([data['pur_property_id']]),
                            "payer": json.dumps([data.get('payerID')]),
                            "receiver": data['ownerID'],
                            "purchase_type": data['purchase_type'].upper(),
                            "description": data['description'],
                            "amount_due": amount_due,
                            "amount_paid": amount_paid,
                            "purchase_notes": charge_month,
                            "purchase_date": charge_date,
                            "purchase_frequency": data["purchase_frequency"],
                            "payment_frequency": data["payment_frequency"],
                            "next_payment": data["next_payment"]
                        }
                        newPurchaseID = db.call('new_purchase_id')[
                            'result'][0]['new_id']

                        newPurchase['purchase_uid'] = newPurchaseID
                        newPurchase['purchase_status'] = data['purchase_status']
                        responseOwner = db.insert('purchases', newPurchase)

                        charge_date += relativedelta(months=12)
                        # return purchaseResponse
                    else:
                        print('here one-time')
                        charge_date = date.fromisoformat(data['next_payment'])
                        charge_month = charge_date.strftime('%B')

                        print('in new purchase')
                        amount_due = int(data["amount_due"]) * \
                            (int(data['splitPercentTenant'])/100)
                        if data['purchase_status'] == 'PAID':
                            amount_paid = amount_due
                        else:
                            amount_paid = 0
                        newPurchase = {
                            "linked_bill_id": None,
                            "pur_property_id": json.dumps([data['pur_property_id']]),
                            "payer": json.dumps([data.get('payerID')]),
                            "receiver": data['tenantID'],
                            "purchase_type": data['purchase_type'].upper(),
                            "description": data['description'],
                            "amount_due": amount_due,
                            "amount_paid": amount_paid,
                            "purchase_notes": charge_month,
                            "purchase_date": charge_date,
                            "purchase_frequency": data["purchase_frequency"],
                            "payment_frequency": data["payment_frequency"],
                            "next_payment": data["next_payment"]
                        }
                        newPurchaseID = db.call('new_purchase_id')[
                            'result'][0]['new_id']
                        newPurchase['purchase_uid'] = newPurchaseID
                        newPurchase['purchase_status'] = data['purchase_status']
                        response = db.insert('purchases', newPurchase)

                        amount_due = int(data["amount_due"]) * \
                            (int(data['splitPercentOwner'])/100)
                        if data['purchase_status'] == 'PAID':
                            amount_paid = amount_due
                        else:
                            amount_paid = 0
                        newPurchase = {
                            "linked_bill_id": None,
                            "pur_property_id": json.dumps([data['pur_property_id']]),
                            "payer": json.dumps([data.get('payerID')]),
                            "receiver": data['ownerID'],
                            "purchase_type": data['purchase_type'].upper(),
                            "description": data['description'],
                            "amount_due": amount_due,
                            "amount_paid": amount_paid,
                            "purchase_notes": charge_month,
                            "purchase_date": charge_date,
                            "purchase_frequency": data["purchase_frequency"],
                            "payment_frequency": data["payment_frequency"],
                            "next_payment": data["next_payment"]
                        }
                        newPurchaseID = db.call('new_purchase_id')[
                            'result'][0]['new_id']
                        newPurchase['purchase_uid'] = newPurchaseID
                        newPurchase['purchase_status'] = data['purchase_status']
                        responseOwner = db.insert('purchases', newPurchase)
                elif (data['splitPercentTenant']) != '0':
                    if data['purchase_frequency'] == 'Monthly':
                        print('here monthly')
                        charge_date = date.today()
                        next_payment = date.fromisoformat(data['next_payment'])
                        print('here monthly', next_payment)
                        charge_month = charge_date.strftime('%B')

                        print('in new purchase')

                        if data['purchase_status'] == 'PAID':
                            amount_paid = data['amount_due']
                        else:
                            amount_paid = 0
                        newPurchase = {
                            "linked_bill_id": None,
                            "pur_property_id": json.dumps([data['pur_property_id']]),
                            "payer": json.dumps([data.get('payerID')]),
                            "receiver": data['tenantID'],
                            "purchase_type": data['purchase_type'].upper(),
                            "description": data['description'],
                            "amount_due": data['amount_due'],
                            "amount_paid": amount_paid,
                            "purchase_notes": charge_month,
                            "purchase_date": charge_date,
                            "purchase_frequency": data["purchase_frequency"],
                            "payment_frequency": data["payment_frequency"],
                            "next_payment": data["next_payment"]
                        }
                        newPurchaseID = db.call('new_purchase_id')[
                            'result'][0]['new_id']

                        newPurchase['purchase_uid'] = newPurchaseID
                        newPurchase['purchase_status'] = data['purchase_status']
                        response = db.insert('purchases', newPurchase)

                    elif data['purchase_frequency'] == 'Annually':
                        print('here annually')
                        charge_date = date.today()
                        next_payment = date.fromisoformat(data['next_payment'])

                        charge_month = charge_date.strftime('%B')

                        print('in new purchase')

                        if data['purchase_status'] == 'PAID':
                            amount_paid = data['amount_due']
                        else:
                            amount_paid = 0
                        newPurchase = {
                            "linked_bill_id": None,
                            "pur_property_id": json.dumps([data['pur_property_id']]),
                            "payer": json.dumps([data.get('payerID')]),
                            "receiver": data['tenantID'],
                            "purchase_type": data['purchase_type'].upper(),
                            "description": data['description'],
                            "amount_due": data['amount_due'],
                            "amount_paid": amount_paid,
                            "purchase_notes": charge_month,
                            "purchase_date": charge_date,
                            "purchase_frequency": data["purchase_frequency"],
                            "payment_frequency": data["payment_frequency"],
                            "next_payment": data["next_payment"]
                        }
                        newPurchaseID = db.call('new_purchase_id')[
                            'result'][0]['new_id']

                        newPurchase['purchase_uid'] = newPurchaseID
                        newPurchase['purchase_status'] = data['purchase_status']
                        response = db.insert('purchases', newPurchase)

                        charge_date += relativedelta(months=12)

                    else:
                        print('here one-time')
                        charge_date = date.fromisoformat(data['next_payment'])
                        charge_month = charge_date.strftime('%B')

                        print('in new purchase')

                        if data['purchase_status'] == 'PAID':
                            amount_paid = data['amount_due']
                        else:
                            amount_paid = 0
                        newPurchase = {
                            "linked_bill_id": None,
                            "pur_property_id": json.dumps([data['pur_property_id']]),
                            "payer": json.dumps([data.get('payerID')]),
                            "receiver": data['tenantID'],
                            "purchase_type": data['purchase_type'].upper(),
                            "description": data['description'],
                            "amount_due": data["amount_due"],
                            "amount_paid": amount_paid,
                            "purchase_notes": charge_month,
                            "purchase_date": charge_date,
                            "purchase_frequency": data["purchase_frequency"],
                            "payment_frequency": data["payment_frequency"],
                            "next_payment": data["next_payment"]
                        }
                        newPurchaseID = db.call('new_purchase_id')[
                            'result'][0]['new_id']
                        newPurchase['purchase_uid'] = newPurchaseID
                        newPurchase['purchase_status'] = data['purchase_status']
                        response = db.insert('purchases', newPurchase)
                elif (data['splitPercentOwner']) != '0':
                    if data['purchase_frequency'] == 'Monthly':
                        print('here monthly')
                        charge_date = date.today()
                        next_payment = date.fromisoformat(data['next_payment'])
                        print('here monthly', next_payment)
                        charge_month = charge_date.strftime('%B')

                        print('in new purchase')

                        if data['purchase_status'] == 'PAID':
                            amount_paid = data['amount_due']
                        else:
                            amount_paid = 0
                        newPurchase = {
                            "linked_bill_id": None,
                            "pur_property_id": json.dumps([data['pur_property_id']]),
                            "payer": json.dumps([data.get('payerID')]),
                            "receiver": data['ownerID'],
                            "purchase_type": data['purchase_type'].upper(),
                            "description": data['description'],
                            "amount_due": data['amount_due'],
                            "amount_paid": amount_paid,
                            "purchase_notes": charge_month,
                            "purchase_date": charge_date,
                            "purchase_frequency": data["purchase_frequency"],
                            "payment_frequency": data["payment_frequency"],
                            "next_payment": data["next_payment"]
                        }
                        newPurchaseID = db.call('new_purchase_id')[
                            'result'][0]['new_id']

                        newPurchase['purchase_uid'] = newPurchaseID
                        newPurchase['purchase_status'] = data['purchase_status']
                        response = db.insert('purchases', newPurchase)

                    elif data['purchase_frequency'] == 'Annually':
                        print('here annually')
                        charge_date = date.today()
                        next_payment = date.fromisoformat(data['next_payment'])

                        charge_month = charge_date.strftime('%B')

                        print('in new purchase')

                        if data['purchase_status'] == 'PAID':
                            amount_paid = data['amount_due']
                        else:
                            amount_paid = 0
                        newPurchase = {
                            "linked_bill_id": None,
                            "pur_property_id": json.dumps([data['pur_property_id']]),
                            "payer": json.dumps([data.get('payerID')]),
                            "receiver": data['ownerID'],
                            "purchase_type": data['purchase_type'].upper(),
                            "description": data['description'],
                            "amount_due": data['amount_due'],
                            "amount_paid": amount_paid,
                            "purchase_notes": charge_month,
                            "purchase_date": charge_date,
                            "purchase_frequency": data["purchase_frequency"],
                            "payment_frequency": data["payment_frequency"],
                            "next_payment": data["next_payment"]
                        }
                        newPurchaseID = db.call('new_purchase_id')[
                            'result'][0]['new_id']

                        newPurchase['purchase_uid'] = newPurchaseID
                        newPurchase['purchase_status'] = data['purchase_status']
                        response = db.insert('purchases', newPurchase)

                        charge_date += relativedelta(months=12)

                    else:
                        print('here one-time')
                        charge_date = date.fromisoformat(data['next_payment'])
                        charge_month = charge_date.strftime('%B')

                        print('in new purchase')

                        if data['purchase_status'] == 'PAID':
                            amount_paid = data['amount_due']
                        else:
                            amount_paid = 0
                        newPurchase = {
                            "linked_bill_id": None,
                            "pur_property_id": json.dumps([data['pur_property_id']]),
                            "payer": json.dumps([data.get('payerID')]),
                            "receiver": data['ownerID'],
                            "purchase_type": data['purchase_type'].upper(),
                            "description": data['description'],
                            "amount_due": data["amount_due"],
                            "amount_paid": amount_paid,
                            "purchase_notes": charge_month,
                            "purchase_date": charge_date,
                            "purchase_frequency": data["purchase_frequency"],
                            "payment_frequency": data["payment_frequency"],
                            "next_payment": data["next_payment"]
                        }
                        newPurchaseID = db.call('new_purchase_id')[
                            'result'][0]['new_id']
                        newPurchase['purchase_uid'] = newPurchaseID
                        newPurchase['purchase_status'] = data['purchase_status']
                        response = db.insert('purchases', newPurchase)
            elif data['payer'] == 'OWNER':
                if data['splitPercentTenant'] != '0' and data['splitPercentManager'] != '0':
                    if data['purchase_frequency'] == 'Monthly':
                        print('here monthly')
                        charge_date = date.today()
                        next_payment = date.fromisoformat(data['next_payment'])
                        print('here monthly', next_payment)
                        charge_month = charge_date.strftime('%B')

                        print('in new purchase')

                        if data['purchase_status'] == 'PAID':
                            amount_paid = data['amount_due']
                        else:
                            amount_paid = 0
                        newPurchase = {
                            "linked_bill_id": None,
                            "pur_property_id": json.dumps([data['pur_property_id']]),
                            "payer": json.dumps([data.get('payerID')]),
                            "receiver": data['managerID'],
                            "purchase_type": data['purchase_type'].upper(),
                            "description": data['description'],
                            "amount_due": data['amount_due'],
                            "amount_paid": amount_paid,
                            "purchase_notes": charge_month,
                            "purchase_date": charge_date,
                            "purchase_frequency": data["purchase_frequency"],
                            "payment_frequency": data["payment_frequency"],
                            "next_payment": data["next_payment"]
                        }
                        newPurchaseID = db.call('new_purchase_id')[
                            'result'][0]['new_id']

                        newPurchase['purchase_uid'] = newPurchaseID
                        newPurchase['purchase_status'] = data['purchase_status']
                        response = db.insert('purchases', newPurchase)

                        charge_date += relativedelta(months=1)
                        amount_due = amount_due = int(data["amount_due"]) * \
                            (int(data['splitPercentTenant'])/100)
                        if data['purchase_status'] == 'PAID':
                            amount_paid = amount_due
                        else:
                            amount_paid = 0
                        newPurchase = {
                            "linked_bill_id": None,
                            "pur_property_id": json.dumps([data['pur_property_id']]),
                            "payer": json.dumps([data.get('managerID')]),
                            "receiver": data['tenantID'],
                            "purchase_type": data['purchase_type'].upper(),
                            "description": data['description'],
                            "amount_due": amount_due,
                            "amount_paid": amount_paid,
                            "purchase_notes": charge_month,
                            "purchase_date": charge_date,
                            "purchase_frequency": data["purchase_frequency"],
                            "payment_frequency": data["payment_frequency"],
                            "next_payment": data["next_payment"]
                        }
                        newPurchaseID = db.call('new_purchase_id')[
                            'result'][0]['new_id']

                        newPurchase['purchase_uid'] = newPurchaseID
                        newPurchase['purchase_status'] = data['purchase_status']
                        responseOwner = db.insert('purchases', newPurchase)

                        charge_date += relativedelta(months=1)

                    elif data['purchase_frequency'] == 'Annually':
                        print('here annually')
                        charge_date = date.today()
                        next_payment = date.fromisoformat(data['next_payment'])

                        charge_month = charge_date.strftime('%B')

                        print('in new purchase')

                        if data['purchase_status'] == 'PAID':
                            amount_paid = data['amount_due']
                        else:
                            amount_paid = 0
                        newPurchase = {
                            "linked_bill_id": None,
                            "pur_property_id": json.dumps([data['pur_property_id']]),
                            "payer": json.dumps([data.get('payerID')]),
                            "receiver": data['managerID'],
                            "purchase_type": data['purchase_type'].upper(),
                            "description": data['description'],
                            "amount_due": data['amount_due'],
                            "amount_paid": amount_paid,
                            "purchase_notes": charge_month,
                            "purchase_date": charge_date,
                            "purchase_frequency": data["purchase_frequency"],
                            "payment_frequency": data["payment_frequency"],
                            "next_payment": data["next_payment"]
                        }
                        newPurchaseID = db.call('new_purchase_id')[
                            'result'][0]['new_id']

                        newPurchase['purchase_uid'] = newPurchaseID
                        newPurchase['purchase_status'] = data['purchase_status']
                        response = db.insert('purchases', newPurchase)

                        charge_date += relativedelta(months=12)

                        amount_due = int(data["amount_due"]) * \
                            (int(data['splitPercentTenant'])/100)
                        if data['purchase_status'] == 'PAID':
                            amount_paid = amount_due
                        else:
                            amount_paid = 0
                        newPurchase = {
                            "linked_bill_id": None,
                            "pur_property_id": json.dumps([data['pur_property_id']]),
                            "payer": json.dumps([data.get('managerID')]),
                            "receiver": data['tenantID'],
                            "purchase_type": data['purchase_type'].upper(),
                            "description": data['description'],
                            "amount_due": amount_due,
                            "amount_paid": amount_paid,
                            "purchase_notes": charge_month,
                            "purchase_date": charge_date,
                            "purchase_frequency": data["purchase_frequency"],
                            "payment_frequency": data["payment_frequency"],
                            "next_payment": data["next_payment"]
                        }
                        newPurchaseID = db.call('new_purchase_id')[
                            'result'][0]['new_id']

                        newPurchase['purchase_uid'] = newPurchaseID
                        newPurchase['purchase_status'] = data['purchase_status']
                        responseOwner = db.insert('purchases', newPurchase)

                        charge_date += relativedelta(months=12)
                        # return purchaseResponse
                    else:
                        print('here one-time')
                        charge_date = date.fromisoformat(data['next_payment'])
                        charge_month = charge_date.strftime('%B')

                        print('in new purchase')
                        if data['purchase_status'] == 'PAID':
                            amount_paid = data['amount_due']
                        else:
                            amount_paid = 0
                        newPurchase = {
                            "linked_bill_id": None,
                            "pur_property_id": json.dumps([data['pur_property_id']]),
                            "payer": json.dumps([data.get('payerID')]),
                            "receiver": data['managerID'],
                            "purchase_type": data['purchase_type'].upper(),
                            "description": data['description'],
                            "amount_due":  data['amount_due'],
                            "amount_paid": amount_paid,
                            "purchase_notes": charge_month,
                            "purchase_date": charge_date,
                            "purchase_frequency": data["purchase_frequency"],
                            "payment_frequency": data["payment_frequency"],
                            "next_payment": data["next_payment"]
                        }
                        newPurchaseID = db.call('new_purchase_id')[
                            'result'][0]['new_id']
                        newPurchase['purchase_uid'] = newPurchaseID
                        newPurchase['purchase_status'] = data['purchase_status']
                        response = db.insert('purchases', newPurchase)

                        amount_due = int(data["amount_due"]) * \
                            (int(data['splitPercentTenant'])/100)
                        if data['purchase_status'] == 'PAID':
                            amount_paid = amount_due
                        else:
                            amount_paid = 0
                        newPurchase = {
                            "linked_bill_id": None,
                            "pur_property_id": json.dumps([data['pur_property_id']]),
                            "payer": json.dumps([data.get('managerID')]),
                            "receiver": data['tenantID'],
                            "purchase_type": data['purchase_type'].upper(),
                            "description": data['description'],
                            "amount_due": amount_due,
                            "amount_paid": amount_paid,
                            "purchase_notes": charge_month,
                            "purchase_date": charge_date,
                            "purchase_frequency": data["purchase_frequency"],
                            "payment_frequency": data["payment_frequency"],
                            "next_payment": data["next_payment"]
                        }
                        newPurchaseID = db.call('new_purchase_id')[
                            'result'][0]['new_id']
                        newPurchase['purchase_uid'] = newPurchaseID
                        newPurchase['purchase_status'] = data['purchase_status']
                        responseOwner = db.insert('purchases', newPurchase)
                elif (data['splitPercentTenant']) != '0' and data['splitPercentManager'] == '0':
                    if data['purchase_frequency'] == 'Monthly':
                        print('here monthly')
                        charge_date = date.today()
                        next_payment = date.fromisoformat(data['next_payment'])
                        print('here monthly', next_payment)
                        charge_month = charge_date.strftime('%B')

                        print('in new purchase')

                        if data['purchase_status'] == 'PAID':
                            amount_paid = data['amount_due']
                        else:
                            amount_paid = 0
                        newPurchase = {
                            "linked_bill_id": None,
                            "pur_property_id": json.dumps([data['pur_property_id']]),
                            "payer": json.dumps([data.get('payerID')]),
                            "receiver": data['managerID'],
                            "purchase_type": data['purchase_type'].upper(),
                            "description": data['description'],
                            "amount_due": data['amount_due'],
                            "amount_paid": amount_paid,
                            "purchase_notes": charge_month,
                            "purchase_date": charge_date,
                            "purchase_frequency": data["purchase_frequency"],
                            "payment_frequency": data["payment_frequency"],
                            "next_payment": data["next_payment"]
                        }
                        newPurchaseID = db.call('new_purchase_id')[
                            'result'][0]['new_id']

                        newPurchase['purchase_uid'] = newPurchaseID
                        newPurchase['purchase_status'] = data['purchase_status']
                        response = db.insert('purchases', newPurchase)

                        newPurchase = {
                            "linked_bill_id": None,
                            "pur_property_id": json.dumps([data['pur_property_id']]),
                            "payer": json.dumps([data.get('managerID')]),
                            "receiver": data['tenantID'],
                            "purchase_type": data['purchase_type'].upper(),
                            "description": data['description'],
                            "amount_due": data['amount_due'],
                            "amount_paid": amount_paid,
                            "purchase_notes": charge_month,
                            "purchase_date": charge_date,
                            "purchase_frequency": data["purchase_frequency"],
                            "payment_frequency": data["payment_frequency"],
                            "next_payment": data["next_payment"]
                        }
                        newPurchaseID = db.call('new_purchase_id')[
                            'result'][0]['new_id']

                        newPurchase['purchase_uid'] = newPurchaseID
                        newPurchase['purchase_status'] = data['purchase_status']
                        response = db.insert('purchases', newPurchase)

                    elif data['purchase_frequency'] == 'Annually':
                        print('here annually')
                        charge_date = date.today()
                        next_payment = date.fromisoformat(data['next_payment'])

                        charge_month = charge_date.strftime('%B')

                        print('in new purchase')

                        if data['purchase_status'] == 'PAID':
                            amount_paid = data['amount_due']
                        else:
                            amount_paid = 0
                        newPurchase = {
                            "linked_bill_id": None,
                            "pur_property_id": json.dumps([data['pur_property_id']]),
                            "payer": json.dumps([data.get('payerID')]),
                            "receiver": data['managerID'],
                            "purchase_type": data['purchase_type'].upper(),
                            "description": data['description'],
                            "amount_due": data['amount_due'],
                            "amount_paid": amount_paid,
                            "purchase_notes": charge_month,
                            "purchase_date": charge_date,
                            "purchase_frequency": data["purchase_frequency"],
                            "payment_frequency": data["payment_frequency"],
                            "next_payment": data["next_payment"]
                        }
                        newPurchaseID = db.call('new_purchase_id')[
                            'result'][0]['new_id']

                        newPurchase['purchase_uid'] = newPurchaseID
                        newPurchase['purchase_status'] = data['purchase_status']
                        response = db.insert('purchases', newPurchase)

                        charge_date += relativedelta(months=12)
                        newPurchase = {
                            "linked_bill_id": None,
                            "pur_property_id": json.dumps([data['pur_property_id']]),
                            "payer": json.dumps([data.get('managerID')]),
                            "receiver": data['tenantID'],
                            "purchase_type": data['purchase_type'].upper(),
                            "description": data['description'],
                            "amount_due": data['amount_due'],
                            "amount_paid": amount_paid,
                            "purchase_notes": charge_month,
                            "purchase_date": charge_date,
                            "purchase_frequency": data["purchase_frequency"],
                            "payment_frequency": data["payment_frequency"],
                            "next_payment": data["next_payment"]
                        }
                        newPurchaseID = db.call('new_purchase_id')[
                            'result'][0]['new_id']

                        newPurchase['purchase_uid'] = newPurchaseID
                        newPurchase['purchase_status'] = data['purchase_status']
                        response = db.insert('purchases', newPurchase)

                        charge_date += relativedelta(months=12)

                    else:
                        print('here one-time')
                        charge_date = date.fromisoformat(data['next_payment'])
                        charge_month = charge_date.strftime('%B')

                        print('in new purchase')

                        if data['purchase_status'] == 'PAID':
                            amount_paid = data['amount_due']
                        else:
                            amount_paid = 0
                        newPurchase = {
                            "linked_bill_id": None,
                            "pur_property_id": json.dumps([data['pur_property_id']]),
                            "payer": json.dumps([data.get('payerID')]),
                            "receiver": data['managerID'],
                            "purchase_type": data['purchase_type'].upper(),
                            "description": data['description'],
                            "amount_due": data["amount_due"],
                            "amount_paid": amount_paid,
                            "purchase_notes": charge_month,
                            "purchase_date": charge_date,
                            "purchase_frequency": data["purchase_frequency"],
                            "payment_frequency": data["payment_frequency"],
                            "next_payment": data["next_payment"]
                        }
                        newPurchaseID = db.call('new_purchase_id')[
                            'result'][0]['new_id']
                        newPurchase['purchase_uid'] = newPurchaseID
                        newPurchase['purchase_status'] = data['purchase_status']
                        response = db.insert('purchases', newPurchase)
                        newPurchase = {
                            "linked_bill_id": None,
                            "pur_property_id": json.dumps([data['pur_property_id']]),
                            "payer": json.dumps([data.get('managerID')]),
                            "receiver": data['tenantID'],
                            "purchase_type": data['purchase_type'].upper(),
                            "description": data['description'],
                            "amount_due": data["amount_due"],
                            "amount_paid": amount_paid,
                            "purchase_notes": charge_month,
                            "purchase_date": charge_date,
                            "purchase_frequency": data["purchase_frequency"],
                            "payment_frequency": data["payment_frequency"],
                            "next_payment": data["next_payment"]
                        }
                        newPurchaseID = db.call('new_purchase_id')[
                            'result'][0]['new_id']
                        newPurchase['purchase_uid'] = newPurchaseID
                        newPurchase['purchase_status'] = data['purchase_status']
                        response = db.insert('purchases', newPurchase)
                elif (data['splitPercentManager']) != '0':
                    if data['purchase_frequency'] == 'Monthly':
                        print('here monthly')
                        charge_date = date.today()
                        next_payment = date.fromisoformat(data['next_payment'])
                        print('here monthly', next_payment)
                        charge_month = charge_date.strftime('%B')

                        print('in new purchase')

                        if data['purchase_status'] == 'PAID':
                            amount_paid = data['amount_due']
                        else:
                            amount_paid = 0
                        newPurchase = {
                            "linked_bill_id": None,
                            "pur_property_id": json.dumps([data['pur_property_id']]),
                            "payer": json.dumps([data.get('payerID')]),
                            "receiver": data['managerID'],
                            "purchase_type": data['purchase_type'].upper(),
                            "description": data['description'],
                            "amount_due": data['amount_due'],
                            "amount_paid": amount_paid,
                            "purchase_notes": charge_month,
                            "purchase_date": charge_date,
                            "purchase_frequency": data["purchase_frequency"],
                            "payment_frequency": data["payment_frequency"],
                            "next_payment": data["next_payment"]
                        }
                        newPurchaseID = db.call('new_purchase_id')[
                            'result'][0]['new_id']

                        newPurchase['purchase_uid'] = newPurchaseID
                        newPurchase['purchase_status'] = data['purchase_status']
                        response = db.insert('purchases', newPurchase)

                    elif data['purchase_frequency'] == 'Annually':
                        print('here annually')
                        charge_date = date.today()
                        next_payment = date.fromisoformat(data['next_payment'])

                        charge_month = charge_date.strftime('%B')

                        print('in new purchase')

                        if data['purchase_status'] == 'PAID':
                            amount_paid = data['amount_due']
                        else:
                            amount_paid = 0
                        newPurchase = {
                            "linked_bill_id": None,
                            "pur_property_id": json.dumps([data['pur_property_id']]),
                            "payer": json.dumps([data.get('payerID')]),
                            "receiver": data['managerID'],
                            "purchase_type": data['purchase_type'].upper(),
                            "description": data['description'],
                            "amount_due": data['amount_due'],
                            "amount_paid": amount_paid,
                            "purchase_notes": charge_month,
                            "purchase_date": charge_date,
                            "purchase_frequency": data["purchase_frequency"],
                            "payment_frequency": data["payment_frequency"],
                            "next_payment": data["next_payment"]
                        }
                        newPurchaseID = db.call('new_purchase_id')[
                            'result'][0]['new_id']

                        newPurchase['purchase_uid'] = newPurchaseID
                        newPurchase['purchase_status'] = data['purchase_status']
                        response = db.insert('purchases', newPurchase)

                        charge_date += relativedelta(months=12)

                    else:
                        print('here one-time')
                        charge_date = date.fromisoformat(data['next_payment'])
                        charge_month = charge_date.strftime('%B')

                        print('in new purchase')

                        if data['purchase_status'] == 'PAID':
                            amount_paid = data['amount_due']
                        else:
                            amount_paid = 0
                        newPurchase = {
                            "linked_bill_id": None,
                            "pur_property_id": json.dumps([data['pur_property_id']]),
                            "payer": json.dumps([data.get('payerID')]),
                            "receiver": data['managerID'],
                            "purchase_type": data['purchase_type'].upper(),
                            "description": data['description'],
                            "amount_due": data["amount_due"],
                            "amount_paid": amount_paid,
                            "purchase_notes": charge_month,
                            "purchase_date": charge_date,
                            "purchase_frequency": data["purchase_frequency"],
                            "payment_frequency": data["payment_frequency"],
                            "next_payment": data["next_payment"]
                        }
                        newPurchaseID = db.call('new_purchase_id')[
                            'result'][0]['new_id']
                        newPurchase['purchase_uid'] = newPurchaseID
                        newPurchase['purchase_status'] = data['purchase_status']
                        response = db.insert('purchases', newPurchase)
                else:
                    print('do nothing')
            else:
                print('do nothing')
        return response


class DeletePurchase(Resource):
    def put(self):
        pur_response = {}
        with connect() as db:
            data = request.json
            delPurchase = {
                "purchase_status": 'DELETED'
            }
            pk = {
                'purchase_uid': data['purchase_uid']
            }
            pur_response = db.update("purchases", pk, delPurchase)
        return pur_response
