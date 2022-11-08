from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from data import connect, uploadImage
import boto3
import json
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import calendar


class OwnerCashflow(Resource):
    def get(self):
        response = {}
        response['message'] = 'Successfully executed SQL query'
        response['code'] = 200
        response['result'] = {}
        filters = ['owner_id']
        where = {}

        with connect() as db:
            filterValue = request.args.get(filters[0])
            print(filterValue)
            today = date.today()

            # initialize revenue variables

            rental_revenue = 0
            extra_revenue = 0
            utility_revenue = 0
            rental_expected_revenue = 0
            extra_expected_revenue = 0
            utility_expected_revenue = 0

            rental_year_revenue = 0
            extra_year_revenue = 0
            utility_year_revenue = 0
            rental_year_expected_revenue = 0
            extra_year_expected_revenue = 0
            utility_year_expected_revenue = 0

            # owner rental and extra charges revenue monthly
            owner_rental_revenue = db.execute("""
            SELECT * FROM purchases pu
            LEFT JOIN payments pa
            ON pa.pay_purchase_id = pu.purchase_uid
            LEFT JOIN properties pr
            ON pu.pur_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN rentals r
            ON r.rental_property_id LIKE CONCAT('%', pr.property_uid, '%')
            WHERE pr.owner_id = \'""" + filterValue + """\'
            AND ({fn MONTHNAME(pu.next_payment)} = {fn MONTHNAME(now())} AND YEAR(pu.next_payment) = YEAR(now()))
            AND (pu.purchase_type= "RENT" OR pu.purchase_type= "EXTRA CHARGES")
            AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED')""")

            response['result']['owner_revenue'] = list(
                owner_rental_revenue['result'])

            # owner utility revenue montlhy
            owner_utility_revenue = db.execute("""
            SELECT * FROM purchases pu
            LEFT JOIN payments pa
            ON pa.pay_purchase_id = pu.purchase_uid
            LEFT JOIN properties pr
            ON pu.pur_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN rentals r
            ON r.rental_property_id LIKE CONCAT('%', pr.property_uid, '%')
            WHERE pr.owner_id = \'""" + filterValue + """\'
            AND ({fn MONTHNAME(pu.next_payment)} = {fn MONTHNAME(now())} AND YEAR(pu.next_payment) = YEAR(now()))
            AND (pu.purchase_type="UTILITY")
            AND pu.receiver = \'""" + filterValue + """\'
            AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED') """)

            response['result']['owner_revenue'] = response['result']['owner_revenue'] + list(
                owner_utility_revenue['result'])

            if len(response['result']['owner_revenue']) > 0:
                for ore in range(len(response['result']['owner_revenue'])):
                    # number of weeks in the current month
                    weeks_current_month = len(
                        calendar.monthcalendar(today.year, int(today.strftime("%m"))))

                    if response['result']['owner_revenue'][ore]['purchase_type'] == 'RENT':
                        if response['result']['owner_revenue'][ore]['purchase_frequency'] == 'Weekly':
                            rental_expected_revenue = rental_expected_revenue + \
                                weeks_current_month*int(response['result']['owner_revenue']
                                                        [ore]['amount_due'])
                            rental_revenue = rental_revenue + \
                                weeks_current_month*int(response['result']['owner_revenue']
                                                        [ore]['amount_paid'])

                        elif response['result']['owner_revenue'][ore]['purchase_frequency'] == 'Biweekly':
                            rental_expected_revenue = rental_expected_revenue + \
                                weeks_current_month/2 * \
                                int(response['result']['owner_revenue']
                                    [ore]['amount_due'])
                            rental_revenue = rental_revenue + \
                                weeks_current_month/2 * \
                                int(response['result']['owner_revenue']
                                    [ore]['amount_paid'])
                        elif response['result']['owner_revenue'][ore]['purchase_frequency'] == 'Monthly':
                            rental_expected_revenue = rental_expected_revenue + \
                                response['result']['owner_revenue'][ore]['amount_due']
                            rental_revenue = rental_revenue + \
                                response['result']['owner_revenue'][ore]['amount_paid']

                        elif response['result']['owner_revenue'][ore]['purchase_frequency'] == 'Annually':
                            rental_expected_revenue = rental_expected_revenue + \
                                response['result']['owner_revenue'][ore]['amount_due']
                            rental_revenue = rental_revenue + \
                                response['result']['owner_revenue'][ore]['amount_paid']
                        else:
                            rental_expected_revenue = rental_expected_revenue + \
                                response['result']['owner_revenue'][ore]['amount_due']
                            rental_revenue = rental_revenue + \
                                response['result']['owner_revenue'][ore]['amount_paid']

                    if response['result']['owner_revenue'][ore]['purchase_type'] == 'EXTRA CHARGES':
                        if response['result']['owner_revenue'][ore]['purchase_frequency'] == 'Weekly':
                            extra_expected_revenue = extra_expected_revenue + \
                                weeks_current_month*int(response['result']['owner_revenue']
                                                        [ore]['amount_due'])
                            extra_revenue = extra_revenue + \
                                weeks_current_month*int(response['result']['owner_revenue']
                                                        [ore]['amount_paid'])
                        elif response['result']['owner_revenue'][ore]['purchase_frequency'] == 'Biweekly':
                            extra_expected_revenue = extra_expected_revenue + \
                                weeks_current_month/2 * \
                                int(response['result']['owner_revenue']
                                    [ore]['amount_due'])
                            extra_revenue = extra_revenue + \
                                weeks_current_month/2 * \
                                int(response['result']['owner_revenue']
                                    [ore]['amount_paid'])
                        elif response['result']['owner_revenue'][ore]['purchase_frequency'] == 'Monthly':
                            extra_expected_revenue = extra_expected_revenue + \
                                response['result']['owner_revenue'][ore]['amount_due']
                            extra_revenue = extra_revenue + \
                                response['result']['owner_revenue'][ore]['amount_paid']
                        elif response['result']['owner_revenue'][ore]['purchase_frequency'] == 'Annually':

                            extra_expected_revenue = extra_expected_revenue + \
                                response['result']['owner_revenue'][ore]['amount_due']
                            extra_revenue = extra_revenue + \
                                response['result']['owner_revenue'][ore]['amount_paid']
                        else:
                            extra_expected_revenue = extra_expected_revenue + \
                                response['result']['owner_revenue'][ore]['amount_due']
                            extra_revenue = extra_revenue + \
                                response['result']['owner_revenue'][ore]['amount_paid']

                    if response['result']['owner_revenue'][ore]['purchase_type'] == 'UTILITY':
                        if response['result']['owner_revenue'][ore]['purchase_frequency'] == 'Weekly':
                            utility_expected_revenue = utility_expected_revenue + \
                                weeks_current_month*int(response['result']['owner_revenue']
                                                        [ore]['amount_due'])
                            utility_revenue = utility_revenue + \
                                weeks_current_month*int(response['result']['owner_revenue']
                                                        [ore]['amount_paid'])
                        elif response['result']['owner_revenue'][ore]['purchase_frequency'] == 'Biweekly':
                            utility_expected_revenue = utility_expected_revenue + \
                                weeks_current_month/2 * \
                                int(response['result']['owner_revenue']
                                    [ore]['amount_due'])
                            utility_revenue = utility_revenue + \
                                weeks_current_month/2 * \
                                int(response['result']['owner_revenue']
                                    [ore]['amount_paid'])
                        elif response['result']['owner_revenue'][ore]['purchase_frequency'] == 'Monthly':
                            utility_expected_revenue = utility_expected_revenue + \
                                response['result']['owner_revenue'][ore]['amount_due']
                            utility_revenue = utility_revenue + \
                                response['result']['owner_revenue'][ore]['amount_paid']
                        elif response['result']['owner_revenue'][ore]['purchase_frequency'] == 'Annually':
                            utility_expected_revenue = utility_expected_revenue + \
                                response['result']['owner_revenue'][ore]['amount_due']
                            utility_revenue = utility_revenue + \
                                response['result']['owner_revenue'][ore]['amount_paid']
                        else:
                            utility_expected_revenue = utility_expected_revenue + \
                                response['result']['owner_revenue'][ore]['amount_due']
                            utility_revenue = utility_revenue + \
                                response['result']['owner_revenue'][ore]['amount_paid']
            response['result']['rental_revenue'] = round(
                rental_revenue, 2)
            response['result']['rental_expected_revenue'] = round(
                rental_expected_revenue, 2)
            response['result']['extra_revenue'] = round(
                extra_revenue, 2)
            response['result']['extra_expected_revenue'] = round(
                extra_expected_revenue, 2)
            response['result']['utility_revenue'] = round(
                utility_revenue, 2)
            response['result']['utility_expected_revenue'] = round(
                utility_expected_revenue, 2)
            # owner rental and extra charged revenue yearly
            owner_rental_revenue_yearly = db.execute("""
            SELECT * FROM purchases pu
            LEFT JOIN payments pa
            ON pa.pay_purchase_id = pu.purchase_uid
            LEFT JOIN properties pr
            ON pu.pur_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN rentals r
            ON r.rental_property_id LIKE CONCAT('%', pr.property_uid, '%')
            WHERE pr.owner_id = \'""" + filterValue + """\'
            AND YEAR(pu.next_payment) = YEAR(now())
            AND (pu.purchase_type= "RENT" OR pu.purchase_type= "EXTRA CHARGES")
            AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED')""")

            response['result']['owner_revenue_yearly'] = list(
                owner_rental_revenue_yearly['result'])

            # owner utility revenue yearly
            owner_utility_revenue_yearly = db.execute("""
            SELECT * FROM purchases pu
            LEFT JOIN payments pa
            ON pa.pay_purchase_id = pu.purchase_uid
            LEFT JOIN properties pr
            ON pu.pur_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN rentals r
            ON r.rental_property_id LIKE CONCAT('%', pr.property_uid, '%')
            WHERE pr.owner_id = \'""" + filterValue + """\'
            AND YEAR(pu.next_payment) = YEAR(now())
            AND (pu.purchase_type="UTILITY")
            AND pu.receiver = \'""" + filterValue + """\'
            AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED') """)

            response['result']['owner_revenue_yearly'] = response['result']['owner_revenue_yearly'] + list(
                owner_utility_revenue_yearly['result'])

            if len(response['result']['owner_revenue_yearly']) > 0:
                for ore in range(len(response['result']['owner_revenue_yearly'])):

                    # number of months a property has been active
                    delta_active = relativedelta((datetime.strptime(
                        response['result']['owner_revenue_yearly'][ore]['active_date'], '%Y-%m-%d')), datetime.now())
                    months_active = abs(delta_active.months +
                                        (delta_active.years * 12))
                    # number of months a property has been under an active lease
                    delta_leased = relativedelta((datetime.strptime(
                        response['result']['owner_revenue_yearly'][ore]['lease_start'], '%Y-%m-%d')), datetime.now())

                    months_leased = abs(delta_leased.months +
                                        (delta_leased.years * 12))
                    # number of weeks in the current month
                    weeks_current_month = len(
                        calendar.monthcalendar(today.year, int(today.strftime("%m"))))
                    # number of weeks a property has been active
                    weeks_active = round((abs(today - datetime.strptime(
                        response['result']['owner_revenue_yearly'][ore]['active_date'], '%Y-%m-%d').date()).days)/7, 1)
                    # number of weeks a property has been under an active lease
                    weeks_leased = round((abs(today - datetime.strptime(
                        response['result']['owner_revenue_yearly'][ore]['lease_start'], '%Y-%m-%d').date()).days)/7, 1)

                    # if revenue type is RENT
                    if response['result']['owner_revenue_yearly'][ore]['purchase_type'] == 'RENT':
                        if response['result']['owner_revenue_yearly'][ore]['purchase_frequency'] == 'Weekly':
                            rental_year_expected_revenue = rental_year_expected_revenue + \
                                weeks_leased*int(response['result']['owner_revenue_yearly']
                                                 [ore]['amount_due'])
                            rental_year_revenue = rental_year_revenue + \
                                weeks_leased*int(response['result']['owner_revenue_yearly']
                                                         [ore]['amount_paid'])

                        elif response['result']['owner_revenue_yearly'][ore]['purchase_frequency'] == 'Biweekly':
                            rental_year_expected_revenue = rental_year_expected_revenue + \
                                weeks_leased/2 * \
                                int(response['result']['owner_revenue_yearly']
                                    [ore]['amount_due'])
                            rental_year_revenue = rental_year_revenue + \
                                weeks_leased/2 * \
                                int(response['result']['owner_revenue_yearly']
                                    [ore]['amount_paid'])
                        elif response['result']['owner_revenue_yearly'][ore]['purchase_frequency'] == 'Monthly':
                            rental_year_expected_revenue = rental_year_expected_revenue + \
                                months_leased * \
                                int(response['result']
                                    ['owner_revenue_yearly'][ore]['amount_due'])
                            rental_year_revenue = rental_year_revenue + \
                                months_leased * \
                                int(response['result']['owner_revenue_yearly']
                                    [ore]['amount_paid'])

                        elif response['result']['owner_revenue_yearly'][ore]['purchase_frequency'] == 'Annually':
                            rental_year_expected_revenue = rental_year_expected_revenue + \
                                response['result']['owner_revenue_yearly'][ore]['amount_due']
                            rental_year_revenue = rental_year_revenue + \
                                response['result']['owner_revenue_yearly'][ore]['amount_paid']
                        else:
                            rental_year_expected_revenue = rental_year_expected_revenue + \
                                response['result']['owner_revenue_yearly'][ore]['amount_due']
                            rental_year_revenue = rental_year_revenue + \
                                response['result']['owner_revenue_yearly'][ore]['amount_paid']

                     # if revenue type is EXTRA CHARGES
                    if response['result']['owner_revenue_yearly'][ore]['purchase_type'] == 'EXTRA CHARGES':
                        if response['result']['owner_revenue_yearly'][ore]['purchase_frequency'] == 'Weekly':
                            extra_year_expected_revenue = extra_year_expected_revenue + \
                                weeks_leased*int(response['result']['owner_revenue_yearly']
                                                         [ore]['amount_due'])
                            extra_year_revenue = extra_year_revenue + \
                                weeks_leased*int(response['result']['owner_revenue_yearly']
                                                         [ore]['amount_paid'])
                        elif response['result']['owner_revenue_yearly'][ore]['purchase_frequency'] == 'Biweekly':
                            extra_year_expected_revenue = extra_year_expected_revenue + \
                                weeks_leased/2 * \
                                int(response['result']['owner_revenue_yearly']
                                    [ore]['amount_due'])
                            extra_year_revenue = extra_year_revenue + \
                                weeks_leased/2 * \
                                int(response['result']['owner_revenue_yearly']
                                    [ore]['amount_paid'])
                        elif response['result']['owner_revenue_yearly'][ore]['purchase_frequency'] == 'Monthly':
                            extra_year_expected_revenue = extra_year_expected_revenue + \
                                months_leased * \
                                int(response['result']
                                    ['owner_revenue_yearly'][ore]['amount_due'])
                            extra_year_revenue = extra_year_revenue + \
                                months_leased * \
                                int(response['result']['owner_revenue_yearly']
                                    [ore]['amount_paid'])
                        elif response['result']['owner_revenue_yearly'][ore]['purchase_frequency'] == 'Annually':

                            extra_year_expected_revenue = extra_year_expected_revenue + \
                                response['result']['owner_revenue_yearly'][ore]['amount_due']
                            extra_year_revenue = extra_year_revenue + \
                                response['result']['owner_revenue_yearly'][ore]['amount_paid']
                        else:
                            extra_year_expected_revenue = extra_year_expected_revenue + \
                                response['result']['owner_revenue_yearly'][ore]['amount_due']
                            extra_year_revenue = extra_year_revenue + \
                                response['result']['owner_revenue_yearly'][ore]['amount_paid']

                     # if revenue type is UTILITY
                    if response['result']['owner_revenue_yearly'][ore]['purchase_type'] == 'UTILITY':
                        if response['result']['owner_revenue_yearly'][ore]['purchase_frequency'] == 'Weekly':
                            utility_year_expected_revenue = utility_year_expected_revenue + \
                                weeks_leased*int(response['result']['owner_revenue_yearly']
                                                         [ore]['amount_due'])
                            utility_year_revenue = utility_year_revenue + \
                                weeks_leased*int(response['result']['owner_revenue_yearly']
                                                         [ore]['amount_paid'])
                        elif response['result']['owner_revenue_yearly'][ore]['purchase_frequency'] == 'Biweekly':
                            utility_year_expected_revenue = utility_year_expected_revenue + \
                                weeks_leased/2 * \
                                int(response['result']['owner_revenue_yearly']
                                    [ore]['amount_due'])
                            utility_year_revenue = utility_year_revenue + \
                                weeks_leased/2 * \
                                int(response['result']['owner_revenue_yearly']
                                    [ore]['amount_paid'])
                        elif response['result']['owner_revenue_yearly'][ore]['purchase_frequency'] == 'Monthly':
                            utility_year_expected_revenue = utility_year_expected_revenue + \
                                months_leased * \
                                int(response['result']
                                    ['owner_revenue_yearly'][ore]['amount_due'])
                            utility_year_revenue = utility_year_revenue + \
                                months_leased * \
                                int(response['result']['owner_revenue_yearly']
                                    [ore]['amount_paid'])
                        elif response['result']['owner_revenue_yearly'][ore]['purchase_frequency'] == 'Annually':
                            utility_year_expected_revenue = utility_year_expected_revenue + \
                                response['result']['owner_revenue_yearly'][ore]['amount_due']
                            utility_year_revenue = utility_year_revenue + \
                                response['result']['owner_revenue_yearly'][ore]['amount_paid']
                        else:
                            utility_year_expected_revenue = utility_year_expected_revenue + \
                                response['result']['owner_revenue_yearly'][ore]['amount_due']
                            utility_year_revenue = utility_year_revenue + \
                                response['result']['owner_revenue_yearly'][ore]['amount_paid']
            response['result']['rental_year_revenue'] = round(
                rental_year_revenue, 2)
            response['result']['rental_year_expected_revenue'] = round(
                rental_year_expected_revenue, 2)
            response['result']['extra_year_revenue'] = round(
                extra_year_revenue, 2)
            response['result']['extra_year_expected_revenue'] = round(
                extra_year_expected_revenue, 2)
            response['result']['utility_year_revenue'] = round(
                utility_year_revenue, 2)
            response['result']['utility_year_expected_revenue'] = round(
                utility_year_expected_revenue, 2)

            # intialize expense variables
            utility_expense = 0
            maintenance_expense = 0
            management_expense = 0
            repairs_expense = 0
            maintenance_expected_expense = 0
            management_expected_expense = 0
            repairs_expected_expense = 0
            utility_expected_expense = 0

            mortgage_expense = 0
            insurance_expense = 0
            taxes_expense = 0

            maintenance_year_expense = 0
            management_year_expense = 0
            repairs_year_expense = 0
            utility_year_expense = 0
            utility_year_expected_expense = 0
            maintenance_year_expected_expense = 0
            management_year_expected_expense = 0
            repairs_year_expected_expense = 0

            mortgage_year_expense = 0
            insurance_year_expense = 0
            taxes_year_expense = 0

            # owner all expense monthly except mortgage, taxes, insurance
            owner_expense = db.execute("""
            SELECT * FROM purchases pu
            LEFT JOIN payments pa
            ON pa.pay_purchase_id = pu.purchase_uid
            LEFT JOIN properties pr
            ON pu.pur_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN rentals r
            ON r.rental_property_id LIKE CONCAT('%', pr.property_uid, '%')
            WHERE pr.owner_id = \'""" + filterValue + """\'
            AND ({fn MONTHNAME(pu.next_payment)} = {fn MONTHNAME(now())} AND YEAR(pu.next_payment) = YEAR(now()))
            AND (pu.purchase_type <> "RENT" AND pu.purchase_type <> "EXTRA CHARGES" AND pu.purchase_type <> "UTILITY")
            AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED')""")

            response['result']['owner_expense'] = list(owner_expense['result'])

            owner_utility_expense = db.execute("""
            SELECT * FROM purchases pu
            LEFT JOIN payments pa
            ON pa.pay_purchase_id = pu.purchase_uid
            LEFT JOIN properties pr
            ON pu.pur_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN rentals r
            ON r.rental_property_id LIKE CONCAT('%', pr.property_uid, '%')
            WHERE pr.owner_id = \'""" + filterValue + """\'
            AND ({fn MONTHNAME(pu.next_payment)} = {fn MONTHNAME(now())} AND YEAR(pu.next_payment) = YEAR(now()))
            AND (pu.purchase_type="UTILITY")
            AND pu.payer LIKE '%""" + filterValue + """%'
            AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED') """)

            response['result']['owner_expense'] = response['result']['owner_expense'] + (list(
                owner_utility_expense['result']))

            # monthly expenses for the property
            owner_management_expense = db.execute("""
            SELECT * FROM purchases pu
            LEFT JOIN payments pa
            ON pa.pay_purchase_id = pu.purchase_uid
            LEFT JOIN properties pr
            ON pu.pur_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN rentals r
            ON r.rental_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN pm.contracts c
            ON c.property_uid LIKE CONCAT('%', pr.property_uid, '%')
            WHERE pr.owner_id = \'""" + filterValue + """\'
            AND c.contract_status = 'ACTIVE'
            AND ({fn MONTHNAME(pu.next_payment)} = {fn MONTHNAME(now())} AND YEAR(pu.next_payment) = YEAR(now()))
            AND (pu.purchase_type= "RENT")
            AND r.rental_status = 'ACTIVE'
            AND pu.purchase_status = 'PAID'""")

            response['result']['owner_expense'] = response['result']['owner_expense'] + (list(
                owner_management_expense['result']))
            if len(owner_management_expense['result']) > 0:
                for mex in range(len(owner_management_expense['result'])):
                    # if management
                    # number of months a property has been active
                    delta_active = relativedelta((datetime.strptime(
                        owner_management_expense['result'][mex]['active_date'], '%Y-%m-%d')), datetime.now())
                    months_active = abs(delta_active.months +
                                        (delta_active.years * 12))
                    # number of months a property has been under an active lease
                    delta_leased = relativedelta((datetime.strptime(
                        owner_management_expense['result'][mex]['lease_start'], '%Y-%m-%d')), datetime.now())

                    months_leased = abs(delta_leased.months +
                                        (delta_leased.years * 12))
                    # number of weeks in the current month
                    weeks_current_month = len(
                        calendar.monthcalendar(today.year, int(today.strftime("%m"))))
                    # number of weeks a property has been active
                    weeks_active = round((abs(today - datetime.strptime(
                        owner_management_expense['result'][mex]['active_date'], '%Y-%m-%d').date()).days)/7, 1)
                    # number of weeks a property has been under an active lease
                    weeks_leased = round((abs(today - datetime.strptime(
                        owner_management_expense['result'][mex]['lease_start'], '%Y-%m-%d').date()).days)/7, 1)

                    if owner_management_expense['result'][mex]['purchase_type'] == 'RENT':
                        managementPayments = json.loads(
                            owner_management_expense['result'][mex]['contract_fees'])

                        for payment in managementPayments:
                            # print('amount paid to owner', payment)
                            if payment['fee_type'] == '%':
                                if payment['of'] == 'Gross Rent':
                                    if payment['frequency'] == 'Weekly':
                                        management_expected_expense = management_expected_expense + weeks_current_month*float((
                                            float(owner_management_expense['result'][mex]['amount_due']) * float(payment['charge']))/100)
                                        management_expense = management_expense +  \
                                            weeks_current_month*float((
                                                float(owner_management_expense['result'][mex]['amount_paid']) * float(payment['charge']))/100)
                                    elif payment['frequency'] == 'Biweekly':
                                        management_expected_expense = management_expected_expense + weeks_current_month/2 * \
                                            ((
                                                float(owner_management_expense['result'][mex]['amount_due']) * float(payment['charge']))/100)
                                        management_expense = management_expense +  \
                                            weeks_current_month/2 * \
                                            ((
                                                float(owner_management_expense['result'][mex]['amount_paid']) * float(payment['charge']))/100)
                                    elif payment['frequency'] == 'Monthly':
                                        management_expected_expense = management_expected_expense +  \
                                            ((
                                                float(owner_management_expense['result'][mex]['amount_due']) * float(payment['charge']))/100)
                                        management_expense = management_expense +  \
                                            (
                                                float(owner_management_expense['result'][mex]['amount_paid']) * float(payment['charge']))/100
                                    elif payment['frequency'] == 'Annually':
                                        if date.fromisoformat(owner_management_expense['result'][mex]['start_date']).month == today.month:
                                            management_expected_expense = management_expected_expense +  \
                                                (
                                                    float(owner_management_expense['result'][mex]['amount_due']) * float(payment['charge']))/100
                                            management_expense = management_expense +  \
                                                (
                                                    float(owner_management_expense['result'][mex]['amount_paid']) * float(payment['charge']))/100
                                    elif payment['frequency'] == 'One-time':
                                        if date.fromisoformat(owner_management_expense['result'][mex]['start_date']).month == today.month:
                                            management_expected_expense = management_expected_expense +  \
                                                (
                                                    float(owner_management_expense['result'][mex]['amount_due']) * float(payment['charge']))/100
                                            management_expense = management_expense +  \
                                                (
                                                    float(owner_management_expense['result'][mex]['amount_paid']) * float(payment['charge']))/100
                                    else:
                                        print('do nothing')
                            elif payment['fee_type'] == '$':
                                if payment['frequency'] == 'Weekly':
                                    management_expected_expense = management_expected_expense + weeks_current_month * \
                                        float(payment['charge'])
                                    management_expense = management_expense + weeks_current_month * \
                                        float(payment['charge'])
                                elif payment['frequency'] == 'Biweekly':
                                    management_expected_expense = management_expected_expense + weeks_current_month/2 * \
                                        float(payment['charge'])
                                    management_expense = management_expense + weeks_current_month/2 * \
                                        float(payment['charge'])
                                elif payment['frequency'] == 'Monthly':
                                    management_expected_expense = management_expected_expense +  \
                                        float(payment['charge'])
                                    management_expense = management_expense + \
                                        float(payment['charge'])
                                elif payment['frequency'] == 'Annually':

                                    if date.fromisoformat(owner_management_expense['result'][mex]['start_date']).month == today.month:
                                        management_expected_expense = management_expected_expense + \
                                            float(payment['charge'])
                                        management_expense = management_expense + \
                                            float(
                                                payment['charge'])
                                elif payment['frequency'] == 'One-time':

                                    if date.fromisoformat(owner_management_expense['result'][mex]['start_date']).month == today.month:
                                        management_expected_expense = management_expected_expense +  \
                                            float(payment['charge'])
                                        management_expense = management_expense + \
                                            float(
                                                payment['charge'])

                                else:
                                    print('do nothing')
                            else:
                                print('do nothing')
            if len(response['result']['owner_expense']) > 0:
                for ore in range(len(response['result']['owner_expense'])):
                    # number of months a property has been active
                    delta_active = relativedelta((datetime.strptime(
                        response['result']['owner_expense'][ore]['active_date'], '%Y-%m-%d')), datetime.now())
                    months_active = abs(delta_active.months +
                                        (delta_active.years * 12))
                    # number of months a property has been under an active lease
                    delta_leased = relativedelta((datetime.strptime(
                        response['result']['owner_expense'][ore]['lease_start'], '%Y-%m-%d')), datetime.now())

                    months_leased = abs(delta_leased.months +
                                        (delta_leased.years * 12))
                    # number of weeks in the current month
                    weeks_current_month = len(
                        calendar.monthcalendar(today.year, int(today.strftime("%m"))))

                    # if expenses type is MAINTAINENCE
                    if response['result']['owner_expense'][ore]['purchase_type'] == 'MAINTENANCE':
                        # if maintenance monthly
                        if response['result']['owner_expense'][ore]['purchase_frequency'] == 'Monthly':
                            # if maintenance monthly once a month
                            if response['result']['owner_expense'][ore]['payment_frequency'] == 'Once a month' or response['result']['owner_expense'][ore]['payment_frequency'] is None:

                                maintenance_expected_expense = maintenance_expected_expense + \
                                    response['result']['owner_expense'][ore]['amount_due']
                                maintenance_expense = maintenance_expense + \
                                    response['result']['owner_expense'][ore]['amount_paid']
                                # if maintenance monthly twice a month
                            elif response['result']['owner_expense'][ore]['payment_frequency'] == 'Twice a month':

                                maintenance_expected_expense = maintenance_expected_expense + 2 * \
                                    (response['result']['owner_expense']
                                        [ore]['amount_due'])
                                maintenance_expense = maintenance_expense + \
                                    2 * \
                                    (response['result']['owner_expense']
                                        [ore]['amount_paid'])
                            else:
                                print('do nothing')
                            # if maintenance annually
                        elif response['result']['owner_expense'][ore]['purchase_frequency'] == 'Annually':
                            # if maintenance annually once a year
                            if response['result']['owner_expense'][ore]['payment_frequency'] == 'Once a year':
                                maintenance_expected_expense = maintenance_expected_expense + \
                                    (response['result']['owner_expense']
                                        [ore]['amount_due'])
                                maintenance_expense = maintenance_expense + \
                                    response['result']['owner_expense'][ore]['amount_paid']
                            # if maintenance annually twice a year
                            elif response['result']['owner_expense'][ore]['payment_frequency'] == 'Twice a year':
                                maintenance_expected_expense = maintenance_expected_expense + \
                                    (response['result']['owner_expense']
                                        [ore]['amount_due'])
                                maintenance_expense = maintenance_expense + \
                                    response['result']['owner_expense'][ore]['amount_paid']
                            else:
                                print('do nothing')
                        # if maintenance one-time
                        else:
                            maintenance_expected_expense = maintenance_expected_expense + \
                                response['result']['owner_expense'][ore]['amount_due']
                            maintenance_expense = maintenance_expense + \
                                response['result']['owner_expense'][ore]['amount_paid']
                    # if management
                    if response['result']['owner_expense'][ore]['purchase_type'] == 'MANAGEMENT':
                        # if management monthly
                        if response['result']['owner_expense'][ore]['purchase_frequency'] == 'Monthly':
                            # if management monthly once a month
                            if response['result']['owner_expense'][ore]['payment_frequency'] == 'Once a month' or response['result']['owner_expense'][ore]['payment_frequency'] is None:
                                management_expected_expense = management_expected_expense + response[
                                    'result']['owner_expense'][ore]['amount_due']
                                management_expense = management_expense + \
                                    response['result']['owner_expense'][ore]['amount_paid']
                                # if management monthly twice a month
                            elif response['result']['owner_expense'][ore]['payment_frequency'] == 'Twice a month':
                                management_expected_expense = management_expected_expense + 2 * \
                                    (response['result']['owner_expense']
                                        [ore]['amount_due'])
                                management_expense = management_expense + \
                                    2 * \
                                    (response['result']['owner_expense']
                                        [ore]['amount_paid'])
                            else:
                                print('do nothing')
                            # if management annually
                        elif response['result']['owner_expense'][ore]['purchase_frequency'] == 'Annually':
                            # if management annually once a year
                            if response['result']['owner_expense'][ore]['payment_frequency'] == 'Once a year':
                                management_expected_expense = management_expected_expense +  \
                                    (response['result']['owner_expense']
                                        [ore]['amount_due'])
                                management_expense = management_expense + \
                                    response['result']['owner_expense'][ore]['amount_paid']
                            # if management annually twice a year
                            elif response['result']['owner_expense'][ore]['payment_frequency'] == 'Twice a year':
                                management_expected_expense = management_expected_expense +  \
                                    (response['result']['owner_expense']
                                        [ore]['amount_due'])
                                management_expense = management_expense + \
                                    response['result']['owner_expense'][ore]['amount_paid']
                            else:
                                print('do nothing')
                        # if management one-time
                        else:
                            management_expected_expense = management_expected_expense + \
                                response['result']['owner_expense'][ore]['amount_due']
                            management_expense = management_expense + \
                                response['result']['owner_expense'][ore]['amount_paid']

                    if response['result']['owner_expense'][ore]['purchase_type'] == 'REPAIRS':
                        # if repairs monthly
                        if response['result']['owner_expense'][ore]['purchase_frequency'] == 'Monthly':
                            # if repairs monthly once a month
                            if response['result']['owner_expense'][ore]['payment_frequency'] == 'Once a month' or response['result']['owner_expense'][ore]['payment_frequency'] is None:
                                repairs_expected_expense = repairs_expected_expense +  \
                                    (response['result']['owner_expense']
                                        [ore]['amount_due'])
                                repairs_expense = repairs_expense + \
                                    response['result']['owner_expense'][ore]['amount_paid']
                                # if repairs monthly twice a month
                            elif response['result']['owner_expense'][ore]['payment_frequency'] == 'Twice a month':
                                repairs_expected_expense = repairs_expected_expense + 2 * \
                                    (response['result']['owner_expense']
                                        [ore]['amount_due'])
                                repairs_expense = repairs_expense + \
                                    2 * \
                                    (response['result']['owner_expense']
                                        [ore]['amount_paid'])
                            else:
                                print('do nothing')
                            # if repairs annually
                        elif response['result']['owner_expense'][ore]['purchase_frequency'] == 'Annually':
                            # if repairs annually once a year
                            if response['result']['owner_expense'][ore]['payment_frequency'] == 'Once a year':
                                repairs_expected_expense = repairs_expected_expense +  \
                                    (response['result']['owner_expense']
                                        [ore]['amount_due'])
                                repairs_expense = repairs_expense + \
                                    response['result']['owner_expense'][ore]['amount_paid']
                            # if repairs annually twice a year
                            elif response['result']['owner_expense'][ore]['payment_frequency'] == 'Twice a year':
                                repairs_expected_expense = repairs_expected_expense + \
                                    (response['result']['owner_expense']
                                        [ore]['amount_due'])
                                repairs_expense = repairs_expense + \
                                    response['result']['owner_expense'][ore]['amount_paid']
                            else:
                                print('do nothing')
                        # if repairs one-time
                        else:
                            repairs_expected_expense = repairs_expected_expense + \
                                response['result']['owner_expense'][ore]['amount_due']
                            repairs_expense = repairs_expense + \
                                response['result']['owner_expense'][ore]['amount_paid']
                    if response['result']['owner_expense'][ore]['purchase_type'] == 'UTILITY':
                        if response['result']['owner_expense'][ore]['purchase_frequency'] == 'Weekly':
                            utility_expected_expense = utility_expected_expense + \
                                weeks_current_month*int(response['result']['owner_expense']
                                                        [ore]['amount_due'])
                            utility_expense = utility_expense + \
                                weeks_current_month*int(response['result']['owner_expense']
                                                        [ore]['amount_paid'])
                        elif response['result']['owner_expense'][ore]['purchase_frequency'] == 'Biweekly':
                            utility_expected_expense = utility_expected_expense + \
                                weeks_current_month/2 * \
                                int(response['result']['owner_expense']
                                    [ore]['amount_due'])
                            utility_expense = utility_expense + \
                                weeks_current_month/2 * \
                                int(response['result']['owner_expense']
                                    [ore]['amount_paid'])
                        elif response['result']['owner_expense'][ore]['purchase_frequency'] == 'Monthly':
                            utility_expected_expense = utility_expected_expense + \
                                response['result']['owner_expense'][ore]['amount_due']
                            utility_expense = utility_expense + \
                                response['result']['owner_expense'][ore]['amount_paid']
                        elif response['result']['owner_expense'][ore]['purchase_frequency'] == 'Annually':
                            utility_expected_expense = utility_expected_expense + \
                                response['result']['owner_expense'][ore]['amount_due']
                            utility_expense = utility_expense + \
                                response['result']['owner_expense'][ore]['amount_paid']
                        else:
                            utility_expected_expense = utility_expected_expense + \
                                response['result']['owner_expense'][ore]['amount_due']
                            utility_expense = utility_expense + \
                                response['result']['owner_expense'][ore]['amount_paid']

            response['result']['maintenance_expense'] = round(
                maintenance_expense, 2)
            response['result']['management_expense'] = round(
                management_expense, 2)
            response['result']['repairs_expense'] = round(
                repairs_expense, 2)
            response['result']['utility_expense'] = round(
                utility_expense, 2)
            response['result']['maintenance_expected_expense'] = round(
                maintenance_expected_expense, 2)
            response['result']['management_expected_expense'] = round(
                management_expected_expense, 2)
            response['result']['repairs_expected_expense'] = round(
                repairs_expected_expense, 2)
            response['result']['utility_expected_expense'] = round(
                utility_expense, 2)

            # owner all expenses monthly except mortgage, taxes, insurance
            owner_expense_yearly = db.execute("""
            SELECT * FROM purchases pu
            LEFT JOIN payments pa
            ON pa.pay_purchase_id = pu.purchase_uid
            LEFT JOIN properties pr
            ON pu.pur_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN rentals r
            ON r.rental_property_id LIKE CONCAT('%', pr.property_uid, '%')
            WHERE pr.owner_id = \'""" + filterValue + """\'
            AND YEAR(pu.next_payment) = YEAR(now())
            AND (pu.purchase_type <> "RENT" AND pu.purchase_type <> "EXTRA CHARGES" AND pu.purchase_type <> "UTILITY")
            AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED')""")

            response['result']['owner_expense_yearly'] = list(
                owner_expense_yearly['result'])

            owner_utility_year_expense = db.execute("""
            SELECT * FROM purchases pu
            LEFT JOIN payments pa
            ON pa.pay_purchase_id = pu.purchase_uid
            LEFT JOIN properties pr
            ON pu.pur_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN rentals r
            ON r.rental_property_id LIKE CONCAT('%', pr.property_uid, '%')
            WHERE pr.owner_id = \'""" + filterValue + """\'
            AND YEAR(pu.next_payment) = YEAR(now())
            AND (pu.purchase_type="UTILITY")
            AND pu.payer LIKE '%""" + filterValue + """%'
            AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED') """)

            response['result']['owner_expense_yearly'] = response['result']['owner_expense_yearly'] + (list(
                owner_utility_year_expense['result']))

            # monthly expenses for the property
            owner_management_year_expense = db.execute("""
            SELECT * FROM purchases pu
            LEFT JOIN payments pa
            ON pa.pay_purchase_id = pu.purchase_uid
            LEFT JOIN properties pr
            ON pu.pur_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN rentals r
            ON r.rental_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN pm.contracts c
            ON c.property_uid LIKE CONCAT('%', pr.property_uid, '%')
            WHERE pr.owner_id = \'""" + filterValue + """\'
            AND c.contract_status = 'ACTIVE'
            AND YEAR(pu.next_payment) = YEAR(now())
            AND (pu.purchase_type= "RENT")
            AND r.rental_status = 'ACTIVE'
            AND pu.purchase_status = 'PAID'""")

            response['result']['owner_expense_yearly'] = response['result']['owner_expense_yearly'] + (list(
                owner_management_year_expense['result']))
            if len(owner_management_year_expense['result']) > 0:
                for mex in range(len(owner_management_year_expense['result'])):
                    # if management
                    # number of months a property has been active
                    delta_active = relativedelta((datetime.strptime(
                        owner_management_year_expense['result'][mex]['active_date'], '%Y-%m-%d')), datetime.now())
                    months_active = abs(delta_active.months +
                                        (delta_active.years * 12))
                    # number of months a property has been under an active lease
                    delta_leased = relativedelta((datetime.strptime(
                        owner_management_year_expense['result'][mex]['lease_start'], '%Y-%m-%d')), datetime.now())

                    months_leased = abs(delta_leased.months +
                                        (delta_leased.years * 12))
                    # number of weeks in the current month
                    weeks_current_month = len(
                        calendar.monthcalendar(today.year, int(today.strftime("%m"))))
                    # number of weeks a property has been active
                    weeks_active = round((abs(today - datetime.strptime(
                        owner_management_year_expense['result'][mex]['active_date'], '%Y-%m-%d').date()).days)/7, 1)
                    # number of weeks a property has been under an active lease
                    weeks_leased = round((abs(today - datetime.strptime(
                        owner_management_year_expense['result'][mex]['lease_start'], '%Y-%m-%d').date()).days)/7, 1)

                    if owner_management_year_expense['result'][mex]['purchase_type'] == 'RENT':
                        managementPayments = json.loads(
                            owner_management_year_expense['result'][mex]['contract_fees'])

                        for payment in managementPayments:
                            # print('amount paid to owner', payment)
                            if payment['fee_type'] == '%':
                                if payment['of'] == 'Gross Rent':
                                    if payment['frequency'] == 'Weekly':
                                        management_year_expected_expense = management_year_expected_expense + weeks_leased*float((
                                            float(owner_management_year_expense['result'][mex]['amount_due']) * float(payment['charge']))/100)
                                        management_year_expense = management_year_expense +  \
                                            weeks_leased*float((
                                                float(owner_management_year_expense['result'][mex]['amount_paid']) * float(payment['charge']))/100)
                                    elif payment['frequency'] == 'Biweekly':
                                        management_year_expected_expense = management_year_expected_expense + weeks_leased/2 * \
                                            ((
                                                float(owner_management_year_expense['result'][mex]['amount_due']) * float(payment['charge']))/100)
                                        management_year_expense = management_year_expense +  \
                                            weeks_leased/2 * \
                                            ((
                                                float(owner_management_year_expense['result'][mex]['amount_paid']) * float(payment['charge']))/100)
                                    elif payment['frequency'] == 'Monthly':
                                        management_year_expected_expense = management_year_expected_expense + months_leased * \
                                            ((
                                                float(owner_management_year_expense['result'][mex]['amount_due']) * float(payment['charge']))/100)
                                        management_year_expense = management_year_expense + months_leased *  \
                                            (
                                                float(owner_management_year_expense['result'][mex]['amount_paid']) * float(payment['charge']))/100
                                    elif payment['frequency'] == 'Annually':

                                        management_year_expected_expense = management_year_expected_expense +  \
                                            (
                                                float(owner_management_year_expense['result'][mex]['amount_due']) * float(payment['charge']))/100
                                        management_year_expense = management_year_expense +  \
                                            (
                                                float(owner_management_year_expense['result'][mex]['amount_paid']) * float(payment['charge']))/100
                                    elif payment['frequency'] == 'One-time':

                                        management_year_expected_expense = management_year_expected_expense +  \
                                            (
                                                float(owner_management_year_expense['result'][mex]['amount_due']) * float(payment['charge']))/100
                                        management_year_expense = management_year_expense +  \
                                            (
                                                float(owner_management_year_expense['result'][mex]['amount_paid']) * float(payment['charge']))/100
                                    else:
                                        print('do nothing')
                            elif payment['fee_type'] == '$':
                                if payment['frequency'] == 'Weekly':
                                    management_year_expected_expense = management_year_expected_expense + weeks_leased * \
                                        float(payment['charge'])
                                    management_year_expense = management_year_expense + weeks_leased * \
                                        float(payment['charge'])
                                elif payment['frequency'] == 'Biweekly':
                                    management_year_expected_expense = management_year_expected_expense + weeks_leased/2 * \
                                        float(payment['charge'])
                                    management_year_expense = management_year_expense + weeks_leased/2 * \
                                        float(payment['charge'])
                                elif payment['frequency'] == 'Monthly':
                                    management_year_expected_expense = management_year_expected_expense + months_leased *  \
                                        float(payment['charge'])
                                    management_year_expense = management_year_expense + \
                                        float(payment['charge'])
                                elif payment['frequency'] == 'Annually':
                                    management_year_expected_expense = management_year_expected_expense + \
                                        float(payment['charge'])
                                    management_year_expense = management_year_expense + \
                                        float(
                                            payment['charge'])
                                elif payment['frequency'] == 'One-time':
                                    management_year_expected_expense = management_year_expected_expense +  \
                                        float(payment['charge'])
                                    management_year_expense = management_year_expense + \
                                        float(
                                            payment['charge'])

                                else:
                                    print('do nothing')
                            else:
                                print('do nothing')
            if len(response['result']['owner_expense_yearly']) > 0:
                for ore in range(len(response['result']['owner_expense_yearly'])):
                    # number of months a property has been active
                    delta_active = relativedelta((datetime.strptime(
                        response['result']['owner_revenue_yearly'][ore]['active_date'], '%Y-%m-%d')), datetime.now())
                    months_active = abs(delta_active.months +
                                        (delta_active.years * 12))
                    # number of months a property has been under an active lease
                    delta_leased = relativedelta((datetime.strptime(
                        response['result']['owner_revenue_yearly'][ore]['lease_start'], '%Y-%m-%d')), datetime.now())

                    months_leased = abs(delta_leased.months +
                                        (delta_leased.years * 12))
                    # number of weeks in the current month
                    weeks_current_month = len(
                        calendar.monthcalendar(today.year, int(today.strftime("%m"))))
                    # number of weeks a property has been active
                    weeks_active = round((abs(today - datetime.strptime(
                        response['result']['owner_revenue_yearly'][ore]['active_date'], '%Y-%m-%d').date()).days)/7, 1)
                    # number of weeks a property has been under an active lease
                    weeks_leased = round((abs(today - datetime.strptime(
                        response['result']['owner_revenue_yearly'][ore]['lease_start'], '%Y-%m-%d').date()).days)/7, 1)

                    # if expenses type is MAINTAINENCE
                    if response['result']['owner_expense_yearly'][ore]['purchase_type'] == 'MAINTENANCE':
                        # if maintenance monthly
                        if response['result']['owner_expense_yearly'][ore]['purchase_frequency'] == 'Monthly':
                            # if maintenance monthly once a month
                            if response['result']['owner_expense_yearly'][ore]['payment_frequency'] == 'Once a month' or response['result']['owner_expense_yearly'][ore]['payment_frequency'] is None:

                                maintenance_year_expense = maintenance_year_expense + months_active * \
                                    (response['result']['owner_expense_yearly']
                                        [ore]['amount_paid'])
                                maintenance_year_expected_expense = maintenance_year_expected_expense + months_active * \
                                    (response['result']['owner_expense_yearly']
                                        [ore]['amount_due'])
                                # if maintenance monthly twice a month
                            elif response['result']['owner_expense_yearly'][ore]['payment_frequency'] == 'Twice a month':

                                maintenance_year_expense = maintenance_year_expense + 2*months_active * \
                                    (response['result']['owner_expense_yearly']
                                        [ore]['amount_paid'])
                                maintenance_year_expected_expense = maintenance_year_expected_expense + \
                                    2*months_active * \
                                    (response['result']['owner_expense_yearly']
                                        [ore]['amount_due'])
                            else:
                                print('do nothing')
                            # if maintenance annually
                        elif response['result']['owner_expense_yearly'][ore]['purchase_frequency'] == 'Annually':
                            print('in maintenance annually')
                            # if maintenance annually once a year
                            if response['result']['owner_expense_yearly'][ore]['payment_frequency'] == 'Once a year':
                                maintenance_year_expense = maintenance_year_expense + \
                                    (response['result']['owner_expense_yearly']
                                        [ore]['amount_paid'])
                                maintenance_year_expected_expense = maintenance_year_expected_expense + \
                                    response['result']['owner_expense_yearly'][ore]['amount_due']
                            # if maintenance annually twice a year
                            elif response['result']['owner_expense_yearly'][ore]['payment_frequency'] == 'Twice a year':
                                maintenance_year_expense = maintenance_year_expense + 2 * \
                                    (response['result']['owner_expense_yearly']
                                        [ore]['amount_paid'])
                                maintenance_year_expected_expense = maintenance_year_expected_expense + \
                                    2*response['result']['owner_expense_yearly'][ore]['amount_due']
                            else:
                                print('do nothing')
                        # if maintenance one-time
                        else:
                            maintenance_year_expense = maintenance_expense + \
                                response['result']['owner_expense_yearly'][ore]['amount_paid']
                            maintenance_year_expected_expense = maintenance_year_expected_expense + \
                                response['result']['owner_expense_yearly'][ore]['amount_due']
                    # if management
                    if response['result']['owner_expense_yearly'][ore]['purchase_type'] == 'MANAGEMENT':
                        print("MANAGEMENT")
                        # if management monthly
                        if response['result']['owner_expense_yearly'][ore]['purchase_frequency'] == 'Monthly':
                            # if management monthly once a month
                            if response['result']['owner_expense_yearly'][ore]['payment_frequency'] == 'Once a month' or response['result']['owner_expense_yearly'][ore]['payment_frequency'] is None:
                                print('here')
                                management_year_expense = management_year_expense + months_active * \
                                    (response['result']['owner_expense_yearly']
                                        [ore]['amount_paid'])
                                management_year_expected_expense = management_year_expected_expense + \
                                    months_active * \
                                    response['result']['owner_expense_yearly'][ore]['amount_due']
                                # if management monthly twice a month
                            elif response['result']['owner_expense_yearly'][ore]['payment_frequency'] == 'Twice a month':
                                management_year_expense = management_year_expense + 2*months_active * \
                                    (response['result']['owner_expense_yearly']
                                        [ore]['amount_paid'])
                                management_year_expected_expense = management_year_expected_expense + \
                                    2*months_active * \
                                    (response['result']['owner_expense_yearly']
                                        [ore]['amount_due'])
                            else:
                                print('do nothing')
                            # if management annually
                        elif response['result']['owner_expense_yearly'][ore]['purchase_frequency'] == 'Annually':
                            # if management annually once a year
                            if response['result']['owner_expense_yearly'][ore]['payment_frequency'] == 'Once a year':
                                management_year_expense = management_year_expense +  \
                                    (response['result']['owner_expense_yearly']
                                        [ore]['amount_paid'])
                                management_year_expected_expense = management_year_expected_expense + \
                                    response['result']['owner_expense_yearly'][ore]['amount_due']
                            # if management annually twice a year
                            elif response['result']['owner_expense_yearly'][ore]['payment_frequency'] == 'Twice a year':
                                management_year_expense = management_year_expense + 2 * \
                                    (response['result']['owner_expense_yearly']
                                        [ore]['amount_paid'])
                                management_year_expected_expense = management_year_expected_expense + \
                                    2*response['result']['owner_expense_yearly'][ore]['amount_due']
                            else:
                                print('do nothing')
                        # if management one-time
                        else:
                            management_year_expense = management_year_expense + \
                                response['result']['owner_expense_yearly'][ore]['amount_paid']
                            management_year_expected_expense = management_year_expected_expense + \
                                response['result']['owner_expense_yearly'][ore]['amount_due']

                    if response['result']['owner_expense_yearly'][ore]['purchase_type'] == 'REPAIRS':
                        # if repairs monthly
                        if response['result']['owner_expense_yearly'][ore]['purchase_frequency'] == 'Monthly':
                            # if repairs monthly once a month
                            if response['result']['owner_expense_yearly'][ore]['payment_frequency'] == 'Once a month' or response['result']['owner_expense_yearly'][ore]['payment_frequency'] is None:
                                repairs_year_expense = repairs_year_expense + months_active * \
                                    (response['result']['owner_expense_yearly']
                                        [ore]['amount_paid'])
                                repairs_year_expected_expense = repairs_year_expected_expense + months_active * \
                                    response['result']['owner_expense_yearly'][ore]['amount_due']
                                # if repairs monthly twice a month
                            elif response['result']['owner_expense_yearly'][ore]['payment_frequency'] == 'Twice a month':
                                repairs_year_expense = repairs_year_expense + 2*months_active * \
                                    (response['result']['owner_expense_yearly']
                                        [ore]['amount_paid'])
                                repairs_year_expected_expense = repairs_year_expected_expense + \
                                    2*months_active * \
                                    (response['result']['owner_expense_yearly']
                                        [ore]['amount_due'])
                            else:
                                print('do nothing')
                            # if repairs annually
                        elif response['result']['owner_expense_yearly'][ore]['purchase_frequency'] == 'Annually':
                            # if repairs annually once a year
                            if response['result']['owner_expense_yearly'][ore]['payment_frequency'] == 'Once a year':
                                repairs_year_expense = repairs_year_expense + (response['result']['owner_expense_yearly']
                                                                               [ore]['amount_paid'])
                                repairs_year_expected_expense = repairs_year_expected_expense + \
                                    response['result']['owner_expense_yearly'][ore]['amount_due']
                            # if repairs annually twice a year
                            elif response['result']['owner_expense_yearly'][ore]['payment_frequency'] == 'Twice a year':
                                repairs_year_expense = repairs_year_expense + 2 * \
                                    (response['result']['owner_expense_yearly']
                                        [ore]['amount_paid'])
                                repairs_year_expected_expense = repairs_year_expected_expense + 2 * \
                                    response['result']['owner_expense_yearly'][ore]['amount_due']
                            else:
                                print('do nothing')
                        # if repairs one-time
                        else:
                            repairs_year_expense = repairs_year_expense + \
                                response['result']['owner_expense_yearly'][ore]['amount_paid']
                            repairs_year_expected_expense = repairs_year_expected_expense + \
                                response['result']['owner_expense_yearly'][ore]['amount_due']
                    if response['result']['owner_expense_yearly'][ore]['purchase_type'] == 'UTILITY':
                        if response['result']['owner_expense_yearly'][ore]['purchase_frequency'] == 'Weekly':
                            utility_year_expected_expense = utility_year_expected_expense + \
                                weeks_leased*int(response['result']['owner_expense_yearly']
                                                 [ore]['amount_due'])
                            utility_year_expense = utility_year_expense + \
                                weeks_leased*int(response['result']['owner_expense_yearly']
                                                 [ore]['amount_paid'])
                        elif response['result']['owner_expense_yearly'][ore]['purchase_frequency'] == 'Biweekly':
                            utility_year_expected_expense = utility_year_expected_expense + \
                                weeks_leased/2 * \
                                int(response['result']['owner_expense_yearly']
                                    [ore]['amount_due'])
                            utility_year_expense = utility_year_expense + \
                                weeks_leased/2 * \
                                int(response['result']['owner_expense_yearly']
                                    [ore]['amount_paid'])
                        elif response['result']['owner_expense_yearly'][ore]['purchase_frequency'] == 'Monthly':
                            utility_year_expected_expense = utility_year_expected_expense + months_leased * \
                                response['result']['owner_expense_yearly'][ore]['amount_due']
                            utility_year_expense = utility_year_expense + months_leased * \
                                response['result']['owner_expense_yearly'][ore]['amount_paid']
                        elif response['result']['owner_expense_yearly'][ore]['purchase_frequency'] == 'Annually':
                            utility_year_expected_expense = utility_year_expected_expense + \
                                response['result']['owner_expense_yearly'][ore]['amount_due']
                            utility_year_expense = utility_year_expense + \
                                response['result']['owner_expense_yearly'][ore]['amount_paid']
                        else:
                            utility_year_expected_expense = utility_year_expected_expense + \
                                response['result']['owner_expense_yearly'][ore]['amount_due']
                            utility_year_expense = utility_year_expense + \
                                response['result']['owner_expense_yearly'][ore]['amount_paid']
            response['result']['maintenance_year_expense'] = round(
                maintenance_year_expense, 2)
            response['result']['management_year_expense'] = round(
                management_year_expense, 2)
            response['result']['repairs_year_expense'] = round(
                repairs_year_expense, 2)
            response['result']['utility_year_expense'] = round(
                utility_year_expense, 2)
            response['result']['maintenance_year_expected_expense'] = round(
                maintenance_year_expected_expense, 2)
            response['result']['management_year_expected_expense'] = round(
                management_year_expected_expense, 2)
            response['result']['repairs_year_expected_expense'] = round(
                repairs_year_expected_expense, 2)
            response['result']['utility_year_expected_expense'] = round(
                utility_year_expected_expense, 2)

            owner_property_expenses = db.execute("""
                        SELECT  pr.property_uid, pr.address,pr.unit, pr.mortgages, pr.taxes, pr.insurance, pr.active_date FROM properties pr
                        WHERE pr.owner_id = \'""" + filterValue + """\'
                        AND pr.mortgages is not null OR  pr.taxes is not null OR  pr.insurance is not null
                        """)

            # monthly expense for the property to include mortgage
            if len(owner_property_expenses['result']) > 0:
                for ope in range(len(owner_property_expenses['result'])):
                    owner_property_expenses['result'][ope]['mortgage_year_expense'] = 0
                    owner_property_expenses['result'][ope]['mortgage_expense'] = 0
                    owner_property_expenses['result'][ope]['taxes_year_expense'] = 0
                    owner_property_expenses['result'][ope]['taxes_expense'] = 0
                    owner_property_expenses['result'][ope]['insurance_year_expense'] = 0
                    owner_property_expenses['result'][ope]['insurance_expense'] = 0
                    # number of months a property has been active
                    delta_active = relativedelta((datetime.strptime(
                        owner_property_expenses['result'][ope]['active_date'], '%Y-%m-%d')), datetime.now())
                    months_active = abs(delta_active.months +
                                        (delta_active.years * 12))
                    # number of weeks in the current month
                    weeks_current_month = len(
                        calendar.monthcalendar(today.year, int(today.strftime("%m"))))
                    # number of weeks a property has been active
                    weeks_active = round((abs(today - datetime.strptime(
                        owner_property_expenses['result'][ope]['active_date'], '%Y-%m-%d').date()).days)/7, 1)

                    if owner_property_expenses['result'][ope]['mortgages'] is not None:
                        # if mortgage monthly
                        if json.loads(owner_property_expenses['result'][ope]['mortgages'])['frequency'] == 'Monthly':
                            # if mortgage monthly and once a month
                            if json.loads(owner_property_expenses['result'][ope]['mortgages'])['frequency_of_payment'] == 'Once a month':
                                mortgage_year_expense = mortgage_year_expense + (months_active*(int(json.loads(owner_property_expenses['result'][ope]['mortgages'])[
                                    'amount'])))
                                mortgage_expense = mortgage_expense + \
                                    int(json.loads(
                                        owner_property_expenses['result'][ope]['mortgages'])['amount'])
                                owner_property_expenses['result'][ope]['mortgage_year_expense'] = (months_active*(int(json.loads(owner_property_expenses['result'][ope]['mortgages'])[
                                    'amount'])))
                                owner_property_expenses['result'][ope]['mortgage_expense'] = int(json.loads(
                                    owner_property_expenses['result'][ope]['mortgages'])['amount'])
                        # if mortgage monthly and twice a month
                            elif json.loads(owner_property_expenses['result'][ope]['mortgages'])['frequency_of_payment'] == 'Twice a month':
                                mortgage_year_expense = mortgage_year_expense + (2*months_active*(int(json.loads(owner_property_expenses['result'][ope]['mortgages'])[
                                    'amount'])))
                                mortgage_expense = mortgage_expense + 2 * \
                                    (int(json.loads(
                                        owner_property_expenses['result'][ope]['mortgages'])['amount']))
                                owner_property_expenses['result'][ope]['mortgage_year_expense'] = (2 * months_active*(int(json.loads(owner_property_expenses['result'][ope]['mortgages'])[
                                    'amount'])))
                                owner_property_expenses['result'][ope]['mortgage_expense'] = 2 * int(json.loads(
                                    owner_property_expenses['result'][ope]['mortgages'])['amount'])
                        # if mortgage weekly
                        elif json.loads(owner_property_expenses['result'][ope]['mortgages'])['frequency'] == 'Weekly':
                            # if mortgage weekly and once a week
                            if json.loads(owner_property_expenses['result'][ope]['mortgages'])['frequency_of_payment'] == 'Once a week':
                                mortgage_year_expense = mortgage_year_expense + (weeks_active*(int(json.loads(owner_property_expenses['result'][ope]['mortgages'])[
                                    'amount'])))
                                mortgage_expense = mortgage_expense + \
                                    weeks_current_month*(int(json.loads(
                                        owner_property_expenses['result'][ope]['mortgages'])['amount']))
                                owner_property_expenses['result'][ope]['mortgage_year_expense'] = (weeks_active*(int(json.loads(owner_property_expenses['result'][ope]['mortgages'])[
                                    'amount'])))
                                owner_property_expenses['result'][ope]['mortgage_expense'] = weeks_current_month * int(json.loads(
                                    owner_property_expenses['result'][ope]['mortgages'])['amount'])
                            # if mortgage weekly and every other week
                            elif json.loads(owner_property_expenses['result'][ope]['mortgages'])['frequency_of_payment'] == 'Every other week':
                                mortgage_year_expense = mortgage_year_expense + ((weeks_active/2)*(int(json.loads(owner_property_expenses['result'][ope]['mortgages'])[
                                    'amount'])))
                                mortgage_expense = mortgage_expense + (weeks_current_month/2) * \
                                    (int(json.loads(
                                        owner_property_expenses['result'][ope]['mortgages'])['amount']))
                                owner_property_expenses['result'][ope]['mortgage_year_expense'] = (weeks_active/2*(int(json.loads(owner_property_expenses['result'][ope]['mortgages'])[
                                    'amount'])))
                                owner_property_expenses['result'][ope]['mortgage_expense'] = weeks_current_month/2 * int(json.loads(
                                    owner_property_expenses['result'][ope]['mortgages'])['amount'])

                    # monthly expense for the property to include taxes
                    if owner_property_expenses['result'][ope]['taxes'] is not None:
                        if len(eval(owner_property_expenses['result'][ope]['taxes'])) > 0:
                            for te in range(len(eval(owner_property_expenses['result'][ope]['taxes']))):

                                # if tax monthly
                                if eval(owner_property_expenses['result'][ope]['taxes'])[te]['frequency'] == 'Monthly':
                                    # if taxes monthly and once a month
                                    if eval(owner_property_expenses['result'][ope]['taxes'])[te]['frequency_of_payment'] == 'Once a month':
                                        print('in once a month')
                                        taxes_year_expense = taxes_year_expense + (months_active * int(eval(owner_property_expenses['result'][ope]
                                                                                                            ['taxes'])[te]['amount']))
                                        taxes_expense = taxes_expense + \
                                            int(eval(owner_property_expenses['result'][ope]['taxes'])[
                                                te]['amount'])
                                        owner_property_expenses['result'][ope]['taxes_year_expense'] = owner_property_expenses['result'][ope]['taxes_year_expense'] + (
                                            months_active * int(eval(owner_property_expenses['result'][ope]['taxes'])[te]['amount']))
                                        owner_property_expenses['result'][ope]['taxes_expense'] = owner_property_expenses['result'][ope]['taxes_expense'] + int(
                                            eval(owner_property_expenses['result'][ope]['taxes'])[te]['amount'])
                                # if taxes monthly and once a month
                                    elif eval(owner_property_expenses['result'][ope]['taxes'])[te]['frequency_of_payment'] == 'Twice a month':
                                        taxes_year_expense = taxes_year_expense + (2*months_active * int(eval(owner_property_expenses['result'][ope]
                                                                                                              ['taxes'])[te]['amount']))
                                        taxes_expense = taxes_expense + \
                                            2*(int(eval(owner_property_expenses['result'][ope]['taxes'])[
                                                te]['amount']))
                                        owner_property_expenses['result'][ope]['taxes_year_expense'] = owner_property_expenses['result'][ope]['taxes_year_expense'] + (
                                            2*months_active * int(eval(owner_property_expenses['result'][ope]['taxes'])[te]['amount']))
                                        owner_property_expenses['result'][ope]['taxes_expense'] = owner_property_expenses['result'][ope]['taxes_expense'] + 2*int(
                                            eval(owner_property_expenses['result'][ope]['taxes'])[te]['amount'])
                                    # if tax Annually
                                elif eval(owner_property_expenses['result'][ope]['taxes'])[te]['frequency'] == 'Annually':

                                    # if taxes annually and once a year
                                    if eval(owner_property_expenses['result'][ope]['taxes'])[te]['frequency_of_payment'] == 'Once a year':

                                        if date.fromisoformat(eval(owner_property_expenses['result'][ope]['taxes'])[te]['next_date']).year == today.year:
                                            taxes_year_expense = taxes_year_expense + (int(eval(owner_property_expenses['result'][ope]
                                                                                                ['taxes'])[te]['amount']))
                                            owner_property_expenses['result'][ope]['taxes_year_expense'] = owner_property_expenses['result'][ope]['taxes_year_expense'] + (int(eval(owner_property_expenses['result'][ope]
                                                                                                                                                                                    ['taxes'])[te]['amount']))

                                        if date.fromisoformat(eval(owner_property_expenses['result'][ope]['taxes'])[te]['next_date']).month == today.month:
                                            taxes_expense = taxes_expense + \
                                                int(eval(owner_property_expenses['result'][ope]['taxes'])[
                                                    te]['amount'])
                                            owner_property_expenses['result'][ope]['taxes_expense'] = owner_property_expenses['result'][ope]['taxes_expense'] + int(eval(owner_property_expenses['result'][ope]['taxes'])[
                                                te]['amount'])
                                    # if taxes annually and twice a year
                                    elif eval(owner_property_expenses['result'][ope]['taxes'])[te]['frequency_of_payment'] == 'Twice a year':
                                        print('in twice a year')
                                        if date.fromisoformat(eval(owner_property_expenses['result'][ope]['taxes'])[te]['next_date']).year == today.year:
                                            taxes_year_expense = taxes_year_expense + (2*(int(eval(owner_property_expenses['result'][ope]
                                                                                                   ['taxes'])[te]['amount'])))
                                            owner_property_expenses['result'][ope]['taxes_year_expense'] = owner_property_expenses['result'][ope]['taxes_year_expense'] + 2*(int(eval(owner_property_expenses['result'][ope]
                                                                                                                                                                                      ['taxes'])[te]['amount']))
                                        if date.fromisoformat(eval(owner_property_expenses['result'][ope]['taxes'])[te]['next_date']).month == today.month or (date.fromisoformat(eval(owner_property_expenses['result'][ope]['taxes'])[te]['next_date']) + relativedelta(months=6)).month == today.month:
                                            taxes_expense = taxes_expense + (int(eval(owner_property_expenses['result'][ope]['taxes'])[
                                                te]['amount']))
                                            owner_property_expenses['result'][ope]['taxes_expense'] = owner_property_expenses['result'][ope]['taxes_expense'] + (int(eval(owner_property_expenses['result'][ope]['taxes'])[
                                                te]['amount']))
                        # monthly expense for the property to include insurance
                    if owner_property_expenses['result'][ope]['insurance'] is not None:
                        if len(eval(owner_property_expenses['result'][ope]['insurance'])) > 0:
                            for te in range(len(eval(owner_property_expenses['result'][ope]['insurance']))):

                                # if insurance monthly
                                if eval(owner_property_expenses['result'][ope]['insurance'])[te]['frequency'] == 'Monthly':

                                    # if insurance monthly and once a month
                                    if eval(owner_property_expenses['result'][ope]['insurance'])[te]['frequency_of_payment'] == 'Once a month':
                                        insurance_year_expense = insurance_year_expense + (months_active * int(eval(owner_property_expenses['result'][ope]
                                                                                                                    ['insurance'])[te]['amount']))
                                        insurance_expense = insurance_expense + \
                                            int(eval(owner_property_expenses['result'][ope]['insurance'])[
                                                te]['amount'])
                                        owner_property_expenses['result'][ope]['insurance_year_expense'] = owner_property_expenses['result'][ope]['insurance_year_expense'] + (
                                            months_active * int(eval(owner_property_expenses['result'][ope]['insurance'])[te]['amount']))
                                        owner_property_expenses['result'][ope]['insurance_expense'] = owner_property_expenses['result'][ope]['insurance_expense'] + int(
                                            eval(owner_property_expenses['result'][ope]['insurance'])[te]['amount'])
                                # if insurance monthly and once a month
                                    elif eval(owner_property_expenses['result'][ope]['insurance'])[te]['frequency_of_payment'] == 'Twice a month':
                                        insurance_year_expense = insurance_year_expense + (2*months_active * int(eval(owner_property_expenses['result'][ope]
                                                                                                                      ['insurance'])[te]['amount']))
                                        insurance_expense = insurance_expense + \
                                            2*(int(eval(owner_property_expenses['result'][ope]['insurance'])[
                                                te]['amount']))
                                        owner_property_expenses['result'][ope]['insurance_year_expense'] = owner_property_expenses['result'][ope]['insurance_year_expense'] + (
                                            2*months_active * int(eval(owner_property_expenses['result'][ope]['insurance'])[te]['amount']))
                                        owner_property_expenses['result'][ope]['insurance_expense'] = owner_property_expenses['result'][ope]['insurance_expense'] + 2*int(
                                            eval(owner_property_expenses['result'][ope]['insurance'])[te]['amount'])
                                    # if insurance Annually
                                elif eval(owner_property_expenses['result'][ope]['insurance'])[te]['frequency'] == 'Annually':

                                    # if insurance annually and once a year
                                    if eval(owner_property_expenses['result'][ope]['insurance'])[te]['frequency_of_payment'] == 'Once a year':
                                        if date.fromisoformat(eval(owner_management_expense['result'][ope]['insurance'])[te]['next_date']).year == today.year:
                                            insurance_year_expense = insurance_year_expense + (int(eval(owner_property_expenses['result'][ope]
                                                                                                        ['insurance'])[te]['amount']))
                                            owner_property_expenses['result'][ope]['insurance_year_expense'] = owner_property_expenses['result'][ope]['insurance_year_expense'] + (int(eval(owner_property_expenses['result'][ope]
                                                                                                                                                                                            ['insurance'])[te]['amount']))
                                        if date.fromisoformat(eval(owner_management_expense['result'][ope]['insurance'])[te]['next_date']).month == today.month:
                                            insurance_expense = insurance_expense + \
                                                int(eval(owner_property_expenses['result'][ope]['insurance'])[
                                                    te]['amount'])
                                            owner_property_expenses['result'][ope]['insurance_expense'] = owner_property_expenses['result'][ope]['insurance_expense'] + (int(eval(owner_property_expenses['result'][ope]
                                                                                                                                                                                  ['insurance'])[te]['amount']))
                                    # if insurance annually and twice a year
                                    elif eval(owner_property_expenses['result'][ope]['insurance'])[te]['frequency_of_payment'] == 'Twice a year':
                                        if date.fromisoformat(eval(owner_management_expense['result'][ope]['insurance'])[te]['next_date']).year == today.year:
                                            insurance_year_expense = insurance_year_expense + (2*(int(eval(owner_property_expenses['result'][ope]
                                                                                                           ['insurance'])[te]['amount'])))
                                            owner_property_expenses['result'][ope]['insurance_year_expense'] = owner_property_expenses['result'][ope]['insurance_year_expense'] + 2*(int(eval(owner_property_expenses['result'][ope]
                                                                                                                                                                                            ['insurance'])[te]['amount']))
                                        if date.fromisoformat(eval(owner_management_expense['result'][ope]['insurance'])[te]['next_date']).month == today.month or (date.fromisoformat(eval(owner_management_expense['result'][ope]['insurance'])[te]['next_date']) + relativedelta(months=6)).month == today.month:
                                            insurance_expense = insurance_expense + \
                                                (int(eval(owner_property_expenses['result'][ope]['insurance'])[
                                                    te]['amount']))
                                            owner_property_expenses['result'][ope]['insurance_expense'] = owner_property_expenses['result'][ope]['insurance_expense'] + (int(eval(owner_property_expenses['result'][ope]
                                                                                                                                                                                  ['insurance'])[te]['amount']))
            response['result']['mortgage_expense'] = mortgage_expense
            response['result']['mortgage_year_expense'] = mortgage_year_expense
            response['result']['taxes_expense'] = taxes_expense
            response['result']['taxes_year_expense'] = taxes_year_expense
            response['result']['insurance_expense'] = insurance_expense
            response['result']['insurance_year_expense'] = insurance_year_expense
            response['result']['owner_property_expense'] = list(
                owner_property_expenses['result'])
        return response


