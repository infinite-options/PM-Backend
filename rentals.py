
from flask import request
from flask_restful import Resource

from data import connect
import json

class Rentals(Resource):
    def get(self):
        filters = ['rental_uid', 'rental_property_id', 'tenant_id', 'rental_status']
        where = {}
        for filter in filters:
            filterValue = request.args.get(filter)
            if filterValue is not None:
                where[filter] = filterValue
        with connect() as db:
            response = db.select('rentals', where)
        return response

    def post(self):
        response = {}
        with connect() as db:
            data = request.get_json()
            fields = ['rental_property_id', 'tenant_id', 'actual_rent', 'lease_start', 'lease_end']
            newRental = {}
            for field in fields:
                newRental[field] = data.get(field)
            newRentalID = db.call('new_rental_id')['result'][0]['new_id']
            newRental['rental_uid'] = newRentalID
            newRental['rental_status'] = 'ACTIVE'
            response = db.insert('rentals', newRental)
        return response
