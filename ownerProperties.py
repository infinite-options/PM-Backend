
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
                                if property_res['result'][pr]['management_status'] == 'ACCEPTED' or property_res['result'][pr]['management_status'] == 'OWNER END EARLY' or property_res['result'][pr]['management_status'] == 'PM END EARLY' or property_res['result'][pr]['management_status'] == 'END EARLY':
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
                        utility_revenue = 0

                        utility_expenses = 0
                        maintenance_expenses = 0
                        management_expenses = 0
                        repairs_expenses = 0

                        rental_expected_revenue = 0
                        extraCharges_expected_revenue = 0
                        utility_expected_revenue = 0

                        maintenance_expected_expenses = 0
                        management_expected_expenses = 0
                        repairs_expected_expenses = 0
                        utility_expected_expenses = 0
                        mortgage_expenses = 0
                        insurance_expenses = 0
                        taxes_expenses = 0
                        rental_year_revenue = 0
                        extraCharges_year_revenue = 0

                        rental_year_expected_revenue = 0
                        extraCharges_year_expected_revenue = 0

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
                                                        ON r.rental_property_id LIKE '%""" + property_id + """%'
                                                        WHERE p.pur_property_id LIKE '%""" + property_id + """%'
                                                        AND ({fn MONTHNAME(p.next_payment)} = {fn MONTHNAME(now())} AND YEAR(p.next_payment) = YEAR(now()))
                                                        AND (p.purchase_type= "RENT" OR p.purchase_type= "EXTRA CHARGES")
                                                        AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED')
                                                        AND p.purchase_status = 'PAID' """)
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
                                                [ore]['amount_paid'])
                                        rental_revenue = rental_revenue + \
                                            weeks_current_month*int(owner_revenue['result']
                                                                    [ore]['amount_paid'])
                                    elif owner_revenue['result'][ore]['purchase_frequency'] == 'Biweekly':
                                        rental_year_revenue = rental_year_revenue + \
                                            weeks_active_revenue/2 * \
                                            int(owner_revenue['result']
                                                [ore]['amount_paid'])
                                        rental_revenue = rental_revenue + \
                                            weeks_current_month/2 * \
                                            int(owner_revenue['result']
                                                [ore]['amount_paid'])
                                    elif owner_revenue['result'][ore]['purchase_frequency'] == 'Monthly':
                                        print('rental_year_revenue',
                                              rental_year_revenue, rental_revenue)
                                        rental_year_revenue = rental_year_revenue + \
                                            yearCal_revenue * \
                                            int(owner_revenue['result']
                                                [ore]['amount_paid'])
                                        rental_revenue = rental_revenue + \
                                            owner_revenue['result'][ore]['amount_paid']
                                        print('rental_year_revenue', yearCal_revenue,
                                              rental_year_revenue, rental_revenue)
                                    elif owner_revenue['result'][ore]['purchase_frequency'] == 'Annually':
                                        rental_year_revenue = rental_year_revenue + \
                                            owner_revenue['result'][ore]['amount_paid']
                                        rental_revenue = rental_revenue + \
                                            owner_revenue['result'][ore]['amount_paid']
                                    else:
                                        rental_year_revenue = rental_year_revenue + \
                                            owner_revenue['result'][ore]['amount_paid']
                                        rental_revenue = rental_revenue + \
                                            owner_revenue['result'][ore]['amount_paid']

                                if owner_revenue['result'][ore]['purchase_type'] == 'EXTRA CHARGES':
                                    if owner_revenue['result'][ore]['purchase_frequency'] == 'Weekly':
                                        extraCharges_year_revenue = extraCharges_year_revenue + \
                                            weeks_active_revenue * \
                                            int(owner_revenue['result']
                                                [ore]['amount_paid'])
                                        extraCharges_revenue = extraCharges_revenue + \
                                            weeks_current_month*int(owner_revenue['result']
                                                                    [ore]['amount_paid'])
                                    elif owner_revenue['result'][ore]['purchase_frequency'] == 'Biweekly':
                                        extraCharges_year_revenue = extraCharges_year_revenue + \
                                            weeks_active_revenue/2 * \
                                            int(owner_revenue['result']
                                                [ore]['amount_paid'])
                                        extraCharges_revenue = extraCharges_revenue + \
                                            weeks_current_month/2 * \
                                            int(owner_revenue['result']
                                                [ore]['amount_paid'])
                                    elif owner_revenue['result'][ore]['purchase_frequency'] == 'Monthly':
                                        extraCharges_year_revenue = extraCharges_year_revenue + \
                                            yearCal_revenue * \
                                            int(owner_revenue['result']
                                                [ore]['amount_paid'])
                                        extraCharges_revenue = extraCharges_revenue + \
                                            owner_revenue['result'][ore]['amount_paid']
                                    elif owner_revenue['result'][ore]['purchase_frequency'] == 'Annually':
                                        extraCharges_year_revenue = extraCharges_year_revenue + \
                                            owner_revenue['result'][ore]['amount_paid']
                                        extraCharges_revenue = extraCharges_revenue + \
                                            owner_revenue['result'][ore]['amount_paid']
                                    else:
                                        extraCharges_year_revenue = extraCharges_year_revenue + \
                                            owner_revenue['result'][ore]['amount_paid']
                                        extraCharges_revenue = extraCharges_revenue + \
                                            owner_revenue['result'][ore]['amount_paid']

                        response['result'][i]['rental_revenue'] = round(
                            rental_revenue, 2)
                        response['result'][i]['extraCharges_revenue'] = round(
                            extraCharges_revenue, 2)
                        response['result'][i]['rental_year_revenue'] = round(
                            rental_year_revenue, 2)
                        response['result'][i]['extraCharges_year_revenue'] = round(
                            extraCharges_year_revenue, 2)
                        print('rental_year_revenue', rental_year_revenue)
                        owner_utility_revenue = db.execute("""SELECT *
                                                        FROM pm.purchases p
                                                        LEFT JOIN
                                                        pm.payments pa
                                                        ON pa.pay_purchase_id = p.purchase_uid
                                                        LEFT JOIN rentals r
                                                        ON r.rental_property_id LIKE '%""" + property_id + """%'
                                                        WHERE p.pur_property_id LIKE '%""" + property_id + """%'
                                                        AND ({fn MONTHNAME(p.next_payment)} = {fn MONTHNAME(now())} AND YEAR(p.next_payment) = YEAR(now()))
                                                        AND (p.purchase_type="UTILITY")
                                                        AND p.receiver = \'""" + filterValue + """\'
                                                        AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED')
                                                        AND p.purchase_status = 'PAID' """)

                        response['result'][i]['owner_revenue'] = response['result'][i]['owner_revenue'] + (list(
                            owner_utility_revenue['result']))

                        if len(owner_utility_revenue['result']) > 0:
                            for ore in range(len(owner_utility_revenue['result'])):
                                if owner_utility_revenue['result'][ore]['purchase_frequency'] == 'Weekly':

                                    utility_revenue = utility_revenue + \
                                        float(owner_utility_revenue['result']
                                              [ore]['amount_paid'])
                                elif owner_utility_revenue['result'][ore]['purchase_frequency'] == 'Biweekly':

                                    utility_revenue = utility_revenue + \
                                        float(owner_utility_revenue['result']
                                              [ore]['amount_paid'])
                                elif owner_utility_revenue['result'][ore]['purchase_frequency'] == 'Monthly':

                                    utility_revenue = utility_revenue + \
                                        owner_utility_revenue['result'][ore]['amount_paid']
                                elif owner_utility_revenue['result'][ore]['purchase_frequency'] == 'Annually':

                                    utility_revenue = utility_revenue + \
                                        owner_utility_revenue['result'][ore]['amount_paid']
                                else:

                                    utility_revenue = utility_revenue + \
                                        owner_utility_revenue['result'][ore]['amount_paid']
                        response['result'][i]['utility_revenue'] = round(
                            utility_revenue, 2)
                        # annual revenue for the property
                        yearly_owner_revenue = db.execute("""SELECT *
                                                        FROM pm.purchases p
                                                        LEFT JOIN
                                                        pm.payments pa
                                                        ON pa.pay_purchase_id = p.purchase_uid
                                                        WHERE p.pur_property_id LIKE '%""" + property_id + """%'
                                                        AND (YEAR(p.next_payment) = YEAR(now()))
                                                        AND (p.purchase_type = "RENT" OR p.purchase_type = "EXTRA CHARGES") AND p.purchase_status = 'PAID' """)

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
                                                        WHERE p.pur_property_id LIKE '%""" + property_id + """%'
                                                        AND ({fn MONTHNAME(p.next_payment)} = {fn MONTHNAME(now())} AND YEAR(p.next_payment) = YEAR(now()))
                                                        AND (p.purchase_type <> "RENT" AND p.purchase_type <> "EXTRA CHARGES" AND p.purchase_type <> "UTILITY")
                                                        AND p.purchase_status = 'PAID' """)
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
                                        if owner_expense['result'][ore]['payment_frequency'] == 'Once a month' or owner_expense['result'][ore]['payment_frequency'] is None:
                                            print('in maintenance once a month')
                                            maintenance_year_expenses = maintenance_year_expenses + yearCal * \
                                                (owner_expense['result']
                                                    [ore]['amount_paid'])
                                            maintenance_expenses = maintenance_expenses + \
                                                owner_expense['result'][ore]['amount_paid']
                                         # if maintenance monthly twice a month
                                        elif owner_expense['result'][ore]['payment_frequency'] == 'Twice a month':
                                            print(
                                                'in maintenance twice a month')
                                            maintenance_year_expenses = maintenance_year_expenses + 2*yearCal * \
                                                (owner_expense['result']
                                                    [ore]['amount_paid'])
                                            maintenance_expenses = maintenance_expenses + \
                                                2 * \
                                                (owner_expense['result']
                                                    [ore]['amount_paid'])
                                        else:
                                            print('do nothing')
                                     # if maintenance annually
                                    elif owner_expense['result'][ore]['purchase_frequency'] == 'Annually':
                                        print('in maintenance annually')
                                        # if maintenance annually once a year
                                        if owner_expense['result'][ore]['payment_frequency'] == 'Once a year':
                                            maintenance_year_expenses = maintenance_year_expenses + \
                                                (owner_expense['result']
                                                    [ore]['amount_paid'])
                                            maintenance_expenses = maintenance_expenses + \
                                                owner_expense['result'][ore]['amount_paid']
                                        # if maintenance annually twice a year
                                        elif owner_expense['result'][ore]['payment_frequency'] == 'Twice a year':
                                            maintenance_year_expenses = maintenance_year_expenses + 2 * \
                                                (owner_expense['result']
                                                    [ore]['amount_paid'])
                                            maintenance_expenses = maintenance_expenses + \
                                                owner_expense['result'][ore]['amount_paid']
                                        else:
                                            print('do nothing')
                                    # if maintenance one-time
                                    else:
                                        maintenance_year_expenses = maintenance_expenses + \
                                            owner_expense['result'][ore]['amount_paid']
                                        maintenance_expenses = maintenance_expenses + \
                                            owner_expense['result'][ore]['amount_paid']
                                # if management
                                if owner_expense['result'][ore]['purchase_type'] == 'MANAGEMENT':
                                    print("MANAGEMTN")
                                    # if management monthly
                                    if owner_expense['result'][ore]['purchase_frequency'] == 'Monthly':
                                        # if management monthly once a month
                                        if owner_expense['result'][ore]['payment_frequency'] == 'Once a month' or owner_expense['result'][ore]['payment_frequency'] is None:
                                            print('here')
                                            management_year_expenses = yearCal * \
                                                (owner_expense['result']
                                                    [ore]['amount_paid'])
                                            management_expenses = management_expenses + \
                                                owner_expense['result'][ore]['amount_paid']
                                         # if management monthly twice a month
                                        elif owner_expense['result'][ore]['payment_frequency'] == 'Twice a month':
                                            management_year_expenses = 2*yearCal * \
                                                (owner_expense['result']
                                                    [ore]['amount_paid'])
                                            management_expenses = management_expenses + \
                                                2 * \
                                                (owner_expense['result']
                                                    [ore]['amount_paid'])
                                        else:
                                            print('do nothing')
                                     # if management annually
                                    elif owner_expense['result'][ore]['purchase_frequency'] == 'Annually':
                                        # if management annually once a year
                                        if owner_expense['result'][ore]['payment_frequency'] == 'Once a year':
                                            management_year_expenses =  \
                                                (owner_expense['result']
                                                    [ore]['amount_paid'])
                                            management_expenses = management_expenses + \
                                                owner_expense['result'][ore]['amount_paid']
                                        # if management annually twice a year
                                        elif owner_expense['result'][ore]['payment_frequency'] == 'Twice a year':
                                            management_year_expenses = 2 * \
                                                (owner_expense['result']
                                                    [ore]['amount_paid'])
                                            management_expenses = management_expenses + \
                                                owner_expense['result'][ore]['amount_paid']
                                        else:
                                            print('do nothing')
                                    # if management one-time
                                    else:
                                        management_year_expenses = management_expenses + \
                                            owner_expense['result'][ore]['amount_paid']
                                        management_expenses = management_expenses + \
                                            owner_expense['result'][ore]['amount_paid']

                                if owner_expense['result'][ore]['purchase_type'] == 'REPAIRS':
                                    # if repairs monthly
                                    if owner_expense['result'][ore]['purchase_frequency'] == 'Monthly':
                                        # if repairs monthly once a month
                                        if owner_expense['result'][ore]['payment_frequency'] == 'Once a month' or owner_expense['result'][ore]['payment_frequency'] is None:
                                            repairs_year_expenses = yearCal * \
                                                (owner_expense['result']
                                                    [ore]['amount_paid'])
                                            repairs_expenses = repairs_expenses + \
                                                owner_expense['result'][ore]['amount_paid']
                                         # if repairs monthly twice a month
                                        elif owner_expense['result'][ore]['payment_frequency'] == 'Twice a month':
                                            repairs_year_expenses = 2*yearCal * \
                                                (owner_expense['result']
                                                    [ore]['amount_paid'])
                                            repairs_expenses = repairs_expenses + \
                                                2 * \
                                                (owner_expense['result']
                                                    [ore]['amount_paid'])
                                        else:
                                            print('do nothing')
                                     # if repairs annually
                                    elif owner_expense['result'][ore]['purchase_frequency'] == 'Annually':
                                        # if repairs annually once a year
                                        if owner_expense['result'][ore]['payment_frequency'] == 'Once a year':
                                            repairs_year_expenses =  \
                                                (owner_expense['result']
                                                    [ore]['amount_paid'])
                                            repairs_expenses = repairs_expenses + \
                                                owner_expense['result'][ore]['amount_paid']
                                        # if repairs annually twice a year
                                        elif owner_expense['result'][ore]['payment_frequency'] == 'Twice a year':
                                            repairs_year_expenses = 2 * \
                                                (owner_expense['result']
                                                    [ore]['amount_paid'])
                                            repairs_expenses = repairs_expenses + \
                                                owner_expense['result'][ore]['amount_paid']
                                        else:
                                            print('do nothing')
                                    # if repairs one-time
                                    else:
                                        repairs_year_expenses = repairs_expenses + \
                                            owner_expense['result'][ore]['amount_paid']
                                        repairs_expenses = repairs_expenses + \
                                            owner_expense['result'][ore]['amount_paid']

                        owner_utility_expense = db.execute("""SELECT *
                                                        FROM pm.purchases p
                                                        LEFT JOIN
                                                        pm.payments pa
                                                        ON pa.pay_purchase_id = p.purchase_uid
                                                        LEFT JOIN rentals r
                                                        ON r.rental_property_id LIKE '%""" + property_id + """%'
                                                        WHERE p.pur_property_id LIKE '%""" + property_id + """%'
                                                        AND ({fn MONTHNAME(p.next_payment)} = {fn MONTHNAME(now())} AND YEAR(p.next_payment) = YEAR(now()))
                                                        AND (p.purchase_type="UTILITY")
                                                        AND p.payer LIKE '%""" + filterValue + """%'
                                                        AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED')
                                                        AND p.purchase_status = 'PAID' """)

                        response['result'][i]['owner_expense'] = response['result'][i]['owner_expense'] + (list(
                            owner_utility_expense['result']))

                        if len(owner_utility_expense['result']) > 0:
                            for ore in range(len(owner_utility_expense['result'])):
                                if owner_utility_expense['result'][ore]['purchase_frequency'] == 'Weekly':

                                    utility_expenses = utility_expenses + \
                                        float(owner_utility_expense['result']
                                              [ore]['amount_paid'])
                                elif owner_utility_expense['result'][ore]['purchase_frequency'] == 'Biweekly':

                                    utility_expenses = utility_expenses + \
                                        float(owner_utility_expense['result']
                                              [ore]['amount_paid'])
                                elif owner_utility_expense['result'][ore]['purchase_frequency'] == 'Monthly':

                                    utility_expenses = utility_expenses + \
                                        owner_utility_expense['result'][ore]['amount_paid']
                                elif owner_utility_expense['result'][ore]['purchase_frequency'] == 'Annually':

                                    utility_expenses = utility_expenses + \
                                        owner_utility_expense['result'][ore]['amount_paid']
                                else:

                                    utility_expenses = utility_expenses + \
                                        owner_utility_expense['result'][ore]['amount_paid']
                        response['result'][i]['utility_expenses'] = round(
                            utility_expenses, 2)

                        # monthly expenses for the property
                        manager_expense = db.execute("""SELECT *
                                                    FROM pm.purchases p
                                                    LEFT JOIN
                                                    pm.payments pa
                                                    ON pa.pay_purchase_id = p.purchase_uid
                                                    LEFT JOIN pm.rentals r
                                                    ON r.rental_property_id LIKE '%""" + response['result'][i]['property_uid'] + """%'
                                                    LEFT JOIN pm.contracts c
                                                    ON c.property_uid LIKE '%""" + response['result'][i]['property_uid'] + """%'
                                                    WHERE p.pur_property_id  LIKE '%""" + response['result'][i]['property_uid'] + """%'
                                                    AND c.contract_status = 'ACTIVE'
                                                    AND ({fn MONTHNAME(p.next_payment)} = {fn MONTHNAME(now())} AND YEAR(p.next_payment) = YEAR(now()))
                                                    AND (p.purchase_type= "RENT")
                                                    AND r.rental_status = 'ACTIVE'
                                                    AND p.purchase_status = 'PAID'""")

                        response['result'][i]['owner_expense'] = response['result'][i]['owner_expense'] + (list(
                            manager_expense['result']))
                        if len(manager_expense['result']) > 0:
                            for mex in range(len(manager_expense['result'])):
                                # print('mex', manager_expense['result'][mex])

                                # if management
                                if manager_expense['result'][mex]['purchase_type'] == 'RENT':
                                    managementPayments = json.loads(
                                        manager_expense['result'][mex]['contract_fees'])

                                    for payment in managementPayments:
                                        # print('amount paid to owner', payment)
                                        if payment['fee_type'] == '%':
                                            print(management_expenses)
                                            if payment['of'] == 'Gross Rent':

                                                if payment['frequency'] == 'Weekly':
                                                    print('amount weekly %',
                                                          management_expenses, float(manager_expense['result'][mex]['amount_paid']), payment['charge'], weeks_current_month)
                                                    management_expenses = management_expenses +  \
                                                        weeks_current_month*float((
                                                            float(manager_expense['result'][mex]['amount_paid']) * float(payment['charge']))/100)
                                                    print('amount weekly %',
                                                          management_expenses, float(manager_expense['result'][mex]['amount_paid']), payment['charge'])
                                                elif payment['frequency'] == 'Biweekly':
                                                    print('amount biweekly %',
                                                          management_expenses, float(manager_expense['result'][mex]['amount_paid']), payment['charge'], weeks_current_month/2)
                                                    management_expenses = management_expenses +  \
                                                        weeks_current_month/2 * \
                                                        ((
                                                            float(manager_expense['result'][mex]['amount_paid']) * float(payment['charge']))/100)
                                                    print('amount biweekly %',
                                                          management_expenses, float(manager_expense['result'][mex]['amount_paid']), payment['charge'])
                                                elif payment['frequency'] == 'Monthly':
                                                    print('amount monthly %',
                                                          management_expenses, float(manager_expense['result'][mex]['amount_paid']), payment['charge'])
                                                    management_expenses = management_expenses +  \
                                                        (
                                                            float(manager_expense['result'][mex]['amount_paid']) * float(payment['charge']))/100
                                                    print('amount monthly %',
                                                          management_expenses, float(
                                                              manager_expense['result'][mex]['amount_paid']), payment['charge'])
                                                elif payment['frequency'] == 'Annually':
                                                    print(
                                                        'amount annually %', management_expenses, float(manager_expense['result'][mex]['amount_paid']), payment['charge'])
                                                    if date.fromisoformat(manager_expense['result'][mex]['start_date']).month == today.month:
                                                        management_expenses = management_expenses +  \
                                                            (
                                                                float(manager_expense['result'][mex]['amount_paid']) * float(payment['charge']))/100
                                                        print(
                                                            'amount annually %', management_expenses, float(manager_expense['result'][mex]['amount_paid']), payment['charge'])
                                                elif payment['frequency'] == 'One-time':
                                                    print(
                                                        'amount one-time %', management_expenses, date.fromisoformat(manager_expense['result'][mex]['start_date']).month)
                                                    if date.fromisoformat(manager_expense['result'][mex]['start_date']).month == today.month:
                                                        management_expenses = management_expenses +  \
                                                            (
                                                                float(manager_expense['result'][mex]['amount_paid']) * float(payment['charge']))/100
                                                        print(
                                                            'amount one-time %', management_expenses, float(manager_expense['result'][mex]['amount_paid']), payment['charge'])
                                                else:
                                                    print('do nothing')
                                        elif payment['fee_type'] == '$':
                                            if payment['frequency'] == 'Weekly':
                                                print('amount weekly $',
                                                      management_expenses)
                                                management_expenses = management_expenses + weeks_current_month * \
                                                    float(payment['charge'])
                                                print('amount weekly $',
                                                      management_expenses)
                                            elif payment['frequency'] == 'Biweekly':
                                                print('amount biweekly $',
                                                      management_expenses)
                                                management_expenses = management_expenses + weeks_current_month/2 * \
                                                    float(payment['charge'])
                                                print('amount biweekly $',
                                                      management_expenses)
                                            elif payment['frequency'] == 'Monthly':
                                                print('amount monthly $',
                                                      management_expenses)
                                                management_expenses = management_expenses + \
                                                    float(payment['charge'])
                                                print('amount monthly $',
                                                      management_expenses)
                                            elif payment['frequency'] == 'Annually':
                                                print('amount annually $',
                                                      management_expenses)
                                                if date.fromisoformat(manager_expense['result'][mex]['start_date']).month == today.month:
                                                    management_expenses = management_expenses + \
                                                        float(
                                                            payment['charge'])
                                                    print(
                                                        'amount annually $', management_expenses, payment['charge'])
                                            elif payment['frequency'] == 'One-time':
                                                print(
                                                    'amount one-time $', management_expenses)
                                                if date.fromisoformat(manager_expense['result'][mex]['start_date']).month == today.month:
                                                    management_expenses = management_expenses + \
                                                        float(
                                                            payment['charge'])
                                                    print(
                                                        'amount one-time $', management_expenses)
                                            else:
                                                print('do nothing')
                                        else:
                                            print('do nothing')

                        response['result'][i]['maintenance_expenses'] = round(
                            maintenance_expenses, 2)
                        response['result'][i]['management_expenses'] = round(
                            management_expenses, 2)
                        response['result'][i]['repairs_expenses'] = round(
                            repairs_expenses, 2)
                        response['result'][i]['utility_expenses'] = round(
                            utility_expenses, 2)
                        response['result'][i]['maintenance_year_expense'] = round(
                            maintenance_year_expenses, 2)
                        response['result'][i]['management_year_expense'] = round(
                            management_year_expenses, 2)
                        response['result'][i]['repairs_year_expense'] = round(
                            repairs_year_expenses, 2)

                        # annual expense for the property
                        yearly_owner_expense = db.execute("""SELECT *
                                                        FROM pm.purchases p
                                                        LEFT JOIN
                                                        pm.payments pa
                                                        ON pa.pay_purchase_id = p.purchase_uid
                                                        WHERE p.pur_property_id  LIKE '%""" + property_id + """%'
                                                        AND (YEAR(p.next_payment) = YEAR(now()))
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
                        # monthly revenue for the property
                        owner_expected_revenue = db.execute("""SELECT *
                                                        FROM pm.purchases p
                                                        LEFT JOIN
                                                        pm.payments pa
                                                        ON pa.pay_purchase_id = p.purchase_uid
                                                        LEFT JOIN rentals r
                                                        ON r.rental_property_id LIKE '%""" + property_id + """%'
                                                        WHERE p.pur_property_id LIKE '%""" + property_id + """%'
                                                        AND ({fn MONTHNAME(p.next_payment)} = {fn MONTHNAME(now())} AND YEAR(p.next_payment) = YEAR(now()))
                                                        AND (p.purchase_type= "RENT" OR p.purchase_type= "EXTRA CHARGES")
                                                        AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED') """)
                        response['result'][i]['owner_expected_revenue'] = list(
                            owner_expected_revenue['result'])

                        if len(owner_expected_revenue['result']) > 0:
                            for ore in range(len(owner_expected_revenue['result'])):
                                print('owner revenue',
                                      owner_expected_revenue['result'][ore])
                                yearCal_expected_revenue = today.month - \
                                    (datetime.strptime(
                                        owner_expected_revenue['result'][ore]['lease_start'], '%Y-%m-%d')).month

                                weeks_current_month = len(calendar.monthcalendar(
                                    2022, int(today.strftime("%m"))))

                                weeks_active_expected_revenue = round((abs(today - datetime.strptime(
                                    owner_expected_revenue['result'][ore]['lease_start'], '%Y-%m-%d').date()).days)/7, 1)
                                if owner_expected_revenue['result'][ore]['purchase_type'] == 'RENT':
                                    if owner_expected_revenue['result'][ore]['purchase_frequency'] == 'Weekly':
                                        rental_year_expected_revenue = rental_year_expected_revenue + \
                                            weeks_active_expected_revenue * \
                                            int(owner_expected_revenue['result']
                                                [ore]['amount_due'])
                                        rental_expected_revenue = rental_expected_revenue + \
                                            weeks_current_month*int(owner_expected_revenue['result']
                                                                    [ore]['amount_due'])
                                    elif owner_expected_revenue['result'][ore]['purchase_frequency'] == 'Biweekly':
                                        rental_year_expected_revenue = rental_year_expected_revenue + \
                                            weeks_active_expected_revenue/2 * \
                                            int(owner_expected_revenue['result']
                                                [ore]['amount_due'])
                                        rental_expected_revenue = rental_expected_revenue + \
                                            weeks_current_month/2 * \
                                            int(owner_expected_revenue['result']
                                                [ore]['amount_due'])
                                    elif owner_expected_revenue['result'][ore]['purchase_frequency'] == 'Monthly':
                                        rental_year_expected_revenue = rental_year_expected_revenue + \
                                            yearCal_expected_revenue * \
                                            int(owner_expected_revenue['result']
                                                [ore]['amount_due'])
                                        rental_expected_revenue = rental_expected_revenue + \
                                            owner_expected_revenue['result'][ore]['amount_due']
                                    elif owner_expected_revenue['result'][ore]['purchase_frequency'] == 'Annually':
                                        rental_year_expected_revenue = rental_year_expected_revenue + \
                                            owner_expected_revenue['result'][ore]['amount_due']
                                        rental_expected_revenue = rental_expected_revenue + \
                                            owner_expected_revenue['result'][ore]['amount_due']
                                    else:
                                        rental_year_expected_revenue = rental_year_expected_revenue + \
                                            owner_expected_revenue['result'][ore]['amount_due']
                                        rental_expected_revenue = rental_expected_revenue + \
                                            owner_expected_revenue['result'][ore]['amount_due']

                                if owner_expected_revenue['result'][ore]['purchase_type'] == 'EXTRA CHARGES':
                                    if owner_expected_revenue['result'][ore]['purchase_frequency'] == 'Weekly':
                                        extraCharges_year_expected_revenue = extraCharges_year_expected_revenue + \
                                            weeks_active_expected_revenue * \
                                            int(owner_expected_revenue['result']
                                                [ore]['amount_due'])
                                        extraCharges_expected_revenue = extraCharges_expected_revenue + \
                                            weeks_current_month*int(owner_expected_revenue['result']
                                                                    [ore]['amount_due'])
                                    elif owner_expected_revenue['result'][ore]['purchase_frequency'] == 'Biweekly':
                                        extraCharges_year_expected_revenue = extraCharges_year_expected_revenue + \
                                            weeks_active_expected_revenue/2 * \
                                            int(owner_expected_revenue['result']
                                                [ore]['amount_due'])
                                        extraCharges_expected_revenue = extraCharges_expected_revenue + \
                                            weeks_current_month/2 * \
                                            int(owner_expected_revenue['result']
                                                [ore]['amount_due'])
                                    elif owner_expected_revenue['result'][ore]['purchase_frequency'] == 'Monthly':
                                        extraCharges_year_expected_revenue = extraCharges_year_expected_revenue + \
                                            yearCal_expected_revenue * \
                                            int(owner_expected_revenue['result']
                                                [ore]['amount_due'])
                                        extraCharges_expected_revenue = extraCharges_expected_revenue + \
                                            owner_expected_revenue['result'][ore]['amount_due']
                                    elif owner_expected_revenue['result'][ore]['purchase_frequency'] == 'Annually':
                                        extraCharges_year_expected_revenue = extraCharges_year_expected_revenue + \
                                            owner_expected_revenue['result'][ore]['amount_due']
                                        extraCharges_expected_revenue = extraCharges_expected_revenue + \
                                            owner_expected_revenue['result'][ore]['amount_due']
                                    else:
                                        extraCharges_year_expected_revenue = extraCharges_year_expected_revenue + \
                                            owner_expected_revenue['result'][ore]['amount_due']
                                        extraCharges_expected_revenue = extraCharges_expected_revenue + \
                                            owner_expected_revenue['result'][ore]['amount_due']

                        response['result'][i]['rental_expected_revenue'] = round(
                            rental_expected_revenue, 2)
                        response['result'][i]['extraCharges_expected_revenue'] = round(
                            extraCharges_expected_revenue, 2)
                        response['result'][i]['rental_year_expected_revenue'] = round(
                            rental_year_expected_revenue, 2)
                        response['result'][i]['extraCharges_year_expected_revenue'] = round(
                            extraCharges_year_expected_revenue, 2)

                        owner_utility_expected_revenue = db.execute("""SELECT *
                                                        FROM pm.purchases p
                                                        LEFT JOIN
                                                        pm.payments pa
                                                        ON pa.pay_purchase_id = p.purchase_uid
                                                        LEFT JOIN rentals r
                                                        ON r.rental_property_id LIKE '%""" + property_id + """%'
                                                        WHERE p.pur_property_id LIKE '%""" + property_id + """%'
                                                        AND ({fn MONTHNAME(p.next_payment)} = {fn MONTHNAME(now())} AND YEAR(p.next_payment) = YEAR(now()))
                                                        AND (p.purchase_type="UTILITY")
                                                        AND p.receiver = \'""" + filterValue + """\'
                                                        AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED') """)

                        response['result'][i]['owner_expected_revenue'] = response['result'][i]['owner_expected_revenue'] + (list(
                            owner_utility_expected_revenue['result']))

                        if len(owner_utility_expected_revenue['result']) > 0:
                            for ore in range(len(owner_utility_expected_revenue['result'])):
                                if owner_utility_expected_revenue['result'][ore]['purchase_frequency'] == 'Weekly':

                                    utility_expected_revenue = utility_expected_revenue + \
                                        float(owner_utility_expected_revenue['result']
                                              [ore]['amount_due'])
                                elif owner_utility_expected_revenue['result'][ore]['purchase_frequency'] == 'Biweekly':

                                    utility_expected_revenue = utility_expected_revenue + \
                                        float(owner_utility_expected_revenue['result']
                                              [ore]['amount_due'])
                                elif owner_utility_expected_revenue['result'][ore]['purchase_frequency'] == 'Monthly':

                                    utility_expected_revenue = utility_expected_revenue + \
                                        owner_utility_expected_revenue['result'][ore]['amount_due']
                                elif owner_utility_expected_revenue['result'][ore]['purchase_frequency'] == 'Annually':

                                    utility_expected_revenue = utility_expected_revenue + \
                                        owner_utility_expected_revenue['result'][ore]['amount_due']
                                else:

                                    utility_expected_revenue = utility_expected_revenue + \
                                        owner_utility_expected_revenue['result'][ore]['amount_due']
                        response['result'][i]['utility_expected_revenue'] = round(
                            utility_expected_revenue, 2)
                        # annual revenue for the property
                        yearly_owner_expected_revenue = db.execute("""SELECT *
                                                        FROM pm.purchases p
                                                        LEFT JOIN
                                                        pm.payments pa
                                                        ON pa.pay_purchase_id = p.purchase_uid
                                                        WHERE p.pur_property_id LIKE '%""" + property_id + """%'
                                                        AND (YEAR(p.next_payment) = YEAR(now()))
                                                        AND (p.purchase_type = "RENT" OR p.purchase_type = "EXTRA CHARGES") """)

                        response['result'][i]['year_expected_revenue'] = 0
                        if len(yearly_owner_expected_revenue['result']) > 0:
                            for pr in range(len(yearly_owner_expected_revenue['result'])):

                                response['result'][i]['year_expected_revenue'] = response['result'][i]['year_expected_revenue'] + int(
                                    yearly_owner_expected_revenue['result'][pr]['amount_due'])
                        else:
                            response['result'][i]['year_expected_revenue'] = 0

                        # monthly expense for the property
                        owner_expected_expense = db.execute("""SELECT *
                                                        FROM pm.purchases p
                                                        LEFT JOIN
                                                        pm.payments pa
                                                        ON pa.pay_purchase_id = p.purchase_uid
                                                        WHERE p.pur_property_id LIKE '%""" + property_id + """%'
                                                        AND ({fn MONTHNAME(p.next_payment)} = {fn MONTHNAME(now())} AND YEAR(p.next_payment) = YEAR(now()))
                                                        AND (p.purchase_type <> "RENT" AND p.purchase_type <> "EXTRA CHARGES" AND p.purchase_type<>'UTILITY')
                                                        AND (payer LIKE '%""" + filterValue + """%') """)
                        response['result'][i]['owner_expected_expense'] = list(
                            owner_expected_expense['result'])

                        maintenance_year_expected_expenses = 0
                        management_year_expected_expenses = 0
                        repairs_year_expected_expenses = 0

                        if len(owner_expected_expense['result']) > 0:
                            for ore in range(len(owner_expected_expense['result'])):
                                print(
                                    'ore', owner_expected_expense['result'][ore])

                                # if maintenance
                                if owner_expected_expense['result'][ore]['purchase_type'] == 'MAINTENANCE':
                                    print('in maintenance')
                                    # if maintenance monthly
                                    if owner_expected_expense['result'][ore]['purchase_frequency'] == 'Monthly':
                                        print('in maintenance monthly')
                                        # if maintenance monthly once a month
                                        if owner_expected_expense['result'][ore]['payment_frequency'] == 'Once a month' or owner_expected_expense['result'][ore]['payment_frequency'] is None:
                                            print('in maintenance once a month')
                                            maintenance_year_expected_expenses = maintenance_year_expected_expenses + yearCal * \
                                                (owner_expected_expense['result']
                                                    [ore]['amount_due'])
                                            maintenance_expected_expenses = maintenance_expected_expenses + \
                                                owner_expected_expense['result'][ore]['amount_due']
                                         # if maintenance monthly twice a month
                                        elif owner_expected_expense['result'][ore]['payment_frequency'] == 'Twice a month':
                                            print(
                                                'in maintenance twice a month')
                                            maintenance_year_expected_expenses = maintenance_year_expected_expenses + 2*yearCal * \
                                                (owner_expected_expense['result']
                                                    [ore]['amount_due'])
                                            maintenance_expected_expenses = maintenance_expected_expenses + \
                                                2 * \
                                                (owner_expected_expense['result']
                                                    [ore]['amount_due'])
                                        else:
                                            print('do nothing')
                                     # if maintenance annually
                                    elif owner_expected_expense['result'][ore]['purchase_frequency'] == 'Annually':
                                        print('in maintenance annually')
                                        # if maintenance annually once a year
                                        if owner_expected_expense['result'][ore]['payment_frequency'] == 'Once a year':
                                            maintenance_year_expected_expenses = maintenance_year_expected_expenses + \
                                                (owner_expected_expense['result']
                                                    [ore]['amount_due'])
                                            maintenance_expected_expenses = maintenance_expected_expenses + \
                                                owner_expected_expense['result'][ore]['amount_due']
                                        # if maintenance annually twice a year
                                        elif owner_expected_expense['result'][ore]['payment_frequency'] == 'Twice a year':
                                            maintenance_year_expected_expenses = maintenance_year_expected_expenses + 2 * \
                                                (owner_expected_expense['result']
                                                    [ore]['amount_due'])
                                            maintenance_expected_expenses = maintenance_expected_expenses + \
                                                owner_expected_expense['result'][ore]['amount_due']
                                        else:
                                            print('do nothing')
                                    # if maintenance one-time
                                    else:
                                        maintenance_year_expected_expenses = maintenance_expected_expenses + \
                                            owner_expected_expense['result'][ore]['amount_due']
                                        maintenance_expected_expenses = maintenance_expected_expenses + \
                                            owner_expected_expense['result'][ore]['amount_due']
                                # if management
                                if owner_expected_expense['result'][ore]['purchase_type'] == 'MANAGEMENT':
                                    print("MANAGEMTN")
                                    # if management monthly
                                    if owner_expected_expense['result'][ore]['purchase_frequency'] == 'Monthly':
                                        # if management monthly once a month
                                        if owner_expected_expense['result'][ore]['payment_frequency'] == 'Once a month' or owner_expected_expense['result'][ore]['payment_frequency'] is None:
                                            print('here')
                                            management_year_expected_expenses = yearCal * \
                                                (owner_expected_expense['result']
                                                    [ore]['amount_due'])
                                            management_expected_expenses = management_expected_expenses + \
                                                owner_expected_expense['result'][ore]['amount_due']
                                         # if management monthly twice a month
                                        elif owner_expected_expense['result'][ore]['payment_frequency'] == 'Twice a month':
                                            management_year_expected_expenses = 2*yearCal * \
                                                (owner_expected_expense['result']
                                                    [ore]['amount_due'])
                                            management_expected_expenses = management_expected_expenses + \
                                                2 * \
                                                (owner_expected_expense['result']
                                                    [ore]['amount_due'])
                                        else:
                                            print('do nothing')
                                     # if management annually
                                    elif owner_expected_expense['result'][ore]['purchase_frequency'] == 'Annually':
                                        # if management annually once a year
                                        if owner_expected_expense['result'][ore]['payment_frequency'] == 'Once a year':
                                            management_year_expected_expenses =  \
                                                (owner_expected_expense['result']
                                                    [ore]['amount_due'])
                                            management_expected_expenses = management_expected_expenses + \
                                                owner_expected_expense['result'][ore]['amount_due']
                                        # if management annually twice a year
                                        elif owner_expected_expense['result'][ore]['payment_frequency'] == 'Twice a year':
                                            management_year_expected_expenses = 2 * \
                                                (owner_expected_expense['result']
                                                    [ore]['amount_due'])
                                            management_expected_expenses = management_expected_expenses + \
                                                owner_expected_expense['result'][ore]['amount_due']
                                        else:
                                            print('do nothing')
                                    # if management one-time
                                    else:
                                        management_year_expected_expenses = management_expected_expenses + \
                                            owner_expected_expense['result'][ore]['amount_due']
                                        management_expected_expenses = management_expected_expenses + \
                                            owner_expected_expense['result'][ore]['amount_due']

                                if owner_expected_expense['result'][ore]['purchase_type'] == 'REPAIRS':
                                    # if repairs monthly
                                    if owner_expected_expense['result'][ore]['purchase_frequency'] == 'Monthly':
                                        # if repairs monthly once a month
                                        if owner_expected_expense['result'][ore]['payment_frequency'] == 'Once a month' or owner_expected_expense['result'][ore]['payment_frequency'] is None:
                                            repairs_year_expected_expenses = yearCal * \
                                                (owner_expected_expense['result']
                                                    [ore]['amount_due'])
                                            repairs_expected_expenses = repairs_expected_expenses + \
                                                owner_expected_expense['result'][ore]['amount_due']
                                         # if repairs monthly twice a month
                                        elif owner_expected_expense['result'][ore]['payment_frequency'] == 'Twice a month':
                                            repairs_year_expected_expenses = 2*yearCal * \
                                                (owner_expected_expense['result']
                                                    [ore]['amount_due'])
                                            repairs_expected_expenses = repairs_expected_expenses + \
                                                2 * \
                                                (owner_expected_expense['result']
                                                    [ore]['amount_due'])
                                        else:
                                            print('do nothing')
                                     # if repairs annually
                                    elif owner_expected_expense['result'][ore]['purchase_frequency'] == 'Annually':
                                        # if repairs annually once a year
                                        if owner_expected_expense['result'][ore]['payment_frequency'] == 'Once a year':
                                            repairs_year_expected_expenses =  \
                                                (owner_expected_expense['result']
                                                    [ore]['amount_due'])
                                            repairs_expected_expenses = repairs_expected_expenses + \
                                                owner_expected_expense['result'][ore]['amount_due']
                                        # if repairs annually twice a year
                                        elif owner_expected_expense['result'][ore]['payment_frequency'] == 'Twice a year':
                                            repairs_year_expected_expenses = 2 * \
                                                (owner_expected_expense['result']
                                                    [ore]['amount_due'])
                                            repairs_expected_expenses = repairs_expected_expenses + \
                                                owner_expected_expense['result'][ore]['amount_due']
                                        else:
                                            print('do nothing')
                                    # if repairs one-time
                                    else:
                                        repairs_year_expected_expenses = repairs_expected_expenses + \
                                            owner_expected_expense['result'][ore]['amount_due']
                                        repairs_expected_expenses = repairs_expected_expenses + \
                                            owner_expected_expense['result'][ore]['amount_due']
                        owner_utility_expected_expenses = db.execute("""SELECT *
                                                        FROM pm.purchases p
                                                        LEFT JOIN
                                                        pm.payments pa
                                                        ON pa.pay_purchase_id = p.purchase_uid
                                                        LEFT JOIN rentals r
                                                        ON r.rental_property_id LIKE '%""" + property_id + """%'
                                                        WHERE p.pur_property_id LIKE '%""" + property_id + """%'
                                                        AND ({fn MONTHNAME(p.next_payment)} = {fn MONTHNAME(now())} AND YEAR(p.next_payment) = YEAR(now()))
                                                        AND (p.purchase_type="UTILITY")
                                                        AND payer LIKE '%""" + filterValue + """%'
                                                        AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED') """)

                        response['result'][i]['owner_expected_expense'] = response['result'][i]['owner_expected_expense'] + (list(
                            owner_utility_expected_expenses['result']))

                        if len(owner_utility_expected_expenses['result']) > 0:
                            for ore in range(len(owner_utility_expected_expenses['result'])):
                                if owner_utility_expected_expenses['result'][ore]['purchase_frequency'] == 'Weekly':

                                    utility_expected_expenses = utility_expected_expenses + \
                                        float(owner_utility_expected_expenses['result']
                                              [ore]['amount_due'])
                                elif owner_utility_expected_expenses['result'][ore]['purchase_frequency'] == 'Biweekly':

                                    utility_expected_expenses = utility_expected_expenses + \
                                        float(owner_utility_expected_expenses['result']
                                              [ore]['amount_due'])
                                elif owner_utility_expected_expenses['result'][ore]['purchase_frequency'] == 'Monthly':

                                    utility_expected_expenses = utility_expected_expenses + \
                                        owner_utility_expected_expenses['result'][ore]['amount_due']
                                elif owner_utility_expected_expenses['result'][ore]['purchase_frequency'] == 'Annually':

                                    utility_expected_expenses = utility_expected_expenses + \
                                        owner_utility_expected_expenses['result'][ore]['amount_due']
                                else:

                                    utility_expected_expenses = utility_expected_expenses + \
                                        owner_utility_expected_expenses['result'][ore]['amount_due']
                        response['result'][i]['utility_expected_expenses'] = round(
                            utility_expected_expenses, 2)
                        # monthly expenses for the property
                        manager_expected_expense = db.execute("""SELECT *
                                                    FROM pm.purchases p
                                                    LEFT JOIN
                                                    pm.payments pa
                                                    ON pa.pay_purchase_id = p.purchase_uid
                                                    LEFT JOIN pm.rentals r
                                                    ON r.rental_property_id LIKE '%""" + response['result'][i]['property_uid'] + """%'
                                                    LEFT JOIN pm.contracts c
                                                    ON c.property_uid LIKE '%""" + response['result'][i]['property_uid'] + """%'
                                                    WHERE p.pur_property_id LIKE '%""" + response['result'][i]['property_uid'] + """%'
                                                    AND c.contract_status = 'ACTIVE'
                                                    AND ({fn MONTHNAME(p.next_payment)} = {fn MONTHNAME(now())} AND YEAR(p.next_payment) = YEAR(now()))
                                                    AND (p.purchase_type= "RENT")
                                                    AND r.rental_status = 'ACTIVE'""")

                        print(
                            'mex', manager_expected_expense['result'])
                        response['result'][i]['owner_expected_expense'] = response['result'][i]['owner_expected_expense'] + (list(
                            manager_expected_expense['result']))
                        if len(manager_expected_expense['result']) > 0:
                            for mex in range(len(manager_expected_expense['result'])):

                                # if management
                                if manager_expected_expense['result'][mex]['purchase_type'] == 'RENT':
                                    managementPayments = json.loads(
                                        manager_expected_expense['result'][mex]['contract_fees'])
                                    print('management_expected_expenses',
                                          management_expected_expenses)
                                    for payment in managementPayments:

                                        if payment['fee_type'] == '%':

                                            if payment['of'] == 'Gross Rent':

                                                if payment['frequency'] == 'Weekly':
                                                    print('amount weekly expected %',
                                                          management_expected_expenses, float(manager_expected_expense['result'][mex]['amount_due']), payment['charge'], weeks_current_month)
                                                    management_expected_expenses = management_expected_expenses +  \
                                                        weeks_current_month*float((
                                                            float(manager_expected_expense['result'][mex]['amount_due']) * float(payment['charge']))/100)
                                                    print('amount weekly %',
                                                          management_expected_expenses, float(manager_expected_expense['result'][mex]['amount_due']), payment['charge'])
                                                elif payment['frequency'] == 'Biweekly':
                                                    print('amount biweekly %',
                                                          management_expected_expenses, float(manager_expected_expense['result'][mex]['amount_due']), payment['charge'], weeks_current_month/2)
                                                    management_expected_expenses = management_expected_expenses +  \
                                                        weeks_current_month/2 * \
                                                        ((
                                                            float(manager_expected_expense['result'][mex]['amount_due']) * float(payment['charge']))/100)
                                                    print('amount biweekly %',
                                                          management_expected_expenses, float(manager_expected_expense['result'][mex]['amount_due']), payment['charge'])
                                                elif payment['frequency'] == 'Monthly':
                                                    print('amount monthly %',
                                                          management_expected_expenses, float(manager_expected_expense['result'][mex]['amount_due']), payment['charge'])
                                                    management_expected_expenses = management_expected_expenses +  \
                                                        (
                                                            float(manager_expected_expense['result'][mex]['amount_due']) * float(payment['charge']))/100
                                                    print('amount monthly %',
                                                          management_expected_expenses, float(
                                                              manager_expected_expense['result'][mex]['amount_due']), payment['charge'])
                                                elif payment['frequency'] == 'Annually':
                                                    print(
                                                        'amount annually %', management_expected_expenses, float(manager_expected_expense['result'][mex]['amount_due']), payment['charge'])
                                                    if date.fromisoformat(manager_expected_expense['result'][mex]['start_date']).month == today.month:
                                                        management_expected_expenses = management_expected_expenses +  \
                                                            (
                                                                float(manager_expected_expense['result'][mex]['amount_due']) * float(payment['charge']))/100
                                                        print(
                                                            'amount annually %', management_expected_expenses, float(manager_expected_expense['result'][mex]['amount_due']), payment['charge'])
                                                elif payment['frequency'] == 'One-time':
                                                    print(
                                                        'amount one-time %', management_expected_expenses, date.fromisoformat(manager_expected_expense['result'][mex]['start_date']).month)
                                                    if date.fromisoformat(manager_expected_expense['result'][mex]['start_date']).month == today.month:
                                                        management_expected_expenses = management_expected_expenses +  \
                                                            (
                                                                float(manager_expected_expense['result'][mex]['amount_due']) * float(payment['charge']))/100
                                                        print(
                                                            'amount one-time %', management_expected_expenses, float(manager_expected_expense['result'][mex]['amount_due']), payment['charge'])
                                                else:
                                                    print('do nothing')
                                        elif payment['fee_type'] == '$':
                                            if payment['frequency'] == 'Weekly':
                                                print('amount weekly $',
                                                      management_expected_expenses)
                                                management_expected_expenses = management_expected_expenses + weeks_current_month * \
                                                    float(payment['charge'])
                                                print('amount weekly $',
                                                      management_expected_expenses)
                                            elif payment['frequency'] == 'Biweekly':
                                                print('amount biweekly $',
                                                      management_expected_expenses)
                                                management_expected_expenses = management_expected_expenses + weeks_current_month/2 * \
                                                    float(payment['charge'])
                                                print('amount biweekly $',
                                                      management_expected_expenses)
                                            elif payment['frequency'] == 'Monthly':
                                                print('amount monthly $',
                                                      management_expected_expenses)
                                                management_expected_expenses = management_expected_expenses + \
                                                    float(payment['charge'])
                                                print('amount monthly $',
                                                      management_expected_expenses)
                                            elif payment['frequency'] == 'Annually':
                                                print('amount annually $',
                                                      management_expected_expenses)
                                                if date.fromisoformat(manager_expected_expense['result'][mex]['start_date']).month == today.month:
                                                    management_expected_expenses = management_expected_expenses + \
                                                        float(
                                                            payment['charge'])
                                                    print(
                                                        'amount annually $', management_expected_expenses, payment['charge'])
                                            elif payment['frequency'] == 'One-time':
                                                print(
                                                    'amount one-time $', management_expected_expenses)
                                                if date.fromisoformat(manager_expected_expense['result'][mex]['start_date']).month == today.month:
                                                    management_expected_expenses = management_expected_expenses + \
                                                        float(
                                                            payment['charge'])
                                                    print(
                                                        'amount one-time $', management_expected_expenses)
                                            else:
                                                print('do nothing')
                                        else:
                                            print('do nothing')

                        response['result'][i]['maintenance_expected_expenses'] = round(
                            maintenance_expected_expenses, 2)
                        response['result'][i]['management_expected_expenses'] = round(
                            management_expected_expenses, 2)
                        response['result'][i]['repairs_expected_expenses'] = round(
                            repairs_expected_expenses, 2)
                        response['result'][i]['utility_expected_expenses'] = round(
                            utility_expected_expenses, 2)
                        # print(response)

                        # get utilities or maintenance/repair expenses
                        expense_res = db.execute("""SELECT p.*, pa.*, CONCAT(prop.address," ", prop.unit,", ", prop.city, ", ", prop.state," ", prop.zip) AS address
                            FROM pm.purchases p
                            LEFT JOIN payments pa
                            ON pa.pay_purchase_id = p.purchase_uid
                            LEFT JOIN pm.properties prop
                            ON prop.property_uid LIKE '%""" + property_id + """%'
                            WHERE p.pur_property_id LIKE '%""" + property_id + """%'
                            AND (purchase_type = 'UTILITY' OR  purchase_type = 'MAINTENANCE' OR purchase_type = 'REPAIRS')
                            AND (receiver = \'""" + filterValue + """\' OR payer LIKE '%""" + filterValue + """%')
                            """)
                        if len(expense_res['result']) > 0:
                            response['result'][i]['expenses'] = list(
                                expense_res['result'])
                            for i in range(len(expense_res['result'])):
                                # if utility return all the details related to the utility
                                if expense_res['result'][i]['purchase_type'] == 'UTILITY':
                                    print('in utility')

                                    billRes = db.execute("""SELECT b.*
                                                            FROM pm.bills b                
                                                            WHERE b.bill_uid = \'""" + expense_res['result'][i]['linked_bill_id'] + """\' """)

                                    if(len(billRes['result']) > 0):
                                        for j in range(len(billRes['result'])):
                                            expense_res['result'][i].update(
                                                billRes['result'][j])
                                            # expense_res['result'][i] = (expense_res['result'][i]) + (
                                            #     billRes['result'][j])
                                # if maintainence return all the details related to the maintenance requests
                                elif expense_res['result'][i]['purchase_type'] == 'MAINTENANCE':
                                    print('in maintenance')
                                    maintenanceRes = db.execute("""SELECT mq.*, mr.*, b.*
                                                                    FROM maintenanceQuotes mq
                                                                    LEFT JOIN pm.maintenanceRequests mr
                                                                    ON mr.maintenance_request_uid = mq.linked_request_uid
                                                                    LEFT JOIN pm.businesses b
                                                                    ON b.business_uid = mq.quote_business_uid
                                                                    WHERE  mq.maintenance_quote_uid = \'""" + expense_res['result'][i]['linked_bill_id'] + """\' """)

                                    if(len(maintenanceRes['result']) > 0):
                                        for j in range(len(maintenanceRes['result'])):
                                            expense_res['result'][i].update(
                                                maintenanceRes['result'][j])
                                # if repair return all the details related to the repair requests
                                elif expense_res['result'][i]['purchase_type'] == 'REPAIRS':
                                    print('in maintenance')
                                    repairRes = db.execute("""SELECT mq.*, mr.*, b.*
                                                                    FROM maintenanceQuotes mq
                                                                    LEFT JOIN pm.maintenanceRequests mr
                                                                    ON mr.maintenance_request_uid = mq.linked_request_uid
                                                                    LEFT JOIN pm.businesses b
                                                                    ON b.business_uid = mq.quote_business_uid
                                                                    WHERE  mq.maintenance_quote_uid = \'""" + expense_res['result'][i]['linked_bill_id'] + """\' """)

                                    if(len(repairRes['result']) > 0):
                                        for j in range(len(repairRes['result'])):
                                            expense_res['result'][i].update(
                                                repairRes['result'][j])
                        else:
                            response['result'][i]['expenses'] = []

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
                                if property_res['result'][pr]['management_status'] == 'ACCEPTED' or property_res['result'][pr]['management_status'] == 'OWNER END EARLY' or property_res['result'][pr]['management_status'] == 'PM END EARLY' or property_res['result'][pr]['management_status'] == 'END EARLY':
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
                            time_between_insertion = datetime.now() - \
                                datetime.strptime(
                                maintenance_res['result'][y]['request_created_date'], '%Y-%m-%d %H:%M:%S')
                            if ',' in str(time_between_insertion):
                                maintenance_res['result'][y]['days_open'] = int((str(time_between_insertion).split(',')[
                                    0]).split(' ')[0])
                            else:
                                maintenance_res['result'][y]['days_open'] = 1
                            maintenance_res['result'][y]['quotes'] = list(
                                quotes_res['result'])
                            maintenance_res['result'][y]['total_quotes'] = len(
                                quotes_res['result'])

                        # get utilities or maintenance/repair expenses
                        expense_res = db.execute("""SELECT p.*, pa.*, CONCAT(prop.address," ", prop.unit,", ", prop.city, ", ", prop.state," ", prop.zip) AS address
                            FROM pm.purchases p
                            LEFT JOIN payments pa
                            ON pa.pay_purchase_id = p.purchase_uid
                            LEFT JOIN pm.properties prop
                            ON prop.property_uid LIKE '%""" + property_id + """%'
                            WHERE p.pur_property_id LIKE '%""" + property_id + """%'
                            AND (purchase_type = 'UTILITY' OR  purchase_type = 'MAINTENANCE' OR purchase_type = 'REPAIRS')
                            AND (receiver = \'""" + filterValue + """\' OR payer LIKE '%""" + filterValue + """%')
                            """)
                        if len(expense_res['result']) > 0:
                            response['result'][i]['expenses'] = list(
                                expense_res['result'])
                            for i in range(len(expense_res['result'])):
                                # if utility return all the details related to the utility
                                if expense_res['result'][i]['purchase_type'] == 'UTILITY':
                                    print('in utility')

                                    billRes = db.execute("""SELECT b.*
                                                            FROM pm.bills b                
                                                            WHERE b.bill_uid = \'""" + expense_res['result'][i]['linked_bill_id'] + """\' """)

                                    if(len(billRes['result']) > 0):
                                        for j in range(len(billRes['result'])):
                                            expense_res['result'][i].update(
                                                billRes['result'][j])
                                            # expense_res['result'][i] = (expense_res['result'][i]) + (
                                            #     billRes['result'][j])
                                # if maintainence return all the details related to the maintenance requests
                                elif expense_res['result'][i]['purchase_type'] == 'MAINTENANCE':
                                    print('in maintenance')
                                    maintenanceRes = db.execute("""SELECT mq.*, mr.*, b.*
                                                                    FROM maintenanceQuotes mq
                                                                    LEFT JOIN pm.maintenanceRequests mr
                                                                    ON mr.maintenance_request_uid = mq.linked_request_uid
                                                                    LEFT JOIN pm.businesses b
                                                                    ON b.business_uid = mq.quote_business_uid
                                                                    WHERE  mq.maintenance_quote_uid = \'""" + expense_res['result'][i]['linked_bill_id'] + """\' """)

                                    if(len(maintenanceRes['result']) > 0):
                                        for j in range(len(maintenanceRes['result'])):
                                            expense_res['result'][i].update(
                                                maintenanceRes['result'][j])
                                # if repair return all the details related to the repair requests
                                elif expense_res['result'][i]['purchase_type'] == 'REPAIRS':
                                    print('in maintenance')
                                    repairRes = db.execute("""SELECT mq.*, mr.*, b.*
                                                                    FROM maintenanceQuotes mq
                                                                    LEFT JOIN pm.maintenanceRequests mr
                                                                    ON mr.maintenance_request_uid = mq.linked_request_uid
                                                                    LEFT JOIN pm.businesses b
                                                                    ON b.business_uid = mq.quote_business_uid
                                                                    WHERE  mq.maintenance_quote_uid = \'""" + expense_res['result'][i]['linked_bill_id'] + """\' """)

                                    if(len(repairRes['result']) > 0):
                                        for j in range(len(repairRes['result'])):
                                            expense_res['result'][i].update(
                                                repairRes['result'][j])
                        else:
                            response['result'][i]['expenses'] = []

        return response


class OwnerPropertyBills(Resource):
    def get(self):
        response = {}
        purchase_res = []
        filters = ['owner_id']
        where = {}

        with connect() as db:
            for filter in filters:
                filterValue = request.args.get(filter)
                if filterValue is not None:
                    where[filter] = filterValue
                    today = date.today()
                    # list of all properties for the owner

                    response = db.execute("""SELECT *
                                            FROM pm.properties prop
                                            WHERE prop.owner_id = \'""" + filterValue + """\'
                                            """)
                    for i in range(len(response['result'])):

                        purchase = db.execute("""SELECT prop.property_uid, prop.address, prop.unit, prop.city, prop.state, prop.zip, p.*, pa.*
                                            FROM pm.properties prop
                                            LEFT JOIN
                                            pm.purchases p
                                            ON p.pur_property_id LIKE '%""" + response['result'][i]['property_uid'] + """%'
                                            LEFT JOIN
                                            pm.payments pa
                                            ON pa.pay_purchase_id = p.purchase_uid
                                            WHERE prop.owner_id = \'""" + filterValue + """\'
                                            AND p.payer LIKE '%""" + filterValue + """%'
                                            AND p.purchase_status = 'UNPAID'
                                            AND ({fn MONTHNAME(p.next_payment)} = {fn MONTHNAME(now())} AND YEAR(p.next_payment) = YEAR(now()))
                                            AND (p.purchase_type <> "RENT" AND p.purchase_type <> "EXTRA CHARGES" )""")

                        purchase_res = purchase_res + list(purchase['result'])
                    response['result'] = purchase_res
                    print(purchase_res)
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
                    lease_docs = db.execute("""
                    SELECT prop.*, b.*,r.*, GROUP_CONCAT(lt.linked_tenant_id) as `tenant_id`,
                    GROUP_CONCAT(tpi.tenant_first_name) as `tenant_first_name`,
                    GROUP_CONCAT(tpi.tenant_last_name) as `tenant_last_name`,
                    GROUP_CONCAT(tpi.tenant_email) as `tenant_email`,
                    GROUP_CONCAT(tpi.tenant_phone_number) as `tenant_phone_number`
                    FROM pm.properties prop
                    LEFT JOIN pm.propertyManager propM
                    ON prop.property_uid = propM.linked_property_id
                    LEFT JOIN pm.businesses b
                    ON propM.linked_business_id = b.business_uid
                    LEFT JOIN
                    pm.rentals r
                    ON r.rental_property_id = prop.property_uid
                    LEFT JOIN pm.leaseTenants lt
                    ON lt.linked_rental_uid = r.rental_uid
                    LEFT JOIN pm.tenantProfileInfo tpi
                    ON tpi.tenant_id = lt.linked_tenant_id
                    WHERE prop.owner_id = \'""" + filterValue + """\'
                    AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'PROCESSING' OR r.rental_status='TENTANT APPROVED')
                    GROUP BY lt.linked_rental_uid""")
                    active_lease_docs = []

                    if len(lease_docs['result']) > 0:
                        print('active lease docs')
                        for doc in lease_docs['result']:
                            if len(json.loads(doc['documents'])) > 0:
                                for d in json.loads(doc['documents']):
                                    d['expiry_date'] = doc['lease_end']
                                    d['created_date'] = doc['lease_start']
                                    d['created_by'] = doc['business_name']
                                    d['created_for'] = {'first_name': doc['tenant_first_name'],
                                                        'last_name': doc['tenant_last_name']}
                                    active_lease_docs.append(d)
                    print(active_lease_docs)

                    # list of all expired leases for the owner
                    past_lease_docs = db.execute("""
                    SELECT prop.*, b.*,r.*, GROUP_CONCAT(lt.linked_tenant_id) as `tenant_id`,
                    GROUP_CONCAT(tpi.tenant_first_name) as `tenant_first_name`,
                    GROUP_CONCAT(tpi.tenant_last_name) as `tenant_last_name`,
                    GROUP_CONCAT(tpi.tenant_email) as `tenant_email`,
                    GROUP_CONCAT(tpi.tenant_phone_number) as `tenant_phone_number`
                    FROM pm.properties prop
                    LEFT JOIN pm.propertyManager propM
                    ON prop.property_uid = propM.linked_property_id
                    LEFT JOIN pm.businesses b
                    ON propM.linked_business_id = b.business_uid
                    LEFT JOIN
                    pm.rentals r
                    ON r.rental_property_id = prop.property_uid
                    LEFT JOIN pm.leaseTenants lt
                    ON lt.linked_rental_uid = r.rental_uid
                    LEFT JOIN pm.tenantProfileInfo tpi
                    ON tpi.tenant_id = lt.linked_tenant_id
                    WHERE prop.owner_id = \'""" + filterValue + """\'
                    AND (r.rental_status = 'EXPIRED' OR r.rental_status = 'TERMINATED')
                    GROUP BY lt.linked_rental_uid""")

                    expired_lease_docs = []
                    if len(past_lease_docs['result']) > 0:
                        print('expired lease docs')
                        for doc in past_lease_docs['result']:
                            if len(json.loads(doc['documents'])) > 0:
                                for d in json.loads(doc['documents']):
                                    d['expiry_date'] = doc['lease_end']
                                    d['created_date'] = doc['lease_start']
                                    d['created_by'] = doc['business_name']
                                    d['created_for'] = {'first_name': doc['tenant_first_name'],
                                                        'last_name': doc['tenant_last_name']}
                                    expired_lease_docs.append(d)
                    print(expired_lease_docs)

                    # list of all active pm contracts for the owner
                    manager_docs = db.execute("""
                    SELECT prop.*,b.*,c.*,u.*
                    FROM pm.properties prop
                    LEFT JOIN pm.contracts c
                    ON c.property_uid = prop.property_uid
                    LEFT JOIN pm.propertyManager propM
                    ON prop.property_uid = propM.linked_property_id
                    LEFT JOIN pm.businesses b
                    ON propM.linked_business_id = b.business_uid
                    LEFT JOIN pm.users u
                    ON prop.owner_id = u.user_uid
                    WHERE prop.owner_id = \'""" + filterValue + """\'
                    AND (propM.management_status= 'ACCEPTED' OR propM.management_status='END EARLY' OR propM.management_status='PM END EARLY' OR propM.management_status='OWNER END EARLY')
                    AND c.business_uid = propM.linked_business_id""")

                    active_manager_docs = []
                    if len(manager_docs['result']) > 0:
                        print('active manager docs')
                        for doc in manager_docs['result']:
                            if len(json.loads(doc['documents'])) > 0:
                                for d in json.loads(doc['documents']):
                                    d['expiry_date'] = doc['end_date']
                                    d['created_date'] = doc['start_date']
                                    d['created_by'] = doc['first_name'] + \
                                        ' ' + doc['last_name']
                                    d['created_for'] = doc['business_name']
                                    active_manager_docs.append(d)

                    print(active_manager_docs)

                    # list of all active pm contracts for the owner
                    past_manager_docs = db.execute("""
                    SELECT prop.*,b.*,c.*,u.*
                    FROM pm.properties prop
                    LEFT JOIN pm.contracts c
                    ON c.property_uid = prop.property_uid
                    LEFT JOIN pm.propertyManager propM
                    ON prop.property_uid = propM.linked_property_id
                    LEFT JOIN pm.businesses b
                    ON propM.linked_business_id = b.business_uid
                    LEFT JOIN pm.users u
                    ON prop.owner_id = u.user_uid
                    WHERE prop.owner_id = \'""" + filterValue + """\'
                    AND propM.management_status <> 'ACCEPTED'
                    AND c.business_uid = propM.linked_business_id""")

                    expired_manager_docs = []
                    if len(past_manager_docs['result']) > 0:
                        print('past manager docs')
                        for doc in past_manager_docs['result']:
                            if len(json.loads(doc['documents'])) > 0:
                                for d in json.loads(doc['documents']):
                                    d['expiry_date'] = doc['end_date']
                                    d['created_date'] = doc['start_date']
                                    d['created_by'] = doc['first_name'] + \
                                        ' ' + doc['last_name']
                                    d['created_for'] = doc['business_name']
                                    expired_manager_docs.append(d)
                    print(expired_manager_docs)

                    response['result'] = [{
                        'active_lease_docs': list(active_lease_docs),
                        'past_lease_docs': list(expired_lease_docs),
                        'active_manager_docs': list(active_manager_docs),
                        'past_manager_docs': list(expired_manager_docs)
                    }]

        return response
