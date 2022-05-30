
from flask import Flask
from flask_restful import Api
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_mail import Mail, Message

from properties import Properties, Property
from users import Users, Login, UpdateAccessToken, UserDetails, UserToken, AvailableAppointments
from ownerProfileInfo import OwnerProfileInfo
from managerProfileInfo import ManagerProfileInfo
from tenantProfileInfo import TenantProfileInfo
from businessProfileInfo import BusinessProfileInfo
from rentals import Rentals
from purchases import Purchases, CreateExpenses
from payments import Payments, UserPayments
from ownerProperties import OwnerProperties, PropertiesOwnerDetail, PropertiesOwner
from managerProperties import ManagerProperties
from tenantProperties import TenantProperties
from refresh import Refresh
from businesses import Businesses
from employees import Employees
from maintenanceRequests import MaintenanceRequests
from maintenanceRequests import MaintenanceRequestsandQuotes
from maintenanceQuotes import MaintenanceQuotes
from contracts import Contracts
from propertyInfo import PropertyInfo, AvailableProperties
from applications import Applications
from socialLogin import UserSocialLogin, UserSocialSignup
from leaseTenants import LeaseTenants

app = Flask(__name__)

# cors = CORS(app, resources={r'/api/*': {'origins': '*'}})
# cors = CORS(app)
CORS(app)
api = Api(app)
app.config['JWT_SECRET_KEY'] = 'secret'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600
app.config['PROPAGATE_EXCEPTIONS'] = True
jwt = JWTManager(app)
app.config["MAIL_SERVER"] = "smtp.mydomain.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USE_SSL"] = True
app.config["MAIL_USERNAME"] = "support@skedul.online"
app.config["MAIL_PASSWORD"] = "SupportSkedul1"
app.config["MAIL_DEFAULT_SENDER"] = "support@skedul.online"
app.config["MAIL_SUPPRESS_SEND"] = False
mail = Mail(app)


def sendEmail(recipient, subject, body):
    msg = Message(
        sender='support@skedul.online',
        recipients=[recipient],
        subject=subject,
        body=body
    )
    mail.send(msg)


app.sendEmail = sendEmail

api.add_resource(Properties, '/properties')
api.add_resource(Property, '/properties/<property_uid>')
api.add_resource(Users, '/users')
api.add_resource(Login, '/login')
api.add_resource(OwnerProfileInfo, '/ownerProfileInfo')
api.add_resource(ManagerProfileInfo, '/managerProfileInfo')
api.add_resource(TenantProfileInfo, '/tenantProfileInfo')
api.add_resource(BusinessProfileInfo, '/businessProfileInfo')
api.add_resource(Rentals, '/rentals')
api.add_resource(Purchases, '/purchases')
api.add_resource(CreateExpenses, '/createExpenses')
api.add_resource(Payments, '/payments')
api.add_resource(UserPayments, '/userPayments')
api.add_resource(OwnerProperties, '/ownerProperties')
api.add_resource(ManagerProperties, '/managerProperties')
api.add_resource(TenantProperties, '/tenantProperties')
api.add_resource(Refresh, '/refresh')
api.add_resource(Businesses, '/businesses')
api.add_resource(Employees, '/employees')
api.add_resource(MaintenanceRequests, '/maintenanceRequests')
api.add_resource(MaintenanceRequestsandQuotes, '/maintenanceRequestsandQuotes')
api.add_resource(MaintenanceQuotes, '/maintenanceQuotes')
api.add_resource(Contracts, '/contracts')
api.add_resource(PropertyInfo, '/propertyInfo')
# api.add_resource(AvailableProperties,
#                  '/availableProperties/<string:tenant_id>')
api.add_resource(AvailableProperties,
                 '/availableProperties')
api.add_resource(PropertiesOwner,
                 '/propertiesOwner')
api.add_resource(PropertiesOwnerDetail,
                 '/propertiesOwnerDetail')
api.add_resource(Applications, '/applications')
api.add_resource(UserSocialLogin, '/userSocialLogin/<string:email>')
api.add_resource(UserSocialSignup, '/userSocialSignup')
api.add_resource(UserDetails, "/UserDetails/<string:user_id>")
api.add_resource(UserToken, "/UserToken/<string:user_email_id>")
api.add_resource(UpdateAccessToken, "/UpdateAccessToken/<string:user_id>")
api.add_resource(
    AvailableAppointments,
    "/AvailableAppointments/<string:date_value>/<string:duration>/<string:user_id>/<string:start_time>,<string:end_time>"
)
api.add_resource(LeaseTenants, "/leaseTenants")
if __name__ == '__main__':
    app.run(debug=True)
