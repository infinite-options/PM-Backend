
from flask import request
from flask_restful import Resource

from data import connect
import json

class Properties(Resource):
    def get(self):
        response = {}
        filters = ['property_id', 'owner_id', 'manager_id', 'address', 'city',
            'state', 'zip', 'type', 'num_beds', 'num_baths', 'area', 'listed_rent', 'deposit',
            'appliances', 'utilities', 'pets_allowed', 'deposit_for_rent']
        where = {}
        for filter in filters:
            filterValue = request.args.get(filter)
            if filterValue is not None:
                where[filter] = filterValue
        with connect() as db:
            response = db.select('properties', where)
        return response

    def post(self):
        response = {}
        with connect() as db:
            data = request.get_json()
            fields = ['owner_id', 'manager_id', 'address', 'city', 'state',
                'zip', 'type', 'num_beds', 'num_baths', 'area', 'listed_rent', 'deposit',
                'appliances', 'utilities', 'pets_allowed', 'deposit_for_rent', 'picture']
            jsonFields = ['appliances', 'utilities']
            newProperty = {}
            for field in fields:
                newProperty[field] = data.get(field)
            for field in jsonFields:
                newProperty[field] = json.dumps(newProperty[field])
            newPropertyID = db.call('new_property_id')['result'][0]['new_id']
            newProperty['property_id'] = newPropertyID
            response = db.insert('properties', newProperty)
        return response
