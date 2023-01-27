from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from data import connect, uploadImage
import boto3
from data import connect, uploadImage, s3
import json
from datetime import date, datetime, timedelta


def updateDocuments(documents, tenant_id):
    for i, doc in enumerate(documents):
        if 'link' in doc:
            bucket = 'io-pm'
            key = doc['link'].split('/io-pm/')[1]
            data = s3.get_object(
                Bucket=bucket,
                Key=key
            )
            doc['file'] = data['Body']
    s3Resource = boto3.resource('s3')
    bucket = s3Resource.Bucket('io-pm')
    bucket.objects.filter(Prefix=f'tenants/{tenant_id}/').delete()
    docs = []
    for i, doc in enumerate(documents):
        filename = f'doc_{i}'
        key = f'tenants/{tenant_id}/{filename}'
        link = uploadImage(doc['file'], key)
        doc['link'] = link
        del doc['file']
        docs.append(doc)
    return docs


class CheckTenantProfileComplete(Resource):
    decorators = [jwt_required()]

    def get(self):
        response = {}
        user = get_jwt_identity()
        where = {'tenant_id': user['user_uid']}
        print('where', where)
        with connect() as db:
            response = db.select('tenantProfileInfo', where)
            if len(response['result']) == 0:
                response['message'] = 'Incomplete Profile'
        return response


class TenantProfileInfo(Resource):
    decorators = [jwt_required()]

    def get(self):
        response = {}
        user = get_jwt_identity()
        where = {'tenant_id': user['user_uid']}

        with connect() as db:
            response = db.select('tenantProfileInfo', where)
        return response

    def post(self):
        response = {}
        user = get_jwt_identity()
        with connect() as db:
            data = request.form
            fields = ['tenant_first_name', 'tenant_last_name', 'tenant_phone_number', 'tenant_email', 'tenant_ssn', 'tenant_current_salary', 'tenant_salary_frequency', 'tenant_current_job_title',
                      'tenant_current_job_company', 'tenant_drivers_license_number', 'tenant_drivers_license_state', 'tenant_current_address', 'tenant_previous_address', 'tenant_adult_occupants', 'tenant_children_occupants', 'tenant_pet_occupants', 'tenant_vehicle_info', 'tenant_references']
            newProfileInfo = {'tenant_id': user['user_uid']}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    newProfileInfo[field] = fieldValue
            documents = json.loads(data.get('documents'))
            for i in range(len(documents)):
                filename = f'doc_{i}'
                file = request.files.get(filename)
                if file:
                    tenant_id = user['user_uid']
                    key = f'tenants/{tenant_id}/{filename}'
                    doc = uploadImage(file, key)
                    documents[i]['link'] = doc
                else:
                    break
            newProfileInfo['documents'] = json.dumps(documents)
            response = db.insert('tenantProfileInfo', newProfileInfo)
        return response

    def put(self):
        response = {}
        user = get_jwt_identity()
        with connect() as db:
            data = request.form
            fields = ['first_name', 'last_name', 'phone_number', 'email', 'ssn', 'current_salary', 'salary_frequency', 'current_job_title',
                      'current_job_company', 'drivers_license_number', 'drivers_license_state', 'current_address', 'previous_address', 'adult_occupants', 'children_occupants', 'pet_occupants', 'vehicle_info', 'references']
            newProfileInfo = {}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    newProfileInfo['tenant_'+field] = fieldValue
            documents = json.loads(data.get('documents'))
            for i, doc in enumerate(documents):
                filename = f'doc_{i}'
                file = request.files.get(filename)
                s3Link = doc.get('link')
                if file:
                    doc['file'] = file
                elif s3Link:
                    doc['link'] = s3Link
                else:
                    break
            documents = updateDocuments(documents,  user['user_uid'])
            newProfileInfo['documents'] = json.dumps(documents)
            primaryKey = {'tenant_id': user['user_uid']}
            response = db.update('tenantProfileInfo',
                                 primaryKey, newProfileInfo)
        return response


class TenantDetails(Resource):
    def get(self):
        response = {}
        filters = ['tenant_id']
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
                    WHERE tpi.tenant_id = \'""" + filterValue + """\'
                    AND (r.rental_status = 'ACTIVE' OR r.rental_status='PROCESSING')
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


