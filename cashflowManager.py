from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from data import connect, uploadImage
import boto3
import json
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import calendar


class CashflowManager(Resource):
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
            # revenue
            response_revenue = db.execute("""
                SELECT prop.owner_id, prop.property_uid, address, unit, city,
                state, zip, 
                pur.*, 
                DATE_FORMAT(next_payment, "%M") AS month, 
                DATE_FORMAT(next_payment, "%Y") AS year
                FROM pm.properties prop
                LEFT JOIN pm.purchases pur
                ON pur_property_id LIKE CONCAT ('%',prop.property_uid, '%')
                LEFT JOIN pm.propertyManager pr
                ON pr.linked_property_id = prop.property_uid
                LEFT JOIN pm.contracts c
                ON c.property_uid LIKE CONCAT('%', prop.property_uid, '%')
                WHERE receiver = \'""" + filterValue + """\'
                AND c.contract_status = 'ACTIVE'
                AND (pr.management_status <> 'REJECTED'  OR pr.management_status <> 'TERMINATED' OR pr.management_status <> 'EXPIRED');""")

            # revenue summary
            response_revenue_summary = db.execute("""
                SELECT owner_id, purchase_type, month, year, Sum(amount_due) AS amount_due,Sum(amount_paid) AS amount_paid FROM (
                    SELECT prop.owner_id, prop.property_uid, address, unit, city,
                    state, zip, 
                    pur.*, 
                    DATE_FORMAT(next_payment, "%M") AS month, 
                    DATE_FORMAT(next_payment, "%Y") AS year
                    FROM pm.properties prop
                    LEFT JOIN pm.purchases pur
                    ON pur_property_id LIKE CONCAT ('%',prop.property_uid, '%')
                    LEFT JOIN pm.propertyManager pr
                    ON pr.linked_property_id = prop.property_uid
                    LEFT JOIN pm.contracts c
                    ON c.property_uid LIKE CONCAT('%', prop.property_uid, '%')
                    WHERE receiver = \'""" + filterValue + """\'
                    AND c.contract_status = 'ACTIVE'
                    AND (pr.management_status <> 'REJECTED'  OR pr.management_status <> 'TERMINATED' OR pr.management_status <> 'EXPIRED')) AS pp
                GROUP BY pp.purchase_type,pp.month, pp.year;""")

            response['result']['revenue'] = list(response_revenue['result'])
            response['result']['revenue_summary'] = list(
                response_revenue_summary['result'])
            # expense
            response_expense = db.execute("""
                SELECT prop.owner_id, prop.property_uid, address, unit, city,
                state, zip, 
                pur.*,
                DATE_FORMAT(next_payment, "%M") AS month,
                DATE_FORMAT(next_payment, "%Y") AS year
                FROM pm.properties prop
                LEFT JOIN pm.purchases pur
                ON pur_property_id LIKE CONCAT ('%',prop.property_uid, '%')
                LEFT JOIN pm.propertyManager pr
                ON pr.linked_property_id = prop.property_uid
                LEFT JOIN pm.contracts c
                ON c.property_uid LIKE CONCAT('%', prop.property_uid, '%')
                WHERE payer LIKE '%""" + filterValue + """%'
                AND c.contract_status = 'ACTIVE'
                AND (pr.management_status <> 'REJECTED'  OR pr.management_status <> 'TERMINATED' OR pr.management_status <> 'EXPIRED');""")
            # expense summary
            response_expense_summary = db.execute("""
                SELECT owner_id, purchase_type, month, year, Sum(amount_due) AS amount_due,Sum(amount_paid) AS amount_paid FROM (
                    SELECT prop.owner_id, prop.property_uid, address, unit, city,
                    state, zip, 
                    pur.*, 
                    DATE_FORMAT(next_payment, "%M") AS month, 
                    DATE_FORMAT(next_payment, "%Y") AS year
                    FROM pm.properties prop
                    LEFT JOIN pm.purchases pur
                    ON pur_property_id LIKE CONCAT ('%',prop.property_uid, '%')
                    LEFT JOIN pm.propertyManager pr
                    ON pr.linked_property_id = prop.property_uid
                    LEFT JOIN pm.contracts c
                    ON c.property_uid LIKE CONCAT('%', prop.property_uid, '%')
                    WHERE payer LIKE '%""" + filterValue + """%'
                    AND c.contract_status = 'ACTIVE'
                    AND (pr.management_status <> 'REJECTED'  OR pr.management_status <> 'TERMINATED' OR pr.management_status <> 'EXPIRED')) AS pp
                GROUP BY pp.purchase_type,pp.month, pp.year;""")
            response['result']['expense_summary'] = list(
                response_expense_summary['result'])
            response['result']['expense'] = list(response_expense['result'])
        return response
