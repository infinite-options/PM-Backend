
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
        filename = f'img_{appliance}_{i-1}'
        if i == 0:
            filename = f'img_{appliance}_cover'
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
            print(data)
            property_uid = data.get('property_uid')
            appliances = eval(data.get('appliances'))
            print(appliances)
            images = []
            i = -1
            imageFiles = {}
            getAppliance = db.execute(
                """SELECT appliances FROM pm.properties WHERE property_uid= \'""" + property_uid + """\'""")
            getappLen = len(json.loads(
                getAppliance['result'][0]['appliances']).keys())
            existingApp = json.loads(
                getAppliance['result'][0]['appliances'])
            print(getappLen)
            if getappLen == 0:
                print('in if len 0')
                for key in appliances:
                    appliances[key]['images'] = []
                    print(key, '->', (appliances[key]['available']))
                    if 'available' in appliances[key].keys():
                        print('here')
                        appliances[key]['available'] = appliances[key]['available'] == 'True'
                        print(appliances[key]['available'])
                    # print('images')
                    while True:
                        filename = f'img_{key}_{i}'
                        if i == -1:
                            filename = 'img_{key}_cover'
                        file = request.files.get(filename)
                        s3Link = data.get(filename)
                        if file:
                            imageFiles[filename] = file
                            # images = updateImagesAppliances(
                            #     imageFiles, property_uid, key)
                            # print('images file', images)
                            # appliances[key]['images'] = list((images))
                            # print(appliances[key])
                        elif s3Link:
                            imageFiles[filename] = s3Link
                            # images = updateImagesAppliances(
                            #     imageFiles, property_uid, key)
                            # print('images s3', images)
                            # appliances[key]['images'] = json.dumps(images)
                        else:
                            break
                        i += 1
                    images = updateImagesAppliances(
                        imageFiles, property_uid, key)
                    appliances[key]['images'] = list((images))
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
                print('in else not 0')
                for key in appliances:
                    if key in existingApp.keys():
                        print('in if key in exisiitngapp')
                        print(key, '->', existingApp.keys())
                        # print('images')
                        if 'available' in appliances[key].keys():
                            print('if available')
                            print('available', '->', appliances[key].keys())
                            appliances[key]['available'] = appliances[key]['available'] == 'True'
                            appliances[key]['available']
                        while True:
                            print('in add images')
                            filename = f'img_{key}_{i}'
                            print('filename', filename)
                            if i == -1:
                                filename = f'img_{key}_cover'
                            print('filename after if', filename)
                            file = request.files.get(filename)
                            print('file', file)
                            s3Link = data.get(filename)
                            print('s3Link', s3Link)
                            if file:
                                print('in if file')
                                imageFiles[filename] = file
                                # images = updateImagesAppliances(
                                #     imageFiles, property_uid, key)
                                # print('images file', images)
                                # appliances[key]['images'] = list((images))
                                print(appliances[key])
                            elif s3Link:
                                print('in if s3link')
                                imageFiles[filename] = s3Link
                                # images = updateImagesAppliances(
                                #     imageFiles, property_uid, key)
                                # print('images s3', images)
                                # appliances[key]['images'] = json.dumps(images)
                            else:
                                break
                            i += 1
                        images = updateImagesAppliances(
                            imageFiles, property_uid, key)
                        appliances[key]['images'] = list((images))
                        existingApp[key] = appliances[key]
                    else:
                        print('in else not in existingapp')
                        # print('images')
                        if 'available' in appliances[key].keys():
                            print('here')
                            appliances[key]['available'] = appliances[key]['available'] == 'True'
                            appliances[key]['available']
                        while True:
                            filename = f'img_{key}_{i}'
                            if i == -1:
                                filename = 'img_{key}_cover'
                            file = request.files.get(filename)
                            s3Link = data.get(filename)
                            if file:
                                imageFiles[filename] = file

                                print('images file', images)
                                print(appliances[key])
                            elif s3Link:
                                imageFiles[filename] = s3Link
                                # images = updateImagesAppliances(
                                #     imageFiles, property_uid, key)
                                # print('images s3', images)
                                # appliances[key]['images'] = json.dumps(images)
                            else:
                                break
                            i += 1
                        images = updateImagesAppliances(
                            imageFiles, property_uid, key)
                        appliances[key]['images'] = list((images))
                        existingApp[key] = appliances[key]
                        ##Image uploading stuff ends here###

                primaryKey = {
                    'property_uid': property_uid
                }
                updatedProperty = {
                    'appliances': json.dumps(existingApp)
                }
                # print(existingApp)
                response = db.update('properties', primaryKey, updatedProperty)
        return response


class RemoveAppliance(Resource):
    def put(self):
        response = {}
        with connect() as db:
            data = request.form
            print(data)
            property_uid = data.get('property_uid')
            appliance = (data.get('appliance'))

            getAppliance = db.execute(
                """SELECT appliances FROM pm.properties WHERE property_uid= \'""" + property_uid + """\'""")
            getappLen = len(json.loads(
                getAppliance['result'][0]['appliances']).keys())
            existingApp = json.loads(
                getAppliance['result'][0]['appliances'])
            print(existingApp)
            if appliance in existingApp:

                del(existingApp[appliance])
                print(existingApp)
                primaryKey = {
                    'property_uid': property_uid
                }
                updatedProperty = {
                    'appliances': json.dumps(existingApp)
                }

                response = db.update('properties', primaryKey, updatedProperty)
            else:
                response['message'] = 'No appliance'
                response['code'] = 200

            # list_existingApp = list(existingApp.items())
            # print(list_existingApp)
            # updatedApp = existingApp

        return response
