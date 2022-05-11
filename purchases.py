
from flask import request
from flask_restful import Resource

from data import connect
from datetime import date
from dateutil.relativedelta import relativedelta
import json


def newPurchase(linked_purchase_id, pur_property_id, payer, receiver, purchase_type,
                description, amount_due, purchase_notes, purchase_date, purchase_frequency):
    response = {}
    print('in new purchase')
    with connect() as db:
        print('in new purchase')
        newPurchase = {
            "linked_purchase_id": linked_purchase_id,
            "pur_property_id": pur_property_id,
            "payer": payer,
            "receiver": receiver,
            "purchase_type": purchase_type,
            "description": description,
            "amount_due": amount_due,
            "purchase_notes": purchase_notes,
            "purchase_date": purchase_date,
            "purchase_frequency": purchase_frequency
        }
        newPurchaseID = db.call('new_purchase_id')['result'][0]['new_id']
        newPurchase['amount_paid'] = 0
        newPurchase['purchase_uid'] = newPurchaseID
        newPurchase['purchase_status'] = 'UNPAID'
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
            'linked_purchase_id',
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
        data = request.get_json()
        print(data)
        return newPurchase(
            data.get('linked_purchase_id'),
            data.get('pur_property_id'),
            json.dumps([data.get('payer')]),
            data.get('receiver'),
            data.get('purchase_type'),
            data.get('description'),
            data.get('amount_due'),
            data.get('purchase_notes'),
            data.get('purchase_date'),
            data.get('purchase_frequency')
        )


class CreateExpenses(Resource):

    def post(self):
        data = request.get_json()

        if data['purchase_frequency'] == 'Monthly':
            print('here monthly')
            charge_date = date.today()
            print('here monthly', charge_date)
            lease_end = date.fromisoformat(data['purchase_date'])
            print('here monthly', lease_end)
            while charge_date < lease_end:
                charge_month = charge_date.strftime('%B')
                with connect() as db:
                    print('in new purchase')
                    newPurchase = {
                        "linked_purchase_id": None,
                        "pur_property_id": data['pur_property_id'],
                        "payer": json.dumps([data.get('payer')]),
                        "receiver": data['receiver'],
                        "purchase_type": data['purchase_type'].upper(),
                        "description": data['description'],
                        "amount_due": data["amount_due"],
                        "amount_paid": data["amount_due"],
                        "purchase_notes": charge_month,
                        "purchase_date": data["purchase_date"],
                        "purchase_frequency": data["purchase_frequency"]
                    }
                    newPurchaseID = db.call('new_purchase_id')[
                        'result'][0]['new_id']

                    newPurchase['purchase_uid'] = newPurchaseID
                    newPurchase['purchase_status'] = 'PAID'
                    response = db.insert('purchases', newPurchase)
                # purchaseResponse = newPurchase(
                #     linked_purchase_id=None,
                #     pur_property_id=data['pur_property_id'],
                #     payer=json.dumps([data.get('payer')]),
                #     receiver=data['receiver'],
                #     purchase_type=data['purchase_type'],
                #     description=data['description'],
                #     amount_due=data['amount_due'],
                #     purchase_notes=charge_month,
                #     purchase_date=data['purchase_date'],
                #     purchase_frequency=data['purchase_frequency']
                # )
                # newPurchase['purchase_status'] = 'UNPAID'

                # print(purchaseResponse)
                    charge_date += relativedelta(months=1)
                # return purchaseResponse
        elif data['purchase_frequency'] == 'Annually':
            print('here annually')
            charge_date = date.today()
            lease_end = date.fromisoformat(data['purchase_date'])
            while charge_date < lease_end:
                charge_month = charge_date.strftime('%B')

                with connect() as db:
                    print('in new purchase')
                    newPurchase = {
                        "linked_purchase_id": None,
                        "pur_property_id": data['pur_property_id'],
                        "payer": json.dumps([data.get('payer')]),
                        "receiver": data['receiver'],
                        "purchase_type": data['purchase_type'].upper(),
                        "description": data['description'],
                        "amount_due": data["amount_due"],
                        "amount_paid": data["amount_due"],
                        "purchase_notes": charge_month,
                        "purchase_date": data["purchase_date"],
                        "purchase_frequency": data["purchase_frequency"]
                    }
                    newPurchaseID = db.call('new_purchase_id')[
                        'result'][0]['new_id']

                    newPurchase['purchase_uid'] = newPurchaseID
                    newPurchase['purchase_status'] = 'PAID'
                    response = db.insert('purchases', newPurchase)

                    charge_date += relativedelta(months=12)
                # return purchaseResponse
        else:
            print('here one-time')

            with connect() as db:
                print('in new purchase')
                newPurchase = {
                    "linked_purchase_id": None,
                    "pur_property_id": data['pur_property_id'],
                    "payer": json.dumps([data.get('payer')]),
                    "receiver": data['receiver'],
                    "purchase_type": data['purchase_type'].upper(),
                    "description": data['description'],
                    "amount_due": data["amount_due"],
                    "amount_paid": data["amount_due"],
                    "purchase_notes": '',
                    "purchase_date": data["purchase_date"],
                    "purchase_frequency": data["purchase_frequency"]
                }
                newPurchaseID = db.call('new_purchase_id')[
                    'result'][0]['new_id']
                newPurchase['purchase_uid'] = newPurchaseID
                newPurchase['purchase_status'] = 'PAID'
                response = db.insert('purchases', newPurchase)

        return response
