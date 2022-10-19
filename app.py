
from flask import Flask
from flask_restful import Api
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_mail import Mail, Message

from flask import request
from flask_restful import Resource
from data import connect
import os
from os import environ
import stripe


from properties import Properties, Property, NotManagedProperties, CancelAgreement, ManagerContractEnd_CLASS, ManagerContractEnd_CRON
from dashboard import OwnerDashboard, TenantDashboard, ManagerDashboard
from appliances import Appliances
from users import Users, Login, UpdateAccessToken, UserDetails, UserToken, AvailableAppointmentsTenant, AvailableAppointmentsMaintenance
from ownerProfileInfo import OwnerProfileInfo
from managerProfileInfo import ManagerProfileInfo, ManagerClients, ManagerPropertyTenants, ManagerDocuments
from tenantProfileInfo import TenantProfileInfo, TenantDetails
from businessProfileInfo import BusinessProfileInfo
from rentals import Rentals, EndLease, ExtendLease, ExtendLeaseCRON_CLASS, ExtendLeaseCRON, LeasetoMonth_CLASS, LeasetoMonth, LateFee_CLASS, LateFee, PerDay_LateFee_CLASS, PerDay_LateFee, LateFeeExtraCharges_CLASS, LateFeeExtraCharges, PerDay_LateFeeExtraCharges_CLASS, PerDay_LateFeeExtraCharges
from purchases import Purchases, CreateExpenses, CreateRevenues
from payments import ManagerPayments, Payments, UserPayments, OwnerPayments, TenantPayments_CLASS, TenantPayments
from ownerProperties import OwnerProperties, PropertiesOwnerDetail, PropertiesOwner, OwnerPropertyBills, OwnerDocuments
from managerProperties import ManagerProperties
from tenantProperties import TenantProperties
from refresh import Refresh
from businesses import Businesses
from employees import Employees
from maintenanceRequests import MaintenanceRequests
from maintenanceRequests import MaintenanceRequestsandQuotes, OwnerMaintenanceRequestsandQuotes
from maintenanceQuotes import MaintenanceQuotes
from contracts import Contracts
from propertyInfo import ManagerExpenses, PropertyInfo, AvailableProperties, PropertiesManagerDetail
from applications import Applications, EndEarly,  TenantRentalEnd_CLASS, TenantRentalEnd_CRON
from socialLogin import UserSocialLogin, UserSocialSignup
from leaseTenants import LeaseTenants
from bills import Bills
app = Flask(__name__)

# cors = CORS(app, resources={r'/api/*': {'origins': '*'}})
# cors = CORS(app)
CORS(app)
api = Api(app)
app.config['JWT_SECRET_KEY'] = 'secret'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600
app.config['PROPAGATE_EXCEPTIONS'] = True
jwt = JWTManager(app)


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

app.config["STRIPE_SECRET_KEY"] = os.environ.get("STRIPE_SECRET_KEY")


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


def sendEmail2(recipient, subject, body):
    print('in sendemail2')
    with app.app_context():
        msg = Message(
            sender="support@nityaayurveda.com",
            recipients=recipient,
            subject=subject,
            body=body
        )
        print(msg)
        mail.send(msg)
        print('after mail send')


app.sendEmail2 = sendEmail2


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
            data = request.json
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
            # body = ("Hello,")

            # msg = Message(
            #     data['message_subject'],
            #     sender="support@nityaayurveda.com",
            #     recipients=["anureetksandhu7@gmail.com"],
            # )
            # msg.body = (
            #     "Hi !\n\n"

            # )
            # # print('msg-bd----', msg.body)
            # mail.send(msg)
        return response


api.add_resource(Properties, '/properties')
api.add_resource(Property, '/properties/<property_uid>')
api.add_resource(NotManagedProperties, '/notManagedProperties')
api.add_resource(TenantDashboard, '/tenantDashboard')
api.add_resource(TenantDetails, '/tenantDetails')

