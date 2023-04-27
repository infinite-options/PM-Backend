
from flask import request
from flask_restful import Resource

from data import connect, uploadImage, s3
import json
from datetime import date, timedelta, datetime
import boto3
from purchases import newPurchase


def updateImages(imageFiles, maintenance_quote_uid):
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
        Prefix=f'maintenanceQuotes/{maintenance_quote_uid}/').delete()
    images = []
    for i in range(len(imageFiles.keys())):

        filename = f'img_{i-1}'
        if i == 0:
            filename = 'img_cover'
        key = f'maintenanceQuotes/{maintenance_quote_uid}/{filename}'
        image = uploadImage(
            imageFiles[filename], key, content[i])

        images.append(image)
    return images


def acceptQuote(quote_id):
    with connect() as db:
        response = db.select('maintenanceQuotes', where={
                             'maintenance_quote_uid': quote_id})
        quote = response['result'][0]
        requestKey = {
            'maintenance_request_uid': quote['linked_request_uid']
        }
        newRequest = {
            'assigned_business': quote['quote_business_uid'],
            'request_adjustment_date': date.today()
        }
        requestUpdate = db.update(
            'maintenanceRequests', requestKey, newRequest)
        print(requestUpdate)
        quoteKey = {
            'linked_request_uid': quote['linked_request_uid']
        }
        newQuote = {
            'quote_status': 'WITHDRAWN',
            'quote_adjustment_date': date.today()
        }
        quoteUpdate = db.update('maintenanceQuotes', quoteKey, newQuote)
        print(quoteUpdate)


