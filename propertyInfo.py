
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
                print(response)
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
                "SELECT * FROM pm.propertyInfo WHERE  (rental_status <> 'ACTIVE' AND rental_status <> 'PROCESSING') OR rental_status IS NULL AND (manager_id IS NOT NULL)  ")
            # response = db.execute("""SELECT * FROM pm.propertyInfo WHERE rental_status <> 'ACTIVE' AND rental_status <> 'PROCESSING' OR rental_status IS NULL OR tenant_id = \'"""
            #                       + tenant_id
            #                       + """\'""")
            # response = db.execute(sql)
            # response = db.execute(
            #     "SELECT * FROM pm.propertyInfo WHERE rental_status <> 'ACTIVE' AND rental_status <> 'PROCESSING' OR rental_status IS NULL OR tenant_id = %(tenant_id)s")
        return response


class PropertiesOwner(Resource):
    def get(self):
        response = {}
        filters = ['owner_id']
        where = {}
        with connect() as db:
            for filter in filters:
                filterValue = request.args.get(filter)
                if filterValue is not None:
                    where[filter] = filterValue
                    # print(where, filter)
                    # response = db.execute(
                    #     """SELECT * FROM pm.properties p JOIN pm.propertyManager pM ON pM.linked_property_id = p.property_uid WHERE p.owner_id = \'"""
                    #     + filterValue
                    #     + """\'""")
                    response = db.execute(
                        """SELECT * FROM pm.properties p WHERE p.owner_id = \'"""
                        + filterValue
                        + """\'""")
                    for i in range(len(response['result'])):
                        property_id = response['result'][i]['property_uid']
                        # print(property_id)
                        pid = {'linked_property_id': property_id}
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
                        # print('property_res', property_res)
                        response['result'][i]['property_manager'] = list(
                            property_res['result'])
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
                                                        r.rental_uid AS rental_uid,
                                                        r.rental_property_id AS rental_property_id,
                                                        r.rent_payments AS rent_payments,
                                                        r.lease_start AS lease_start,
                                                        r.lease_end AS lease_end,
                                                        r.rental_status AS rental_status,
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
                        purchases_res = db.execute("""SELECT p.*
                                                        FROM pm.purchases p
                                                        WHERE p.pur_property_id = \'""" + property_id + """\'""")
                        response['result'][i]['purchases'] = list(
                            purchases_res['result'])

                    print(response)

        return response


class PropertiesOwnerDetail(Resource):
    def get(self):
        response = {}
        filters = ['property_uid']
        where = {}
        with connect() as db:
            for filter in filters:
                filterValue = request.args.get(filter)
                if filterValue is not None:
                    where[filter] = filterValue
                    # print(where, filter)
                    # response = db.execute(
                    #     """SELECT * FROM pm.properties p JOIN pm.propertyManager pM ON pM.linked_property_id = p.property_uid WHERE p.owner_id = \'"""
                    #     + filterValue
                    #     + """\'""")
                    response = db.execute(
                        """SELECT * FROM pm.properties p WHERE p.property_uid = \'"""
                        + filterValue
                        + """\'""")
                    for i in range(len(response['result'])):
                        property_id = response['result'][i]['property_uid']
                        # print(property_id)
                        pid = {'linked_property_id': property_id}
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
                        # print('property_res', property_res)
                        response['result'][i]['property_manager'] = list(
                            property_res['result'])
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
                                                        r.rental_uid AS rental_uid,
                                                        r.rental_property_id AS rental_property_id,
                                                        r.rent_payments AS rent_payments,
                                                        r.lease_start AS lease_start,
                                                        r.lease_end AS lease_end,
                                                        r.rental_status AS rental_status,
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
                        purchases_res = db.execute("""SELECT p.*
                                                        FROM pm.purchases p
                                                        WHERE p.pur_property_id = \'""" + property_id + """\'""")
                        response['result'][i]['purchases'] = list(
                            purchases_res['result'])

                    print(response)

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
                    # print(where, filter)
                    # response = db.execute(
                    #     """SELECT * FROM pm.properties p JOIN pm.propertyManager pM ON pM.linked_property_id = p.property_uid WHERE p.owner_id = \'"""
                    #     + filterValue
                    #     + """\'""")
                    response = db.execute(
                        """SELECT * FROM pm.properties p WHERE p.property_uid = \'"""
                        + filterValue
                        + """\'""")
                    for i in range(len(response['result'])):
                        property_id = response['result'][i]['property_uid']
                        # print(property_id)
                        pid = {'linked_property_id': property_id}
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
                        # print('property_res', property_res)
                        response['result'][i]['property_manager'] = list(
                            property_res['result'])
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
                                                        r.rental_uid AS rental_uid,
                                                        r.rental_property_id AS rental_property_id,
                                                        r.rent_payments AS rent_payments,
                                                        r.lease_start AS lease_start,
                                                        r.lease_end AS lease_end,
                                                        r.rental_status AS rental_status,
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
                        purchases_res = db.execute("""SELECT p.*
                                                        FROM pm.purchases p
                                                        WHERE p.pur_property_id = \'""" + property_id + """\'""")
                        response['result'][i]['purchases'] = list(
                            purchases_res['result'])

                    print(response)

        return response
