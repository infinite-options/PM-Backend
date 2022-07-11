from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from data import connect
import json


class ManagerProfileInfo(Resource):
    decorators = [jwt_required()]

    def get(self):
        response = {}
        user = get_jwt_identity()
        where = {'manager_id': user['user_uid']}
        with connect() as db:
            response = db.select('managerProfileInfo', where)
        return response

    def post(self):
        response = {}
        user = get_jwt_identity()
        with connect() as db:
            data = request.get_json()
            fields = ['first_name', 'last_name', 'phone_number', 'email',
                      'ein_number', 'ssn', 'paypal', 'apple_pay', 'zelle', 'venmo',
                      'account_number', 'routing_number', 'fees', 'locations']
            jsonFields = ['fees', 'locations']
            newProfileInfo = {'manager_id': user['user_uid']}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    if field in jsonFields:
                        newProfileInfo['manager_' +
                                       field] = json.dumps(fieldValue)
                    else:
                        newProfileInfo['manager_'+field] = fieldValue
            response = db.insert('managerProfileInfo', newProfileInfo)
        return response

    def put(self):
        response = {}
        user = get_jwt_identity()
        with connect() as db:
            data = request.get_json()
            fields = ['first_name', 'last_name', 'phone_number', 'email',
                      'ein_number', 'ssn', 'paypal', 'apple_pay', 'zelle', 'venmo',
                      'account_number', 'routing_number', 'fees', 'locations']
            jsonFields = ['fees', 'locations']
            newProfileInfo = {}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    if field in jsonFields:
                        newProfileInfo['manager_' +
                                       field] = json.dumps(fieldValue)
                    else:
                        newProfileInfo['manager_'+field] = fieldValue
            primaryKey = {'manager_id': user['user_uid']}
            response = db.update('managerProfileInfo',
                                 primaryKey, newProfileInfo)
        return response


class ManagerClients(Resource):
    def get(self):
        response = {}
        filters = ['manager_id']
        where = {}
        with connect() as db:
            for filter in filters:
                filterValue = request.args.get(filter)
                if filterValue is not None:
                    where[filter] = filterValue
                response = db.execute("""
                    SELECT DISTINCT opi.* FROM properties p
                    LEFT JOIN propertyManager pm
                    ON pm.linked_property_id = p.property_uid
                    LEFT JOIN ownerProfileInfo opi
                    ON opi.owner_id = p.owner_id
                    WHERE pm.linked_business_id = \'""" + filterValue + """\'
                    AND pm.management_status = 'ACCEPTED'
                """)

        return response


class ManagerPropertyTenants(Resource):
    def get(self):
        response = {}
        filters = ['manager_id']
        where = {}
        with connect() as db:
            for filter in filters:
                filterValue = request.args.get(filter)
                if filterValue is not None:
                    where[filter] = filterValue
                response = db.execute("""
                    SELECT DISTINCT tpi.*                    
                    FROM properties p
                    LEFT JOIN propertyManager pm
                    ON pm.linked_property_id = p.property_uid
                    LEFT JOIN rentals r
                    ON r.rental_property_id = p.property_uid
                    LEFT JOIN leaseTenants lt
                    ON lt.linked_rental_uid = r.rental_uid
                    LEFT JOIN pm.tenantProfileInfo tpi
                    ON tpi.tenant_id = lt.linked_tenant_id
                    WHERE pm.linked_business_id = \'""" + filterValue + """\'
                    AND pm.management_status = 'ACCEPTED'
                    AND r.rental_status = 'ACTIVE'
                """)

        return response
