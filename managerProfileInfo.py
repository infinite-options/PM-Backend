from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from data import connect
import json
from datetime import date, datetime, timedelta


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
                    AND (pm.management_status = 'ACCEPTED' OR pm.management_status='END EARLY' OR pm.management_status='PM END EARLY' OR pm.management_status='OWNER END EARLY' OR pm.management_status='SENT')
                """)
            if len(response['result']) > 0:
                for i in range(len(response['result'])):
                    owner_properties = db.execute(""" 
                    SELECT * FROM properties p
                    LEFT JOIN propertyManager pm
                    ON pm.linked_property_id = p.property_uid
                    LEFT JOIN pm.contracts c
                    ON c.property_uid = p.property_uid
                    WHERE owner_id = \'""" + response['result'][i]['owner_id'] + """\'
                    AND pm.linked_business_id = \'""" + filterValue + """\'
                    AND (pm.management_status = 'ACCEPTED' OR pm.management_status='END EARLY' OR pm.management_status='PM END EARLY' OR pm. management_status='OWNER END EARLY')
                    AND c.contract_status='ACTIVE'
                    AND c.business_uid= pm.linked_business_id """)
                    response['result'][i]['properties'] = list(
                        owner_properties['result'])

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
                    SELECT DISTINCT tpi.*, r.*, p.*
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
                    AND (pm.management_status = 'ACCEPTED' OR pm.management_status='END EARLY' OR pm.management_status='PM END EARLY' OR pm.management_status='OWNER END EARLY')
                    AND r.rental_status = 'ACTIVE'
                """)
                if len(response['result']) > 0:
                    for i in range(len(response['result'])):
                        user_payments = db.execute("""SELECT * FROM payments p1 LEFT JOIN purchases p2 ON pay_purchase_id = purchase_uid
                                        WHERE p2.payer LIKE '%""" + response['result'][i]['tenant_id'] + """%'
                                    """)
                        response['result'][i]['user_payments'] = list(
                            user_payments['result'])
                        user_repairRequests = db.execute("""
                        SELECT mr.*, p.address, p.unit, p.city, p.state, p.zip
                        FROM pm.maintenanceRequests mr
                        LEFT JOIN pm.maintenanceQuotes mq
                        ON mq.linked_request_uid = mr.maintenance_request_uid
                        LEFT JOIN pm.businesses b
                        ON b.business_uid = mq.quote_business_uid
                        LEFT JOIN pm.properties p
                        ON mr.property_uid = p.property_uid
                        WHERE mr.property_uid = \'""" + response['result'][i]['property_uid'] + """\'
                                                            """)
                        response['result'][i]['user_repairRequests'] = list(
                            user_repairRequests['result'])
                        if len(user_repairRequests['result']) > 0:
                            for y in range(len(user_repairRequests['result'])):
                                time_between_insertion = datetime.now() - \
                                    datetime.strptime(
                                        user_repairRequests['result'][y]['request_created_date'], '%Y-%m-%d %H:%M:%S')
                                if ',' in str(time_between_insertion):
                                    user_repairRequests['result'][y]['days_open'] = int(
                                        (str(time_between_insertion).split(',')[0]).split(' ')[0])
                                else:
                                    user_repairRequests['result'][y]['days_open'] = 1

        return response
