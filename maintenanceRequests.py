
from flask import request
from flask_restful import Resource

from data import connect, uploadImage, s3
import json
from datetime import datetime
import boto3


# If it is an s3 link, we save the file data into the attribute
# If it is a file, no need to worry about it, the data is already there.
def updateImages(imageFiles, maintenance_request_uid):
    for filename in imageFiles:
        if type(imageFiles[filename]) == str:
            bucket = 'io-pm'
            key = imageFiles[filename].split('/io-pm/')[1]
            data = s3.get_object(
                Bucket=bucket,
                Key=key
            )
            imageFiles[filename] = data['Body']
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
        image = uploadImage(imageFiles[filename], key)
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
                    else:
                        res = db.select('maintenanceRequests', where)
            print(len(fv))
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
                    image = uploadImage(file, key)
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
            print(data)
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
            # while True:
            #     print('if true')
            #     filename = f'img_{i}'
            #     if i == -1:
            #         filename = 'img_cover'
            #     file = request.files.get(filename)
            #     s3Link = data.get(filename)
            #     if file:
            #         imageFiles[filename] = file
            #
            # ##Mickey is trying something - start ##
            # key = f'maintenanceRequests/{maintenance_request_uid}/{filename}'
            # resultURL = uploadImage(file, key)
            # images.append(resultURL)
            ##Mickey is trying something - end  ##
            #
            #         print('images', images)
            #         newRequest['images'] = json.dumps(images)
            #     elif s3Link:
            #         imageFiles[filename] = s3Link
            #         #images = updateImages(imageFiles, maintenance_request_uid)
            #         images.append(s3Link)
            #         print('images', images)
            #         newRequest['images'] = json.dumps(images)
            #     else:
            #         break
            #     i += 1
            while True:
                print('if true')
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
            print('"yay, linear imageFilesBuild --> imageFile: ', imageFiles)
            images = updateImages(imageFiles, maintenance_request_uid)
            print(images)

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
        filters = ['property_uid', 'manager_id', 'owner_id']
        where = {}
        for filter in filters:
            filterValue = request.args.get(filter)
            if filterValue is not None:
                where[filter] = filterValue
                print((where))

        print('here',  'manager_id' in where)
        with connect() as db:
            if 'manager_id' in where:
                print('in if')

                response = db.execute(""" SELECT * FROM 
                maintenanceRequests mr
                LEFT JOIN properties p
                ON p.property_uid = mr.property_uid
                LEFT JOIN propertyManager pm
                ON pm.linked_property_id = p.property_uid
                WHERE linked_business_id =  \'""" + where['manager_id'] + """\' AND (pm.management_status = 'ACCEPTED' OR pm.management_status='END EARLY' OR pm.management_status='PM END EARLY' OR pm.management_status='OWNER END EARLY'  )""")
                print(response)
                for i in range(len(response['result'])):
                    req_id = response['result'][i]['maintenance_request_uid']
                    rid = {'linked_request_uid': req_id}  # rid
                    quotes_res = db.select(
                        ''' maintenanceQuotes quote ''', rid)
                    # print(quotes_res)
                    # change the response variable here, don't know why
                    response['result'][i]['quotes'] = list(
                        quotes_res['result'])
                    response['result'][i]['total_quotes'] = len(
                        quotes_res['result'])
            elif 'owner_id' in where:
                print('in elif')

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
                        maintenance_res['result'][y]['quotes'] = list(
                            quotes_res['result'])
                        maintenance_res['result'][y]['total_quotes'] = len(
                            quotes_res['result'])
                sorted_props = []
                for prop in response['result']:
                    print("all", prop['property_uid'])
                    if len(prop['maintenanceRequests']) > 0:
                        # print("removed", prop['property_uid'])
                        # response['result'].remove(prop)
                        sorted_props.append(prop)
                response['result'] = sorted_props
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
                    print(rid)
                    quotes_res = db.select(
                        ''' maintenanceQuotes quote ''', rid)
                    print(quotes_res)
                    # change the response variable here, don't know why
                    response['result'][i]['quotes'] = list(
                        quotes_res['result'])
                    response['result'][i]['total_quotes'] = len(
                        quotes_res['result'])

        return response
