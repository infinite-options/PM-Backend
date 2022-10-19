from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
import boto3
from data import connect, uploadImage, s3
from datetime import date
import json


class Message(Resource):

    def get(self):
        response = {}
        filters = ['message_uid', 'message_created_at',
                   'sender_name', 'sender_email', 'sender_phone', 'message_subject', 'message_details', 'message_created_by', 'user_messaged', 'message_status', 'receiver_email']
        where = {}
        for filter in filters:
            filterValue = request.args.get(filter)
            if filterValue is not None:
                where[f'a.{filter}'] = filterValue
        with connect() as db:
            sql = 'SELECT  FROM messages c'
            cols = 'c.*'
            tables = 'messages c '
            response = db.select(cols=cols, tables=tables, where=where)
        return response

    def post(self):
        response = {}
        with connect() as db:
            data = request.form
            fields = ['sender_name', 'sender_email', 'sender_phone', 'message_subject',
                      'message_details', 'message_created_by', 'user_messaged', 'message_status', 'receiver_email']
            newMessage = {}
            for field in fields:
                fieldValue = data.get(field)
                print(fields, fieldValue)
                if fieldValue:
                    newMessage[field] = fieldValue
            newMessageID = db.call('new_message_uid')['result'][0]['new_id']
            newMessage['message_uid'] = newMessageID

            print('newMessage', newMessage)
            response = db.insert('messages', newMessage)
            response['message_uid'] = newMessageID
        return response
