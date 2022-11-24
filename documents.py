from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from data import connect
import json
from datetime import date, datetime, timedelta


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


class OwnerDocuments(Resource):
    def get(self):
        response = {'message': 'Successfully committed SQL query',
                    'code': 200,
                    'result': []}
        filters = ['owner_id']
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
                    LEFT JOIN pm.propertyManager propM
                    ON prop.property_uid = propM.linked_property_id
                    LEFT JOIN pm.businesses b
                    ON propM.linked_business_id = b.business_uid
                    LEFT JOIN
                    pm.rentals r
                    ON r.rental_property_id = prop.property_uid
                    LEFT JOIN pm.leaseTenants lt
                    ON lt.linked_rental_uid = r.rental_uid
                    LEFT JOIN pm.tenantProfileInfo tpi
                    ON tpi.tenant_id = lt.linked_tenant_id
                    WHERE prop.owner_id = \'""" + filterValue + """\'
                    AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'PROCESSING' OR r.rental_status='TENANT APPROVED')
                    AND propM.management_status = 'ACCEPTED'
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
                    LEFT JOIN pm.propertyManager propM
                    ON prop.property_uid = propM.linked_property_id
                    LEFT JOIN pm.businesses b
                    ON propM.linked_business_id = b.business_uid
                    LEFT JOIN
                    pm.rentals r
                    ON r.rental_property_id = prop.property_uid
                    LEFT JOIN pm.leaseTenants lt
                    ON lt.linked_rental_uid = r.rental_uid
                    LEFT JOIN pm.tenantProfileInfo tpi
                    ON tpi.tenant_id = lt.linked_tenant_id
                    WHERE prop.owner_id = \'""" + filterValue + """\'
                    AND (r.rental_status = 'EXPIRED' OR r.rental_status = 'TERMINATED')
                    AND propM.management_status = 'ACCEPTED'
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
                    LEFT JOIN pm.contracts c
                    ON c.property_uid = prop.property_uid
                    LEFT JOIN pm.propertyManager propM
                    ON prop.property_uid = propM.linked_property_id
                    LEFT JOIN pm.businesses b
                    ON propM.linked_business_id = b.business_uid
                    LEFT JOIN pm.users u
                    ON prop.owner_id = u.user_uid
                    WHERE prop.owner_id = \'""" + filterValue + """\'
                    AND (propM.management_status= 'ACCEPTED' OR propM.management_status='END EARLY' OR propM.management_status='PM END EARLY' OR propM.management_status='OWNER END EARLY')
                    AND c.business_uid = propM.linked_business_id""")

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
                    LEFT JOIN pm.contracts c
                    ON c.property_uid = prop.property_uid
                    LEFT JOIN pm.propertyManager propM
                    ON prop.property_uid = propM.linked_property_id
                    LEFT JOIN pm.businesses b
                    ON propM.linked_business_id = b.business_uid
                    LEFT JOIN pm.users u
                    ON prop.owner_id = u.user_uid
                    WHERE prop.owner_id = \'""" + filterValue + """\'
                    AND propM.management_status <> 'ACCEPTED'
                    AND c.business_uid = propM.linked_business_id""")

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


class TenantDocuments(Resource):
    def get(self):
        response = {'message': 'Successfully committed SQL query',
                    'code': 200,
                    'result': []}
        filters = ['tenant_id']
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
                    WHERE tpi.tenant_id = \'""" + filterValue + """\'
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
                                    d['address'] = doc['address'] + ' ' + doc['unit'] + ', ' + \
                                        doc['city'] + ', ' + \
                                        doc['state'] + ' ' + doc['zip']
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
                    WHERE tpi.tenant_id = \'""" + filterValue + """\'
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
                                    d['address'] = doc['address'] + ' ' + doc['unit'] + ', ' + \
                                        doc['city'] + ', ' + \
                                        doc['state'] + ' ' + doc['zip']
                                    d['created_for'] = {'first_name': doc['tenant_first_name'],
                                                        'last_name': doc['tenant_last_name']}
                                    expired_lease_docs.append(d)
                    print(expired_lease_docs)

                    tenant_docs = db.execute("""
                    SELECT *
                    FROM tenantProfileInfo t
                    WHERE tenant_id  = \'""" + filterValue + """\'""")
                    tenant_uploaded_docs = []
                    if len(tenant_docs['result']) > 0:
                        print('expired lease docs')
                        for doc in tenant_docs['result']:
                            if len(json.loads(doc['documents'])) > 0:
                                for d in json.loads(doc['documents']):
                                    d['created_by'] = {'first_name': doc['tenant_first_name'],
                                                       'last_name': doc['tenant_last_name']}
                                    d['created_for'] = {'first_name': doc['tenant_first_name'],
                                                        'last_name': doc['tenant_last_name']}
                                    tenant_uploaded_docs.append(d)

                    response['result'] = [{
                        'active_lease_docs': list(active_lease_docs),
                        'past_lease_docs': list(expired_lease_docs),
                        'tenant_uploaded_docs': list(tenant_uploaded_docs),
                    }]

        return response
