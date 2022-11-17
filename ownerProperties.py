
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
                        response['result'][i]['rent_paid'] = ''
                        if len(rental_res['result']) > 0:

                            response['result'][i]['rental_status'] = rental_res['result'][0]['rental_status']
                            if len(rental_res['result'][0]['tenant_id'].split(',')) > 0:
                                print('in if')
                                for r in rental_res['result'][0]['tenant_id'].split(','):
                                    rentPayment = db.execute("""
                                    SELECT * FROM pm.purchases pur
                                    WHERE (DATE_FORMAT(pur.next_payment,'%d') <= DATE_FORMAT(now(),'%d') AND {fn MONTHNAME(pur.next_payment)} = {fn MONTHNAME(now())} AND YEAR(pur.next_payment) = YEAR(now()))
                                    AND pur.payer  LIKE '%""" + r + """%'
                                    AND pur.purchase_type= "RENT"
                                    AND pur.pur_property_id LIKE '%""" + property_id + """%'
                                    """)
                                    if len(rentPayment['result']) > 0:
                                        response['result'][i]['rent_paid'] = rentPayment['result'][0]['purchase_status']
                            else:
                                rentPayment = db.execute("""
                                SELECT * FROM pm.purchases pur
                                WHERE (DATE_FORMAT(pur.next_payment,'%d') <= DATE_FORMAT(now(),'%d') AND {fn MONTHNAME(pur.next_payment)} = {fn MONTHNAME(now())} AND YEAR(pur.next_payment) = YEAR(now()))
                                AND  pur.payer  LIKE '%""" + rental_res['result'][0]['tenant_id'] + """%'
                                AND pur.purchase_type= "RENT"
                                AND pur.pur_property_id LIKE '%""" + property_id + """%'
                                """)
                                if len(rentPayment['result']) > 0:
                                    response['result'][i]['rent_paid'] = rentPayment['result'][0]['purchase_status']
                        else:
                            response['result'][i]['rental_status'] = ""
                            response['result'][i]['rent_paid'] = ""

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
                        response['result'][i]['rent_paid'] = ''
                        if len(rental_res['result']) > 0:

                            response['result'][i]['rental_status'] = rental_res['result'][0]['rental_status']
                            if len(rental_res['result'][0]['tenant_id'].split(',')) > 0:
                                print('in if')
                                for r in rental_res['result'][0]['tenant_id'].split(','):
                                    rentPayment = db.execute("""
                                    SELECT * FROM pm.purchases pur
                                    WHERE (DATE_FORMAT(pur.next_payment,'%d') <= DATE_FORMAT(now(),'%d') AND {fn MONTHNAME(pur.next_payment)} = {fn MONTHNAME(now())} AND YEAR(pur.next_payment) = YEAR(now()))
                                    AND pur.payer  LIKE '%""" + r + """%'
                                    AND pur.purchase_type= "RENT"
                                    AND pur.pur_property_id LIKE '%""" + property_id + """%'
                                    """)
                                    if len(rentPayment['result']) > 0:
                                        response['result'][i]['rent_paid'] = rentPayment['result'][0]['purchase_status']
                            else:
                                rentPayment = db.execute("""
                                SELECT * FROM pm.purchases pur
                                WHERE (DATE_FORMAT(pur.next_payment,'%d') <= DATE_FORMAT(now(),'%d') AND {fn MONTHNAME(pur.next_payment)} = {fn MONTHNAME(now())} AND YEAR(pur.next_payment) = YEAR(now()))
                                AND  pur.payer  LIKE '%""" + rental_res['result'][0]['tenant_id'] + """%'
                                AND pur.purchase_type= "RENT"
                                AND pur.pur_property_id LIKE '%""" + property_id + """%'
                                """)
                                if len(rentPayment['result']) > 0:
                                    response['result'][i]['rent_paid'] = rentPayment['result'][0]['purchase_status']
                        else:
                            response['result'][i]['rental_status'] = ""
                            response['result'][i]['rent_paid'] = ""

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
                    AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'PROCESSING' OR r.rental_status='TENANT APPROVED')
                    AND propM.management_status = 'ACCEPTED'
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
                    AND propM.management_status = 'ACCEPTED'
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
