from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from data import connect, uploadImage
import boto3
import json
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import calendar


class CashflowOwner(Resource):
    def get(self):
        response = {}
        response['message'] = 'Successfully executed SQL query'
        response['code'] = 200
        response['result'] = {}
        filters = ['owner_id', 'year']
        where = {}

        with connect() as db:
            filterValue = request.args.get(filters[0])
            year = request.args.get(filters[1])
            print(filterValue)
            print(year)
            today = date.today()
            response_revenue = db.execute("""
                SELECT prop.owner_id, prop.property_uid, address, unit, city,
                state, zip, 
                pur.*, 
                DATE_FORMAT(next_payment, "%M") AS month, 
                DATE_FORMAT(next_payment, "%Y") AS year
                FROM pm.properties prop
                LEFT JOIN pm.purchases pur
                ON pur_property_id LIKE CONCAT ('%',prop.property_uid, '%')
                WHERE pur.receiver = \'""" + filterValue + """\'                
                AND (YEAR(pur.next_payment) = \'""" + year + """\');""")

            # -- FOR AN OWNER, WHAT PROPERTIES DOES HE OWN, AND WHAT RENTS WERE COLLECTED
            response_rental_revenue = db.execute("""    
                SELECT prop.owner_id, prop.property_uid, address, unit, city, state, zip, 
                pur.*, DATE_FORMAT(next_payment, "%M") AS month, DATE_FORMAT(next_payment, "%Y") AS year
                FROM pm.properties prop
                LEFT JOIN pm.purchases pur
                ON pur_property_id LIKE CONCAT ('%',prop.property_uid, '%')
                WHERE owner_id =  \'""" + filterValue + """\'
                AND purchase_type = "RENT"
                AND (YEAR(pur.next_payment) = \'""" + year + """\');
                """)
            # -- FOR AN OWNER, WHAT PROPERTIES DOES HE OWN, AND WHAT RENTS WERE COLLECTED
            response_extra_revenue = db.execute("""    
                SELECT prop.owner_id, prop.property_uid, address, unit, city, state, zip, 
                pur.*, DATE_FORMAT(next_payment, "%M") AS month, DATE_FORMAT(next_payment, "%Y") AS year
                FROM pm.properties prop
                LEFT JOIN pm.purchases pur
                ON pur_property_id LIKE CONCAT ('%',prop.property_uid, '%')
                WHERE owner_id =  \'""" + filterValue + """\'
                AND purchase_type = "EXTRA CHARGES"
                AND (YEAR(pur.next_payment) = \'""" + year + """\');
                """)
            # -- FOR AN OWNER, WHAT PROPERTIES DOES HE OWN, AND WHAT RENTS WERE COLLECTED
            response_deposit_revenue = db.execute("""
                SELECT prop.owner_id, prop.property_uid, address, unit, city, state, zip,
                pur.*, DATE_FORMAT(next_payment, "%M") AS month, DATE_FORMAT(next_payment, "%Y") AS year
                FROM pm.properties prop
                LEFT JOIN pm.purchases pur
                ON pur_property_id LIKE CONCAT ('%',prop.property_uid, '%')
                WHERE owner_id =  \'""" + filterValue + """\'
                AND purchase_type = "DEPOSIT"
                AND (YEAR(pur.next_payment) = \'""" + year + """\'); 
                """)
            # -- FOR AN OWNER, WHAT PROPERTIES DOES HE OWN, AND WHAT RENTS WERE COLLECTED
            response_late_fee_revenue = db.execute("""    
                SELECT prop.owner_id, prop.property_uid, address, unit, city, state, zip, 
                pur.*, DATE_FORMAT(next_payment, "%M") AS month, DATE_FORMAT(next_payment, "%Y") AS year
                FROM pm.properties prop
                LEFT JOIN pm.purchases pur
                ON pur_property_id LIKE CONCAT ('%',prop.property_uid, '%')
                WHERE owner_id =  \'""" + filterValue + """\'
                AND purchase_type = "LATE FEE"
                AND (YEAR(pur.next_payment) = \'""" + year + """\');
                """)
            # revenue summary
            response_revenue_summary = db.execute("""
                SELECT owner_id, purchase_type, month, year, ROUND(SUM(amount_due), 2) AS amount_due ,ROUND(SUM(amount_paid),2) AS amount_paid FROM (
                    SELECT prop.owner_id, prop.property_uid, address, unit, city,
                    state, zip, 
                    pur.*, 
                    DATE_FORMAT(next_payment, "%M") AS month, 
                    DATE_FORMAT(next_payment, "%Y") AS year
                    FROM pm.properties prop
                    LEFT JOIN pm.purchases pur
                    ON pur_property_id LIKE CONCAT ('%',prop.property_uid, '%')
                    WHERE pur.receiver = \'""" + filterValue + """\' 
                    AND (YEAR(pur.next_payment) = \'""" + year + """\')) AS pp
                GROUP BY pp.purchase_type,pp.month, pp.year;""")
            response_rental_revenue_summary = db.execute("""
                SELECT owner_id, purchase_type, month, year, ROUND(SUM(amount_due), 2) AS amount_due ,ROUND(SUM(amount_paid),2) AS amount_paid FROM (
                    SELECT prop.owner_id, prop.property_uid, address, unit, city,
                    state, zip, 
                    pur.*, 
                    DATE_FORMAT(next_payment, "%M") AS month, 
                    DATE_FORMAT(next_payment, "%Y") AS year
                    FROM pm.properties prop
                    LEFT JOIN pm.purchases pur
                    ON pur_property_id LIKE CONCAT ('%',prop.property_uid, '%')
                    WHERE owner_id =  \'""" + filterValue + """\'
                    AND purchase_type = "RENT"
                    AND (YEAR(pur.next_payment) = \'""" + year + """\')) AS pp
                GROUP BY pp.purchase_type,pp.month, pp.year;""")

            response_extra_revenue_summary = db.execute("""
                SELECT owner_id, purchase_type, month, year, ROUND(SUM(amount_due), 2) AS amount_due ,ROUND(SUM(amount_paid),2) AS amount_paid FROM (
                    SELECT prop.owner_id, prop.property_uid, address, unit, city,
                    state, zip,
                    pur.*,
                    DATE_FORMAT(next_payment, "%M") AS month,
                    DATE_FORMAT(next_payment, "%Y") AS year
                    FROM pm.properties prop
                    LEFT JOIN pm.purchases pur
                    ON pur_property_id LIKE CONCAT ('%',prop.property_uid, '%')
                    WHERE owner_id =  \'""" + filterValue + """\'
                    AND purchase_type = "EXTRA CHARGES"
                    AND (YEAR(pur.next_payment) = \'""" + year + """\')) AS pp
                GROUP BY pp.purchase_type,pp.month, pp.year;""")
            response_deposit_revenue_summary = db.execute("""
                SELECT owner_id, purchase_type, month, year, ROUND(SUM(amount_due), 2) AS amount_due ,ROUND(SUM(amount_paid),2) AS amount_paid FROM (
                    SELECT prop.owner_id, prop.property_uid, address, unit, city,
                    state, zip,
                    pur.*,
                    DATE_FORMAT(next_payment, "%M") AS month,
                    DATE_FORMAT(next_payment, "%Y") AS year
                    FROM pm.properties prop
                    LEFT JOIN pm.purchases pur
                    ON pur_property_id LIKE CONCAT ('%',prop.property_uid, '%')
                    WHERE owner_id =  \'""" + filterValue + """\'
                    AND purchase_type = 'DEPOSIT'
                    AND (YEAR(pur.next_payment) = \'""" + year + """\')) AS pp
                GROUP BY pp.purchase_type,pp.month, pp.year;""")
            response_late_fee_revenue_summary = db.execute("""
                SELECT owner_id, purchase_type, month, year, ROUND(SUM(amount_due), 2) AS amount_due ,ROUND(SUM(amount_paid),2) AS amount_paid FROM (
                    SELECT prop.owner_id, prop.property_uid, address, unit, city,
                    state, zip,
                    pur.*,
                    DATE_FORMAT(next_payment, "%M") AS month,
                    DATE_FORMAT(next_payment, "%Y") AS year
                    FROM pm.properties prop
                    LEFT JOIN pm.purchases pur
                    ON pur_property_id LIKE CONCAT ('%',prop.property_uid, '%')
                    WHERE owner_id =  \'""" + filterValue + """\'
                    AND purchase_type = "LATE FEE"
                    AND (YEAR(pur.next_payment) = \'""" + year + """\')) AS pp
                GROUP BY pp.purchase_type,pp.month, pp.year;""")
            # revenue by unit
            response_revenue_unit = db.execute("""
            SELECT owner_id, purchase_type, receiver, property_uid, month, year, ROUND(SUM(amount_due), 2) AS amount_due,ROUND(SUM(amount_paid),2) AS amount_paid 
                FROM (
                -- OWNER REVENUE FILTERED BY MONTH AND YEAR
                SELECT prop.owner_id, prop.property_uid, address, unit, city, state, zip,  
                pur.*,
                DATE_FORMAT(next_payment, "%M") AS month, 
                DATE_FORMAT(next_payment, "%Y") AS year
                FROM pm.properties prop
                LEFT JOIN pm.purchases pur
                ON pur_property_id LIKE CONCAT ('%',prop.property_uid, '%')
                WHERE pur.receiver = \'""" + filterValue + """\' 
                AND (YEAR(pur.next_payment) = \'""" + year + """\')) AS pp
                GROUP BY pp.property_uid,pp.purchase_type,pp.month, pp.year;""")

            response_rental_revenue_unit = db.execute("""
            SELECT owner_id,purchase_type, receiver, property_uid, month, year, ROUND(SUM(amount_due), 2) AS amount_due,ROUND(SUM(amount_paid),2) AS amount_paid 
                FROM (
                -- OWNER REVENUE FILTERED BY MONTH AND YEAR
                SELECT prop.owner_id, prop.property_uid, address, unit, city, state, zip,  
                pur.*,
                DATE_FORMAT(next_payment, "%M") AS month, 
                DATE_FORMAT(next_payment, "%Y") AS year
                FROM pm.properties prop
                LEFT JOIN pm.purchases pur
                ON pur_property_id LIKE CONCAT ('%',prop.property_uid, '%')
                WHERE owner_id =  \'""" + filterValue + """\'
                AND purchase_type = "RENT" 
                AND (YEAR(pur.next_payment) = \'""" + year + """\')) AS pp
                GROUP BY pp.property_uid,pp.purchase_type,pp.month, pp.year;""")
            response_exta_revenue_unit = db.execute("""
            SELECT owner_id,purchase_type, receiver, property_uid, month, year, ROUND(SUM(amount_due), 2) AS amount_due,ROUND(SUM(amount_paid),2) AS amount_paid 
                FROM (
                -- OWNER REVENUE FILTERED BY MONTH AND YEAR
                SELECT prop.owner_id, prop.property_uid, address, unit, city, state, zip,  
                pur.*,
                DATE_FORMAT(next_payment, "%M") AS month, 
                DATE_FORMAT(next_payment, "%Y") AS year
                FROM pm.properties prop
                LEFT JOIN pm.purchases pur
                ON pur_property_id LIKE CONCAT ('%',prop.property_uid, '%')
                WHERE owner_id =  \'""" + filterValue + """\'
                AND purchase_type = "EXTRA CHARGES"
                AND (YEAR(pur.next_payment) = \'""" + year + """\')) AS pp
                GROUP BY pp.property_uid,pp.purchase_type,pp.month, pp.year;""")
            response_deposit_revenue_unit = db.execute("""
            SELECT owner_id,purchase_type, receiver, property_uid, month, year, ROUND(SUM(amount_due), 2) AS amount_due,ROUND(SUM(amount_paid),2) AS amount_paid 
                FROM (
                -- OWNER REVENUE FILTERED BY MONTH AND YEAR
                SELECT prop.owner_id, prop.property_uid, address, unit, city, state, zip,  
                pur.*,
                DATE_FORMAT(next_payment, "%M") AS month, 
                DATE_FORMAT(next_payment, "%Y") AS year
                FROM pm.properties prop
                LEFT JOIN pm.purchases pur
                ON pur_property_id LIKE CONCAT ('%',prop.property_uid, '%')
                WHERE owner_id =  \'""" + filterValue + """\'
                AND purchase_type = "DEPOSIT"
                AND (YEAR(pur.next_payment) = \'""" + year + """\')) AS pp
                GROUP BY pp.property_uid,pp.purchase_type,pp.month, pp.year;""")
            response_late_fee_revenue_unit = db.execute("""
            SELECT owner_id,purchase_type, receiver, property_uid, month, year, ROUND(SUM(amount_due), 2) AS amount_due,ROUND(SUM(amount_paid),2) AS amount_paid 
                FROM (
                -- OWNER REVENUE FILTERED BY MONTH AND YEAR
                SELECT prop.owner_id, prop.property_uid, address, unit, city, state, zip,  
                pur.*,
                DATE_FORMAT(next_payment, "%M") AS month, 
                DATE_FORMAT(next_payment, "%Y") AS year
                FROM pm.properties prop
                LEFT JOIN pm.purchases pur
                ON pur_property_id LIKE CONCAT ('%',prop.property_uid, '%')
                WHERE owner_id =  \'""" + filterValue + """\'
                AND purchase_type = "LATE FEE" 
                AND (YEAR(pur.next_payment) = \'""" + year + """\')) AS pp
                GROUP BY pp.property_uid,pp.purchase_type,pp.month, pp.year;""")
            response['result']['revenue'] = list(
                response_revenue['result']) + list(response_rental_revenue['result']) + list(response_extra_revenue['result']) + list(response_late_fee_revenue['result']) + list(response_deposit_revenue)
            response['result']['revenue_summary'] = list(
                response_revenue_summary['result']) + list(response_rental_revenue_summary['result']) + list(response_extra_revenue_summary['result']) + list(response_deposit_revenue_summary['result']) + list(response_late_fee_revenue_summary['result'])
            response['result']['revenue_unit'] = list(
                response_revenue_unit['result']) + list(response_rental_revenue_unit['result']) + list(
                response_exta_revenue_unit['result']) + list(response_late_fee_revenue_unit['result']) + list(response_deposit_revenue_unit['result'])
            # expense
            response_expense = db.execute("""
                SELECT owner_id, prop.property_uid, address, unit, city,
                state, zip, 
                pur.*,
                DATE_FORMAT(next_payment, "%M") AS month,
                DATE_FORMAT(next_payment, "%Y") AS year
                FROM pm.properties prop
                LEFT JOIN pm.purchases pur
                ON pur_property_id LIKE CONCAT ('%',prop.property_uid, '%')
                WHERE payer LIKE '%""" + filterValue + """%'
                AND (YEAR(pur.next_payment) = \'""" + year + """\');""")
            print(response_expense)
            # expense summary
            response_expense_summary = db.execute("""
                SELECT owner_id, purchase_type, month, year, ROUND(SUM(amount_due), 2) AS amount_due,ROUND(SUM(amount_paid),2) AS amount_paid FROM (
                    SELECT prop.owner_id, prop.property_uid, address, unit, city,
                    state, zip, 
                    pur.*, 
                    DATE_FORMAT(next_payment, "%M") AS month, 
                    DATE_FORMAT(next_payment, "%Y") AS year
                    FROM pm.properties prop
                    LEFT JOIN pm.purchases pur
                    ON pur_property_id LIKE CONCAT ('%',prop.property_uid, '%')
                    WHERE payer LIKE '%""" + filterValue + """%'                    
                AND (YEAR(pur.next_payment) = \'""" + year + """\')) AS pp
                GROUP BY pp.purchase_type,pp.month, pp.year;""")
            print(response_expense_summary)
            # expense by unit
            response_expense_unit = db.execute("""
            SELECT owner_id,purchase_type, receiver, property_uid, month, year, ROUND(SUM(amount_due), 2) AS amount_due,ROUND(SUM(amount_paid),2) AS amount_paid 
                FROM (
                -- OWNER REVENUE FILTERED BY MONTH AND YEAR
                SELECT prop.owner_id, prop.property_uid, address, unit, city, state, zip,  pur.*, DATE_FORMAT(next_payment, "%M") AS month, DATE_FORMAT(next_payment, "%Y") AS year
                FROM pm.properties prop
                LEFT JOIN pm.purchases pur
                ON pur_property_id LIKE CONCAT ('%',prop.property_uid, '%')
                WHERE payer LIKE '%""" + filterValue + """%'
                AND (YEAR(pur.next_payment) = \'""" + year + """\')) AS pp
                GROUP BY pp.property_uid,pp.purchase_type,pp.month, pp.year;""")
            print(response_expense_unit)
            response['result']['expense_summary'] = list(
                response_expense_summary['result'])
            response['result']['expense'] = list(response_expense['result'])
            response['result']['expense_unit'] = list(
                response_expense_unit['result'])
        return response
