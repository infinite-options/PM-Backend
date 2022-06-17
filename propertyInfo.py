
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


class PropertiesManagerDetail(Resource):
    def get(self):
        response = {}
        filters = ['property_uid']
        where = {}
        with connect() as db:
            for filter in filters:
                filterValue = request.args.get(filter)
                if filterValue is not None:
                    where[filter] = filterValue

                    response = db.execute(
                        """SELECT * FROM pm.properties p WHERE p.property_uid = \'"""
                        + filterValue
                        + """\'""")
                    for i in range(len(response['result'])):
                        property_id = response['result'][i]['property_uid']
                        print(property_id)
                        pid = {'linked_property_id': property_id}
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
                        property_res = db.execute("""SELECT 
                                                        pm.*, 
                                                        b.business_uid AS manager_id, 
                                                        b.business_name AS manager_business_name, 
                                                        b.business_email AS manager_email, 
                                                        b.business_phone_number AS manager_phone_number 
                                                        FROM pm.propertyManager pm 
                                                        LEFT JOIN businesses b 
                                                        ON b.business_uid = pm.linked_business_id 
                                                        WHERE pm.linked_property_id = \'""" + property_id + """\'""")

                        response['result'][i]['property_manager'] = list(
                            property_res['result'])
                        response['result'][i]['management_status'] = ""
                        response['result'][i]['managerInfo'] = {}
                        if len(property_res['result']) > 0:

                            for pr in range(len(property_res['result'])):
                                if property_res['result'][pr]['management_status'] == 'ACCEPTED':
                                    response['result'][i]['management_status'] = "ACCEPTED"
                                    response['result'][i]['managerInfo'] = property_res['result'][pr]
                                else:
                                    print('in else')
                        else:
                            response['result'][i]['management_status'] = ""
                            response['result'][i]['managerInfo'] = {}
                        owner_id = response['result'][i]['owner_id']
                        owner_res = db.execute("""SELECT 
                                                        o.owner_first_name AS owner_first_name, 
                                                        o.owner_last_name AS owner_last_name, 
                                                        o.owner_email AS owner_email ,
                                                        o.owner_phone_number AS owner_phone_number
                                                        FROM pm.ownerProfileInfo o 
                                                        WHERE o.owner_id = \'""" + owner_id + """\'""")
                        response['result'][i]['owner'] = list(
                            owner_res['result'])
                        rental_res = db.execute("""SELECT 
                                                        r.*,
                                                        tpi.tenant_id AS tenant_id,
                                                        tpi.tenant_first_name AS tenant_first_name,
                                                        tpi.tenant_last_name AS tenant_last_name,
                                                        tpi.tenant_email AS tenant_email,
                                                        tpi.tenant_phone_number AS tenant_phone_number
                                                        FROM pm.rentals r 
                                                        LEFT JOIN pm.leaseTenants lt
                                                        ON lt.linked_rental_uid = r.rental_uid
                                                        LEFT JOIN pm.tenantProfileInfo tpi
                                                        ON tpi.tenant_id = lt.linked_tenant_id
                                                        WHERE r.rental_property_id = \'""" + property_id + """\'""")
                        response['result'][i]['rentalInfo'] = list(
                            rental_res['result'])
                        if len(rental_res['result']) > 0:
                            response['result'][i]['rental_status'] = rental_res['result'][0]['rental_status']
                        else:
                            response['result'][i]['rental_status'] = ""

        return response
