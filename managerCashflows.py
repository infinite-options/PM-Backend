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
            management_revenue = 0
            rental_expected_revenue = 0
            extra_expected_revenue = 0
            utility_expected_revenue = 0
            management_expected_revenue = 0

            rental_year_revenue = 0
            extra_year_revenue = 0
            utility_year_revenue = 0
            management_year_revenue = 0
            rental_year_expected_revenue = 0
            extra_year_expected_revenue = 0
            utility_year_expected_revenue = 0
            management_year_expected_revenue = 0

            amortized_rental_revenue = 0
            amortized_extra_revenue = 0
            amortized_management_revenue = 0
            amortized_utility_revenue = 0
            amortized_rental_expected_revenue = 0
            amortized_extra_expected_revenue = 0
            amortized_management_expected_revenue = 0
            amortized_utility_expected_revenue = 0

            amortized_rental_year_revenue = 0
            amortized_extra_year_revenue = 0
            amortized_utility_year_revenue = 0
            amortized_management_year_revenue = 0
            amortized_rental_year_expected_revenue = 0
            amortized_extra_year_expected_revenue = 0
            amortized_management_year_expected_revenue = 0
            amortized_utility_year_expected_revenue = 0

            # owner rental and extra charges revenue monthly
            manager_rental_revenue = db.execute("""
            SELECT * FROM purchases pu
            LEFT JOIN payments pa
            ON pa.pay_purchase_id = pu.purchase_uid
            LEFT JOIN properties pr
            ON pu.pur_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN rentals r
            ON r.rental_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN pm.propertyManager prm
            ON prm.linked_property_id = pr.property_uid
            WHERE prm.linked_business_id = \'""" + filterValue + """\'
            AND (DATE_FORMAT(pu.next_payment,'%d') <= DATE_FORMAT(now(),'%d') AND {fn MONTHNAME(pu.next_payment)} = {fn MONTHNAME(now())} AND YEAR(pu.next_payment) = YEAR(now()))
            AND (pu.purchase_type= "RENT" OR pu.purchase_type= "EXTRA CHARGES")
            AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED')
            AND (prm.management_status = 'ACCEPTED' OR prm.management_status='END EARLY' OR prm.management_status='PM END EARLY' OR prm.management_status='OWNER END EARLY')""")

            response['result']['manager_revenue'] = list(
                manager_rental_revenue['result'])

            # owner utility revenue montlhy
            manager_utility_revenue = db.execute("""
            SELECT * FROM purchases pu
            LEFT JOIN payments pa
            ON pa.pay_purchase_id = pu.purchase_uid
            LEFT JOIN properties pr
            ON pu.pur_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN rentals r
            ON r.rental_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN pm.propertyManager prm
            ON prm.linked_property_id = pr.property_uid
            WHERE prm.linked_business_id = \'""" + filterValue + """\'
            AND (DATE_FORMAT(pu.next_payment,'%d') <= DATE_FORMAT(now(),'%d') AND {fn MONTHNAME(pu.next_payment)} = {fn MONTHNAME(now())} AND YEAR(pu.next_payment) = YEAR(now()))
            AND (pu.purchase_type="UTILITY")
            AND pu.receiver = \'""" + filterValue + """\'
            AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED') 
            AND (prm.management_status = 'ACCEPTED' OR prm.management_status='END EARLY' OR prm.management_status='PM END EARLY' OR prm.management_status='OWNER END EARLY') """)

            response['result']['manager_revenue'] = response['result']['manager_revenue'] + list(
                manager_utility_revenue['result'])

            # owner utility revenue montlhy
            manager_management_revenue = db.execute("""
            SELECT * FROM purchases pu
            LEFT JOIN payments pa
            ON pa.pay_purchase_id = pu.purchase_uid
            LEFT JOIN properties pr
            ON pu.pur_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN rentals r
            ON r.rental_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN pm.propertyManager prm
            ON prm.linked_property_id = pr.property_uid
            WHERE prm.linked_business_id = \'""" + filterValue + """\'
            AND (DATE_FORMAT(pu.next_payment,'%d') <= DATE_FORMAT(now(),'%d') AND {fn MONTHNAME(pu.next_payment)} = {fn MONTHNAME(now())} AND YEAR(pu.next_payment) = YEAR(now()))
            AND pu.purchase_type="MANAGEMENT"
            AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED') 
            AND (prm.management_status = 'ACCEPTED' OR prm.management_status='END EARLY' OR prm.management_status='PM END EARLY' OR prm.management_status='OWNER END EARLY') """)

            response['result']['manager_revenue'] = response['result']['manager_revenue'] + list(
                manager_management_revenue['result'])

            if len(response['result']['manager_revenue']) > 0:
                for ore in range(len(response['result']['manager_revenue'])):
                    # number of weeks in the current month
                    weeks_current_month = len(
                        calendar.monthcalendar(today.year, int(today.strftime("%m"))))
                    if response['result']['manager_revenue'][ore]['purchase_type'] == 'RENT':
                        if response['result']['manager_revenue'][ore]['purchase_frequency'] == 'Weekly':

                            rental_revenue = rental_revenue + \
                                weeks_current_month*int(response['result']['manager_revenue']
                                                        [ore]['amount_paid'])

                        elif response['result']['manager_revenue'][ore]['purchase_frequency'] == 'Biweekly':

                            rental_revenue = rental_revenue + \
                                weeks_current_month/2 * \
                                int(response['result']['manager_revenue']
                                    [ore]['amount_paid'])
                        elif response['result']['manager_revenue'][ore]['purchase_frequency'] == 'Monthly':
                            print('before', rental_revenue)
                            rental_revenue = rental_revenue + \
                                response['result']['manager_revenue'][ore]['amount_paid']
                            print(rental_revenue)
                        elif response['result']['manager_revenue'][ore]['purchase_frequency'] == 'Annually':

                            rental_revenue = rental_revenue + \
                                response['result']['manager_revenue'][ore]['amount_paid']
                            amortized_rental_revenue = amortized_rental_revenue + \
                                int(response['result']['manager_revenue']
                                    [ore]['amount_due'])/(datetime.now().month-1)

                        else:

                            rental_revenue = rental_revenue + \
                                response['result']['manager_revenue'][ore]['amount_paid']

                    if response['result']['manager_revenue'][ore]['purchase_type'] == 'EXTRA CHARGES':
                        if response['result']['manager_revenue'][ore]['purchase_frequency'] == 'Weekly':

                            extra_revenue = extra_revenue + \
                                weeks_current_month*int(response['result']['manager_revenue']
                                                        [ore]['amount_paid'])
                        elif response['result']['manager_revenue'][ore]['purchase_frequency'] == 'Biweekly':

                            extra_revenue = extra_revenue + \
                                weeks_current_month/2 * \
                                int(response['result']['manager_revenue']
                                    [ore]['amount_paid'])
                        elif response['result']['manager_revenue'][ore]['purchase_frequency'] == 'Monthly':

                            extra_revenue = extra_revenue + \
                                response['result']['manager_revenue'][ore]['amount_paid']
                        elif response['result']['manager_revenue'][ore]['purchase_frequency'] == 'Annually':

                            extra_revenue = extra_revenue + \
                                response['result']['manager_revenue'][ore]['amount_paid']
                            amortized_extra_revenue = amortized_extra_revenue + \
                                int(response['result']['manager_revenue']
                                    [ore]['amount_due'])/(datetime.now().month-1)

                        else:

                            extra_revenue = extra_revenue + \
                                response['result']['manager_revenue'][ore]['amount_paid']

                    if response['result']['manager_revenue'][ore]['purchase_type'] == 'UTILITY':
                        if response['result']['manager_revenue'][ore]['purchase_frequency'] == 'Weekly':

                            utility_revenue = utility_revenue + \
                                weeks_current_month*int(response['result']['manager_revenue']
                                                        [ore]['amount_paid'])
                        elif response['result']['manager_revenue'][ore]['purchase_frequency'] == 'Biweekly':

                            utility_revenue = utility_revenue + \
                                weeks_current_month/2 * \
                                int(response['result']['manager_revenue']
                                    [ore]['amount_paid'])
                        elif response['result']['manager_revenue'][ore]['purchase_frequency'] == 'Monthly':

                            utility_revenue = utility_revenue + \
                                response['result']['manager_revenue'][ore]['amount_paid']
                        elif response['result']['manager_revenue'][ore]['purchase_frequency'] == 'Annually':

                            utility_revenue = utility_revenue + \
                                response['result']['manager_revenue'][ore]['amount_paid']
                            amortized_utility_revenue = amortized_utility_revenue + \
                                int(response['result']['manager_revenue']
                                    [ore]['amount_due'])/(datetime.now().month-1)

                        else:

                            utility_revenue = utility_revenue + \
                                response['result']['manager_revenue'][ore]['amount_paid']

                    if response['result']['manager_revenue'][ore]['purchase_type'] == 'MANAGEMENT':
                        if response['result']['manager_revenue'][ore]['purchase_frequency'] == 'Weekly':

                            management_revenue = management_revenue + \
                                weeks_current_month*abs(int(response['result']['manager_revenue']
                                                        [ore]['amount_paid']))
                        elif response['result']['manager_revenue'][ore]['purchase_frequency'] == 'Biweekly':

                            management_revenue = management_revenue + \
                                weeks_current_month/2 * \
                                abs(int(response['result']['manager_revenue']
                                    [ore]['amount_paid']))
                        elif response['result']['manager_revenue'][ore]['purchase_frequency'] == 'Monthly':

                            management_revenue = management_revenue + \
                                abs(response['result']['manager_revenue']
                                    [ore]['amount_paid'])
                        elif response['result']['manager_revenue'][ore]['purchase_frequency'] == 'Annually':

                            management_revenue = management_revenue + \
                                abs(response['result']['manager_revenue']
                                    [ore]['amount_paid'])
                            amortized_management_revenue = amortized_management_revenue + \
                                int(response['result']['manager_revenue']
                                    [ore]['amount_due'])/(datetime.now().month-1)

                        else:

                            management_revenue = management_revenue + \
                                abs(response['result']['manager_revenue']
                                    [ore]['amount_paid'])

            response['result']['rental_revenue'] = round(
                rental_revenue, 2)

            response['result']['amortized_rental_revenue'] = round(
                amortized_rental_revenue, 2)

            response['result']['extra_revenue'] = round(
                extra_revenue, 2)

            response['result']['amortized_extra_revenue'] = round(
                amortized_extra_revenue, 2)

            response['result']['utility_revenue'] = round(
                utility_revenue, 2)

            response['result']['amortized_utility_revenue'] = round(
                amortized_utility_revenue, 2)
            response['result']['management_revenue'] = round(
                management_revenue, 2)

            response['result']['amortized_management_revenue'] = round(
                amortized_extra_revenue, 2)

            # owner rental and extra charged revenue yearly
            # owner rental and extra charges revenue monthly
            manager_rental_expected_revenue = db.execute("""
            SELECT * FROM purchases pu
            LEFT JOIN payments pa
            ON pa.pay_purchase_id = pu.purchase_uid
            LEFT JOIN properties pr
            ON pu.pur_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN rentals r
            ON r.rental_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN pm.propertyManager prm
            ON prm.linked_property_id = pr.property_uid
            WHERE prm.linked_business_id = \'""" + filterValue + """\'
            AND ({fn MONTHNAME(pu.next_payment)} = {fn MONTHNAME(now())} AND YEAR(pu.next_payment) = YEAR(now()))
            AND (pu.purchase_type= "RENT" OR pu.purchase_type= "EXTRA CHARGES")
            AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED')
            AND (prm.management_status = 'ACCEPTED' OR prm.management_status='END EARLY' OR prm.management_status='PM END EARLY' OR prm.management_status='OWNER END EARLY') """)

            response['result']['manager_expected_revenue'] = list(
                manager_rental_expected_revenue['result'])

            # owner utility revenue montlhy
            manager_utility_expected_revenue = db.execute("""
            SELECT * FROM purchases pu
            LEFT JOIN payments pa
            ON pa.pay_purchase_id = pu.purchase_uid
            LEFT JOIN properties pr
            ON pu.pur_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN rentals r
            ON r.rental_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN pm.propertyManager prm
            ON prm.linked_property_id = pr.property_uid
            WHERE prm.linked_business_id = \'""" + filterValue + """\'
            AND ({fn MONTHNAME(pu.next_payment)} = {fn MONTHNAME(now())} AND YEAR(pu.next_payment) = YEAR(now()))
            AND (pu.purchase_type="UTILITY")
            AND pu.receiver = \'""" + filterValue + """\'
            AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED') 
            AND (prm.management_status = 'ACCEPTED' OR prm.management_status='END EARLY' OR prm.management_status='PM END EARLY' OR prm.management_status='OWNER END EARLY')""")

            response['result']['manager_expected_revenue'] = response['result']['manager_expected_revenue'] + list(
                manager_utility_expected_revenue['result'])
            response['result']['manager_utility_expected_revenue'] = list(
                manager_utility_expected_revenue['result'])
            # owner utility revenue montlhy
            manager_management_expected_revenue = db.execute("""
            SELECT * FROM purchases pu
            LEFT JOIN payments pa
            ON pa.pay_purchase_id = pu.purchase_uid
            LEFT JOIN properties pr
            ON pu.pur_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN rentals r
            ON r.rental_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN pm.propertyManager prm
            ON prm.linked_property_id = pr.property_uid
            WHERE prm.linked_business_id = \'""" + filterValue + """\'
            AND ({fn MONTHNAME(pu.next_payment)} = {fn MONTHNAME(now())} AND YEAR(pu.next_payment) = YEAR(now()))
            AND (pu.purchase_type="MANAGEMENT")
            AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED') 
            AND (prm.management_status = 'ACCEPTED' OR prm.management_status='END EARLY' OR prm.management_status='PM END EARLY' OR prm.management_status='OWNER END EARLY')""")

            response['result']['manager_expected_revenue'] = response['result']['manager_expected_revenue'] + list(
                manager_management_expected_revenue['result'])

            if len(response['result']['manager_expected_revenue']) > 0:
                for ore in range(len(response['result']['manager_expected_revenue'])):
                    # number of weeks in the current month
                    weeks_current_month = len(
                        calendar.monthcalendar(today.year, int(today.strftime("%m"))))

                    if response['result']['manager_expected_revenue'][ore]['purchase_type'] == 'RENT':
                        if response['result']['manager_expected_revenue'][ore]['purchase_frequency'] == 'Weekly':
                            rental_expected_revenue = rental_expected_revenue + \
                                weeks_current_month*int(response['result']['manager_expected_revenue']
                                                        [ore]['amount_due'])

                        elif response['result']['manager_expected_revenue'][ore]['purchase_frequency'] == 'Biweekly':
                            rental_expected_revenue = rental_expected_revenue + \
                                weeks_current_month/2 * \
                                int(response['result']['manager_expected_revenue']
                                    [ore]['amount_due'])

                        elif response['result']['manager_expected_revenue'][ore]['purchase_frequency'] == 'Monthly':
                            rental_expected_revenue = rental_expected_revenue + \
                                response['result']['manager_expected_revenue'][ore]['amount_due']

                        elif response['result']['manager_expected_revenue'][ore]['purchase_frequency'] == 'Annually':
                            rental_expected_revenue = rental_expected_revenue + \
                                response['result']['manager_expected_revenue'][ore]['amount_due']

                            amortized_rental_expected_revenue = amortized_rental_expected_revenue + \
                                int(response['result']['manager_expected_revenue']
                                    [ore]['amount_due'])/12
                        else:
                            rental_expected_revenue = rental_expected_revenue + \
                                response['result']['manager_expected_revenue'][ore]['amount_due']

                    if response['result']['manager_expected_revenue'][ore]['purchase_type'] == 'EXTRA CHARGES':
                        if response['result']['manager_expected_revenue'][ore]['purchase_frequency'] == 'Weekly':
                            extra_expected_revenue = extra_expected_revenue + \
                                weeks_current_month*int(response['result']['manager_expected_revenue']
                                                        [ore]['amount_due'])

                        elif response['result']['manager_expected_revenue'][ore]['purchase_frequency'] == 'Biweekly':
                            extra_expected_revenue = extra_expected_revenue + \
                                weeks_current_month/2 * \
                                int(response['result']['manager_expected_revenue']
                                    [ore]['amount_due'])

                        elif response['result']['manager_expected_revenue'][ore]['purchase_frequency'] == 'Monthly':
                            extra_expected_revenue = extra_expected_revenue + \
                                response['result']['manager_expected_revenue'][ore]['amount_due']

                        elif response['result']['manager_expected_revenue'][ore]['purchase_frequency'] == 'Annually':

                            extra_expected_revenue = extra_expected_revenue + \
                                response['result']['manager_expected_revenue'][ore]['amount_due']

                            amortized_extra_expected_revenue = amortized_extra_expected_revenue + \
                                int(response['result']['manager_expected_revenue']
                                    [ore]['amount_due'])/12
                        else:
                            extra_expected_revenue = extra_expected_revenue + \
                                response['result']['manager_expected_revenue'][ore]['amount_due']

                    if response['result']['manager_expected_revenue'][ore]['purchase_type'] == 'UTILITY':
                        if response['result']['manager_expected_revenue'][ore]['purchase_frequency'] == 'Weekly':
                            utility_expected_revenue = utility_expected_revenue + \
                                weeks_current_month*int(response['result']['manager_expected_revenue']
                                                        [ore]['amount_due'])

                        elif response['result']['manager_expected_revenue'][ore]['purchase_frequency'] == 'Biweekly':
                            utility_expected_revenue = utility_expected_revenue + \
                                weeks_current_month/2 * \
                                int(response['result']['manager_expected_revenue']
                                    [ore]['amount_due'])

                        elif response['result']['manager_expected_revenue'][ore]['purchase_frequency'] == 'Monthly':
                            utility_expected_revenue = utility_expected_revenue + \
                                response['result']['manager_expected_revenue'][ore]['amount_due']

                        elif response['result']['manager_expected_revenue'][ore]['purchase_frequency'] == 'Annually':
                            utility_expected_revenue = utility_expected_revenue + \
                                response['result']['manager_expected_revenue'][ore]['amount_due']
                            amortized_utility_expected_revenue = amortized_utility_expected_revenue + \
                                int(response['result']['manager_expected_revenue']
                                    [ore]['amount_due'])/12
                        else:
                            utility_expected_revenue = utility_expected_revenue + \
                                response['result']['manager_expected_revenue'][ore]['amount_due']
                    if response['result']['manager_expected_revenue'][ore]['purchase_type'] == 'MANAGEMENT':
                        if response['result']['manager_expected_revenue'][ore]['purchase_frequency'] == 'Weekly':
                            management_expected_revenue = management_expected_revenue + \
                                weeks_current_month*int(abs(response['result']['manager_expected_revenue']
                                                        [ore]['amount_due']))

                        elif response['result']['manager_expected_revenue'][ore]['purchase_frequency'] == 'Biweekly':
                            management_expected_revenue = management_expected_revenue + \
                                weeks_current_month/2 * \
                                int(abs(response['result']['manager_expected_revenue']
                                    [ore]['amount_due']))

                        elif response['result']['manager_expected_revenue'][ore]['purchase_frequency'] == 'Monthly':
                            management_expected_revenue = management_expected_revenue + \
                                abs(response['result']
                                    ['manager_expected_revenue'][ore]['amount_due'])

                        elif response['result']['manager_expected_revenue'][ore]['purchase_frequency'] == 'Annually':
                            management_expected_revenue = management_expected_revenue + \
                                abs(response['result']
                                    ['manager_expected_revenue'][ore]['amount_due'])
                            amortized_management_expected_revenue = amortized_management_expected_revenue + \
                                int(response['result']['manager_expected_revenue']
                                    [ore]['amount_due'])/12
                        else:
                            management_expected_revenue = management_expected_revenue + \
                                abs(response['result']
                                    ['manager_expected_revenue'][ore]['amount_due'])
            response['result']['rental_expected_revenue'] = round(
                rental_expected_revenue, 2)
            response['result']['amortized_rental_expected_revenue'] = round(
                amortized_rental_expected_revenue, 2)
            response['result']['extra_expected_revenue'] = round(
                extra_expected_revenue, 2)
            response['result']['amortized_extra_expected_revenue'] = round(
                amortized_extra_expected_revenue, 2)
            response['result']['utility_expected_revenue'] = round(
                utility_expected_revenue, 2)
            response['result']['amortized_utility_expected_revenue'] = round(
                amortized_utility_expected_revenue, 2)
            response['result']['management_expected_revenue'] = round(
                management_expected_revenue, 2)
            response['result']['amortized_management_expected_revenue'] = round(
                amortized_management_expected_revenue, 2)

            manager_rental_revenue_yearly = db.execute("""
            SELECT * FROM purchases pu
            LEFT JOIN payments pa
            ON pa.pay_purchase_id = pu.purchase_uid
            LEFT JOIN properties pr
            ON pu.pur_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN rentals r
            ON r.rental_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN pm.propertyManager prm
            ON prm.linked_property_id = pr.property_uid
            WHERE prm.linked_business_id = \'""" + filterValue + """\'
            AND YEAR(pu.next_payment) = YEAR(now())
            AND (pu.purchase_type= "RENT" OR pu.purchase_type= "EXTRA CHARGES")
            AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED')
            AND (prm.management_status = 'ACCEPTED' OR prm.management_status='END EARLY' OR prm.management_status='PM END EARLY' OR prm.management_status='OWNER END EARLY')""")

            response['result']['manager_revenue_yearly'] = list(
                manager_rental_revenue_yearly['result'])

            # owner utility revenue yearly
            manager_utility_revenue_yearly = db.execute("""
            SELECT * FROM purchases pu
            LEFT JOIN payments pa
            ON pa.pay_purchase_id = pu.purchase_uid
            LEFT JOIN properties pr
            ON pu.pur_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN rentals r
            ON r.rental_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN pm.propertyManager prm
            ON prm.linked_property_id = pr.property_uid
            WHERE prm.linked_business_id = \'""" + filterValue + """\'
            AND YEAR(pu.next_payment) = YEAR(now())
            AND (pu.purchase_type="UTILITY")
            AND pu.receiver = \'""" + filterValue + """\'
            AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED')
            AND (prm.management_status = 'ACCEPTED' OR prm.management_status='END EARLY' OR prm.management_status='PM END EARLY' OR prm.management_status='OWNER END EARLY') """)

            response['result']['manager_revenue_yearly'] = response['result']['manager_revenue_yearly'] + list(
                manager_utility_revenue_yearly['result'])
            # owner management revenue yearly
            manager_management_revenue_yearly = db.execute("""
            SELECT * FROM purchases pu
            LEFT JOIN payments pa
            ON pa.pay_purchase_id = pu.purchase_uid
            LEFT JOIN properties pr
            ON pu.pur_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN rentals r
            ON r.rental_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN pm.propertyManager prm
            ON prm.linked_property_id = pr.property_uid
            WHERE prm.linked_business_id = \'""" + filterValue + """\'
            AND YEAR(pu.next_payment) = YEAR(now())
            AND (pu.purchase_type="MANAGEMENT")
            AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED')
            AND (prm.management_status = 'ACCEPTED' OR prm.management_status='END EARLY' OR prm.management_status='PM END EARLY' OR prm.management_status='OWNER END EARLY') """)

            response['result']['manager_revenue_yearly'] = response['result']['manager_revenue_yearly'] + list(
                manager_management_revenue_yearly['result'])
            if len(response['result']['manager_revenue_yearly']) > 0:
                for ore in range(len(response['result']['manager_revenue_yearly'])):

                    # number of months a property has been active
                    delta_active = relativedelta((datetime.strptime(
                        response['result']['manager_revenue_yearly'][ore]['active_date'], '%Y-%m-%d')), datetime.now())
                    months_active = abs(delta_active.months +
                                        (delta_active.years * 12))
                    # number of months a property has been under an active lease
                    delta_leased = relativedelta((datetime.strptime(
                        response['result']['manager_revenue_yearly'][ore]['lease_start'], '%Y-%m-%d')), datetime.now())

                    months_leased = abs(delta_leased.months +
                                        (delta_leased.years * 12))
                    if months_leased == 0:
                        months_leased = 1
                    # number of weeks in the current month
                    weeks_current_month = len(
                        calendar.monthcalendar(today.year, int(today.strftime("%m"))))
                    # number of weeks a property has been active
                    weeks_active = round((abs(today - datetime.strptime(
                        response['result']['manager_revenue_yearly'][ore]['active_date'], '%Y-%m-%d').date()).days)/7, 1)
                    # number of weeks a property has been under an active lease
                    weeks_leased = round((abs(today - datetime.strptime(
                        response['result']['manager_revenue_yearly'][ore]['lease_start'], '%Y-%m-%d').date()).days)/7, 1)
                    print('months leased', months_leased)
                    # if revenue type is RENT
                    if response['result']['manager_revenue_yearly'][ore]['purchase_type'] == 'RENT':
                        print('IF RENT')
                        if response['result']['manager_revenue_yearly'][ore]['purchase_frequency'] == 'Weekly':
                            rental_year_expected_revenue = rental_year_expected_revenue + \
                                weeks_leased*int(response['result']['manager_revenue_yearly']
                                                 [ore]['amount_due'])
                            rental_year_revenue = rental_year_revenue + \
                                weeks_leased*int(response['result']['manager_revenue_yearly']
                                                         [ore]['amount_paid'])

                        elif response['result']['manager_revenue_yearly'][ore]['purchase_frequency'] == 'Biweekly':
                            rental_year_expected_revenue = rental_year_expected_revenue + \
                                weeks_leased/2 * \
                                int(response['result']['manager_revenue_yearly']
                                    [ore]['amount_due'])
                            rental_year_revenue = rental_year_revenue + \
                                weeks_leased/2 * \
                                int(response['result']['manager_revenue_yearly']
                                    [ore]['amount_paid'])
                        elif response['result']['manager_revenue_yearly'][ore]['purchase_frequency'] == 'Monthly':
                            print('if monthly')
                            rental_year_expected_revenue = rental_year_expected_revenue + \
                                months_leased * \
                                int(response['result']
                                    ['manager_revenue_yearly'][ore]['amount_due'])
                            rental_year_revenue = rental_year_revenue + \
                                months_leased * \
                                int(response['result']['manager_revenue_yearly']
                                    [ore]['amount_paid'])

                        elif response['result']['manager_revenue_yearly'][ore]['purchase_frequency'] == 'Annually':
                            rental_year_expected_revenue = rental_year_expected_revenue + \
                                response['result']['manager_revenue_yearly'][ore]['amount_due']
                            rental_year_revenue = rental_year_revenue + \
                                response['result']['manager_revenue_yearly'][ore]['amount_paid']
                            amortized_rental_year_expected_revenue = amortized_rental_year_expected_revenue + \
                                int(response['result']['manager_revenue_yearly']
                                    [ore]['amount_due'])/12
                            amortized_rental_year_revenue = amortized_rental_year_revenue + \
                                int(response['result']['manager_revenue_yearly']
                                    [ore]['amount_paid'])/12
                        else:
                            rental_year_expected_revenue = rental_year_expected_revenue + \
                                response['result']['manager_revenue_yearly'][ore]['amount_due']
                            rental_year_revenue = rental_year_revenue + \
                                response['result']['manager_revenue_yearly'][ore]['amount_paid']

                     # if revenue type is EXTRA CHARGES
                    if response['result']['manager_revenue_yearly'][ore]['purchase_type'] == 'EXTRA CHARGES':
                        if response['result']['manager_revenue_yearly'][ore]['purchase_frequency'] == 'Weekly':
                            extra_year_expected_revenue = extra_year_expected_revenue + \
                                weeks_leased*int(response['result']['manager_revenue_yearly']
                                                         [ore]['amount_due'])
                            extra_year_revenue = extra_year_revenue + \
                                weeks_leased*int(response['result']['manager_revenue_yearly']
                                                         [ore]['amount_paid'])
                        elif response['result']['manager_revenue_yearly'][ore]['purchase_frequency'] == 'Biweekly':
                            extra_year_expected_revenue = extra_year_expected_revenue + \
                                weeks_leased/2 * \
                                int(response['result']['manager_revenue_yearly']
                                    [ore]['amount_due'])
                            extra_year_revenue = extra_year_revenue + \
                                weeks_leased/2 * \
                                int(response['result']['manager_revenue_yearly']
                                    [ore]['amount_paid'])
                        elif response['result']['manager_revenue_yearly'][ore]['purchase_frequency'] == 'Monthly':
                            extra_year_expected_revenue = extra_year_expected_revenue + \
                                months_leased * \
                                int(response['result']
                                    ['manager_revenue_yearly'][ore]['amount_due'])
                            extra_year_revenue = extra_year_revenue + \
                                months_leased * \
                                int(response['result']['manager_revenue_yearly']
                                    [ore]['amount_paid'])
                        elif response['result']['manager_revenue_yearly'][ore]['purchase_frequency'] == 'Annually':

                            extra_year_expected_revenue = extra_year_expected_revenue + \
                                response['result']['manager_revenue_yearly'][ore]['amount_due']
                            extra_year_revenue = extra_year_revenue + \
                                response['result']['manager_revenue_yearly'][ore]['amount_paid']
                            amortized_extra_year_expected_revenue = amortized_extra_year_expected_revenue + \
                                int(response['result']['manager_revenue_yearly']
                                    [ore]['amount_due'])/12
                            amortized_extra_year_revenue = amortized_extra_year_revenue + \
                                int(response['result']['manager_revenue_yearly']
                                    [ore]['amount_paid'])/12
                        else:
                            extra_year_expected_revenue = extra_year_expected_revenue + \
                                response['result']['manager_revenue_yearly'][ore]['amount_due']
                            extra_year_revenue = extra_year_revenue + \
                                response['result']['manager_revenue_yearly'][ore]['amount_paid']

                     # if revenue type is UTILITY
                    if response['result']['manager_revenue_yearly'][ore]['purchase_type'] == 'UTILITY':
                        if response['result']['manager_revenue_yearly'][ore]['purchase_frequency'] == 'Weekly':
                            utility_year_expected_revenue = utility_year_expected_revenue + \
                                weeks_leased*int(response['result']['manager_revenue_yearly']
                                                         [ore]['amount_due'])
                            utility_year_revenue = utility_year_revenue + \
                                weeks_leased*int(response['result']['manager_revenue_yearly']
                                                         [ore]['amount_paid'])
                        elif response['result']['manager_revenue_yearly'][ore]['purchase_frequency'] == 'Biweekly':
                            utility_year_expected_revenue = utility_year_expected_revenue + \
                                weeks_leased/2 * \
                                int(response['result']['manager_revenue_yearly']
                                    [ore]['amount_due'])
                            utility_year_revenue = utility_year_revenue + \
                                weeks_leased/2 * \
                                int(response['result']['manager_revenue_yearly']
                                    [ore]['amount_paid'])
                        elif response['result']['manager_revenue_yearly'][ore]['purchase_frequency'] == 'Monthly':
                            utility_year_expected_revenue = utility_year_expected_revenue + \
                                months_leased * \
                                int(response['result']
                                    ['manager_revenue_yearly'][ore]['amount_due'])
                            utility_year_revenue = utility_year_revenue + \
                                months_leased * \
                                int(response['result']['manager_revenue_yearly']
                                    [ore]['amount_paid'])
                        elif response['result']['manager_revenue_yearly'][ore]['purchase_frequency'] == 'Annually':
                            utility_year_expected_revenue = utility_year_expected_revenue + \
                                response['result']['manager_revenue_yearly'][ore]['amount_due']
                            utility_year_revenue = utility_year_revenue + \
                                response['result']['manager_revenue_yearly'][ore]['amount_paid']
                            amortized_utility_year_expected_revenue = amortized_utility_year_expected_revenue + \
                                int(response['result']['manager_revenue_yearly']
                                    [ore]['amount_due'])/12
                            amortized_utility_year_revenue = amortized_utility_year_revenue + \
                                int(response['result']['manager_revenue_yearly']
                                    [ore]['amount_paid'])/12
                        else:
                            utility_year_expected_revenue = utility_year_expected_revenue + \
                                response['result']['manager_revenue_yearly'][ore]['amount_due']
                            utility_year_revenue = utility_year_revenue + \
                                response['result']['manager_revenue_yearly'][ore]['amount_paid']
                    if response['result']['manager_revenue_yearly'][ore]['purchase_type'] == 'MANAGEMENT':
                        if response['result']['manager_revenue_yearly'][ore]['purchase_frequency'] == 'Weekly':
                            management_year_expected_revenue = management_year_expected_revenue + \
                                weeks_leased*int(abs(response['result']['manager_revenue_yearly']
                                                     [ore]['amount_due']))
                            management_year_revenue = management_year_revenue + \
                                weeks_leased*int(abs(response['result']['manager_revenue_yearly']
                                                     [ore]['amount_paid']))
                        elif response['result']['manager_revenue_yearly'][ore]['purchase_frequency'] == 'Biweekly':
                            management_year_expected_revenue = management_year_expected_revenue + \
                                weeks_leased/2 * \
                                int(abs(response['result']['manager_revenue_yearly']
                                    [ore]['amount_due']))
                            management_year_revenue = management_year_revenue + \
                                weeks_leased/2 * \
                                int(response['result']['manager_revenue_yearly']
                                    [ore]['amount_paid'])
                        elif response['result']['manager_revenue_yearly'][ore]['purchase_frequency'] == 'Monthly':
                            management_year_expected_revenue = management_year_expected_revenue + \
                                months_leased * \
                                int(abs(response['result']
                                    ['manager_revenue_yearly'][ore]['amount_due']))
                            management_year_revenue = management_year_revenue + \
                                months_leased * \
                                int(abs(response['result']['manager_revenue_yearly']
                                    [ore]['amount_paid']))
                        elif response['result']['manager_revenue_yearly'][ore]['purchase_frequency'] == 'Annually':
                            management_year_expected_revenue = management_year_expected_revenue + \
                                abs(response['result']
                                    ['manager_revenue_yearly'][ore]['amount_due'])
                            management_year_revenue = management_year_revenue + \
                                abs(response['result']['manager_revenue_yearly']
                                    [ore]['amount_paid'])
                            amortized_management_year_expected_revenue = amortized_management_year_expected_revenue + \
                                int(abs(response['result']['manager_revenue_yearly']
                                    [ore]['amount_due']))/12
                            amortized_management_year_revenue = amortized_management_year_revenue + \
                                int(abs(response['result']['manager_revenue_yearly']
                                    [ore]['amount_paid']))/12
                        else:
                            management_year_expected_revenue = management_year_expected_revenue + \
                                abs(response['result']
                                    ['manager_revenue_yearly'][ore]['amount_due'])
                            management_year_revenue = management_year_revenue + \
                                abs(response['result']['manager_revenue_yearly']
                                    [ore]['amount_paid'])

            response['result']['rental_year_revenue'] = round(
                rental_year_revenue, 2)
            response['result']['rental_year_expected_revenue'] = round(
                rental_year_expected_revenue, 2)
            response['result']['amortized_rental_year_revenue'] = round(
                amortized_rental_year_revenue, 2)
            response['result']['amortized_rental_year_expected_revenue'] = round(
                amortized_rental_year_expected_revenue, 2)
            response['result']['extra_year_revenue'] = round(
                extra_year_revenue, 2)
            response['result']['extra_year_expected_revenue'] = round(
                extra_year_expected_revenue, 2)
            response['result']['amortized_extra_year_revenue'] = round(
                amortized_extra_year_revenue, 2)
            response['result']['amortized_extra_year_expected_revenue'] = round(
                amortized_extra_year_expected_revenue, 2)
            response['result']['utility_year_revenue'] = round(
                utility_year_revenue, 2)
            response['result']['utility_year_expected_revenue'] = round(
                utility_year_expected_revenue, 2)
            response['result']['amortized_utility_year_revenue'] = round(
                amortized_utility_year_revenue, 2)
            response['result']['amortized_utility_year_expected_revenue'] = round(
                amortized_utility_year_expected_revenue, 2)
            response['result']['management_year_revenue'] = round(
                management_year_revenue, 2)
            response['result']['management_year_expected_revenue'] = round(
                management_year_expected_revenue, 2)
            response['result']['amortized_management_year_revenue'] = round(
                amortized_management_year_revenue, 2)
            response['result']['amortized_management_year_expected_revenue'] = round(
                amortized_management_year_expected_revenue, 2)

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
            LEFT JOIN pm.propertyManager prm
            ON pr.property_uid = prm.linked_property_id
            LEFT JOIN pm.contracts c
            ON c.property_uid LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN pm.rentals r
            ON r.rental_property_id = pr.property_uid
            WHERE pu.pur_property_id LIKE CONCAT('%', pr.property_uid, '%')
            AND c.contract_status = 'ACTIVE'
            AND (DATE_FORMAT(pu.next_payment,'%d') <= DATE_FORMAT(now(),'%d') AND {fn MONTHNAME(pu.next_payment)} = {fn MONTHNAME(now())} AND YEAR(pu.next_payment) = YEAR(now()))
            AND (prm.management_status <> 'REJECTED'  OR prm.management_status <> 'TERMINATED' OR prm.management_status <> 'EXPIRED')
            AND (pu.purchase_type = "MAINTENANCE" OR pu.purchase_type = 'REPAIRS' OR pu.purchase_type = "UTILITY" OR pu.purchase_type = "OWNER PAYMENT" )
            AND (payer LIKE '%""" + filterValue + """%')""")
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
                    print(response['result']['manager_expense'][mex])
                    delta_leased = relativedelta((datetime.strptime(
                        response['result']['manager_expense'][mex]['lease_start'], '%Y-%m-%d')), datetime.now())

                    months_leased = abs(delta_leased.months +
                                        (delta_leased.years * 12))
                    if months_leased == 0:
                        months_leased = 1
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

                            utility_expense = utility_expense + \
                                float(manager_expense['result']
                                      [mex]['amount_paid'])
                        elif manager_expense['result'][mex]['purchase_frequency'] == 'Biweekly':

                            utility_expense = utility_expense + \
                                float(manager_expense['result']
                                      [mex]['amount_paid'])
                        elif manager_expense['result'][mex]['purchase_frequency'] == 'Monthly':

                            utility_expense = utility_expense + \
                                manager_expense['result'][mex]['amount_paid']
                        elif manager_expense['result'][mex]['purchase_frequency'] == 'Annually':

                            utility_expense = utility_expense + \
                                manager_expense['result'][mex]['amount_paid']
                            amortized_utility_expense = amortized_utility_expense + \
                                float(
                                    response['result']['manager_expense'][mex]['amount_paid'])/12
                        else:

                            utility_expense = utility_expense + \
                                manager_expense['result'][mex]['amount_paid']
                    if manager_expense['result'][mex]['purchase_type'] == 'OWNER PAYMENT':
                        if manager_expense['result'][mex]['purchase_frequency'] == 'Weekly':

                            management_expense = management_expense + \
                                float(manager_expense['result']
                                      [mex]['amount_paid'])
                        elif manager_expense['result'][mex]['purchase_frequency'] == 'Biweekly':

                            management_expense = management_expense + \
                                float(manager_expense['result']
                                      [mex]['amount_paid'])
                        elif manager_expense['result'][mex]['purchase_frequency'] == 'Monthly':

                            management_expense = management_expense + \
                                manager_expense['result'][mex]['amount_paid']
                        elif manager_expense['result'][mex]['purchase_frequency'] == 'Annually':

                            management_expense = management_expense + \
                                manager_expense['result'][mex]['amount_paid']
                            amortized_management_expense = amortized_management_expense + \
                                float(
                                    response['result']['manager_expense'][mex]['amount_paid'])/12
                        else:

                            management_expense = management_expense + \
                                manager_expense['result'][mex]['amount_paid']

            response['result']['maintenance_expense'] = round(
                maintenance_expense, 2)
            response['result']['repairs_expense'] = round(
                repairs_expense, 2)
            response['result']['utility_expense'] = round(
                utility_expense, 2)
            response['result']['management_expense'] = round(
                management_expense, 2)
            response['result']['amortized_maintenance_expense'] = round(
                amortized_maintenance_expense, 2)
            response['result']['amortized_repairs_expense'] = round(
                amortized_repairs_expense, 2)
            response['result']['amortized_utility_expense'] = round(
                amortized_utility_expense, 2)
            response['result']['amortized_management_expense'] = round(
                amortized_management_expense, 2)

            manager_expected_expense = db.execute("""
            SELECT *
            FROM pm.purchases pu
            LEFT JOIN pm.payments pa
            ON pa.pay_purchase_id = pu.purchase_uid
            LEFT JOIN properties pr
            ON pu.pur_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN pm.propertyManager prm
            ON pr.property_uid = prm.linked_property_id
            LEFT JOIN pm.contracts c
            ON c.property_uid LIKE CONCAT('%', pr.property_uid, '%')
            WHERE pu.pur_property_id LIKE CONCAT('%', pr.property_uid, '%')
            AND c.contract_status = 'ACTIVE'
            AND ({fn MONTHNAME(pu.next_payment)} = {fn MONTHNAME(now())} AND YEAR(pu.next_payment) = YEAR(now()))
            AND (prm.management_status <> 'REJECTED'  OR prm.management_status <> 'TERMINATED' OR prm.management_status <> 'EXPIRED')
            AND (pu.purchase_type = "MAINTENANCE" OR pu.purchase_type = 'REPAIRS' OR pu.purchase_type = "UTILITY" OR pu.purchase_type = "OWNER PAYMENT")
            AND (payer LIKE '%""" + filterValue + """%')""")
            print(manager_expected_expense)
            response['result']['manager_expected_expense'] = (list(
                manager_expected_expense['result']))

            if len(response['result']['manager_expected_expense']) > 0:
                for ore in range(len(response['result']['manager_expected_expense'])):
                    # number of months a property has been active
                    delta_active = relativedelta((datetime.strptime(
                        response['result']['manager_expected_expense'][ore]['active_date'], '%Y-%m-%d')), datetime.now())
                    months_active = abs(delta_active.months +
                                        (delta_active.years * 12))
                    # number of months a property has been under an active lease

                    # number of weeks in the current month
                    weeks_current_month = len(
                        calendar.monthcalendar(today.year, int(today.strftime("%m"))))

                    # if expenses type is MAINTAINENCE
                    if response['result']['manager_expected_expense'][ore]['purchase_type'] == 'MAINTENANCE':
                        # if maintenance monthly
                        if response['result']['manager_expected_expense'][ore]['purchase_frequency'] == 'Monthly':
                            # if maintenance monthly once a month
                            if response['result']['manager_expected_expense'][ore]['payment_frequency'] == 'Once a month' or response['result']['manager_expected_expense'][ore]['payment_frequency'] is None:

                                maintenance_expected_expense = maintenance_expected_expense + \
                                    response['result']['manager_expected_expense'][ore]['amount_due']

                                # if maintenance monthly twice a month
                            elif response['result']['manager_expected_expense'][ore]['payment_frequency'] == 'Twice a month':

                                maintenance_expected_expense = maintenance_expected_expense + 2 * \
                                    (response['result']['manager_expected_expense']
                                        [ore]['amount_due'])

                            else:
                                print('do nothing')
                            # if maintenance annually
                        elif response['result']['manager_expected_expense'][ore]['purchase_frequency'] == 'Annually':
                            # if maintenance annually once a year
                            if response['result']['manager_expected_expense'][ore]['payment_frequency'] == 'Once a year':
                                maintenance_expected_expense = maintenance_expected_expense + \
                                    (response['result']['manager_expected_expense']
                                        [ore]['amount_due'])

                                amortized_maintenance_expected_expense = amortized_maintenance_expected_expense + \
                                    (response['result']['manager_expected_expense']
                                        [ore]['amount_due'])/(datetime.now().month-1)

                            # if maintenance annually twice a year
                            elif response['result']['manager_expected_expense'][ore]['payment_frequency'] == 'Twice a year':
                                maintenance_expected_expense = maintenance_expected_expense + \
                                    (response['result']['manager_expected_expense']
                                        [ore]['amount_due'])
                                amortized_maintenance_expected_expense = amortized_maintenance_expected_expense + \
                                    (response['result']['manager_expected_expense']
                                        [ore]['amount_due'])/((datetime.now().month-1)/2)
                            else:
                                print('do nothing')
                        # if maintenance one-time
                        else:
                            maintenance_expected_expense = maintenance_expected_expense + \
                                response['result']['manager_expected_expense'][ore]['amount_due']

                    # if management
                    if response['result']['manager_expected_expense'][ore]['purchase_type'] == 'OWNER PAYMENT':
                        # if management monthly
                        if response['result']['manager_expected_expense'][ore]['purchase_frequency'] == 'Monthly':
                            print('here 1150', management_expected_expense)

                            management_expected_expense = management_expected_expense + response[
                                'result']['manager_expected_expense'][ore]['amount_due']

                            # if management annually
                        elif response['result']['manager_expected_expense'][ore]['purchase_frequency'] == 'Annually':
                            # if management annually once a year

                            management_expected_expense = management_expected_expense +  \
                                (response['result']['manager_expected_expense']
                                    [ore]['amount_due'])

                            amortized_management_expected_expense = amortized_management_expected_expense +  \
                                (response['result']['manager_expected_expense']
                                    [ore]['amount_due'])/(datetime.now().month-1)

                        # if management one-time
                        else:
                            management_expected_expense = management_expected_expense + \
                                response['result']['manager_expected_expense'][ore]['amount_due']

                    if response['result']['manager_expected_expense'][ore]['purchase_type'] == 'REPAIRS':
                        # if repairs monthly
                        if response['result']['manager_expected_expense'][ore]['purchase_frequency'] == 'Monthly':
                            # if repairs monthly once a month
                            if response['result']['manager_expected_expense'][ore]['payment_frequency'] == 'Once a month' or response['result']['manager_expected_expense'][ore]['payment_frequency'] is None:
                                repairs_expected_expense = repairs_expected_expense +  \
                                    (response['result']['manager_expected_expense']
                                        [ore]['amount_due'])

                                # if repairs monthly twice a month
                            elif response['result']['manager_expected_expense'][ore]['payment_frequency'] == 'Twice a month':
                                repairs_expected_expense = repairs_expected_expense + 2 * \
                                    (response['result']['manager_expected_expense']
                                        [ore]['amount_due'])

                            else:
                                print('do nothing')
                            # if repairs annually
                        elif response['result']['manager_expected_expense'][ore]['purchase_frequency'] == 'Annually':
                            # if repairs annually once a year
                            if response['result']['manager_expected_expense'][ore]['payment_frequency'] == 'Once a year':
                                repairs_expected_expense = repairs_expected_expense +  \
                                    (response['result']['manager_expected_expense']
                                        [ore]['amount_due'])

                                amortized_repairs_expected_expense = amortized_repairs_expected_expense +  \
                                    (response['result']['manager_expected_expense']
                                        [ore]['amount_due'])/(datetime.now().month-1)

                            # if repairs annually twice a year
                            elif response['result']['manager_expected_expense'][ore]['payment_frequency'] == 'Twice a year':
                                repairs_expected_expense = repairs_expected_expense + \
                                    (response['result']['manager_expected_expense']
                                        [ore]['amount_due'])

                                amortized_repairs_expected_expense = amortized_repairs_expected_expense +  \
                                    (response['result']['manager_expected_expense']
                                        [ore]['amount_due'])/((datetime.now().month-1)/2)

                            else:
                                print('do nothing')
                        # if repairs one-time
                        else:
                            repairs_expected_expense = repairs_expected_expense + \
                                response['result']['manager_expected_expense'][ore]['amount_due']
                    # if revenue type is UTILITY
                    if response['result']['manager_expected_expense'][ore]['purchase_type'] == 'UTILITY':
                        if response['result']['manager_expected_expense'][ore]['purchase_frequency'] == 'Weekly':
                            utility_expected_expense = utility_expected_expense + \
                                weeks_current_month*int(response['result']['manager_expected_expense']
                                                        [ore]['amount_due'])

                        elif response['result']['manager_expected_expense'][ore]['purchase_frequency'] == 'Biweekly':
                            utility_expected_expense = utility_expected_expense + \
                                weeks_current_month/2 * \
                                int(response['result']['manager_expected_expense']
                                    [ore]['amount_due'])

                        elif response['result']['manager_expected_expense'][ore]['purchase_frequency'] == 'Monthly':
                            utility_expected_expense = utility_expected_expense + \
                                response['result']['manager_expected_expense'][ore]['amount_due']

                        elif response['result']['manager_expected_expense'][ore]['purchase_frequency'] == 'Annually':
                            utility_expected_expense = utility_expected_expense + \
                                response['result']['manager_expected_expense'][ore]['amount_due']
                            amortized_utility_expected_revenue = amortized_utility_expected_revenue + \
                                int(response['result']['manager_expected_expense']
                                    [ore]['amount_due'])/12
                        else:
                            utility_expected_expense = utility_expected_expense + \
                                response['result']['manager_expected_expense'][ore]['amount_due']

            response['result']['maintenance_expected_expense'] = round(
                maintenance_expected_expense, 2)
            response['result']['management_expected_expense'] = round(
                management_expected_expense, 2)
            response['result']['repairs_expected_expense'] = round(
                repairs_expected_expense, 2)
            response['result']['utility_expected_expense'] = round(
                utility_expected_expense, 2)

            response['result']['amortized_maintenance_expected_expense'] = round(
                amortized_maintenance_expected_expense, 2)
            response['result']['amortized_management_expected_expense'] = round(
                amortized_management_expected_expense, 2)
            response['result']['amortized_repairs_expected_expense'] = round(
                amortized_repairs_expected_expense, 2)
            response['result']['amortized_utility_expected_expense'] = round(
                amortized_utility_expected_expense, 2)
            manager_expense_yearly = db.execute("""
            SELECT *
            FROM pm.purchases pu
            LEFT JOIN pm.payments pa
            ON pa.pay_purchase_id = pu.purchase_uid
            LEFT JOIN properties pr
            ON pu.pur_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN pm.propertyManager prm
            ON pr.property_uid = prm.linked_property_id
            LEFT JOIN pm.contracts c
            ON c.property_uid LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN pm.rentals r
            ON r.rental_property_id = pr.property_uid
            WHERE pu.pur_property_id LIKE CONCAT('%', pr.property_uid, '%')
            AND c.contract_status = 'ACTIVE'
            AND YEAR(pu.next_payment) = YEAR(now())
            AND (prm.management_status <> 'REJECTED'  OR prm.management_status <> 'TERMINATED' OR prm.management_status <> 'EXPIRED')
            AND (pu.purchase_type = "MAINTENANCE" OR pu.purchase_type = 'REPAIRS' OR pu.purchase_type = "UTILITY" OR pu.purchase_type = "OWNER PAYMENT" )
            AND (payer LIKE '%""" + filterValue + """%')""")
            print(manager_expense_yearly)
            response['result']['manager_expense_yearly'] = (list(
                manager_expense_yearly['result']))
            if len(manager_expense_yearly['result']) > 0:
                # number of weeks in the current month

                for mex in range(len(manager_expense_yearly['result'])):
                    # number of months a property has been active
                    delta_active = relativedelta((datetime.strptime(
                        response['result']['manager_expense_yearly'][mex]['start_date'], '%Y-%m-%d')), datetime.now())
                    months_active = abs(delta_active.months +
                                        (delta_active.years * 12))
                    # number of months a property has been under an active lease
                    print(response['result']['manager_expense_yearly'][mex])
                    delta_leased = relativedelta((datetime.strptime(
                        response['result']['manager_expense_yearly'][mex]['lease_start'], '%Y-%m-%d')), datetime.now())

                    months_leased = abs(delta_leased.months +
                                        (delta_leased.years * 12))
                    if months_leased == 0:
                        months_leased = 1
                    # number of weeks in the current month
                    weeks_current_month = len(
                        calendar.monthcalendar(today.year, int(today.strftime("%m"))))
                    # number of weeks a property has been active
                    weeks_active = round((abs(today - datetime.strptime(
                        response['result']['manager_expense_yearly'][mex]['start_date'], '%Y-%m-%d').date()).days)/7, 1)
                    # number of weeks a property has been under an active lease
                    weeks_leased = round((abs(today - datetime.strptime(
                        response['result']['manager_expense_yearly'][mex]['lease_start'], '%Y-%m-%d').date()).days)/7, 1)
                    # print('mex', manager_expense_yearly['result'][mex])
                    # if maintenance
                    if manager_expense_yearly['result'][mex]['purchase_type'] == 'MAINTENANCE':
                        # if maintenance monthly
                        # if maintenance monthly
                        if response['result']['manager_expense_yearly'][mex]['purchase_frequency'] == 'Monthly':
                            # if maintenance monthly once a month
                            if response['result']['manager_expense_yearly'][mex]['payment_frequency'] == 'Once a month' or response['result']['manager_expense_yearly'][mex]['payment_frequency'] is None:

                                maintenance_year_expense = maintenance_year_expense + \
                                    response['result']['manager_expense_yearly'][mex]['amount_paid']
                                # if maintenance monthly twice a month
                            elif response['result']['manager_expense_yearly'][mex]['payment_frequency'] == 'Twice a month':

                                maintenance_year_expense = maintenance_year_expense + \
                                    2 * \
                                    (response['result']['manager_expense_yearly']
                                        [mex]['amount_paid'])
                            else:
                                print('do nothing')
                            # if maintenance annually
                        elif response['result']['manager_expense_yearly'][mex]['purchase_frequency'] == 'Annually':
                            # if maintenance annually once a year
                            if response['result']['manager_expense_yearly'][mex]['payment_frequency'] == 'Once a year':

                                maintenance_year_expense = maintenance_year_expense + \
                                    response['result']['manager_expense_yearly'][mex]['amount_paid']

                                amortized_maintenance_year_expense = amortized_maintenance_year_expense + \
                                    (response['result']['manager_expense_yearly']
                                     [mex]['amount_paid'])/12
                            # if maintenance annually twice a year
                            elif response['result']['manager_expense_yearly'][mex]['payment_frequency'] == 'Twice a year':

                                maintenance_year_expense = maintenance_year_expense + \
                                    response['result']['manager_expense_yearly'][mex]['amount_paid']

                                amortized_maintenance_year_expense = amortized_maintenance_year_expense + \
                                    (response['result']['manager_expense_yearly']
                                     [mex]['amount_paid'])/6
                            else:
                                print('do nothing')
                        # if maintenance one-time
                        else:

                            maintenance_year_expense = maintenance_year_expense + \
                                response['result']['manager_expense_yearly'][mex]['amount_paid']

                    if manager_expense_yearly['result'][mex]['purchase_type'] == 'REPAIRS':
                        # if repairs monthly
                        if response['result']['manager_expense_yearly'][mex]['purchase_frequency'] == 'Monthly':
                            # if repairs monthly once a month
                            if response['result']['manager_expense_yearly'][mex]['payment_frequency'] == 'Once a month' or response['result']['manager_expense_yearly'][mex]['payment_frequency'] is None:

                                repairs_year_expense = repairs_year_expense + \
                                    response['result']['manager_expense_yearly'][mex]['amount_paid']
                                # if repairs monthly twice a month
                            elif response['result']['manager_expense_yearly'][mex]['payment_frequency'] == 'Twice a month':

                                repairs_year_expense = repairs_year_expense + \
                                    2 * \
                                    (response['result']['manager_expense_yearly']
                                        [mex]['amount_paid'])
                            else:
                                print('do nothing')
                            # if repairs annually
                        elif response['result']['manager_expense_yearly'][mex]['purchase_frequency'] == 'Annually':
                            # if repairs annually once a year
                            if response['result']['manager_expense_yearly'][mex]['payment_frequency'] == 'Once a year':

                                repairs_year_expense = repairs_year_expense + \
                                    response['result']['manager_expense_yearly'][mex]['amount_paid']

                                amortized_repairs_year_expense = amortized_repairs_year_expense + \
                                    float(
                                        response['result']['manager_expense_yearly'][mex]['amount_paid'])/12
                            # if repairs annually twice a year
                            elif response['result']['manager_expense_yearly'][mex]['payment_frequency'] == 'Twice a year':

                                repairs_year_expense = repairs_year_expense + \
                                    response['result']['manager_expense_yearly'][mex]['amount_paid']

                                amortized_repairs_year_expense = amortized_repairs_year_expense + \
                                    float(
                                        response['result']['manager_expense_yearly'][mex]['amount_paid'])/6
                            else:
                                print('do nothing')
                        # if repairs one-time
                        else:

                            repairs_year_expense = repairs_year_expense + \
                                response['result']['manager_expense_yearly'][mex]['amount_paid']

                    if manager_expense_yearly['result'][mex]['purchase_type'] == 'UTILITY':
                        if manager_expense_yearly['result'][mex]['purchase_frequency'] == 'Weekly':

                            utility_year_expense = utility_year_expense + \
                                float(manager_expense_yearly['result']
                                      [mex]['amount_paid'])
                        elif manager_expense_yearly['result'][mex]['purchase_frequency'] == 'Biweekly':

                            utility_year_expense = utility_year_expense + \
                                float(manager_expense_yearly['result']
                                      [mex]['amount_paid'])
                        elif manager_expense_yearly['result'][mex]['purchase_frequency'] == 'Monthly':

                            utility_year_expense = utility_year_expense + \
                                manager_expense_yearly['result'][mex]['amount_paid']
                        elif manager_expense_yearly['result'][mex]['purchase_frequency'] == 'Annually':

                            utility_year_expense = utility_year_expense + \
                                manager_expense_yearly['result'][mex]['amount_paid']
                            amortized_utility_year_expense = amortized_utility_year_expense + \
                                (response['result']['manager_expense_yearly']
                                 [mex]['amount_paid'])/12
                        else:

                            utility_year_expense = utility_year_expense + \
                                manager_expense_yearly['result'][mex]['amount_paid']
                    if manager_expense_yearly['result'][mex]['purchase_type'] == 'OWNER PAYMENT':
                        if manager_expense_yearly['result'][mex]['purchase_frequency'] == 'Weekly':

                            management_year_expense = management_year_expense + \
                                float(manager_expense_yearly['result']
                                      [mex]['amount_paid'])
                        elif manager_expense_yearly['result'][mex]['purchase_frequency'] == 'Biweekly':

                            management_year_expense = management_year_expense + \
                                float(manager_expense_yearly['result']
                                      [mex]['amount_paid'])
                        elif manager_expense_yearly['result'][mex]['purchase_frequency'] == 'Monthly':

                            management_year_expense = management_year_expense + \
                                manager_expense_yearly['result'][mex]['amount_paid']

                        elif manager_expense_yearly['result'][mex]['purchase_frequency'] == 'Annually':

                            management_year_expense = management_year_expense + \
                                manager_expense_yearly['result'][mex]['amount_paid']
                            amortized_management_year_expense = amortized_management_year_expense + \
                                (response['result']['manager_expense_yearly']
                                 [mex]['amount_paid'])/12
                        else:

                            management_year_expense = management_year_expense + \
                                manager_expense_yearly['result'][mex]['amount_paid']

            response['result']['maintenance_year_expense'] = round(
                maintenance_year_expense, 2)
            response['result']['repairs_year_expense'] = round(
                repairs_year_expense, 2)
            response['result']['utility_year_expense'] = round(
                utility_year_expense, 2)
            response['result']['management_year_expense'] = round(
                management_year_expense, 2)
            response['result']['amortized_maintenance_year_expense'] = round(
                amortized_maintenance_year_expense, 2)
            response['result']['amortized_repairs_year_expense'] = round(
                amortized_repairs_year_expense, 2)
            response['result']['amortized_utility_year_expense'] = round(
                amortized_utility_year_expense, 2)
            response['result']['amortized_management_year_expense'] = round(
                amortized_management_year_expense, 2)

            manager_expected_year_expense = db.execute("""
            SELECT *
            FROM pm.purchases pu
            LEFT JOIN pm.payments pa
            ON pa.pay_purchase_id = pu.purchase_uid
            LEFT JOIN properties pr
            ON pu.pur_property_id LIKE CONCAT('%', pr.property_uid, '%')
            LEFT JOIN pm.propertyManager prm
            ON pr.property_uid = prm.linked_property_id
            LEFT JOIN pm.contracts c
            ON c.property_uid LIKE CONCAT('%', pr.property_uid, '%')
            WHERE pu.pur_property_id LIKE CONCAT('%', pr.property_uid, '%')
            AND c.contract_status = 'ACTIVE'
            AND YEAR(pu.next_payment) = YEAR(now())
            AND (prm.management_status <> 'REJECTED'  OR prm.management_status <> 'TERMINATED' OR prm.management_status <> 'EXPIRED')
            AND (pu.purchase_type = "MAINTENANCE" OR pu.purchase_type = 'REPAIRS' OR pu.purchase_type = "UTILITY" OR pu.purchase_type = "OWNER PAYMENT")
            AND (payer LIKE '%""" + filterValue + """%')""")
            print(manager_expected_year_expense)
            response['result']['manager_expected_year_expense'] = (list(
                manager_expected_year_expense['result']))

            if len(response['result']['manager_expected_year_expense']) > 0:
                for ore in range(len(response['result']['manager_expected_year_expense'])):
                    # number of months a property has been active
                    delta_active = relativedelta((datetime.strptime(
                        response['result']['manager_expected_year_expense'][ore]['active_date'], '%Y-%m-%d')), datetime.now())
                    months_active = abs(delta_active.months +
                                        (delta_active.years * 12))
                    # number of months a property has been under an active lease

                    # number of weeks in the current month
                    weeks_current_month = len(
                        calendar.monthcalendar(today.year, int(today.strftime("%m"))))

                    # if expenses type is MAINTAINENCE
                    if response['result']['manager_expected_year_expense'][ore]['purchase_type'] == 'MAINTENANCE':
                        # if maintenance monthly
                        if response['result']['manager_expected_year_expense'][ore]['purchase_frequency'] == 'Monthly':
                            # if maintenance monthly once a month
                            if response['result']['manager_expected_year_expense'][ore]['payment_frequency'] == 'Once a month' or response['result']['manager_expected_year_expense'][ore]['payment_frequency'] is None:

                                maintenance_year_expected_expense = maintenance_year_expected_expense + \
                                    response['result']['manager_expected_year_expense'][ore]['amount_due']

                                # if maintenance monthly twice a month
                            elif response['result']['manager_expected_year_expense'][ore]['payment_frequency'] == 'Twice a month':

                                maintenance_year_expected_expense = maintenance_year_expected_expense + 2 * \
                                    (response['result']['manager_expected_year_expense']
                                        [ore]['amount_due'])

                            else:
                                print('do nothing')
                            # if maintenance annually
                        elif response['result']['manager_expected_year_expense'][ore]['purchase_frequency'] == 'Annually':
                            # if maintenance annually once a year
                            if response['result']['manager_expected_year_expense'][ore]['payment_frequency'] == 'Once a year':
                                maintenance_year_expected_expense = maintenance_year_expected_expense + \
                                    (response['result']['manager_expected_year_expense']
                                        [ore]['amount_due'])

                                amortized_maintenance_year_expected_expense = amortized_maintenance_year_expected_expense + \
                                    (response['result']['manager_expected_year_expense']
                                        [ore]['amount_due'])/(datetime.now().month-1)

                            # if maintenance annually twice a year
                            elif response['result']['manager_expected_year_expense'][ore]['payment_frequency'] == 'Twice a year':
                                maintenance_year_expected_expense = maintenance_year_expected_expense + \
                                    (response['result']['manager_expected_year_expense']
                                        [ore]['amount_due'])
                                amortized_maintenance_year_expected_expense = amortized_maintenance_year_expected_expense + \
                                    (response['result']['manager_expected_year_expense']
                                        [ore]['amount_due'])/((datetime.now().month-1)/2)
                            else:
                                print('do nothing')
                        # if maintenance one-time
                        else:
                            maintenance_year_expected_expense = maintenance_year_expected_expense + \
                                response['result']['manager_expected_year_expense'][ore]['amount_due']

                    # if management
                    if response['result']['manager_expected_year_expense'][ore]['purchase_type'] == 'OWNER PAYMENT':
                        # if management monthly
                        if response['result']['manager_expected_year_expense'][ore]['purchase_frequency'] == 'Monthly':
                            management_year_expected_expense = management_year_expected_expense + response[
                                'result']['manager_expected_year_expense'][ore]['amount_due']

                            # if management annually
                        elif response['result']['manager_expected_year_expense'][ore]['purchase_frequency'] == 'Annually':
                            # if management annually once a year

                            management_year_expected_expense = management_year_expected_expense +  \
                                (response['result']['manager_expected_year_expense']
                                    [ore]['amount_due'])

                            amortized_management_year_expected_expense = amortized_management_year_expected_expense +  \
                                (response['result']['manager_expected_year_expense']
                                    [ore]['amount_due'])/(datetime.now().month-1)

                        # if management one-time
                        else:
                            management_year_expected_expense = management_year_expected_expense + \
                                response['result']['manager_expected_year_expense'][ore]['amount_due']

                    if response['result']['manager_expected_year_expense'][ore]['purchase_type'] == 'REPAIRS':
                        # if repairs monthly
                        if response['result']['manager_expected_year_expense'][ore]['purchase_frequency'] == 'Monthly':
                            # if repairs monthly once a month
                            if response['result']['manager_expected_year_expense'][ore]['payment_frequency'] == 'Once a month' or response['result']['manager_expected_year_expense'][ore]['payment_frequency'] is None:
                                repairs_year_expected_expense = repairs_year_expected_expense +  \
                                    (response['result']['manager_expected_year_expense']
                                        [ore]['amount_due'])

                                # if repairs monthly twice a month
                            elif response['result']['manager_expected_year_expense'][ore]['payment_frequency'] == 'Twice a month':
                                repairs_year_expected_expense = repairs_year_expected_expense + 2 * \
                                    (response['result']['manager_expected_year_expense']
                                        [ore]['amount_due'])

                            else:
                                print('do nothing')
                            # if repairs annually
                        elif response['result']['manager_expected_year_expense'][ore]['purchase_frequency'] == 'Annually':
                            # if repairs annually once a year
                            if response['result']['manager_expected_year_expense'][ore]['payment_frequency'] == 'Once a year':
                                repairs_year_expected_expense = repairs_year_expected_expense +  \
                                    (response['result']['manager_expected_year_expense']
                                        [ore]['amount_due'])

                                amortized_repairs_year_expected_expense = amortized_repairs_year_expected_expense +  \
                                    (response['result']['manager_expected_year_expense']
                                        [ore]['amount_due'])/(datetime.now().month-1)

                            # if repairs annually twice a year
                            elif response['result']['manager_expected_year_expense'][ore]['payment_frequency'] == 'Twice a year':
                                repairs_year_expected_expense = repairs_year_expected_expense + \
                                    (response['result']['manager_expected_year_expense']
                                        [ore]['amount_due'])

                                amortized_repairs_year_expected_expense = amortized_repairs_year_expected_expense +  \
                                    (response['result']['manager_expected_year_expense']
                                        [ore]['amount_due'])/((datetime.now().month-1)/2)

                            else:
                                print('do nothing')
                        # if repairs one-time
                        else:
                            repairs_year_expected_expense = repairs_year_expected_expense + \
                                response['result']['manager_expected_year_expense'][ore]['amount_due']
                    if response['result']['manager_expected_year_expense'][ore]['purchase_type'] == 'UTILITY':
                        if response['result']['manager_expected_year_expense'][ore]['purchase_frequency'] == 'Weekly':
                            utility_year_expected_expense = utility_year_expected_expense + \
                                weeks_leased*int(response['result']['manager_expected_year_expense']
                                                         [ore]['amount_due'])

                        elif response['result']['manager_expected_year_expense'][ore]['purchase_frequency'] == 'Biweekly':
                            utility_year_expected_expense = utility_year_expected_expense + \
                                weeks_leased/2 * \
                                int(response['result']['manager_expected_year_expense']
                                    [ore]['amount_due'])

                        elif response['result']['manager_expected_year_expense'][ore]['purchase_frequency'] == 'Monthly':
                            utility_year_expected_expense = utility_year_expected_expense + \
                                months_leased * \
                                int(response['result']
                                    ['manager_expected_year_expense'][ore]['amount_due'])

                        elif response['result']['manager_expected_year_expense'][ore]['purchase_frequency'] == 'Annually':
                            utility_year_expected_expense = utility_year_expected_expense + \
                                response['result']['manager_expected_year_expense'][ore]['amount_due']

                            amortized_utility_year_expected_expense = amortized_utility_year_expected_expense + \
                                int(response['result']['manager_expected_year_expense']
                                    [ore]['amount_due'])/12
                            amortized_utility_year_revenue = amortized_utility_year_revenue + \
                                int(response['result']['manager_expected_year_expense']
                                    [ore]['amount_paid'])/12
                        else:
                            utility_year_expected_expense = utility_year_expected_expense + \
                                response['result']['manager_expected_year_expense'][ore]['amount_due']

            response['result']['maintenance_year_expected_expense'] = round(
                maintenance_year_expected_expense, 2)
            response['result']['management_year_expected_expense'] = round(
                management_year_expected_expense, 2)
            response['result']['repairs_year_expected_expense'] = round(
                repairs_year_expected_expense, 2)
            response['result']['utility_year_expected_expense'] = round(
                utility_year_expected_expense, 2)

            response['result']['amortized_maintenance_year_expected_expense'] = round(
                amortized_maintenance_year_expected_expense, 2)
            response['result']['amortized_management_year_expected_expense'] = round(
                amortized_management_year_expected_expense, 2)
            response['result']['amortized_repairs_year_expected_expense'] = round(
                amortized_repairs_year_expected_expense, 2)
            response['result']['amortized_utility_year_expected_expense'] = round(
                amortized_utility_year_expected_expense, 2)
        return response
