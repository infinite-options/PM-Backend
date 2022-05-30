
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from matplotlib.font_manager import json_dump

from data import connect
from datetime import date
import json


class PropertyInfo(Resource):
    def get(self):
        response = {}
        filters = ['property_uid', 'owner_id', 'manager_id', 'tenant_id']
        where = {}
        filterType = ''
        filterVal = ''
        with connect() as db:
            for filter in filters:
                filterValue = request.args.get(filter)
                if filterValue is not None:
                    where[filter] = filterValue
                    print(where, filter)
                    filterType = filter
                    filterVal = filterValue

            if filterType == 'manager_id':
                print('here if')
                response = db.execute(
                    """SELECT * FROM pm.propertyInfo WHERE management_status <> 'REJECTED' AND manager_id = \'"""
                    + filterVal
                    + """\' """)
                for i in range(len(response['result'])):
                    property_id = response['result'][i]['property_uid']
                    application_res = db.execute("""SELECT 
                                                        *
                                                        FROM pm.applications WHERE property_uid = \'""" + property_id + """\'""")
                    # print('application_res', application_res)
                    response['result'][i]['applications'] = list(
                        application_res['result'])
                    maintenance_res = db.execute("""SELECT *
                                                        FROM pm.maintenanceRequests mr
                                                        WHERE mr.property_uid = \'""" + property_id + """\'
                                                        """)
                    response['result'][i]['maintenanceRequests'] = list(
                        maintenance_res['result'])
                # print(response)
            elif filterType == 'owner_id':
                print('here if')
                response = db.execute(
                    """SELECT * FROM pm.propertyInfo WHERE owner_id = \'"""
                    + filterVal
                    + """\' """)
                print(response)
            else:
                print('here else')
                response = db.select('propertyInfo', where)
        return response


class AvailableProperties(Resource):
    def get(self):
        response = {}

        with connect() as db:

            # sql = """SELECT * FROM pm.propertyInfo WHERE rental_status <> 'ACTIVE' AND rental_status <> 'PROCESSING' OR rental_status IS NULL OR tenant_id = \'"""
            # + tenant_id
            # + """\'"""
            # print(sql)

            response = db.execute(
                "SELECT * FROM pm.propertyInfo WHERE  (rental_status <> 'ACTIVE' AND rental_status <> 'PROCESSING') OR rental_status IS NULL AND (manager_id IS NOT NULL) AND (management_status = 'ACCEPTED') ")
            # response = db.execute("""SELECT * FROM pm.propertyInfo WHERE rental_status <> 'ACTIVE' AND rental_status <> 'PROCESSING' OR rental_status IS NULL OR tenant_id = \'"""
            #                       + tenant_id
            #                       + """\'""")
            # response = db.execute(sql)
            # response = db.execute(
            #     "SELECT * FROM pm.propertyInfo WHERE rental_status <> 'ACTIVE' AND rental_status <> 'PROCESSING' OR rental_status IS NULL OR tenant_id = %(tenant_id)s")
        return response
