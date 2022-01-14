
from flask import Flask
from flask_restful import Api
from flask_jwt_extended import JWTManager
from flask_cors import CORS

from properties import Properties
from users import Users, Login
from ownerProfileInfo import OwnerProfileInfo
from managerProfileInfo import ManagerProfileInfo
from tenantProfileInfo import TenantProfileInfo
from businessProfileInfo import BusinessProfileInfo
from rentals import Rentals
from purchases import Purchases
from payments import Payments

app = Flask(__name__)
CORS(app)
api = Api(app)
app.config['JWT_SECRET_KEY'] = 'secret'
jwt = JWTManager(app)

api.add_resource(Properties, '/properties')
api.add_resource(Users, '/users')
api.add_resource(Login, '/login')
api.add_resource(OwnerProfileInfo, '/ownerProfileInfo')
api.add_resource(ManagerProfileInfo, '/managerProfileInfo')
api.add_resource(TenantProfileInfo, '/tenantProfileInfo')
api.add_resource(BusinessProfileInfo, '/businessProfileInfo')
api.add_resource(Rentals, '/rentals')
api.add_resource(Purchases, '/purchases')
api.add_resource(Payments, '/payments')

if __name__ == '__main__':
    app.run(debug=True)
