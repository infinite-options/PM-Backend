
from flask import Flask
from flask_restful import Api
from flask_jwt_extended import JWTManager
from flask_cors import CORS

from properties import Properties, Property
from users import Users, Login
from ownerProfileInfo import OwnerProfileInfo
from managerProfileInfo import ManagerProfileInfo
from tenantProfileInfo import TenantProfileInfo
from businessProfileInfo import BusinessProfileInfo
from rentals import Rentals
from purchases import Purchases
from payments import Payments, UserPayments
from ownerProperties import OwnerProperties
from managerProperties import ManagerProperties
from tenantProperties import TenantProperties
from refresh import Refresh
from businesses import Businesses
from employees import Employees
from maintenanceRequests import MaintenanceRequests
from maintenanceQuotes import MaintenanceQuotes
from contracts import Contracts
from propertyInfo import PropertyInfo

app = Flask(__name__)
CORS(app)
api = Api(app)
app.config['JWT_SECRET_KEY'] = 'secret'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600
app.config['PROPAGATE_EXCEPTIONS'] = True
jwt = JWTManager(app)

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
api.add_resource(Payments, '/payments')
api.add_resource(UserPayments, '/userPayments')
api.add_resource(OwnerProperties, '/ownerProperties')
api.add_resource(ManagerProperties, '/managerProperties')
api.add_resource(TenantProperties, '/tenantProperties')
api.add_resource(Refresh, '/refresh')
api.add_resource(Businesses, '/businesses')
api.add_resource(Employees, '/employees')
api.add_resource(MaintenanceRequests, '/maintenanceRequests')
api.add_resource(MaintenanceQuotes, '/maintenanceQuotes')
api.add_resource(Contracts, '/contracts')
api.add_resource(PropertyInfo, '/propertyInfo')

if __name__ == '__main__':
    app.run(debug=True)
