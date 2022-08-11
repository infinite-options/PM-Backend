
from flask import request
from flask_restful import Resource

import boto3
from data import connect, uploadImage, s3
from datetime import date, timedelta, datetime
from calendar import monthrange
import json
import ast
from dateutil.relativedelta import relativedelta
from purchases import newPurchase


def updateImagesAppliances(imageFiles, property_uid, appliance):
    for filename in imageFiles:
        if type(imageFiles[filename]) == str:
            print('here')
            bucket = 'io-pm'
            key = imageFiles[filename].split('/io-pm/')[1]
            data = s3.get_object(
                Bucket=bucket,
                Key=key
            )
            imageFiles[filename] = data['Body']
    s3Resource = boto3.resource('s3')
    bucket = s3Resource.Bucket('io-pm')
    # bucket.objects.filter(Prefix=f'appliances/{property_uid}/').delete()
    images = []
    for i in range(len(imageFiles.keys())):
        filename = f'img_{appliance}_{i}'
        key = f'appliances/{property_uid}/{filename}'
        image = uploadImage(imageFiles[filename], key)
        images.append(image)
        print(images)
    return images


class Appliances(Resource):
    def put(self):
        response = {}
        with connect() as db:
            data = request.form
            property_uid = data.get('property_uid')
            appliances = eval(data.get('appliances'))
            images = []
            i = 0
            imageFiles = {}
            getAppliance = db.execute(
                """SELECT appliances FROM pm.properties WHERE property_uid= \'""" + property_uid + """\'""")
            getappLen = len(json.loads(
                getAppliance['result'][0]['appliances']).keys())
            existingApp = json.loads(
                getAppliance['result'][0]['appliances'])
            if getappLen == 0:
                for key in appliances:
                    appliances[key]['images'] = []
                    print(key, '->', (appliances[key]['available']))
                    if 'available' in appliances[key].keys():
                        print('here')
                        appliances[key]['available'] = appliances[key]['available'] == 'True'
                        print(appliances[key]['available'])
                    # print('images')
                    while True:
                        print('if true')
                        filename = f'img_{key}_{i}'
                        print(filename)

                        file = request.files.get(filename)
                        s3Link = data.get(filename)
                        print(file)
                        print(s3Link)

                        if file:
                            imageFiles[filename] = file
                            images = updateImagesAppliances(
                                imageFiles, property_uid, key)
                            print('images file', images)
                            appliances[key]['images'] = list((images))
                            print(appliances[key])
                        elif s3Link:
                            imageFiles[filename] = s3Link
                            images = updateImagesAppliances(
                                imageFiles, property_uid, key)
                            print('images s3', images)
                            appliances[key]['images'] = json.dumps(images)
                        else:
                            break
                        i += 1

                    ##Image uploading stuff ends here###

                    primaryKey = {
                        'property_uid': property_uid
                    }
                    updatedProperty = {
                        'appliances': json.dumps(appliances)
                    }
                    print(appliances)
                    response = db.update(
                        'properties', primaryKey, updatedProperty)
            else:
                for key in appliances:
                    if key in existingApp.keys():
                        print(key, '->', existingApp.keys())
                        # print('images')
                        if 'available' in appliances[key].keys():
                            print('here')
                            appliances[key]['available'] = appliances[key]['available'] == 'True'
                            appliances[key]['available']
                        while True:
                            print('if true')
                            filename = f'img_{key}_{i}'
                            print(filename)

                            file = request.files.get(filename)
                            s3Link = data.get(filename)
                            print(file)
                            print(s3Link)

                            if file:
                                imageFiles[filename] = file
                                images = updateImagesAppliances(
                                    imageFiles, property_uid, key)
                                print('images file', images)
                                appliances[key]['images'] = list((images))
                                print(appliances[key])
                            elif s3Link:
                                imageFiles[filename] = s3Link
                                images = updateImagesAppliances(
                                    imageFiles, property_uid, key)
                                print('images s3', images)
                                appliances[key]['images'] = json.dumps(images)
                            else:
                                break
                            i += 1
                        print(appliances[key])
                        existingApp[key] = appliances[key]
                    else:
                        # print('images')
                        if 'available' in appliances[key].keys():
                            print('here')
                            appliances[key]['available'] = appliances[key]['available'] == 'True'
                            appliances[key]['available']
                        while True:
                            print('if true')
                            filename = f'img_{key}_{i}'
                            print(filename)

                            file = request.files.get(filename)
                            s3Link = data.get(filename)
                            print(file)
                            print(s3Link)

                            if file:
                                imageFiles[filename] = file
                                images = updateImagesAppliances(
                                    imageFiles, property_uid, key)
                                print('images file', images)
                                appliances[key]['images'] = list((images))
                                print(appliances[key])
                            elif s3Link:
                                imageFiles[filename] = s3Link
                                images = updateImagesAppliances(
                                    imageFiles, property_uid, key)
                                print('images s3', images)
                                appliances[key]['images'] = json.dumps(images)
                            else:
                                break
                            i += 1
                        existingApp[key] = appliances[key]
                        ##Image uploading stuff ends here###

                primaryKey = {
                    'property_uid': property_uid
                }
                updatedProperty = {
                    'appliances': json.dumps(existingApp)
                }
                print(existingApp)
                response = db.update('properties', primaryKey, updatedProperty)
        return response
