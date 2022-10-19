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
    for i, doc in enumerate(documents):
        filename = f'doc_{i}'
        key = f'tenants/{tenant_id}/{filename}'
        link = uploadImage(doc['file'], key)
        doc['link'] = link
        del doc['file']
    return documents


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
                      'tenant_current_job_company', 'tenant_drivers_license_number', 'tenant_drivers_license_state', 'tenant_current_address', 'tenant_previous_address']
            newProfileInfo = {'tenant_id': user['user_uid']}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    newProfileInfo[field] = fieldValue
                if field == 'documents':
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
                    documents = updateDocuments(documents, user['user_uid'])
                    newProfileInfo['documents'] = json.dumps(documents)
            #     fieldValue = data.get(field)
            #     if fieldValue:
            #         newProfileInfo['tenant_'+field] = fieldValue
            # documents = json.loads(data.get('documents'))
            # for i in range(len(documents)):
            #     filename = f'doc_{i}'
            #     file = request.files.get(filename)
            #     if file:
            #         key = f"tenants/{user['user_uid']}/{filename}"
            #         doc = uploadImage(file, key)
            #         documents[i]['link'] = doc
            #     else:
            #         break
            # newProfileInfo['documents'] = json.dumps(documents)
            response = db.insert('tenantProfileInfo', newProfileInfo)
        return response

    def put(self):
        response = {}
        user = get_jwt_identity()
        with connect() as db:
            data = request.form
            fields = ['first_name', 'last_name', 'phone_number', 'email', 'ssn', 'current_salary', 'salary_frequency', 'current_job_title',
                      'current_job_company', 'drivers_license_number', 'drivers_license_state', 'current_address', 'previous_address']
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
            documents = updateDocuments(documents, user['user_uid'])
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
                                    user_repairRequests['result'][y]['days_open'] = 0

        return response
