import requests
from flask import request
from flask_restful import Resource

class ApplePay(Resource):
    def post(self):
        data = request.get_json()
        payload = {
            "merchantIdentifier": data.get('merchantIdentifier'),
            "displayName": data.get('displayName'),
            "initiative": data.get('initiative'),
            "initiativeContext": data.get('initiativeContext')
        }
        merchantSession = requests.post(data.get('url'), json=payload, cert=('certs/ApplePayCrt.pem', 'certs/ApplePayKey.pem'))
        return merchantSession.json()