from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from data import connect, uploadImage
import boto3
import json
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import calendar


class TenantDashboard(Resource):
    decorators = [jwt_required()]

    def get(self):
        res = {}
        user = get_jwt_identity()
        where = {'tenant_id': user['user_uid']}
        with connect() as db:
            res = db.select('tenantProfileInfo', where)
            print('user_id:', user['user_uid'])
            response = db.execute(""" SELECT * FROM pm.properties
                                        LEFT JOIN pm.rentals
                                        ON rental_property_id = property_uid
                                        LEFT JOIN pm.leaseTenants
                                        ON linked_rental_uid = rental_uid
                                        LEFT JOIN pm.propertyManager p
                                        ON linked_property_id = property_uid
                                        WHERE linked_tenant_id = \'""" + user['user_uid'] + """\' AND rental_status = 'ACTIVE' AND (p.management_status = 'ACCEPTED' OR p.management_status='END EARLY' OR p.management_status='PM END EARLY' OR p.management_status='OWNER END EARLY')  ; """)

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
                                            AND (pm.management_status = 'ACCEPTED' OR pm.management_status='END EARLY' OR pm.management_status='PM END EARLY' OR pm.management_status='OWNER END EARLY')   """)

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
                                                        WHERE p.pur_property_id LIKE '%""" + property_id + """%'
                                                        AND p.payer LIKE '%""" + user['user_uid'] + """%'
                                                        AND (p.purchase_type= "RENT" OR p.purchase_type= "EXTRA CHARGES" OR p.purchase_type= "UTILITY")""")
                response['result'][i]['tenantExpenses'] = []
                if len(tenant_expenses['result']) > 0:
                    num_days = []
                    date = []
                    for ore in range(len(tenant_expenses['result'])):
                        print('here', tenant_expenses['result'][ore])
                        time_between_insertion = datetime.now() - \
                            datetime.strptime(
                                tenant_expenses['result'][ore]['next_payment'], '%Y-%m-%d %H:%M:%S')
                        print(time_between_insertion)
                        # if older than 30 days
                        if time_between_insertion.days > 30:
                            print('older than 30 days')
                            # if unpaid then all
                            if tenant_expenses['result'][ore]['purchase_status'] == 'UNPAID':
                                response['result'][i]['tenantExpenses'].append(
                                    (tenant_expenses['result'][ore]))
                        # if in future
                        elif time_between_insertion.days < 0:
                            print('in future')
                            # if utility or extra charges then all
                            if tenant_expenses['result'][ore]['purchase_type'] != 'RENT':
                                print('here no rents')
                                print(
                                    'appended from here', tenant_expenses['result'][ore]['purchase_type'])
                                if tenant_expenses['result'][ore]['purchase_frequency'] != 'Monthly':
                                    print(
                                        'appended from here purchase_frequency not monthly', tenant_expenses['result'][ore]['purchase_frequency'])
                                    response['result'][i]['tenantExpenses'].append(
                                        (tenant_expenses['result'][ore]))
                                else:
                                    print(
                                        'appended from here monthly', tenant_expenses['result'][ore]['purchase_frequency'])
                                    num_days.append(datetime.strptime(
                                        tenant_expenses['result'][ore]['next_payment'], '%Y-%m-%d %H:%M:%S'))
                            # add time differences in date, if rent get the most recent upcoming
                            else:

                                date.append(datetime.strptime(
                                    tenant_expenses['result'][ore]['next_payment'], '%Y-%m-%d %H:%M:%S'))
                        # if in the last 30 days
                        elif 0 <= time_between_insertion.days < 30:
                            print('not older than 30 days not in future',
                                  time_between_insertion)

                            response['result'][i]['tenantExpenses'].append(
                                (tenant_expenses['result'][ore]))
                        # nothing if anything else
                        else:
                            print('not older than 30 days',
                                  time_between_insertion.days)

                for ore in range(len(tenant_expenses['result'])):
                    # upcoming 1 rent in the future
                    if tenant_expenses['result'][ore]['purchase_type'] == 'RENT':
                        if len(date) > 0:
                            if datetime.strftime(min(
                                    date, key=lambda d: abs(d - datetime.now())), '%Y-%m-%d %H:%M:%S') == tenant_expenses['result'][ore]['next_payment']:
                                print('next payment due',
                                      tenant_expenses['result'][ore])
                                response['result'][i]['tenantExpenses'].append(
                                    (tenant_expenses['result'][ore]))
                    else:
                        if len(num_days) > 0:
                            if datetime.strftime(min(
                                    num_days, key=lambda d: abs(d - datetime.now())), '%Y-%m-%d %H:%M:%S') == tenant_expenses['result'][ore]['next_payment']:
                                print('next payment due',
                                      tenant_expenses['result'][ore])
                                response['result'][i]['tenantExpenses'].append(
                                    (tenant_expenses['result'][ore]))
                # for ore in range(len(tenant_expenses['result'])):
                #     # upcoming 1 rent in the future

                #     if datetime.strftime(min(
                #             num_days, key=lambda d: abs(d - datetime.now())), '%Y-%m-%d %H:%M:%S') == tenant_expenses['result'][ore]['next_payment']:
                #         print('next payment due',
                #               tenant_expenses['result'][ore])
                #         response['result'][i]['tenantExpenses'].append(
                #             (tenant_expenses['result'][ore]))
                print('tenantExpenses',
                      response['result'][i]['tenantExpenses'])

            res['result'][0]['properties'] = list(response['result'])

        return res


