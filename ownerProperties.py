
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from data import connect
from datetime import date, datetime, timedelta
import json
import calendar
import math


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
                        print(property_res)
                        # management status for property
                        if len(property_res['result']) > 0:
                            for pr in range(len(property_res['result'])):
                                print(property_res['result']
                                      [pr]['management_status'])
                                if property_res['result'][pr]['management_status'] == 'ACCEPTED' or property_res['result'][pr]['management_status'] == 'OWNER END EARLY' or property_res['result'][pr]['management_status'] == 'PM END EARLY':
                                    response['result'][i]['management_status'] = property_res['result'][pr]['management_status']
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
                                                    GROUP_CONCAT(lt.linked_tenant_id) as `tenant_id`,
                                                    GROUP_CONCAT(tpi.tenant_first_name) as `tenant_first_name`,
                                                    GROUP_CONCAT(tpi.tenant_last_name) as `tenant_last_name`,
                                                    GROUP_CONCAT(tpi.tenant_email) as `tenant_email`,
                                                    GROUP_CONCAT(tpi.tenant_phone_number) as `tenant_phone_number`
                                                    FROM pm.rentals r 
                                                    LEFT JOIN pm.leaseTenants lt
                                                    ON lt.linked_rental_uid = r.rental_uid
                                                    LEFT JOIN pm.tenantProfileInfo tpi
                                                    ON tpi.tenant_id = lt.linked_tenant_id
                                                    WHERE r.rental_property_id = \'""" + property_id + """\'
                                                    AND (r.rental_status = 'PROCESSING' OR r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED')
                                                    GROUP BY lt.linked_rental_uid""")
                        response['result'][i]['rentalInfo'] = list(
                            rental_res['result'])
                        # rental status for the property
                        if len(rental_res['result']) > 0:
                            response['result'][i]['rental_status'] = rental_res['result'][0]['rental_status']
                        else:
                            response['result'][i]['rental_status'] = ""

                        maintenance_res = db.execute("""SELECT *
                                                        FROM pm.maintenanceRequests mr
                                                        WHERE mr.property_uid = \'""" + property_id + """\'
                                                        """)
                        response['result'][i]['maintenanceRequests'] = list(
                            maintenance_res['result'])

                        # print(maintenance_res['result'])
                        for y in range(len(maintenance_res['result'])):
                            req_id = maintenance_res['result'][y]['maintenance_request_uid']
                            rid = {'linked_request_uid': req_id}  # rid
                            # print(rid)
                            quotes_res = db.select(
                                ''' maintenanceQuotes quote ''', rid)
                            # print(quotes_res)
                            # change the response variable here, don't know why
                            maintenance_res['result'][y]['quotes'] = list(
                                quotes_res['result'])
                            maintenance_res['result'][y]['total_quotes'] = len(
                                quotes_res['result'])

                        rental_revenue = 0
                        extraCharges_revenue = 0
                        maintenance_expenses = 0
                        management_expenses = 0
                        insurance_expenses = 0
                        repairs_expenses = 0
                        mortgage_expenses = 0
                        taxes_expenses = 0
                        rental_year_revenue = 0
                        extraCharges_year_revenue = 0

                        yearCal = today.month - \
                            (datetime.strptime(
                                response['result'][i]['active_date'], '%Y-%m-%d')).month

                        weeks_current_month = len(
                            calendar.monthcalendar(2022, int(today.strftime("%m"))))

                        weeks_active = round((abs(today - datetime.strptime(
                            response['result'][i]['active_date'], '%Y-%m-%d').date()).days)/7, 1)

                        # monthly revenue for the property
                        owner_revenue = db.execute("""SELECT *
                                                        FROM pm.purchases p
                                                        LEFT JOIN
                                                        pm.payments pa
                                                        ON pa.pay_purchase_id = p.purchase_uid
                                                        LEFT JOIN rentals r
                                                        ON r.rental_property_id = p.pur_property_id
                                                        WHERE p.pur_property_id = \'""" + property_id + """\'
                                                        AND ({fn MONTHNAME(p.purchase_date)} = {fn MONTHNAME(now())} AND YEAR(p.purchase_date) = YEAR(now()))
                                                        AND (p.purchase_type= "RENT" OR p.purchase_type= "EXTRA CHARGES" )
                                                        AND (r.rental_status = 'PROCESSING' OR r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED')""")
                        response['result'][i]['owner_revenue'] = list(
                            owner_revenue['result'])

                        if len(owner_revenue['result']) > 0:
                            for ore in range(len(owner_revenue['result'])):
                                print('owner revenue',
                                      owner_revenue['result'][ore])
                                yearCal_revenue = today.month - \
                                    (datetime.strptime(
                                        owner_revenue['result'][ore]['lease_start'], '%Y-%m-%d')).month

                                weeks_current_month = len(calendar.monthcalendar(
                                    2022, int(today.strftime("%m"))))

                                weeks_active_revenue = round((abs(today - datetime.strptime(
                                    owner_revenue['result'][ore]['lease_start'], '%Y-%m-%d').date()).days)/7, 1)
                                if owner_revenue['result'][ore]['purchase_type'] == 'RENT':
                                    if owner_revenue['result'][ore]['purchase_frequency'] == 'Weekly':
                                        rental_year_revenue = rental_year_revenue + \
                                            weeks_active_revenue * \
                                            int(owner_revenue['result']
                                                [ore]['amount_due'])
                                        rental_revenue = rental_revenue + \
                                            weeks_current_month*int(owner_revenue['result']
                                                                    [ore]['amount_due'])
                                    elif owner_revenue['result'][ore]['purchase_frequency'] == 'Biweekly':
                                        rental_year_revenue = rental_year_revenue + \
                                            weeks_active_revenue/2 * \
                                            int(owner_revenue['result']
                                                [ore]['amount_due'])
                                        rental_revenue = rental_revenue + \
                                            weeks_current_month/2 * \
                                            int(owner_revenue['result']
                                                [ore]['amount_due'])
                                    elif owner_revenue['result'][ore]['purchase_frequency'] == 'Monthly':
                                        rental_year_revenue = rental_year_revenue + \
                                            yearCal_revenue * \
                                            int(owner_revenue['result']
                                                [ore]['amount_due'])
                                        rental_revenue = rental_revenue + \
                                            owner_revenue['result'][ore]['amount_due']
                                    elif owner_revenue['result'][ore]['purchase_frequency'] == 'Annually':
                                        rental_year_revenue = rental_year_revenue + \
                                            owner_revenue['result'][ore]['amount_due']
                                        rental_revenue = rental_revenue + \
                                            owner_revenue['result'][ore]['amount_due']
                                    else:
                                        rental_year_revenue = rental_year_revenue + \
                                            owner_revenue['result'][ore]['amount_due']
                                        rental_revenue = rental_revenue + \
                                            owner_revenue['result'][ore]['amount_due']

                                if owner_revenue['result'][ore]['purchase_type'] == 'EXTRA CHARGES':
                                    if owner_revenue['result'][ore]['purchase_frequency'] == 'Weekly':
                                        extraCharges_year_revenue = extraCharges_year_revenue + \
                                            weeks_active_revenue * \
                                            int(owner_revenue['result']
                                                [ore]['amount_due'])
                                        extraCharges_revenue = extraCharges_revenue + \
                                            weeks_current_month*int(owner_revenue['result']
                                                                    [ore]['amount_due'])
                                    elif owner_revenue['result'][ore]['purchase_frequency'] == 'Biweekly':
                                        extraCharges_year_revenue = extraCharges_year_revenue + \
                                            weeks_active_revenue/2 * \
                                            int(owner_revenue['result']
                                                [ore]['amount_due'])
                                        extraCharges_revenue = extraCharges_revenue + \
                                            weeks_current_month/2 * \
                                            int(owner_revenue['result']
                                                [ore]['amount_due'])
                                    elif owner_revenue['result'][ore]['purchase_frequency'] == 'Monthly':
                                        extraCharges_year_revenue = extraCharges_year_revenue + \
                                            yearCal_revenue * \
                                            int(owner_revenue['result']
                                                [ore]['amount_due'])
                                        extraCharges_revenue = extraCharges_revenue + \
                                            owner_revenue['result'][ore]['amount_due']
                                    elif owner_revenue['result'][ore]['purchase_frequency'] == 'Annually':
                                        extraCharges_year_revenue = extraCharges_year_revenue + \
                                            owner_revenue['result'][ore]['amount_due']
                                        extraCharges_revenue = extraCharges_revenue + \
                                            owner_revenue['result'][ore]['amount_due']
                                    else:
                                        extraCharges_year_revenue = extraCharges_year_revenue + \
                                            owner_revenue['result'][ore]['amount_due']
                                        extraCharges_revenue = extraCharges_revenue + \
                                            owner_revenue['result'][ore]['amount_due']

                        response['result'][i]['rental_revenue'] = rental_revenue
                        response['result'][i]['extraCharges_revenue'] = extraCharges_revenue
                        response['result'][i]['rental_year_revenue'] = rental_year_revenue
                        response['result'][i]['extraCharges_year_revenue'] = extraCharges_year_revenue

                        # annual revenue for the property
                        yearly_owner_revenue = db.execute("""SELECT *
                                                        FROM pm.purchases p
                                                        LEFT JOIN
                                                        pm.payments pa
                                                        ON pa.pay_purchase_id = p.purchase_uid
                                                        WHERE p.pur_property_id = \'""" + property_id + """\'
                                                        AND (YEAR(p.purchase_date) = YEAR(now()))
                                                        AND (p.purchase_type = "RENT" OR p.purchase_type = "EXTRA CHARGES")""")

                        response['result'][i]['year_revenue'] = 0
                        if len(yearly_owner_revenue['result']) > 0:
                            for pr in range(len(yearly_owner_revenue['result'])):

                                response['result'][i]['year_revenue'] = response['result'][i]['year_revenue'] + int(
                                    yearly_owner_revenue['result'][pr]['amount_due'])
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
                                                        AND (p.purchase_type <> "RENT" AND p.purchase_type <> "EXTRA CHARGES")""")
                        response['result'][i]['owner_expense'] = list(
                            owner_expense['result'])

                        maintenance_year_expenses = 0
                        management_year_expenses = 0
                        repairs_year_expenses = 0

                        if len(owner_expense['result']) > 0:
                            for ore in range(len(owner_expense['result'])):
                                print('ore', owner_expense['result'][ore])
                                # if maintenance
                                if owner_expense['result'][ore]['purchase_type'] == 'MAINTENANCE':
                                    print('in maintenance')
                                    # if maintenance monthly
                                    if owner_expense['result'][ore]['purchase_frequency'] == 'Monthly':
                                        print('in maintenance monthly')
                                        # if maintenance monthly once a month
                                        if owner_expense['result'][ore]['payment_frequency'] == 'Once a month':
                                            print('in maintenance once a month')
                                            maintenance_year_expenses = maintenance_year_expenses + yearCal * \
                                                (owner_expense['result']
                                                    [ore]['amount_due'])
                                            maintenance_expenses = maintenance_expenses + \
                                                owner_expense['result'][ore]['amount_due']
                                         # if maintenance monthly twice a month
                                        elif owner_expense['result'][ore]['payment_frequency'] == 'Twice a month':
                                            print(
                                                'in maintenance twice a month')
                                            maintenance_year_expenses = maintenance_year_expenses + 2*yearCal * \
                                                (owner_expense['result']
                                                    [ore]['amount_due'])
                                            maintenance_expenses = maintenance_expenses + \
                                                2 * \
                                                (owner_expense['result']
                                                    [ore]['amount_due'])
                                        else:
                                            print('do nothing')
                                     # if maintenance annually
                                    elif owner_expense['result'][ore]['purchase_frequency'] == 'Annually':
                                        print('in maintenance annually')
                                        # if maintenance annually once a year
                                        if owner_expense['result'][ore]['payment_frequency'] == 'Once a year':
                                            maintenance_year_expenses = maintenance_year_expenses + \
                                                (owner_expense['result']
                                                    [ore]['amount_due'])
                                            maintenance_expenses = maintenance_expenses + \
                                                owner_expense['result'][ore]['amount_due']
                                        # if maintenance annually twice a year
                                        elif owner_expense['result'][ore]['payment_frequency'] == 'Twice a year':
                                            maintenance_year_expenses = maintenance_year_expenses + 2 * \
                                                (owner_expense['result']
                                                    [ore]['amount_due'])
                                            maintenance_expenses = maintenance_expenses + \
                                                owner_expense['result'][ore]['amount_due']
                                        else:
                                            print('do nothing')
                                    # if maintenance one-time
                                    else:
                                        maintenance_year_expenses = maintenance_expenses + \
                                            owner_expense['result'][ore]['amount_due']
                                        maintenance_expenses = maintenance_expenses + \
                                            owner_expense['result'][ore]['amount_due']
                                # if management
                                if owner_expense['result'][ore]['purchase_type'] == 'MANAGEMENT':
                                    # if management monthly
                                    if owner_expense['result'][ore]['purchase_frequency'] == 'Monthly':
                                        # if management monthly once a month
                                        if owner_expense['result'][ore]['payment_frequency'] == 'Once a month':
                                            management_year_expenses = yearCal * \
                                                (owner_expense['result']
                                                    [ore]['amount_due'])
                                            management_expenses = management_expenses + \
                                                owner_expense['result'][ore]['amount_due']
                                         # if management monthly twice a month
                                        elif owner_expense['result'][ore]['payment_frequency'] == 'Twice a month':
                                            management_year_expenses = 2*yearCal * \
                                                (owner_expense['result']
                                                    [ore]['amount_due'])
                                            management_expenses = management_expenses + \
                                                2 * \
                                                (owner_expense['result']
                                                    [ore]['amount_due'])
                                        else:
                                            print('do nothing')
                                     # if management annually
                                    elif owner_expense['result'][ore]['purchase_frequency'] == 'Annually':
                                        # if management annually once a year
                                        if owner_expense['result'][ore]['payment_frequency'] == 'Once a year':
                                            management_year_expenses =  \
                                                (owner_expense['result']
                                                    [ore]['amount_due'])
                                            management_expenses = management_expenses + \
                                                owner_expense['result'][ore]['amount_due']
                                        # if management annually twice a year
                                        elif owner_expense['result'][ore]['payment_frequency'] == 'Twice a year':
                                            management_year_expenses = 2 * \
                                                (owner_expense['result']
                                                    [ore]['amount_due'])
                                            management_expenses = management_expenses + \
                                                owner_expense['result'][ore]['amount_due']
                                        else:
                                            print('do nothing')
                                    # if management one-time
                                    else:
                                        management_year_expenses = management_expenses + \
                                            owner_expense['result'][ore]['amount_due']
                                        management_expenses = management_expenses + \
                                            owner_expense['result'][ore]['amount_due']

                                if owner_expense['result'][ore]['purchase_type'] == 'REPAIRS':
                                    # if repairs monthly
                                    if owner_expense['result'][ore]['purchase_frequency'] == 'Monthly':
                                        # if repairs monthly once a month
                                        if owner_expense['result'][ore]['payment_frequency'] == 'Once a month':
                                            repairs_year_expenses = yearCal * \
                                                (owner_expense['result']
                                                    [ore]['amount_due'])
                                            repairs_expenses = repairs_expenses + \
                                                owner_expense['result'][ore]['amount_due']
                                         # if repairs monthly twice a month
                                        elif owner_expense['result'][ore]['payment_frequency'] == 'Twice a month':
                                            repairs_year_expenses = 2*yearCal * \
                                                (owner_expense['result']
                                                    [ore]['amount_due'])
                                            repairs_expenses = repairs_expenses + \
                                                2 * \
                                                (owner_expense['result']
                                                    [ore]['amount_due'])
                                        else:
                                            print('do nothing')
                                     # if repairs annually
                                    elif owner_expense['result'][ore]['purchase_frequency'] == 'Annually':
                                        # if repairs annually once a year
                                        if owner_expense['result'][ore]['payment_frequency'] == 'Once a year':
                                            repairs_year_expenses =  \
                                                (owner_expense['result']
                                                    [ore]['amount_due'])
                                            repairs_expenses = repairs_expenses + \
                                                owner_expense['result'][ore]['amount_due']
                                        # if repairs annually twice a year
                                        elif owner_expense['result'][ore]['payment_frequency'] == 'Twice a year':
                                            repairs_year_expenses = 2 * \
                                                (owner_expense['result']
                                                    [ore]['amount_due'])
                                            repairs_expenses = repairs_expenses + \
                                                owner_expense['result'][ore]['amount_due']
                                        else:
                                            print('do nothing')
                                    # if repairs one-time
                                    else:
                                        repairs_year_expenses = repairs_expenses + \
                                            owner_expense['result'][ore]['amount_due']
                                        repairs_expenses = repairs_expenses + \
                                            owner_expense['result'][ore]['amount_due']

                            response['result'][i]['maintenance_expenses'] = maintenance_expenses
                            response['result'][i]['management_expenses'] = management_expenses
                            response['result'][i]['repairs_expenses'] = repairs_expenses
                            response['result'][i]['maintenance_year_expense'] = maintenance_year_expenses
                            response['result'][i]['management_year_expense'] = management_year_expenses
                            response['result'][i]['repairs_year_expense'] = repairs_year_expenses

                        # annual expense for the property
                        yearly_owner_expense = db.execute("""SELECT *
                                                        FROM pm.purchases p
                                                        LEFT JOIN
                                                        pm.payments pa
                                                        ON pa.pay_purchase_id = p.purchase_uid
                                                        WHERE p.pur_property_id = \'""" + property_id + """\'
                                                        AND (YEAR(p.purchase_date) = YEAR(now()))
                                                        AND (p.purchase_type <> "RENT" AND p.purchase_type <> "EXTRA CHARGES")""")

                        response['result'][i]['year_expense'] = 0
                        response['result'][i]['mortgage_year_expense'] = 0
                        response['result'][i]['tax_year_expense'] = 0
                        response['result'][i]['insurance_year_expense'] = 0
                        if len(yearly_owner_expense['result']) > 0:
                            for pr in range(len(yearly_owner_expense['result'])):

                                response['result'][i]['year_expense'] = response['result'][i]['year_expense'] + int(
                                    yearly_owner_expense['result'][pr]['amount_due'])
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
                                    response['result'][i]['year_expense'] = response['result'][i]['year_expense'] + (weeks_active*(int(json.loads(response['result'][i]['mortgages'])[
                                        'amount'])))
                                    response['result'][i]['mortgage_year_expense'] = weeks_active*(int(json.loads(response['result'][i]['mortgages'])[
                                        'amount']))
                                    mortgage_expenses = mortgage_expenses + \
                                        weeks_current_month*(int(json.loads(
                                            response['result'][i]['mortgages'])['amount']))
                             # if mortgage weekly and every other week
                                elif json.loads(response['result'][i]['mortgages'])['frequency_of_payment'] == 'Every other week':
                                    response['result'][i]['year_expense'] = response['result'][i]['year_expense'] + ((weeks_active/2)*(int(json.loads(response['result'][i]['mortgages'])[
                                        'amount'])))
                                    response['result'][i]['mortgage_year_expense'] = (weeks_active/2)*(int(json.loads(response['result'][i]['mortgages'])[
                                        'amount']))
                                    mortgage_expenses = mortgage_expenses + (weeks_current_month/2) * \
                                        (int(json.loads(
                                            response['result'][i]['mortgages'])['amount']))
                        # print(mortgage_expenses)
                        response['result'][i]['mortgage_expenses'] = mortgage_expenses

                        # monthly expense for the property to include taxes
                        if response['result'][i]['taxes'] is not None:
                            if len(eval(response['result'][i]['taxes'])) > 0:
                                for te in range(len(eval(response['result'][i]['taxes']))):

                                    # if tax monthly
                                    if eval(response['result'][i]['taxes'])[te]['frequency'] == 'Monthly':

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

                                     # if taxes annually and once a year
                                        if eval(response['result'][i]['taxes'])[te]['frequency_of_payment'] == 'Once a year':

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
                        # response['result'][i]['insurance_expenses'] = insurance_expenses
                        if response['result'][i]['insurance'] is not None:
                            if len(eval(response['result'][i]['insurance'])) > 0:
                                for te in range(len(eval(response['result'][i]['insurance']))):

                                    # if insurance monthly
                                    if eval(response['result'][i]['insurance'])[te]['frequency'] == 'Monthly':

                                     # if insurance monthly and once a month
                                        if eval(response['result'][i]['insurance'])[te]['frequency_of_payment'] == 'Once a month':
                                            response['result'][i]['year_expense'] = response['result'][i]['year_expense'] + (yearCal * int(eval(response['result'][i]
                                                                                                                                                ['insurance'])[te]['amount']))
                                            response['result'][i]['insurance_year_expense'] = (
                                                yearCal * int(eval(response['result'][i]['insurance'])[te]['amount']))
                                            insurance_expenses = insurance_expenses + \
                                                int(eval(response['result'][i]['insurance'])[
                                                    te]['amount'])
                                    # if insurance monthly and once a month
                                        elif eval(response['result'][i]['insurance'])[te]['frequency_of_payment'] == 'Twice a month':
                                            response['result'][i]['year_expense'] = response['result'][i]['year_expense'] + (2*yearCal * int(eval(response['result'][i]
                                                                                                                                                  ['insurance'])[te]['amount']))
                                            response['result'][i]['insurance_year_expense'] = (
                                                2*yearCal * int(eval(response['result'][i]['insurance'])[te]['amount']))
                                            insurance_expenses = insurance_expenses + \
                                                2*(int(eval(response['result'][i]['insurance'])[
                                                    te]['amount']))
                                     # if insurance Annually
                                    elif eval(response['result'][i]['insurance'])[te]['frequency'] == 'Annually':

                                     # if insurance annually and once a year
                                        if eval(response['result'][i]['insurance'])[te]['frequency_of_payment'] == 'Once a year':

                                            response['result'][i]['year_expense'] = response['result'][i]['year_expense'] + (int(eval(response['result'][i]
                                                                                                                                      ['insurance'])[te]['amount']))
                                            response['result'][i]['insurance_year_expense'] = (
                                                int(eval(response['result'][i]['insurance'])[te]['amount']))
                                            insurance_expenses = insurance_expenses + \
                                                int(eval(response['result'][i]['insurance'])[
                                                    te]['amount'])
                                     # if insurance annually and twice a year
                                        elif eval(response['result'][i]['insurance'])[te]['frequency_of_payment'] == 'Twice a year':
                                            response['result'][i]['year_expense'] = response['result'][i]['year_expense'] + (2*(int(eval(response['result'][i]
                                                                                                                                         ['insurance'])[te]['amount'])))
                                            response['result'][i]['insurance_year_expense'] = (
                                                2 * int(eval(response['result'][i]['insurance'])[te]['amount']))
                                            insurance_expenses = insurance_expenses + \
                                                (int(eval(response['result'][i]['insurance'])[
                                                    te]['amount']))
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
                                if property_res['result'][pr]['management_status'] == 'ACCEPTED' or property_res['result'][pr]['management_status'] == 'OWNER END EARLY' or property_res['result'][pr]['management_status'] == 'PM END EARLY':
                                    response['result'][i]['management_status'] = property_res['result'][pr]['management_status']
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
                                                    GROUP_CONCAT(lt.linked_tenant_id) as `tenant_id`,
                                                    GROUP_CONCAT(tpi.tenant_first_name) as `tenant_first_name`,
                                                    GROUP_CONCAT(tpi.tenant_last_name) as `tenant_last_name`,
                                                    GROUP_CONCAT(tpi.tenant_email) as `tenant_email`,
                                                    GROUP_CONCAT(tpi.tenant_phone_number) as `tenant_phone_number`
                                                    FROM pm.rentals r 
                                                    LEFT JOIN pm.leaseTenants lt
                                                    ON lt.linked_rental_uid = r.rental_uid
                                                    LEFT JOIN pm.tenantProfileInfo tpi
                                                    ON tpi.tenant_id = lt.linked_tenant_id
                                                    WHERE r.rental_property_id = \'""" + property_id + """\'
                                                    AND (r.rental_status = 'PROCESSING' OR r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED')
                                                    GROUP BY lt.linked_rental_uid""")
                        print(rental_res['result'])
                        response['result'][i]['rentalInfo'] = list(
                            rental_res['result'])
                        if len(rental_res['result']) > 0:
                            response['result'][i]['rental_status'] = rental_res['result'][0]['rental_status']
                        else:
                            response['result'][i]['rental_status'] = ""

                        maintenance_res = db.execute("""SELECT *
                                                        FROM pm.maintenanceRequests mr
                                                        WHERE mr.property_uid = \'""" + property_id + """\'
                                                        """)
                        response['result'][i]['maintenanceRequests'] = list(
                            maintenance_res['result'])

                        # print(maintenance_res['result'])
                        for y in range(len(maintenance_res['result'])):
                            req_id = maintenance_res['result'][y]['maintenance_request_uid']
                            rid = {'linked_request_uid': req_id}  # rid
                            # print(rid)
                            quotes_res = db.select(
                                ''' maintenanceQuotes quote ''', rid)
                            # print(quotes_res)
                            # change the response variable here, don't know why
                            maintenance_res['result'][y]['quotes'] = list(
                                quotes_res['result'])
                            maintenance_res['result'][y]['total_quotes'] = len(
                                quotes_res['result'])

                        rental_revenue = 0
                        extraCharges_revenue = 0
                        maintenance_expenses = 0
                        management_expenses = 0
                        insurance_expenses = 0
                        repairs_expenses = 0
                        mortgage_expenses = 0
                        taxes_expenses = 0
                        rental_year_revenue = 0
                        extraCharges_year_revenue = 0

                        yearCal = today.month - \
                            (datetime.strptime(
                                response['result'][i]['active_date'], '%Y-%m-%d')).month

                        weeks_current_month = len(
                            calendar.monthcalendar(2022, int(today.strftime("%m"))))

                        weeks_active = round((abs(today - datetime.strptime(
                            response['result'][i]['active_date'], '%Y-%m-%d').date()).days)/7, 1)

                        # monthly bills for the property
                        owner_bills = db.execute("""SELECT *
                                                        FROM pm.purchases p
                                                        LEFT JOIN
                                                        pm.payments pa
                                                        ON pa.pay_purchase_id = p.purchase_uid
                                                        WHERE p.pur_property_id = \'""" + property_id + """\'
                                                        AND p.payer LIKE '%%\"""" + owner_id + """\"%%'
                                                        AND p.purchase_status = 'UNPAID'
                                                        AND ({fn MONTHNAME(p.next_payment)} = {fn MONTHNAME(now())} AND YEAR(p.next_payment) = YEAR(now()))
                                                        AND (p.purchase_type <> "RENT" AND p.purchase_type <> "EXTRA CHARGES" )""")

                        response['result'][i]['owner_bills'] = list(
                            owner_bills['result'])

                        # monthly revenue for the property
                        owner_revenue = db.execute("""SELECT *
                                                        FROM pm.purchases p
                                                        LEFT JOIN
                                                        pm.payments pa
                                                        ON pa.pay_purchase_id = p.purchase_uid
                                                        WHERE p.pur_property_id = \'""" + property_id + """\'
                                                        AND ({fn MONTHNAME(p.purchase_date)} = {fn MONTHNAME(now())} AND YEAR(p.purchase_date) = YEAR(now()))
                                                        AND (p.purchase_type= "RENT" OR p.purchase_type= "EXTRA CHARGES")""")
                        response['result'][i]['owner_revenue'] = list(
                            owner_revenue['result'])
                        print(len(owner_revenue['result']))

                        if len(owner_revenue['result']) > 0:
                            for ore in range(len(owner_revenue['result'])):
                                print('ore', owner_revenue['result'][ore])
                                if owner_revenue['result'][ore]['purchase_type'] == 'RENT':
                                    if owner_revenue['result'][ore]['purchase_frequency'] == 'Weekly':
                                        rental_year_revenue = rental_year_revenue + \
                                            weeks_active * \
                                            int(owner_revenue['result']
                                                [ore]['amount_due'])
                                        rental_revenue = rental_revenue + \
                                            weeks_current_month*int(owner_revenue['result']
                                                                    [ore]['amount_due'])
                                    elif owner_revenue['result'][ore]['purchase_frequency'] == 'Biweekly':
                                        rental_year_revenue = rental_year_revenue + \
                                            weeks_active/2 * \
                                            int(owner_revenue['result']
                                                [ore]['amount_due'])
                                        rental_revenue = rental_revenue + \
                                            weeks_current_month/2 * \
                                            int(owner_revenue['result']
                                                [ore]['amount_due'])
                                    elif owner_revenue['result'][ore]['purchase_frequency'] == 'Monthly':
                                        rental_year_revenue = rental_year_revenue + \
                                            yearCal * \
                                            int(owner_revenue['result']
                                                [ore]['amount_due'])
                                        rental_revenue = rental_revenue + \
                                            owner_revenue['result'][ore]['amount_due']
                                    elif owner_revenue['result'][ore]['purchase_frequency'] == 'Annually':
                                        rental_year_revenue = rental_year_revenue + \
                                            owner_revenue['result'][ore]['amount_due']
                                        rental_revenue = rental_revenue + \
                                            owner_revenue['result'][ore]['amount_due']
                                    else:
                                        rental_year_revenue = rental_year_revenue + \
                                            owner_revenue['result'][ore]['amount_due']
                                        rental_revenue = rental_revenue + \
                                            owner_revenue['result'][ore]['amount_due']

                                if owner_revenue['result'][ore]['purchase_type'] == 'EXTRA CHARGES':
                                    if owner_revenue['result'][ore]['purchase_frequency'] == 'Weekly':
                                        extraCharges_year_revenue = extraCharges_year_revenue + \
                                            weeks_active * \
                                            int(owner_revenue['result']
                                                [ore]['amount_due'])
                                        extraCharges_revenue = extraCharges_revenue + \
                                            weeks_current_month*int(owner_revenue['result']
                                                                    [ore]['amount_due'])
                                    elif owner_revenue['result'][ore]['purchase_frequency'] == 'Biweekly':
                                        extraCharges_year_revenue = extraCharges_year_revenue + \
                                            weeks_active/2 * \
                                            int(owner_revenue['result']
                                                [ore]['amount_due'])
                                        extraCharges_revenue = extraCharges_revenue + \
                                            weeks_current_month/2 * \
                                            int(owner_revenue['result']
                                                [ore]['amount_due'])
                                    elif owner_revenue['result'][ore]['purchase_frequency'] == 'Monthly':
                                        extraCharges_year_revenue = extraCharges_year_revenue + \
                                            yearCal * \
                                            int(owner_revenue['result']
                                                [ore]['amount_due'])
                                        extraCharges_revenue = extraCharges_revenue + \
                                            owner_revenue['result'][ore]['amount_due']
                                    elif owner_revenue['result'][ore]['purchase_frequency'] == 'Annually':
                                        extraCharges_year_revenue = extraCharges_year_revenue + \
                                            owner_revenue['result'][ore]['amount_due']
                                        extraCharges_revenue = extraCharges_revenue + \
                                            owner_revenue['result'][ore]['amount_due']
                                    else:
                                        extraCharges_year_revenue = extraCharges_year_revenue + \
                                            owner_revenue['result'][ore]['amount_due']
                                        extraCharges_revenue = extraCharges_revenue + \
                                            owner_revenue['result'][ore]['amount_due']

                        response['result'][i]['rental_revenue'] = rental_revenue
                        response['result'][i]['extraCharges_revenue'] = extraCharges_revenue
                        response['result'][i]['rental_year_revenue'] = rental_year_revenue
                        response['result'][i]['extraCharges_year_revenue'] = extraCharges_year_revenue

                        # annual revenue for the property
                        yearly_owner_revenue = db.execute("""SELECT *
                                                        FROM pm.purchases p
                                                        LEFT JOIN
                                                        pm.payments pa
                                                        ON pa.pay_purchase_id = p.purchase_uid
                                                        WHERE p.pur_property_id = \'""" + property_id + """\'
                                                        AND (YEAR(p.purchase_date) = YEAR(now()))
                                                        AND (p.purchase_type = "RENT" OR p.purchase_type = "EXTRA CHARGES")""")

                        response['result'][i]['year_revenue'] = 0
                        if len(yearly_owner_revenue['result']) > 0:
                            for pr in range(len(yearly_owner_revenue['result'])):

                                response['result'][i]['year_revenue'] = response['result'][i]['year_revenue'] + int(
                                    yearly_owner_revenue['result'][pr]['amount_due'])
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
                                                        AND (p.purchase_type <> "RENT" AND p.purchase_type <> "EXTRA CHARGES")""")
                        response['result'][i]['owner_expense'] = list(
                            owner_expense['result'])
                        maintenance_year_expenses = 0
                        management_year_expenses = 0
                        repairs_year_expenses = 0

                        if len(owner_expense['result']) > 0:
                            for ore in range(len(owner_expense['result'])):
                                print('ore', owner_expense['result'][ore])
                                # if maintenance
                                if owner_expense['result'][ore]['purchase_type'] == 'MAINTENANCE':
                                    print('in maintenance')
                                    # if maintenance monthly
                                    if owner_expense['result'][ore]['purchase_frequency'] == 'Monthly':
                                        print('in maintenance monthly')
                                        # if maintenance monthly once a month
                                        if owner_expense['result'][ore]['payment_frequency'] == 'Once a month':
                                            print('in maintenance once a month')
                                            maintenance_year_expenses = maintenance_year_expenses + yearCal * \
                                                (owner_expense['result']
                                                    [ore]['amount_due'])
                                            maintenance_expenses = maintenance_expenses + \
                                                owner_expense['result'][ore]['amount_due']
                                         # if maintenance monthly twice a month
                                        elif owner_expense['result'][ore]['payment_frequency'] == 'Twice a month':
                                            print(
                                                'in maintenance twice a month')
                                            maintenance_year_expenses = maintenance_year_expenses + 2*yearCal * \
                                                (owner_expense['result']
                                                    [ore]['amount_due'])
                                            maintenance_expenses = maintenance_expenses + \
                                                2 * \
                                                (owner_expense['result']
                                                    [ore]['amount_due'])
                                        else:
                                            print('do nothing')
                                     # if maintenance annually
                                    elif owner_expense['result'][ore]['purchase_frequency'] == 'Annually':
                                        print('in maintenance annually')
                                        # if maintenance annually once a year
                                        if owner_expense['result'][ore]['payment_frequency'] == 'Once a year':
                                            maintenance_year_expenses = maintenance_year_expenses + \
                                                (owner_expense['result']
                                                    [ore]['amount_due'])
                                            maintenance_expenses = maintenance_expenses + \
                                                owner_expense['result'][ore]['amount_due']
                                        # if maintenance annually twice a year
                                        elif owner_expense['result'][ore]['payment_frequency'] == 'Twice a year':
                                            maintenance_year_expenses = maintenance_year_expenses + 2 * \
                                                (owner_expense['result']
                                                    [ore]['amount_due'])
                                            maintenance_expenses = maintenance_expenses + \
                                                owner_expense['result'][ore]['amount_due']
                                        else:
                                            print('do nothing')
                                    # if maintenance one-time
                                    else:
                                        maintenance_year_expenses = maintenance_expenses + \
                                            owner_expense['result'][ore]['amount_due']
                                        maintenance_expenses = maintenance_expenses + \
                                            owner_expense['result'][ore]['amount_due']
                                # if management
                                if owner_expense['result'][ore]['purchase_type'] == 'MANAGEMENT':
                                    # if management monthly
                                    if owner_expense['result'][ore]['purchase_frequency'] == 'Monthly':
                                        # if management monthly once a month
                                        if owner_expense['result'][ore]['payment_frequency'] == 'Once a month':
                                            management_year_expenses = yearCal * \
                                                (owner_expense['result']
                                                    [ore]['amount_due'])
                                            management_expenses = management_expenses + \
                                                owner_expense['result'][ore]['amount_due']
                                         # if management monthly twice a month
                                        elif owner_expense['result'][ore]['payment_frequency'] == 'Twice a month':
                                            management_year_expenses = 2*yearCal * \
                                                (owner_expense['result']
                                                    [ore]['amount_due'])
                                            management_expenses = management_expenses + \
                                                2 * \
                                                (owner_expense['result']
                                                    [ore]['amount_due'])
                                        else:
                                            print('do nothing')
                                     # if management annually
                                    elif owner_expense['result'][ore]['purchase_frequency'] == 'Annually':
                                        # if management annually once a year
                                        if owner_expense['result'][ore]['payment_frequency'] == 'Once a year':
                                            management_year_expenses =  \
                                                (owner_expense['result']
                                                    [ore]['amount_due'])
                                            management_expenses = management_expenses + \
                                                owner_expense['result'][ore]['amount_due']
                                        # if management annually twice a year
                                        elif owner_expense['result'][ore]['payment_frequency'] == 'Twice a year':
                                            management_year_expenses = 2 * \
                                                (owner_expense['result']
                                                    [ore]['amount_due'])
                                            management_expenses = management_expenses + \
                                                owner_expense['result'][ore]['amount_due']
                                        else:
                                            print('do nothing')
                                    # if management one-time
                                    else:
                                        management_year_expenses = management_expenses + \
                                            owner_expense['result'][ore]['amount_due']
                                        management_expenses = management_expenses + \
                                            owner_expense['result'][ore]['amount_due']

                                if owner_expense['result'][ore]['purchase_type'] == 'REPAIRS':
                                    # if repairs monthly
                                    if owner_expense['result'][ore]['purchase_frequency'] == 'Monthly':
                                        # if repairs monthly once a month
                                        if owner_expense['result'][ore]['payment_frequency'] == 'Once a month':
                                            repairs_year_expenses = yearCal * \
                                                (owner_expense['result']
                                                    [ore]['amount_due'])
                                            repairs_expenses = repairs_expenses + \
                                                owner_expense['result'][ore]['amount_due']
                                         # if repairs monthly twice a month
                                        elif owner_expense['result'][ore]['payment_frequency'] == 'Twice a month':
                                            repairs_year_expenses = 2*yearCal * \
                                                (owner_expense['result']
                                                    [ore]['amount_due'])
                                            repairs_expenses = repairs_expenses + \
                                                2 * \
                                                (owner_expense['result']
                                                    [ore]['amount_due'])
                                        else:
                                            print('do nothing')
                                     # if repairs annually
                                    elif owner_expense['result'][ore]['purchase_frequency'] == 'Annually':
                                        # if repairs annually once a year
                                        if owner_expense['result'][ore]['payment_frequency'] == 'Once a year':
                                            repairs_year_expenses =  \
                                                (owner_expense['result']
                                                    [ore]['amount_due'])
                                            repairs_expenses = repairs_expenses + \
                                                owner_expense['result'][ore]['amount_due']
                                        # if repairs annually twice a year
                                        elif owner_expense['result'][ore]['payment_frequency'] == 'Twice a year':
                                            repairs_year_expenses = 2 * \
                                                (owner_expense['result']
                                                    [ore]['amount_due'])
                                            repairs_expenses = repairs_expenses + \
                                                owner_expense['result'][ore]['amount_due']
                                        else:
                                            print('do nothing')
                                    # if repairs one-time
                                    else:
                                        repairs_year_expenses = repairs_expenses + \
                                            owner_expense['result'][ore]['amount_due']
                                        repairs_expenses = repairs_expenses + \
                                            owner_expense['result'][ore]['amount_due']

                            response['result'][i]['maintenance_expenses'] = maintenance_expenses
                            response['result'][i]['management_expenses'] = management_expenses
                            response['result'][i]['repairs_expenses'] = repairs_expenses
                            response['result'][i]['maintenance_year_expense'] = maintenance_year_expenses
                            response['result'][i]['management_year_expense'] = management_year_expenses
                            response['result'][i]['repairs_year_expense'] = repairs_year_expenses

                        # annual expense for the property
                        yearly_owner_expense = db.execute("""SELECT *
                                                        FROM pm.purchases p
                                                        LEFT JOIN
                                                        pm.payments pa
                                                        ON pa.pay_purchase_id = p.purchase_uid
                                                        WHERE p.pur_property_id = \'""" + property_id + """\'
                                                        AND (YEAR(p.purchase_date) = YEAR(now()))
                                                        AND (p.purchase_type <> "RENT" AND p.purchase_type <> "EXTRA CHARGES")""")

                        response['result'][i]['year_expense'] = 0
                        response['result'][i]['mortgage_year_expense'] = 0
                        response['result'][i]['tax_year_expense'] = 0
                        # yearCal = today.month - \
                        #     (datetime.strptime(
                        #         response['result'][i]['active_date'], '%Y-%m-%d')).month
                        if len(yearly_owner_expense['result']) > 0:
                            for pr in range(len(yearly_owner_expense['result'])):

                                response['result'][i]['year_expense'] = response['result'][i]['year_expense'] + int(
                                    yearly_owner_expense['result'][pr]['amount_due'])
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
                                    response['result'][i]['year_expense'] = response['result'][i]['year_expense'] + (weeks_active * (int(json.loads(response['result'][i]['mortgages'])[
                                        'amount'])))
                                    response['result'][i]['mortgage_year_expense'] = weeks_active*(int(json.loads(response['result'][i]['mortgages'])[
                                        'amount']))
                                    mortgage_expenses = mortgage_expenses + \
                                        weeks_current_month*(int(json.loads(
                                            response['result'][i]['mortgages'])['amount']))
                             # if mortgage weekly and every other week
                                elif json.loads(response['result'][i]['mortgages'])['frequency_of_payment'] == 'Every other week':
                                    response['result'][i]['year_expense'] = response['result'][i]['year_expense'] + (weeks_active / 2*(int(json.loads(response['result'][i]['mortgages'])[
                                        'amount'])))
                                    response['result'][i]['mortgage_year_expense'] = weeks_active / 2*(int(json.loads(response['result'][i]['mortgages'])[
                                        'amount']))
                                    mortgage_expenses = mortgage_expenses + (weeks_current_month/2) * \
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

                                     # if taxes annually and once a year
                                        if eval(response['result'][i]['taxes'])[te]['frequency_of_payment'] == 'Once a year':

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
                        # response['result'][i]['insurance_expenses'] = insurance_expenses
                        if response['result'][i]['insurance'] is not None:
                            if len(eval(response['result'][i]['insurance'])) > 0:
                                for te in range(len(eval(response['result'][i]['insurance']))):
                                    print('here for', eval(
                                        response['result'][i]['insurance'])[te]['frequency'])
                                    # if insurance monthly
                                    if eval(response['result'][i]['insurance'])[te]['frequency'] == 'Monthly':

                                     # if insurance monthly and once a month
                                        if eval(response['result'][i]['insurance'])[te]['frequency_of_payment'] == 'Once a month':
                                            response['result'][i]['year_expense'] = response['result'][i]['year_expense'] + (yearCal * int(eval(response['result'][i]
                                                                                                                                                ['insurance'])[te]['amount']))
                                            response['result'][i]['insurance_year_expense'] = (
                                                yearCal * int(eval(response['result'][i]['insurance'])[te]['amount']))
                                            insurance_expenses = insurance_expenses + \
                                                int(eval(response['result'][i]['insurance'])[
                                                    te]['amount'])
                                    # if insurance monthly and once a month
                                        elif eval(response['result'][i]['insurance'])[te]['frequency_of_payment'] == 'Twice a month':
                                            response['result'][i]['year_expense'] = response['result'][i]['year_expense'] + (2*yearCal * int(eval(response['result'][i]
                                                                                                                                                  ['insurance'])[te]['amount']))
                                            response['result'][i]['insurance_year_expense'] = (
                                                2*yearCal * int(eval(response['result'][i]['insurance'])[te]['amount']))
                                            insurance_expenses = insurance_expenses + \
                                                2*(int(eval(response['result'][i]['insurance'])[
                                                    te]['amount']))
                                     # if insurance Annually
                                    elif eval(response['result'][i]['insurance'])[te]['frequency'] == 'Annually':

                                     # if insurance annually and once a year
                                        if eval(response['result'][i]['insurance'])[te]['frequency_of_payment'] == 'Once a year':

                                            response['result'][i]['year_expense'] = response['result'][i]['year_expense'] + (int(eval(response['result'][i]
                                                                                                                                      ['insurance'])[te]['amount']))
                                            response['result'][i]['insurance_year_expense'] = (
                                                int(eval(response['result'][i]['insurance'])[te]['amount']))
                                            insurance_expenses = insurance_expenses + \
                                                int(eval(response['result'][i]['insurance'])[
                                                    te]['amount'])
                                     # if insurance annually and twice a year
                                        elif eval(response['result'][i]['insurance'])[te]['frequency_of_payment'] == 'Twice a year':
                                            response['result'][i]['year_expense'] = response['result'][i]['year_expense'] + (2*(int(eval(response['result'][i]
                                                                                                                                         ['insurance'])[te]['amount'])))
                                            response['result'][i]['insurance_year_expense'] = (
                                                2 * int(eval(response['result'][i]['insurance'])[te]['amount']))
                                            insurance_expenses = insurance_expenses + \
                                                (int(eval(response['result'][i]['insurance'])[
                                                    te]['amount']))
                            response['result'][i]['insurance_expenses'] = insurance_expenses

                    # print(response)

        return response


class OwnerPropertyBills(Resource):
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
                    response = db.execute("""SELECT prop.property_uid, prop.address, prop.unit, prop.city, prop.state, prop.zip, p.*, pa.*
                                            FROM pm.properties prop
                                            LEFT JOIN
                                            pm.purchases p
                                            ON p.pur_property_id = prop.property_uid
                                            LEFT JOIN
                                            pm.payments pa
                                            ON pa.pay_purchase_id = p.purchase_uid
                                            WHERE prop.owner_id = \'""" + filterValue + """\'
                                            AND p.payer LIKE '%%\"""" + filterValue + """\"%%'
                                            AND p.purchase_status = 'UNPAID'
                                            AND ({fn MONTHNAME(p.next_payment)} = {fn MONTHNAME(now())} AND YEAR(p.next_payment) = YEAR(now()))
                                            AND (p.purchase_type <> "RENT" AND p.purchase_type <> "EXTRA CHARGES" )""")

        return response


class OwnerDocuments(Resource):
    def get(self):
        response = {'message': 'Successfully committed SQL query',
                    'code': 200,
                    'result': []}
        filters = ['owner_id']
        where = {}

        with connect() as db:
            for filter in filters:
                filterValue = request.args.get(filter)
                if filterValue is not None:
                    where[filter] = filterValue
                    today = date.today()
                    # list of all active leases for the owner
                    lease_docs = db.execute("""SELECT *
                                            FROM pm.properties prop
                                            LEFT JOIN
                                            pm.rentals r
                                            ON r.rental_property_id = prop.property_uid
                                            WHERE prop.owner_id = \'""" + filterValue + """\'
                                            AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'PROCESSING' OR r.rental_status='TENTANT APPROVED')""")
                    active_lease_docs = []
                    if len(lease_docs['result']) > 0:
                        print('active lease docs')
                        for doc in lease_docs['result']:
                            if len(json.loads(doc['documents'])) > 0:
                                active_lease_docs.append(
                                    json.loads(doc['documents']))
                    print(active_lease_docs)

                    # list of all expired leases for the owner
                    past_lease_docs = db.execute("""SELECT *
                                            FROM pm.properties prop
                                            LEFT JOIN
                                            pm.rentals r
                                            ON r.rental_property_id = prop.property_uid
                                            WHERE prop.owner_id = \'""" + filterValue + """\'
                                            AND (r.rental_status = 'EXPIRED' OR r.rental_status = 'TERMINATED')""")

                    expired_lease_docs = []
                    if len(past_lease_docs['result']) > 0:
                        print('expired lease docs')
                        for doc in past_lease_docs['result']:
                            if len(json.loads(doc['documents'])) > 0:
                                expired_lease_docs.append(
                                    json.loads(doc['documents']))
                    print(expired_lease_docs)

                    # list of all active pm contracts for the owner
                    manager_docs = db.execute("""SELECT *
                                            FROM pm.properties prop
                                            LEFT JOIN
                                            pm.contracts c
                                            ON c.property_uid = prop.property_uid
                                            LEFT JOIN
                                            pm.propertyManager pm
                                            ON pm.linked_property_id = prop.property_uid
                                            WHERE prop.owner_id = \'""" + filterValue + """\'
                                            AND pm.management_status= 'ACCEPTED'
                                            AND c.business_uid = pm.linked_business_id""")

                    active_manager_docs = []
                    if len(manager_docs['result']) > 0:
                        print('active manager docs')
                        for doc in manager_docs['result']:
                            if len(json.loads(doc['documents'])) > 0:
                                active_manager_docs.append(
                                    json.loads(doc['documents']))
                    print(active_manager_docs)

                    # list of all active pm contracts for the owner
                    past_manager_docs = db.execute("""SELECT *
                                            FROM pm.properties prop
                                            LEFT JOIN
                                            pm.contracts c
                                            ON c.property_uid = prop.property_uid
                                            LEFT JOIN
                                            pm.propertyManager pm
                                            ON pm.linked_property_id = prop.property_uid
                                            WHERE prop.owner_id = \'""" + filterValue + """\'
                                            AND pm.management_status <> 'ACCEPTED'
                                            AND c.business_uid = pm.linked_business_id""")
                    expired_manager_docs = []
                    if len(past_manager_docs['result']) > 0:
                        print('past manager docs')
                        for doc in past_manager_docs['result']:
                            if len(json.loads(doc['documents'])) > 0:
                                expired_manager_docs.append(
                                    json.loads(doc['documents']))
                    print(expired_manager_docs)

                    response['result'] = [{
                        'active_lease_docs': list(active_lease_docs),
                        'past_lease_docs': list(expired_lease_docs),
                        'active_manager_docs': list(active_manager_docs),
                        'past_manager_docs': list(expired_manager_docs)
                    }]

        return response
