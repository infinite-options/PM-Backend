
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

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
                'amount_due',
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
        return response


class UserPayments(Resource):
    decorators = [jwt_required()]
    def get(self):
        response = {}
        user = get_jwt_identity()
        with connect() as db:
            sql = '''
                SELECT * FROM payments p1 LEFT JOIN purchases p2 ON pay_purchase_id = purchase_uid
                WHERE p2.payer = %(user_uid)s
            '''
            args = {
                'user_uid': user['user_uid']
            }
            filters = ['pur_property_id']
            for filter in filters:
                filterValue = request.args.get(filter)
                if filterValue is not None:
                    sql += f" AND {filter} = %({filter})s"
                    args[filter] = filterValue
            response = db.execute(sql, args)
        return response