api.add_resource(ManagerDashboard, '/managerDashboard')
api.add_resource(OwnerDashboard, '/ownerDashboard')
api.add_resource(Users, '/users')
api.add_resource(Login, '/login')
api.add_resource(OwnerProfileInfo, '/ownerProfileInfo')
api.add_resource(ManagerProfileInfo, '/managerProfileInfo')
api.add_resource(TenantProfileInfo, '/tenantProfileInfo')
api.add_resource(BusinessProfileInfo, '/businessProfileInfo')
api.add_resource(Rentals, '/rentals')
api.add_resource(EndLease, '/endLease')
api.add_resource(ExtendLease, '/extendLease')
api.add_resource(ExtendLeaseCRON_CLASS, '/ExtendLeaseCRON_CLASS')
api.add_resource(LeasetoMonth_CLASS, '/LeasetoMonth_CLASS')
api.add_resource(LateFee_CLASS, '/LateFee_CLASS')
api.add_resource(LateFeeExtraCharges_CLASS, '/LateFeeExtraCharges_CLASS')
api.add_resource(PerDay_LateFee_CLASS, '/PerDay_LateFee_CLASS')
api.add_resource(PerDay_LateFeeExtraCharges_CLASS,
                 '/PerDay_LateFeeExtraCharges_CLASS')
api.add_resource(stripe_key, "/stripe_key/<string:desc>")

api.add_resource(LeaseExpiringNotify_CLASS, '/LeaseExpiringNotify_CLASS')
api.add_resource(SignUpForm, '/signUpForm')

api.add_resource(Purchases, '/purchases')
api.add_resource(CreateExpenses, '/createExpenses')
api.add_resource(CreateRevenues, '/createRevenues')
api.add_resource(Payments, '/payments')
api.add_resource(UserPayments, '/userPayments')
api.add_resource(ManagerClients, '/managerClients')
api.add_resource(ManagerPropertyTenants, '/managerPropertyTenants')
api.add_resource(ManagerDocuments, '/managerDocuments')

api.add_resource(CancelAgreement, '/cancelAgreement')
api.add_resource(ManagerContractEnd_CLASS,
                 '/managerContractEnd_CLASS')
api.add_resource(TenantRentalEnd_CLASS, '/tenantRentalEnd_CLASS')

api.add_resource(OwnerPayments, '/ownerPayments')

api.add_resource(OwnerProperties, '/ownerProperties')
api.add_resource(OwnerPropertyBills, '/ownerPropertyBills')

api.add_resource(OwnerDocuments, '/ownerDocuments')
api.add_resource(Message, '/message')
api.add_resource(ManagerProperties, '/managerProperties')
# api.add_resource(ManagerContractFees_CLASS, '/ManagerContractFees_CLASS')

api.add_resource(TenantPayments_CLASS, '/TenantPayments_CLASS')


api.add_resource(TenantProperties, '/tenantProperties')
api.add_resource(Refresh, '/refresh')
api.add_resource(Businesses, '/businesses')
api.add_resource(Employees, '/employees')
api.add_resource(MaintenanceRequests, '/maintenanceRequests')
api.add_resource(MaintenanceRequestsandQuotes, '/maintenanceRequestsandQuotes')
api.add_resource(OwnerMaintenanceRequestsandQuotes,
                 '/ownerMaintenanceRequestsandQuotes')
api.add_resource(MaintenanceQuotes, '/maintenanceQuotes')
api.add_resource(Contracts, '/contracts')
api.add_resource(PropertiesManagerDetail, '/propertiesManagerDetail')
api.add_resource(PropertyInfo, '/propertyInfo')
api.add_resource(ManagerExpenses, '/managerExpenses')
api.add_resource(ManagerPayments, '/managerPayments')
api.add_resource(AvailableProperties,
                 '/availableProperties')
api.add_resource(PropertiesOwner,
                 '/propertiesOwner')
api.add_resource(PropertiesOwnerDetail,
                 '/propertiesOwnerDetail')
api.add_resource(Applications, '/applications')
api.add_resource(EndEarly, '/endEarly')
api.add_resource(UserSocialLogin, '/userSocialLogin/<string:email>')
api.add_resource(UserSocialSignup, '/userSocialSignup')
api.add_resource(UserDetails, "/UserDetails/<string:user_id>")
api.add_resource(UserToken, "/UserToken/<string:user_email_id>")

api.add_resource(Appliances, "/appliances")

api.add_resource(UpdateAccessToken, "/UpdateAccessToken/<string:user_id>")
api.add_resource(
    AvailableAppointmentsTenant,
    "/AvailableAppointmentsTenant/<string:date_value>/<string:duration>/<string:user_id>/<string:start_time>,<string:end_time>"
)
api.add_resource(
    AvailableAppointmentsMaintenance,
    "/AvailableAppointmentsMaintenance/<string:date_value>/<string:duration>/<string:user_id>/<string:start_time>,<string:end_time>"
)

api.add_resource(LeaseTenants, "/leaseTenants")
api.add_resource(Bills, "/bills")
if __name__ == '__main__':
    app.run(debug=True)