class MaintenanceQuotes(Resource):
    def get(self):
        response = {}
        filters = ['maintenance_quote_uid', 'linked_request_uid',
                   'quote_business_uid', 'quote_status']
        where = {}
        for filter in filters:
            filterValue = request.args.get(filter)
            if filterValue is not None:
                where[filter] = filterValue
        with connect() as db:

            response = db.select('''
                maintenanceQuotes quote LEFT JOIN maintenanceRequests mr
                ON linked_request_uid = maintenance_request_uid
                LEFT JOIN businesses business 
                ON quote_business_uid = business_uid
                LEFT JOIN properties p
                ON p.property_uid = mr.property_uid
            ''', where)
            for i in range(len(response['result'])):
                # from properties table, maintenanceRequests table
                pid = response['result'][i]['property_uid']
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
                WHERE pm.linked_property_id = \'""" + pid + """\'
                AND (pm.management_status = 'ACCEPTED' OR pm.management_status='END EARLY' OR pm.management_status='PM END EARLY' OR pm.management_status='OWNER END EARLY') """)
                # print('property_res', property_res)
                response['result'][i]['property_manager'] = list(
                    property_res['result'])
                owner_id = response['result'][i]['owner_id']
                owner_res = db.execute("""SELECT
                                            o.owner_id AS owner_id,
                                            o.owner_first_name AS owner_first_name,
                                            o.owner_last_name AS owner_last_name,
                                            o.owner_email AS owner_email ,
                                            o.owner_phone_number AS owner_phone_number
                                            FROM pm.ownerProfileInfo o
                                            WHERE o.owner_id = \'""" + owner_id + """\'""")
                response['result'][i]['owner'] = list(owner_res['result'])
                rental_res = db.execute("""SELECT
                                            r.rental_uid AS rental_uid,
                                            r.rental_property_id AS rental_property_id,
                                            r.rent_payments AS rent_payments,
                                            r.lease_start AS lease_start,
                                            r.lease_end AS lease_end,
                                            r.rental_status AS rental_status,
                                            tpi.tenant_id AS tenant_id,
                                            tpi.tenant_first_name AS tenant_first_name,
                                            tpi.tenant_last_name AS tenant_last_name,
                                            tpi.tenant_email AS tenant_email,
                                            tpi.tenant_phone_number AS tenant_phone_number
                                            FROM pm.rentals r
                                            LEFT JOIN pm.leaseTenants lt
                                            ON lt.linked_rental_uid = r.rental_uid
                                            LEFT JOIN pm.tenantProfileInfo tpi
                                            ON tpi.tenant_id = lt.linked_tenant_id
                                            WHERE r.rental_property_id = \'""" + pid + """\'""")
                response['result'][i]['rentalInfo'] = list(
                    rental_res['result'])
                if len(rental_res['result']) > 0:
                    response['result'][i]['rental_status'] = rental_res['result'][0]['rental_status']
                else:
                    response['result'][i]['rental_status'] = ""

        return response

    def post(self):
        response = {}
        with connect() as db:
            data = request.json
            fields = ['linked_request_uid', 'quote_business_uid']
            newQuote = {}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    newQuote[field] = fieldValue
            requestKey = {
                'maintenance_request_uid': newQuote.get('linked_request_uid')
            }
            newStatus = {
                'request_status': 'PROCESSING',
                'request_adjustment_date': date.today()
            }
            db.update('maintenanceRequests', requestKey, newStatus)
            if type(newQuote['quote_business_uid']) is list:
                businesses = newQuote['quote_business_uid']
                for business_uid in businesses:
                    newQuoteID = db.call('new_quote_id')['result'][0]['new_id']
                    newQuote['maintenance_quote_uid'] = newQuoteID
                    newQuote['quote_business_uid'] = business_uid
                    newQuote['quote_status'] = 'REQUESTED'
                    response = db.insert('maintenanceQuotes', newQuote)
                    if response['code'] != 200:
                        return newQuote
            else:
                newQuoteID = db.call('new_quote_id')['result'][0]['new_id']
                newQuote['maintenance_quote_uid'] = newQuoteID
                newQuote['quote_status'] = 'REQUESTED'
                response = db.insert('maintenanceQuotes', newQuote)

        return response

    def put(self):
        response = {}
        with connect() as db:
            data = request.json
            maintenance_quote_uid = data.get('maintenance_quote_uid')
            fields = ['services_expenses', 'earliest_availability',
                      'event_type', 'event_duration', 'notes', 'quote_status', 'total_estimate', "quote_adjustment_date"]
            jsonFields = ['services_expenses']
            newQuote = {}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    if field in jsonFields:
                        newQuote[field] = json.dumps(fieldValue)
                    else:
                        newQuote[field] = fieldValue

                if field == 'event_type':
                    print(field, fieldValue)
                    if fieldValue == '1 Hour Job':
                        print('here')
                        newQuote['event_duration'] = '0:59:59'
                    elif fieldValue == '2 Hour Job':
                        print(field)
                        newQuote['event_duration'] = '1:59:59'
                    elif fieldValue == '3 Hour Job':
                        print(field)
                        newQuote['event_duration'] = '2:59:59'
                    elif fieldValue == '4 Hour Job':
                        print(field)
                        newQuote['event_duration'] = '3:59:59'
                    elif fieldValue == '6 Hour Job':
                        print(field)
                        newQuote['event_duration'] = '5:59:59'
                    elif fieldValue == '8 Hour Job':
                        print(field)
                        newQuote['event_duration'] = '8:59:59'
            print(newQuote)
            if newQuote.get('quote_status') == 'ACCEPTED':
                acceptQuote(maintenance_quote_uid)
                newQuote['quote_adjustment_date'] = date.today()

            primaryKey = {
                'maintenance_quote_uid': maintenance_quote_uid
            }
            response = db.update('maintenanceQuotes', primaryKey, newQuote)
        return response


class FinishMaintenance(Resource):
    def put(self):
        response = {}
        with connect() as db:
            data = request.form
            print(data)
            maintenance_quote_uid = data.get('maintenance_quote_uid')
            request_status = data.get('request_status')
            notes = data.get('notes')
            updateQuote = {}
            linked_mr = db.execute("""SELECT * FROM pm.maintenanceQuotes mq
            LEFT JOIN pm.maintenanceRequests mr
            ON mr.maintenance_request_uid= mq.linked_request_uid
            LEFT JOIN pm.propertyManager p
            ON p.linked_property_id = mr.property_uid 
            WHERE mq.maintenance_quote_uid = \'""" + maintenance_quote_uid + """\'
            AND (p.management_status = 'ACCEPTED' OR p.management_status='END EARLY' OR p.management_status='PM END EARLY' OR p.management_status='OWNER END EARLY');""")
            if len(linked_mr['result']) > 0:
                updateRequest = {
                    'request_closed_date': date.today(),
                    'request_status': request_status,
                    'request_adjustment_date': date.today()
                }
                primaryKey = {
                    'maintenance_request_uid': linked_mr['result'][0]['maintenance_request_uid']
                }
                response = db.update('maintenanceRequests',
                                     primaryKey, updateRequest)

            images = []
            i = -1
            imageFiles = {}
            while True:
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
            images = updateImages(imageFiles, maintenance_quote_uid)

            updateQuote = {
                'maintenance_images': json.dumps(images),
                'notes': notes,
                'quote_adjustment_date': date.today()
            }
            primaryKey = {
                'maintenance_quote_uid': maintenance_quote_uid
            }
            response = db.update('maintenanceQuotes',
                                 primaryKey, updateQuote)
            date_created = datetime.strptime(
                linked_mr['result'][0]['request_created_date'], '%Y-%m-%d %H:%M:%S')
            purchaseResponse = newPurchase(
                linked_bill_id=linked_mr['result'][0]['maintenance_request_uid'],
                pur_property_id=json.dumps(
                    [linked_mr['result'][0]['property_uid']]),
                payer=json.dumps(
                    [linked_mr['result'][0]['linked_business_id']]),
                receiver=linked_mr['result'][0]['quote_business_uid'],
                purchase_type='MAINTENANCE',
                description=linked_mr['result'][0]['title'],
                amount_due=int(linked_mr['result'][0]['total_estimate']),
                purchase_notes=date.today().strftime(
                    '%B'),
                purchase_date=datetime.strftime(
                    date_created, '%Y-%m-%d 00:00:00'),
                purchase_frequency='ONE-TIME',
                next_payment=date.today()
            )
        return response


