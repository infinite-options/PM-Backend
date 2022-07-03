
from flask import request
from flask_restful import Resource

import boto3
from data import connect, uploadImage, s3
from datetime import date, timedelta, datetime
from calendar import monthrange
import json
from dateutil.relativedelta import relativedelta
from purchases import newPurchase


def updateImages(imageFiles, property_uid):
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
    bucket.objects.filter(Prefix=f'properties/{property_uid}/').delete()
    images = []
    for i in range(len(imageFiles.keys())):
        filename = f'img_{i-1}'
        if i == 0:
            filename = 'img_cover'
        key = f'properties/{property_uid}/{filename}'
        image = uploadImage(imageFiles[filename], key)
        images.append(image)
    return images


def days_in_month(dt): return monthrange(
    dt.year, dt.month)[1]


def next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    return d + timedelta(days_ahead)


def next_weekday_biweekly(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 14
    return d + timedelta(days_ahead)


class Properties(Resource):
    def get(self):
        response = {}
        filters = ['property_uid', 'active_date', 'owner_id', 'manager_id', 'address', 'city',
                   'state', 'zip', 'type', 'num_beds', 'num_baths', 'area', 'listed_rent', 'deposit',
                   'appliances', 'utilities', 'pets_allowed', 'deposit_for_rent']
        where = {}
        for filter in filters:
            filterValue = request.args.get(filter)
            if filterValue is not None:
                where[filter] = filterValue
        with connect() as db:
            sql = 'SELECT  FROM properties p LEFT JOIN propertyManager pm ON p.property_uid = pm.linked_property_id'
            cols = 'pm.*, p.*'
            tables = 'properties p LEFT JOIN propertyManager pm ON p.property_uid = pm.linked_property_id'
            response = db.select(cols=cols, tables=tables, where=where)
            # response = db.select('properties', where)
        return response

    def post(self):
        response = {}
        with connect() as db:
            data = request.form
            fields = ['owner_id', 'active_date', 'manager_id', 'address', 'unit', 'city', 'state',
                      'zip', 'property_type', 'num_beds', 'num_baths', 'area', 'listed_rent', 'deposit',
                      'appliances', 'utilities', 'pets_allowed', 'deposit_for_rent']
            boolFields = ['pets_allowed', 'deposit_for_rent']
            newProperty = {}
            print(boolFields)
            for field in fields:
                fieldValue = data.get(field)
                if field in boolFields:
                    # newProperty[field] = bool(data.get(field))
                    if fieldValue == 'true':
                        newProperty[field] = 1
                    else:
                        newProperty[field] = 0
                else:
                    newProperty[field] = data.get(field)

            newPropertyID = db.call('new_property_id')['result'][0]['new_id']
            newProperty['property_uid'] = newPropertyID
            images = []
            i = -1
            while True:
                filename = f'img_{i}'
                if i == -1:
                    filename = 'img_cover'
                file = request.files.get(filename)
                if file:
                    key = f'properties/{newPropertyID}/{filename}'
                    image = uploadImage(file, key)
                    images.append(image)
                else:
                    break
                i += 1
            newProperty['images'] = json.dumps(images)
            # print(newProperty)
            response = db.insert('properties', newProperty)
        return response

    def put(self):
        response = {}
        with connect() as db:
            data = request.form
            print(data)
            property_uid = data.get('property_uid')
            fields = ['owner_id', 'active_date', 'address', 'unit', 'city', 'state',
                      'zip', 'property_type', 'num_beds', 'num_baths', 'area', 'listed_rent', 'deposit',
                      'appliances', 'utilities', 'pets_allowed', 'deposit_for_rent', 'taxes', 'mortgages', 'insurance']
            newProperty = {}
            for field in fields:

                fieldValue = data.get(field)
                print('field', field, fieldValue)
                if fieldValue:
                    newProperty[field] = data.get(field)
            images = []
            i = -1
            imageFiles = {}
            while True:
                print('if true')
                filename = f'img_{i}'
                if i == -1:
                    filename = 'img_cover'
                file = request.files.get(filename)
                s3Link = data.get(filename)
                if file:
                    imageFiles[filename] = file
                    images = updateImages(imageFiles, property_uid)
                    print('images', images)
                    newProperty['images'] = json.dumps(images)
                elif s3Link:
                    imageFiles[filename] = s3Link
                    images = updateImages(imageFiles, property_uid)
                    print('images', images)
                    newProperty['images'] = json.dumps(images)
                else:
                    break
                i += 1

                ##Image uploading stuff ends here###
            primaryKey = {
                'property_uid': property_uid
            }
            print('manager_id', data.get('manager_id'),
                  data.get('management_status'))
            if data.get('manager_id') != None and data.get('management_status') != None:
                manager_id = data.get('manager_id')
                management_status = data.get('management_status')
                pk = {
                    'linked_property_id': property_uid,
                    'linked_business_id': manager_id
                }
                res = db.execute(
                    """SELECT * FROM pm.propertyManager WHERE linked_property_id = \'""" + property_uid + """\' AND linked_business_id= \'""" + manager_id + """\'""")
                print('res', res)

                propertyManager = {
                    'linked_property_id': property_uid,
                    'linked_business_id': manager_id,
                    'management_status': management_status
                }
                if len(res['result']) > 0:
                    db.update('propertyManager', pk, propertyManager)
                propertyManagerReject = {
                    'linked_property_id': property_uid,
                    'linked_business_id': '',
                    'management_status': management_status
                }
                if management_status == 'REJECT':
                    print('in reject')
                    db.update('propertyManager', pk, propertyManagerReject)
                if management_status != 'FORWARDED':
                    print('in not forward')
                    db.update('propertyManager', pk, propertyManager)
                else:
                    db.insert('propertyManager', propertyManager)
                if management_status == 'ACCEPTED':
                    contractRes = db.execute(
                        """SELECT * FROM
                            pm.contracts c
                            LEFT JOIN
                            pm.properties p
                            ON p.property_uid = c.property_uid  WHERE c.property_uid = \'""" + property_uid + """\' AND c.business_uid= \'""" + manager_id + """\'""")
                    print(contractRes)

                    today = date.today()
                    if len(contractRes['result']) > 0:
                        start_date = date.fromisoformat(
                            contractRes['result'][0]['start_date'])
                        # creating purchases
                        managementPayments = json.loads(
                            contractRes['result'][0]['contract_fees'])
                        payer = contractRes['result'][0]['owner_id']
                        if '[' in payer:
                            payer = json.loads(payer)
                        if type(payer) == str:
                            payer = [payer]
                        payer = json.dumps(payer)
                        for payment in managementPayments:
                            print(payment)

                            # distinguish by $ payments and % payments, then by weekly, biweekly, monthly, annually, one-time
                            if payment['fee_type'] == '$':
                                print('payment fee type $')
                                if payment['frequency'] == 'Weekly':
                                    print('payment frequency weekly $')
                                    charge_month = start_date.strftime('%B')
                                    # charge_date = next_weekday(start_date, 4)
                                    charge_date = start_date
                                    # print('charge_date', charge_date)
                                    daily_charge = round(
                                        int(payment['charge']) / days_in_month(start_date), 2)
                                    num_days_active = days_in_month(
                                        start_date) - start_date.day
                                    prorated_charge = num_days_active * daily_charge
                                    purchaseResponse = newPurchase(
                                        linked_bill_id=None,
                                        pur_property_id=contractRes['result'][0]['property_uid'],
                                        payer=payer,
                                        receiver=contractRes['result'][0]['business_uid'],
                                        purchase_type='MANAGEMENT',
                                        description=payment['fee_name'],
                                        amount_due=prorated_charge,
                                        purchase_notes=charge_month,
                                        purchase_date=start_date,
                                        purchase_frequency=payment['frequency'],
                                        next_payment=charge_date
                                    )
                                elif payment['frequency'] == 'Biweekly':
                                    print('payment frequency biweekly $')
                                    charge_month = start_date.strftime('%B')
                                    # charge_date = next_weekday_biweekly(
                                    #     start_date, 4)
                                    charge_date = start_date
                                    # print('charge_date', charge_date)
                                    daily_charge = round(
                                        int(payment['charge']) / days_in_month(start_date), 2)
                                    num_days_active = days_in_month(
                                        start_date) - start_date.day
                                    prorated_charge = num_days_active * daily_charge
                                    purchaseResponse = newPurchase(
                                        linked_bill_id=None,
                                        pur_property_id=contractRes['result'][0]['property_uid'],
                                        payer=payer,
                                        receiver=contractRes['result'][0]['business_uid'],
                                        purchase_type='MANAGEMENT',
                                        description=payment['fee_name'],
                                        amount_due=prorated_charge,
                                        purchase_notes=charge_month,
                                        purchase_date=start_date,
                                        purchase_frequency=payment['frequency'],
                                        next_payment=charge_date
                                    )
                                elif payment['frequency'] == 'Monthly':
                                    print('payment frequency monthly $')
                                    charge_month = start_date.strftime('%B')
                                    # charge_date = start_date.replace(
                                    #     day=days_in_month(start_date))
                                    charge_date = start_date
                                    daily_charge = round(
                                        int(payment['charge']) / days_in_month(start_date), 2)
                                    num_days_active = days_in_month(
                                        start_date) - start_date.day
                                    prorated_charge = num_days_active * daily_charge
                                    purchaseResponse = newPurchase(
                                        linked_bill_id=None,
                                        pur_property_id=contractRes['result'][0]['property_uid'],
                                        payer=payer,
                                        receiver=contractRes['result'][0]['business_uid'],
                                        purchase_type='MANAGEMENT',
                                        description=payment['fee_name'],
                                        amount_due=prorated_charge,
                                        purchase_notes=charge_month,
                                        purchase_date=start_date,
                                        purchase_frequency=payment['frequency'],
                                        next_payment=charge_date
                                    )
                                elif payment['frequency'] == 'Annually':
                                    print('payment frequency annually $')
                                    charge_month = (start_date +
                                                    relativedelta(months=1)).strftime('%B')
                                    # charge_date = start_date.replace(
                                    #     day=1) + relativedelta(months=1)
                                    charge_date = start_date
                                    purchaseResponse = newPurchase(
                                        linked_bill_id=None,
                                        pur_property_id=contractRes['result'][0]['property_uid'],
                                        payer=payer,
                                        receiver=contractRes['result'][0]['business_uid'],
                                        purchase_type='MANAGEMENT',
                                        description=payment['fee_name'],
                                        amount_due=payment['charge'],
                                        purchase_notes=charge_month,
                                        purchase_date=start_date,
                                        purchase_frequency=payment['frequency'],
                                        next_payment=charge_date
                                    )
                                else:
                                    print('payment frequency one-time $')
                                    charge_month = (start_date +
                                                    relativedelta(months=1)).strftime('%B')
                                    # charge_date = start_date.replace(
                                    #     day=1) + relativedelta(months=1)
                                    charge_date = start_date
                                    purchaseResponse = newPurchase(
                                        linked_bill_id=None,
                                        pur_property_id=contractRes['result'][0]['property_uid'],
                                        payer=payer,
                                        receiver=contractRes['result'][0]['business_uid'],
                                        purchase_type='MANAGEMENT',
                                        description=payment['fee_name'],
                                        amount_due=payment['charge'],
                                        purchase_notes=charge_month,
                                        purchase_date=start_date,
                                        purchase_frequency=payment['frequency'],
                                        next_payment=charge_date
                                    )

                            else:
                                print('payment fee type %')
                                if payment['frequency'] == 'Weekly':
                                    print('payment frequency weekly %')
                                    charge_month = start_date.strftime('%B')
                                    # charge_date = next_weekday(start_date, 4)
                                    # charge_date = start_date.replace(
                                    #     day=days_in_month(start_date))
                                    charge_date = start_date
                                    # print('charge_date', charge_date)
                                    daily_charge = round((int(payment['charge']) * int(
                                        contractRes['result'][0]['listed_rent']))/100 / days_in_month(start_date), 2)
                                    num_days_active = days_in_month(
                                        start_date) - start_date.day
                                    prorated_charge = num_days_active * daily_charge
                                    purchaseResponse = newPurchase(
                                        linked_bill_id=None,
                                        pur_property_id=contractRes['result'][0]['property_uid'],
                                        payer=payer,
                                        receiver=contractRes['result'][0]['business_uid'],
                                        purchase_type='MANAGEMENT',
                                        description=payment['fee_name'],
                                        amount_due=prorated_charge,
                                        purchase_notes=charge_month,
                                        purchase_date=start_date,
                                        purchase_frequency=payment['frequency'],
                                        next_payment=charge_date
                                    )
                                elif payment['frequency'] == 'Biweekly':
                                    print('payment frequency biweekly %')
                                    charge_month = start_date.strftime('%B')
                                    # charge_date = next_weekday_biweekly(
                                    #     start_date, 4)
                                    # charge_date = start_date.replace(
                                    #     day=days_in_month(start_date))
                                    charge_date = start_date
                                    # print('charge_date', charge_date)
                                    daily_charge = round((int(payment['charge']) * int(
                                        contractRes['result'][0]['listed_rent']))/100 / days_in_month(start_date), 2)
                                    num_days_active = days_in_month(
                                        start_date) - start_date.day
                                    prorated_charge = num_days_active * daily_charge
                                    purchaseResponse = newPurchase(
                                        linked_bill_id=None,
                                        pur_property_id=contractRes['result'][0]['property_uid'],
                                        payer=payer,
                                        receiver=contractRes['result'][0]['business_uid'],
                                        purchase_type='MANAGEMENT',
                                        description=payment['fee_name'],
                                        amount_due=prorated_charge,
                                        purchase_notes=charge_month,
                                        purchase_date=start_date,
                                        purchase_frequency=payment['frequency'],
                                        next_payment=charge_date
                                    )
                                elif payment['frequency'] == 'Monthly':
                                    print('payment frequency monthly %')
                                    print(start_date)
                                    charge_month = start_date.strftime('%B')
                                    # charge_date = start_date.replace(
                                    #     day=days_in_month(start_date))
                                    charge_date = start_date
                                    daily_charge = round((int(payment['charge']) * int(
                                        contractRes['result'][0]['listed_rent']))/100 / days_in_month(start_date), 2)
                                    num_days_active = days_in_month(
                                        start_date) - start_date.day
                                    prorated_charge = num_days_active * daily_charge
                                    purchaseResponse = newPurchase(
                                        linked_bill_id=None,
                                        pur_property_id=contractRes['result'][0]['property_uid'],
                                        payer=payer,
                                        receiver=contractRes['result'][0]['business_uid'],
                                        purchase_type='MANAGEMENT',
                                        description=payment['fee_name'],
                                        amount_due=prorated_charge,
                                        purchase_notes=charge_month,
                                        purchase_date=start_date,
                                        purchase_frequency=payment['frequency'],
                                        next_payment=charge_date
                                    )
                                elif payment['frequency'] == 'Annually':
                                    print('payment frequency annually %')
                                    charge_month = (start_date +
                                                    relativedelta(months=1)).strftime('%B')
                                    # charge_date = start_date.replace(
                                    #     day=1) + relativedelta(months=1)
                                    charge_date = start_date
                                    purchaseResponse = newPurchase(
                                        linked_bill_id=None,
                                        pur_property_id=contractRes['result'][0]['property_uid'],
                                        payer=payer,
                                        receiver=contractRes['result'][0]['business_uid'],
                                        purchase_type='MANAGEMENT',
                                        description=payment['fee_name'],
                                        amount_due=(
                                            int(payment['charge']) * int(contractRes['result'][0]['listed_rent']))/100,
                                        purchase_notes=charge_month,
                                        purchase_date=start_date,
                                        purchase_frequency=payment['frequency'],
                                        next_payment=charge_date
                                    )
                                else:
                                    print('payment frequency one-time %')
                                    charge_month = (start_date +
                                                    relativedelta(months=1)).strftime('%B')
                                    # charge_date = start_date.replace(
                                    #     day=1) + relativedelta(months=1)
                                    charge_date = start_date
                                    purchaseResponse = newPurchase(
                                        linked_bill_id=None,
                                        pur_property_id=contractRes['result'][0]['property_uid'],
                                        payer=payer,
                                        receiver=contractRes['result'][0]['business_uid'],
                                        purchase_type='MANAGEMENT',
                                        description=payment['fee_name'],
                                        amount_due=(
                                            int(payment['charge']) * int(contractRes['result'][0]['listed_rent']))/100,
                                        purchase_notes=charge_month,
                                        purchase_date=start_date,
                                        purchase_frequency=payment['frequency'],
                                        next_payment=charge_date
                                    )

                    print('accepted')
                print(newProperty)
            if newProperty == {}:
                response['message'] = 'Successfully committed SQL query'
                response['code'] = 200
            else:
                response = db.update('properties', primaryKey, newProperty)
        return response


class Property(Resource):
    def put(self, property_uid):
        response = {}
        with connect() as db:
            data = request.form
            fields = ['owner_id', 'manager_id', 'address', 'unit', 'city', 'state',
                      'zip', 'property_type', 'num_beds', 'num_baths', 'area', 'listed_rent', 'deposit',
                      'appliances', 'utilities', 'pets_allowed', 'deposit_for_rent', 'taxes', 'mortgages']
            newProperty = {}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    newProperty[field] = fieldValue
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
            images = updateImages(imageFiles, property_uid)
            newProperty['images'] = json.dumps(images)
            primaryKey = {
                'property_uid': property_uid
            }
            response = db.update('properties', primaryKey, newProperty)
        return response
