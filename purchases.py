
from flask import request
from flask_restful import Resource

from data import connect
import json

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
        response = {}
        with connect() as db:
            data = request.get_json()
            fields = [
                'linked_purchase_id',
                'pur_property_id',
                'payer',
                'receiver',
                'purchase_type',
                'description',
                'amount',
                'purchase_notes'
            ]
            newPurchase = {}
            for field in fields:
                newPurchase[field] = data.get(field)
            newPurchaseID = db.call('new_purchase_id')['result'][0]['new_id']
            newPurchase['purchase_uid'] = newPurchaseID
            newPurchase['purchase_status'] = 'UNPAID'
            response = db.insert('purchases', newPurchase)
        return response