class QuotePaid(Resource):
    def put(self):
        response = {}
        with connect() as db:
            data = request.json
            print(data)
            maintenance_request_uid = data.get('maintenance_request_uid')
            quote_status = data.get('quote_status')

            updateQuote = {}
            linked_mr = db.execute("""
            SELECT * FROM pm.maintenanceRequests mr
            LEFT JOIN pm.maintenanceQuotes mq
            ON mq.linked_request_uid= mr.maintenance_request_uid
            WHERE mr.maintenance_request_uid = \'""" + maintenance_request_uid + """\'
            AND mq.quote_business_uid= mr.assigned_business;""")
            if len(linked_mr['result']) > 0:
                updateQuote = {
                    'quote_status': quote_status,
                    'quote_adjustment_date': date.today()
                }
                primaryKey = {
                    'maintenance_quote_uid': linked_mr['result'][0]['maintenance_quote_uid']
                }
                response = db.update('maintenanceQuotes',
                                     primaryKey, updateQuote)

        return response


class FinishMaintenanceNoQuote(Resource):
    def put(self):
        response = {}
        with connect() as db:
            data = request.form
            print(data)
            maintenance_request_uid = data.get('maintenance_request_uid')
            request_status = data.get('request_status')
            request_adjustment_date = data.get('request_adjustment_date')
            notes = data.get('notes')
            cost = data.get('cost')
            linked_mr = db.execute("""SELECT * FROM pm.maintenanceRequests mr
            LEFT JOIN pm.propertyManager p
            ON p.linked_property_id = mr.property_uid 
            WHERE mr.maintenance_request_uid = \'""" + maintenance_request_uid + """\'
            AND (p.management_status = 'ACCEPTED' OR p.management_status='END EARLY' OR p.management_status='PM END EARLY' OR p.management_status='OWNER END EARLY');""")
            if len(linked_mr['result']) > 0:
                images = []
                i = -1
                imageFiles = {}
                while True:
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
                updateRequest = {
                    'request_closed_date': request_adjustment_date,
                    'request_status': request_status,
                    'request_adjustment_date': request_adjustment_date,
                    'notes': notes,

                    'images': json.dumps(images),
                    'assigned_business': linked_mr['result'][0]['linked_business_id']
                }
                primaryKey = {
                    'maintenance_request_uid': linked_mr['result'][0]['maintenance_request_uid']
                }
                response = db.update('maintenanceRequests',
                                     primaryKey, updateRequest)

            date_created = datetime.strptime(
                linked_mr['result'][0]['request_created_date'], '%Y-%m-%d %H:%M:%S')
            purchaseResponse = newPurchase(
                linked_bill_id=linked_mr['result'][0]['maintenance_request_uid'],
                pur_property_id=json.dumps(
                    [linked_mr['result'][0]['property_uid']]),
                payer=json.dumps(
                    [linked_mr['result'][0]['request_created_by']]),
                receiver=linked_mr['result'][0]['linked_business_id'],
                purchase_type='MAINTENANCE',
                description=linked_mr['result'][0]['title'],
                amount_due=int(cost),
                purchase_notes=date.today().strftime(
                    '%B'),
                purchase_date=datetime.strftime(
                    date_created, '%Y-%m-%d 00:00:00'),
                purchase_frequency='ONE-TIME',
                next_payment=date.today()
            )
        return response
