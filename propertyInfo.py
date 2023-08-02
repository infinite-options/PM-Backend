from flask import request
from flask_restful import Resource

# from matplotlib import style
from data import connect
from datetime import date, datetime


class PropertyInfo(Resource):
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
                    print(filter)
                    response = db.execute("""
                    SELECT *
                    FROM pm.propertyInfo
                    WHERE management_status <> 'REJECTED'
                    AND management_status <> 'TERMINATED'
                    AND management_status <> 'EXPIRED'
                    AND property_uid = \'""" + filterValue + """\' """)
                    for i in range(len(response['result'])):
                        property_id = response['result'][i]['property_uid']
                        application_res = db.execute("""
                        SELECT *
                        FROM pm.applications WHERE property_uid = \'""" + property_id + """\'""")

                        response['result'][i]['applications'] = list(
                            application_res['result'])

                        # get maintenance requests
                        maintenance_res = db.execute("""
                        SELECT *
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

            response = db.execute("""
            SELECT * FROM pm.properties p
            LEFT JOIN   pm.rentals r
            ON r.rental_property_id = p.property_uid
            LEFT JOIN pm.propertyManager pM
            ON pM.linked_property_id = p.property_uid
            LEFT JOIN pm.businesses b
            ON b.business_uid = pM.linked_business_id
            WHERE (management_status = 'ACCEPTED' OR management_status = 'END EARLY' OR management_status = 'PM END EARLY' OR management_status = 'OWNER END EARLY' ) 
            AND p.available_to_rent=1 """)

            # print(response['result'])
            availableProperties = []
            terminated = []
            rentals = []
            expired = []
            notRented = []
            endingSoon = []
            processing = []
            if len(response['result']) > 0:
                for rentals in response['result']:
                    # skip rental status ACTIVE
                    if rentals['rental_status'] == 'ACTIVE':
                        # print('skip if rental_status active',rentals['rental_status'])
                        # print('lease end', rentals['lease_end'])
                        time_between_insertion = datetime.strptime(
                            rentals['lease_end'], '%Y-%m-%d') - datetime.now()
                        # print(time_between_insertion)
                        # if older than 30 days
                        if time_between_insertion.days > 91:
                            print('skip if over 90')
                        else:
                            print('make available')
                            endingSoon.append(rentals)
                    # skip rental status PROCESSING
                    elif rentals['rental_status'] == 'PROCESSING':
                        # print('skip if rental_status processing', rentals['rental_status'])
                        processing.append(rentals)
                    # skip rental status TENANT APPROVED
                    elif rentals['rental_status'] == 'TENANT APPROVED':
                        print('skip if rental_status tenant approved',rentals['rental_status'])
                    # do sometginf rental status TERMINATED
                    elif rentals['rental_status'] == 'TERMINATED':
                        # print('do something if rental_status terminated',rentals['rental_status'])
                        # check if another lease active for the same property
                        terminatedResponse = db.execute("""
                        SELECT * FROM pm.rentals r
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
                        expiredResponse = db.execute("""
                        SELECT * FROM pm.rentals r
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
            availableProperties = terminated + expired + notRented + endingSoon

            print(type(availableProperties))
            # remove any duplicates
            seen_titles = set()
            new_list = []
            for obj in availableProperties:
                # print(obj)
                if obj['property_uid'] not in seen_titles:
                    new_list.append(obj)
                    seen_titles.add(obj['property_uid'])
            response['result'] = new_list
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
                        owner_id = response['result'][i]['owner_id']
                        # owner info for the property
                        if owner_id is not None:
                            owner_res = db.execute("""
                            SELECT
                            o.owner_id AS owner_id,
                            o.owner_first_name AS owner_first_name,
                            o.owner_last_name AS owner_last_name,
                            o.owner_email AS owner_email ,
                            o.owner_phone_number AS owner_phone_number
                            FROM pm.ownerProfileInfo o
                            WHERE o.owner_id = \'""" + owner_id + """\'""")
                            response['result'][i]['owner'] = list(
                                owner_res['result'])
                        else:
                            response['result'][i]['owner'] = []
                        application_res = db.execute("""SELECT
                                                        *
                                                        FROM pm.applications WHERE property_uid = \'""" + property_id + """\'""")

                        response['result'][i]['applications'] = list(
                            application_res['result'])

                        maintenance_res = db.execute("""
                        SELECT mr.*,p.owner_id, p.property_uid, p.address, p.unit, p.city, p.state, p.zip
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
                                for quote in quotes_res['result']:
                                    if quote['quote_status'] == 'ACCEPTED':
                                        maintenance_res['result'][y]['total_estimate'] = quote['total_estimate']
                                    else:
                                        maintenance_res['result'][y]['total_estimate'] = 0
                            else:
                                maintenance_res['result'][y]['total_estimate'] = 0
                            maintenance_res['result'][y]['total_quotes'] = len(
                                quotes_res['result'])
                        property_res = db.execute("""
                        SELECT
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

                        rental_res = db.execute("""
                        SELECT
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
                        AND (r.rental_status = 'PROCESSING' OR r.rental_status = 'ACTIVE' OR r.rental_status = 'TENANT APPROVED' OR r.rental_status = 'PENDING' OR r.rental_status = 'REFUSED')
                        GROUP BY lt.linked_rental_uid""")
                        response['result'][i]['rentalInfo'] = list(
                            rental_res['result'])
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

        return response
