
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from data import connect
from datetime import date, datetime
import json


class OwnerProperties(Resource):
    decorators = [jwt_required()]

    def get(self):
        response = {}
        user = get_jwt_identity()
        with connect() as db:
            where = {
                'owner_id': user['user_uid']
            }
            response = db.select('propertyInfo', where)
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
                        response['result'][i]['management_status'] = ""
                        response['result'][i]['managerInfo'] = {}
                        # management status for property
                        if len(property_res['result']) > 0:
                            for pr in range(len(property_res['result'])):
                                if property_res['result'][pr]['management_status'] == 'ACCEPTED':
                                    response['result'][i]['management_status'] = "ACCEPTED"
                                    response['result'][i]['managerInfo'] = property_res['result'][pr]

                        else:
                            response['result'][i]['management_status'] = ""
                            response['result'][i]['managerInfo'] = {}
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

                        rental_revenue = 0
                        extraCharges_revenue = 0
                        maintenance_expenses = 0
                        management_expenses = 0
                        insurance_expenses = 0
                        repairs_expenses = 0
                        mortgage_expenses = 0
                        taxes_expenses = 0

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
                        print(len(owner_revenue['result']))

                        if len(owner_revenue['result']) > 0:
                            for ore in range(len(owner_revenue['result'])):
                                print('ore', owner_revenue['result'][ore])
                                if owner_revenue['result'][ore]['purchase_type'] == 'RENT':
                                    rental_revenue = rental_revenue + \
                                        owner_revenue['result'][ore]['amount_paid']
                                if owner_revenue['result'][ore]['purchase_type'] == 'EXTRA CHARGES':
                                    extraCharges_revenue = extraCharges_revenue + \
                                        owner_revenue['result'][ore]['amount_paid']
                        response['result'][i]['rental_revenue'] = rental_revenue
                        response['result'][i]['extraCharges_revenue'] = extraCharges_revenue

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

                        if len(owner_expense['result']) > 0:
                            for ore in range(len(owner_expense['result'])):
                                # print('ore', owner_expense['result'][ore])
                                if owner_expense['result'][ore]['purchase_type'] == 'MAINTENANCE':
                                    maintenance_expenses = maintenance_expenses + \
                                        owner_expense['result'][ore]['amount_paid']
                                if owner_expense['result'][ore]['purchase_type'] == 'MANAGEMENT':
                                    management_expenses = management_expenses + \
                                        owner_expense['result'][ore]['amount_paid']
                                if owner_expense['result'][ore]['purchase_type'] == 'REPAIRS':
                                    repairs_expenses = repairs_expenses + \
                                        owner_expense['result'][ore]['amount_paid']

                        response['result'][i]['maintenance_expenses'] = maintenance_expenses
                        response['result'][i]['management_expenses'] = management_expenses
                        response['result'][i]['repairs_expenses'] = repairs_expenses

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
                        response['result'][i]['mortgage_year_expense'] = 0
                        response['result'][i]['tax_year_expense'] = 0
                        if len(yearly_owner_expense['result']) > 0:
                            for pr in range(len(yearly_owner_expense['result'])):

                                response['result'][i]['year_expense'] = response['result'][i]['year_expense'] + int(
                                    yearly_owner_expense['result'][pr]['amount_paid'])
                        else:
                            print('')
                        yearCal = today.month - \
                            (datetime.strptime(
                                response['result'][i]['active_date'], '%Y-%m-%d')).month

                        # monthly expense for the property to include mortgage
                        if response['result'][i]['mortgages'] is not None:
                            # if mortgage monthly
                            if json.loads(response['result'][i]['mortgages'])['frequency'] == 'Monthly':
                             # if mortgage monthly and once a month
                                if json.loads(response['result'][i]['mortgages'])['frequency_of_payment'] == 'Once a month':
                                    response['result'][i]['year_expense'] = response['result'][i]['year_expense'] + (yearCal*(int(json.loads(response['result'][i]['mortgages'])[
                                        'amount'])))
                                    response['result'][i]['mortgage_year_expense'] = yearCal*(int(json.loads(response['result'][i]['mortgages'])[
                                        'amount']))
                                    mortgage_expenses = mortgage_expenses + \
                                        int(json.loads(
                                            response['result'][i]['mortgages'])['amount'])
                            # if mortgage monthly and twice a month
                                elif json.loads(response['result'][i]['mortgages'])['frequency_of_payment'] == 'Twice a month':
                                    print('in here elif')
                                    response['result'][i]['year_expense'] = response['result'][i]['year_expense'] + (2*yearCal*(int(json.loads(response['result'][i]['mortgages'])[
                                        'amount'])))
                                    response['result'][i]['mortgage_year_expense'] = 2*yearCal*(int(json.loads(response['result'][i]['mortgages'])[
                                        'amount']))
                                    mortgage_expenses = mortgage_expenses + 2 * \
                                        (int(json.loads(
                                            response['result'][i]['mortgages'])['amount']))
                        # if mortgage weekly
                            elif json.loads(response['result'][i]['mortgages'])['frequency'] == 'Weekly':
                                # if mortgage weekly and once a week
                                if json.loads(response['result'][i]['mortgages'])['frequency_of_payment'] == 'Once a week':
                                    response['result'][i]['year_expense'] = response['result'][i]['year_expense'] + (4*yearCal*(int(json.loads(response['result'][i]['mortgages'])[
                                        'amount'])))
                                    response['result'][i]['mortgage_year_expense'] = 4*yearCal*(int(json.loads(response['result'][i]['mortgages'])[
                                        'amount']))
                                    mortgage_expenses = mortgage_expenses + \
                                        4*(int(json.loads(
                                            response['result'][i]['mortgages'])['amount']))
                             # if mortgage weekly and every other week
                                elif json.loads(response['result'][i]['mortgages'])['frequency_of_payment'] == 'Every other week':
                                    response['result'][i]['year_expense'] = response['result'][i]['year_expense'] + (2*yearCal*(int(json.loads(response['result'][i]['mortgages'])[
                                        'amount'])))
                                    response['result'][i]['mortgage_year_expense'] = 2*yearCal*(int(json.loads(response['result'][i]['mortgages'])[
                                        'amount']))
                                    mortgage_expenses = mortgage_expenses + 2 * \
                                        (int(json.loads(
                                            response['result'][i]['mortgages'])['amount']))
                        print(mortgage_expenses)
                        response['result'][i]['mortgage_expenses'] = mortgage_expenses

                        # monthly expense for the property to include taxes
                        if response['result'][i]['taxes'] is not None:
                            if len(eval(response['result'][i]['taxes'])) > 0:
                                for te in range(len(eval(response['result'][i]['taxes']))):
                                    print('here for', eval(
                                        response['result'][i]['taxes'])[te]['frequency'])
                                    # if tax monthly
                                    if eval(response['result'][i]['taxes'])[te]['frequency'] == 'Monthly':
                                        print('here monthly')
                                     # if taxes monthly and once a month
                                        if eval(response['result'][i]['taxes'])[te]['frequency_of_payment'] == 'Once a month':
                                            response['result'][i]['year_expense'] = response['result'][i]['year_expense'] + (yearCal * int(eval(response['result'][i]
                                                                                                                                                ['taxes'])[te]['amount']))
                                            response['result'][i]['tax_year_expense'] = (
                                                yearCal * int(eval(response['result'][i]['taxes'])[te]['amount']))
                                            taxes_expenses = taxes_expenses + \
                                                int(eval(response['result'][i]['taxes'])[
                                                    te]['amount'])
                                    # if taxes monthly and once a month
                                        elif eval(response['result'][i]['taxes'])[te]['frequency_of_payment'] == 'Twice a month':
                                            response['result'][i]['year_expense'] = response['result'][i]['year_expense'] + (2*yearCal * int(eval(response['result'][i]
                                                                                                                                                  ['taxes'])[te]['amount']))
                                            response['result'][i]['tax_year_expense'] = (
                                                2*yearCal * int(eval(response['result'][i]['taxes'])[te]['amount']))
                                            taxes_expenses = taxes_expenses + \
                                                2*(int(eval(response['result'][i]['taxes'])[
                                                    te]['amount']))
                                     # if tax Annually
                                    elif eval(response['result'][i]['taxes'])[te]['frequency'] == 'Annually':
                                        print('here annually')
                                     # if taxes annually and once a year
                                        if eval(response['result'][i]['taxes'])[te]['frequency_of_payment'] == 'Once a year':
                                            print('here once a year')
                                            response['result'][i]['year_expense'] = response['result'][i]['year_expense'] + (int(eval(response['result'][i]
                                                                                                                                      ['taxes'])[te]['amount']))
                                            response['result'][i]['tax_year_expense'] = (
                                                int(eval(response['result'][i]['taxes'])[te]['amount']))
                                            taxes_expenses = taxes_expenses + \
                                                int(eval(response['result'][i]['taxes'])[
                                                    te]['amount'])
                                     # if taxes annually and twice a year
                                        elif eval(response['result'][i]['taxes'])[te]['frequency_of_payment'] == 'Twice a year':
                                            response['result'][i]['year_expense'] = response['result'][i]['year_expense'] + (2*(int(eval(response['result'][i]
                                                                                                                                         ['taxes'])[te]['amount'])))
                                            response['result'][i]['tax_year_expense'] = (
                                                2 * int(eval(response['result'][i]['taxes'])[te]['amount']))
                                            taxes_expenses = taxes_expenses + \
                                                (int(eval(response['result'][i]['taxes'])[
                                                    te]['amount']))
                                    response['result'][i]['tax_expenses'] = taxes_expenses

                        # monthly expense for the property to include insurance
                        response['result'][i]['insurance_expenses'] = insurance_expenses
                        if response['result'][i]['insurance'] is not None:
                            if len(eval(response['result'][i]['insurance'])) > 0:
                                for te in range(len(eval(response['result'][i]['insurance']))):
                                    response['result'][i]['year_expense'] = response['result'][i]['year_expense'] + (yearCal * int(eval(response['result'][i]
                                                                                                                                        ['insurance'])[te]['amount']))
                                    insurance_expenses = insurance_expenses + \
                                        int(eval(response['result'][i]['insurance'])[
                                            te]['amount'])

                        response['result'][i]['insurance_expenses'] = insurance_expenses
                        # print('after mortgage and taxes',
                        #       response['result'][i]['year_expense'])
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
                        rental_revenue = 0
                        extraCharges_revenue = 0
                        maintenance_expenses = 0
                        management_expenses = 0
                        insurance_expenses = 0
                        repairs_expenses = 0
                        mortgage_expenses = 0
                        taxes_expenses = 0

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
                        print(len(owner_revenue['result']))

                        if len(owner_revenue['result']) > 0:
                            for ore in range(len(owner_revenue['result'])):
                                print('ore', owner_revenue['result'][ore])
                                if owner_revenue['result'][ore]['purchase_type'] == 'RENT':
                                    rental_revenue = rental_revenue + \
                                        owner_revenue['result'][ore]['amount_paid']
                                if owner_revenue['result'][ore]['purchase_type'] == 'EXTRA CHARGES':
                                    extraCharges_revenue = extraCharges_revenue + \
                                        owner_revenue['result'][ore]['amount_paid']
                        response['result'][i]['rental_revenue'] = rental_revenue
                        response['result'][i]['extraCharges_revenue'] = extraCharges_revenue

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
                        # # monthly expense for the property
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

                        if len(owner_expense['result']) > 0:
                            for ore in range(len(owner_expense['result'])):
                                # print('ore', owner_expense['result'][ore])
                                if owner_expense['result'][ore]['purchase_type'] == 'MAINTENANCE':
                                    maintenance_expenses = maintenance_expenses + \
                                        owner_expense['result'][ore]['amount_paid']
                                if owner_expense['result'][ore]['purchase_type'] == 'MANAGEMENT':
                                    management_expenses = management_expenses + \
                                        owner_expense['result'][ore]['amount_paid']

                                if owner_expense['result'][ore]['purchase_type'] == 'REPAIRS':
                                    repairs_expenses = repairs_expenses + \
                                        owner_expense['result'][ore]['amount_paid']

                        response['result'][i]['maintenance_expenses'] = maintenance_expenses
                        response['result'][i]['management_expenses'] = management_expenses
                        response['result'][i]['repairs_expenses'] = repairs_expenses

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
                        response['result'][i]['mortgage_year_expense'] = 0
                        response['result'][i]['tax_year_expense'] = 0
                        yearCal = today.month - \
                            (datetime.strptime(
                                response['result'][i]['active_date'], '%Y-%m-%d')).month
                        if len(yearly_owner_expense['result']) > 0:
                            for pr in range(len(yearly_owner_expense['result'])):

                                response['result'][i]['year_expense'] = response['result'][i]['year_expense'] + int(
                                    yearly_owner_expense['result'][pr]['amount_paid'])
                        else:
                            print('')
                        # monthly expense for the property to include mortgage
                        if response['result'][i]['mortgages'] is not None:
                            # if mortgage monthly
                            if json.loads(response['result'][i]['mortgages'])['frequency'] == 'Monthly':
                             # if mortgage monthly and once a month
                                if json.loads(response['result'][i]['mortgages'])['frequency_of_payment'] == 'Once a month':
                                    response['result'][i]['year_expense'] = response['result'][i]['year_expense'] + (yearCal*(int(json.loads(response['result'][i]['mortgages'])[
                                        'amount'])))
                                    response['result'][i]['mortgage_year_expense'] = yearCal*(int(json.loads(response['result'][i]['mortgages'])[
                                        'amount']))
                                    mortgage_expenses = mortgage_expenses + \
                                        int(json.loads(
                                            response['result'][i]['mortgages'])['amount'])
                            # if mortgage monthly and twice a month
                                elif json.loads(response['result'][i]['mortgages'])['frequency_of_payment'] == 'Twice a month':
                                    print('in here elif')
                                    response['result'][i]['year_expense'] = response['result'][i]['year_expense'] + (2*yearCal*(int(json.loads(response['result'][i]['mortgages'])[
                                        'amount'])))
                                    response['result'][i]['mortgage_year_expense'] = 2*yearCal*(int(json.loads(response['result'][i]['mortgages'])[
                                        'amount']))
                                    mortgage_expenses = mortgage_expenses + 2 * \
                                        (int(json.loads(
                                            response['result'][i]['mortgages'])['amount']))
                        # if mortgage weekly
                            elif json.loads(response['result'][i]['mortgages'])['frequency'] == 'Weekly':
                                # if mortgage weekly and once a week
                                if json.loads(response['result'][i]['mortgages'])['frequency_of_payment'] == 'Once a week':
                                    response['result'][i]['year_expense'] = response['result'][i]['year_expense'] + (4*yearCal*(int(json.loads(response['result'][i]['mortgages'])[
                                        'amount'])))
                                    response['result'][i]['mortgage_year_expense'] = 4*yearCal*(int(json.loads(response['result'][i]['mortgages'])[
                                        'amount']))
                                    mortgage_expenses = mortgage_expenses + \
                                        4*(int(json.loads(
                                            response['result'][i]['mortgages'])['amount']))
                             # if mortgage weekly and every other week
                                elif json.loads(response['result'][i]['mortgages'])['frequency_of_payment'] == 'Every other week':
                                    response['result'][i]['year_expense'] = response['result'][i]['year_expense'] + (2*yearCal*(int(json.loads(response['result'][i]['mortgages'])[
                                        'amount'])))
                                    response['result'][i]['mortgage_year_expense'] = 2*yearCal*(int(json.loads(response['result'][i]['mortgages'])[
                                        'amount']))
                                    mortgage_expenses = mortgage_expenses + 2 * \
                                        (int(json.loads(
                                            response['result'][i]['mortgages'])['amount']))
                        print(mortgage_expenses)
                        response['result'][i]['mortgage_expenses'] = mortgage_expenses

                        # monthly expense for the property to include taxes
                        if response['result'][i]['taxes'] is not None:
                            if len(eval(response['result'][i]['taxes'])) > 0:
                                for te in range(len(eval(response['result'][i]['taxes']))):
                                    print('here for', eval(
                                        response['result'][i]['taxes'])[te]['frequency'])
                                    # if tax monthly
                                    if eval(response['result'][i]['taxes'])[te]['frequency'] == 'Monthly':
                                        print('here monthly')
                                     # if taxes monthly and once a month
                                        if eval(response['result'][i]['taxes'])[te]['frequency_of_payment'] == 'Once a month':
                                            response['result'][i]['year_expense'] = response['result'][i]['year_expense'] + (yearCal * int(eval(response['result'][i]
                                                                                                                                                ['taxes'])[te]['amount']))
                                            response['result'][i]['tax_year_expense'] = (
                                                yearCal * int(eval(response['result'][i]['taxes'])[te]['amount']))
                                            taxes_expenses = taxes_expenses + \
                                                int(eval(response['result'][i]['taxes'])[
                                                    te]['amount'])
                                    # if taxes monthly and once a month
                                        elif eval(response['result'][i]['taxes'])[te]['frequency_of_payment'] == 'Twice a month':
                                            response['result'][i]['year_expense'] = response['result'][i]['year_expense'] + (2*yearCal * int(eval(response['result'][i]
                                                                                                                                                  ['taxes'])[te]['amount']))
                                            response['result'][i]['tax_year_expense'] = (
                                                2*yearCal * int(eval(response['result'][i]['taxes'])[te]['amount']))
                                            taxes_expenses = taxes_expenses + \
                                                2*(int(eval(response['result'][i]['taxes'])[
                                                    te]['amount']))
                                     # if tax Annually
                                    elif eval(response['result'][i]['taxes'])[te]['frequency'] == 'Annually':
                                        print('here annually')
                                     # if taxes annually and once a year
                                        if eval(response['result'][i]['taxes'])[te]['frequency_of_payment'] == 'Once a year':
                                            print('here once a year')
                                            response['result'][i]['year_expense'] = response['result'][i]['year_expense'] + (int(eval(response['result'][i]
                                                                                                                                      ['taxes'])[te]['amount']))
                                            response['result'][i]['tax_year_expense'] = (
                                                int(eval(response['result'][i]['taxes'])[te]['amount']))
                                            taxes_expenses = taxes_expenses + \
                                                int(eval(response['result'][i]['taxes'])[
                                                    te]['amount'])
                                     # if taxes annually and twice a year
                                        elif eval(response['result'][i]['taxes'])[te]['frequency_of_payment'] == 'Twice a year':
                                            response['result'][i]['year_expense'] = response['result'][i]['year_expense'] + (2*(int(eval(response['result'][i]
                                                                                                                                         ['taxes'])[te]['amount'])))
                                            response['result'][i]['tax_year_expense'] = (
                                                2 * int(eval(response['result'][i]['taxes'])[te]['amount']))
                                            taxes_expenses = taxes_expenses + \
                                                (int(eval(response['result'][i]['taxes'])[
                                                    te]['amount']))
                                    response['result'][i]['tax_expenses'] = taxes_expenses
                        response['result'][i]['insurance_expenses'] = insurance_expenses
                        if response['result'][i]['insurance'] is not None:
                            if len(eval(response['result'][i]['insurance'])) > 0:
                                for te in range(len(eval(response['result'][i]['insurance']))):
                                    response['result'][i]['year_expense'] = response['result'][i]['year_expense'] + (today.month * int(eval(response['result'][i]
                                                                                                                                            ['insurance'])[te]['amount']))
                                    insurance_expenses = insurance_expenses + \
                                        int(eval(response['result'][i]['insurance'])[
                                            te]['amount'])

                        response['result'][i]['insurance_expenses'] = insurance_expenses

                    # print(response)

        return response