class PropertiesTenantDetail(Resource):
    def get(self):
        response = {}
        filters = ['property_uid', 'tenant_id']
        where = {}
        with connect() as db:
            for filter in filters:
                filterValue1 = request.args.get(filters[0])

                filterValue2 = request.args.get(filters[1])
                print(filterValue1, filterValue2)
                if filterValue1 is not None:
                    where[filter] = filterValue1

                    response = db.execute(
                        """SELECT * FROM pm.properties p WHERE p.property_uid = \'"""
                        + filterValue1
                        + """\'""")
                    for i in range(len(response['result'])):
                        property_id = response['result'][i]['property_uid']
                        # print(property_id)
                        pid = {'linked_property_id': property_id}

                        maintenance_res = db.execute("""
                        SELECT mr.*,p.owner_id, p.property_uid, p.address, p.unit, p.city, p.state, p.zip
                        FROM pm.maintenanceRequests mr
                        LEFT JOIN pm.properties p
                        ON mr.property_uid = p.property_uid
                        WHERE mr.property_uid = \'""" + property_id + """\'
                        """)
                        response['result'][i]['maintenanceRequests'] = list(
                            maintenance_res['result'])

                        # print(maintenance_res['result'])
                        for y in range(len(maintenance_res['result'])):
                            req_id = maintenance_res['result'][y]['maintenance_request_uid']
                            rid = {'linked_request_uid': req_id}  # rid

                            # print(rid)
                            quotes_res = db.select(
                                ''' maintenanceQuotes quote ''', rid)
                            # print(quotes_res)
                            time_between_insertion = datetime.now() - \
                                datetime.strptime(
                                maintenance_res['result'][y]['request_created_date'], '%Y-%m-%d %H:%M:%S')
                            if ',' in str(time_between_insertion):
                                maintenance_res['result'][y]['days_open'] = int((str(time_between_insertion).split(',')[
                                    0]).split(' ')[0])
                            else:
                                maintenance_res['result'][y]['days_open'] = 1

                            maintenance_res['result'][y]['quotes'] = list(
                                quotes_res['result'])
                            if len(quotes_res['result']) > 0:
                                for quote in quotes_res['result']:
                                    if quote['quote_status'] == 'ACCEPTED':
                                        maintenance_res['result'][y]['total_estimate'] = quote['total_estimate']
                                    else:
                                        maintenance_res['result'][y]['total_estimate'] = 0
                            else:
                                maintenance_res['result'][y]['total_estimate'] = 0
                            maintenance_res['result'][y]['total_quotes'] = len(
                                quotes_res['result'])
                        property_res = db.execute("""
                        SELECT
                        p.address, p.unit, p.city, p.state,p.zip,
                        b.business_uid AS manager_id,
                        b.business_name AS manager_business_name,
                        b.business_email AS manager_email,
                        b.business_phone_number AS manager_phone_number
                        FROM pm.propertyManager pm
                        LEFT JOIN businesses b
                        ON b.business_uid = pm.linked_business_id
                        LEFT JOIN properties p
                        ON pm.linked_property_id = p.property_uid
                        WHERE pm.linked_property_id = \'""" + property_id + """\'
                        AND (pm.management_status = 'ACCEPTED' OR pm.management_status='END EARLY' OR pm.management_status='PM END EARLY' OR pm.management_status='OWNER END EARLY')   """)

                        response['result'][i]['property_manager'] = list(
                            property_res['result'])
                        app_res = db.execute("""
                        SELECT * FROM pm.applications a
                        WHERE a.property_uid= \'""" + property_id + """\'
                        AND a.tenant_id = \'""" + filterValue2 + """\'""")
                        response['result'][i]['applications'] = list(
                            app_res['result'])
                        rental_res = db.execute("""
                        SELECT
                        a.*,
                        r.*,
                        GROUP_CONCAT(lt.linked_tenant_id) as `tenant_id`,
                        GROUP_CONCAT(tpi.tenant_first_name) as `tenant_first_name`,
                        GROUP_CONCAT(tpi.tenant_last_name) as `tenant_last_name`,
                        GROUP_CONCAT(tpi.tenant_email) as `tenant_email`,
                        GROUP_CONCAT(tpi.tenant_phone_number) as `tenant_phone_number`
                        FROM pm.rentals r
                        LEFT JOIN pm.leaseTenants lt
                        ON lt.linked_rental_uid = r.rental_uid
                        LEFT JOIN pm.tenantProfileInfo tpi
                        ON tpi.tenant_id = lt.linked_tenant_id
                        LEFT JOIN pm.applications a
                        ON r.linked_application_id LIKE CONCAT('%', a.application_uid, '%') 
                        WHERE r.rental_property_id = \'""" + property_id + """\'
                        AND a.tenant_id = \'""" + filterValue2 + """\'
                        AND (r.rental_status = 'PROCESSING' OR r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED')
                        GROUP BY lt.linked_rental_uid""")
                        response['result'][i]['rentalInfo'] = list(
                            rental_res['result'])
                        if len(rental_res['result']) > 0:
                            response['result'][i]['rental_status'] = rental_res['result'][0]['rental_status']
                        else:
                            response['result'][i]['rental_status'] = ""

                        tenant_expenses = db.execute("""
                        SELECT *
                        FROM pm.purchases pu
                        LEFT JOIN
                        pm.payments pa
                        ON pa.pay_purchase_id = pu.purchase_uid
                        LEFT JOIN pm.properties p
                        ON pu.pur_property_id LIKE CONCAT('%', p.property_uid, '%')
                        WHERE pu.pur_property_id LIKE '%""" + property_id + """%'
                        AND pu.payer LIKE '%""" + filterValue2 + """%'
                        AND (pu.purchase_type= "RENT" OR pu.purchase_type= "EXTRA CHARGES" OR pu.purchase_type= "UTILITY")""")
                        response['result'][i]['tenantExpenses'] = []
                        if len(tenant_expenses['result']) > 0:
                            num_days = []
                            date = []
                            for ore in range(len(tenant_expenses['result'])):
                                print('here', tenant_expenses['result'][ore])
                                time_between_insertion = datetime.now() - \
                                    datetime.strptime(
                                        tenant_expenses['result'][ore]['next_payment'], '%Y-%m-%d %H:%M:%S')
                                print(time_between_insertion)
                                # if older than 30 days
                                if time_between_insertion.days > 30:
                                    print('older than 30 days')
                                    # if unpaid then all
                                    if tenant_expenses['result'][ore]['purchase_status'] == 'UNPAID':
                                        response['result'][i]['tenantExpenses'].append(
                                            (tenant_expenses['result'][ore]))
                                # if in future
                                elif time_between_insertion.days < 0:
                                    print('in future')
                                    # if utility or extra charges then all
                                    if tenant_expenses['result'][ore]['purchase_type'] != 'RENT':
                                        print('here no rents')
                                        print(
                                            'appended from here', tenant_expenses['result'][ore]['purchase_type'])
                                        if tenant_expenses['result'][ore]['purchase_frequency'] != 'Monthly':
                                            print(
                                                'appended from here purchase_frequency not monthly', tenant_expenses['result'][ore]['purchase_frequency'])
                                            response['result'][i]['tenantExpenses'].append(
                                                (tenant_expenses['result'][ore]))
                                        else:
                                            print(
                                                'appended from here monthly', tenant_expenses['result'][ore]['purchase_frequency'])
                                            num_days.append(datetime.strptime(
                                                tenant_expenses['result'][ore]['next_payment'], '%Y-%m-%d %H:%M:%S'))
                                    # add time differences in date, if rent get the most recent upcoming
                                    else:

                                        date.append(datetime.strptime(
                                            tenant_expenses['result'][ore]['next_payment'], '%Y-%m-%d %H:%M:%S'))
                                # if in the last 30 days
                                elif 0 <= time_between_insertion.days < 30:
                                    print('not older than 30 days not in future',
                                          time_between_insertion)

                                    response['result'][i]['tenantExpenses'].append(
                                        (tenant_expenses['result'][ore]))
                                # nothing if anything else
                                else:
                                    print('not older than 30 days',
                                          time_between_insertion.days)

                        for ore in range(len(tenant_expenses['result'])):
                            # upcoming 1 rent in the future
                            if tenant_expenses['result'][ore]['purchase_type'] == 'RENT':
                                if len(date) > 0:
                                    if datetime.strftime(min(
                                            date, key=lambda d: abs(d - datetime.now())), '%Y-%m-%d %H:%M:%S') == tenant_expenses['result'][ore]['next_payment']:
                                        print('next payment due',
                                              tenant_expenses['result'][ore])
                                        response['result'][i]['tenantExpenses'].append(
                                            (tenant_expenses['result'][ore]))
                            else:
                                if len(num_days) > 0:
                                    if datetime.strftime(min(
                                            num_days, key=lambda d: abs(d - datetime.now())), '%Y-%m-%d %H:%M:%S') == tenant_expenses['result'][ore]['next_payment']:
                                        print('next payment due',
                                              tenant_expenses['result'][ore])
                                        response['result'][i]['tenantExpenses'].append(
                                            (tenant_expenses['result'][ore]))

                        print('tenantExpenses',
                              response['result'][i]['tenantExpenses'])
                return response
