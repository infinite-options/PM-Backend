
from flask import request
from flask_restful import Resource

from data import connect
import boto3
from botocore.response import StreamingBody
import json
from datetime import datetime
s3 = boto3.client('s3')

def uploadImage(file, key):
    bucket = 'io-pm'
    contentType = 'image/jpeg'
    if type(file) != StreamingBody and '.svg' in file.filename:
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
                    key = f'properties/{property_uid}/{filename}'
                    image = uploadImage(file, key)
                    images.append(image)
                else:
                    break
                i += 1
            newProperty['images'] = json.dumps(images)
            response = db.insert('properties', newProperty)
        return response

class Property(Resource):
    def put(self, property_uid):
        response = {}
        with connect() as db:
            data = request.form
            fields = ['owner_id', 'manager_id', 'address', 'unit', 'city', 'state',
                'zip', 'property_type', 'num_beds', 'num_baths', 'area', 'listed_rent', 'deposit',
                'appliances', 'utilities', 'pets_allowed', 'deposit_for_rent']
            newProperty = {}
            for field in fields:
                newProperty[field] = data.get(field)
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
