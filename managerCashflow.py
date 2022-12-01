from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from data import connect, uploadImage
import boto3
import json
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import calendar


class ManagerCashflow(Resource):
    def get(self):
        response = {}
        response['message'] = 'Successfully executed SQL query'
        response['code'] = 200
        response['result'] = {}
        filters = ['manager_id']
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

            amortized_rental_revenue = 0
            amortized_extra_revenue = 0
            amortized_utility_revenue = 0
            amortized_rental_expected_revenue = 0
            amortized_extra_expected_revenue = 0
            amortized_utility_expected_revenue = 0

            amortized_rental_year_revenue = 0
            amortized_extra_year_revenue = 0
            amortized_utility_year_revenue = 0
            amortized_rental_year_expected_revenue = 0
            amortized_extra_year_expected_revenue = 0
            amortized_utility_year_expected_revenue = 0

            # intialize expense variables
            utility_expense = 0
            maintenance_expense = 0
            management_expense = 0
            repairs_expense = 0
            maintenance_expected_expense = 0
            management_expected_expense = 0
            repairs_expected_expense = 0
            utility_expected_expense = 0

            maintenance_year_expense = 0
            management_year_expense = 0
            repairs_year_expense = 0
            utility_year_expense = 0
            utility_year_expected_expense = 0
            maintenance_year_expected_expense = 0
            management_year_expected_expense = 0
            repairs_year_expected_expense = 0

            amortized_utility_expense = 0
            amortized_maintenance_expense = 0
            amortized_management_expense = 0
            amortized_repairs_expense = 0
            amortized_maintenance_expected_expense = 0
            amortized_management_expected_expense = 0
            amortized_repairs_expected_expense = 0
            amortized_utility_expected_expense = 0

            amortized_maintenance_year_expense = 0
            amortized_management_year_expense = 0
            amortized_repairs_year_expense = 0
            amortized_utility_year_expense = 0
            amortized_utility_year_expected_expense = 0
            amortized_maintenance_year_expected_expense = 0
            amortized_management_year_expected_expense = 0
            amortized_repairs_year_expected_expense = 0
            # monthly expenses for the property
            manager_expense = db.execute("""
            SELECT *
            FROM pm.purchases pu
            LEFT JOIN pm.payments pa
            ON pa.pay_purchase_id = pu.purchase_uid
            LEFT JOIN properties pr
            ON pu.pur_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN pm.propertyManager propM
            ON pr.property_uid = propM.linked_property_id
            LEFT JOIN pm.contracts c
            ON c.property_uid LIKE CONCAT('%', pr.property_uid, '%')
            WHERE pu.pur_property_id LIKE CONCAT('%', pr.property_uid, '%')
            AND c.contract_status = 'ACTIVE'
            AND (DATE_FORMAT(pu.next_payment,'%d') <= DATE_FORMAT(now(),'%d') AND {fn MONTHNAME(pu.next_payment)} = {fn MONTHNAME(now())} AND YEAR(pu.next_payment) = YEAR(now()))
            AND (propM.management_status <> 'REJECTED'  OR propM.management_status <> 'TERMINATED' OR propM.management_status <> 'EXPIRED')
            AND (pu.purchase_type = "MAINTENANCE" OR pu.purchase_type = 'REPAIRS' OR pu.purchase_type = "UTILITY")
            AND (payer LIKE '%""" + filterValue + """%')
            AND pu.purchase_status = 'PAID'""")
            print(manager_expense)
            response['result']['manager_expense'] = (list(
                manager_expense['result']))
            if len(manager_expense['result']) > 0:
                # number of weeks in the current month

                for mex in range(len(manager_expense['result'])):
                    # number of months a property has been active
                    delta_active = relativedelta((datetime.strptime(
                        response['result']['manager_expense'][mex]['start_date'], '%Y-%m-%d')), datetime.now())
                    months_active = abs(delta_active.months +
                                        (delta_active.years * 12))
                    # number of months a property has been under an active lease
                    delta_leased = relativedelta((datetime.strptime(
                        response['result']['manager_expense'][mex]['lease_start'], '%Y-%m-%d')), datetime.now())

                    months_leased = abs(delta_leased.months +
                                        (delta_leased.years * 12))
                    # number of weeks in the current month
                    weeks_current_month = len(
                        calendar.monthcalendar(today.year, int(today.strftime("%m"))))
                    # number of weeks a property has been active
                    weeks_active = round((abs(today - datetime.strptime(
                        response['result']['manager_expense'][mex]['start_date'], '%Y-%m-%d').date()).days)/7, 1)
                    # number of weeks a property has been under an active lease
                    weeks_leased = round((abs(today - datetime.strptime(
                        response['result']['manager_expense'][mex]['lease_start'], '%Y-%m-%d').date()).days)/7, 1)
                    # print('mex', manager_expense['result'][mex])
                    # if maintenance
                    if manager_expense['result'][mex]['purchase_type'] == 'MAINTENANCE':
                        # if maintenance monthly
                        # if maintenance monthly
                        if response['result']['manager_expense'][mex]['purchase_frequency'] == 'Monthly':
                            # if maintenance monthly once a month
                            if response['result']['manager_expense'][mex]['payment_frequency'] == 'Once a month' or response['result']['manager_expense'][mex]['payment_frequency'] is None:

                                maintenance_expense = maintenance_expense + \
                                    response['result']['manager_expense'][mex]['amount_paid']
                                # if maintenance monthly twice a month
                            elif response['result']['manager_expense'][mex]['payment_frequency'] == 'Twice a month':

                                maintenance_expense = maintenance_expense + \
                                    2 * \
                                    (response['result']['manager_expense']
                                        [mex]['amount_paid'])
                            else:
                                print('do nothing')
                            # if maintenance annually
                        elif response['result']['manager_expense'][mex]['purchase_frequency'] == 'Annually':
                            # if maintenance annually once a year
                            if response['result']['manager_expense'][mex]['payment_frequency'] == 'Once a year':

                                maintenance_expense = maintenance_expense + \
                                    response['result']['manager_expense'][mex]['amount_paid']

                                amortized_maintenance_expense = amortized_maintenance_expense + \
                                    (response['result']['manager_expense']
                                     [mex]['amount_paid'])/12
                            # if maintenance annually twice a year
                            elif response['result']['manager_expense'][mex]['payment_frequency'] == 'Twice a year':

                                maintenance_expense = maintenance_expense + \
                                    response['result']['manager_expense'][mex]['amount_paid']

                                amortized_maintenance_expense = amortized_maintenance_expense + \
                                    (response['result']['manager_expense']
                                     [mex]['amount_paid'])/6
                            else:
                                print('do nothing')
                        # if maintenance one-time
                        else:

                            maintenance_expense = maintenance_expense + \
                                response['result']['manager_expense'][mex]['amount_paid']

                    if manager_expense['result'][mex]['purchase_type'] == 'REPAIRS':
                        # if repairs monthly
                        if response['result']['manager_expense'][mex]['purchase_frequency'] == 'Monthly':
                            # if repairs monthly once a month
                            if response['result']['manager_expense'][mex]['payment_frequency'] == 'Once a month' or response['result']['manager_expense'][mex]['payment_frequency'] is None:

                                repairs_expense = repairs_expense + \
                                    response['result']['manager_expense'][mex]['amount_paid']
                                # if repairs monthly twice a month
                            elif response['result']['manager_expense'][mex]['payment_frequency'] == 'Twice a month':

                                repairs_expense = repairs_expense + \
                                    2 * \
                                    (response['result']['manager_expense']
                                        [mex]['amount_paid'])
                            else:
                                print('do nothing')
                            # if repairs annually
                        elif response['result']['manager_expense'][mex]['purchase_frequency'] == 'Annually':
                            # if repairs annually once a year
                            if response['result']['manager_expense'][mex]['payment_frequency'] == 'Once a year':

                                repairs_expense = repairs_expense + \
                                    response['result']['manager_expense'][mex]['amount_paid']

                                amortized_repairs_expense = amortized_repairs_expense + \
                                    float(
                                        response['result']['manager_expense'][mex]['amount_paid'])/12
                            # if repairs annually twice a year
                            elif response['result']['manager_expense'][mex]['payment_frequency'] == 'Twice a year':

                                repairs_expense = repairs_expense + \
                                    response['result']['manager_expense'][mex]['amount_paid']

                                amortized_repairs_expense = amortized_repairs_expense + \
                                    float(
                                        response['result']['manager_expense'][mex]['amount_paid'])/6
                            else:
                                print('do nothing')
                        # if repairs one-time
                        else:

                            repairs_expense = repairs_expense + \
                                response['result']['manager_expense'][mex]['amount_paid']

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

            response['result']['maintenance_expense'] = round(
                maintenance_expense, 2)
            response['result']['repairs_expense'] = round(
                repairs_expense, 2)
            response['result']['utility_expense'] = round(
                utility_expense, 2)

            manager_expected_expense = db.execute("""
            SELECT *
            FROM pm.purchases pu
            LEFT JOIN pm.payments pa
            ON pa.pay_purchase_id = pu.purchase_uid
            LEFT JOIN properties pr
            ON pu.pur_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN pm.propertyManager propM
            ON pr.property_uid = propM.linked_property_id
            LEFT JOIN pm.contracts c
            ON c.property_uid LIKE CONCAT('%', pr.property_uid, '%')
            WHERE pu.pur_property_id LIKE CONCAT('%', pr.property_uid, '%')
            AND c.contract_status = 'ACTIVE'
            AND ({fn MONTHNAME(pu.next_payment)} = {fn MONTHNAME(now())} AND YEAR(pu.next_payment) = YEAR(now()))
            AND (propM.management_status <> 'REJECTED'  OR propM.management_status <> 'TERMINATED' OR propM.management_status <> 'EXPIRED')
            AND (pu.purchase_type = "MAINTENANCE" OR pu.purchase_type = 'REPAIRS' OR pu.purchase_type = "UTILITY")
            AND (payer LIKE '%""" + filterValue + """%')""")
            print(manager_expected_expense)
            response['result']['manager_expected_expense'] = (list(
                manager_expected_expense['result']))
        return response
