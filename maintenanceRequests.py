
from flask import request
from flask_restful import Resource

from data import connect, uploadImage, s3
import json
from datetime import datetime
import boto3


# If it is an s3 link, we save the file data into the attribute
# If it is a file, no need to worry about it, the data is already there.

def updateImages(imageFiles, maintenance_request_uid):
    content = []

    for filename in imageFiles:

        if type(imageFiles[filename]) == str:

            bucket = 'io-pm'
            key = imageFiles[filename].split('/io-pm/')[1]
            data = s3.get_object(
                Bucket=bucket,
                Key=key
            )
            imageFiles[filename] = data['Body']
            content.append(data['ContentType'])
        else:
            content.append('')

    s3Resource = boto3.resource('s3')
    bucket = s3Resource.Bucket('io-pm')
    bucket.objects.filter(
        Prefix=f'maintenanceRequests/{maintenance_request_uid}/').delete()
    images = []
    for i in range(len(imageFiles.keys())):

        filename = f'img_{i-1}'
        if i == 0:
            filename = 'img_cover'
        key = f'maintenanceRequests/{maintenance_request_uid}/{filename}'
        image = uploadImage(
            imageFiles[filename], key, content[i])

        images.append(image)
    return images


class MaintenanceRequests(Resource):
    def get(self):
        response = {}
        filters = ['maintenance_request_uid', 'property_uid', 'priority',
                   'assigned_business', 'assigned_worker', 'request_status', 'request_created_by', 'request_type', 'scheduled_time']

        where = {}
        res = {"message": '', "code": "", 'result': []}
        fv = []
        with connect() as db:
            for filter in filters:
                filterValue = request.args.get(filter)

                if filterValue is not None:
                    fv.append(filterValue)
                    where[filter] = filterValue
                    # print(filter)
                    # print(where[filter], where)
                    if filter == 'property_uid':
                        pf = where[filter].split(',')
                        # print('pf', pf)
                        for p in pf:
                            where[filter] = p
                            print('where', where)
                            response = db.select('maintenanceRequests', where)
                            print(len(response['result']))
                            # print((response['result'][0]))
                            if(len(response['result']) > 0):
                                # print('response', response['result'])
                                for r in response['result']:
                                    res["message"] = "Successfully executed SQL query"
                                    res["code"] = 200
                                    res["result"].append(r)
                                # res["result"] = r
                    if filter == 'maintenance_request_uid':
                        res = db.execute(""" SELECT * FROM 
                        maintenanceRequests mr
                        LEFT JOIN properties p
                        ON p.property_uid = mr.property_uid
                        WHERE maintenance_request_uid =  \'""" + where['maintenance_request_uid'] + """\' """)
                        # print(res)
                        for i in range(len(res['result'])):
                            req_id = res['result'][i]['maintenance_request_uid']
                            rid = {'linked_request_uid': req_id}  # rid
                            quotes_res = db.select(
                                ''' maintenanceQuotes quote ''', rid)
                            time_between_insertion = datetime.now() - \
                                datetime.strptime(
                                res['result'][i]['request_created_date'], '%Y-%m-%d %H:%M:%S')
                            if ',' in str(time_between_insertion):
                                res['result'][i]['days_open'] = int((str(time_between_insertion).split(',')[
                                    0]).split(' ')[0])
                            else:
                                res['result'][i]['days_open'] = 1

                            # print(quotes_res)
                            res['result'][i]['quotes'] = list(
                                quotes_res['result'])
                            res['result'][i]['total_quotes'] = len(
                                quotes_res['result'])
                            # owner info for the property
                            owner_res = db.execute("""
                            SELECT
                            o.owner_id AS owner_id,
                            o.owner_first_name AS owner_first_name,
                            o.owner_last_name AS owner_last_name,
                            o.owner_email AS owner_email ,
                            o.owner_phone_number AS owner_phone_number
                            FROM pm.ownerProfileInfo o
                            WHERE o.owner_id = \'""" + res['result'][i]['owner_id'] + """\'""")
                            res['result'][i]['owner'] = list(
                                owner_res['result'])
                            rental_res = db.execute("""
                            SELECT r.*,
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
                            WHERE r.rental_property_id = \'""" + res['result'][i]['property_uid'] + """\'
                            AND (r.rental_status = 'PROCESSING' OR r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED')
                            GROUP BY lt.linked_rental_uid""")

                            if len(rental_res['result']) > 0:

                                res['result'][i]['rentalInfo'] = list(
                                    rental_res['result'])
                            else:
                                res['result'][i]['rentalInfo'] = 'Not Rented'

                            property_res = db.execute("""
                            SELECT 
                            pm.*, 
                            b.business_uid AS manager_id, 
                            b.business_name AS manager_business_name, 
                            b.business_email AS manager_email, 
                            b.business_phone_number AS manager_phone_number 
                            FROM pm.propertyManager pm 
                            LEFT JOIN businesses b 
                            ON b.business_uid = pm.linked_business_id 
                            WHERE pm.linked_property_id = \'""" + res['result'][i]['property_uid'] + """\' AND pm.management_status='ACCEPTED'""")
                            # print('property_res', property_res)
                            res['result'][i]['property_manager'] = list(
                                property_res['result'])

                    else:
                        res = db.select('maintenanceRequests', where)
            # print(len(fv))
            if len(fv) == 0:
                res = db.select('maintenanceRequests', where)

        return res

    def post(self):
        response = {}
        with connect() as db:
            data = request.form
            fields = ['property_uid', 'title', 'description',
                      'priority', 'request_created_by', 'request_type']
            newRequest = {}
            for field in fields:
                newRequest[field] = data.get(field)
            newRequestID = db.call('new_request_id')['result'][0]['new_id']
            newRequest['maintenance_request_uid'] = newRequestID
            images = []
            i = -1
            while True:
                filename = f'img_{i}'
                if i == -1:
                    filename = 'img_cover'
                file = request.files.get(filename)
                if file:
                    key = f'maintenanceRequests/{newRequestID}/{filename}'
                    image = uploadImage(file, key, '')
                    images.append(image)
                else:
                    break
                i += 1
            newRequest['images'] = json.dumps(images)
            newRequest['request_status'] = 'NEW'
            newRequest['frequency'] = 'One time'
            newRequest['can_reschedule'] = False
            response = db.insert('maintenanceRequests', newRequest)
        return response

    def put(self):
        response = {}
        with connect() as db:
            data = request.form
            # print(data)
            maintenance_request_uid = data.get('maintenance_request_uid')
            fields = ['title', 'description', 'priority', 'can_reschedule',
                      'assigned_business', 'assigned_worker', 'scheduled_date', 'scheduled_time', 'request_status', 'request_created_by', 'request_type', "notes"]
            newRequest = {}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    newRequest[field] = fieldValue
            images = []
            i = -1
            imageFiles = {}

            while True:
                # print('if true')
                filename = f'img_{i}'
                if i == -1:
                    filename = 'img_cover'
                file = request.files.get(filename)
                s3Link = data.get(filename)
                if file:
                    imageFiles[filename] = file
                elif s3Link:
                    imageFiles[filename] = s3Link
                else:
                    break
                i += 1
            images = updateImages(imageFiles, maintenance_request_uid)
            # print(images)

            # Perform write to database
            newRequest['images'] = json.dumps(images)
            primaryKey = {
                'maintenance_request_uid': maintenance_request_uid
            }
            response = db.update('maintenanceRequests', primaryKey, newRequest)
        return response


