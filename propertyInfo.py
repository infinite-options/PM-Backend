from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from matplotlib.font_manager import json_dump
from matplotlib.style import available

from data import connect
from datetime import date, datetime, timedelta
import json
import calendar
import math


class PropertyInfo(Resource):
    def get(self):
        response = {}
        filters = ['manager_id', 'property_uid']
        where = {}

        with connect() as db:
            for filter in filters:
                filterValue = request.args.get(filter)
                if filterValue is not None:
                    where[filter] = filterValue
                    today = date.today()
                    print(filter)
                    if filter == 'manager_id':
                        response = db.execute("""SELECT *
                                                FROM pm.propertyInfo
                                                WHERE management_status <> 'REJECTED'
                                                AND management_status <> 'TERMINATED'
                                                AND management_status <> 'EXPIRED'
                                                AND manager_id = \'""" + filterValue + """\' """)

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
                                                            AND p.receiver = \'""" + filterValue + """\'
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
                                                        AND (receiver = \'""" + filterValue + """\' OR payer LIKE '%""" + filterValue + """%')
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
                                                        float(
                                                            payment['charge'])

                                                elif payment['frequency'] == 'Biweekly':

                                                    management_expenses = management_expenses + weeks_current_month/2 * \
                                                        float(
                                                            payment['charge'])

                                                elif payment['frequency'] == 'Monthly':

                                                    management_expenses = management_expenses + \
                                                        float(
                                                            payment['charge'])

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
                                                            AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED') AND receiver = \'""" + filterValue + """\'  """)
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
                            AND (receiver = \'""" + filterValue + """\' OR payer LIKE '%""" + filterValue + """%')""")
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
                                                print(
                                                    'in maintenance once a month')

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
                                                        float(
                                                            payment['charge'])

                                                elif payment['frequency'] == 'Biweekly':

                                                    management_expected_expenses = management_expected_expenses + weeks_current_month/2 * \
                                                        float(
                                                            payment['charge'])

                                                elif payment['frequency'] == 'Monthly':

                                                    management_expected_expenses = management_expected_expenses + \
                                                        float(
                                                            payment['charge'])

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
                    else:
                        print('filter property_uid')
                        response = db.execute("""SELECT *
                                                FROM pm.propertyInfo
                                                WHERE management_status <> 'REJECTED'
                                                AND management_status <> 'TERMINATED'
                                                AND management_status <> 'EXPIRED'
                                                AND property_uid = \'""" + filterValue + """\' """)
                        for i in range(len(response['result'])):
                            property_id = response['result'][i]['property_uid']
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

        return response


class AvailableProperties(Resource):
    def get(self):
        response = {}

        with connect() as db:
            # response = db.execute("""SELECT * FROM pm.propertyInfo
            #                             WHERE(rental_status <> 'ACTIVE' AND rental_status <> 'PROCESSING')
            #                             OR rental_status IS NULL AND (manager_id IS NOT NULL)
            #                             AND r.lease_end < DATE_FORMAT(NOW(), "%Y-%m-%d")
            #                             OR r.lease_end = DATE_FORMAT(NOW(), "%Y-%m-%d")
            #                             AND (management_status = 'ACCEPTED') """)

            response = db.execute("""SELECT * FROM pm.properties p
                                        LEFT JOIN   pm.rentals r
                                        ON r.rental_property_id = p.property_uid
                                        LEFT JOIN pm.propertyManager pM
                                        ON pM.linked_property_id = p.property_uid
                                        LEFT JOIN pm.businesses b
                                        ON b.business_uid = pM.linked_business_id
                                        WHERE (management_status = 'ACCEPTED' OR management_status = 'END EARLY' OR management_status = 'PM END EARLY' OR management_status = 'OWNER END EARLY' ) AND p.available_to_rent=1 """)

            # print(response['result'])
            availableProperties = []
            terminated = []
            rentals = []
            expired = []
            notRented = []
            if len(response['result']) > 0:
                for rentals in response['result']:
                    # skip rental status ACTIVE
                    if rentals['rental_status'] == 'ACTIVE':
                        print('skip if rental_status active',
                              rentals['rental_status'])
                    # skip rental status PROCESSING
                    elif rentals['rental_status'] == 'PROCESSING':
                        print('skip if rental_status processing',
                              rentals['rental_status'])
                    # skip rental status TENANT APPROVED
                    elif rentals['rental_status'] == 'TENANT APPROVED':
                        print('skip if rental_status tenant approved',
                              rentals['rental_status'])
                    # do sometginf rental status TERMINATED
                    elif rentals['rental_status'] == 'TERMINATED':
                        print('do something if rental_status terminated',
                              rentals['rental_status'])
                        # check if another lease active for the same property
                        terminatedResponse = db.execute("""SELECT * FROM pm.rentals r
                                                        LEFT JOIN  pm.properties p
                                                        ON p.property_uid = r.rental_property_id
                                                        LEFT JOIN pm.propertyManager pM
                                                        ON pM.linked_property_id = p.property_uid
                                                        WHERE (rental_status = 'ACTIVE' OR rental_status = 'PROCESSING' OR rental_status='TENANT APPROVED')
                                                        AND r.rental_property_id = \'""" + rentals['rental_property_id'] + """\'
                                                        AND (pM.management_status = 'ACCEPTED' OR pM.management_status='END EARLY' OR pM.management_status='PM END EARLY' OR pM.management_status='OWNER END EARLY')   """)

                        if len(terminatedResponse['result']) > 0:
                            print('do not add terminated')
                        else:
                            # print('add terminated')
                            terminated.append(rentals)

                     # do sometginf rental status EXPIRED
                    elif rentals['rental_status'] == 'EXPIRED':
                        # print('do something if rental_status expired',
                        #   rentals['rental_status'])
                        # check if another lease active for the same property
                        expiredResponse = db.execute("""SELECT * FROM pm.rentals r
                                                        LEFT JOIN  pm.properties p
                                                        ON p.property_uid = r.rental_property_id
                                                        LEFT JOIN pm.propertyManager pM
                                                        ON pM.linked_property_id = p.property_uid
                                                        WHERE (rental_status = 'ACTIVE' OR rental_status = 'PROCESSING' OR rental_status='TENANT APPROVED')
                                                        AND r.rental_property_id = \'""" + rentals['rental_property_id'] + """\'
                                                        AND (pM.management_status = 'ACCEPTED' OR pM.management_status='END EARLY' OR pM.management_status='PM END EARLY' OR pM.management_status='OWNER END EARLY')     """)

                        if len(expiredResponse['result']) > 0:
                            print('do not add expired')
                        else:
                            # print('add expired')
                            expired.append(rentals)
                        # print('expired', expired,  len(expired))
                    else:
                        # print('do something if rental_status None',
                        #   rentals['rental_status'])
                        notRented.append(rentals)
            availableProperties = terminated + expired + notRented
            response['result'] = availableProperties
            # print(availableProperties, len(availableProperties))
        return response


class PropertiesManagerDetail(Resource):
    def get(self):
        response = {}
        filters = ['property_uid']
        where = {}
        with connect() as db:
            today = date.today()
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
                        # print(property_id)
                        pid = {'linked_property_id': property_id}
                        application_res = db.execute("""SELECT
                                                        *
                                                        FROM pm.applications WHERE property_uid = \'""" + property_id + """\'""")

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
                                if property_res['result'][pr]['management_status'] == 'ACCEPTED' or property_res['result'][pr]['management_status'] == 'OWNER END EARLY' or property_res['result'][pr]['management_status'] == 'PM END EARLY' or property_res['result'][pr]['management_status'] == 'END EARLY':
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
                        response['result'][i]['rentalInfo'] = list(
                            rental_res['result'])
                        if len(rental_res['result']) > 0:
                            response['result'][i]['rental_status'] = rental_res['result'][0]['rental_status']
                        else:
                            response['result'][i]['rental_status'] = ""

                        rental_revenue = 0
                        extraCharges_revenue = 0
                        utility_revenue = 0
                        maintenance_expenses = 0
                        management_expenses = 0
                        repairs_expenses = 0
                        utility_expenses = 0

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
                        AND p.purchase_status = 'PAID' """)

                        response['result'][i]['rental_revenue'] = round(
                            rental_revenue, 2)
                        response['result'][i]['extraCharges_revenue'] = round(
                            extraCharges_revenue, 2)
                        response['result'][i]['utility_revenue'] = round(
                            utility_revenue, 2)
                        response['result'][i]['manager_revenue'] = list(
                            manager_revenue['result'])

                        if len(manager_revenue['result']) > 0:
                            for mre in range(len(manager_revenue['result'])):
                                # print('mre', manager_revenue['result'][mre])

                                # calculate rental revenue
                                if manager_revenue['result'][mre]['purchase_type'] == 'RENT':
                                    if manager_revenue['result'][mre]['purchase_frequency'] == 'Weekly':

                                        rental_revenue = rental_revenue + \
                                            float(manager_revenue['result']
                                                  [mre]['amount_paid'])
                                    elif manager_revenue['result'][mre]['purchase_frequency'] == 'Biweekly':

                                        rental_revenue = rental_revenue + \
                                            float(manager_revenue['result']
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

                                # calculate revenue from extra charges
                                if manager_revenue['result'][mre]['purchase_type'] == 'EXTRA CHARGES':
                                    if manager_revenue['result'][mre]['purchase_frequency'] == 'Weekly':

                                        extraCharges_revenue = extraCharges_revenue + \
                                            float(manager_revenue['result']
                                                  [mre]['amount_paid'])
                                    elif manager_revenue['result'][mre]['purchase_frequency'] == 'Biweekly':

                                        extraCharges_revenue = extraCharges_revenue + \
                                            float(manager_revenue['result']
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

                                # calculate revenue from UTILITY payments
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
                        response['result'][i]['maintenance_expenses'] = 0
                        response['result'][i]['management_expenses'] = 0
                        response['result'][i]['repairs_expenses'] = 0
                        response['result'][i]['utiltiy_expenses'] = 0
                        # monthly expenses for the property
                        manager_expense = db.execute("""SELECT *
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
                        AND (p.purchase_type= "RENT" OR p.purchase_type = "MAINTENANCE" OR p.purchase_type = 'REPAIRS')
                        AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED')
                        AND p.purchase_status ='PAID' """)

                        response['result'][i]['manager_expense'] = list(
                            manager_expense['result'])
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

                            response['result'][i]['maintenance_expenses'] = round(
                                maintenance_expenses, 2)
                            response['result'][i]['management_expenses'] = abs(round((float(manager_expense['result'][mex]['amount_paid']) -
                                                                                      management_expenses), 2))
                            response['result'][i]['repairs_expenses'] = round(
                                repairs_expenses, 2)

                        manager_utility_expense = db.execute("""SELECT *
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

                        response['result'][i]['manager_expense'] = response['result'][i]['manager_expense'] + (list(
                            manager_utility_expense['result']))

                        if len(manager_utility_expense['result']) > 0:
                            for ore in range(len(manager_utility_expense['result'])):
                                if manager_utility_expense['result'][ore]['purchase_frequency'] == 'Weekly':

                                    utility_expenses = utility_expenses + \
                                        float(manager_utility_expense['result']
                                              [ore]['amount_paid'])
                                elif manager_utility_expense['result'][ore]['purchase_frequency'] == 'Biweekly':

                                    utility_expenses = utility_expenses + \
                                        float(manager_utility_expense['result']
                                              [ore]['amount_paid'])
                                elif manager_utility_expense['result'][ore]['purchase_frequency'] == 'Monthly':

                                    utility_expenses = utility_expenses + \
                                        manager_utility_expense['result'][ore]['amount_paid']
                                elif manager_utility_expense['result'][ore]['purchase_frequency'] == 'Annually':

                                    utility_expenses = utility_expenses + \
                                        manager_utility_expense['result'][ore]['amount_paid']
                                else:

                                    utility_expenses = utility_expenses + \
                                        manager_utility_expense['result'][ore]['amount_paid']
                        response['result'][i]['utility_expenses'] = round(
                            utility_expenses, 2)

                        rental_expected_revenue = 0
                        extraCharges_expected_revenue = 0
                        utility_expected_revenue = 0
                        maintenance_expected_expenses = 0
                        management_expected_expenses = 0
                        repairs_expected_expenses = 0
                        utility_expected_expenses = 0

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
                        AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED')""")

                        response['result'][i]['rental_expected_revenue'] = round(
                            rental_expected_revenue, 2)
                        response['result'][i]['extraCharges_expected_revenue'] = round(
                            extraCharges_expected_revenue, 2)
                        response['result'][i]['utility_expected_revenue'] = round(
                            utility_expected_revenue, 2)
                        response['result'][i]['manager_expected_revenue'] = list(
                            manager_expected_revenue['result'])

                        if len(manager_expected_revenue['result']) > 0:
                            for mre in range(len(manager_expected_revenue['result'])):
                                # print('mre', manager_expected_revenue['result'][mre])

                                # calculate rental revenue
                                if manager_expected_revenue['result'][mre]['purchase_type'] == 'RENT':
                                    if manager_expected_revenue['result'][mre]['purchase_frequency'] == 'Weekly':

                                        rental_expected_revenue = rental_expected_revenue + \
                                            float(manager_expected_revenue['result']
                                                  [mre]['amount_due'])
                                    elif manager_expected_revenue['result'][mre]['purchase_frequency'] == 'Biweekly':

                                        rental_expected_revenue = rental_expected_revenue + \
                                            float(manager_expected_revenue['result']
                                                  [mre]['amount_due'])
                                    elif manager_expected_revenue['result'][mre]['purchase_frequency'] == 'Monthly':

                                        rental_expected_revenue = rental_expected_revenue + \
                                            manager_expected_revenue['result'][mre]['amount_due']
                                    elif manager_expected_revenue['result'][mre]['purchase_frequency'] == 'Annually':

                                        rental_expected_revenue = rental_expected_revenue + \
                                            manager_expected_revenue['result'][mre]['amount_due']
                                    else:

                                        rental_expected_revenue = rental_expected_revenue + \
                                            manager_expected_revenue['result'][mre]['amount_due']

                                # calculate revenue from extra charges
                                if manager_expected_revenue['result'][mre]['purchase_type'] == 'EXTRA CHARGES':
                                    if manager_expected_revenue['result'][mre]['purchase_frequency'] == 'Weekly':

                                        extraCharges_expected_revenue = extraCharges_expected_revenue + \
                                            float(manager_expected_revenue['result']
                                                  [mre]['amount_due'])
                                    elif manager_expected_revenue['result'][mre]['purchase_frequency'] == 'Biweekly':

                                        extraCharges_expected_revenue = extraCharges_expected_revenue + \
                                            float(manager_expected_revenue['result']
                                                  [mre]['amount_due'])
                                    elif manager_expected_revenue['result'][mre]['purchase_frequency'] == 'Monthly':

                                        extraCharges_expected_revenue = extraCharges_expected_revenue + \
                                            manager_expected_revenue['result'][mre]['amount_due']
                                    elif manager_expected_revenue['result'][mre]['purchase_frequency'] == 'Annually':

                                        extraCharges_expected_revenue = extraCharges_expected_revenue + \
                                            manager_expected_revenue['result'][mre]['amount_due']
                                    else:

                                        extraCharges_expected_revenue = extraCharges_expected_revenue + \
                                            manager_expected_revenue['result'][mre]['amount_due']

                                # calculate revenue from UTILITY payments
                                if manager_expected_revenue['result'][mre]['purchase_type'] == 'UTILITY':
                                    if manager_expected_revenue['result'][mre]['purchase_frequency'] == 'Weekly':

                                        utility_expected_revenue = utility_expected_revenue + \
                                            float(manager_expected_revenue['result']
                                                  [mre]['amount_due'])
                                    elif manager_expected_revenue['result'][mre]['purchase_frequency'] == 'Biweekly':

                                        utility_expected_revenue = utility_expected_revenue + \
                                            float(manager_expected_revenue['result']
                                                  [mre]['amount_due'])
                                    elif manager_expected_revenue['result'][mre]['purchase_frequency'] == 'Monthly':

                                        utility_expected_revenue = utility_expected_revenue + \
                                            manager_expected_revenue['result'][mre]['amount_due']
                                    elif manager_expected_revenue['result'][mre]['purchase_frequency'] == 'Annually':

                                        utility_expected_revenue = utility_expected_revenue + \
                                            manager_expected_revenue['result'][mre]['amount_due']
                                    else:

                                        utility_expected_revenue = utility_expected_revenue + \
                                            manager_expected_revenue['result'][mre]['amount_due']

                            response['result'][i]['rental_expected_revenue'] = round(
                                rental_expected_revenue, 2)
                            response['result'][i]['extraCharges_expected_revenue'] = round(
                                extraCharges_expected_revenue, 2)
                            response['result'][i]['utility_expected_revenue'] = round(
                                utility_expected_revenue, 2)

                        # monthly expenses for the property
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
                        AND (p.purchase_type= "RENT" OR p.purchase_type = "MAINTENANCE" OR p.purchase_type = 'REPAIRS')
                        AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED') """)

                        response['result'][i]['maintenance_expected_expenses'] = round(
                            maintenance_expected_expenses, 2)
                        response['result'][i]['management_expected_expenses'] = round(
                            management_expected_expenses, 2)
                        response['result'][i]['repairs_expected_expenses'] = round(
                            repairs_expected_expenses, 2)
                        response['result'][i]['utility_expected_expenses'] = round(
                            utility_expected_expenses, 2)
                        response['result'][i]['manager_expected_expense'] = list(
                            manager_expected_expense['result'])
                        if len(manager_expected_expense['result']) > 0:
                            for mee in range(len(manager_expected_expense['result'])):
                                # print('mee', manager_expected_expense['result'][mee])
                                # if maintenance
                                if manager_expected_expense['result'][mee]['purchase_type'] == 'MAINTENANCE':
                                    #
                                    # if maintenance monthly
                                    if manager_expected_expense['result'][mee]['purchase_frequency'] == 'Monthly':
                                        # print('in maintenance monthly')
                                        # if maintenance monthly once a month
                                        if manager_expected_expense['result'][mee]['payment_frequency'] == 'Once a month':
                                            # print('in maintenance once a month')

                                            maintenance_expected_expenses = maintenance_expected_expenses + \
                                                manager_expected_expense['result'][mee]['amount_due']
                                            # if maintenance monthly twice a month
                                        elif manager_expected_expense['result'][mee]['payment_frequency'] == 'Twice a month':
                                            # print(
                                            # 'in maintenance twice a month')

                                            maintenance_expected_expenses = maintenance_expected_expenses + \
                                                2 * \
                                                (manager_expected_expense['result']
                                                    [mee]['amount_due'])
                                        else:
                                            print('do nothing')
                                        # if maintenance annually
                                    elif manager_expected_expense['result'][mee]['purchase_frequency'] == 'Annually':
                                        # print('in maintenance annually')
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

                            response['result'][i]['maintenance_expected_expenses'] = round(
                                maintenance_expected_expenses, 2)
                            response['result'][i]['management_expected_expenses'] = abs(round((float(manager_expected_expense['result'][mee]['amount_due']) -
                                                                                               management_expected_expenses), 2))
                            response['result'][i]['repairs_expected_expenses'] = round(
                                repairs_expected_expenses, 2)

                        manager_utility_expected_expenses = db.execute("""SELECT *
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

                        response['result'][i]['manager_expected_expense'] = response['result'][i]['manager_expected_expense'] + (list(
                            manager_utility_expected_expenses['result']))

                        if len(manager_utility_expected_expenses['result']) > 0:
                            for ore in range(len(manager_utility_expected_expenses['result'])):
                                if manager_utility_expected_expenses['result'][ore]['purchase_frequency'] == 'Weekly':

                                    utility_expected_expenses = utility_expected_expenses + \
                                        float(manager_utility_expected_expenses['result']
                                              [ore]['amount_due'])
                                elif manager_utility_expected_expenses['result'][ore]['purchase_frequency'] == 'Biweekly':

                                    utility_expected_expenses = utility_expected_expenses + \
                                        float(manager_utility_expected_expenses['result']
                                              [ore]['amount_due'])
                                elif manager_utility_expected_expenses['result'][ore]['purchase_frequency'] == 'Monthly':

                                    utility_expected_expenses = utility_expected_expenses + \
                                        manager_utility_expected_expenses['result'][ore]['amount_due']
                                elif manager_utility_expected_expenses['result'][ore]['purchase_frequency'] == 'Annually':

                                    utility_expected_expenses = utility_expected_expenses + \
                                        manager_utility_expected_expenses['result'][ore]['amount_due']
                                else:

                                    utility_expected_expenses = utility_expected_expenses + \
                                        manager_utility_expected_expenses['result'][ore]['amount_due']
                        response['result'][i]['utility_expected_expenses'] = round(
                            utility_expected_expenses, 2)
            return response


class ManagerExpenses(Resource):
    def get(self):
        response = {}
        filters = ['manager_id']
        where = {}
        with connect() as db:
            for filter in filters:
                filterValue = request.args.get(filter)
                if filterValue is not None:
                    where[filter] = filterValue

            response = db.execute("""SELECT p.*,
                                    GROUP_CONCAT(p.payer) AS payers,
                                    GROUP_CONCAT(p.pur_property_id) AS properties,
                                    GROUP_CONCAT(p.amount_due) AS amounts_due,
                                    GROUP_CONCAT(p.amount_paid) AS amounts_paid,
                                    GROUP_CONCAT(p.purchase_status) AS purchases_status
                                    FROM pm.purchases p
                                    WHERE (purchase_type = 'UTILITY' OR  purchase_type = 'MAINTENANCE' OR purchase_type = 'REPAIRS')
                                    AND (receiver = \'""" + filterValue + """\' OR payer LIKE '%""" + filterValue + """%')
                                    GROUP BY linked_bill_id
                                    """)
            if(len(response['result']) > 0):

                for i in range(len(response['result'])):
                    if response['result'][i]['purchase_type'] == 'UTILITY':
                        # print('in utility')
                        billRes = db.execute("""SELECT b.*
                                                FROM pm.bills b
                                                WHERE b.bill_uid = \'""" + response['result'][i]['linked_bill_id'] + """\' """)

                        if(len(billRes['result']) > 0):
                            for j in range(len(billRes['result'])):
                                response['result'][i].update(
                                    billRes['result'][j])
                        if len(response['result'][i]['properties'].split(',')) > 0:
                            property_uids = response['result'][i]['properties'].split(
                                ',')
                            # print('here', property_uids)
                            response['result'][i]['address'] = []
                            for id in range(len(property_uids)):
                                # print(property_uids[id])
                                propRes = db.execute("""SELECT CONCAT(p.address," ", p.unit,", ", p.city, ", ", p.state," ", p.zip) AS address
                                                FROM pm.properties p
                                                WHERE p.property_uid = \'""" + property_uids[id] + """\' """)

                                response['result'][i]['address'].append(
                                    propRes['result'][0]['address'])

                    elif response['result'][i]['purchase_type'] == 'MAINTENANCE':
                        #
                        maintenanceRes = db.execute("""SELECT mq.*, b.*, CONCAT(p.address," ", p.unit,", ", p.city, ", ", p.state," ", p.zip) AS address
                                                                FROM maintenanceQuotes mq
                                                                LEFT JOIN pm.businesses b
                                                                ON b.business_uid = mq.quote_business_uid
                                                                LEFT JOIN properties p
                                                                ON p.property_uid LIKE '%""" + response['result'][i]['pur_property_id'] + """%'
                                                                WHERE  mq.maintenance_quote_uid = \'""" + response['result'][i]['linked_bill_id'] + """\' """)

                        if(len(maintenanceRes['result']) > 0):
                            for j in range(len(maintenanceRes['result'])):
                                response['result'][i].update(
                                    maintenanceRes['result'][j])
                    elif response['result'][i]['purchase_type'] == 'REPAIRS':
                        #
                        maintenanceRes = db.execute("""SELECT mq.*, b.*, CONCAT(p.address," ", p.unit,", ", p.city, ", ", p.state," ", p.zip) AS address
                                                                FROM maintenanceQuotes mq
                                                                LEFT JOIN pm.businesses b
                                                                ON b.business_uid = mq.quote_business_uid
                                                                LEFT JOIN properties p
                                                                ON p.property_uid = LIKE '%""" + response['result'][i]['pur_property_id'] + """%'
                                                                WHERE  mq.maintenance_quote_uid = \'""" + response['result'][i]['linked_bill_id'] + """\' """)

                        if(len(maintenanceRes['result']) > 0):
                            for j in range(len(maintenanceRes['result'])):
                                response['result'][i].update(
                                    maintenanceRes['result'][j])
            else:
                response['result'][i] = []
        return response
