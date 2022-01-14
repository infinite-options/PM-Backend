
from flask import request
from flask_restful import Resource

from data import connect
import json

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
                'subtotal',
                'amount_discount',
                'service_fee',
                'taxes',
                'amount_due',
                'amount_paid',
                'cc_num',
                'cc_exp_date',
                'cc_cvv',
                'cc_zip',
                'payment_type'
            ]
            newPayment = {}
            for field in fields:
                newPayment[field] = data.get(field)
            newPaymentID = db.call('new_payment_id')['result'][0]['new_id']
            newPayment['payment_uid'] = newPaymentID
            response = db.insert('payments', newPayment)
        return response