class OwnerDashboard(Resource):
    decorators = [jwt_required()]

    def get(self):
        response = {}
        user = get_jwt_identity()
        where = {'owner_id': user['user_uid']}

        with connect() as db:

            today = date.today()
            # list of all properties for the owner
            response = db.execute(
                """SELECT * FROM pm.properties p WHERE p.owner_id = \'"""
                + user['user_uid']
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
                                                AND p.receiver = \'""" + user['user_uid'] + """\'
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
                                                AND p.payer LIKE '%""" + user['user_uid'] + """%'
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
                                                AND p.receiver = \'""" + user['user_uid'] + """\'
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
                                                AND (payer LIKE '%""" + user['user_uid'] + """%') """)
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
                                                AND payer LIKE '%""" + user['user_uid'] + """%'
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
                    AND (receiver = \'""" + user['user_uid'] + """\' OR payer LIKE '%""" + user['user_uid'] + """%')
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


class ManagerDashboard(Resource):

    decorators = [jwt_required()]

    def get(self):
        response = {}
        user = get_jwt_identity()
        buid = ''
        for business in user['businesses']:
            # print(business)
            if business['business_type'] == 'MANAGEMENT' and business['employee_role'] == 'Owner':
                buid = business['business_uid']
                # print(buid)
        # print('buid', buid)
        with connect() as db:

            today = date.today()

            response = db.execute("""SELECT *
                                    FROM pm.propertyInfo
                                    WHERE management_status <> 'REJECTED'
                                    AND management_status <> 'TERMINATED'
                                    AND management_status <> 'EXPIRED'
                                    AND manager_id = \'""" + buid + """\' """)

            for i in range(len(response['result'])):
                property_id = response['result'][i]['property_uid']
                print(property_id)

                # rental_revenue = 0
                # extraCharges_revenue = 0
                # utility_revenue = 0
                # maintenance_expenses = 0
                # management_expenses = 0
                # repairs_expenses = 0
                # rental_expected_revenue = 0
                # extraCharges_expected_revenue = 0
                # utility_expected_revenue = 0
                # maintenance_expected_expenses = 0
                # management_expected_expenses = 0
                # repairs_expected_expenses = 0
                # get tenant applications
                application_res = db.execute("""SELECT
                                                    *
                                                    FROM pm.applications WHERE property_uid = \'""" + property_id + """\'""")

                response['result'][i]['applications'] = list(
                    application_res['result'])

                # get maintenance requests
                maintenance_res = db.execute("""SELECT *
                                                    FROM pm.maintenanceRequests mr
                                                    WHERE mr.property_uid = \'""" + property_id + """\'
                                                    """)
                response['result'][i]['maintenanceRequests'] = list(
                    maintenance_res['result'])
                if len(maintenance_res['result']) > 0:
                    num_days = []
                    for mr in maintenance_res['result']:
                        num_days.append(datetime.strptime(
                            mr['request_created_date'], '%Y-%m-%d %H:%M:%S'))

                    for mr in maintenance_res['result']:
                        if len(num_days) > 0:
                            if datetime.strftime(max(
                                    num_days, key=lambda d: abs(d - datetime.now())), '%Y-%m-%d %H:%M:%S') == mr['request_created_date']:

                                time_between_insertion = datetime.now() - \
                                    datetime.strptime(
                                    mr['request_created_date'], '%Y-%m-%d %H:%M:%S')

                                response['result'][i]['oldestOpenMR'] = str(time_between_insertion).split(',')[
                                    0]
                else:
                    response['result'][i]['oldestOpenMR'] = ''
                rent_status_result = db.execute("""SELECT *
                                                FROM pm.purchases p
                                                LEFT JOIN
                                                pm.payments pa
                                                ON pa.pay_purchase_id = p.purchase_uid
                                                LEFT JOIN rentals r
                                                ON r.rental_property_id LIKE '%""" + property_id + """%'
                                                WHERE p.pur_property_id LIKE '%""" + property_id + """%'
                                                AND ({fn MONTHNAME(p.next_payment)} = {fn MONTHNAME(now())} AND YEAR(p.next_payment) = YEAR(now()))
                                                AND p.purchase_type= "RENT"
                                                AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED')
                                                AND p.receiver = \'""" + buid + """\'""")
                if len(rent_status_result['result']) > 0:
                    response['result'][i]['rent_status'] = rent_status_result['result'][0]['purchase_status']
                    rent_payments = json.loads(
                        rent_status_result['result'][0]['rent_payments'])
                    for r in range(len(rent_payments)):

                        print(rent_payments[r])
                        if rent_payments[r]['fee_name'] == 'Rent':
                            charge_date = date.today()
                            due_date = charge_date.replace(
                                day=int(rent_payments[r]['due_by']))
                            print(due_date)
                            late_date = due_date + \
                                relativedelta(
                                    days=int(rent_payments[r]['late_by']))
                            print(rent_payments[r]['late_by'], late_date)
                            response['result'][i]['late_date'] = late_date.isoformat()
                else:
                    response['result'][i]['rent_status'] = 'NOT RENTED'
                    response['result'][i]['late_date'] = ''
                rental_revenue = 0
                extraCharges_revenue = 0
                utility_revenue = 0

                maintenance_expenses = 0
                management_expenses = 0
                repairs_expenses = 0
                utility_expenses = 0

                rental_expected_revenue = 0
                extraCharges_expected_revenue = 0
                utility_expected_revenue = 0

                maintenance_expected_expenses = 0
                management_expected_expenses = 0
                repairs_expected_expenses = 0
                utility_expected_expenses = 0

                yearCal = today.month - \
                    (datetime.strptime(
                        response['result'][i]['active_date'], '%Y-%m-%d')).month

                weeks_current_month = len(
                    calendar.monthcalendar(2022, int(today.strftime("%m"))))

                weeks_active = round((abs(today - datetime.strptime(
                    response['result'][i]['active_date'], '%Y-%m-%d').date()).days)/7, 1)

                # monthly revenue for the property
                manager_revenue = db.execute("""SELECT *
                                                FROM pm.purchases p
                                                LEFT JOIN
                                                pm.payments pa
                                                ON pa.pay_purchase_id = p.purchase_uid
                                                LEFT JOIN rentals r
                                                ON r.rental_property_id LIKE '%""" + property_id + """%'
                                                WHERE p.pur_property_id LIKE '%""" + property_id + """%'
                                                AND ({fn MONTHNAME(p.next_payment)} = {fn MONTHNAME(now())} AND YEAR(p.next_payment) = YEAR(now()))
                                                AND (p.purchase_type= "RENT" OR p.purchase_type= "EXTRA CHARGES" OR p.purchase_type= 'UTILITY')
                                                AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED')
                                                AND p.receiver = \'""" + buid + """\'
                                                AND p.purchase_status = 'PAID' """)
                response['result'][i]['manager_revenue'] = list(
                    manager_revenue['result'])

                if len(manager_revenue['result']) > 0:
                    for mre in range(len(manager_revenue['result'])):

                        weeks_current_month = len(calendar.monthcalendar(
                            2022, int(today.strftime("%m"))))

                        if manager_revenue['result'][mre]['purchase_type'] == 'RENT':
                            if manager_revenue['result'][mre]['purchase_frequency'] == 'Weekly':

                                rental_revenue = rental_revenue + \
                                    weeks_current_month*int(manager_revenue['result']
                                                            [mre]['amount_paid'])
                            elif manager_revenue['result'][mre]['purchase_frequency'] == 'Biweekly':

                                rental_revenue = rental_revenue + \
                                    weeks_current_month/2 * \
                                    int(manager_revenue['result']
                                        [mre]['amount_paid'])
                            elif manager_revenue['result'][mre]['purchase_frequency'] == 'Monthly':

                                rental_revenue = rental_revenue + \
                                    manager_revenue['result'][mre]['amount_paid']

                            elif manager_revenue['result'][mre]['purchase_frequency'] == 'Annually':

                                rental_revenue = rental_revenue + \
                                    manager_revenue['result'][mre]['amount_paid']
                            else:

                                rental_revenue = rental_revenue + \
                                    manager_revenue['result'][mre]['amount_paid']

                        if manager_revenue['result'][mre]['purchase_type'] == 'EXTRA CHARGES':
                            if manager_revenue['result'][mre]['purchase_frequency'] == 'Weekly':

                                extraCharges_revenue = extraCharges_revenue + \
                                    weeks_current_month*int(manager_revenue['result']
                                                            [mre]['amount_paid'])
                            elif manager_revenue['result'][mre]['purchase_frequency'] == 'Biweekly':

                                extraCharges_revenue = extraCharges_revenue + \
                                    weeks_current_month/2 * \
                                    int(manager_revenue['result']
                                        [mre]['amount_paid'])
                            elif manager_revenue['result'][mre]['purchase_frequency'] == 'Monthly':

                                extraCharges_revenue = extraCharges_revenue + \
                                    manager_revenue['result'][mre]['amount_paid']
                            elif manager_revenue['result'][mre]['purchase_frequency'] == 'Annually':

                                extraCharges_revenue = extraCharges_revenue + \
                                    manager_revenue['result'][mre]['amount_paid']
                            else:

                                extraCharges_revenue = extraCharges_revenue + \
                                    manager_revenue['result'][mre]['amount_paid']
                        if manager_revenue['result'][mre]['purchase_type'] == 'UTILITY':
                            if manager_revenue['result'][mre]['purchase_frequency'] == 'Weekly':

                                utility_revenue = utility_revenue + \
                                    float(manager_revenue['result']
                                          [mre]['amount_paid'])
                            elif manager_revenue['result'][mre]['purchase_frequency'] == 'Biweekly':

                                utility_revenue = utility_revenue + \
                                    float(manager_revenue['result']
                                          [mre]['amount_paid'])
                            elif manager_revenue['result'][mre]['purchase_frequency'] == 'Monthly':

                                utility_revenue = utility_revenue + \
                                    manager_revenue['result'][mre]['amount_paid']
                            elif manager_revenue['result'][mre]['purchase_frequency'] == 'Annually':

                                utility_revenue = utility_revenue + \
                                    manager_revenue['result'][mre]['amount_paid']
                            else:

                                utility_revenue = utility_revenue + \
                                    manager_revenue['result'][mre]['amount_paid']

                response['result'][i]['rental_revenue'] = round(
                    rental_revenue, 2)
                response['result'][i]['extraCharges_revenue'] = round(
                    extraCharges_revenue, 2)
                response['result'][i]['utility_revenue'] = round(
                    utility_revenue, 2)

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
                                            AND (p.purchase_type= "RENT" OR p.purchase_type = "MAINTENANCE" OR p.purchase_type = 'REPAIRS' OR p.purchase_type = "UTILITY")
                                            AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED')
                                            AND (receiver = \'""" + buid + """\' OR payer LIKE '%""" + buid + """%')
                                            AND p.purchase_status = 'PAID'""")

                response['result'][i]['manager_expense'] = (list(
                    manager_expense['result']))
                if len(manager_expense['result']) > 0:
                    for mex in range(len(manager_expense['result'])):
                        # print('mex', manager_expense['result'][mex])
                        # if maintenance
                        if manager_expense['result'][mex]['purchase_type'] == 'MAINTENANCE':
                            #
                            # if maintenance monthly
                            if manager_expense['result'][mex]['purchase_frequency'] == 'Monthly':
                                # print('in maintenance monthly')
                                # if maintenance monthly once a month
                                if manager_expense['result'][mex]['payment_frequency'] == 'Once a month':
                                    # print('in maintenance once a month')

                                    maintenance_expenses = maintenance_expenses + \
                                        manager_expense['result'][mex]['amount_paid']
                                    # if maintenance monthly twice a month
                                elif manager_expense['result'][mex]['payment_frequency'] == 'Twice a month':
                                    # print(
                                    # 'in maintenance twice a month')

                                    maintenance_expenses = maintenance_expenses + \
                                        2 * \
                                        (manager_expense['result']
                                            [mex]['amount_paid'])
                                else:
                                    print('do nothing')
                                # if maintenance annually
                            elif manager_expense['result'][mex]['purchase_frequency'] == 'Annually':
                                # print('in maintenance annually')
                                # if maintenance annually once a year
                                if manager_expense['result'][mex]['payment_frequency'] == 'Once a year':

                                    maintenance_expenses = maintenance_expenses + \
                                        manager_expense['result'][mex]['amount_paid']
                                # if maintenance annually twice a year
                                elif manager_expense['result'][mex]['payment_frequency'] == 'Twice a year':

                                    maintenance_expenses = maintenance_expenses + \
                                        manager_expense['result'][mex]['amount_paid']
                                else:
                                    print('do nothing')
                            # if maintenance one-time
                            else:
                                maintenance_expenses = maintenance_expenses + \
                                    manager_expense['result'][mex]['amount_paid']

                        if manager_expense['result'][mex]['purchase_type'] == 'REPAIRS':
                            # if repairs monthly
                            if manager_expense['result'][mex]['purchase_frequency'] == 'Monthly':
                                # if repairs monthly once a month
                                if manager_expense['result'][mex]['payment_frequency'] == 'Once a month':

                                    repairs_expenses = repairs_expenses + \
                                        manager_expense['result'][mex]['amount_paid']
                                    # if repairs monthly twice a month
                                elif manager_expense['result'][mex]['payment_frequency'] == 'Twice a month':

                                    repairs_expenses = repairs_expenses + 2 * \
                                        (manager_expense['result']
                                            [mex]['amount_paid'])
                                else:
                                    print('do nothing')
                                # if repairs annually
                            elif manager_expense['result'][mex]['purchase_frequency'] == 'Annually':
                                # if repairs annually once a year
                                if manager_expense['result'][mex]['payment_frequency'] == 'Once a year':

                                    repairs_expenses = repairs_expenses + \
                                        manager_expense['result'][mex]['amount_paid']
                                # if repairs annually twice a year
                                elif manager_expense['result'][mex]['payment_frequency'] == 'Twice a year':

                                    repairs_expenses = repairs_expenses + \
                                        manager_expense['result'][mex]['amount_paid']
                                else:
                                    print('do nothing')
                            # if repairs one-time
                            else:
                                repairs_expenses = repairs_expenses + \
                                    manager_expense['result'][mex]['amount_paid']

                        if manager_expense['result'][mex]['purchase_type'] == 'UTILITY':
                            if manager_expense['result'][mex]['purchase_frequency'] == 'Weekly':

                                utility_expenses = utility_expenses + \
                                    float(manager_expense['result']
                                          [mex]['amount_paid'])
                            elif manager_expense['result'][mex]['purchase_frequency'] == 'Biweekly':

                                utility_expenses = utility_expenses + \
                                    float(manager_expense['result']
                                          [mex]['amount_paid'])
                            elif manager_expense['result'][mex]['purchase_frequency'] == 'Monthly':

                                utility_expenses = utility_expenses + \
                                    manager_expense['result'][mex]['amount_paid']
                            elif manager_expense['result'][mex]['purchase_frequency'] == 'Annually':

                                utility_expenses = utility_expenses + \
                                    manager_expense['result'][mex]['amount_paid']
                            else:

                                utility_expenses = utility_expenses + \
                                    manager_expense['result'][mex]['amount_paid']
                        # if management
                        if manager_expense['result'][mex]['purchase_type'] == 'RENT':
                            managementPayments = json.loads(
                                manager_expense['result'][mex]['contract_fees'])

                            for payment in managementPayments:
                                # print('amount paid to owner', payment)
                                if payment['fee_type'] == '%':

                                    if payment['of'] == 'Gross Rent':

                                        if payment['frequency'] == 'Weekly':

                                            management_expenses = management_expenses +  \
                                                weeks_current_month*float((
                                                    float(manager_expense['result'][mex]['amount_paid']) * float(payment['charge']))/100)

                                        elif payment['frequency'] == 'Biweekly':

                                            management_expenses = management_expenses +  \
                                                weeks_current_month/2 * \
                                                ((
                                                    float(manager_expense['result'][mex]['amount_paid']) * float(payment['charge']))/100)

                                        elif payment['frequency'] == 'Monthly':

                                            management_expenses = management_expenses +  \
                                                (
                                                    float(manager_expense['result'][mex]['amount_paid']) * float(payment['charge']))/100

                                        elif payment['frequency'] == 'Annually':

                                            if date.fromisoformat(manager_expense['result'][mex]['start_date']).month == today.month:
                                                management_expenses = management_expenses +  \
                                                    (
                                                        float(manager_expense['result'][mex]['amount_paid']) * float(payment['charge']))/100

                                        elif payment['frequency'] == 'One-time':

                                            if date.fromisoformat(manager_expense['result'][mex]['start_date']).month == today.month:
                                                management_expenses = management_expenses +  \
                                                    (
                                                        float(manager_expense['result'][mex]['amount_paid']) * float(payment['charge']))/100

                                        else:
                                            print('do nothing')
                                elif payment['fee_type'] == '$':
                                    if payment['frequency'] == 'Weekly':

                                        management_expenses = management_expenses + weeks_current_month * \
                                            float(payment['charge'])

                                    elif payment['frequency'] == 'Biweekly':

                                        management_expenses = management_expenses + weeks_current_month/2 * \
                                            float(payment['charge'])

                                    elif payment['frequency'] == 'Monthly':

                                        management_expenses = management_expenses + \
                                            float(payment['charge'])

                                    elif payment['frequency'] == 'Annually':

                                        if date.fromisoformat(manager_expense['result'][mex]['start_date']).month == today.month:
                                            management_expenses = management_expenses + \
                                                float(
                                                    payment['charge'])

                                    elif payment['frequency'] == 'One-time':

                                        if date.fromisoformat(manager_expense['result'][mex]['start_date']).month == today.month:
                                            management_expenses = management_expenses + \
                                                float(
                                                    payment['charge'])

                                    else:
                                        print('do nothing')
                                else:
                                    print('do nothing')

                    response['result'][i]['maintenance_expenses'] = round(
                        maintenance_expenses, 2)
                    response['result'][i]['management_expenses'] = abs(round((float(manager_expense['result'][mex]['amount_paid']) -
                                                                              management_expenses), 2))
                    response['result'][i]['repairs_expenses'] = round(
                        repairs_expenses, 2)
                    response['result'][i]['utility_expenses'] = round(
                        utility_expenses, 2)

                # monthly revenue for the property
                manager_expected_revenue = db.execute("""SELECT *
                                                FROM pm.purchases p
                                                LEFT JOIN
                                                pm.payments pa
                                                ON pa.pay_purchase_id = p.purchase_uid
                                                LEFT JOIN rentals r
                                                ON r.rental_property_id LIKE '%""" + property_id + """%'
                                                WHERE p.pur_property_id LIKE '%""" + property_id + """%'
                                                AND ({fn MONTHNAME(p.next_payment)} = {fn MONTHNAME(now())} AND YEAR(p.next_payment) = YEAR(now()))
                                                AND (p.purchase_type= "RENT" OR p.purchase_type= "EXTRA CHARGES" OR p.purchase_type= 'UTILITY')
                                                AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED') AND receiver = \'""" + buid + """\'  """)
                response['result'][i]['manager_expected_revenue'] = list(
                    manager_expected_revenue['result'])

                if len(manager_expected_revenue['result']) > 0:
                    for mex in range(len(manager_expected_revenue['result'])):

                        weeks_current_month = len(calendar.monthcalendar(
                            2022, int(today.strftime("%m"))))

                        if manager_expected_revenue['result'][mex]['purchase_type'] == 'RENT':
                            if manager_expected_revenue['result'][mex]['purchase_frequency'] == 'Weekly':

                                rental_expected_revenue = rental_expected_revenue + \
                                    weeks_current_month*int(manager_expected_revenue['result']
                                                            [mex]['amount_due'])
                            elif manager_expected_revenue['result'][mex]['purchase_frequency'] == 'Biweekly':

                                rental_expected_revenue = rental_expected_revenue + \
                                    weeks_current_month/2 * \
                                    int(manager_expected_revenue['result']
                                        [mex]['amount_due'])
                            elif manager_expected_revenue['result'][mex]['purchase_frequency'] == 'Monthly':

                                rental_expected_revenue = rental_expected_revenue + \
                                    manager_expected_revenue['result'][mex]['amount_due']
                            elif manager_expected_revenue['result'][mex]['purchase_frequency'] == 'Annually':

                                rental_expected_revenue = rental_expected_revenue + \
                                    manager_expected_revenue['result'][mex]['amount_due']
                            else:

                                rental_expected_revenue = rental_expected_revenue + \
                                    manager_expected_revenue['result'][mex]['amount_due']

                        if manager_expected_revenue['result'][mex]['purchase_type'] == 'EXTRA CHARGES':
                            if manager_expected_revenue['result'][mex]['purchase_frequency'] == 'Weekly':

                                extraCharges_expected_revenue = extraCharges_expected_revenue + \
                                    weeks_current_month*int(manager_expected_revenue['result']
                                                            [mex]['amount_due'])
                            elif manager_expected_revenue['result'][mex]['purchase_frequency'] == 'Biweekly':

                                extraCharges_expected_revenue = extraCharges_expected_revenue + \
                                    weeks_current_month/2 * \
                                    int(manager_expected_revenue['result']
                                        [mex]['amount_due'])
                            elif manager_expected_revenue['result'][mex]['purchase_frequency'] == 'Monthly':

                                extraCharges_expected_revenue = extraCharges_expected_revenue + \
                                    manager_expected_revenue['result'][mex]['amount_due']
                            elif manager_expected_revenue['result'][mex]['purchase_frequency'] == 'Annually':

                                extraCharges_expected_revenue = extraCharges_expected_revenue + \
                                    manager_expected_revenue['result'][mex]['amount_due']
                            else:

                                extraCharges_expected_revenue = extraCharges_expected_revenue + \
                                    manager_expected_revenue['result'][mex]['amount_due']
                        # calculate revenue from UTILITY payments
                        if manager_expected_revenue['result'][mex]['purchase_type'] == 'UTILITY':
                            if manager_expected_revenue['result'][mex]['purchase_frequency'] == 'Weekly':

                                utility_expected_revenue = utility_expected_revenue + \
                                    float(manager_expected_revenue['result']
                                          [mex]['amount_due'])
                            elif manager_expected_revenue['result'][mex]['purchase_frequency'] == 'Biweekly':

                                utility_expected_revenue = utility_expected_revenue + \
                                    float(manager_expected_revenue['result']
                                          [mex]['amount_due'])
                            elif manager_expected_revenue['result'][mex]['purchase_frequency'] == 'Monthly':

                                utility_expected_revenue = utility_expected_revenue + \
                                    manager_expected_revenue['result'][mex]['amount_due']
                            elif manager_expected_revenue['result'][mex]['purchase_frequency'] == 'Annually':

                                utility_expected_revenue = utility_expected_revenue + \
                                    manager_expected_revenue['result'][mex]['amount_due']
                            else:

                                utility_expected_revenue = utility_expected_revenue + \
                                    manager_expected_revenue['result'][mex]['amount_due']
                response['result'][i]['rental_expected_revenue'] = round(
                    rental_expected_revenue, 2)
                response['result'][i]['extraCharges_expected_revenue'] = round(
                    extraCharges_expected_revenue, 2)
                response['result'][i]['utility_expected_revenue'] = round(
                    utility_expected_revenue, 2)

                # monthly expense for the property
                manager_expected_expense = db.execute("""SELECT *
                FROM pm.purchases p
                LEFT JOIN
                pm.payments pa
                ON pa.pay_purchase_id = p.purchase_uid
                LEFT JOIN pm.rentals r
                ON r.rental_property_id LIKE '%""" + property_id + """%'
                LEFT JOIN pm.contracts c
                ON c.property_uid LIKE '%""" + property_id + """%'
                WHERE p.pur_property_id LIKE '%""" + property_id + """%'
                AND c.contract_status = 'ACTIVE'
                AND ({fn MONTHNAME(p.next_payment)} = {fn MONTHNAME(now())} AND YEAR(p.next_payment) = YEAR(now()))
                AND (p.purchase_type= "RENT" OR p.purchase_type = "MAINTENANCE" OR p.purchase_type = 'REPAIRS' OR p.purchase_type = 'UTILITY' )
                AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED') 
                AND (receiver = \'""" + buid + """\' OR payer LIKE '%""" + buid + """%')""")
                response['result'][i]['manager_expected_expense'] = list(
                    manager_expected_expense['result'])

                if len(manager_expected_expense['result']) > 0:
                    for mee in range(len(manager_expected_expense['result'])):
                        # if maintenance
                        if manager_expected_expense['result'][mee]['purchase_type'] == 'MAINTENANCE':
                            print('in maintenance')
                            # if maintenance monthly
                            if manager_expected_expense['result'][mee]['purchase_frequency'] == 'Monthly':
                                print('in maintenance monthly')
                                # if maintenance monthly once a month
                                if manager_expected_expense['result'][mee]['payment_frequency'] == 'Once a month' or manager_expected_expense['result'][mee]['payment_frequency'] is None:
                                    print('in maintenance once a month')

                                    maintenance_expected_expenses = maintenance_expected_expenses + \
                                        manager_expected_expense['result'][mee]['amount_due']
                                    # if maintenance monthly twice a month
                                elif manager_expected_expense['result'][mee]['payment_frequency'] == 'Twice a month':

                                    maintenance_expected_expenses = maintenance_expected_expenses + \
                                        2 * \
                                        (manager_expected_expense['result']
                                            [mee]['amount_due'])
                                else:
                                    print('do nothing')
                                # if maintenance annually
                            elif manager_expected_expense['result'][mee]['purchase_frequency'] == 'Annually':
                                print('in maintenance annually')
                                # if maintenance annually once a year
                                if manager_expected_expense['result'][mee]['payment_frequency'] == 'Once a year':

                                    maintenance_expected_expenses = maintenance_expected_expenses + \
                                        manager_expected_expense['result'][mee]['amount_due']
                                # if maintenance annually twice a year
                                elif manager_expected_expense['result'][mee]['payment_frequency'] == 'Twice a year':

                                    maintenance_expected_expenses = maintenance_expected_expenses + \
                                        manager_expected_expense['result'][mee]['amount_due']
                                else:
                                    print('do nothing')
                            # if maintenance one-time
                            else:

                                maintenance_expected_expenses = maintenance_expected_expenses + \
                                    manager_expected_expense['result'][mee]['amount_due']
                        # if management
                        if manager_expected_expense['result'][mee]['purchase_type'] == 'RENT':
                            managementPayments = json.loads(
                                manager_expected_expense['result'][mee]['contract_fees'])

                            for payment in managementPayments:
                                # print('amount paid to owner', payment)
                                if payment['fee_type'] == '%':
                                    if payment['of'] == 'Gross Rent':

                                        if payment['frequency'] == 'Weekly':

                                            management_expected_expenses = management_expected_expenses +  \
                                                weeks_current_month*float((
                                                    float(manager_expected_expense['result'][mee]['amount_due']) * float(payment['charge']))/100)

                                        elif payment['frequency'] == 'Biweekly':

                                            management_expected_expenses = management_expected_expenses +  \
                                                weeks_current_month/2 * \
                                                ((
                                                    float(manager_expected_expense['result'][mee]['amount_due']) * float(payment['charge']))/100)

                                        elif payment['frequency'] == 'Monthly':

                                            management_expected_expenses = management_expected_expenses +  \
                                                (
                                                    float(manager_expected_expense['result'][mee]['amount_due']) * float(payment['charge']))/100

                                        elif payment['frequency'] == 'Annually':

                                            if date.fromisoformat(manager_expected_expense['result'][mee]['start_date']).month == today.month:
                                                management_expected_expenses = management_expected_expenses +  \
                                                    (
                                                        float(manager_expected_expense['result'][mee]['amount_due']) * float(payment['charge']))/100

                                        elif payment['frequency'] == 'One-time':

                                            if date.fromisoformat(manager_expected_expense['result'][mee]['start_date']).month == today.month:
                                                management_expected_expenses = management_expected_expenses +  \
                                                    (
                                                        float(manager_expected_expense['result'][mee]['amount_due']) * float(payment['charge']))/100

                                        else:
                                            print('do nothing')
                                elif payment['fee_type'] == '$':
                                    if payment['frequency'] == 'Weekly':

                                        management_expected_expenses = management_expected_expenses + weeks_current_month * \
                                            float(payment['charge'])

                                    elif payment['frequency'] == 'Biweekly':

                                        management_expected_expenses = management_expected_expenses + weeks_current_month/2 * \
                                            float(payment['charge'])

                                    elif payment['frequency'] == 'Monthly':

                                        management_expected_expenses = management_expected_expenses + \
                                            float(payment['charge'])

                                    elif payment['frequency'] == 'Annually':

                                        if date.fromisoformat(manager_expected_expense['result'][mee]['start_date']).month == today.month:
                                            management_expected_expenses = management_expected_expenses + \
                                                float(
                                                    payment['charge'])

                                    elif payment['frequency'] == 'One-time':

                                        if date.fromisoformat(manager_expected_expense['result'][mee]['start_date']).month == today.month:
                                            management_expected_expenses = management_expected_expenses + \
                                                float(
                                                    payment['charge'])

                                    else:
                                        print('do nothing')
                                else:
                                    print('do nothing')
                        if manager_expected_expense['result'][mee]['purchase_type'] == 'REPAIRS':
                            # if repairs monthly
                            if manager_expected_expense['result'][mee]['purchase_frequency'] == 'Monthly':
                                # if repairs monthly once a month
                                if manager_expected_expense['result'][mee]['payment_frequency'] == 'Once a month':

                                    repairs_expected_expenses = repairs_expected_expenses + \
                                        manager_expected_expense['result'][mee]['amount_due']
                                    # if repairs monthly twice a month
                                elif manager_expected_expense['result'][mee]['payment_frequency'] == 'Twice a month':

                                    repairs_expected_expenses = repairs_expected_expenses + 2 * \
                                        (manager_expected_expense['result']
                                            [mee]['amount_due'])
                                else:
                                    print('do nothing')
                                # if repairs annually
                            elif manager_expected_expense['result'][mee]['purchase_frequency'] == 'Annually':
                                # if repairs annually once a year
                                if manager_expected_expense['result'][mee]['payment_frequency'] == 'Once a year':

                                    repairs_expected_expenses = repairs_expected_expenses + \
                                        manager_expected_expense['result'][mee]['amount_due']
                                # if repairs annually twice a year
                                elif manager_expected_expense['result'][mee]['payment_frequency'] == 'Twice a year':

                                    repairs_expected_expenses = repairs_expected_expenses + \
                                        manager_expected_expense['result'][mee]['amount_due']
                                else:
                                    print('do nothing')
                            # if repairs one-time
                            else:
                                repairs_expected_expenses = repairs_expected_expenses + \
                                    manager_expected_expense['result'][mee]['amount_due']
                        # calculate revenue from UTILITY payments
                        if manager_expected_expense['result'][mee]['purchase_type'] == 'UTILITY':
                            if manager_expected_expense['result'][mee]['purchase_frequency'] == 'Weekly':

                                utility_expected_expenses = utility_expected_expenses + \
                                    float(manager_expected_expense['result']
                                          [mee]['amount_due'])
                            elif manager_expected_expense['result'][mee]['purchase_frequency'] == 'Biweekly':

                                utility_expected_expenses = utility_expected_expenses + \
                                    float(manager_expected_expense['result']
                                          [mee]['amount_due'])
                            elif manager_expected_expense['result'][mee]['purchase_frequency'] == 'Monthly':

                                utility_expected_expenses = utility_expected_expenses + \
                                    manager_expected_expense['result'][mee]['amount_due']
                            elif manager_expected_expense['result'][mee]['purchase_frequency'] == 'Annually':

                                utility_expected_expenses = utility_expected_expenses + \
                                    manager_expected_expense['result'][mee]['amount_due']
                            else:

                                utility_expected_expenses = utility_expected_expenses + \
                                    manager_expected_expense['result'][mee]['amount_due']
                        response['result'][i]['maintenance_expected_expenses'] = round(
                            maintenance_expected_expenses, 2)
                        response['result'][i]['management_expected_expenses'] = abs(round((float(manager_expected_expense['result'][mee]['amount_due']) -
                                                                                           management_expected_expenses), 2))
                        response['result'][i]['repairs_expected_expenses'] = round(
                            repairs_expected_expenses, 2)
                        response['result'][i]['utility_expected_expenses'] = round(
                            utility_expected_expenses, 2)
                # get utilities or maintenance/repair expenses
                expense_res = db.execute("""SELECT p.*, pa.*, CONCAT(prop.address," ", prop.unit,", ", prop.city, ", ", prop.state," ", prop.zip) AS address
                    FROM pm.purchases p
                    LEFT JOIN payments pa
                    ON pa.pay_purchase_id = p.purchase_uid
                    LEFT JOIN pm.properties prop
                    ON prop.property_uid LIKE '%""" + property_id + """%'
                    WHERE p.pur_property_id LIKE '%""" + property_id + """%'
                    AND (purchase_type = 'UTILITY' OR  purchase_type = 'MAINTENANCE' OR purchase_type = 'REPAIRS')
                    AND (receiver = \'""" + buid + """\' OR payer LIKE '%""" + buid + """%')
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
