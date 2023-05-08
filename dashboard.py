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
        where = {'tenant_id': user['tenant_id'][0]['tenant_id']}
        with connect() as db:
            res = db.select('tenantProfileInfo', where)
            # print('res:', res)
            response = db.execute(""" 
            SELECT * FROM pm.properties prop
            LEFT JOIN pm.rentals r
            ON r.rental_property_id = prop.property_uid
            LEFT JOIN pm.leaseTenants lt
            ON lt.linked_rental_uid = r.rental_uid
            LEFT JOIN pm.applications a
            ON r.linked_application_id LIKE CONCAT('%', a.application_uid, '%') 
            LEFT JOIN pm.propertyManager p
            ON p.linked_property_id = prop.property_uid
            WHERE lt.linked_tenant_id = \'""" + user['tenant_id'][0]['tenant_id'] + """\' AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'PM END EARLY' OR r.rental_status = 'TENANT END EARLY') AND (p.management_status = 'ACCEPTED' OR p.management_status='END EARLY' OR p.management_status='PM END EARLY' OR p.management_status='OWNER END EARLY')  ; """)

            for i in range(len(response['result'])):
                property_id = response['result'][i]['property_uid']
                # print(property_id)
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
                WHERE receiver LIKE '%""" + user['tenant_id'][0]['tenant_id'] + """%'
                AND (announcement_mode = 'Tenants' OR announcement_mode = 'Properties')
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
                    maintenance_res['result'][y]['total_estimate'] = 0
                    if len(quotes_res['result']) > 0:
                        for quote in quotes_res['result']:
                            if quote['quote_status'] == 'ACCEPTED' or quote['quote_status'] == 'AGREED' or quote['quote_status'] == 'PAID':
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
                                            WHERE tenant_id = \'""" + user['tenant_id'][0]['tenant_id'] + """\' """)
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
                AND pu.payer LIKE '%""" + user['tenant_id'][0]['tenant_id'] + """%'
                AND (pu.purchase_type= "RENT" OR pu.purchase_type= "EXTRA CHARGES" OR pu.purchase_type= "DEPOSIT" OR pu.purchase_type= "UTILITY" OR pu.purchase_type= "MAINTENANCE" OR pu.purchase_type= "REPAIRS" OR pu.purchase_type="LATE FEE")""")
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
                        if tenant_expenses['result'][ore]['purchase_status'] == 'PAID':
                            time_between_insertion_paid = datetime.now() - \
                                datetime.strptime(
                                tenant_expenses['result'][ore]['payment_date'], '%Y-%m-%d %H:%M:%S')
                            if 0 <= time_between_insertion_paid.days < 30:
                                print('not older than 30 days not in future',
                                      time_between_insertion_paid)
                                response['result'][i]['tenantExpenses'].append(
                                    (tenant_expenses['result'][ore]))

                        if tenant_expenses['result'][ore]['purchase_status'] == 'UNPAID':
                            # if older than 30 days
                            if time_between_insertion.days > 30:
                                print('older than 30 days')
                                # if unpaid then all
                                response['result'][i]['tenantExpenses'].append(
                                    (tenant_expenses['result'][ore]))
                            # if in future
                            elif time_between_insertion.days < 0:
                                print('in future')
                                # if utility or extra charges then all
                                if tenant_expenses['result'][ore]['purchase_type'] != 'RENT':
                                    print('here no rents')
                                    if tenant_expenses['result'][ore]['purchase_frequency'] != 'Monthly':
                                        response['result'][i]['tenantExpenses'].append(
                                            (tenant_expenses['result'][ore]))
                                    else:
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
            print(response['result'])
            if len(res['result']) > 0:
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
                property_res = db.execute("""
                SELECT  pm.*, b.business_uid AS manager_id, 
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
                owner_res = db.execute("""
                SELECT o.owner_first_name AS owner_first_name, 
                o.owner_last_name AS owner_last_name, 
                o.owner_email AS owner_email ,
                o.owner_phone_number AS owner_phone_number
                FROM pm.ownerProfileInfo o 
                WHERE o.owner_id = \'""" + owner_id + """\'""")
                response['result'][i]['owner'] = list(
                    owner_res['result'])
                # rental info for the property
                rental_res = db.execute("""
                SELECT  r.*,
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
                AND (r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED')""")
                print('rent_status_result', rent_status_result['result'])
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
                    response['result'][i]['rent_status'] = 'No Rent Info'
                    response['result'][i]['late_date'] = 'Not Applicable'
                maintenance_res = db.execute("""
                SELECT mr.*, p.address, p.unit, p.city, p.state, p.zip
                FROM pm.maintenanceRequests mr
                LEFT JOIN pm.properties p
                ON mr.property_uid = p.property_uid
                WHERE mr.property_uid = \'""" + property_id + """\'
                                                """)
                response['result'][i]['maintenanceRequests'] = list(
                    maintenance_res['result'])

                if len(maintenance_res['result']) > 0:
                    for y in range(len(maintenance_res['result'])):
                        # owner info for the property
                        property_manager_res = db.execute("""
                        SELECT *
                        FROM pm.propertyManager p
                        LEFT JOIN pm.businesses b
                        ON p.linked_business_id = b.business_uid
                        WHERE p.linked_property_id = \'""" + maintenance_res['result'][y]['property_uid'] + """\'
                        AND (p.management_status = 'ACCEPTED' OR p.management_status ='OWNER END EARLY' OR p.management_status ='PM END EARLY') """)
                        maintenance_res['result'][y]['property_manager'] = list(
                            property_manager_res['result'])
                        req_id = maintenance_res['result'][y]['maintenance_request_uid']
                        rid = {'linked_request_uid': req_id}  # rid
                        # print(rid)
                        if maintenance_res['result'][y]['assigned_business'] != None:
                            as_busiResponse = db.execute("""SELECT * FROM businesses b
                            WHERE business_uid = \'""" + maintenance_res['result'][y]['assigned_business'] + """\' """)
                            print(as_busiResponse)
                            maintenance_res['result'][y]['assigned_business_info'] = as_busiResponse['result']
                        else:
                            maintenance_res['result'][y]['assigned_business_info'] = [
                            ]
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
                                if quote['quote_status'] == 'ACCEPTED' or quote['quote_status'] == 'AGREED' or quote['quote_status'] == 'PAID':
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

                            if (len(billRes['result']) > 0):
                                for j in range(len(billRes['result'])):
                                    expense_res['result'][i].update(
                                        billRes['result'][j])
                                    # expense_res['result'][i] = (expense_res['result'][i]) + (
                                    #     billRes['result'][j])
                        # if maintainence return all the details related to the maintenance requests
                        elif expense_res['result'][i]['purchase_type'] == 'MAINTENANCE':
                            # print('in maintenance')
                            if expense_res['result'][i]['linked_bill_id'] != None:
                                print(expense_res['result']
                                      [i]['linked_bill_id'])
                                maintenanceRes = db.execute("""
                                SELECT mq.*, mr.*, b.*
                                FROM maintenanceQuotes mq
                                LEFT JOIN pm.maintenanceRequests mr
                                ON mr.maintenance_request_uid = mq.linked_request_uid
                                LEFT JOIN pm.businesses b
                                ON b.business_uid = mq.quote_business_uid
                                WHERE  mr.maintenance_request_uid = \'""" + expense_res['result'][i]['linked_bill_id'] + """\' """)
                                print(maintenanceRes)
                                if (len(maintenanceRes['result']) > 0):
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
                                WHERE  mr.maintenance_request_uid = \'""" + expense_res['result'][i]['linked_bill_id'] + """\' """)

                                if (len(repairRes['result']) > 0):
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
            AND management_status <> 'REFUSED'
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
                FROM pm.applications a
                LEFT JOIN pm.tenantProfileInfo tpi
                ON a.tenant_id = tpi.tenant_id WHERE a.property_uid = \'""" + property_id + """\'""")

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
                        if mr['assigned_business'] != None:
                            as_busiResponse = db.execute("""SELECT * FROM businesses b
                            WHERE business_uid = \'""" + mr['assigned_business'] + """\' """)
                            print(as_busiResponse)
                            mr['assigned_business_info'] = as_busiResponse['result']
                        else:
                            mr['assigned_business_info'] = []
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
                if len(maintenance_res['result']) > 0:
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
                        maintenance_res['result'][y]['quotes_received'] = 0
                        if len(quotes_res['result']) > 0:
                            quotes_received = 0
                            for quote in quotes_res['result']:
                                if quote['quote_status'] == 'ACCEPTED' or quote['quote_status'] == 'AGREED' or quote['quote_status'] == 'PAID':
                                    maintenance_res['result'][y]['total_estimate'] = quote['total_estimate']
                                else:
                                    maintenance_res['result'][y]['total_estimate'] = 0

                                if quote['quote_status'] == 'SENT':
                                    maintenance_res['result'][y]['quotes_received'] = quotes_received + 1

                                if quote['quote_status'] == 'ACCEPTED':
                                    maintenance_res['result'][y]['tenant_status'] = 'QUOTE ACCEPTED'
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
                print('rent_status_result', rent_status_result['result'])
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
                    response['result'][i]['rent_status'] = 'No Rent Info'
                    response['result'][i]['late_date'] = 'Not Applicable'

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

                            if (len(billRes['result']) > 0):
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
                                WHERE  mr.maintenance_request_uid = \'""" + expense_res['result'][i]['linked_bill_id'] + """\' """)

                                if (len(maintenanceRes['result']) > 0):
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
                                WHERE  mr.maintenance_request_uid = \'""" + expense_res['result'][i]['linked_bill_id'] + """\' """)

                                if (len(repairRes['result']) > 0):
                                    for j in range(len(repairRes['result'])):
                                        expense_res['result'][i].update(
                                            repairRes['result'][j])
                else:
                    response['result'][i]['expenses'] = []

        return response
