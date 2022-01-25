from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from security import createTokens

class Refresh(Resource):
    decorators = [jwt_required(refresh=True)]
    def get(self):
        response = {}
        user = get_jwt_identity()
        tokens = createTokens(user)
        response['code'] = 200
        response['message'] = 'Session refreshed'
        response['result'] = tokens
        return response