class OwnerCashflowProperty(Resource):
    def get(self):
        response = {}
        response['message'] = 'Successfully executed SQL query'
        response['code'] = 200
        response['result'] = {}
        filters = ['property_id']
        where = {}

        with connect() as db:
            filterValue = request.args.get(filters[0])
            print(filterValue)
            today = date.today()

            # initialize revenue variables

            rental_revenue = 0
            extra_revenue = 0
            utility_revenue = 0
            rental_expected_revenue = 0
            extra_expected_revenue = 0
            utility_expected_revenue = 0

            rental_year_revenue = 0
            extra_year_revenue = 0
            utility_year_revenue = 0
            rental_year_expected_revenue = 0
            extra_year_expected_revenue = 0
            utility_year_expected_revenue = 0

            # owner rental and extra charges revenue monthly
            owner_rental_revenue = db.execute("""
            SELECT * FROM purchases pu
            LEFT JOIN payments pa
            ON pa.pay_purchase_id = pu.purchase_uid
            LEFT JOIN properties pr
            ON pu.pur_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN rentals r
            ON r.rental_property_id LIKE CONCAT('%', pr.property_uid, '%')
            WHERE pr.property_uid = \'""" + filterValue + """\'
            AND ({fn MONTHNAME(pu.next_payment)} = {fn MONTHNAME(now())} AND YEAR(pu.next_payment) = YEAR(now()))
            AND (pu.purchase_type= "RENT" OR pu.purchase_type= "EXTRA CHARGES")
            AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED')""")

            response['result']['owner_revenue'] = list(
                owner_rental_revenue['result'])

            # owner utility revenue montlhy
            owner_utility_revenue = db.execute("""
            SELECT * FROM purchases pu
            LEFT JOIN payments pa
            ON pa.pay_purchase_id = pu.purchase_uid
            LEFT JOIN properties pr
            ON pu.pur_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN rentals r
            ON r.rental_property_id LIKE CONCAT('%', pr.property_uid, '%')
            WHERE pr.property_uid = \'""" + filterValue + """\'
            AND ({fn MONTHNAME(pu.next_payment)} = {fn MONTHNAME(now())} AND YEAR(pu.next_payment) = YEAR(now()))
            AND (pu.purchase_type="UTILITY")
            AND pu.receiver = \'""" + filterValue + """\'
            AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED') """)

            response['result']['owner_revenue'] = response['result']['owner_revenue'] + list(
                owner_utility_revenue['result'])

            if len(response['result']['owner_revenue']) > 0:
                for ore in range(len(response['result']['owner_revenue'])):
                    # number of weeks in the current month
                    weeks_current_month = len(
                        calendar.monthcalendar(today.year, int(today.strftime("%m"))))

                    if response['result']['owner_revenue'][ore]['purchase_type'] == 'RENT':
                        if response['result']['owner_revenue'][ore]['purchase_frequency'] == 'Weekly':
                            rental_expected_revenue = rental_expected_revenue + \
                                weeks_current_month*int(response['result']['owner_revenue']
                                                        [ore]['amount_due'])
                            rental_revenue = rental_revenue + \
                                weeks_current_month*int(response['result']['owner_revenue']
                                                        [ore]['amount_paid'])

                        elif response['result']['owner_revenue'][ore]['purchase_frequency'] == 'Biweekly':
                            rental_expected_revenue = rental_expected_revenue + \
                                weeks_current_month/2 * \
                                int(response['result']['owner_revenue']
                                    [ore]['amount_due'])
                            rental_revenue = rental_revenue + \
                                weeks_current_month/2 * \
                                int(response['result']['owner_revenue']
                                    [ore]['amount_paid'])
                        elif response['result']['owner_revenue'][ore]['purchase_frequency'] == 'Monthly':
                            rental_expected_revenue = rental_expected_revenue + \
                                response['result']['owner_revenue'][ore]['amount_due']
                            rental_revenue = rental_revenue + \
                                response['result']['owner_revenue'][ore]['amount_paid']

                        elif response['result']['owner_revenue'][ore]['purchase_frequency'] == 'Annually':
                            rental_expected_revenue = rental_expected_revenue + \
                                response['result']['owner_revenue'][ore]['amount_due']
                            rental_revenue = rental_revenue + \
                                response['result']['owner_revenue'][ore]['amount_paid']
                        else:
                            rental_expected_revenue = rental_expected_revenue + \
                                response['result']['owner_revenue'][ore]['amount_due']
                            rental_revenue = rental_revenue + \
                                response['result']['owner_revenue'][ore]['amount_paid']

                    if response['result']['owner_revenue'][ore]['purchase_type'] == 'EXTRA CHARGES':
                        if response['result']['owner_revenue'][ore]['purchase_frequency'] == 'Weekly':
                            extra_expected_revenue = extra_expected_revenue + \
                                weeks_current_month*int(response['result']['owner_revenue']
                                                        [ore]['amount_due'])
                            extra_revenue = extra_revenue + \
                                weeks_current_month*int(response['result']['owner_revenue']
                                                        [ore]['amount_paid'])
                        elif response['result']['owner_revenue'][ore]['purchase_frequency'] == 'Biweekly':
                            extra_expected_revenue = extra_expected_revenue + \
                                weeks_current_month/2 * \
                                int(response['result']['owner_revenue']
                                    [ore]['amount_due'])
                            extra_revenue = extra_revenue + \
                                weeks_current_month/2 * \
                                int(response['result']['owner_revenue']
                                    [ore]['amount_paid'])
                        elif response['result']['owner_revenue'][ore]['purchase_frequency'] == 'Monthly':
                            extra_expected_revenue = extra_expected_revenue + \
                                response['result']['owner_revenue'][ore]['amount_due']
                            extra_revenue = extra_revenue + \
                                response['result']['owner_revenue'][ore]['amount_paid']
                        elif response['result']['owner_revenue'][ore]['purchase_frequency'] == 'Annually':

                            extra_expected_revenue = extra_expected_revenue + \
                                response['result']['owner_revenue'][ore]['amount_due']
                            extra_revenue = extra_revenue + \
                                response['result']['owner_revenue'][ore]['amount_paid']
                        else:
                            extra_expected_revenue = extra_expected_revenue + \
                                response['result']['owner_revenue'][ore]['amount_due']
                            extra_revenue = extra_revenue + \
                                response['result']['owner_revenue'][ore]['amount_paid']

                    if response['result']['owner_revenue'][ore]['purchase_type'] == 'UTILITY':
                        if response['result']['owner_revenue'][ore]['purchase_frequency'] == 'Weekly':
                            utility_expected_revenue = utility_expected_revenue + \
                                weeks_current_month*int(response['result']['owner_revenue']
                                                        [ore]['amount_due'])
                            utility_revenue = utility_revenue + \
                                weeks_current_month*int(response['result']['owner_revenue']
                                                        [ore]['amount_paid'])
                        elif response['result']['owner_revenue'][ore]['purchase_frequency'] == 'Biweekly':
                            utility_expected_revenue = utility_expected_revenue + \
                                weeks_current_month/2 * \
                                int(response['result']['owner_revenue']
                                    [ore]['amount_due'])
                            utility_revenue = utility_revenue + \
                                weeks_current_month/2 * \
                                int(response['result']['owner_revenue']
                                    [ore]['amount_paid'])
                        elif response['result']['owner_revenue'][ore]['purchase_frequency'] == 'Monthly':
                            utility_expected_revenue = utility_expected_revenue + \
                                response['result']['owner_revenue'][ore]['amount_due']
                            utility_revenue = utility_revenue + \
                                response['result']['owner_revenue'][ore]['amount_paid']
                        elif response['result']['owner_revenue'][ore]['purchase_frequency'] == 'Annually':
                            utility_expected_revenue = utility_expected_revenue + \
                                response['result']['owner_revenue'][ore]['amount_due']
                            utility_revenue = utility_revenue + \
                                response['result']['owner_revenue'][ore]['amount_paid']
                        else:
                            utility_expected_revenue = utility_expected_revenue + \
                                response['result']['owner_revenue'][ore]['amount_due']
                            utility_revenue = utility_revenue + \
                                response['result']['owner_revenue'][ore]['amount_paid']
            response['result']['rental_revenue'] = round(
                rental_revenue, 2)
            response['result']['rental_expected_revenue'] = round(
                rental_expected_revenue, 2)
            response['result']['extra_revenue'] = round(
                extra_revenue, 2)
            response['result']['extra_expected_revenue'] = round(
                extra_expected_revenue, 2)
            response['result']['utility_revenue'] = round(
                utility_revenue, 2)
            response['result']['utility_expected_revenue'] = round(
                utility_expected_revenue, 2)
            # owner rental and extra charged revenue yearly
            owner_rental_revenue_yearly = db.execute("""
            SELECT * FROM purchases pu
            LEFT JOIN payments pa
            ON pa.pay_purchase_id = pu.purchase_uid
            LEFT JOIN properties pr
            ON pu.pur_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN rentals r
            ON r.rental_property_id LIKE CONCAT('%', pr.property_uid, '%')
            WHERE pr.property_uid = \'""" + filterValue + """\' 
            AND YEAR(pu.next_payment) = YEAR(now())
            AND (pu.purchase_type= "RENT" OR pu.purchase_type= "EXTRA CHARGES")
            AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED')""")

            response['result']['owner_revenue_yearly'] = list(
                owner_rental_revenue_yearly['result'])

            # owner utility revenue yearly
            owner_utility_revenue_yearly = db.execute("""
            SELECT * FROM purchases pu
            LEFT JOIN payments pa
            ON pa.pay_purchase_id = pu.purchase_uid
            LEFT JOIN properties pr
            ON pu.pur_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN rentals r
            ON r.rental_property_id LIKE CONCAT('%', pr.property_uid, '%')
            WHERE pr.property_uid = \'""" + filterValue + """\' 
            AND YEAR(pu.next_payment) = YEAR(now())
            AND (pu.purchase_type="UTILITY")
            AND pu.receiver = \'""" + filterValue + """\'
            AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED') """)

            response['result']['owner_revenue_yearly'] = response['result']['owner_revenue_yearly'] + list(
                owner_utility_revenue_yearly['result'])

            if len(response['result']['owner_revenue_yearly']) > 0:
                for ore in range(len(response['result']['owner_revenue_yearly'])):

                    # number of months a property has been active
                    delta_active = relativedelta((datetime.strptime(
                        response['result']['owner_revenue_yearly'][ore]['active_date'], '%Y-%m-%d')), datetime.now())
                    months_active = abs(delta_active.months +
                                        (delta_active.years * 12))
                    # number of months a property has been under an active lease
                    delta_leased = relativedelta((datetime.strptime(
                        response['result']['owner_revenue_yearly'][ore]['lease_start'], '%Y-%m-%d')), datetime.now())

                    months_leased = abs(delta_leased.months +
                                        (delta_leased.years * 12))
                    # number of weeks in the current month
                    weeks_current_month = len(
                        calendar.monthcalendar(today.year, int(today.strftime("%m"))))
                    # number of weeks a property has been active
                    weeks_active = round((abs(today - datetime.strptime(
                        response['result']['owner_revenue_yearly'][ore]['active_date'], '%Y-%m-%d').date()).days)/7, 1)
                    # number of weeks a property has been under an active lease
                    weeks_leased = round((abs(today - datetime.strptime(
                        response['result']['owner_revenue_yearly'][ore]['lease_start'], '%Y-%m-%d').date()).days)/7, 1)

                    # if revenue type is RENT
                    if response['result']['owner_revenue_yearly'][ore]['purchase_type'] == 'RENT':
                        if response['result']['owner_revenue_yearly'][ore]['purchase_frequency'] == 'Weekly':
                            rental_year_expected_revenue = rental_year_expected_revenue + \
                                weeks_leased*int(response['result']['owner_revenue_yearly']
                                                 [ore]['amount_due'])
                            rental_year_revenue = rental_year_revenue + \
                                weeks_leased*int(response['result']['owner_revenue_yearly']
                                                         [ore]['amount_paid'])

                        elif response['result']['owner_revenue_yearly'][ore]['purchase_frequency'] == 'Biweekly':
                            rental_year_expected_revenue = rental_year_expected_revenue + \
                                weeks_leased/2 * \
                                int(response['result']['owner_revenue_yearly']
                                    [ore]['amount_due'])
                            rental_year_revenue = rental_year_revenue + \
                                weeks_leased/2 * \
                                int(response['result']['owner_revenue_yearly']
                                    [ore]['amount_paid'])
                        elif response['result']['owner_revenue_yearly'][ore]['purchase_frequency'] == 'Monthly':
                            rental_year_expected_revenue = rental_year_expected_revenue + \
                                months_leased * \
                                int(response['result']
                                    ['owner_revenue_yearly'][ore]['amount_due'])
                            rental_year_revenue = rental_year_revenue + \
                                months_leased * \
                                int(response['result']['owner_revenue_yearly']
                                    [ore]['amount_paid'])

                        elif response['result']['owner_revenue_yearly'][ore]['purchase_frequency'] == 'Annually':
                            rental_year_expected_revenue = rental_year_expected_revenue + \
                                response['result']['owner_revenue_yearly'][ore]['amount_due']
                            rental_year_revenue = rental_year_revenue + \
                                response['result']['owner_revenue_yearly'][ore]['amount_paid']
                        else:
                            rental_year_expected_revenue = rental_year_expected_revenue + \
                                response['result']['owner_revenue_yearly'][ore]['amount_due']
                            rental_year_revenue = rental_year_revenue + \
                                response['result']['owner_revenue_yearly'][ore]['amount_paid']

                     # if revenue type is EXTRA CHARGES
                    if response['result']['owner_revenue_yearly'][ore]['purchase_type'] == 'EXTRA CHARGES':
                        if response['result']['owner_revenue_yearly'][ore]['purchase_frequency'] == 'Weekly':
                            extra_year_expected_revenue = extra_year_expected_revenue + \
                                weeks_leased*int(response['result']['owner_revenue_yearly']
                                                         [ore]['amount_due'])
                            extra_year_revenue = extra_year_revenue + \
                                weeks_leased*int(response['result']['owner_revenue_yearly']
                                                         [ore]['amount_paid'])
                        elif response['result']['owner_revenue_yearly'][ore]['purchase_frequency'] == 'Biweekly':
                            extra_year_expected_revenue = extra_year_expected_revenue + \
                                weeks_leased/2 * \
                                int(response['result']['owner_revenue_yearly']
                                    [ore]['amount_due'])
                            extra_year_revenue = extra_year_revenue + \
                                weeks_leased/2 * \
                                int(response['result']['owner_revenue_yearly']
                                    [ore]['amount_paid'])
                        elif response['result']['owner_revenue_yearly'][ore]['purchase_frequency'] == 'Monthly':
                            extra_year_expected_revenue = extra_year_expected_revenue + \
                                months_leased * \
                                int(response['result']
                                    ['owner_revenue_yearly'][ore]['amount_due'])
                            extra_year_revenue = extra_year_revenue + \
                                months_leased * \
                                int(response['result']['owner_revenue_yearly']
                                    [ore]['amount_paid'])
                        elif response['result']['owner_revenue_yearly'][ore]['purchase_frequency'] == 'Annually':

                            extra_year_expected_revenue = extra_year_expected_revenue + \
                                response['result']['owner_revenue_yearly'][ore]['amount_due']
                            extra_year_revenue = extra_year_revenue + \
                                response['result']['owner_revenue_yearly'][ore]['amount_paid']
                        else:
                            extra_year_expected_revenue = extra_year_expected_revenue + \
                                response['result']['owner_revenue_yearly'][ore]['amount_due']
                            extra_year_revenue = extra_year_revenue + \
                                response['result']['owner_revenue_yearly'][ore]['amount_paid']

                     # if revenue type is UTILITY
                    if response['result']['owner_revenue_yearly'][ore]['purchase_type'] == 'UTILITY':
                        if response['result']['owner_revenue_yearly'][ore]['purchase_frequency'] == 'Weekly':
                            utility_year_expected_revenue = utility_year_expected_revenue + \
                                weeks_leased*int(response['result']['owner_revenue_yearly']
                                                         [ore]['amount_due'])
                            utility_year_revenue = utility_year_revenue + \
                                weeks_leased*int(response['result']['owner_revenue_yearly']
                                                         [ore]['amount_paid'])
                        elif response['result']['owner_revenue_yearly'][ore]['purchase_frequency'] == 'Biweekly':
                            utility_year_expected_revenue = utility_year_expected_revenue + \
                                weeks_leased/2 * \
                                int(response['result']['owner_revenue_yearly']
                                    [ore]['amount_due'])
                            utility_year_revenue = utility_year_revenue + \
                                weeks_leased/2 * \
                                int(response['result']['owner_revenue_yearly']
                                    [ore]['amount_paid'])
                        elif response['result']['owner_revenue_yearly'][ore]['purchase_frequency'] == 'Monthly':
                            utility_year_expected_revenue = utility_year_expected_revenue + \
                                months_leased * \
                                int(response['result']
                                    ['owner_revenue_yearly'][ore]['amount_due'])
                            utility_year_revenue = utility_year_revenue + \
                                months_leased * \
                                int(response['result']['owner_revenue_yearly']
                                    [ore]['amount_paid'])
                        elif response['result']['owner_revenue_yearly'][ore]['purchase_frequency'] == 'Annually':
                            utility_year_expected_revenue = utility_year_expected_revenue + \
                                response['result']['owner_revenue_yearly'][ore]['amount_due']
                            utility_year_revenue = utility_year_revenue + \
                                response['result']['owner_revenue_yearly'][ore]['amount_paid']
                        else:
                            utility_year_expected_revenue = utility_year_expected_revenue + \
                                response['result']['owner_revenue_yearly'][ore]['amount_due']
                            utility_year_revenue = utility_year_revenue + \
                                response['result']['owner_revenue_yearly'][ore]['amount_paid']
            response['result']['rental_year_revenue'] = round(
                rental_year_revenue, 2)
            response['result']['rental_year_expected_revenue'] = round(
                rental_year_expected_revenue, 2)
            response['result']['extra_year_revenue'] = round(
                extra_year_revenue, 2)
            response['result']['extra_year_expected_revenue'] = round(
                extra_year_expected_revenue, 2)
            response['result']['utility_year_revenue'] = round(
                utility_year_revenue, 2)
            response['result']['utility_year_expected_revenue'] = round(
                utility_year_expected_revenue, 2)

            # intialize expense variables
            utility_expense = 0
            maintenance_expense = 0
            management_expense = 0
            repairs_expense = 0
            maintenance_expected_expense = 0
            management_expected_expense = 0
            repairs_expected_expense = 0
            utility_expected_expense = 0

            mortgage_expense = 0
            insurance_expense = 0
            taxes_expense = 0

            maintenance_year_expense = 0
            management_year_expense = 0
            repairs_year_expense = 0
            utility_year_expense = 0
            utility_year_expected_expense = 0
            maintenance_year_expected_expense = 0
            management_year_expected_expense = 0
            repairs_year_expected_expense = 0

            mortgage_year_expense = 0
            insurance_year_expense = 0
            taxes_year_expense = 0

            # owner all expense monthly except mortgage, taxes, insurance
            owner_expense = db.execute("""
            SELECT * FROM purchases pu
            LEFT JOIN payments pa
            ON pa.pay_purchase_id = pu.purchase_uid
            LEFT JOIN properties pr
            ON pu.pur_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN rentals r
            ON r.rental_property_id LIKE CONCAT('%', pr.property_uid, '%')
            WHERE pr.property_uid = \'""" + filterValue + """\' 
            AND ({fn MONTHNAME(pu.next_payment)} = {fn MONTHNAME(now())} AND YEAR(pu.next_payment) = YEAR(now()))
            AND (pu.purchase_type <> "RENT" AND pu.purchase_type <> "EXTRA CHARGES" AND pu.purchase_type <> "UTILITY")
            AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED')""")

            response['result']['owner_expense'] = list(owner_expense['result'])

            owner_utility_expense = db.execute("""
            SELECT * FROM purchases pu
            LEFT JOIN payments pa
            ON pa.pay_purchase_id = pu.purchase_uid
            LEFT JOIN properties pr
            ON pu.pur_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN rentals r
            ON r.rental_property_id LIKE CONCAT('%', pr.property_uid, '%')
            WHERE pr.property_uid = \'""" + filterValue + """\'
            AND ({fn MONTHNAME(pu.next_payment)} = {fn MONTHNAME(now())} AND YEAR(pu.next_payment) = YEAR(now()))
            AND (pu.purchase_type="UTILITY")
            AND pu.payer LIKE '%""" + filterValue + """%'
            AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED') """)

            response['result']['owner_expense'] = response['result']['owner_expense'] + (list(
                owner_utility_expense['result']))

            # monthly expenses for the property
            owner_management_expense = db.execute("""
            SELECT * FROM purchases pu
            LEFT JOIN payments pa
            ON pa.pay_purchase_id = pu.purchase_uid
            LEFT JOIN properties pr
            ON pu.pur_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN rentals r
            ON r.rental_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN pm.contracts c
            ON c.property_uid LIKE CONCAT('%', pr.property_uid, '%')
            WHERE pr.property_uid = \'""" + filterValue + """\'
            AND c.contract_status = 'ACTIVE'
            AND ({fn MONTHNAME(pu.next_payment)} = {fn MONTHNAME(now())} AND YEAR(pu.next_payment) = YEAR(now()))
            AND (pu.purchase_type= "RENT")
            AND r.rental_status = 'ACTIVE'
            AND pu.purchase_status = 'PAID'""")

            response['result']['owner_expense'] = response['result']['owner_expense'] + (list(
                owner_management_expense['result']))
            if len(owner_management_expense['result']) > 0:
                for mex in range(len(owner_management_expense['result'])):
                    # if management
                    # number of months a property has been active
                    delta_active = relativedelta((datetime.strptime(
                        owner_management_expense['result'][mex]['active_date'], '%Y-%m-%d')), datetime.now())
                    months_active = abs(delta_active.months +
                                        (delta_active.years * 12))
                    # number of months a property has been under an active lease
                    delta_leased = relativedelta((datetime.strptime(
                        owner_management_expense['result'][mex]['lease_start'], '%Y-%m-%d')), datetime.now())

                    months_leased = abs(delta_leased.months +
                                        (delta_leased.years * 12))
                    # number of weeks in the current month
                    weeks_current_month = len(
                        calendar.monthcalendar(today.year, int(today.strftime("%m"))))
                    # number of weeks a property has been active
                    weeks_active = round((abs(today - datetime.strptime(
                        owner_management_expense['result'][mex]['active_date'], '%Y-%m-%d').date()).days)/7, 1)
                    # number of weeks a property has been under an active lease
                    weeks_leased = round((abs(today - datetime.strptime(
                        owner_management_expense['result'][mex]['lease_start'], '%Y-%m-%d').date()).days)/7, 1)

                    if owner_management_expense['result'][mex]['purchase_type'] == 'RENT':
                        managementPayments = json.loads(
                            owner_management_expense['result'][mex]['contract_fees'])

                        for payment in managementPayments:
                            # print('amount paid to owner', payment)
                            if payment['fee_type'] == '%':
                                if payment['of'] == 'Gross Rent':
                                    if payment['frequency'] == 'Weekly':
                                        management_expected_expense = management_expected_expense + weeks_current_month*float((
                                            float(owner_management_expense['result'][mex]['amount_due']) * float(payment['charge']))/100)
                                        management_expense = management_expense +  \
                                            weeks_current_month*float((
                                                float(owner_management_expense['result'][mex]['amount_paid']) * float(payment['charge']))/100)
                                    elif payment['frequency'] == 'Biweekly':
                                        management_expected_expense = management_expected_expense + weeks_current_month/2 * \
                                            ((
                                                float(owner_management_expense['result'][mex]['amount_due']) * float(payment['charge']))/100)
                                        management_expense = management_expense +  \
                                            weeks_current_month/2 * \
                                            ((
                                                float(owner_management_expense['result'][mex]['amount_paid']) * float(payment['charge']))/100)
                                    elif payment['frequency'] == 'Monthly':
                                        management_expected_expense = management_expected_expense +  \
                                            ((
                                                float(owner_management_expense['result'][mex]['amount_due']) * float(payment['charge']))/100)
                                        management_expense = management_expense +  \
                                            (
                                                float(owner_management_expense['result'][mex]['amount_paid']) * float(payment['charge']))/100
                                    elif payment['frequency'] == 'Annually':
                                        if date.fromisoformat(owner_management_expense['result'][mex]['start_date']).month == today.month:
                                            management_expected_expense = management_expected_expense +  \
                                                (
                                                    float(owner_management_expense['result'][mex]['amount_due']) * float(payment['charge']))/100
                                            management_expense = management_expense +  \
                                                (
                                                    float(owner_management_expense['result'][mex]['amount_paid']) * float(payment['charge']))/100
                                    elif payment['frequency'] == 'One-time':
                                        if date.fromisoformat(owner_management_expense['result'][mex]['start_date']).month == today.month:
                                            management_expected_expense = management_expected_expense +  \
                                                (
                                                    float(owner_management_expense['result'][mex]['amount_due']) * float(payment['charge']))/100
                                            management_expense = management_expense +  \
                                                (
                                                    float(owner_management_expense['result'][mex]['amount_paid']) * float(payment['charge']))/100
                                    else:
                                        print('do nothing')
                            elif payment['fee_type'] == '$':
                                if payment['frequency'] == 'Weekly':
                                    management_expected_expense = management_expected_expense + weeks_current_month * \
                                        float(payment['charge'])
                                    management_expense = management_expense + weeks_current_month * \
                                        float(payment['charge'])
                                elif payment['frequency'] == 'Biweekly':
                                    management_expected_expense = management_expected_expense + weeks_current_month/2 * \
                                        float(payment['charge'])
                                    management_expense = management_expense + weeks_current_month/2 * \
                                        float(payment['charge'])
                                elif payment['frequency'] == 'Monthly':
                                    management_expected_expense = management_expected_expense +  \
                                        float(payment['charge'])
                                    management_expense = management_expense + \
                                        float(payment['charge'])
                                elif payment['frequency'] == 'Annually':

                                    if date.fromisoformat(owner_management_expense['result'][mex]['start_date']).month == today.month:
                                        management_expected_expense = management_expected_expense + \
                                            float(payment['charge'])
                                        management_expense = management_expense + \
                                            float(
                                                payment['charge'])
                                elif payment['frequency'] == 'One-time':

                                    if date.fromisoformat(owner_management_expense['result'][mex]['start_date']).month == today.month:
                                        management_expected_expense = management_expected_expense +  \
                                            float(payment['charge'])
                                        management_expense = management_expense + \
                                            float(
                                                payment['charge'])

                                else:
                                    print('do nothing')
                            else:
                                print('do nothing')
            if len(response['result']['owner_expense']) > 0:
                for ore in range(len(response['result']['owner_expense'])):
                    # number of months a property has been active
                    delta_active = relativedelta((datetime.strptime(
                        response['result']['owner_expense'][ore]['active_date'], '%Y-%m-%d')), datetime.now())
                    months_active = abs(delta_active.months +
                                        (delta_active.years * 12))
                    # number of months a property has been under an active lease
                    delta_leased = relativedelta((datetime.strptime(
                        response['result']['owner_expense'][ore]['lease_start'], '%Y-%m-%d')), datetime.now())

                    months_leased = abs(delta_leased.months +
                                        (delta_leased.years * 12))
                    # number of weeks in the current month
                    weeks_current_month = len(
                        calendar.monthcalendar(today.year, int(today.strftime("%m"))))

                    # if expenses type is MAINTAINENCE
                    if response['result']['owner_expense'][ore]['purchase_type'] == 'MAINTENANCE':
                        # if maintenance monthly
                        if response['result']['owner_expense'][ore]['purchase_frequency'] == 'Monthly':
                            # if maintenance monthly once a month
                            if response['result']['owner_expense'][ore]['payment_frequency'] == 'Once a month' or response['result']['owner_expense'][ore]['payment_frequency'] is None:

                                maintenance_expected_expense = maintenance_expected_expense + \
                                    response['result']['owner_expense'][ore]['amount_due']
                                maintenance_expense = maintenance_expense + \
                                    response['result']['owner_expense'][ore]['amount_paid']
                                # if maintenance monthly twice a month
                            elif response['result']['owner_expense'][ore]['payment_frequency'] == 'Twice a month':

                                maintenance_expected_expense = maintenance_expected_expense + 2 * \
                                    (response['result']['owner_expense']
                                        [ore]['amount_due'])
                                maintenance_expense = maintenance_expense + \
                                    2 * \
                                    (response['result']['owner_expense']
                                        [ore]['amount_paid'])
                            else:
                                print('do nothing')
                            # if maintenance annually
                        elif response['result']['owner_expense'][ore]['purchase_frequency'] == 'Annually':
                            # if maintenance annually once a year
                            if response['result']['owner_expense'][ore]['payment_frequency'] == 'Once a year':
                                maintenance_expected_expense = maintenance_expected_expense + \
                                    (response['result']['owner_expense']
                                        [ore]['amount_due'])
                                maintenance_expense = maintenance_expense + \
                                    response['result']['owner_expense'][ore]['amount_paid']
                            # if maintenance annually twice a year
                            elif response['result']['owner_expense'][ore]['payment_frequency'] == 'Twice a year':
                                maintenance_expected_expense = maintenance_expected_expense + \
                                    (response['result']['owner_expense']
                                        [ore]['amount_due'])
                                maintenance_expense = maintenance_expense + \
                                    response['result']['owner_expense'][ore]['amount_paid']
                            else:
                                print('do nothing')
                        # if maintenance one-time
                        else:
                            maintenance_expected_expense = maintenance_expected_expense + \
                                response['result']['owner_expense'][ore]['amount_due']
                            maintenance_expense = maintenance_expense + \
                                response['result']['owner_expense'][ore]['amount_paid']
                    # if management
                    if response['result']['owner_expense'][ore]['purchase_type'] == 'MANAGEMENT':
                        # if management monthly
                        if response['result']['owner_expense'][ore]['purchase_frequency'] == 'Monthly':
                            # if management monthly once a month
                            if response['result']['owner_expense'][ore]['payment_frequency'] == 'Once a month' or response['result']['owner_expense'][ore]['payment_frequency'] is None:
                                management_expected_expense = management_expected_expense + response[
                                    'result']['owner_expense'][ore]['amount_due']
                                management_expense = management_expense + \
                                    response['result']['owner_expense'][ore]['amount_paid']
                                # if management monthly twice a month
                            elif response['result']['owner_expense'][ore]['payment_frequency'] == 'Twice a month':
                                management_expected_expense = management_expected_expense + 2 * \
                                    (response['result']['owner_expense']
                                        [ore]['amount_due'])
                                management_expense = management_expense + \
                                    2 * \
                                    (response['result']['owner_expense']
                                        [ore]['amount_paid'])
                            else:
                                print('do nothing')
                            # if management annually
                        elif response['result']['owner_expense'][ore]['purchase_frequency'] == 'Annually':
                            # if management annually once a year
                            if response['result']['owner_expense'][ore]['payment_frequency'] == 'Once a year':
                                management_expected_expense = management_expected_expense +  \
                                    (response['result']['owner_expense']
                                        [ore]['amount_due'])
                                management_expense = management_expense + \
                                    response['result']['owner_expense'][ore]['amount_paid']
                            # if management annually twice a year
                            elif response['result']['owner_expense'][ore]['payment_frequency'] == 'Twice a year':
                                management_expected_expense = management_expected_expense +  \
                                    (response['result']['owner_expense']
                                        [ore]['amount_due'])
                                management_expense = management_expense + \
                                    response['result']['owner_expense'][ore]['amount_paid']
                            else:
                                print('do nothing')
                        # if management one-time
                        else:
                            management_expected_expense = management_expected_expense + \
                                response['result']['owner_expense'][ore]['amount_due']
                            management_expense = management_expense + \
                                response['result']['owner_expense'][ore]['amount_paid']

                    if response['result']['owner_expense'][ore]['purchase_type'] == 'REPAIRS':
                        # if repairs monthly
                        if response['result']['owner_expense'][ore]['purchase_frequency'] == 'Monthly':
                            # if repairs monthly once a month
                            if response['result']['owner_expense'][ore]['payment_frequency'] == 'Once a month' or response['result']['owner_expense'][ore]['payment_frequency'] is None:
                                repairs_expected_expense = repairs_expected_expense +  \
                                    (response['result']['owner_expense']
                                        [ore]['amount_due'])
                                repairs_expense = repairs_expense + \
                                    response['result']['owner_expense'][ore]['amount_paid']
                                # if repairs monthly twice a month
                            elif response['result']['owner_expense'][ore]['payment_frequency'] == 'Twice a month':
                                repairs_expected_expense = repairs_expected_expense + 2 * \
                                    (response['result']['owner_expense']
                                        [ore]['amount_due'])
                                repairs_expense = repairs_expense + \
                                    2 * \
                                    (response['result']['owner_expense']
                                        [ore]['amount_paid'])
                            else:
                                print('do nothing')
                            # if repairs annually
                        elif response['result']['owner_expense'][ore]['purchase_frequency'] == 'Annually':
                            # if repairs annually once a year
                            if response['result']['owner_expense'][ore]['payment_frequency'] == 'Once a year':
                                repairs_expected_expense = repairs_expected_expense +  \
                                    (response['result']['owner_expense']
                                        [ore]['amount_due'])
                                repairs_expense = repairs_expense + \
                                    response['result']['owner_expense'][ore]['amount_paid']
                            # if repairs annually twice a year
                            elif response['result']['owner_expense'][ore]['payment_frequency'] == 'Twice a year':
                                repairs_expected_expense = repairs_expected_expense + \
                                    (response['result']['owner_expense']
                                        [ore]['amount_due'])
                                repairs_expense = repairs_expense + \
                                    response['result']['owner_expense'][ore]['amount_paid']
                            else:
                                print('do nothing')
                        # if repairs one-time
                        else:
                            repairs_expected_expense = repairs_expected_expense + \
                                response['result']['owner_expense'][ore]['amount_due']
                            repairs_expense = repairs_expense + \
                                response['result']['owner_expense'][ore]['amount_paid']
                    if response['result']['owner_expense'][ore]['purchase_type'] == 'UTILITY':
                        if response['result']['owner_expense'][ore]['purchase_frequency'] == 'Weekly':
                            utility_expected_expense = utility_expected_expense + \
                                weeks_current_month*int(response['result']['owner_expense']
                                                        [ore]['amount_due'])
                            utility_expense = utility_expense + \
                                weeks_current_month*int(response['result']['owner_expense']
                                                        [ore]['amount_paid'])
                        elif response['result']['owner_expense'][ore]['purchase_frequency'] == 'Biweekly':
                            utility_expected_expense = utility_expected_expense + \
                                weeks_current_month/2 * \
                                int(response['result']['owner_expense']
                                    [ore]['amount_due'])
                            utility_expense = utility_expense + \
                                weeks_current_month/2 * \
                                int(response['result']['owner_expense']
                                    [ore]['amount_paid'])
                        elif response['result']['owner_expense'][ore]['purchase_frequency'] == 'Monthly':
                            utility_expected_expense = utility_expected_expense + \
                                response['result']['owner_expense'][ore]['amount_due']
                            utility_expense = utility_expense + \
                                response['result']['owner_expense'][ore]['amount_paid']
                        elif response['result']['owner_expense'][ore]['purchase_frequency'] == 'Annually':
                            utility_expected_expense = utility_expected_expense + \
                                response['result']['owner_expense'][ore]['amount_due']
                            utility_expense = utility_expense + \
                                response['result']['owner_expense'][ore]['amount_paid']
                        else:
                            utility_expected_expense = utility_expected_expense + \
                                response['result']['owner_expense'][ore]['amount_due']
                            utility_expense = utility_expense + \
                                response['result']['owner_expense'][ore]['amount_paid']

            response['result']['maintenance_expense'] = round(
                maintenance_expense, 2)
            response['result']['management_expense'] = round(
                management_expense, 2)
            response['result']['repairs_expense'] = round(
                repairs_expense, 2)
            response['result']['utility_expense'] = round(
                utility_expense, 2)
            response['result']['maintenance_expected_expense'] = round(
                maintenance_expected_expense, 2)
            response['result']['management_expected_expense'] = round(
                management_expected_expense, 2)
            response['result']['repairs_expected_expense'] = round(
                repairs_expected_expense, 2)
            response['result']['utility_expected_expense'] = round(
                utility_expense, 2)

            # owner all expenses monthly except mortgage, taxes, insurance
            owner_expense_yearly = db.execute("""
            SELECT * FROM purchases pu
            LEFT JOIN payments pa
            ON pa.pay_purchase_id = pu.purchase_uid
            LEFT JOIN properties pr
            ON pu.pur_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN rentals r
            ON r.rental_property_id LIKE CONCAT('%', pr.property_uid, '%')
            WHERE pr.property_uid = \'""" + filterValue + """\' 
            AND YEAR(pu.next_payment) = YEAR(now())
            AND (pu.purchase_type <> "RENT" AND pu.purchase_type <> "EXTRA CHARGES" AND pu.purchase_type <> "UTILITY")
            AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED')""")

            response['result']['owner_expense_yearly'] = list(
                owner_expense_yearly['result'])

            owner_utility_year_expense = db.execute("""
            SELECT * FROM purchases pu
            LEFT JOIN payments pa
            ON pa.pay_purchase_id = pu.purchase_uid
            LEFT JOIN properties pr
            ON pu.pur_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN rentals r
            ON r.rental_property_id LIKE CONCAT('%', pr.property_uid, '%')
            WHERE pr.property_uid = \'""" + filterValue + """\'
            AND YEAR(pu.next_payment) = YEAR(now())
            AND (pu.purchase_type="UTILITY")
            AND pu.payer LIKE '%""" + filterValue + """%'
            AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED') """)

            response['result']['owner_expense_yearly'] = response['result']['owner_expense_yearly'] + (list(
                owner_utility_year_expense['result']))

            # monthly expenses for the property
            owner_management_year_expense = db.execute("""
            SELECT * FROM purchases pu
            LEFT JOIN payments pa
            ON pa.pay_purchase_id = pu.purchase_uid
            LEFT JOIN properties pr
            ON pu.pur_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN rentals r
            ON r.rental_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN pm.contracts c
            ON c.property_uid LIKE CONCAT('%', pr.property_uid, '%')
            WHERE pr.property_uid = \'""" + filterValue + """\'
            AND c.contract_status = 'ACTIVE'
            AND YEAR(pu.next_payment) = YEAR(now())
            AND (pu.purchase_type= "RENT")
            AND r.rental_status = 'ACTIVE'
            AND pu.purchase_status = 'PAID'""")

            response['result']['owner_expense_yearly'] = response['result']['owner_expense_yearly'] + (list(
                owner_management_year_expense['result']))
            if len(owner_management_year_expense['result']) > 0:
                for mex in range(len(owner_management_year_expense['result'])):
                    # if management
                    # number of months a property has been active
                    delta_active = relativedelta((datetime.strptime(
                        owner_management_year_expense['result'][mex]['active_date'], '%Y-%m-%d')), datetime.now())
                    months_active = abs(delta_active.months +
                                        (delta_active.years * 12))
                    # number of months a property has been under an active lease
                    delta_leased = relativedelta((datetime.strptime(
                        owner_management_year_expense['result'][mex]['lease_start'], '%Y-%m-%d')), datetime.now())

                    months_leased = abs(delta_leased.months +
                                        (delta_leased.years * 12))
                    # number of weeks in the current month
                    weeks_current_month = len(
                        calendar.monthcalendar(today.year, int(today.strftime("%m"))))
                    # number of weeks a property has been active
                    weeks_active = round((abs(today - datetime.strptime(
                        owner_management_year_expense['result'][mex]['active_date'], '%Y-%m-%d').date()).days)/7, 1)
                    # number of weeks a property has been under an active lease
                    weeks_leased = round((abs(today - datetime.strptime(
                        owner_management_year_expense['result'][mex]['lease_start'], '%Y-%m-%d').date()).days)/7, 1)

                    if owner_management_year_expense['result'][mex]['purchase_type'] == 'RENT':
                        managementPayments = json.loads(
                            owner_management_year_expense['result'][mex]['contract_fees'])

                        for payment in managementPayments:
                            # print('amount paid to owner', payment)
                            if payment['fee_type'] == '%':
                                if payment['of'] == 'Gross Rent':
                                    if payment['frequency'] == 'Weekly':
                                        management_year_expected_expense = management_year_expected_expense + weeks_leased*float((
                                            float(owner_management_year_expense['result'][mex]['amount_due']) * float(payment['charge']))/100)
                                        management_year_expense = management_year_expense +  \
                                            weeks_leased*float((
                                                float(owner_management_year_expense['result'][mex]['amount_paid']) * float(payment['charge']))/100)
                                    elif payment['frequency'] == 'Biweekly':
                                        management_year_expected_expense = management_year_expected_expense + weeks_leased/2 * \
                                            ((
                                                float(owner_management_year_expense['result'][mex]['amount_due']) * float(payment['charge']))/100)
                                        management_year_expense = management_year_expense +  \
                                            weeks_leased/2 * \
                                            ((
                                                float(owner_management_year_expense['result'][mex]['amount_paid']) * float(payment['charge']))/100)
                                    elif payment['frequency'] == 'Monthly':
                                        management_year_expected_expense = management_year_expected_expense + months_leased * \
                                            ((
                                                float(owner_management_year_expense['result'][mex]['amount_due']) * float(payment['charge']))/100)
                                        management_year_expense = management_year_expense + months_leased *  \
                                            (
                                                float(owner_management_year_expense['result'][mex]['amount_paid']) * float(payment['charge']))/100
                                    elif payment['frequency'] == 'Annually':

                                        management_year_expected_expense = management_year_expected_expense +  \
                                            (
                                                float(owner_management_year_expense['result'][mex]['amount_due']) * float(payment['charge']))/100
                                        management_year_expense = management_year_expense +  \
                                            (
                                                float(owner_management_year_expense['result'][mex]['amount_paid']) * float(payment['charge']))/100
                                    elif payment['frequency'] == 'One-time':

                                        management_year_expected_expense = management_year_expected_expense +  \
                                            (
                                                float(owner_management_year_expense['result'][mex]['amount_due']) * float(payment['charge']))/100
                                        management_year_expense = management_year_expense +  \
                                            (
                                                float(owner_management_year_expense['result'][mex]['amount_paid']) * float(payment['charge']))/100
                                    else:
                                        print('do nothing')
                            elif payment['fee_type'] == '$':
                                if payment['frequency'] == 'Weekly':
                                    management_year_expected_expense = management_year_expected_expense + weeks_leased * \
                                        float(payment['charge'])
                                    management_year_expense = management_year_expense + weeks_leased * \
                                        float(payment['charge'])
                                elif payment['frequency'] == 'Biweekly':
                                    management_year_expected_expense = management_year_expected_expense + weeks_leased/2 * \
                                        float(payment['charge'])
                                    management_year_expense = management_year_expense + weeks_leased/2 * \
                                        float(payment['charge'])
                                elif payment['frequency'] == 'Monthly':
                                    management_year_expected_expense = management_year_expected_expense + months_leased *  \
                                        float(payment['charge'])
                                    management_year_expense = management_year_expense + \
                                        float(payment['charge'])
                                elif payment['frequency'] == 'Annually':
                                    management_year_expected_expense = management_year_expected_expense + \
                                        float(payment['charge'])
                                    management_year_expense = management_year_expense + \
                                        float(
                                            payment['charge'])
                                elif payment['frequency'] == 'One-time':
                                    management_year_expected_expense = management_year_expected_expense +  \
                                        float(payment['charge'])
                                    management_year_expense = management_year_expense + \
                                        float(
                                            payment['charge'])

                                else:
                                    print('do nothing')
                            else:
                                print('do nothing')
            if len(response['result']['owner_expense_yearly']) > 0:
                for ore in range(len(response['result']['owner_expense_yearly'])):
                    # number of months a property has been active
                    delta_active = relativedelta((datetime.strptime(
                        response['result']['owner_revenue_yearly'][ore]['active_date'], '%Y-%m-%d')), datetime.now())
                    months_active = abs(delta_active.months +
                                        (delta_active.years * 12))
                    # number of months a property has been under an active lease
                    delta_leased = relativedelta((datetime.strptime(
                        response['result']['owner_revenue_yearly'][ore]['lease_start'], '%Y-%m-%d')), datetime.now())

                    months_leased = abs(delta_leased.months +
                                        (delta_leased.years * 12))
                    # number of weeks in the current month
                    weeks_current_month = len(
                        calendar.monthcalendar(today.year, int(today.strftime("%m"))))
                    # number of weeks a property has been active
                    weeks_active = round((abs(today - datetime.strptime(
                        response['result']['owner_revenue_yearly'][ore]['active_date'], '%Y-%m-%d').date()).days)/7, 1)
                    # number of weeks a property has been under an active lease
                    weeks_leased = round((abs(today - datetime.strptime(
                        response['result']['owner_revenue_yearly'][ore]['lease_start'], '%Y-%m-%d').date()).days)/7, 1)

                    # if expenses type is MAINTAINENCE
                    if response['result']['owner_expense_yearly'][ore]['purchase_type'] == 'MAINTENANCE':
                        # if maintenance monthly
                        if response['result']['owner_expense_yearly'][ore]['purchase_frequency'] == 'Monthly':
                            # if maintenance monthly once a month
                            if response['result']['owner_expense_yearly'][ore]['payment_frequency'] == 'Once a month' or response['result']['owner_expense_yearly'][ore]['payment_frequency'] is None:

                                maintenance_year_expense = maintenance_year_expense + months_active * \
                                    (response['result']['owner_expense_yearly']
                                        [ore]['amount_paid'])
                                maintenance_year_expected_expense = maintenance_year_expected_expense + months_active * \
                                    (response['result']['owner_expense_yearly']
                                        [ore]['amount_due'])
                                # if maintenance monthly twice a month
                            elif response['result']['owner_expense_yearly'][ore]['payment_frequency'] == 'Twice a month':

                                maintenance_year_expense = maintenance_year_expense + 2*months_active * \
                                    (response['result']['owner_expense_yearly']
                                        [ore]['amount_paid'])
                                maintenance_year_expected_expense = maintenance_year_expected_expense + \
                                    2*months_active * \
                                    (response['result']['owner_expense_yearly']
                                        [ore]['amount_due'])
                            else:
                                print('do nothing')
                            # if maintenance annually
                        elif response['result']['owner_expense_yearly'][ore]['purchase_frequency'] == 'Annually':
                            print('in maintenance annually')
                            # if maintenance annually once a year
                            if response['result']['owner_expense_yearly'][ore]['payment_frequency'] == 'Once a year':
                                maintenance_year_expense = maintenance_year_expense + \
                                    (response['result']['owner_expense_yearly']
                                        [ore]['amount_paid'])
                                maintenance_year_expected_expense = maintenance_year_expected_expense + \
                                    response['result']['owner_expense_yearly'][ore]['amount_due']
                            # if maintenance annually twice a year
                            elif response['result']['owner_expense_yearly'][ore]['payment_frequency'] == 'Twice a year':
                                maintenance_year_expense = maintenance_year_expense + 2 * \
                                    (response['result']['owner_expense_yearly']
                                        [ore]['amount_paid'])
                                maintenance_year_expected_expense = maintenance_year_expected_expense + \
                                    2*response['result']['owner_expense_yearly'][ore]['amount_due']
                            else:
                                print('do nothing')
                        # if maintenance one-time
                        else:
                            maintenance_year_expense = maintenance_expense + \
                                response['result']['owner_expense_yearly'][ore]['amount_paid']
                            maintenance_year_expected_expense = maintenance_year_expected_expense + \
                                response['result']['owner_expense_yearly'][ore]['amount_due']
                    # if management
                    if response['result']['owner_expense_yearly'][ore]['purchase_type'] == 'MANAGEMENT':
                        print("MANAGEMENT")
                        # if management monthly
                        if response['result']['owner_expense_yearly'][ore]['purchase_frequency'] == 'Monthly':
                            # if management monthly once a month
                            if response['result']['owner_expense_yearly'][ore]['payment_frequency'] == 'Once a month' or response['result']['owner_expense_yearly'][ore]['payment_frequency'] is None:
                                print('here')
                                management_year_expense = management_year_expense + months_active * \
                                    (response['result']['owner_expense_yearly']
                                        [ore]['amount_paid'])
                                management_year_expected_expense = management_year_expected_expense + \
                                    months_active * \
                                    response['result']['owner_expense_yearly'][ore]['amount_due']
                                # if management monthly twice a month
                            elif response['result']['owner_expense_yearly'][ore]['payment_frequency'] == 'Twice a month':
                                management_year_expense = management_year_expense + 2*months_active * \
                                    (response['result']['owner_expense_yearly']
                                        [ore]['amount_paid'])
                                management_year_expected_expense = management_year_expected_expense + \
                                    2*months_active * \
                                    (response['result']['owner_expense_yearly']
                                        [ore]['amount_due'])
                            else:
                                print('do nothing')
                            # if management annually
                        elif response['result']['owner_expense_yearly'][ore]['purchase_frequency'] == 'Annually':
                            # if management annually once a year
                            if response['result']['owner_expense_yearly'][ore]['payment_frequency'] == 'Once a year':
                                management_year_expense = management_year_expense +  \
                                    (response['result']['owner_expense_yearly']
                                        [ore]['amount_paid'])
                                management_year_expected_expense = management_year_expected_expense + \
                                    response['result']['owner_expense_yearly'][ore]['amount_due']
                            # if management annually twice a year
                            elif response['result']['owner_expense_yearly'][ore]['payment_frequency'] == 'Twice a year':
                                management_year_expense = management_year_expense + 2 * \
                                    (response['result']['owner_expense_yearly']
                                        [ore]['amount_paid'])
                                management_year_expected_expense = management_year_expected_expense + \
                                    2*response['result']['owner_expense_yearly'][ore]['amount_due']
                            else:
                                print('do nothing')
                        # if management one-time
                        else:
                            management_year_expense = management_year_expense + \
                                response['result']['owner_expense_yearly'][ore]['amount_paid']
                            management_year_expected_expense = management_year_expected_expense + \
                                response['result']['owner_expense_yearly'][ore]['amount_due']

                    if response['result']['owner_expense_yearly'][ore]['purchase_type'] == 'REPAIRS':
                        # if repairs monthly
                        if response['result']['owner_expense_yearly'][ore]['purchase_frequency'] == 'Monthly':
                            # if repairs monthly once a month
                            if response['result']['owner_expense_yearly'][ore]['payment_frequency'] == 'Once a month' or response['result']['owner_expense_yearly'][ore]['payment_frequency'] is None:
                                repairs_year_expense = repairs_year_expense + months_active * \
                                    (response['result']['owner_expense_yearly']
                                        [ore]['amount_paid'])
                                repairs_year_expected_expense = repairs_year_expected_expense + months_active * \
                                    response['result']['owner_expense_yearly'][ore]['amount_due']
                                # if repairs monthly twice a month
                            elif response['result']['owner_expense_yearly'][ore]['payment_frequency'] == 'Twice a month':
                                repairs_year_expense = repairs_year_expense + 2*months_active * \
                                    (response['result']['owner_expense_yearly']
                                        [ore]['amount_paid'])
                                repairs_year_expected_expense = repairs_year_expected_expense + \
                                    2*months_active * \
                                    (response['result']['owner_expense_yearly']
                                        [ore]['amount_due'])
                            else:
                                print('do nothing')
                            # if repairs annually
                        elif response['result']['owner_expense_yearly'][ore]['purchase_frequency'] == 'Annually':
                            # if repairs annually once a year
                            if response['result']['owner_expense_yearly'][ore]['payment_frequency'] == 'Once a year':
                                repairs_year_expense = repairs_year_expense + (response['result']['owner_expense_yearly']
                                                                               [ore]['amount_paid'])
                                repairs_year_expected_expense = repairs_year_expected_expense + \
                                    response['result']['owner_expense_yearly'][ore]['amount_due']
                            # if repairs annually twice a year
                            elif response['result']['owner_expense_yearly'][ore]['payment_frequency'] == 'Twice a year':
                                repairs_year_expense = repairs_year_expense + 2 * \
                                    (response['result']['owner_expense_yearly']
                                        [ore]['amount_paid'])
                                repairs_year_expected_expense = repairs_year_expected_expense + 2 * \
                                    response['result']['owner_expense_yearly'][ore]['amount_due']
                            else:
                                print('do nothing')
                        # if repairs one-time
                        else:
                            repairs_year_expense = repairs_year_expense + \
                                response['result']['owner_expense_yearly'][ore]['amount_paid']
                            repairs_year_expected_expense = repairs_year_expected_expense + \
                                response['result']['owner_expense_yearly'][ore]['amount_due']
                    if response['result']['owner_expense_yearly'][ore]['purchase_type'] == 'UTILITY':
                        if response['result']['owner_expense_yearly'][ore]['purchase_frequency'] == 'Weekly':
                            utility_year_expected_expense = utility_year_expected_expense + \
                                weeks_leased*int(response['result']['owner_expense_yearly']
                                                 [ore]['amount_due'])
                            utility_year_expense = utility_year_expense + \
                                weeks_leased*int(response['result']['owner_expense_yearly']
                                                 [ore]['amount_paid'])
                        elif response['result']['owner_expense_yearly'][ore]['purchase_frequency'] == 'Biweekly':
                            utility_year_expected_expense = utility_year_expected_expense + \
                                weeks_leased/2 * \
                                int(response['result']['owner_expense_yearly']
                                    [ore]['amount_due'])
                            utility_year_expense = utility_year_expense + \
                                weeks_leased/2 * \
                                int(response['result']['owner_expense_yearly']
                                    [ore]['amount_paid'])
                        elif response['result']['owner_expense_yearly'][ore]['purchase_frequency'] == 'Monthly':
                            utility_year_expected_expense = utility_year_expected_expense + months_leased * \
                                response['result']['owner_expense_yearly'][ore]['amount_due']
                            utility_year_expense = utility_year_expense + months_leased * \
                                response['result']['owner_expense_yearly'][ore]['amount_paid']
                        elif response['result']['owner_expense_yearly'][ore]['purchase_frequency'] == 'Annually':
                            utility_year_expected_expense = utility_year_expected_expense + \
                                response['result']['owner_expense_yearly'][ore]['amount_due']
                            utility_year_expense = utility_year_expense + \
                                response['result']['owner_expense_yearly'][ore]['amount_paid']
                        else:
                            utility_year_expected_expense = utility_year_expected_expense + \
                                response['result']['owner_expense_yearly'][ore]['amount_due']
                            utility_year_expense = utility_year_expense + \
                                response['result']['owner_expense_yearly'][ore]['amount_paid']
            response['result']['maintenance_year_expense'] = round(
                maintenance_year_expense, 2)
            response['result']['management_year_expense'] = round(
                management_year_expense, 2)
            response['result']['repairs_year_expense'] = round(
                repairs_year_expense, 2)
            response['result']['utility_year_expense'] = round(
                utility_year_expense, 2)
            response['result']['maintenance_year_expected_expense'] = round(
                maintenance_year_expected_expense, 2)
            response['result']['management_year_expected_expense'] = round(
                management_year_expected_expense, 2)
            response['result']['repairs_year_expected_expense'] = round(
                repairs_year_expected_expense, 2)
            response['result']['utility_year_expected_expense'] = round(
                utility_year_expected_expense, 2)
            owner_property_expenses = db.execute("""
                        SELECT pr.address,pr.unit, pr.mortgages, pr.taxes, pr.insurance, pr.active_date FROM properties pr
                        WHERE pr.property_uid = \'""" + filterValue + """\'
                        AND pr.mortgages is not null OR  pr.taxes is not null OR  pr.insurance is not null
                        """)
            # monthly expense for the property to include mortgage
            if len(owner_property_expenses['result']) > 0:
                for ope in range(len(owner_property_expenses['result'])):
                    owner_property_expenses['result'][ope]['mortgage_year_expense'] = 0
                    owner_property_expenses['result'][ope]['mortgage_expense'] = 0
                    owner_property_expenses['result'][ope]['taxes_year_expense'] = 0
                    owner_property_expenses['result'][ope]['taxes_expense'] = 0
                    owner_property_expenses['result'][ope]['insurance_year_expense'] = 0
                    owner_property_expenses['result'][ope]['insurance_expense'] = 0
                    # number of months a property has been active
                    delta_active = relativedelta((datetime.strptime(
                        owner_property_expenses['result'][ope]['active_date'], '%Y-%m-%d')), datetime.now())
                    months_active = abs(delta_active.months +
                                        (delta_active.years * 12))
                    # number of weeks in the current month
                    weeks_current_month = len(
                        calendar.monthcalendar(today.year, int(today.strftime("%m"))))
                    # number of weeks a property has been active
                    weeks_active = round((abs(today - datetime.strptime(
                        owner_property_expenses['result'][ope]['active_date'], '%Y-%m-%d').date()).days)/7, 1)

                    if owner_property_expenses['result'][ope]['mortgages'] is not None:
                        # if mortgage monthly
                        if json.loads(owner_property_expenses['result'][ope]['mortgages'])['frequency'] == 'Monthly':
                            # if mortgage monthly and once a month
                            if json.loads(owner_property_expenses['result'][ope]['mortgages'])['frequency_of_payment'] == 'Once a month':
                                mortgage_year_expense = mortgage_year_expense + (months_active*(int(json.loads(owner_property_expenses['result'][ope]['mortgages'])[
                                    'amount'])))
                                mortgage_expense = mortgage_expense + \
                                    int(json.loads(
                                        owner_property_expenses['result'][ope]['mortgages'])['amount'])
                                owner_property_expenses['result'][ope]['mortgage_year_expense'] = (months_active*(int(json.loads(owner_property_expenses['result'][ope]['mortgages'])[
                                    'amount'])))
                                owner_property_expenses['result'][ope]['mortgage_expense'] = int(json.loads(
                                    owner_property_expenses['result'][ope]['mortgages'])['amount'])
                        # if mortgage monthly and twice a month
                            elif json.loads(owner_property_expenses['result'][ope]['mortgages'])['frequency_of_payment'] == 'Twice a month':
                                mortgage_year_expense = mortgage_year_expense + (2*months_active*(int(json.loads(owner_property_expenses['result'][ope]['mortgages'])[
                                    'amount'])))
                                mortgage_expense = mortgage_expense + 2 * \
                                    (int(json.loads(
                                        owner_property_expenses['result'][ope]['mortgages'])['amount']))
                                owner_property_expenses['result'][ope]['mortgage_year_expense'] = (2 * months_active*(int(json.loads(owner_property_expenses['result'][ope]['mortgages'])[
                                    'amount'])))
                                owner_property_expenses['result'][ope]['mortgage_expense'] = 2 * int(json.loads(
                                    owner_property_expenses['result'][ope]['mortgages'])['amount'])
                        # if mortgage weekly
                        elif json.loads(owner_property_expenses['result'][ope]['mortgages'])['frequency'] == 'Weekly':
                            # if mortgage weekly and once a week
                            if json.loads(owner_property_expenses['result'][ope]['mortgages'])['frequency_of_payment'] == 'Once a week':
                                mortgage_year_expense = mortgage_year_expense + (weeks_active*(int(json.loads(owner_property_expenses['result'][ope]['mortgages'])[
                                    'amount'])))
                                mortgage_expense = mortgage_expense + \
                                    weeks_current_month*(int(json.loads(
                                        owner_property_expenses['result'][ope]['mortgages'])['amount']))
                                owner_property_expenses['result'][ope]['mortgage_year_expense'] = (weeks_active*(int(json.loads(owner_property_expenses['result'][ope]['mortgages'])[
                                    'amount'])))
                                owner_property_expenses['result'][ope]['mortgage_expense'] = weeks_current_month * int(json.loads(
                                    owner_property_expenses['result'][ope]['mortgages'])['amount'])
                            # if mortgage weekly and every other week
                            elif json.loads(owner_property_expenses['result'][ope]['mortgages'])['frequency_of_payment'] == 'Every other week':
                                mortgage_year_expense = mortgage_year_expense + ((weeks_active/2)*(int(json.loads(owner_property_expenses['result'][ope]['mortgages'])[
                                    'amount'])))
                                mortgage_expense = mortgage_expense + (weeks_current_month/2) * \
                                    (int(json.loads(
                                        owner_property_expenses['result'][ope]['mortgages'])['amount']))
                                owner_property_expenses['result'][ope]['mortgage_year_expense'] = (weeks_active/2*(int(json.loads(owner_property_expenses['result'][ope]['mortgages'])[
                                    'amount'])))
                                owner_property_expenses['result'][ope]['mortgage_expense'] = weeks_current_month/2 * int(json.loads(
                                    owner_property_expenses['result'][ope]['mortgages'])['amount'])

                    # monthly expense for the property to include taxes
                    if owner_property_expenses['result'][ope]['taxes'] is not None:
                        if len(eval(owner_property_expenses['result'][ope]['taxes'])) > 0:
                            for te in range(len(eval(owner_property_expenses['result'][ope]['taxes']))):

                                # if tax monthly
                                if eval(owner_property_expenses['result'][ope]['taxes'])[te]['frequency'] == 'Monthly':
                                    # if taxes monthly and once a month
                                    if eval(owner_property_expenses['result'][ope]['taxes'])[te]['frequency_of_payment'] == 'Once a month':
                                        print('in once a month')
                                        taxes_year_expense = taxes_year_expense + (months_active * int(eval(owner_property_expenses['result'][ope]
                                                                                                            ['taxes'])[te]['amount']))
                                        taxes_expense = taxes_expense + \
                                            int(eval(owner_property_expenses['result'][ope]['taxes'])[
                                                te]['amount'])
                                        owner_property_expenses['result'][ope]['taxes_year_expense'] = owner_property_expenses['result'][ope]['taxes_year_expense'] + (
                                            months_active * int(eval(owner_property_expenses['result'][ope]['taxes'])[te]['amount']))
                                        owner_property_expenses['result'][ope]['taxes_expense'] = owner_property_expenses['result'][ope]['taxes_expense'] + int(
                                            eval(owner_property_expenses['result'][ope]['taxes'])[te]['amount'])
                                # if taxes monthly and once a month
                                    elif eval(owner_property_expenses['result'][ope]['taxes'])[te]['frequency_of_payment'] == 'Twice a month':
                                        taxes_year_expense = taxes_year_expense + (2*months_active * int(eval(owner_property_expenses['result'][ope]
                                                                                                              ['taxes'])[te]['amount']))
                                        taxes_expense = taxes_expense + \
                                            2*(int(eval(owner_property_expenses['result'][ope]['taxes'])[
                                                te]['amount']))
                                        owner_property_expenses['result'][ope]['taxes_year_expense'] = owner_property_expenses['result'][ope]['taxes_year_expense'] + (
                                            2*months_active * int(eval(owner_property_expenses['result'][ope]['taxes'])[te]['amount']))
                                        owner_property_expenses['result'][ope]['taxes_expense'] = owner_property_expenses['result'][ope]['taxes_expense'] + 2*int(
                                            eval(owner_property_expenses['result'][ope]['taxes'])[te]['amount'])
                                    # if tax Annually
                                elif eval(owner_property_expenses['result'][ope]['taxes'])[te]['frequency'] == 'Annually':

                                    # if taxes annually and once a year
                                    if eval(owner_property_expenses['result'][ope]['taxes'])[te]['frequency_of_payment'] == 'Once a year':

                                        if date.fromisoformat(eval(owner_property_expenses['result'][ope]['taxes'])[te]['next_date']).year == today.year:
                                            taxes_year_expense = taxes_year_expense + (int(eval(owner_property_expenses['result'][ope]
                                                                                                ['taxes'])[te]['amount']))
                                            owner_property_expenses['result'][ope]['taxes_year_expense'] = owner_property_expenses['result'][ope]['taxes_year_expense'] + (int(eval(owner_property_expenses['result'][ope]
                                                                                                                                                                                    ['taxes'])[te]['amount']))

                                        if date.fromisoformat(eval(owner_property_expenses['result'][ope]['taxes'])[te]['next_date']).month == today.month:
                                            taxes_expense = taxes_expense + \
                                                int(eval(owner_property_expenses['result'][ope]['taxes'])[
                                                    te]['amount'])
                                            owner_property_expenses['result'][ope]['taxes_expense'] = owner_property_expenses['result'][ope]['taxes_expense'] + int(eval(owner_property_expenses['result'][ope]['taxes'])[
                                                te]['amount'])
                                    # if taxes annually and twice a year
                                    elif eval(owner_property_expenses['result'][ope]['taxes'])[te]['frequency_of_payment'] == 'Twice a year':
                                        print('in twice a year')
                                        if date.fromisoformat(eval(owner_property_expenses['result'][ope]['taxes'])[te]['next_date']).year == today.year:
                                            taxes_year_expense = taxes_year_expense + (2*(int(eval(owner_property_expenses['result'][ope]
                                                                                                   ['taxes'])[te]['amount'])))
                                            owner_property_expenses['result'][ope]['taxes_year_expense'] = owner_property_expenses['result'][ope]['taxes_year_expense'] + 2*(int(eval(owner_property_expenses['result'][ope]
                                                                                                                                                                                      ['taxes'])[te]['amount']))
                                        if date.fromisoformat(eval(owner_property_expenses['result'][ope]['taxes'])[te]['next_date']).month == today.month or (date.fromisoformat(eval(owner_property_expenses['result'][ope]['taxes'])[te]['next_date']) + relativedelta(months=6)).month == today.month:
                                            taxes_expense = taxes_expense + (int(eval(owner_property_expenses['result'][ope]['taxes'])[
                                                te]['amount']))
                                            owner_property_expenses['result'][ope]['taxes_expense'] = owner_property_expenses['result'][ope]['taxes_expense'] + (int(eval(owner_property_expenses['result'][ope]['taxes'])[
                                                te]['amount']))
                        # monthly expense for the property to include insurance
                    if owner_property_expenses['result'][ope]['insurance'] is not None:
                        if len(eval(owner_property_expenses['result'][ope]['insurance'])) > 0:
                            for te in range(len(eval(owner_property_expenses['result'][ope]['insurance']))):

                                # if insurance monthly
                                if eval(owner_property_expenses['result'][ope]['insurance'])[te]['frequency'] == 'Monthly':

                                    # if insurance monthly and once a month
                                    if eval(owner_property_expenses['result'][ope]['insurance'])[te]['frequency_of_payment'] == 'Once a month':
                                        insurance_year_expense = insurance_year_expense + (months_active * int(eval(owner_property_expenses['result'][ope]
                                                                                                                    ['insurance'])[te]['amount']))
                                        insurance_expense = insurance_expense + \
                                            int(eval(owner_property_expenses['result'][ope]['insurance'])[
                                                te]['amount'])
                                        owner_property_expenses['result'][ope]['insurance_year_expense'] = owner_property_expenses['result'][ope]['insurance_year_expense'] + (
                                            months_active * int(eval(owner_property_expenses['result'][ope]['insurance'])[te]['amount']))
                                        owner_property_expenses['result'][ope]['insurance_expense'] = owner_property_expenses['result'][ope]['insurance_expense'] + int(
                                            eval(owner_property_expenses['result'][ope]['insurance'])[te]['amount'])
                                # if insurance monthly and once a month
                                    elif eval(owner_property_expenses['result'][ope]['insurance'])[te]['frequency_of_payment'] == 'Twice a month':
                                        insurance_year_expense = insurance_year_expense + (2*months_active * int(eval(owner_property_expenses['result'][ope]
                                                                                                                      ['insurance'])[te]['amount']))
                                        insurance_expense = insurance_expense + \
                                            2*(int(eval(owner_property_expenses['result'][ope]['insurance'])[
                                                te]['amount']))
                                        owner_property_expenses['result'][ope]['insurance_year_expense'] = owner_property_expenses['result'][ope]['insurance_year_expense'] + (
                                            2*months_active * int(eval(owner_property_expenses['result'][ope]['insurance'])[te]['amount']))
                                        owner_property_expenses['result'][ope]['insurance_expense'] = owner_property_expenses['result'][ope]['insurance_expense'] + 2*int(
                                            eval(owner_property_expenses['result'][ope]['insurance'])[te]['amount'])
                                    # if insurance Annually
                                elif eval(owner_property_expenses['result'][ope]['insurance'])[te]['frequency'] == 'Annually':

                                    # if insurance annually and once a year
                                    if eval(owner_property_expenses['result'][ope]['insurance'])[te]['frequency_of_payment'] == 'Once a year':
                                        if date.fromisoformat(eval(owner_management_expense['result'][ope]['insurance'])[te]['next_date']).year == today.year:
                                            insurance_year_expense = insurance_year_expense + (int(eval(owner_property_expenses['result'][ope]
                                                                                                        ['insurance'])[te]['amount']))
                                            owner_property_expenses['result'][ope]['insurance_year_expense'] = owner_property_expenses['result'][ope]['insurance_year_expense'] + (int(eval(owner_property_expenses['result'][ope]
                                                                                                                                                                                            ['insurance'])[te]['amount']))
                                        if date.fromisoformat(eval(owner_management_expense['result'][ope]['insurance'])[te]['next_date']).month == today.month:
                                            insurance_expense = insurance_expense + \
                                                int(eval(owner_property_expenses['result'][ope]['insurance'])[
                                                    te]['amount'])
                                            owner_property_expenses['result'][ope]['insurance_expense'] = owner_property_expenses['result'][ope]['insurance_expense'] + (int(eval(owner_property_expenses['result'][ope]
                                                                                                                                                                                  ['insurance'])[te]['amount']))
                                    # if insurance annually and twice a year
                                    elif eval(owner_property_expenses['result'][ope]['insurance'])[te]['frequency_of_payment'] == 'Twice a year':
                                        if date.fromisoformat(eval(owner_management_expense['result'][ope]['insurance'])[te]['next_date']).year == today.year:
                                            insurance_year_expense = insurance_year_expense + (2*(int(eval(owner_property_expenses['result'][ope]
                                                                                                           ['insurance'])[te]['amount'])))
                                            owner_property_expenses['result'][ope]['insurance_year_expense'] = owner_property_expenses['result'][ope]['insurance_year_expense'] + 2*(int(eval(owner_property_expenses['result'][ope]
                                                                                                                                                                                              ['insurance'])[te]['amount']))
                                        if date.fromisoformat(eval(owner_management_expense['result'][ope]['insurance'])[te]['next_date']).month == today.month or (date.fromisoformat(eval(owner_management_expense['result'][ope]['insurance'])[te]['next_date']) + relativedelta(months=6)).month == today.month:
                                            insurance_expense = insurance_expense + \
                                                (int(eval(owner_property_expenses['result'][ope]['insurance'])[
                                                    te]['amount']))
                                            owner_property_expenses['result'][ope]['insurance_expense'] = owner_property_expenses['result'][ope]['insurance_expense'] + (int(eval(owner_property_expenses['result'][ope]
                                                                                                                                                                                  ['insurance'])[te]['amount']))
            response['result']['mortgage_expense'] = mortgage_expense
            response['result']['mortgage_year_expense'] = mortgage_year_expense
            response['result']['taxes_expense'] = taxes_expense
            response['result']['taxes_year_expense'] = taxes_year_expense
            response['result']['insurance_expense'] = insurance_expense
            response['result']['insurance_year_expense'] = insurance_year_expense
            response['result']['owner_property_expense'] = list(
                owner_property_expenses['result'])
        return response
