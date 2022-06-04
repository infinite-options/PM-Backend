from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from data import connect
from datetime import date
import json


class Bills(Resource):

    def get(self):
        response = {}
        filters = ['bill_property_id', 'bill_created_by', 'bill_utility_type']
        where = {}
        for filter in filters:
            filterValue = request.args.get(filter)
            if filterValue is not None:
                where[f'a.{filter}'] = filterValue
        with connect() as db:
            sql = 'SELECT  FROM bills b LEFT JOIN purchases p ON b.bill_uid = p.linked_purchase_id'
            cols = 'b.*, p.*'
            tables = 'bills b LEFT JOIN purchases p ON b.bill_uid = p.linked_purchase_id'
            response = db.select(cols=cols, tables=tables, where=where)
        return response

    def post(self):
        response = {}
        with connect() as db:
            data = request.form
            fields = ['bill_property_id', 'bill_created_by',
                      'bill_description', 'bill_utility_type', 'bill_distribution_type']
            newBill = {}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    newBill[field] = fieldValue
            newBillID = db.call('new_bill_id')['result'][0]['new_id']
            newBill['bill_uid'] = newBillID

            print(newBill)
            response = db.insert('bills', newBill)
        return response
