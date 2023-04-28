
from applepay import ApplePay
from appliances import Appliances, RemoveAppliance
from applications import Applications, EndEarly,  TenantRentalEnd_CLASS, TenantRentalEnd_CRON
from bills import Bills
from businesses import Businesses
from businessProfileInfo import BusinessProfileInfo
from cashflow import OwnerCashflow, OwnerCashflowProperty
from cashflowManager import CashflowManager
from cashflowOwner import CashflowOwner
from contact import Contact
from contracts import Contracts
from dashboard import OwnerDashboard, TenantDashboard, ManagerDashboard
from data import connect
from documents import OwnerDocuments, ManagerDocuments, TenantDocuments, MaintenanceDocuments
from employees import Employees
from leaseTenants import LeaseTenants
from maintenanceRequests import MaintenanceRequests, MaintenanceRequestsandQuotes, OwnerMaintenanceRequestsandQuotes
from maintenanceQuotes import MaintenanceQuotes, FinishMaintenance, QuotePaid, FinishMaintenanceNoQuote
from managerCashflows import ManagerCashflow, ManagerCashflowProperty
from managerProfileInfo import ManagerProfileInfo, ManagerClients, ManagerPropertyTenants
from managerProperties import ManagerProperties, ManagerContractFees_CLASS, ManagerContractFees
from ownerProfileInfo import OwnerProfileInfo
from ownerProperties import OwnerProperties, PropertiesOwnerDetail, PropertiesOwner, OwnerPropertyBills
from payments import ManagerPayments, Payments, UserPayments, OwnerPayments, TenantPayments_CLASS, ManagerPayments_CLASS, TenantPayments, ManagerPayments_CRON, MaintenancePayments
from properties import Properties, Property, NotManagedProperties, CancelAgreement, ManagerContractEnd_CLASS, RemovePropertyOwner
from propertyInfo import PropertyInfo, AvailableProperties, PropertiesManagerDetail
from purchases import Purchases, CreateExpenses, DeletePurchase
from refresh import Refresh
from rentals import Rentals, UpdateActiveLease, EndLease, ExtendLease, ExtendLeaseCRON_CLASS, LeasetoMonth_CLASS, LateFee_CLASS, \
    PerDay_LateFee_CLASS,  PerDay_LateFee, LateFee,  ExtendLeaseCRON, LeasetoMonth
from security import createSalt, createHash
from socialLogin import UserSocialLogin, UserSocialSignup
from tenantProfileInfo import CheckTenantProfileComplete, TenantProfileInfo, TenantDetails, PropertiesTenantDetail
from tenantProperties import TenantProperties
from users import Users, Login, UpdateAccessToken, UserDetails, UserToken, AvailableAppointmentsTenant, AvailableAppointmentsMaintenance

from twilio.rest import Client
from flask import Flask
from flask_restful import Api
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_mail import Mail, Message

from flask import request
from flask_restful import Resource
import os
import stripe
import json
import string
import random
from datetime import date, timedelta, datetime
import calendar
from calendar import monthrange
from dateutil.relativedelta import relativedelta

app = Flask(__name__)

# cors = CORS(app, resources={r'/api/*': {'origins': '*'}})
# cors = CORS(app)
CORS(app)
api = Api(app)
app.config['JWT_SECRET_KEY'] = 'secret'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600
app.config['PROPAGATE_EXCEPTIONS'] = True
jwt = JWTManager(app)

# Twilio settings

TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')

