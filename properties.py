
from flask import request
from flask_restful import Resource

from data import connect
import boto3
import json
from datetime import datetime
s3 = boto3.client('s3')

def uploadImage(file, key):
    bucket = 'io-pm'
    contentType = 'image/jpeg'
    if '.svg' in file.filename:
        contentType = 'image/svg+xml'
    if file:
        filename = f'https://s3-us-west-1.amazonaws.com/{bucket}/{key}'
        upload_file = s3.put_object(
            Bucket=bucket,
            Body=file.read(),
            Key=key,
            ACL='public-read',
            ContentType=contentType
        )
        return filename
    return None

class Properties(Resource):
    def get(self):
        response = {}
        filters = ['property_uid', 'owner_id', 'manager_id', 'address', 'city',
            'state', 'zip', 'type', 'num_beds', 'num_baths', 'area', 'listed_rent', 'deposit',
            'appliances', 'utilities', 'pets_allowed', 'deposit_for_rent']
        where = {}
        for filter in filters:
            filterValue = request.args.get(filter)
            if filterValue is not None:
                where[filter] = filterValue
        with connect() as db:
            response = db.select('properties', where)
        return response

    def post(self):
        response = {}
        with connect() as db:
            data = request.form
            fields = ['owner_id', 'manager_id', 'address', 'unit', 'city', 'state',
                'zip', 'property_type', 'num_beds', 'num_baths', 'area', 'listed_rent', 'deposit',
                'appliances', 'utilities', 'pets_allowed', 'deposit_for_rent']
            newProperty = {}
            for field in fields:
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
            response = db.insert('properties', newProperty)
        return response
