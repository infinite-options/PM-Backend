
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from data import connect
import json


class PropertyInfo(Resource):
    def get(self):
        response = {}
        filters = ['property_uid', 'owner_id', 'manager_id', 'tenant_id']
        where = {}
        for filter in filters:
            filterValue = request.args.get(filter)
            if filterValue is not None:
                where[filter] = filterValue
        with connect() as db:
            response = db.select('propertyInfo', where)
        return response


class AvailableProperties(Resource):
    def get(self, tenant_id):
        response = {}
        print(tenant_id)
        with connect() as db:
            print(tenant_id)
            # sql = """SELECT * FROM pm.propertyInfo WHERE rental_status <> 'ACTIVE' AND rental_status <> 'PROCESSING' OR rental_status IS NULL OR tenant_id = \'"""
            # + tenant_id
            # + """\'"""
            # print(sql)
            response = db.execute("""SELECT * FROM pm.propertyInfo WHERE rental_status <> 'ACTIVE' AND rental_status <> 'PROCESSING' OR rental_status IS NULL OR tenant_id = \'"""
                                  + tenant_id
                                  + """\'""")
            # response = db.execute(sql)
            # response = db.execute(
            #     "SELECT * FROM pm.propertyInfo WHERE rental_status <> 'ACTIVE' AND rental_status <> 'PROCESSING' OR rental_status IS NULL OR tenant_id = %(tenant_id)s")
        return response
