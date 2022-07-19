
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from matplotlib.font_manager import json_dump
from matplotlib.style import available

from data import connect
from datetime import date
import json


class PropertyInfo(Resource):
    def get(self):
        response = {}
        filters = ['property_uid', 'owner_id', 'manager_id', 'tenant_id']
        where = {}
        filterType = ''
        filterVal = ''
        with connect() as db:
            for filter in filters:
                filterValue = request.args.get(filter)
                if filterValue is not None:
                    where[filter] = filterValue
                    print(where, filter)
                    filterType = filter
                    filterVal = filterValue

            if filterType == 'manager_id':
                print('here if')
                response = db.execute(
                    """SELECT * FROM pm.propertyInfo WHERE management_status <> 'REJECTED' AND management_status <> 'TERMINATED' AND management_status <> 'EXPIRED' AND manager_id = \'"""
                    + filterVal
                    + """\' """)
                for i in range(len(response['result'])):
                    property_id = response['result'][i]['property_uid']
                    application_res = db.execute("""SELECT
                                                        *
                                                        FROM pm.applications WHERE property_uid = \'""" + property_id + """\'""")
                    # print('application_res', application_res)
                    response['result'][i]['applications'] = list(
                        application_res['result'])
                    maintenance_res = db.execute("""SELECT *
                                                        FROM pm.maintenanceRequests mr
                                                        WHERE mr.property_uid = \'""" + property_id + """\'
                                                        """)
                    response['result'][i]['maintenanceRequests'] = list(
                        maintenance_res['result'])

                    expense_res = db.execute("""SELECT *
                                                        FROM pm.purchases p
                                                        LEFT JOIN payments pa
                                                        ON pa.pay_purchase_id = p.purchase_uid
                                                        WHERE p.pur_property_id = \'""" + property_id + """\'
                                                        AND (purchase_type = 'UTILITY' OR  purchase_type = 'MAINTENANCE' OR purchase_type = 'REPAIRS')
                                                        AND (receiver = \'""" + filterVal + """\' OR payer LIKE '%%\"""" + filterVal + """\"%%')
                                                        """)

                    if(len(expense_res['result']) > 0):
                        response['result'][i]['expenses'] = list(
                            expense_res['result'])
                        for i in range(len(expense_res['result'])):
                            if expense_res['result'][i]['purchase_type'] == 'UTILITY':
                                print('in utility')
                                billRes = db.execute("""SELECT b.*, CONCAT(p.address," ", p.unit,", ", p.city, ", ", p.state," ", p.zip) AS address
                                                        FROM pm.bills b
                                                        LEFT JOIN properties p
                                                        ON p.property_uid = \'""" + expense_res['result'][i]['pur_property_id'] + """\'
                                                        WHERE b.bill_uid = \'""" + expense_res['result'][i]['linked_bill_id'] + """\' """)

                                if(len(billRes['result']) > 0):
                                    for j in range(len(billRes['result'])):
                                        expense_res['result'][i].update(
                                            billRes['result'][j])
                                        # expense_res['result'][i] = (expense_res['result'][i]) + (
                                        #     billRes['result'][j])
                            elif expense_res['result'][i]['purchase_type'] == 'MAINTENANCE':
                                print('in maintenance')
                                maintenanceRes = db.execute("""SELECT mq.*, mr.*, b.*, CONCAT(p.address," ", p.unit,", ", p.city, ", ", p.state," ", p.zip) AS address
                                                                FROM maintenanceQuotes mq
                                                                LEFT JOIN pm.maintenanceRequests mr
                                                                ON mr.maintenance_request_uid = mq.linked_request_uid
                                                                LEFT JOIN pm.businesses b
                                                                ON b.business_uid = mq.quote_business_uid
                                                                LEFT JOIN properties p
                                                                ON p.property_uid = \'""" + expense_res['result'][i]['pur_property_id'] + """\'
                                                                WHERE  mq.maintenance_quote_uid = \'""" + expense_res['result'][i]['linked_bill_id'] + """\' """)

                                if(len(maintenanceRes['result']) > 0):
                                    for j in range(len(maintenanceRes['result'])):
                                        expense_res['result'][i].update(
                                            maintenanceRes['result'][j])
                            elif expense_res['result'][i]['purchase_type'] == 'REPAIRS':
                                print('in maintenance')
                                repairRes = db.execute("""SELECT mq.*, mr.*, b.*, CONCAT(p.address," ", p.unit,", ", p.city, ", ", p.state," ", p.zip) AS address
                                                                FROM maintenanceQuotes mq
                                                                LEFT JOIN pm.maintenanceRequests mr
                                                                ON mr.maintenance_request_uid = mq.linked_request_uid
                                                                LEFT JOIN pm.businesses b
                                                                ON b.business_uid = mq.quote_business_uid
                                                                LEFT JOIN properties p
                                                                ON p.property_uid = \'""" + expense_res['result'][i]['pur_property_id'] + """\'
                                                                WHERE  mq.maintenance_quote_uid = \'""" + expense_res['result'][i]['linked_bill_id'] + """\' """)

                                if(len(repairRes['result']) > 0):
                                    for j in range(len(repairRes['result'])):
                                        expense_res['result'][i].update(
                                            repairRes['result'][j])
                    else:
                        response['result'][i]['expenses'] = []

                    # response['result'][i]['expenses'] = list(
                    #     expense_res['result'])
                # print(response)
            elif filterType == 'owner_id':
                print('here if')
                response = db.execute(
                    """SELECT * FROM pm.propertyInfo WHERE owner_id = \'"""
                    + filterVal
                    + """\' """)
                print(response)
            else:
                print('here else')
                response = db.select('propertyInfo', where)
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
                                        WHERE (management_status = 'ACCEPTED' OR management_status = 'END EARLY' OR management_status = 'PM END EARLY' OR management_status = 'OWNER END EARLY' ) """)

            print(response['result'])
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
                            print('add terminated')
                            terminated.append(rentals)

                     # do sometginf rental status EXPIRED
                    elif rentals['rental_status'] == 'EXPIRED':
                        print('do something if rental_status expired',
                              rentals['rental_status'])
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
                            print('add expired')
                            expired.append(rentals)
                        print('expired', expired,  len(expired))
                    else:
                        print('do something if rental_status None',
                              rentals['rental_status'])
                        notRented.append(rentals)
            availableProperties = terminated + expired + notRented
            response['result'] = availableProperties
            print(availableProperties, len(availableProperties))
        return response


class PropertiesManagerDetail(Resource):
    def get(self):
        response = {}
        filters = ['property_uid']
        where = {}
        with connect() as db:
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
                        print(property_id)
                        pid = {'linked_property_id': property_id}
                        application_res = db.execute("""SELECT
                                                        *
                                                        FROM pm.applications WHERE property_uid = \'""" + property_id + """\'""")
                        # print('application_res', application_res)
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
                                    AND (receiver = \'""" + filterValue + """\' OR payer LIKE '%%\"""" + filterValue + """\"%%')
                                    GROUP BY linked_bill_id
                                    """)
            if(len(response['result']) > 0):

                for i in range(len(response['result'])):
                    if response['result'][i]['purchase_type'] == 'UTILITY':
                        print('in utility')
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
                            print('here', property_uids)
                            response['result'][i]['address'] = []
                            for id in range(len(property_uids)):
                                print(property_uids[id])
                                propRes = db.execute("""SELECT CONCAT(p.address," ", p.unit,", ", p.city, ", ", p.state," ", p.zip) AS address
                                                FROM pm.properties p
                                                WHERE p.property_uid = \'""" + property_uids[id] + """\' """)

                                response['result'][i]['address'].append(
                                    propRes['result'][0]['address'])

                    elif response['result'][i]['purchase_type'] == 'MAINTENANCE':
                        print('in maintenance')
                        maintenanceRes = db.execute("""SELECT mq.*, b.*, CONCAT(p.address," ", p.unit,", ", p.city, ", ", p.state," ", p.zip) AS address
                                                                FROM maintenanceQuotes mq
                                                                LEFT JOIN pm.businesses b
                                                                ON b.business_uid = mq.quote_business_uid
                                                                LEFT JOIN properties p
                                                                ON p.property_uid = \'""" + response['result'][i]['pur_property_id'] + """\'
                                                                WHERE  mq.maintenance_quote_uid = \'""" + response['result'][i]['linked_bill_id'] + """\' """)

                        if(len(maintenanceRes['result']) > 0):
                            for j in range(len(maintenanceRes['result'])):
                                response['result'][i].update(
                                    maintenanceRes['result'][j])
                    elif response['result'][i]['purchase_type'] == 'REPAIRS':
                        print('in maintenance')
                        maintenanceRes = db.execute("""SELECT mq.*, b.*, CONCAT(p.address," ", p.unit,", ", p.city, ", ", p.state," ", p.zip) AS address
                                                                FROM maintenanceQuotes mq
                                                                LEFT JOIN pm.businesses b
                                                                ON b.business_uid = mq.quote_business_uid
                                                                LEFT JOIN properties p
                                                                ON p.property_uid = \'""" + response['result'][i]['pur_property_id'] + """\'
                                                                WHERE  mq.maintenance_quote_uid = \'""" + response['result'][i]['linked_bill_id'] + """\' """)

                        if(len(maintenanceRes['result']) > 0):
                            for j in range(len(maintenanceRes['result'])):
                                response['result'][i].update(
                                    maintenanceRes['result'][j])
            else:
                response['result'][i] = []
        return response