app.config['MAIL_USERNAME'] = os.environ.get('SUPPORT_EMAIL')
app.config['MAIL_PASSWORD'] = os.environ.get('SUPPORT_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

app.config["MAIL_SERVER"] = "smtp.mydomain.com"
app.config["MAIL_PORT"] = 465

app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USE_SSL"] = True

# STRIPE KEYS

stripe_public_test_key = os.environ.get("stripe_public_test_key")
stripe_secret_test_key = os.environ.get("stripe_secret_test_key")

stripe_public_live_key = os.environ.get("stripe_public_live_key")
stripe_secret_live_key = os.environ.get("stripe_secret_live_key")

stripe.api_key = stripe_secret_test_key

# app.config["MAIL_USERNAME"] = "support@skedul.online"
# # app.config["MAIL_PASSWORD"] = "SupportSkedul1"
# app.config["MAIL_SUPPRESS_SEND"] = False
mail = Mail(app)


def sendEmail(recipient, subject, body):
    with app.app_context():
        print(recipient, subject, body)
        msg = Message(
            sender=app.config["MAIL_USERNAME"],
            recipients=[recipient],
            subject=subject,
            body=body
        )
        mail.send(msg)


def diff_month(d1, d2):
    return (d1.year - d2.year) * 12 + d1.month - d2.month


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


class stripe_key(Resource):
    def get(self, desc):
        print(desc)
        if desc == "PMTEST":
            return {"publicKey": stripe_public_test_key}
        else:
            return {"publicKey": stripe_public_live_key}


class LeaseExpiringNotify_CLASS(Resource):
    def get(self):
        with connect() as db:
            response = db.execute("""
            SELECT *
            FROM pm.rentals r
            LEFT JOIN pm.leaseTenants lt
            ON lt.linked_rental_uid = r.rental_uid
            LEFT JOIN pm.propertyManager pM
            ON pM.linked_property_id = r.rental_property_id
            LEFT JOIN pm.businesses b
            ON b.business_uid = pM.linked_business_id
            LEFT JOIN pm.properties p
            ON p.property_uid = r.rental_property_id
            LEFT JOIN pm.users u
            ON u.user_uid = lt.linked_tenant_id
            WHERE r.lease_end = DATE_FORMAT(DATE_ADD(NOW(), INTERVAL 2 MONTH), "%Y-%m-%d")
            AND r.rental_status='ACTIVE'
            AND pM.management_status= 'ACCEPTED' OR pM.management_status='END EARLY' OR pM.management_status='PM END EARLY' OR pM.management_status='OWNER END EARLY'; """)

            if len(response['result']) > 0:
                for i in range(len(response['result'])):
                    print(response['result'][i]['rental_uid'])
                    name = response['result'][i]['first_name'] + \
                        ' ' + response['result'][i]['last_name']
                    address = response['result'][i]["address"] + \
                        ' ' + response['result'][i]["unit"] + ", " + response['result'][i]["city"] + \
                        ', ' + response['result'][i]["state"] + \
                        ' ' + response['result'][i]["zip"]
                    start_date = response['result'][i]['lease_start']
                    end_date = response['result'][i]['lease_end']
                    business_name = response['result'][i]['business_name']
                    phone = response['result'][i]['business_phone_number']
                    email = response['result'][i]['business_email']
                    recipient = response['result'][i]['email']
                    subject = "Lease in ending soon..."
                    body = (
                        "Hello " + str(name) + "," + "\n"
                        "\n"
                        "Property: " + str(address) + "\n"
                        "This is your 2 month reminder, that your lease is ending. \n"
                        "Here are your lease details: \n"
                        "Start Date: " +
                        str(start_date) + "\n"
                        "End Date: " +
                        str(end_date) + "\n"
                        "Please contact your Property Manager if you wish to renew or end your lease before the time of expiry. \n"
                        "\n"
                        "Name: " + str(business_name) + "\n"
                        "Phone: " + str(phone) + "\n"
                        "Email: " + str(email) + "\n"
                        "\n"
                        "Thank you - Team Property Management\n\n"
                    )
                    # mail.send(msg)
                    sendEmail(recipient, subject, body)
                    print('sending')

        return response


def LeaseExpiringNotify():
    print("In LeaseExpiringNotify")

    with connect() as db:
        response = db.execute("""SELECT *
                                    FROM pm.rentals r
                                    LEFT JOIN
                                    pm.leaseTenants lt
                                    ON lt.linked_rental_uid = r.rental_uid
                                    LEFT JOIN
                                    pm.propertyManager pM
                                    ON pM.linked_property_id = r.rental_property_id
                                    LEFT JOIN
                                    pm.businesses b
                                    ON b.business_uid = pM.linked_business_id
                                    LEFT JOIN
                                    pm.properties p
                                    ON p.property_uid = r.rental_property_id
                                    LEFT JOIN
                                    pm.users u
                                    ON u.user_uid = lt.linked_tenant_id
                                    WHERE r.lease_end = DATE_FORMAT(DATE_ADD(NOW(), INTERVAL 2 MONTH), "%Y-%m-%d")
                                    AND r.rental_status='ACTIVE'
                                    AND pM.management_status= 'ACCEPTED'; """)

        if len(response['result']) > 0:
            for i in range(len(response['result'])):
                print(response['result'][i]['rental_uid'])
                name = response['result'][i]['first_name'] + \
                    ' ' + response['result'][i]['last_name']
                address = response['result'][i]["address"] + \
                    ' ' + response['result'][i]["unit"] + ", " + response['result'][i]["city"] + \
                    ', ' + response['result'][i]["state"] + \
                    ' ' + response['result'][i]["zip"]
                start_date = response['result'][i]['lease_start']
                end_date = response['result'][i]['lease_end']
                business_name = response['result'][i]['business_name']
                phone = response['result'][i]['business_phone_number']
                email = response['result'][i]['business_email']
                recipient = response['result'][i]['email']
                subject = "Lease in ending soon..."
                body = (
                    "Hello " + str(name) + "," + "\n"
                    "\n"
                    "Property: " + str(address) + "\n"
                    "This is your 2 month reminder, that your lease is ending. \n"
                    "Here are your lease details: \n"
                    "Start Date: " +
                    str(start_date) + "\n"
                    "End Date: " +
                    str(end_date) + "\n"
                    "Please contact your Property Manager if you wish to renew or end your lease before the time of expiry. \n"
                    "\n"
                    "Name: " + str(business_name) + "\n"
                    "Phone: " + str(phone) + "\n"
                    "Email: " + str(email) + "\n"
                    "\n"
                    "Thank you - Team Property Management\n\n"
                )
                # mail.send(msg)
                sendEmail(recipient, subject, body)
                print('sending')

    return response


class SignUpForm(Resource):

    def post(self):
        with connect() as db:
            response = {
                "message": "Successfully committed SQL query",
                "code": 200
            }
            data = request.json
            fields = ['first_name', 'last_name', 'message',
                      'email', 'phone_no']
            newEmail = {}
            for field in fields:
                fieldValue = data.get(field)
                if fieldValue:
                    newEmail[field] = fieldValue

            phone = newEmail['phone_no']
            first_name = newEmail['first_name']
            last_name = newEmail['last_name']
            message = newEmail['message']
            email = newEmail['email']
            recipient = 'prashant3.potluri@gmail.com'
            subject = "New Sign Up and Message"
            body = (
                "Hello," + "\n"
                "\n"
                + str(first_name) +
                " just signed up for receiving emails from Manifest MySpace\n"
                "Please see below for more information. \n"
                "\n"
                "Name: " + str(first_name) + ' ' + str(last_name) + "\n"
                "Phone: " + str(phone) + "\n"
                "Email: " + str(email) + "\n"
                "Message: " + str(message) + "\n"
                "\n"
            )
            # mail.send(msg)
            sendEmail(recipient, subject, body)
            print('sending')

        return response


class set_temp_password(Resource):
    def get_random_string(self, stringLength=8):
        lettersAndDigits = string.ascii_letters + string.digits
        return "".join([random.choice(lettersAndDigits) for i in range(stringLength)])

    def post(self):
        response = {}
        with connect() as db:
            data = request.get_json(force=True)
            email = data['email']

            user_lookup = db.execute("""
            SELECT * FROM pm.users
            WHERE email =\'""" + email + """\';""")

            if not user_lookup['result']:
                user_lookup['message'] = 'No such email exists'
                return user_lookup

            user_uid = {'user_uid': user_lookup['result'][0]['user_uid']}
            print('user', user_uid)
            pass_temp = self.get_random_string()
            passwordSalt = createSalt()
            passwordHash = createHash(pass_temp, passwordSalt)
            passwordSet = {
                'password_hash': passwordHash,
                'password_salt': passwordSalt
            }

            query_result = db.update('users', user_uid, passwordSet)

            msg = Message("Email Verification", sender=app.config["MAIL_USERNAME"],
                          recipients=[email], bcc=app.config["MAIL_USERNAME"])
            msg.body = "Your temporary password is {}. Please use it to reset your password".format(
                pass_temp)

            mail.send(msg)
            response['message'] = "A temporary password has been sent"
        return response


class update_email_password(Resource):
    def post(self):
        response = {}
        with connect() as db:
            conn = connect()
            data = request.get_json(force=True)

            response = db.execute("""
            SELECT *
            FROM pm.users 
            WHERE user_uid = \'""" + data['user_uid'] + """\'
            """)

            if not response['result']:

                response['message'] = "User UID doesn't exists"
                response['result'] = response['result']
                response['code'] = 404
                return response

            salt = createSalt()
            password = createHash(data['password'], salt)

            passwordSet = {
                'email': data['email'],
                'password_hash': password,
                'password_salt': salt
            }
            user_uid = {'user_uid': data['user_uid']}
            response = db.update('users', user_uid, passwordSet)

            response['message'] = 'User email and password updated successfully'

        return response


class MessageEmail(Resource):

    def get(self):
        response = {}
        filters = ['message_uid', 'message_created_at',
                   'sender_name', 'sender_email', 'sender_phone', 'message_subject', 'message_details', 'message_created_by', 'user_messaged', 'message_status', 'receiver_email', 'receiver_phone']
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
            data = request.json
            fields = ['sender_name', 'sender_email', 'sender_phone', 'message_subject',
                      'message_details', 'message_created_by', 'user_messaged', 'message_status', 'receiver_email', 'receiver_phone']
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

            subject = data['message_subject']
            message = data['message_details']
            recipient = data['receiver_email']
            body = (
                "Hello," + "\n"
                "Name: " + data['sender_name'] + "\n"
                "Phone: " + data['sender_phone'] + "\n"
                "Email: " + data['sender_email'] + "\n"
                "Message: " + str(message) + "\n"
                "\n"
            )
            # mail.send(msg)
            try:
                sendEmail(recipient, subject, body)
                response['message'] = 'Email to ' + \
                    recipient + ' sent successfully'
            except:
                response['message'] = 'Email to ' + recipient + ' failed'

        return response


class MessageText(Resource):

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
            data = request.json
            fields = ['sender_name', 'sender_email', 'sender_phone', 'message_subject',
                      'message_details', 'message_created_by', 'user_messaged', 'message_status', 'receiver_email', 'receiver_phone']
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

            subject = data['message_subject']
            message = data['message_details']
            recipient = data['receiver_phone']
            text_msg = (subject + "\n" +
                        message)
            try:
                Send_Twilio_SMS2(
                    text_msg, recipient)
                response['message'] = 'Text message to ' + \
                    recipient + ' sent successfully'
            except:
                response['message'] = 'Text message to ' + \
                    recipient + ' failed'

        return response


class MessageGroupEmail(Resource):
    def post(self):
        response = {}
        response['message'] = []
        data = request.get_json(force=True)
        sender_name = data['sender_name']
        sender_email = data['sender_email']
        subject = data['announcement_title']
        message = data['announcement_msg']
        tenant_email = data['email']
        tenant_name = data['name']

        for e in range(len(tenant_email)):

            recipient = tenant_email[e]
            body = (
                "Hello " + tenant_name[e] + "\n"
                "\n" + str(message) + "\n"
                "\n"
            )
            try:
                sendEmail(recipient, subject, body)
                response['message'].append(
                    'Email to ' + tenant_email[e] + ' sent successfully')
            except:
                response['message'].append(
                    'Email to ' + tenant_email[e] + ' failed')
                continue
        recipient_sender = sender_email
        body = (
            "Hello " + sender_name + "\n"
            "\n" + str(message) + "\n"
            "\n"
        )
        try:
            sendEmail(recipient_sender, subject, body)
            response['message'].append(
                'Email to sender ' + tenant_email[e] + ' sent successfully')
        except:
            response['message'].append(
                'Email to sender ' + tenant_email[e] + ' failed')

        return response


class MessageGroupText(Resource):
    def post(self):
        response = {}
        response['message'] = []
        data = request.get_json(force=True)
        subject = data['announcement_title']
        message = data['announcement_msg']
        tenant_pno = data['pno']
        tenant_name = data['name']
        sender_name = data['sender_name']
        sender_phone = data['sender_phone']

        for e in range(len(tenant_pno)):
            text_msg = (subject + "\n" +
                        message)
            try:
                Send_Twilio_SMS2(
                    text_msg, tenant_pno[e])
                response['message'].append('Text message to ' +
                                           tenant_pno[e] + ' sent successfully')

            except:
                response['message'].append('Text message to ' +
                                           tenant_pno[e] + ' failed')
                continue
        text_msg_sender = (subject + "\n" +
                           message)
        try:
            Send_Twilio_SMS2(
                text_msg_sender, sender_phone)
            response['message'].append('Text message to sender ' +
                                       sender_phone + ' sent successfully')
        except:
            response['message'].append('Text message to sender ' +
                                       sender_phone + ' failed')

        return response


class Send_Twilio_SMS(Resource):

    def post(self):
        items = {}
        data = request.get_json(force=True)
        numbers = data['numbers']
        message = data['message']
        numbers = list(set(numbers.split(',')))
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        for destination in numbers:
            try:
                client.messages.create(
                    body=message,
                    from_='+19254815757',
                    to="+1" + destination
                )
            except:
                continue
        items['code'] = 200
        items['Message'] = 'SMS sent successfully to all recipients'
        return {'code': 200, 'Message': 'SMS sent successfully to all recipients'}


def Send_Twilio_SMS2(message, phone_number):
    items = {}
    numbers = phone_number
    message = message
    numbers = list(set(numbers.split(',')))
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    for destination in numbers:
        client.messages.create(
            body=message,
            from_='+19254815757',
            to="+1" + destination
        )
        print('client.mes', client.messages.create(
            body=message,
            from_='+19254815757',
            to="+1" + destination
        ))
    items['code'] = 200
    items['Message'] = 'SMS sent successfully to all recipients'
    return {'code': 200, 'Message': 'SMS sent successfully to all recipients'}


class Announcement(Resource):

    def get(self):
        response = {}
        filters = ['announcement_uid', 'pm_id', 'receiver']
        where = {}
        for filter in filters:
            filterValue = request.args.get(filter)
            if filterValue is not None:
                where[f'a.{filter}'] = filterValue
        with connect() as db:
            print('filter', filter, filterValue)
            if(filter == 'receiver' and filterValue is not None):
                print('do this if receiver')
                response = db.execute(
                    """SELECT * FROM announcements WHERE receiver LIKE '%""" + filterValue + """%'; """)
                if len(response['result']) > 0:
                    for res in response['result']:
                        manager_response = db.execute(
                            """SELECT * FROM businesses WHERE business_uid = \'""" + res['pm_id'] + """\'; """)

                        res['pm_details'] = list(
                            manager_response['result'])
                        tenantInfo = []
                        if res['announcement_mode'] == 'Tenants':
                            tenantInfo = []
                            if len(res['receiver_properties']) > 0:
                                for prop in json.loads(res['receiver_properties']):
                                    print(prop)
                                    tenantResponse = db.execute("""
                                    SELECT tenant_id AS id, 
                                    t.tenant_first_name AS first_name,
                                    t.tenant_last_name AS last_name,
                                    t.tenant_email AS email,
                                    t.tenant_phone_number AS phone_number, p.*
                                    FROM pm.tenantProfileInfo t
                                    LEFT JOIN pm.leaseTenants lt
                                    ON t.tenant_id = lt.linked_tenant_id
                                    LEFT JOIN pm.rentals r
                                    ON lt.linked_rental_uid = r.rental_uid
                                    LEFT JOIN pm.properties p
                                    ON r.rental_property_id = p.property_uid
                                    WHERE t.tenant_id LIKE '%""" + filterValue + """%' AND p.property_uid = \'""" + prop + """\' ; """)
                                    print(tenantResponse)
                                    if(len(tenantResponse['result'])) > 0:
                                        tenantInfo.append(
                                            (tenantResponse['result'][0]))
                                    res['receiver_details'] = (tenantInfo)
                        elif res['announcement_mode'] == 'Owners':
                            ownerInfo = []
                            if len(json.loads(res['receiver_properties'])) > 0:
                                for prop in json.loads(res['receiver_properties']):
                                    print(prop)
                                    ownerResponse = db.execute("""
                                    SELECT o.owner_id AS id,
                                    o.owner_first_name AS first_name,
                                    o.owner_last_name AS last_name,
                                    o.owner_email AS email,
                                    o.owner_phone_number AS phone_number, p.*
                                    FROM pm.ownerProfileInfo o
                                    LEFT JOIN pm.properties p
                                    ON p.owner_id = o.owner_id
                                    WHERE p.property_uid = \'""" + prop + """\' ; """)
                                    print(ownerResponse)
                                    if(len(ownerResponse['result'])) > 0:
                                        ownerInfo.append(
                                            (ownerResponse['result'][0]))
                            res['receiver_details'] = (ownerInfo)
                        else:
                            tenantInfo = []
                            # if len(json.loads(res['receiver'])) > 0:
                            #     for info in json.loads(res['receiver']):
                            #         print(info)
                            #         print(res['receiver_properties'])
                            if len(json.loads(res['receiver_properties'])) > 0:
                                for prop in json.loads(res['receiver_properties']):
                                    print(prop)
                                    tenantResponse = db.execute("""
                                     SELECT tenant_id AS id, 
                                            t.tenant_first_name AS first_name,
                                            t.tenant_last_name AS last_name,
                                            t.tenant_email AS email,
                                            t.tenant_phone_number AS phone_number, p.*
                                    FROM pm.tenantProfileInfo t
                                    LEFT JOIN leaseTenants lt
                                    ON t.tenant_id = lt.linked_tenant_id
                                    LEFT JOIN rentals r
                                    ON lt.linked_rental_uid = r.rental_uid
                                    LEFT JOIN properties p
                                    ON r.rental_property_id = p.property_uid
                                    WHERE p.property_uid = \'""" + prop + """\' ; """)
                                    print(tenantResponse['result'])
                                    if(len(tenantResponse['result'])) > 0:
                                        for tenant in tenantResponse['result']:
                                            tenantInfo.append(tenant)
                            res['receiver_details'] = (tenantInfo)

            else:
                sql = 'SELECT  FROM announcements a'
                cols = 'a.*'
                tables = 'announcements a '
                response = db.select(cols=cols, tables=tables, where=where)

                if len(response['result']) > 0:

                    for res in response['result']:
                        print(res)
                        manager_response = db.execute(
                            """SELECT * FROM businesses WHERE business_uid = \'""" + res['pm_id'] + """\'; """)

                        res['pm_details'] = list(
                            manager_response['result'])
                        if res['announcement_mode'] == 'Tenants':
                            tenantInfo = []
                            if len(json.loads(res['receiver'])) > 0:
                                for info in json.loads(res['receiver']):
                                    print(info)
                                    print(res['receiver_properties'])
                                    if len(json.loads(res['receiver_properties'])) > 0:
                                        for prop in json.loads(res['receiver_properties']):
                                            print(prop)
                                            tenantResponse = db.execute("""
                                            SELECT tenant_id AS id, 
                                            t.tenant_first_name AS first_name,
                                            t.tenant_last_name AS last_name,
                                            t.tenant_email AS email,
                                            t.tenant_phone_number AS phone_number, p.*
                                            FROM pm.tenantProfileInfo t
                                            LEFT JOIN leaseTenants lt
                                            ON t.tenant_id = lt.linked_tenant_id
                                            LEFT JOIN rentals r
                                            ON lt.linked_rental_uid = r.rental_uid
                                            LEFT JOIN properties p
                                            ON r.rental_property_id = p.property_uid
                                            WHERE tenant_id =  \'""" + info + """\' AND p.property_uid = \'""" + prop + """\' ; """)
                                            print(tenantResponse)
                                            if(len(tenantResponse['result'])) > 0:
                                                tenantInfo.append(
                                                    (tenantResponse['result'][0]))
                                    res['receiver_details'] = (tenantInfo)
                        elif res['announcement_mode'] == 'Owners':
                            ownerInfo = []
                            if len(json.loads(res['receiver'])) > 0:
                                for info in json.loads(res['receiver']):
                                    print(info)
                                    print(res['receiver_properties'])
                                    if len(json.loads(res['receiver_properties'])) > 0:
                                        for prop in json.loads(res['receiver_properties']):
                                            print(prop)
                                            ownerResponse = db.execute("""
                                            SELECT o.owner_id AS id,
                                            o.owner_first_name AS first_name,
                                            o.owner_last_name AS last_name,
                                            o.owner_email AS email,
                                            o.owner_phone_number AS phone_number, p.*
                                            FROM pm.ownerProfileInfo o
                                            LEFT JOIN pm.properties p
                                            ON p.owner_id = o.owner_id
                                            WHERE o.owner_id =  \'""" + info + """\' AND p.property_uid = \'""" + prop + """\' ; """)
                                            print(ownerResponse)
                                            if(len(ownerResponse['result'])) > 0:
                                                ownerInfo.append(
                                                    (ownerResponse['result'][0]))
                                    res['receiver_details'] = (ownerInfo)

                        else:
                            tenantInfo = []
                            # if len(json.loads(res['receiver'])) > 0:
                            #     for info in json.loads(res['receiver']):
                            #         print(info)
                            #         print(res['receiver_properties'])
                            if len(json.loads(res['receiver_properties'])) > 0:
                                for prop in json.loads(res['receiver_properties']):
                                    print(prop)
                                    tenantResponse = db.execute("""
                                     SELECT tenant_id AS id, 
                                            t.tenant_first_name AS first_name,
                                            t.tenant_last_name AS last_name,
                                            t.tenant_email AS email,
                                            t.tenant_phone_number AS phone_number, p.*
                                    FROM pm.tenantProfileInfo t
                                    LEFT JOIN leaseTenants lt
                                    ON t.tenant_id = lt.linked_tenant_id
                                    LEFT JOIN rentals r
                                    ON lt.linked_rental_uid = r.rental_uid
                                    LEFT JOIN properties p
                                    ON r.rental_property_id = p.property_uid
                                    WHERE p.property_uid = \'""" + prop + """\' ; """)
                                    print(tenantResponse['result'])
                                    if(len(tenantResponse['result'])) > 0:
                                        for tenant in tenantResponse['result']:
                                            tenantInfo.append(tenant)
                            res['receiver_details'] = (tenantInfo)

        return response

    def post(self):
        response = {}
        with connect() as db:
            data = request.json
            fields = ['pm_id', 'announcement_msg', 'announcement_title', 'announcement_mode',
                      'receiver', 'receiver_properties']
            newAnnouncement = {}
            for field in fields:
                fieldValue = data.get(field)
                print(fields, fieldValue)
                if fieldValue:
                    newAnnouncement[field] = fieldValue
            newAnnouncementID = db.call('new_announcement_id')[
                'result'][0]['new_id']
            newAnnouncement['announcement_uid'] = newAnnouncementID

            newAnnouncement['receiver'] = json.dumps(data['receiver'])
            newAnnouncement['receiver_properties'] = json.dumps(
                data['receiver_properties'])
            print('newAnnouncement', newAnnouncement)
            response = db.insert('announcements', newAnnouncement)
            print(response)
            response['announcement_uid'] = newAnnouncementID
            tenant_pno = []
            tenant_email = []
            tenant_name = []
            owner_pno = []
            owner_email = []
            owner_name = []
            if len(data['receiver']) > 0:
                if data['announcement_mode'] == 'Owners':
                    print('send to owner info')
                    for info in data['receiver']:
                        print(info)
                        ownerResponse = db.execute("""
                        SELECT owner_id,
                        owner_first_name,
                        owner_last_name,
                        owner_email,
                        owner_phone_number
                        FROM pm.ownerProfileInfo
                        WHERE
                        owner_id =  \'""" + info + """\'; """)
                        owner_pno.append(
                            ownerResponse['result'][0]['owner_phone_number'])
                        owner_email.append(
                            ownerResponse['result'][0]['owner_email'])
                        owner_name.append(
                            ownerResponse['result'][0]['owner_first_name'] + ' ' + ownerResponse['result'][0]['owner_last_name'])
                        response['name'] = owner_name
                        response['pno'] = owner_pno
                        response['email'] = owner_email

                else:

                    for info in data['receiver']:
                        print(info)
                        tenantResponse = db.execute("""
                        SELECT tenant_id,
                        tenant_first_name,
                        tenant_last_name,
                        tenant_email,
                        tenant_phone_number
                        FROM pm.tenantProfileInfo
                        WHERE
                        tenant_id =  \'""" + info + """\'; """)
                        tenant_pno.append(
                            tenantResponse['result'][0]['tenant_phone_number'])
                        tenant_email.append(
                            tenantResponse['result'][0]['tenant_email'])
                        tenant_name.append(
                            tenantResponse['result'][0]['tenant_first_name'] + ' ' + tenantResponse['result'][0]['tenant_last_name'])
                        print(tenant_email, tenant_pno, tenant_name)
                        response['name'] = tenant_name
                        response['pno'] = tenant_pno
                        response['email'] = tenant_email
        return response


class SendAnnouncement(Resource):

    def post(self):
        data = request.get_json(force=True)
        subject = data['announcement_title']
        message = data['announcement_msg']
        tenant_email = data['email']
        tenant_pno = data['pno']
        tenant_name = data['name']
        sender_name = data['sender_name']
        sender_email = data['sender_email']
        sender_phone = data['sender_phone']

        for e in range(len(tenant_email)):
            recipient = tenant_email[e]
            body = (
                "Hello " + tenant_name[e] + "\n"
                "\n" + str(message) + "\n"
                "\n"
            )

            sendEmail(recipient, subject, body)
            text_msg = (subject + "\n" +
                        message)
            Send_Twilio_SMS2(
                text_msg, tenant_pno[e])
        recipient_sender = sender_email
        body = (
            "Hello " + sender_name + "\n"
            "\n" + str(message) + "\n"
            "\n"
        )

        sendEmail(recipient_sender, subject, body)
        text_msg_sender = (subject + "\n" +
                           message)
        Send_Twilio_SMS2(
            text_msg_sender, sender_phone)
        return 'Email and Text Sent'


class DeleteAnnouncement(Resource):
    def put(self):
        ann_response = {}
        with connect() as db:
            data = request.json
            a_id = {
                'announcement_uid': data['announcement_uid']
            }
            ann_response = db.delete(
                """DELETE FROM pm.announcements WHERE announcement_uid = \'""" + data['announcement_uid'] + """\' """)
        return ann_response


class RequestMorePictures(Resource):
    def put(self):
        response = {}
        with connect() as db:
            data = request.json
            request_pk = {
                'maintenance_request_uid': data['maintenance_request_uid']
            }
            response = db.update(
                'maintenanceRequests', request_pk, data)
        return response


class TenantEmailNotifications_CLASS(Resource):

    def get(self):
        response = {}
        with connect() as db:
            payments = []
            response = db.execute("""
            SELECT r.*, prop.*, propM.*,
            GROUP_CONCAT(lt.linked_tenant_id) as `tenants`, GROUP_CONCAT(tpi.tenant_email) as 'tenant_emails'
            FROM pm.rentals r
            LEFT JOIN pm.properties prop
            ON prop.property_uid = r.rental_property_id
            LEFT JOIN pm.leaseTenants lt
            ON lt.linked_rental_uid = r.rental_uid
            LEFT JOIN pm.propertyManager propM
            ON propM.linked_property_id = r.rental_property_id
            LEFT JOIN pm.tenantProfileInfo tpi
            ON tpi.tenant_id = lt.linked_tenant_id
            WHERE r.rental_status = 'ACTIVE'
            AND (propM.management_status = 'ACCEPTED' OR propM.management_status='END EARLY' OR propM.management_status='PM END EARLY' OR propM.management_status='OWNER END EARLY')
            GROUP BY lt.linked_rental_uid;  """)

            # getting all the previous rental payments
            if len(response['result']) > 0:

                for i in range(len(response['result'])):
                    print(
                        len((response['result'][i]['tenant_emails']).split(',')))
                    purRes = db.execute("""
                    SELECT * FROM purchases pur
                    WHERE pur.pur_property_id LIKE '%""" + response['result'][i]['property_uid'] + """%'
                    AND (pur.purchase_type = 'RENT' OR pur.purchase_type= 'EXTRA CHARGES') """)
                    # print('purRes', purRes['result'])
                    response['result'][i]['prevPurchases'] = list(
                        purRes['result'])
             # getting all the expenses and calculating the expense amount
            if len(response['result']) > 0:
                for i in range(len(response['result'])):
                    response['result'][i]['expense_amount'] = 0
                    purRes = db.execute("""
                    SELECT * FROM purchases pur
                    WHERE pur.pur_property_id= \'""" + response['result'][i]['property_uid'] + """\'
                    AND (pur.purchase_type = 'UTILITY' OR pur.purchase_type = 'MAINTENANCE' OR pur.purchase_type = 'REPAIRS') """)
                    response['result'][i]['expenses'] = list(
                        purRes['result'])
                    if len(purRes['result']) > 0:
                        for ore in range(len(purRes['result'])):
                            response['result'][i]['expense_amount'] = response['result'][i]['expense_amount'] + int(
                                purRes['result'][ore]['amount_due'])

            if len(response['result']) > 0:
                # today's date
                today = date.today()
                for lease in response['result']:
                    # creating purchases
                    tenantPayments = json.loads(lease['rent_payments'])
                    payer = lease['tenants'].split(',')
                    payer = json.dumps(payer)
                    for payment in tenantPayments:
                        # if fee_type is $, put the charge amount directly
                        print(lease['property_uid'], payment)

                        if(payment['fee_name'] == 'Rent'):
                            print('payment fee purchase_type RENT')
                            if payment['frequency'] == 'Weekly':
                                print('payment frequency weekly $')
                                lease_start = date.fromisoformat(
                                    lease['lease_start'])
                                lease_end = date.fromisoformat(
                                    lease['lease_end'])
                                # check if today's date is before lease end
                                if today < lease_end:
                                    # get previous purchases
                                    if lease['prevPurchases'] != []:
                                        for prev in lease['prevPurchases']:
                                            if prev['purchase_frequency'] == 'Weekly' and payment['fee_name'] in prev['description']:
                                                prevPurchaseDate = datetime.strptime(
                                                    prev['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                    # set charge date as friday of every week
                                        due_date = next_weekday(
                                            prevPurchaseDate,  int(payment['due_by']))
                                        if len(payment['available_topay']) == 0:
                                            charge_date = due_date
                                        else:
                                            charge_date = due_date - \
                                                timedelta(
                                                    days=int(payment['available_topay']))
                                        charge_month = due_date.strftime(
                                            '%B')
                                        rent = int(payment['charge'])
                                        # if charge date == today then enter the monthly fee
                                        if charge_date == today:
                                            print('here send email')
                                            for e in range(len((lease['tenant_emails']).split(','))):
                                                recipient = (
                                                    lease['tenant_emails']).split(',')[e]
                                                subject = "Rent available to pay"
                                                body = (
                                                    "Hello " + "\n"
                                                    "\n" + "This email is to notify your rent is availablle to pay" + "\n"
                                                    "\n"
                                                    "Thank you - Team Manifest MySpace"
                                                )

                                                sendEmail(
                                                    recipient, subject, body)
                                        if due_date == today:
                                            print(
                                                'here send email', lease['tenant_emails'])
                                            for e in range(len((lease['tenant_emails']).split(','))):
                                                recipient = (
                                                    lease['tenant_emails']).split(',')[e]
                                                subject = "Rent due today"
                                                body = (
                                                    "Hello " + "\n"
                                                    "\n" + "This email is to notify your rent is due today" + "\n"
                                                    "\n"
                                                    "Thank you - Team Manifest MySpace"
                                                )

                                                sendEmail(
                                                    recipient, subject, body)

                            elif payment['frequency'] == 'Biweekly':
                                print('payment frequency biweekly $')
                                lease_start = date.fromisoformat(
                                    lease['lease_start'])
                                lease_end = date.fromisoformat(
                                    lease['lease_end'])
                                # check if today's date is before lease end
                                if today < lease_end:
                                    # get previous purchases
                                    if lease['prevPurchases'] != []:
                                        for prev in lease['prevPurchases']:
                                            if prev['purchase_frequency'] == 'Biweekly' and payment['fee_name'] in prev['description']:
                                                prevPurchaseDate = datetime.strptime(
                                                    prev['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                    # set charge date as friday of every 2 week
                                        due_date = next_weekday_biweekly(
                                            prevPurchaseDate,  int(payment['due_by']))
                                        if len(payment['available_topay']) == 0:
                                            charge_date = due_date
                                        else:
                                            charge_date = due_date - \
                                                timedelta(
                                                    days=int(payment['available_topay']))
                                        charge_month = due_date.strftime(
                                            '%B')
                                        rent = int(payment['charge'])
                                        # if charge date == today then enter the monthly fee
                                        if charge_date == today:
                                            print('here send email')
                                            for e in range(len((lease['tenant_emails']).split(','))):
                                                recipient = (
                                                    lease['tenant_emails']).split(',')[e]
                                                subject = "Rent available to pay"
                                                body = (
                                                    "Hello " + "\n"
                                                    "\n" + "This email is to notify your rent is availablle to pay" + "\n"
                                                    "\n"
                                                    "Thank you - Team Manifest MySpace"
                                                )

                                                sendEmail(
                                                    recipient, subject, body)
                                        if due_date == today:
                                            print(
                                                'here send email', lease['tenant_emails'])
                                            for e in range(len((lease['tenant_emails']).split(','))):
                                                recipient = (
                                                    lease['tenant_emails']).split(',')[e]
                                                subject = "Rent due today"
                                                body = (
                                                    "Hello " + "\n"
                                                    "\n" + "This email is to notify your rent is due today" + "\n"
                                                    "\n"
                                                    "Thank you - Team Manifest MySpace"
                                                )

                                                sendEmail(
                                                    recipient, subject, body)
                            elif payment['frequency'] == 'Monthly':
                                print('payment frequency monthly $')
                                lease_start = date.fromisoformat(
                                    lease['lease_start'])
                                lease_end = date.fromisoformat(
                                    lease['lease_end'])
                                # check if today's date is before lease end
                                if today < lease_end:
                                    # get previous purchases
                                    if lease['prevPurchases'] != []:
                                        for prev in lease['prevPurchases']:
                                            if prev['purchase_frequency'] == 'Monthly' and payment['fee_name'] in prev['description']:
                                                prevPurchaseDate = datetime.strptime(
                                                    prev['next_payment'], '%Y-%m-%d %H:%M:%S').date()

                                        due_date = prevPurchaseDate.replace(
                                            day=int(payment['due_by'])) + relativedelta(months=1)

                                        if len(payment['available_topay']) == 0:
                                            charge_date = due_date

                                        else:
                                            charge_date = due_date - \
                                                timedelta(
                                                    days=int(payment['available_topay']))

                                        charge_month = due_date.strftime(
                                            '%B')

                                        daily_charge_end = round(
                                            int(payment['charge']) / days_in_month(lease_end), 2)
                                        num_days_active_end = lease_end.day
                                        prorated_charge_end = num_days_active_end * daily_charge_end
                                        print('charge_date',
                                              charge_date, due_date)
                                        if charge_date == today:
                                            print(
                                                'here send email', lease['tenant_emails'])
                                            for e in range(len((lease['tenant_emails']).split(','))):
                                                recipient = (
                                                    lease['tenant_emails']).split(',')[e]
                                                subject = "Rent available to pay"
                                                body = (
                                                    "Hello " + "\n"
                                                    "\n" + "This email is to notify your rent is availablle to pay" + "\n"
                                                    "\n"
                                                    "Thank you - Team Manifest MySpace"
                                                )

                                                sendEmail(
                                                    recipient, subject, body)

                                        elif lease_end.month == charge_date.month and lease_end.year == charge_date.year:
                                            print(
                                                'here send email', lease['tenant_emails'])
                                            for e in range(len((lease['tenant_emails']).split(','))):
                                                recipient = (
                                                    lease['tenant_emails']).split(',')[e]
                                                subject = "Rent available to pay"
                                                body = (
                                                    "Hello " + "\n"
                                                    "\n" + "This email is to notify your rent is availablle to pay" + "\n"
                                                    "\n"
                                                    "Thank you - Team Manifest MySpace"
                                                )

                                                sendEmail(
                                                    recipient, subject, body)
                                        if due_date == today:
                                            print(
                                                'here send email', lease['tenant_emails'])
                                            for e in range(len((lease['tenant_emails']).split(','))):
                                                recipient = (
                                                    lease['tenant_emails']).split(',')[e]
                                                subject = "Rent due today"
                                                body = (
                                                    "Hello " + "\n"
                                                    "\n" + "This email is to notify your rent is due today" + "\n"
                                                    "\n"
                                                    "Thank you - Team Manifest MySpace"
                                                )

                                                sendEmail(
                                                    recipient, subject, body)
                                        elif lease_end.month == due_date.month and lease_end.year == due_date.year:
                                            print(
                                                'here send email', lease['tenant_emails'])
                                            for e in range(len((lease['tenant_emails']).split(','))):
                                                recipient = (
                                                    lease['tenant_emails']).split(',')[e]
                                                subject = "Rent due today"
                                                body = (
                                                    "Hello " + "\n"
                                                    "\n" + "This email is to notify your rent is due today" + "\n"
                                                    "\n"
                                                    "Thank you - Team Manifest MySpace"
                                                )

                                                sendEmail(
                                                    recipient, subject, body)
                            elif payment['frequency'] == 'Annually':
                                print('payment frequency annually $')
                                lease_start = date.fromisoformat(
                                    lease['lease_start'])
                                lease_end = date.fromisoformat(
                                    lease['lease_end'])

                                diff = diff_month(lease_end, lease_start)

                                if diff > 12 and today < lease_end:
                                    print('lease longer than 1 year')
                                    due_date = lease_start.replace(
                                        day=int(payment['due_by'])) + relativedelta(months=12)
                                    if len(payment['available_topay']) == 0:
                                        charge_date = due_date
                                    else:
                                        charge_date = due_date - \
                                            timedelta(
                                                days=int(payment['available_topay']))
                                    charge_month = due_date.strftime(
                                        '%B')
                                    rent = int(payment['charge'])
                                    # check if today's date == the charge date
                                    if charge_date == today:
                                        print('here send email')
                                        for e in range(len((lease['tenant_emails']).split(','))):
                                            recipient = (
                                                lease['tenant_emails']).split(',')[e]
                                            subject = "Rent available to pay"
                                            body = (
                                                "Hello " + "\n"
                                                "\n" + "This email is to notify your rent is availablle to pay" + "\n"
                                                "\n"
                                                "Thank you - Team Manifest MySpace"
                                            )

                                            sendEmail(
                                                recipient, subject, body)
                                    if due_date == today:
                                        print(
                                            'here send email', lease['tenant_emails'])
                                        for e in range(len((lease['tenant_emails']).split(','))):
                                            recipient = (
                                                lease['tenant_emails']).split(',')[e]
                                            subject = "Rent due today"
                                            body = (
                                                "Hello " + "\n"
                                                "\n" + "This email is to notify your rent is due today" + "\n"
                                                "\n"
                                                "Thank you - Team Manifest MySpace"
                                            )

                                            sendEmail(
                                                recipient, subject, body)
                            else:
                                print('payment frequency one-time $')
                        elif payment['frequency'] == 'Move-Out Charge':
                            print(
                                'payment fee purchase_type Move-Out Charge ')

                            print('payment frequency one-time $')
                            if today < lease_end:
                                # get previous purchases
                                if lease['prevPurchases'] != []:
                                    for prev in lease['prevPurchases']:
                                        if prev['purchase_frequency'] == 'Move-Out Charge' and payment['fee_name'] in prev['description']:
                                            prevPurchaseDate = datetime.strptime(
                                                prev['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                    charge_month = (
                                        lease_end).strftime('%B')

                                    due_date = lease_end
                                    if len(payment['available_topay']) == 0:
                                        charge_date = due_date
                                    else:
                                        charge_date = due_date - \
                                            timedelta(
                                                days=int(payment['available_topay']))
                                    if charge_date == today:
                                        print('here send email')
                                        for e in range(len((lease['tenant_emails']).split(','))):
                                            recipient = (
                                                lease['tenant_emails']).split(',')[e]
                                            subject = payment['description'] + \
                                                " available to pay"
                                            body = (
                                                "Hello " + "\n"
                                                "\n" + "This email is to notify your " +
                                                payment['description'] +
                                                " is availablle to pay" + "\n"
                                                "\n"
                                                "Thank you - Team Manifest MySpace"
                                            )

                                            sendEmail(
                                                recipient, subject, body)
                                    if due_date == today:
                                        print(
                                            'here send email', lease['tenant_emails'])
                                        for e in range(len((lease['tenant_emails']).split(','))):
                                            recipient = (
                                                lease['tenant_emails']).split(',')[e]
                                            subject = payment['description'] + \
                                                " due today"
                                            body = (
                                                "Hello " + "\n"
                                                "\n" + "This email is to notify your " +
                                                payment['description'] +
                                                " is due today" + "\n"
                                                "\n"
                                                "Thank you - Team Manifest MySpace"
                                            )

                                            sendEmail(
                                                recipient, subject, body)
                        elif payment['frequency'] == 'Move-in Charge':
                            print(
                                'payment fee purchase_type EXTRA CHARGES')
                            print('skip')

                        else:
                            print(
                                'payment fee purchase_type EXTRA CHARGES')
                            if payment['frequency'] == 'Weekly':
                                print('payment frequency weekly $')
                                lease_start = date.fromisoformat(
                                    lease['lease_start'])
                                lease_end = date.fromisoformat(
                                    lease['lease_end'])
                                # check if today's date is before lease end
                                if today < lease_end:
                                    # get previous purchases
                                    if lease['prevPurchases'] != []:
                                        for prev in lease['prevPurchases']:
                                            if prev['purchase_frequency'] == 'Weekly' and payment['fee_name'] in prev['description']:
                                                prevPurchaseDate = datetime.strptime(
                                                    prev['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                    # set charge date as friday of every week
                                        due_date = next_weekday(
                                            prevPurchaseDate,  int(payment['due_by']))
                                        if len(payment['available_topay']) == 0:
                                            charge_date = due_date
                                        else:
                                            charge_date = due_date - \
                                                timedelta(
                                                    days=int(payment['available_topay']))
                                        charge_month = due_date.strftime(
                                            '%B')
                                        print('due_date',
                                              due_date, charge_month, charge_date)
                                        # if charge date == today then enter the monthly fee
                                        if charge_date == today:
                                            print('here send email')
                                            for e in range(len((lease['tenant_emails']).split(','))):
                                                recipient = (
                                                    lease['tenant_emails']).split(',')[e]
                                                subject = payment['description'] + \
                                                    " available to pay"
                                                body = (
                                                    "Hello " + "\n"
                                                    "\n" + "This email is to notify your " +
                                                    payment['description'] +
                                                    " is availablle to pay" + "\n"
                                                    "\n"
                                                    "Thank you - Team Manifest MySpace"
                                                )

                                                sendEmail(
                                                    recipient, subject, body)
                                        if due_date == today:
                                            print(
                                                'here send email', lease['tenant_emails'])
                                            for e in range(len((lease['tenant_emails']).split(','))):
                                                recipient = (
                                                    lease['tenant_emails']).split(',')[e]
                                                subject = payment['description'] + \
                                                    " due today"
                                                body = (
                                                    "Hello " + "\n"
                                                    "\n" +
                                                    "This email is to notify your " +
                                                    payment['description'] +
                                                    " is due today" + "\n"
                                                    "\n"
                                                    "Thank you - Team Manifest MySpace"
                                                )

                                                sendEmail(
                                                    recipient, subject, body)
                            elif payment['frequency'] == 'Biweekly':
                                print('payment frequency biweekly $')
                                lease_start = date.fromisoformat(
                                    lease['lease_start'])
                                lease_end = date.fromisoformat(
                                    lease['lease_end'])
                                # check if today's date is before lease end
                                if today < lease_end:
                                    # get previous purchases
                                    if lease['prevPurchases'] != []:
                                        if prev['purchase_frequency'] == 'Biweekly' and payment['fee_name'] in prev['description']:
                                            prevPurchaseDate = datetime.strptime(
                                                prev['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                    # set charge date as friday of every 2 week
                                        due_date = next_weekday_biweekly(
                                            prevPurchaseDate,  int(payment['due_by']))
                                        if len(payment['available_topay']) == 0:
                                            charge_date = due_date
                                        else:
                                            charge_date = due_date - \
                                                timedelta(
                                                    days=int(payment['available_topay']))
                                        charge_month = due_date.strftime(
                                            '%B')
                                        print('due_date',
                                              due_date, charge_month, charge_date)
                                        # if charge date == today then enter the monthly fee
                                        if charge_date == today:
                                            print('here send email')
                                            for e in range(len((lease['tenant_emails']).split(','))):
                                                recipient = (
                                                    lease['tenant_emails']).split(',')[e]
                                                subject = payment['description'] + \
                                                    " available to pay"
                                                body = (
                                                    "Hello " + "\n"
                                                    "\n" + "This email is to notify your " +
                                                    payment['description'] +
                                                    " is availablle to pay" + "\n"
                                                    "\n"
                                                    "Thank you - Team Manifest MySpace"
                                                )

                                                sendEmail(
                                                    recipient, subject, body)
                                        if due_date == today:
                                            print(
                                                'here send email', lease['tenant_emails'])
                                            for e in range(len((lease['tenant_emails']).split(','))):
                                                recipient = (
                                                    lease['tenant_emails']).split(',')[e]
                                                subject = payment['description'] + \
                                                    "due today"
                                                body = (
                                                    "Hello " + "\n"
                                                    "\n" + "This email is to notify your " +
                                                    payment['description'] +
                                                    " is due today" + "\n"
                                                    "\n"
                                                    "Thank you - Team Manifest MySpace"
                                                )

                                                sendEmail(
                                                    recipient, subject, body)

                            elif payment['frequency'] == 'Monthly':
                                print('payment frequency monthly $')
                                lease_start = date.fromisoformat(
                                    lease['lease_start'])
                                lease_end = date.fromisoformat(
                                    lease['lease_end'])
                                # check if today's date is before lease end
                                if today < lease_end:
                                    # get previous purchases
                                    if lease['prevPurchases'] != []:
                                        for prev in lease['prevPurchases']:
                                            if prev['purchase_frequency'] == 'Monthly' and payment['fee_name'] in prev['description']:
                                                prevPurchaseDate = datetime.strptime(
                                                    prev['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                        # set charge date as first of every month
                                        due_date = prevPurchaseDate.replace(
                                            day=int(payment['due_by'])) + relativedelta(months=1)
                                        if len(payment['available_topay']) == 0:
                                            charge_date = due_date
                                        else:
                                            charge_date = due_date - \
                                                timedelta(
                                                    days=int(payment['available_topay']))
                                        charge_month = due_date.strftime(
                                            '%B')
                                        print('due_date',
                                              due_date, charge_month, charge_date)
                                        # if charge date == today then enter the monthly fee
                                        if charge_date == today:
                                            print('here send email')
                                            for e in range(len((lease['tenant_emails']).split(','))):
                                                recipient = (
                                                    lease['tenant_emails']).split(',')[e]
                                                subject = payment['description'] + \
                                                    " available to pay"
                                                body = (
                                                    "Hello " + "\n"
                                                    "\n" + "This email is to notify your " +
                                                    payment['description'] +
                                                    " is availablle to pay" + "\n"
                                                    "\n"
                                                    "Thank you - Team Manifest MySpace"
                                                )

                                                sendEmail(
                                                    recipient, subject, body)
                                        if due_date == today:
                                            print(
                                                'here send email', lease['tenant_emails'])
                                            for e in range(len((lease['tenant_emails']).split(','))):
                                                recipient = (
                                                    lease['tenant_emails']).split(',')[e]
                                                subject = payment['description'] + \
                                                    " due today"
                                                body = (
                                                    "Hello " + "\n"
                                                    "\n" + "This email is to notify your " +
                                                    payment['description'] +
                                                    " is due today" + "\n"
                                                    "\n"
                                                    "Thank you - Team Manifest MySpace"
                                                )

                                                sendEmail(
                                                    recipient, subject, body)

                            elif payment['frequency'] == 'Annually':
                                print('payment frequency annually $')
                                lease_start = date.fromisoformat(
                                    lease['lease_start'])
                                lease_end = date.fromisoformat(
                                    lease['lease_end'])
                                # calculate the lease length
                                diff = diff_month(lease_end, lease_start)
                                # check if lease is at least an year long and today's date is before the lease ends
                                if diff > 12 and today < lease_end:
                                    print('lease longer than 1 year')
                                    # create a charge date for 1 year from start date
                                    due_date = lease_start.replace(
                                        day=int(payment['due_by'])) + relativedelta(months=12)
                                    if len(payment['available_topay']) == 0:
                                        charge_date = due_date
                                    else:
                                        charge_date = due_date - \
                                            timedelta(
                                                days=int(payment['available_topay']))
                                    charge_month = due_date.strftime(
                                        '%B')
                                    # check if today's date == the charge date
                                    if charge_date == today:
                                        print('here send email')
                                        for e in range(len((lease['tenant_emails']).split(','))):
                                            recipient = (
                                                lease['tenant_emails']).split(',')[e]
                                            subject = payment['description'] + \
                                                " available to pay"
                                            body = (
                                                "Hello " + "\n"
                                                "\n" + "This email is to notify your " +
                                                payment['description'] +
                                                " is availablle to pay" + "\n"
                                                "\n"
                                                "Thank you - Team Manifest MySpace"
                                            )

                                            sendEmail(
                                                recipient, subject, body)
                                    if due_date == today:
                                        print(
                                            'here send email', lease['tenant_emails'])
                                        for e in range(len((lease['tenant_emails']).split(','))):
                                            recipient = (
                                                lease['tenant_emails']).split(',')[e]
                                            subject = payment['description'] + \
                                                " due today"
                                            body = (
                                                "Hello " + "\n"
                                                "\n" + "This email is to notify your " +
                                                payment['description'] +
                                                " is due today" + "\n"
                                                "\n"
                                                "Thank you - Team Manifest MySpace"
                                            )

                                            sendEmail(
                                                recipient, subject, body)
                            else:
                                print('payment frequency one-time $')

        return response


def TenantEmailNotifications(self):
    print("In TenantEmailNotifications")

    from datetime import date, timedelta, datetime
    from dateutil.relativedelta import relativedelta

    with connect() as db:
        print("In TenantEmailNotifications")
        response = {'message': 'Successfully committed SQL query',
                    'code': 200}
        payments = []
        response = db.execute("""
        SELECT r.*, prop.*, propM.*,
        GROUP_CONCAT(lt.linked_tenant_id) as `tenants`, GROUP_CONCAT(tpi.tenant_email) as 'tenant_emails'
        FROM pm.rentals r
        LEFT JOIN pm.properties prop
        ON prop.property_uid = r.rental_property_id
        LEFT JOIN pm.leaseTenants lt
        ON lt.linked_rental_uid = r.rental_uid
        LEFT JOIN pm.propertyManager propM
        ON propM.linked_property_id = r.rental_property_id
        LEFT JOIN pm.tenantProfileInfo tpi
        ON tpi.tenant_id = lt.linked_tenant_id
        WHERE r.rental_status = 'ACTIVE'
        AND (propM.management_status = 'ACCEPTED' OR propM.management_status='END EARLY' OR propM.management_status='PM END EARLY' OR propM.management_status='OWNER END EARLY')
        GROUP BY lt.linked_rental_uid;  """)

        # getting all the previous rental payments
        if len(response['result']) > 0:

            for i in range(len(response['result'])):
                print(
                    len((response['result'][i]['tenant_emails']).split(',')))
                purRes = db.execute("""
                SELECT * FROM purchases pur
                WHERE pur.pur_property_id LIKE '%""" + response['result'][i]['property_uid'] + """%'
                AND (pur.purchase_type = 'RENT' OR pur.purchase_type= 'EXTRA CHARGES') """)
                # print('purRes', purRes['result'])
                response['result'][i]['prevPurchases'] = list(
                    purRes['result'])
            # getting all the expenses and calculating the expense amount
        if len(response['result']) > 0:
            for i in range(len(response['result'])):
                response['result'][i]['expense_amount'] = 0
                purRes = db.execute("""
                SELECT * FROM purchases pur
                WHERE pur.pur_property_id= \'""" + response['result'][i]['property_uid'] + """\'
                AND (pur.purchase_type = 'UTILITY' OR pur.purchase_type = 'MAINTENANCE' OR pur.purchase_type = 'REPAIRS') """)
                response['result'][i]['expenses'] = list(
                    purRes['result'])
                if len(purRes['result']) > 0:
                    for ore in range(len(purRes['result'])):
                        response['result'][i]['expense_amount'] = response['result'][i]['expense_amount'] + int(
                            purRes['result'][ore]['amount_due'])

        if len(response['result']) > 0:
            # today's date
            today = date.today()
            for lease in response['result']:
                # creating purchases
                tenantPayments = json.loads(lease['rent_payments'])
                payer = lease['tenants'].split(',')
                payer = json.dumps(payer)
                for payment in tenantPayments:
                    # if fee_type is $, put the charge amount directly
                    print(lease['property_uid'], payment)

                    if(payment['fee_name'] == 'Rent'):
                        print('payment fee purchase_type RENT')
                        if payment['frequency'] == 'Weekly':
                            print('payment frequency weekly $')
                            lease_start = date.fromisoformat(
                                lease['lease_start'])
                            lease_end = date.fromisoformat(
                                lease['lease_end'])
                            # check if today's date is before lease end
                            if today < lease_end:
                                # get previous purchases
                                if lease['prevPurchases'] != []:
                                    for prev in lease['prevPurchases']:
                                        if prev['purchase_frequency'] == 'Weekly' and payment['fee_name'] in prev['description']:
                                            prevPurchaseDate = datetime.strptime(
                                                prev['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                # set charge date as friday of every week
                                    due_date = next_weekday(
                                        prevPurchaseDate,  int(payment['due_by']))
                                    if len(payment['available_topay']) == 0:
                                        charge_date = due_date
                                    else:
                                        charge_date = due_date - \
                                            timedelta(
                                                days=int(payment['available_topay']))
                                    charge_month = due_date.strftime(
                                        '%B')
                                    rent = int(payment['charge'])
                                    # if charge date == today then enter the monthly fee
                                    if charge_date == today:
                                        print('here send email')
                                        for e in range(len((lease['tenant_emails']).split(','))):
                                            recipient = (
                                                lease['tenant_emails']).split(',')[e]
                                            subject = "Rent available to pay"
                                            body = (
                                                "Hello " + "\n"
                                                "\n" + "This email is to notify your rent is availablle to pay" + "\n"
                                                "\n"
                                                "Thank you - Team Manifest MySpace"
                                            )

                                            sendEmail(
                                                recipient, subject, body)
                                    if due_date == today:
                                        print(
                                            'here send email', lease['tenant_emails'])
                                        for e in range(len((lease['tenant_emails']).split(','))):
                                            recipient = (
                                                lease['tenant_emails']).split(',')[e]
                                            subject = "Rent due today"
                                            body = (
                                                "Hello " + "\n"
                                                "\n" + "This email is to notify your rent is due today" + "\n"
                                                "\n"
                                                "Thank you - Team Manifest MySpace"
                                            )

                                            sendEmail(
                                                recipient, subject, body)

                        elif payment['frequency'] == 'Biweekly':
                            print('payment frequency biweekly $')
                            lease_start = date.fromisoformat(
                                lease['lease_start'])
                            lease_end = date.fromisoformat(
                                lease['lease_end'])
                            # check if today's date is before lease end
                            if today < lease_end:
                                # get previous purchases
                                if lease['prevPurchases'] != []:
                                    for prev in lease['prevPurchases']:
                                        if prev['purchase_frequency'] == 'Biweekly' and payment['fee_name'] in prev['description']:
                                            prevPurchaseDate = datetime.strptime(
                                                prev['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                # set charge date as friday of every 2 week
                                    due_date = next_weekday_biweekly(
                                        prevPurchaseDate,  int(payment['due_by']))
                                    if len(payment['available_topay']) == 0:
                                        charge_date = due_date
                                    else:
                                        charge_date = due_date - \
                                            timedelta(
                                                days=int(payment['available_topay']))
                                    charge_month = due_date.strftime(
                                        '%B')
                                    rent = int(payment['charge'])
                                    # if charge date == today then enter the monthly fee
                                    if charge_date == today:
                                        print('here send email')
                                        for e in range(len((lease['tenant_emails']).split(','))):
                                            recipient = (
                                                lease['tenant_emails']).split(',')[e]
                                            subject = "Rent available to pay"
                                            body = (
                                                "Hello " + "\n"
                                                "\n" + "This email is to notify your rent is availablle to pay" + "\n"
                                                "\n"
                                                "Thank you - Team Manifest MySpace"
                                            )

                                            sendEmail(
                                                recipient, subject, body)
                                    if due_date == today:
                                        print(
                                            'here send email', lease['tenant_emails'])
                                        for e in range(len((lease['tenant_emails']).split(','))):
                                            recipient = (
                                                lease['tenant_emails']).split(',')[e]
                                            subject = "Rent due today"
                                            body = (
                                                "Hello " + "\n"
                                                "\n" + "This email is to notify your rent is due today" + "\n"
                                                "\n"
                                                "Thank you - Team Manifest MySpace"
                                            )

                                            sendEmail(
                                                recipient, subject, body)
                        elif payment['frequency'] == 'Monthly':
                            print('payment frequency monthly $')
                            lease_start = date.fromisoformat(
                                lease['lease_start'])
                            lease_end = date.fromisoformat(
                                lease['lease_end'])
                            # check if today's date is before lease end
                            if today < lease_end:
                                # get previous purchases
                                if lease['prevPurchases'] != []:
                                    for prev in lease['prevPurchases']:
                                        if prev['purchase_frequency'] == 'Monthly' and payment['fee_name'] in prev['description']:
                                            prevPurchaseDate = datetime.strptime(
                                                prev['next_payment'], '%Y-%m-%d %H:%M:%S').date()

                                    due_date = prevPurchaseDate.replace(
                                        day=int(payment['due_by'])) + relativedelta(months=1)

                                    if len(payment['available_topay']) == 0:
                                        charge_date = due_date

                                    else:
                                        charge_date = due_date - \
                                            timedelta(
                                                days=int(payment['available_topay']))

                                    charge_month = due_date.strftime(
                                        '%B')

                                    daily_charge_end = round(
                                        int(payment['charge']) / days_in_month(lease_end), 2)
                                    num_days_active_end = lease_end.day
                                    prorated_charge_end = num_days_active_end * daily_charge_end
                                    print('charge_date',
                                          charge_date, due_date)
                                    if charge_date == today:
                                        print(
                                            'here send email', lease['tenant_emails'])
                                        for e in range(len((lease['tenant_emails']).split(','))):
                                            recipient = (
                                                lease['tenant_emails']).split(',')[e]
                                            subject = "Rent available to pay"
                                            body = (
                                                "Hello " + "\n"
                                                "\n" + "This email is to notify your rent is availablle to pay" + "\n"
                                                "\n"
                                                "Thank you - Team Manifest MySpace"
                                            )

                                            sendEmail(
                                                recipient, subject, body)

                                    elif lease_end.month == charge_date.month and lease_end.year == charge_date.year:
                                        print(
                                            'here send email', lease['tenant_emails'])
                                        for e in range(len((lease['tenant_emails']).split(','))):
                                            recipient = (
                                                lease['tenant_emails']).split(',')[e]
                                            subject = "Rent available to pay"
                                            body = (
                                                "Hello " + "\n"
                                                "\n" + "This email is to notify your rent is availablle to pay" + "\n"
                                                "\n"
                                                "Thank you - Team Manifest MySpace"
                                            )

                                            sendEmail(
                                                recipient, subject, body)
                                    if due_date == today:
                                        print(
                                            'here send email', lease['tenant_emails'])
                                        for e in range(len((lease['tenant_emails']).split(','))):
                                            recipient = (
                                                lease['tenant_emails']).split(',')[e]
                                            subject = "Rent due today"
                                            body = (
                                                "Hello " + "\n"
                                                "\n" + "This email is to notify your rent is due today" + "\n"
                                                "\n"
                                                "Thank you - Team Manifest MySpace"
                                            )

                                            sendEmail(
                                                recipient, subject, body)
                                    elif lease_end.month == due_date.month and lease_end.year == due_date.year:
                                        print(
                                            'here send email', lease['tenant_emails'])
                                        for e in range(len((lease['tenant_emails']).split(','))):
                                            recipient = (
                                                lease['tenant_emails']).split(',')[e]
                                            subject = "Rent due today"
                                            body = (
                                                "Hello " + "\n"
                                                "\n" + "This email is to notify your rent is due today" + "\n"
                                                "\n"
                                                "Thank you - Team Manifest MySpace"
                                            )

                                            sendEmail(
                                                recipient, subject, body)
                        elif payment['frequency'] == 'Annually':
                            print('payment frequency annually $')
                            lease_start = date.fromisoformat(
                                lease['lease_start'])
                            lease_end = date.fromisoformat(
                                lease['lease_end'])

                            diff = diff_month(lease_end, lease_start)

                            if diff > 12 and today < lease_end:
                                print('lease longer than 1 year')
                                due_date = lease_start.replace(
                                    day=int(payment['due_by'])) + relativedelta(months=12)
                                if len(payment['available_topay']) == 0:
                                    charge_date = due_date
                                else:
                                    charge_date = due_date - \
                                        timedelta(
                                            days=int(payment['available_topay']))
                                charge_month = due_date.strftime(
                                    '%B')
                                rent = int(payment['charge'])
                                # check if today's date == the charge date
                                if charge_date == today:
                                    print('here send email')
                                    for e in range(len((lease['tenant_emails']).split(','))):
                                        recipient = (
                                            lease['tenant_emails']).split(',')[e]
                                        subject = "Rent available to pay"
                                        body = (
                                            "Hello " + "\n"
                                            "\n" + "This email is to notify your rent is availablle to pay" + "\n"
                                            "\n"
                                            "Thank you - Team Manifest MySpace"
                                        )

                                        sendEmail(
                                            recipient, subject, body)
                                if due_date == today:
                                    print(
                                        'here send email', lease['tenant_emails'])
                                    for e in range(len((lease['tenant_emails']).split(','))):
                                        recipient = (
                                            lease['tenant_emails']).split(',')[e]
                                        subject = "Rent due today"
                                        body = (
                                            "Hello " + "\n"
                                            "\n" + "This email is to notify your rent is due today" + "\n"
                                            "\n"
                                            "Thank you - Team Manifest MySpace"
                                        )

                                        sendEmail(
                                            recipient, subject, body)
                        else:
                            print('payment frequency one-time $')
                    elif payment['frequency'] == 'Move-Out Charge':
                        print(
                            'payment fee purchase_type Move-Out Charge ')

                        print('payment frequency one-time $')
                        if today < lease_end:
                            # get previous purchases
                            if lease['prevPurchases'] != []:
                                for prev in lease['prevPurchases']:
                                    if prev['purchase_frequency'] == 'Move-Out Charge' and payment['fee_name'] in prev['description']:
                                        prevPurchaseDate = datetime.strptime(
                                            prev['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                charge_month = (
                                    lease_end).strftime('%B')

                                due_date = lease_end
                                if len(payment['available_topay']) == 0:
                                    charge_date = due_date
                                else:
                                    charge_date = due_date - \
                                        timedelta(
                                            days=int(payment['available_topay']))
                                if charge_date == today:
                                    print('here send email')
                                    for e in range(len((lease['tenant_emails']).split(','))):
                                        recipient = (
                                            lease['tenant_emails']).split(',')[e]
                                        subject = payment['description'] + \
                                            " available to pay"
                                        body = (
                                            "Hello " + "\n"
                                            "\n" + "This email is to notify your " +
                                            payment['description'] +
                                            " is availablle to pay" + "\n"
                                            "\n"
                                            "Thank you - Team Manifest MySpace"
                                        )

                                        sendEmail(
                                            recipient, subject, body)
                                if due_date == today:
                                    print(
                                        'here send email', lease['tenant_emails'])
                                    for e in range(len((lease['tenant_emails']).split(','))):
                                        recipient = (
                                            lease['tenant_emails']).split(',')[e]
                                        subject = payment['description'] + \
                                            " due today"
                                        body = (
                                            "Hello " + "\n"
                                            "\n" + "This email is to notify your " +
                                            payment['description'] +
                                            " is due today" + "\n"
                                            "\n"
                                            "Thank you - Team Manifest MySpace"
                                        )

                                        sendEmail(
                                            recipient, subject, body)
                    elif payment['frequency'] == 'Move-in Charge':
                        print(
                            'payment fee purchase_type EXTRA CHARGES')
                        print('skip')

                    else:
                        print(
                            'payment fee purchase_type EXTRA CHARGES')
                        if payment['frequency'] == 'Weekly':
                            print('payment frequency weekly $')
                            lease_start = date.fromisoformat(
                                lease['lease_start'])
                            lease_end = date.fromisoformat(
                                lease['lease_end'])
                            # check if today's date is before lease end
                            if today < lease_end:
                                # get previous purchases
                                if lease['prevPurchases'] != []:
                                    for prev in lease['prevPurchases']:
                                        if prev['purchase_frequency'] == 'Weekly' and payment['fee_name'] in prev['description']:
                                            prevPurchaseDate = datetime.strptime(
                                                prev['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                # set charge date as friday of every week
                                    due_date = next_weekday(
                                        prevPurchaseDate,  int(payment['due_by']))
                                    if len(payment['available_topay']) == 0:
                                        charge_date = due_date
                                    else:
                                        charge_date = due_date - \
                                            timedelta(
                                                days=int(payment['available_topay']))
                                    charge_month = due_date.strftime(
                                        '%B')
                                    print('due_date',
                                          due_date, charge_month, charge_date)
                                    # if charge date == today then enter the monthly fee
                                    if charge_date == today:
                                        print('here send email')
                                        for e in range(len((lease['tenant_emails']).split(','))):
                                            recipient = (
                                                lease['tenant_emails']).split(',')[e]
                                            subject = payment['description'] + \
                                                " available to pay"
                                            body = (
                                                "Hello " + "\n"
                                                "\n" + "This email is to notify your " +
                                                payment['description'] +
                                                " is availablle to pay" + "\n"
                                                "\n"
                                                "Thank you - Team Manifest MySpace"
                                            )

                                            sendEmail(
                                                recipient, subject, body)
                                    if due_date == today:
                                        print(
                                            'here send email', lease['tenant_emails'])
                                        for e in range(len((lease['tenant_emails']).split(','))):
                                            recipient = (
                                                lease['tenant_emails']).split(',')[e]
                                            subject = payment['description'] + \
                                                " due today"
                                            body = (
                                                "Hello " + "\n"
                                                "\n" +
                                                "This email is to notify your " +
                                                payment['description'] +
                                                " is due today" + "\n"
                                                "\n"
                                                "Thank you - Team Manifest MySpace"
                                            )

                                            sendEmail(
                                                recipient, subject, body)
                        elif payment['frequency'] == 'Biweekly':
                            print('payment frequency biweekly $')
                            lease_start = date.fromisoformat(
                                lease['lease_start'])
                            lease_end = date.fromisoformat(
                                lease['lease_end'])
                            # check if today's date is before lease end
                            if today < lease_end:
                                # get previous purchases
                                if lease['prevPurchases'] != []:
                                    if prev['purchase_frequency'] == 'Biweekly' and payment['fee_name'] in prev['description']:
                                        prevPurchaseDate = datetime.strptime(
                                            prev['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                # set charge date as friday of every 2 week
                                    due_date = next_weekday_biweekly(
                                        prevPurchaseDate,  int(payment['due_by']))
                                    if len(payment['available_topay']) == 0:
                                        charge_date = due_date
                                    else:
                                        charge_date = due_date - \
                                            timedelta(
                                                days=int(payment['available_topay']))
                                    charge_month = due_date.strftime(
                                        '%B')
                                    print('due_date',
                                          due_date, charge_month, charge_date)
                                    # if charge date == today then enter the monthly fee
                                    if charge_date == today:
                                        print('here send email')
                                        for e in range(len((lease['tenant_emails']).split(','))):
                                            recipient = (
                                                lease['tenant_emails']).split(',')[e]
                                            subject = payment['description'] + \
                                                " available to pay"
                                            body = (
                                                "Hello " + "\n"
                                                "\n" + "This email is to notify your " +
                                                payment['description'] +
                                                " is availablle to pay" + "\n"
                                                "\n"
                                                "Thank you - Team Manifest MySpace"
                                            )

                                            sendEmail(
                                                recipient, subject, body)
                                    if due_date == today:
                                        print(
                                            'here send email', lease['tenant_emails'])
                                        for e in range(len((lease['tenant_emails']).split(','))):
                                            recipient = (
                                                lease['tenant_emails']).split(',')[e]
                                            subject = payment['description'] + \
                                                "due today"
                                            body = (
                                                "Hello " + "\n"
                                                "\n" + "This email is to notify your " +
                                                payment['description'] +
                                                " is due today" + "\n"
                                                "\n"
                                                "Thank you - Team Manifest MySpace"
                                            )

                                            sendEmail(
                                                recipient, subject, body)

                        elif payment['frequency'] == 'Monthly':
                            print('payment frequency monthly $')
                            lease_start = date.fromisoformat(
                                lease['lease_start'])
                            lease_end = date.fromisoformat(
                                lease['lease_end'])
                            # check if today's date is before lease end
                            if today < lease_end:
                                # get previous purchases
                                if lease['prevPurchases'] != []:
                                    for prev in lease['prevPurchases']:
                                        if prev['purchase_frequency'] == 'Monthly' and payment['fee_name'] in prev['description']:
                                            prevPurchaseDate = datetime.strptime(
                                                prev['next_payment'], '%Y-%m-%d %H:%M:%S').date()
                                    # set charge date as first of every month
                                    due_date = prevPurchaseDate.replace(
                                        day=int(payment['due_by'])) + relativedelta(months=1)
                                    if len(payment['available_topay']) == 0:
                                        charge_date = due_date
                                    else:
                                        charge_date = due_date - \
                                            timedelta(
                                                days=int(payment['available_topay']))
                                    charge_month = due_date.strftime(
                                        '%B')
                                    print('due_date',
                                          due_date, charge_month, charge_date)
                                    # if charge date == today then enter the monthly fee
                                    if charge_date == today:
                                        print('here send email')
                                        for e in range(len((lease['tenant_emails']).split(','))):
                                            recipient = (
                                                lease['tenant_emails']).split(',')[e]
                                            subject = payment['description'] + \
                                                " available to pay"
                                            body = (
                                                "Hello " + "\n"
                                                "\n" + "This email is to notify your " +
                                                payment['description'] +
                                                " is availablle to pay" + "\n"
                                                "\n"
                                                "Thank you - Team Manifest MySpace"
                                            )

                                            sendEmail(
                                                recipient, subject, body)
                                    if due_date == today:
                                        print(
                                            'here send email', lease['tenant_emails'])
                                        for e in range(len((lease['tenant_emails']).split(','))):
                                            recipient = (
                                                lease['tenant_emails']).split(',')[e]
                                            subject = payment['description'] + \
                                                " due today"
                                            body = (
                                                "Hello " + "\n"
                                                "\n" + "This email is to notify your " +
                                                payment['description'] +
                                                " is due today" + "\n"
                                                "\n"
                                                "Thank you - Team Manifest MySpace"
                                            )

                                            sendEmail(
                                                recipient, subject, body)

                        elif payment['frequency'] == 'Annually':
                            print('payment frequency annually $')
                            lease_start = date.fromisoformat(
                                lease['lease_start'])
                            lease_end = date.fromisoformat(
                                lease['lease_end'])
                            # calculate the lease length
                            diff = diff_month(lease_end, lease_start)
                            # check if lease is at least an year long and today's date is before the lease ends
                            if diff > 12 and today < lease_end:
                                print('lease longer than 1 year')
                                # create a charge date for 1 year from start date
                                due_date = lease_start.replace(
                                    day=int(payment['due_by'])) + relativedelta(months=12)
                                if len(payment['available_topay']) == 0:
                                    charge_date = due_date
                                else:
                                    charge_date = due_date - \
                                        timedelta(
                                            days=int(payment['available_topay']))
                                charge_month = due_date.strftime(
                                    '%B')
                                # check if today's date == the charge date
                                if charge_date == today:
                                    print('here send email')
                                    for e in range(len((lease['tenant_emails']).split(','))):
                                        recipient = (
                                            lease['tenant_emails']).split(',')[e]
                                        subject = payment['description'] + \
                                            " available to pay"
                                        body = (
                                            "Hello " + "\n"
                                            "\n" + "This email is to notify your " +
                                            payment['description'] +
                                            " is availablle to pay" + "\n"
                                            "\n"
                                            "Thank you - Team Manifest MySpace"
                                        )

                                        sendEmail(
                                            recipient, subject, body)
                                if due_date == today:
                                    print(
                                        'here send email', lease['tenant_emails'])
                                    for e in range(len((lease['tenant_emails']).split(','))):
                                        recipient = (
                                            lease['tenant_emails']).split(',')[e]
                                        subject = payment['description'] + \
                                            " due today"
                                        body = (
                                            "Hello " + "\n"
                                            "\n" + "This email is to notify your " +
                                            payment['description'] +
                                            " is due today" + "\n"
                                            "\n"
                                            "Thank you - Team Manifest MySpace"
                                        )

                                        sendEmail(
                                            recipient, subject, body)
                        else:
                            print('payment frequency one-time $')

        return response


# applepay
api.add_resource(ApplePay, "/applepay")
# appliances
api.add_resource(Appliances, "/appliances")
api.add_resource(RemoveAppliance, "/RemoveAppliance")
# applications
api.add_resource(Applications, '/applications')
api.add_resource(EndEarly, '/endEarly')
api.add_resource(TenantRentalEnd_CLASS, '/tenantRentalEnd_CLASS')
# bills
api.add_resource(Bills, "/bills")
# businesses
api.add_resource(Businesses, '/businesses')
# businessProfileInfo
api.add_resource(BusinessProfileInfo, '/businessProfileInfo')
# cashflow
api.add_resource(OwnerCashflow, "/ownerCashflow")
api.add_resource(OwnerCashflowProperty, "/ownerCashflowProperty")
# CashflowManager
api.add_resource(CashflowManager, "/CashflowManager")
# CashflowOwner
api.add_resource(CashflowOwner, "/CashflowOwner")
# contact
api.add_resource(Contact, "/contact")
# contracts
api.add_resource(Contracts, '/contracts')
# dashboard
api.add_resource(TenantDashboard, '/tenantDashboard')
api.add_resource(ManagerDashboard, '/managerDashboard')
api.add_resource(OwnerDashboard, '/ownerDashboard')
# documents
api.add_resource(OwnerDocuments, '/ownerDocuments')
api.add_resource(ManagerDocuments, '/managerDocuments')
api.add_resource(MaintenanceDocuments, '/maintenanceDocuments')
api.add_resource(TenantDocuments, '/tenantDocuments')
# employees
api.add_resource(Employees, '/employees')
# leaseTenants
api.add_resource(LeaseTenants, "/leaseTenants")
# maintenanceRequests
api.add_resource(MaintenanceRequests, '/maintenanceRequests')
api.add_resource(MaintenanceRequestsandQuotes, '/maintenanceRequestsandQuotes')
api.add_resource(OwnerMaintenanceRequestsandQuotes,
                 '/ownerMaintenanceRequestsandQuotes')
# maintenanceQuotes
api.add_resource(MaintenanceQuotes, '/maintenanceQuotes')
api.add_resource(FinishMaintenance, '/FinishMaintenance')

api.add_resource(FinishMaintenanceNoQuote, '/FinishMaintenanceNoQuote')
api.add_resource(QuotePaid, '/QuotePaid')

# managerCashflows
api.add_resource(ManagerCashflow, "/managerCashflow")
api.add_resource(ManagerCashflowProperty, "/managerCashflowProperty")

# managerProfileInfo
api.add_resource(ManagerProfileInfo, '/managerProfileInfo')
api.add_resource(ManagerClients, '/managerClients')
api.add_resource(ManagerPropertyTenants, '/managerPropertyTenants')
# managerProperties
api.add_resource(ManagerProperties, '/managerProperties')
api.add_resource(ManagerContractFees_CLASS, '/ManagerContractFees_CLASS')
# ownerProfileInfo
api.add_resource(OwnerProfileInfo, '/ownerProfileInfo')
# ownerProperties
api.add_resource(OwnerProperties, '/ownerProperties')
api.add_resource(PropertiesOwner,
                 '/propertiesOwner')
api.add_resource(PropertiesOwnerDetail,
                 '/propertiesOwnerDetail')
api.add_resource(OwnerPropertyBills, '/ownerPropertyBills')
# payments
api.add_resource(Payments, '/payments')
api.add_resource(UserPayments, '/userPayments')
api.add_resource(ManagerPayments, '/managerPayments')
api.add_resource(MaintenancePayments, '/maintenancePayments')
api.add_resource(OwnerPayments, '/ownerPayments')
api.add_resource(TenantPayments_CLASS, '/TenantPayments_CLASS')
api.add_resource(ManagerPayments_CLASS, '/ManagerPayments_CLASS')
# properties
api.add_resource(Properties, '/properties')
api.add_resource(Property, '/properties/<property_uid>')
api.add_resource(NotManagedProperties, '/notManagedProperties')
api.add_resource(CancelAgreement, '/cancelAgreement')
api.add_resource(ManagerContractEnd_CLASS,
                 '/managerContractEnd_CLASS')
api.add_resource(RemovePropertyOwner, "/RemovePropertyOwner")
# propertyInfo
api.add_resource(PropertiesManagerDetail, '/propertiesManagerDetail')
api.add_resource(PropertyInfo, '/propertyInfo')
api.add_resource(AvailableProperties,
                 '/availableProperties')
# purchases
api.add_resource(Purchases, '/purchases')
api.add_resource(CreateExpenses, '/createExpenses')
api.add_resource(DeletePurchase, '/DeletePurchase')
# refresh
api.add_resource(Refresh, '/refresh')
# rentals
api.add_resource(Rentals, '/rentals')
api.add_resource(EndLease, '/endLease')
api.add_resource(ExtendLease, '/extendLease')
api.add_resource(ExtendLeaseCRON_CLASS, '/ExtendLeaseCRON_CLASS')
api.add_resource(LeasetoMonth_CLASS, '/LeasetoMonth_CLASS')
api.add_resource(LateFee_CLASS, '/LateFee_CLASS')
api.add_resource(PerDay_LateFee_CLASS, '/PerDay_LateFee_CLASS')
api.add_resource(UpdateActiveLease, '/UpdateActiveLease')
# socialLogin
api.add_resource(UserSocialLogin, '/userSocialLogin/<string:email>')
api.add_resource(UserSocialSignup, '/userSocialSignup')
# tenantProfileInfo
api.add_resource(CheckTenantProfileComplete, '/CheckTenantProfileComplete')
api.add_resource(TenantProfileInfo, '/tenantProfileInfo')
api.add_resource(TenantDetails, '/tenantDetails')
api.add_resource(PropertiesTenantDetail, '/propertiesTenantDetail')
# tenantProperties
api.add_resource(TenantProperties, '/tenantProperties')
# users
api.add_resource(Users, '/users')
api.add_resource(Login, '/login')
api.add_resource(UserDetails, "/UserDetails/<string:user_id>")
api.add_resource(UserToken, "/UserToken/<string:user_email_id>")
api.add_resource(UpdateAccessToken, "/UpdateAccessToken/<string:user_id>")
api.add_resource(
    AvailableAppointmentsTenant,
    "/AvailableAppointmentsTenant/<string:date_value>/<string:duration>/<string:user_id>/<string:start_time>,<string:end_time>"
)
api.add_resource(
    AvailableAppointmentsMaintenance,
    "/AvailableAppointmentsMaintenance/<string:date_value>/<string:duration>/<string:user_id>/<string:start_time>,<string:end_time>"
)
# app
api.add_resource(Send_Twilio_SMS, '/Send_Twilio_SMS')
api.add_resource(SendAnnouncement, '/SendAnnouncement')
api.add_resource(DeleteAnnouncement, '/DeleteAnnouncement')
api.add_resource(stripe_key, "/stripe_key/<string:desc>")
api.add_resource(LeaseExpiringNotify_CLASS, '/LeaseExpiringNotify_CLASS')
api.add_resource(SignUpForm, '/signUpForm')
api.add_resource(MessageEmail, '/messageEmail')
api.add_resource(MessageText, '/messageText')
api.add_resource(MessageGroupEmail, '/messageGroupEmail')
api.add_resource(MessageGroupText, '/messageGroupText')
api.add_resource(Announcement, '/announcement')
api.add_resource(RequestMorePictures, '/RequestMorePictures')
api.add_resource(TenantEmailNotifications_CLASS,
                 '/TenantEmailNotifications_CLASS')
api.add_resource(set_temp_password, "/set_temp_password")
api.add_resource(update_email_password, '/update_email_password')
if __name__ == '__main__':
    app.run(debug=True)