class MaintenanceRequestsandQuotes(Resource):
    def get(self):
        response = {}
        filters = ['property_uid', 'manager_id', 'owner_id', 'tenant_id']
        where = {}
        for filter in filters:
            filterValue = request.args.get(filter)
            if filterValue is not None:
                where[filter] = filterValue
                # print((where))

        # print('here',  'manager_id' in where)
        with connect() as db:
            if 'manager_id' in where:
                # print('in if')

                response = db.execute(""" SELECT * FROM 
                maintenanceRequests mr
                LEFT JOIN properties p
                ON p.property_uid = mr.property_uid
                LEFT JOIN propertyManager pm
                ON pm.linked_property_id = p.property_uid
                WHERE linked_business_id =  \'""" + where['manager_id'] + """\' AND (pm.management_status = 'ACCEPTED' OR pm.management_status='END EARLY' OR pm.management_status='PM END EARLY' OR pm.management_status='OWNER END EARLY'  )""")
                # print(response)
                for i in range(len(response['result'])):
                    req_id = response['result'][i]['maintenance_request_uid']
                    rid = {'linked_request_uid': req_id}  # rid
                    quotes_res = db.select(
                        ''' maintenanceQuotes quote ''', rid)
                    time_between_insertion = datetime.now() - \
                        datetime.strptime(
                        response['result'][i]['request_created_date'], '%Y-%m-%d %H:%M:%S')
                    if ',' in str(time_between_insertion):
                        response['result'][i]['days_open'] = int((str(time_between_insertion).split(',')[
                            0]).split(' ')[0])
                    else:
                        response['result'][i]['days_open'] = 1

                    # print(quotes_res)
                    response['result'][i]['quotes'] = list(
                        quotes_res['result'])
                    response['result'][i]['total_quotes'] = len(
                        quotes_res['result'])
                    # owner info for the property
                    owner_res = db.execute("""SELECT
                                                o.owner_id AS owner_id,
                                                o.owner_first_name AS owner_first_name,
                                                o.owner_last_name AS owner_last_name,
                                                o.owner_email AS owner_email ,
                                                o.owner_phone_number AS owner_phone_number
                                                FROM pm.ownerProfileInfo o
                                                WHERE o.owner_id = \'""" + response['result'][i]['owner_id'] + """\'""")
                    response['result'][i]['owner'] = list(owner_res['result'])
                    rental_res = db.execute("""
                   SELECT r.*,
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
                    WHERE r.rental_property_id = \'""" + response['result'][i]['property_uid'] + """\'
                    AND (r.rental_status = 'PROCESSING' OR r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED')
                    GROUP BY lt.linked_rental_uid""")

                    if len(rental_res['result']) > 0:

                        response['result'][i]['rentalInfo'] = list(
                            rental_res['result'])
                    else:
                        response['result'][i]['rentalInfo'] = 'Not Rented'
            elif 'owner_id' in where:
                # print('in elif', where['owner_id'])

                # list of all properties for the owner
                response = db.execute(
                    """SELECT * FROM pm.properties p WHERE p.owner_id = \'"""
                    + where['owner_id']
                    + """\'""")
                # print('here')
                # info for each property
                for i in range(len(response['result'])):
                    # print('in for loop')
                    property_id = response['result'][i]['property_uid']
                    # print(property_id)
                    pid = {'linked_property_id': property_id}
                    maintenance_res = db.execute("""
                    SELECT *
                    FROM pm.maintenanceRequests mr
                    WHERE mr.property_uid = \'""" + property_id + """\'
                    """)
                    response['result'][i]['maintenanceRequests'] = list(
                        maintenance_res['result'])

                    # print(maintenance_res['result'])
                    for y in range(len(maintenance_res['result'])):
                        property_res = db.execute("""
                        SELECT 
                        pm.*, 
                        b.business_uid AS manager_id, 
                        b.business_name AS manager_business_name, 
                        b.business_email AS manager_email, 
                        b.business_phone_number AS manager_phone_number 
                        FROM pm.propertyManager pm 
                        LEFT JOIN businesses b 
                        ON b.business_uid = pm.linked_business_id 
                        WHERE pm.linked_property_id = \'""" + property_id + """\' AND pm.management_status='ACCEPTED'""")
                        # print('property_res', property_res)
                        maintenance_res['result'][y]['property_manager'] = list(
                            property_res['result'])
                        req_id = maintenance_res['result'][y]['maintenance_request_uid']
                        rid = {'linked_request_uid': req_id}  # rid
                        # print(rid)
                        quotes_res = db.select(
                            ''' maintenanceQuotes quote ''', rid)
                        # print(quotes_res)
                        # change the response variable here, don't know why
                        time_between_insertion = datetime.now() - \
                            datetime.strptime(
                            maintenance_res['result'][y]['request_created_date'], '%Y-%m-%d %H:%M:%S')
                        if ',' in str(time_between_insertion):
                            maintenance_res['result'][y]['days_open'] = int((str(time_between_insertion).split(',')[
                                0]).split(' ')[0])
                        else:
                            maintenance_res['result'][y]['days_open'] = 1
                        if len(quotes_res['result']) > 0:
                            for quote in quotes_res['result']:
                                if quote['quote_status'] == 'ACCEPTED':
                                    maintenance_res['result'][y]['total_estimate'] = quote['total_estimate']
                                else:
                                    maintenance_res['result'][y]['total_estimate'] = 0
                        else:
                            maintenance_res['result'][y]['total_estimate'] = 0
                        maintenance_res['result'][y]['quotes'] = list(
                            quotes_res['result'])
                        maintenance_res['result'][y]['total_quotes'] = len(
                            quotes_res['result'])

                        maintenance_res['result'][y]['address'] = response['result'][i]['address'] + ' ' + response['result'][i]['unit'] + ', ' + \
                            response['result'][i]['city'] + ', ' + \
                            response['result'][i]['state'] + ' ' + \
                            response['result'][i]['zip']
                sorted_props = []
                for prop in response['result']:
                    # print("all", prop['property_uid'])
                    if len(prop['maintenanceRequests']) > 0:
                        # print("removed", prop['property_uid'])
                        # response['result'].remove(prop)
                        sorted_props.append(prop)
                response['result'] = sorted_props

            elif 'tenant_id' in where:
                # print('in elif')

                # list of all properties for the owner
                response = db.execute("""
                    SELECT * FROM 
                    maintenanceRequests mr
                    LEFT JOIN properties p
                    ON p.property_uid = mr.property_uid
                    LEFT JOIN pm.rentals r
                    ON r.rental_property_id=p.property_uid
                    LEFT JOIN pm.leaseTenants lt
                    ON lt.linked_rental_uid=r.rental_uid
                    LEFT JOIN pm.propertyManager pM
                    ON pM.linked_property_id=p.property_uid
                    WHERE linked_tenant_id= \'""" + filterValue + """\' AND (rental_status = 'ACTIVE' OR rental_status = 'PM END EARLY' OR rental_status = 'TENANT END EARLY') AND (pM.management_status = 'ACCEPTED' OR pM.management_status='END EARLY' OR pM.management_status='PM END EARLY' OR pM.management_status='OWNER END EARLY'); """)
                # info for each property
                # print(response)
                for i in range(len(response['result'])):
                    req_id = response['result'][i]['maintenance_request_uid']
                    rid = {'linked_request_uid': req_id}  # rid
                    quotes_res = db.select(
                        ''' maintenanceQuotes quote ''', rid)
                    time_between_insertion = datetime.now() - \
                        datetime.strptime(
                        response['result'][i]['request_created_date'], '%Y-%m-%d %H:%M:%S')
                    if ',' in str(time_between_insertion):
                        response['result'][i]['days_open'] = int((str(time_between_insertion).split(',')[
                            0]).split(' ')[0])
                    else:
                        response['result'][i]['days_open'] = 1

                    # print(quotes_res)
                    response['result'][i]['quotes'] = list(
                        quotes_res['result'])
                    response['result'][i]['total_quotes'] = len(
                        quotes_res['result'])
                    # owner info for the property
                    owner_res = db.execute("""
                    SELECT
                    o.owner_id AS owner_id,
                    o.owner_first_name AS owner_first_name,
                    o.owner_last_name AS owner_last_name,
                    o.owner_email AS owner_email ,
                    o.owner_phone_number AS owner_phone_number
                    FROM pm.ownerProfileInfo o
                    WHERE o.owner_id = \'""" + response['result'][i]['owner_id'] + """\'""")
                    response['result'][i]['owner'] = list(owner_res['result'])
                    rental_res = db.execute("""
                   SELECT r.*,
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
                    WHERE r.rental_property_id = \'""" + response['result'][i]['property_uid'] + """\'
                    AND (r.rental_status = 'PROCESSING' OR r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED')
                    GROUP BY lt.linked_rental_uid""")

                    if len(rental_res['result']) > 0:

                        response['result'][i]['rentalInfo'] = list(
                            rental_res['result'])
                    else:
                        response['result'][i]['rentalInfo'] = 'Not Rented'

                    manager_res = db.execute("""SELECT * FROM businesses b WHERE b.business_uid = \'""" + response['result'][i]['linked_business_id'] + """\' """)
                    if len(manager_res['result']) > 0:

                        response['result'][i]['managerInfo'] = list(
                            manager_res['result'])
                    else:
                        response['result'][i]['managerInfo'] = 'Not Rented'
            else:
                response = db.select(
                    ''' maintenanceRequests request ''', where)
                for i in range(len(response['result'])):
                    req_id = response['result'][i]['maintenance_request_uid']
                    print(req_id)
                    rid = {'linked_request_uid': req_id}
                    quotes_res = db.select(
                        ''' maintenanceQuotes quote ''', rid)
                    # print(quotes_res)
                    response['result'][i]['quotes'] = list(
                        quotes_res['result'])
                    response['result'][i]['total_quotes'] = len(
                        quotes_res['result'])

        return response


class OwnerMaintenanceRequestsandQuotes(Resource):
    def get(self):
        response = {}
        filters = ['owner_id']
        where = {}
        for filter in filters:
            filterValue = request.args.get(filter)
            if filterValue is not None:
                where[filter] = filterValue
                # print((where))
        with connect() as db:

            # print('in elif', filterValue)
            # list of all properties for the owner
            response = db.execute(
                """SELECT * FROM pm.properties p WHERE p.owner_id = \'"""
                + filterValue
                + """\'""")
            # info for each property
            for i in range(len(response['result'])):
                property_id = response['result'][i]['property_uid']
                # print(property_id)
                pid = {'linked_property_id': property_id}
                maintenance_res = db.execute("""SELECT *
                                                    FROM pm.maintenanceRequests mr
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
                    # change the response variable here, don't know why
                    response['result'][i]['quotes'] = list(
                        quotes_res['result'])
                    response['result'][i]['total_quotes'] = len(
                        quotes_res['result'])

        return response
