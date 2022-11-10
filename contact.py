
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from data import connect
import json
from datetime import datetime


class Contact(Resource):
    def get(self):
        response = {}
        filters = ['contact_uid', 'contact_type', 'contact_name',
                   'contact_email', 'contact_created_by']
        where = {}
        for filter in filters:
            filterValue = request.args.get(filter)
            if filterValue is not None:
                where[filter] = filterValue
        with connect() as db:
            for key in where:
                print(key)
                response = db.select('contacts', where)

                if key == 'contact_created_by':
                    businessResponse = db.execute("""
                    SELECT DISTINCT b.* FROM pm.properties prop
                    LEFT JOIN pm.propertyManager propm
                    ON prop.property_uid = propm.linked_property_id
                    LEFT JOIN pm.businesses b
                    ON propm.linked_business_id = b.business_uid
                    WHERE prop.owner_id = \'""" + where[key] + """\'
                    AND b.business_uid = propm.linked_business_id""")

                    if len(businessResponse['result']) > 0:
                        for br in businessResponse['result']:
                            print(br)
                            busi = {}
                            busi['contact_uid'] = br['business_uid']
                            busi['contact_name'] = br['business_name']
                            busi['contact_type'] = br['business_type']
                            busi['contact_email'] = br['business_email']
                            busi['contact_phone_number'] = br['business_phone_number']
                            busi['contact_created_by'] = where[key]
                            print(busi)
                            response['result'].append(busi)

                else:
                    response = db.select('contacts', where)
        return response

    def post(self):
        response = {}
        with connect() as db:
            data = request.json
            fields = ['type', 'name', 'email',
                      'phone_number', 'created_by']

            newContact = {}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    newContact[f'contact_{field}'] = fieldValue
                    print(newContact)
            newContactID = db.call('new_contact_id')['result'][0]['new_id']
            newContact['contact_uid'] = newContactID
            print(newContact)
            response = db.insert('contacts', newContact)

        return response

    def put(self):
        response = {}
        with connect() as db:
            data = request.json
            fields = ['type', 'name', 'email',
                      'phone_number', 'created_by']

            newContact = {}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    newContact[f'contact_{field}'] = fieldValue
            primaryKey = {
                'contact_uid': data.get('contact_uid')
            }
            response = db.update('contacts', primaryKey, newContact)
        return response
