
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from data import connect
import json


class TenantProperties(Resource):
    decorators = [jwt_required()]

    def get(self):
        response = {}
        user = get_jwt_identity()
        with connect() as db:
            # where = {
            #     'tenant_id': user['user_uid']
            # }
            # response = db.execute("""SELECT * FROM pm.propertyInfo WHERE rental_status = 'ACTIVE' AND management_status <> 'REJECTED' AND tenant_id = \'"""
            #                       + user['user_uid']
            #                       + """\'""")
            # response = db.select(
            #     "propertyInfo WHERE rental_status= 'ACTIVE'", where)
            print('here', user['user_uid'])
            response = db.execute(""" SELECT * FROM pm.properties
                                        LEFT JOIN pm.rentals 
                                        ON rental_property_id = property_uid
                                        LEFT JOIN pm.leaseTenants
                                        ON linked_rental_uid = rental_uid
                                        LEFT JOIN pm.propertyManager
                                        ON linked_property_id = property_uid
                                        WHERE linked_tenant_id = \'""" + user['user_uid'] + """\' AND rental_status = 'ACTIVE' AND management_status <> 'REJECTED'; """)

            for i in range(len(response['result'])):
                property_id = response['result'][i]['property_uid']
                print(property_id)
                property_res = db.execute("""SELECT
                                            b.business_uid AS manager_id,
                                            b.business_name AS manager_business_name,
                                            b.business_email AS manager_email,
                                            b.business_phone_number AS manager_phone_number
                                            FROM pm.propertyManager pm
                                            LEFT JOIN businesses b
                                            ON b.business_uid = pm.linked_business_id
                                            WHERE pm.linked_property_id = \'""" + property_id + """\'
                                            AND pm.management_status = 'ACCEPTED' """)

                response['result'][i]['property_manager'] = list(
                    property_res['result'])

                owner_id = response['result'][i]['owner_id']
                # owner info for the property
                owner_res = db.execute("""SELECT 
                                            o.owner_id AS owner_id,
                                            o.owner_first_name AS owner_first_name, 
                                            o.owner_last_name AS owner_last_name, 
                                            o.owner_email AS owner_email ,
                                            o.owner_phone_number AS owner_phone_number
                                            FROM pm.ownerProfileInfo o 
                                            WHERE o.owner_id = \'""" + owner_id + """\'""")
                response['result'][i]['owner'] = list(owner_res['result'])
                # rental info for the property
                rental_res = db.execute("""SELECT 
                                            tpi.tenant_id AS tenant_id,
                                            tpi.tenant_first_name AS tenant_first_name,
                                            tpi.tenant_last_name AS tenant_last_name,
                                            u.email AS tenant_email,
                                            u.phone_number AS tenant_phone_number
                                            FROM pm.tenantProfileInfo tpi
                                            LEFT JOIN pm.users u
                                            ON u.user_uid = tpi.tenant_id
                                            WHERE tenant_id = \'""" + user['user_uid'] + """\' """)
                response['result'][i]['tenantInfo'] = list(
                    rental_res['result'])
                tenant_expenses = db.execute("""SELECT *
                                                        FROM pm.purchases p
                                                        LEFT JOIN
                                                        pm.payments pa
                                                        ON pa.pay_purchase_id = p.purchase_uid
                                                        WHERE p.pur_property_id = \'""" + property_id + """\'
                                                        AND (p.purchase_type= "RENT" OR p.purchase_type= "EXTRA CHARGES")""")
                response['result'][i]['tenantExpenses'] = list(
                    tenant_expenses['result'])
        return response
