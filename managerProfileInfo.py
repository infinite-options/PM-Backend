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
                    AND pm.management_status = 'ACCEPTED' OR pm.management_status='END EARLY' OR pm.management_status='PM END EARLY' OR pm.management_status='OWNER END EARLY'
                """)
            if len(response['result']) > 0:
                for i in range(len(response['result'])):
                    owner_properties = db.execute(""" SELECT * FROM properties p
                                                    LEFT JOIN propertyManager pm
                                                    ON pm.linked_property_id = p.property_uid
                                                    WHERE owner_id = \'""" + response['result'][i]['owner_id'] + """\'
                                                    AND pm.linked_business_id = \'""" + filterValue + """\'
                                                    AND pm.management_status = 'ACCEPTED' OR pm.management_status='END EARLY' OR pm.management_status='PM END EARLY' OR pm. management_status='OWNER END EARLY' """)
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
                        user_repairRequests = db.execute("""SELECT *
                                                            FROM pm.maintenanceRequests mr
                                                            LEFT JOIN pm.maintenanceQuotes mq
                                                            ON mq.linked_request_uid = mr.maintenance_request_uid
                                                            LEFT JOIN pm.businesses b
                                                            ON b.business_uid = mq.quote_business_uid
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


class ManagerDocuments(Resource):
    def get(self):
        response = {'message': 'Successfully committed SQL query',
                    'code': 200,
                    'result': []}
        filters = ['manager_id']
        where = {}

        with connect() as db:
            for filter in filters:
                filterValue = request.args.get(filter)
                if filterValue is not None:
                    where[filter] = filterValue
                    today = date.today()
                    # list of all active leases for the owner
                    lease_docs = db.execute("""
                    SELECT prop.*, b.*,r.*, GROUP_CONCAT(lt.linked_tenant_id) as `tenant_id`,
                    GROUP_CONCAT(tpi.tenant_first_name) as `tenant_first_name`,
                    GROUP_CONCAT(tpi.tenant_last_name) as `tenant_last_name`,
                    GROUP_CONCAT(tpi.tenant_email) as `tenant_email`,
                    GROUP_CONCAT(tpi.tenant_phone_number) as `tenant_phone_number`
                    FROM pm.properties prop
                    LEFT JOIN propertyManager pm
                    ON pm.linked_property_id=prop.property_uid
                    LEFT JOIN pm.businesses b
                    ON pm.linked_business_id = b.business_uid
                    LEFT JOIN
                    pm.rentals r
                    ON r.rental_property_id = prop.property_uid
                    LEFT JOIN pm.leaseTenants lt
                    ON lt.linked_rental_uid = r.rental_uid
                    LEFT JOIN pm.tenantProfileInfo tpi
                    ON tpi.tenant_id = lt.linked_tenant_id
                    WHERE pm.linked_business_id = \'""" + filterValue + """\'
                    AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'PROCESSING' OR r.rental_status='TENANT APPROVED')
                    AND pm.management_status = 'ACCEPTED'
                    GROUP BY lt.linked_rental_uid""")
                    active_lease_docs = []
                    if len(lease_docs['result']) > 0:
                        print('active lease docs')
                        for doc in lease_docs['result']:
                            if len(json.loads(doc['documents'])) > 0:
                                for d in json.loads(doc['documents']):
                                    d['expiry_date'] = doc['lease_end']
                                    d['created_date'] = doc['lease_start']
                                    d['created_by'] = doc['business_name']
                                    d['created_for'] = {'first_name': doc['tenant_first_name'],
                                                        'last_name': doc['tenant_last_name']}
                                    active_lease_docs.append(d)
                    print(active_lease_docs)

                    # list of all expired leases for the owner
                    past_lease_docs = db.execute("""
                    SELECT prop.*, b.*,r.*, GROUP_CONCAT(lt.linked_tenant_id) as `tenant_id`,
                    GROUP_CONCAT(tpi.tenant_first_name) as `tenant_first_name`,
                    GROUP_CONCAT(tpi.tenant_last_name) as `tenant_last_name`,
                    GROUP_CONCAT(tpi.tenant_email) as `tenant_email`,
                    GROUP_CONCAT(tpi.tenant_phone_number) as `tenant_phone_number`
                    FROM pm.properties prop
                    LEFT JOIN propertyManager pm
                    ON pm.linked_property_id=prop.property_uid
                    LEFT JOIN pm.businesses b
                    ON pm.linked_business_id = b.business_uid
                    LEFT JOIN
                    pm.rentals r
                    ON r.rental_property_id = prop.property_uid
                    LEFT JOIN pm.leaseTenants lt
                    ON lt.linked_rental_uid = r.rental_uid
                    LEFT JOIN pm.tenantProfileInfo tpi
                    ON tpi.tenant_id = lt.linked_tenant_id
                    WHERE pm.linked_business_id = \'""" + filterValue + """\'
                    AND (r.rental_status = 'EXPIRED' OR r.rental_status = 'TERMINATED')
                    AND pm.management_status = 'ACCEPTED'
                    GROUP BY lt.linked_rental_uid""")

                    expired_lease_docs = []
                    if len(past_lease_docs['result']) > 0:
                        print('expired lease docs')
                        for doc in past_lease_docs['result']:
                            if len(json.loads(doc['documents'])) > 0:
                                for d in json.loads(doc['documents']):
                                    d['expiry_date'] = doc['lease_end']
                                    d['created_date'] = doc['lease_start']
                                    d['created_by'] = doc['business_name']
                                    d['created_for'] = {'first_name': doc['tenant_first_name'],
                                                        'last_name': doc['tenant_last_name']}
                                    expired_lease_docs.append(d)
                    print(expired_lease_docs)

                    # list of all active pm contracts for the owner
                    manager_docs = db.execute("""
                    SELECT prop.*,b.*,c.*,u.*
                    FROM pm.properties prop
                    LEFT JOIN
                    pm.contracts c
                    ON c.property_uid = prop.property_uid
                    LEFT JOIN
                    pm.propertyManager pm
                    ON pm.linked_property_id = prop.property_uid
                    LEFT JOIN pm.businesses b
                    ON pm.linked_business_id = b.business_uid
                    LEFT JOIN pm.users u
                    ON prop.owner_id = u.user_uid
                    WHERE pm.linked_business_id = \'""" + filterValue + """\'
                    AND (pm.management_status= 'ACCEPTED' OR pm.management_status='END EARLY' OR pm.management_status='PM END EARLY' OR pm.management_status='OWNER END EARLY')
                    AND c.business_uid = pm.linked_business_id""")

                    active_manager_docs = []
                    if len(manager_docs['result']) > 0:
                        print('active manager docs')
                        for doc in manager_docs['result']:
                            if len(json.loads(doc['documents'])) > 0:
                                for d in json.loads(doc['documents']):
                                    d['expiry_date'] = doc['end_date']
                                    d['created_date'] = doc['start_date']
                                    d['created_by'] = doc['first_name'] + \
                                        ' ' + doc['last_name']
                                    d['created_for'] = doc['business_name']
                                    active_manager_docs.append(d)
                    print(active_manager_docs)

                    # list of all active pm contracts for the owner
                    past_manager_docs = db.execute("""
                    SELECT prop.*,b.*,c.*,u.*
                    FROM pm.properties prop
                    LEFT JOIN
                    pm.contracts c
                    ON c.property_uid = prop.property_uid
                    LEFT JOIN
                    pm.propertyManager pm
                    ON pm.linked_property_id = prop.property_uid
                    LEFT JOIN pm.businesses b
                    ON pm.linked_business_id = b.business_uid
                    LEFT JOIN pm.users u
                    ON prop.owner_id = u.user_uid
                    WHERE pm.linked_business_id = \'""" + filterValue + """\'
                    AND pm.management_status <> 'ACCEPTED'
                    AND c.business_uid = pm.linked_business_id""")
                    expired_manager_docs = []
                    if len(past_manager_docs['result']) > 0:
                        print('past manager docs')
                        for doc in past_manager_docs['result']:
                            if len(json.loads(doc['documents'])) > 0:
                                for d in json.loads(doc['documents']):
                                    d['expiry_date'] = doc['end_date']
                                    d['created_date'] = doc['start_date']
                                    d['created_by'] = doc['first_name'] + \
                                        ' ' + doc['last_name']
                                    d['created_for'] = doc['business_name']
                                    expired_manager_docs.append(d)
                    print(expired_manager_docs)

                    response['result'] = [{
                        'active_lease_docs': list(active_lease_docs),
                        'past_lease_docs': list(expired_lease_docs),
                        'active_manager_docs': list(active_manager_docs),
                        'past_manager_docs': list(expired_manager_docs)
                    }]

        return response
