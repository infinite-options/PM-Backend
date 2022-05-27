
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
                    today = date.today()
                    # list of all properties for the owner
                    response = db.execute(
                        """SELECT * FROM pm.properties p WHERE p.owner_id = \'"""
                        + filterValue
                        + """\'""")
                    # info for each property
                    for i in range(len(response['result'])):
                        property_id = response['result'][i]['property_uid']
                        print(property_id)
                        pid = {'linked_property_id': property_id}
                        # property manager info for property
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
                        # management status for property
                        if len(property_res['result']) > 0:
                            for pr in range(len(property_res['result'])):

                                if property_res['result'][pr]['management_status'] == 'ACCEPTED':

                                    response['result'][i]['management_status'] = "ACCEPTED"
                                else:
                                    print('here in else')
                        else:
                            response['result'][i]['management_status'] = ""
                        owner_id = response['result'][i]['owner_id']
                        # owner info for the property
                        owner_res = db.execute("""SELECT 
                                                        o.owner_first_name AS owner_first_name, 
                                                        o.owner_last_name AS owner_last_name, 
                                                        o.owner_email AS owner_email ,
                                                        o.owner_phone_number AS owner_phone_number
                                                        FROM pm.ownerProfileInfo o 
                                                        WHERE o.owner_id = \'""" + owner_id + """\'""")
                        response['result'][i]['owner'] = list(
                            owner_res['result'])
                        # rental info for the property
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
                        # rental status for the property
                        if len(rental_res['result']) > 0:
                            response['result'][i]['rental_status'] = rental_res['result'][0]['rental_status']
                        else:
                            response['result'][i]['rental_status'] = ""
                        # monthly revenue for the property
                        owner_revenue = db.execute("""SELECT *
                                                        FROM pm.purchases p
                                                        LEFT JOIN
                                                        pm.payments pa
                                                        ON pa.pay_purchase_id = p.purchase_uid
                                                        WHERE p.pur_property_id = \'""" + property_id + """\'
                                                        AND ({fn MONTHNAME(pa.payment_date)} = {fn MONTHNAME(now())} AND YEAR(pa.payment_date) = YEAR(now()))
                                                        AND p.purchase_status ="PAID" 
                                                        AND (p.purchase_type= "RENT" OR p.purchase_type= "EXTRA CHARGES")""")
                        response['result'][i]['owner_revenue'] = list(
                            owner_revenue['result'])
                        # annual revenue for the property
                        yearly_owner_revenue = db.execute("""SELECT *
                                                        FROM pm.purchases p
                                                        LEFT JOIN
                                                        pm.payments pa
                                                        ON pa.pay_purchase_id = p.purchase_uid
                                                        WHERE p.pur_property_id = \'""" + property_id + """\'
                                                        AND (YEAR(p.purchase_date) = YEAR(now()))
                                                        AND p.purchase_status ="PAID" 
                                                        AND (p.purchase_type = "RENT" OR p.purchase_type = "EXTRA CHARGES")""")

                        response['result'][i]['year_revenue'] = 0
                        if len(yearly_owner_revenue['result']) > 0:
                            for pr in range(len(yearly_owner_revenue['result'])):

                                response['result'][i]['year_revenue'] = response['result'][i]['year_revenue'] + int(
                                    yearly_owner_revenue['result'][pr]['amount_paid'])
                        else:
                            response['result'][i]['year_revenue'] = 0
                        # monthly expense for the property
                        owner_expense = db.execute("""SELECT *
                                                        FROM pm.purchases p
                                                        LEFT JOIN
                                                        pm.payments pa
                                                        ON pa.pay_purchase_id = p.purchase_uid
                                                        WHERE p.pur_property_id = \'""" + property_id + """\'
                                                        AND ({fn MONTHNAME(p.purchase_date)} = {fn MONTHNAME(now())} AND YEAR(p.purchase_date) = YEAR(now()))
                                                        AND p.purchase_status ="PAID" 
                                                        AND (p.purchase_type <> "RENT" AND p.purchase_type <> "EXTRA CHARGES")""")
                        response['result'][i]['owner_expense'] = list(
                            owner_expense['result'])
                        # annual expense for the property
                        yearly_owner_expense = db.execute("""SELECT *
                                                        FROM pm.purchases p
                                                        LEFT JOIN
                                                        pm.payments pa
                                                        ON pa.pay_purchase_id = p.purchase_uid
                                                        WHERE p.pur_property_id = \'""" + property_id + """\'
                                                        AND (YEAR(p.purchase_date) = YEAR(now()))
                                                        AND p.purchase_status ="PAID" 
                                                        AND (p.purchase_type <> "RENT" AND p.purchase_type <> "EXTRA CHARGES")""")

                        response['result'][i]['year_expense'] = 0
                        if len(yearly_owner_expense['result']) > 0:
                            for pr in range(len(yearly_owner_expense['result'])):

                                response['result'][i]['year_expense'] = response['result'][i]['year_expense'] + int(
                                    yearly_owner_expense['result'][pr]['amount_paid'])
                        else:
                            print('in else')
                        # monthly expense for the property to include mortgage
                        if response['result'][i]['mortgages'] is not None:
                            response['result'][i]['year_expense'] = response['result'][i]['year_expense'] + (today.month*(int(json.loads(response['result'][i]['mortgages'])[
                                'amount'])))
                        # monthly expense for the property to include taxes
                        if response['result'][i]['taxes'] is not None:
                            if len(eval(response['result'][i]['taxes'])) > 0:
                                for te in range(len(eval(response['result'][i]['taxes']))):
                                    response['result'][i]['year_expense'] = response['result'][i]['year_expense'] + (today.month * int(eval(response['result'][i]
                                                                                                                                            ['taxes'])[te]['amount']))
                        print('after mortgage and taxes',
                              response['result'][i]['year_expense'])
                    # print(response)

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
                    today = date.today()
                    response = db.execute(
                        """SELECT * FROM pm.properties p WHERE p.property_uid = \'"""
                        + filterValue
                        + """\'""")
                    for i in range(len(response['result'])):
                        property_id = response['result'][i]['property_uid']
                        print(property_id)
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

                        response['result'][i]['property_manager'] = list(
                            property_res['result'])
                        if len(property_res['result']) > 0:

                            for pr in range(len(property_res['result'])):
                                if property_res['result'][pr]['management_status'] == 'ACCEPTED':
                                    response['result'][i]['management_status'] = "ACCEPTED"
                                else:
                                    print('in else')
                        else:
                            response['result'][i]['management_status'] = ""
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
                        owner_revenue = db.execute("""SELECT p.*
                                                        FROM pm.purchases p
                                                        LEFT JOIN
                                                        pm.payments pa
                                                        ON pa.pay_purchase_id = p.purchase_uid
                                                        WHERE p.pur_property_id = \'""" + property_id + """\'
                                                        AND ({fn MONTHNAME(pa.payment_date)} = {fn MONTHNAME(now())} AND YEAR(pa.payment_date) = YEAR(now()))
                                                        AND p.purchase_status ="PAID" 
                                                        AND (p.purchase_type= "RENT" OR p.purchase_type= "EXTRA CHARGES")""")
                        response['result'][i]['owner_revenue'] = list(
                            owner_revenue['result'])
                        yearly_owner_revenue = db.execute("""SELECT *
                                                        FROM pm.purchases p
                                                        LEFT JOIN
                                                        pm.payments pa
                                                        ON pa.pay_purchase_id = p.purchase_uid
                                                        WHERE p.pur_property_id = \'""" + property_id + """\'
                                                        AND (YEAR(p.purchase_date) = YEAR(now()))
                                                        AND p.purchase_status ="PAID" 
                                                        AND (p.purchase_type = "RENT" OR p.purchase_type = "EXTRA CHARGES")""")

                        response['result'][i]['year_revenue'] = 0
                        if len(yearly_owner_revenue['result']) > 0:
                            for pr in range(len(yearly_owner_revenue['result'])):

                                response['result'][i]['year_revenue'] = response['result'][i]['year_revenue'] + int(
                                    yearly_owner_revenue['result'][pr]['amount_paid'])
                        else:
                            response['result'][i]['year_revenue'] = 0
                        owner_expense = db.execute("""SELECT p.*
                                                        FROM pm.purchases p
                                                        LEFT JOIN
                                                        pm.payments pa
                                                        ON pa.pay_purchase_id = p.purchase_uid
                                                        WHERE p.pur_property_id = \'""" + property_id + """\'
                                                        AND ({fn MONTHNAME(p.purchase_date)} = {fn MONTHNAME(now())} AND YEAR(p.purchase_date) = YEAR(now()))
                                                        AND p.purchase_status ="PAID" 
                                                        AND (p.purchase_type <> "RENT" AND p.purchase_type <> "EXTRA CHARGES")""")
                        response['result'][i]['owner_expense'] = list(
                            owner_expense['result'])
                        yearly_owner_expense = db.execute("""SELECT *
                                                        FROM pm.purchases p
                                                        LEFT JOIN
                                                        pm.payments pa
                                                        ON pa.pay_purchase_id = p.purchase_uid
                                                        WHERE p.pur_property_id = \'""" + property_id + """\'
                                                        AND (YEAR(p.purchase_date) = YEAR(now()))
                                                        AND p.purchase_status ="PAID" 
                                                        AND (p.purchase_type <> "RENT" AND p.purchase_type <> "EXTRA CHARGES")""")
                        print(response['result'][i]['mortgages'])
                        response['result'][i]['year_expense'] = 0
                        if len(yearly_owner_expense['result']) > 0:
                            for pr in range(len(yearly_owner_expense['result'])):

                                response['result'][i]['year_expense'] = response['result'][i]['year_expense'] + int(
                                    yearly_owner_expense['result'][pr]['amount_paid'])
                        else:
                            response['result'][i]['year_expense'] = 0
                        print('before mortgage and taxes',
                              response['result'][i]['year_expense'])
                        if response['result'][i]['mortgages'] is not None:

                            response['result'][i]['year_expense'] = response['result'][i]['year_expense'] + (today.month*(int(json.loads(response['result'][i]['mortgages'])[
                                'amount'])))
                        if response['result'][i]['taxes'] is not None:
                            if len(eval(response['result'][i]['taxes'])) > 0:
                                for te in range(len(eval(response['result'][i]['taxes']))):
                                    response['result'][i]['year_expense'] = response['result'][i]['year_expense'] + (today.month * int(eval(response['result'][i]
                                                                                                                                            ['taxes'])[te]['amount']))
                        print('after mortgage and taxes',
                              response['result'][i]['year_expense'])

                    # print(response)

        return response
