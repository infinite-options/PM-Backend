
from flask import request
from flask_restful import Resource

from data import connect
import json

def newPurchase(linked_purchase_id, pur_property_id, payer, receiver, purchase_type,
description, amount_due, purchase_notes, purchase_date, purchase_frequency):
    response = {}
    with connect() as db:
        newPurchase = {
            'linked_purchase_id': linked_purchase_id,
            'pur_property_id': pur_property_id,
            'payer': payer,
            'receiver': receiver,
            'purchase_type': purchase_type,
            'description': description,
            'amount_due': amount_due,
            'purchase_notes': purchase_notes,
            'purchase_date': purchase_date,
            'purchase_frequency': purchase_frequency
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
        return newPurchase(
            data.get('linked_purchase_id'),
            data.get('pur_property_id'),
            data.get('payer'),
            data.get('receiver'),
            data.get('purchase_type'),
            data.get('description'),
            data.get('amount_due'),
            data.get('purchase_notes'),
            data.get('purchase_date'),
            data.get('purchase_frequency')
        )
