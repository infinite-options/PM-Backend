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
            response = db.execute(""" 
            SELECT * FROM pm.properties
            LEFT JOIN pm.rentals
            ON rental_property_id = property_uid
            LEFT JOIN pm.leaseTenants
            ON linked_rental_uid = rental_uid
            LEFT JOIN pm.propertyManager p
            ON linked_property_id = property_uid
            WHERE linked_tenant_id = \'""" + user['user_uid'] + """\' AND (rental_status = 'ACTIVE' OR rental_status = 'PM END EARLY' OR rental_status = 'TENANT END EARLY') AND (p.management_status = 'ACCEPTED' OR p.management_status='END EARLY' OR p.management_status='PM END EARLY' OR p.management_status='OWNER END EARLY')  ; """)

            for i in range(len(response['result'])):
                property_id = response['result'][i]['property_uid']
                print(property_id)
                property_res = db.execute("""
                SELECT
                p.address, p.unit, p.city, p.state,p.zip,
                b.business_uid AS manager_id,
                b.business_name AS manager_business_name,
                b.business_email AS manager_email,
                b.business_phone_number AS manager_phone_number
                FROM pm.propertyManager pm
                LEFT JOIN businesses b
                ON b.business_uid = pm.linked_business_id
                LEFT JOIN properties p
                ON pm.linked_property_id = p.property_uid
                WHERE pm.linked_property_id = \'""" + property_id + """\'
                AND (pm.management_status = 'ACCEPTED' OR pm.management_status='END EARLY' OR pm.management_status='PM END EARLY' OR pm.management_status='OWNER END EARLY')   """)

                response['result'][i]['property_manager'] = list(
                    property_res['result'])
                announcements_res = db.execute("""
                SELECT * FROM announcements
                WHERE receiver LIKE '%""" + user['user_uid'] + """%'
                AND receiver_properties LIKE  '%""" + property_id + """%' """)
                response['result'][i]['announcements'] = list(
                    announcements_res['result'])
                # get maintenance requests
                maintenance_res = db.execute("""
                SELECT mr.*, p.owner_id, p.property_uid,p.address, p.unit, p.city, p.state, p.zip
                FROM pm.maintenanceRequests mr
                LEFT JOIN pm.properties p
                ON mr.property_uid = p.property_uid
                WHERE mr.property_uid = \'""" + property_id + """\'
                """)
                response['result'][i]['maintenanceRequests'] = list(
                    maintenance_res['result'])
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
                    if len(quotes_res['result']) > 0:
                        for quote in quotes_res['result']:
                            if quote['quote_status'] == 'ACCEPTED':
                                maintenance_res['result'][y]['total_estimate'] = quote['total_estimate']
                            else:
                                maintenance_res['result'][y]['total_estimate'] = 0
                    else:
                        maintenance_res['result'][y]['total_estimate'] = 0
                    maintenance_res['result'][y]['total_quotes'] = len(
                        quotes_res['result'])
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

                tenant_expenses = db.execute("""
                SELECT *
                FROM pm.purchases pu
                LEFT JOIN
                pm.payments pa
                ON pa.pay_purchase_id = pu.purchase_uid
                LEFT JOIN pm.properties p
                ON pu.pur_property_id LIKE CONCAT('%', p.property_uid, '%')
                WHERE pu.pur_property_id LIKE '%""" + property_id + """%'
                AND pu.payer LIKE '%""" + user['user_uid'] + """%'
                AND (pu.purchase_type= "RENT" OR pu.purchase_type= "EXTRA CHARGES" OR pu.purchase_type= "UTILITY" OR pu.purchase_type= "MAINTENANCE" OR pu.purchase_type= "REPAIRS")""")
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
                response['result'][i]['per_sqft'] = round(response['result'][i]['listed_rent'] /
                                                          response['result'][i]['area'], 2)
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
                # print(property_res)
                # management status for property
                if len(property_res['result']) > 0:
                    for pr in range(len(property_res['result'])):
                        # print(property_res['result']
                        #       [pr]['management_status'])
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
                    print(rental_res['result'][0]['tenant_id'].split(','))
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

                maintenance_res = db.execute("""
                SELECT mr.*, p.address, p.unit, p.city, p.state, p.zip
                FROM pm.maintenanceRequests mr
                LEFT JOIN pm.properties p
                ON mr.property_uid = p.property_uid
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
                    if len(quotes_res['result']) > 0:
                        for quote in quotes_res['result']:
                            if quote['quote_status'] == 'ACCEPTED':
                                maintenance_res['result'][y]['total_estimate'] = quote['total_estimate']
                            else:
                                maintenance_res['result'][y]['total_estimate'] = 0
                    else:
                        maintenance_res['result'][y]['total_estimate'] = 0
                    maintenance_res['result'][y]['total_quotes'] = len(
                        quotes_res['result'])

                # get utilities or maintenance/repair expenses
                expense_res = db.execute("""
                SELECT p.*, pa.*, CONCAT(prop.address," ", prop.unit,", ", prop.city, ", ", prop.state," ", prop.zip) AS address
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
                    print(expense_res['result'])
                    for i in range(len(expense_res['result'])):
                        # if utility return all the details related to the utility
                        if expense_res['result'][i]['purchase_type'] == 'UTILITY':
                            # print('in utility')

                            billRes = db.execute("""
                            SELECT b.*
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
                            # print('in maintenance')
                            if expense_res['result'][i]['linked_bill_id'] != None:
                                maintenanceRes = db.execute("""
                                SELECT mq.*, mr.*, b.*
                                FROM maintenanceQuotes mq
                                LEFT JOIN pm.maintenanceRequests mr
                                ON mr.maintenance_request_uid = mq.linked_request_uid
                                LEFT JOIN pm.businesses b
                                ON b.business_uid = mq.quote_business_uid)
                                WHERE  mq.maintenance_quote_uid = \'""" + expense_res['result'][i]['linked_bill_id'] + """\' """)

                                if(len(maintenanceRes['result']) > 0):
                                    for j in range(len(maintenanceRes['result'])):
                                        expense_res['result'][i].update(
                                            maintenanceRes['result'][j])
                        # if repair return all the details related to the repair requests
                        elif expense_res['result'][i]['purchase_type'] == 'REPAIRS':
                            # print('in maintenance')
                            if expense_res['result'][i]['linked_bill_id'] != None:
                                repairRes = db.execute("""
                                SELECT mq.*, mr.*, b.*
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
            print(business)
            if business['business_type'] == 'MANAGEMENT' and business['employee_role'] == 'Owner':
                buid = business['business_uid']
                print(buid)
        print('buid', buid)
        with connect() as db:

            today = date.today()
            print(buid)

            response = db.execute("""
            SELECT *
            FROM pm.propertyInfo
            WHERE management_status <> 'REJECTED'
            AND management_status <> 'TERMINATED'
            AND management_status <> 'EXPIRED'
            AND management_status <> 'END EARLY'
            AND manager_id = \'""" + buid + """\' """)
            print(response)
            for i in range(len(response['result'])):
                property_id = response['result'][i]['property_uid']
                print(property_id)
                response['result'][i]['per_sqft'] = round(response['result'][i]['listed_rent'] /
                                                          response['result'][i]['area'], 2)
                # get tenant applications
                application_res = db.execute("""
                SELECT *
                FROM pm.applications WHERE property_uid = \'""" + property_id + """\'""")

                response['result'][i]['applications'] = list(
                    application_res['result'])
                num_apps = 0
                if len(application_res['result']) > 0:
                    for apps in application_res['result']:
                        if apps['application_status'] == 'NEW':
                            num_apps = num_apps+1
                response['result'][i]['num_apps'] = num_apps

                # get maintenance requests
                maintenance_res = db.execute("""
                SELECT mr.*, p.owner_id, p.property_uid,p.address, p.unit, p.city, p.state, p.zip
                FROM pm.maintenanceRequests mr
                LEFT JOIN pm.properties p
                ON mr.property_uid = p.property_uid
                WHERE mr.property_uid = \'""" + property_id + """\'
                """)
                response['result'][i]['maintenanceRequests'] = list(
                    maintenance_res['result'])
                new_mr = 0
                process_mr = 0
                quote_received_mr = 0
                quote_accepted_mr = 0
                response['result'][i]['new_mr'] = new_mr
                response['result'][i]['process_mr'] = process_mr
                response['result'][i]['quote_received_mr'] = quote_received_mr
                response['result'][i]['quote_accepted_mr'] = quote_accepted_mr
                if len(maintenance_res['result']) > 0:
                    for mr in maintenance_res['result']:
                        req_id = mr['maintenance_request_uid']
                        rid = {'linked_request_uid': req_id}  # rid
                        quotes_res = db.select(
                            ''' maintenanceQuotes quote ''', rid)
                        if len(quotes_res['result']) > 0:
                            for mq in quotes_res['result']:
                                if mq['quote_status'] == 'SENT':
                                    quote_received_mr = quote_received_mr + 1
                                elif mq['quote_status'] == 'ACCEPTED':
                                    quote_accepted_mr = quote_accepted_mr + 1
                        if mr['request_status'] == 'NEW':
                            new_mr = new_mr + 1
                        elif mr['request_status'] == 'PROCESSING' and (quote_received_mr == 0 and quote_accepted_mr == 0):
                            process_mr = process_mr + 1
                        else:
                            print('do nothing')

                response['result'][i]['new_mr'] = new_mr
                response['result'][i]['process_mr'] = process_mr
                response['result'][i]['quote_received_mr'] = quote_received_mr
                response['result'][i]['quote_accepted_mr'] = quote_accepted_mr
                # print(maintenance_res['result'])
                for y in range(len(maintenance_res['result'])):
                    req_id = maintenance_res['result'][y]['maintenance_request_uid']
                    rid = {'linked_request_uid': req_id}  # rid
                    rental_res = db.execute("""
                    SELECT r.*,
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
                        WHERE r.rental_property_id = \'""" + maintenance_res['result'][y]['property_uid'] + """\'
                        AND (r.rental_status = 'PROCESSING' OR r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED')
                        GROUP BY lt.linked_rental_uid""")

                    if len(rental_res['result']) > 0:

                        maintenance_res['result'][y]['rentalInfo'] = list(
                            rental_res['result'])
                    else:
                        maintenance_res['result'][y]['rentalInfo'] = 'Not Rented'

                    owner_id = maintenance_res['result'][y]['owner_id']
                    # owner info for the property
                    owner_res = db.execute("""
                    SELECT
                    o.owner_id AS owner_id,
                    o.owner_first_name AS owner_first_name,
                    o.owner_last_name AS owner_last_name,
                    o.owner_email AS owner_email ,
                    o.owner_phone_number AS owner_phone_number
                    FROM pm.ownerProfileInfo o
                    WHERE o.owner_id = \'""" + owner_id + """\'""")
                    maintenance_res['result'][y]['owner'] = list(
                        owner_res['result'])
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
                    if len(quotes_res['result']) > 0:
                        quotes_received = 0
                        for quote in quotes_res['result']:
                            if quote['quote_status'] == 'ACCEPTED':
                                maintenance_res['result'][y]['total_estimate'] = quote['total_estimate']
                            else:
                                maintenance_res['result'][y]['total_estimate'] = 0
                            if quote['quote_status'] == 'SENT':
                                maintenance_res['result'][y]['quotes_received'] = quotes_received + 1
                            else:
                                maintenance_res['result'][y]['quotes_received'] = 0
                            if quote['quote_status'] == 'ACCEPTED':
                                maintenance_res['result'][y]['tenant_status'] = 'IN PROGRESS'
                            elif quote['quote_status'] == 'SENT':
                                maintenance_res['result'][y]['tenant_status'] = 'QUOTE RECEIVED'

                    else:
                        maintenance_res['result'][y]['total_estimate'] = 0
                    maintenance_res['result'][y]['total_quotes'] = len(
                        quotes_res['result'])
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
                                print('mr', time_between_insertion)
                                if ',' in str(time_between_insertion):
                                    response['result'][i]['oldestOpenMR'] = int(
                                        (str(time_between_insertion).split(',')[0]).split(' ')[0])
                                else:
                                    response['result'][i]['oldestOpenMR'] = 1

                else:
                    response['result'][i]['oldestOpenMR'] = 'Not Applicable'
                # rental info for the property
                rental_res = db.execute("""
                SELECT r.*, lt.*,tpi.*
                FROM pm.rentals r 
                LEFT JOIN pm.leaseTenants lt
                ON lt.linked_rental_uid = r.rental_uid
                LEFT JOIN pm.tenantProfileInfo tpi
                ON tpi.tenant_id = lt.linked_tenant_id
                WHERE r.rental_property_id = \'""" + property_id + """\'
                AND (r.rental_status = 'PROCESSING' OR r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED')""")

                if len(rental_res['result']) > 0:

                    response['result'][i]['rentalInfo'] = list(
                        rental_res['result'])
                else:
                    response['result'][i]['rentalInfo'] = 'Not Rented'

                rent_status_result = db.execute("""
                SELECT *
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
                            time_between_insertion = (
                                date.today() - late_date)
                            if ',' in str(time_between_insertion):

                                print('time', due_date, time_between_insertion,
                                      'late_date', late_date)
                                response['result'][i]['late_date'] = int((str(
                                    time_between_insertion).split(',')[0]).split(' ')[0])
                                print(int((str(
                                    time_between_insertion).split(',')[0]).split(' ')[0]))
                            else:
                                time_between_insertion = 0
                                print('time', due_date, time_between_insertion,
                                      'late_date', late_date)
                                response['result'][i]['late_date'] = 0

                else:
                    response['result'][i]['rent_status'] = 'Not Rented'
                    response['result'][i]['late_date'] = 'Not Applicable'
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

                            billRes = db.execute("""
                            SELECT b.*
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
                            if expense_res['result'][i]['linked_bill_id'] != None:
                                maintenanceRes = db.execute("""
                                SELECT mq.*, mr.*, b.*
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
                            if expense_res['result'][i]['linked_bill_id'] != None:
                                repairRes = db.execute("""
                                SELECT mq.*, mr.*, b.*
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
