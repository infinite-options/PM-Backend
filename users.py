
from flask import request
from flask_restful import Resource
import math
from data import connect
from security import createSalt, createHash, createTokens


def getUserByEmail(email):
    with connect() as db:
        result = db.select('users', {'email': email})
        if len(result['result']) > 0:
            return result['result'][0]


def createUser(firstName, lastName, phoneNumber, email, password, role,
               google_auth_token=None, google_refresh_token=None, social_id=None, access_expires_in=None):
    with connect() as db:
        newUserID = db.call('new_user_id')['result'][0]['new_id']
        passwordSalt = createSalt()
        passwordHash = createHash(password, passwordSalt)
        newUser = {
            'user_uid': newUserID,
            'first_name': firstName,
            'last_name': lastName,
            'phone_number': phoneNumber,
            'email': email,
            'password_salt': passwordSalt,
            'password_hash': passwordHash,
            'role': role,
            'google_auth_token': google_auth_token,
            'google_refresh_token': google_refresh_token,
            'social_id': social_id,
            'access_expires_in': access_expires_in
        }
        response = db.insert('users', newUser)
        return newUser


class Login(Resource):
    def post(self):
        response = {}
        print('IN LOGIN')
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        user = getUserByEmail(email)
        if user:
            print('IN IF LOGIN')
            passwordSalt = user['password_salt']
            passwordHash = createHash(password, passwordSalt)
            print('IN IF LOGIN', passwordHash, passwordSalt)
            if passwordHash == user['password_hash']:
                response['message'] = 'Login successful'
                response['code'] = 200
                response['result'] = createTokens(user)
                print('IN IF IF LOGIN', response)
            else:
                response['message'] = 'Incorrect password'
                response['code'] = 401
                print('IN IF ELSE LOGIN', response)
        else:
            print('IN ELSE LOGIN')
            response['message'] = 'Email not found'
            response['code'] = 404
            print('IN ELSE LOGIN', response)
        return response


class Users(Resource):
    def get(self):
        response = {}
        filters = ['user_uid', 'email', 'role']
        where = {}
        for filter in filters:
            filterValue = request.args.get(filter)
            if filterValue is not None:
                where[filter] = filterValue
        with connect() as db:
            response = db.select('users', where)
        return response

    def post(self):
        response = {}
        data = request.get_json()
        firstName = data.get('first_name')
        lastName = data.get('last_name')
        phoneNumber = data.get('phone_number')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role')
        user = getUserByEmail(email)
        # if user:
        #     response['message'] = 'Email taken'
        #     response['code'] = 409
        # else:
        #     user = createUser(firstName, lastName, phoneNumber, email, password, role)
        #     response['message'] = 'Signup success'
        #     response['code'] = 200
        #     response['result'] = createTokens(user)
        if user:
            response['message'] = 'User already exists'
        else:
            user = createUser(firstName, lastName, phoneNumber,
                              email, password, role)
            response['message'] = 'Signup success'
            response['code'] = 200
            response['result'] = createTokens(user)
        return response

    def put(self):
        response = {}
        data = request.get_json()
        email = data.get('email')
        role = data.get('role')
        user = getUserByEmail(email)
        if user:
            print(user)
            uid = {'user_uid': user['user_uid']}
            updateRole = {'role': user['role'] + ',' + role}
            with connect() as db:
                res = db.update('users', uid, updateRole)
                u = getUserByEmail(email)
                response['message'] = 'Signup success'
                response['code'] = 200
                response['result'] = createTokens(u)

        else:

            response['message'] = 'Account does not exist! Please Signup'
            response['code'] = 200

        return response

# updating access token if expired


class UpdateAccessToken(Resource):
    def post(self, user_id):
        print("In UpdateAccessToken")
        response = {}
        items = {}
        with connect() as db:
            data = request.json
            google_auth_token = data["google_auth_token"]
            query = """UPDATE users
                SET google_auth_token = \'""" + google_auth_token + """\'
                WHERE user_uid = \'""" + user_id + """\' """
            print(query)
            pk = {
                'user_uid': user_id}
            updateUserToken = {
                'google_auth_token': google_auth_token}
            response = db.update('users', pk, updateUserToken)

        return response, 200

# get user tokens


class UserToken(Resource):
    def get(self, user_email_id):
        print("In usertoken")
        response = {}
        items = {}

        with connect() as db:

            query = (
                """SELECT user_unique_id
                                , email
                                , google_auth_token
                                , google_refresh_token
                        FROM
                        users WHERE email = \'"""
                + user_email_id
                + """\';"""
            )
            print(query)
            response = db.execute(
                """SELECT user_uid
                                , email
                                , google_auth_token
                                , google_refresh_token FROM users WHERE email = \'"""
                + user_email_id
                + """\' """)

            return response, 200


class AvailableAppointmentsTenant(Resource):
    def get(self, date_value, duration, user_id, start_time, end_time):
        print("\nInside Available Appointments")
        with connect() as db:

            print("Inside try block", date_value,
                  duration,  user_id, start_time, end_time)
            h, m, s = duration.split(':')
            interval = math.ceil(
                ((int(h) * 3600 + int(m) * 60 + int(s))/60)/30)
            print(type(interval), interval)

            atimes = {'message': 'Successfully executed SQL query.',
                      'code': 280, 'result': []}
            for k in range(0, interval):
                print(k)
                query = ("""
                    -- AVAILABLE TIME SLOTS QUERY - WORKS
                    WITH ats AS (
                    -- CALCULATE AVAILABLE TIME SLOTS
                    SELECT
                        row_num,
                        cast(begin_datetime as time) AS begin_time,
                        cast(end_datetime as time) AS end_time
                    FROM(
                        -- GET TIME SLOTS
                        SELECT ts.*,
                            ROW_NUMBER() OVER() AS row_num,
                            TIME(ts.begin_datetime) AS ts_begin,
                            TIME(ts.end_datetime) AS ts_end,
                            meet_dur.*
                        FROM pm.time_slots ts
                        -- GET CURRENT APPOINTMENTS
                        LEFT JOIN (
                        SELECT -- *,
                            maintenance_request_uid,
                            scheduled_date,
                            scheduled_time AS start_time,
                            event_duation,
                            linked_tenant_id AS tenant_id,
                            ADDTIME(scheduled_time, event_duation) AS end_time,
                            cast(concat(scheduled_date, ' ', scheduled_time) as datetime) as start,
                            cast(concat(scheduled_date, ' ', ADDTIME(scheduled_time, event_duation)) as datetime) as end
                        FROM pm.maintenanceRequests
                        LEFT JOIN pm.maintenanceQuotes
                        ON linked_request_uid = maintenance_request_uid
                        LEFT JOIN pm.rentals
                        ON rental_property_id = property_uid
                        LEFT JOIN pm.leaseTenants
                        ON linked_rental_uid = rental_uid
                        WHERE scheduled_date = '"""
                         + date_value
                         + """' AND linked_tenant_id = '"""
                         + user_id
                         + """' ) AS meet_dur
                        ON TIME(ts.begin_datetime) = meet_dur.start_time
                            OR (TIME(ts.begin_datetime) > meet_dur.start_time AND TIME(end_datetime) <= ADDTIME(meet_dur.end_time,"0:29"))
                        )AS taadpa
                     WHERE ISNULL(taadpa.maintenance_request_uid) AND (taadpa.ts_begin BETWEEN '"""
                         + start_time
                         + """' AND '"""
                         + end_time
                         + """')
                    )

                    SELECT *
                    FROM (
                        SELECT  -- *,
                              row_num,
                              -- row_num_hr,
                              DATE_FORMAT(begin_time, '%T') AS "begin_time",
                              CASE
                                WHEN ISNULL(row_num_hr) THEN "0:29:59"
                                ELSE '""" + duration + """'
                              END AS available_duration
                        FROM (
                            SELECT *
                            FROM ats
                            LEFT JOIN (
                                SELECT
                                    row_num as row_num_hr,
                                    begin_time AS begin_time_hr,
                                    end_time AS end_time_hr
                                FROM ats) AS ats1
                            ON ats.row_num + """ + str(k) + """ = ats1.row_num_hr
                          ) AS atss) AS atsss
                    WHERE '""" + duration + """' <= available_duration; """)
                print(query)
                available_times = db.execute("""
                            WITH ats AS (
                            SELECT
                                row_num,
                                cast(begin_datetime as time) AS begin_time,
                                cast(end_datetime as time) AS end_time
                            FROM(SELECT ts.*,
                                    ROW_NUMBER() OVER() AS row_num,
                                    TIME(ts.begin_datetime) AS ts_begin,
                                    TIME(ts.end_datetime) AS ts_end,
                                    meet_dur.*
                                FROM pm.time_slots ts
                                LEFT JOIN (
                                    SELECT -- *,
                                        maintenance_request_uid,
                                        scheduled_date,
                                        scheduled_time AS start_time,
                                        event_duration,
                                        linked_tenant_id AS tenant_id,
                                        ADDTIME(scheduled_time, event_duration) AS end_time,
                                        cast(concat(scheduled_date, ' ', scheduled_time) as datetime) as start,
                                        cast(concat(scheduled_date, ' ', ADDTIME(scheduled_time, event_duration)) as datetime) as end
                                    FROM pm.maintenanceRequests
                                    LEFT JOIN pm.maintenanceQuotes
                                    ON linked_request_uid = maintenance_request_uid
                                    LEFT JOIN pm.rentals
                                    ON rental_property_id = property_uid
                                    LEFT JOIN pm.leaseTenants
                                    ON linked_rental_uid = rental_uid
                                    WHERE scheduled_date = '"""
                                             + date_value
                                             + """' AND linked_tenant_id = '"""
                                             + user_id
                                             + """') AS meet_dur
                                ON TIME(ts.begin_datetime) = meet_dur.start_time
                                    OR (TIME(ts.begin_datetime) > meet_dur.start_time AND TIME(end_datetime) <= ADDTIME(meet_dur.end_time,"0:29"))
                                )AS taadpa
                            WHERE ISNULL(taadpa.maintenance_request_uid) AND (taadpa.ts_begin BETWEEN '"""
                                             + start_time
                                             + """' AND '"""
                                             + end_time
                                             + """')
                            )
                            SELECT *
                            FROM (
                                SELECT row_num,
                                    DATE_FORMAT(begin_time, '%T') AS "begin_time",
                                    CASE
                                        WHEN ISNULL(row_num_hr) THEN "0:29:59"
                                        ELSE '"""
                                             + duration
                                             + """'
                                    END AS available_duration
                                FROM (
                                    SELECT *
                                    FROM ats
                                    LEFT JOIN (
                                        SELECT
                                            row_num as row_num_hr,
                                            begin_time AS begin_time_hr,
                                            end_time AS end_time_hr
                                        FROM ats) AS ats1
                                    ON ats.row_num + """ + str(k) + """ = ats1.row_num_hr
                                ) AS atss) AS atsss
                            WHERE '"""
                                             + duration
                                             + """' <= available_duration""")
                print(available_times)
                atimes['result'] = atimes['result'] + \
                    (available_times['result'])

            blocked = ["row_num_hr", "begin_time", "available_duration"]

            total = []
            for i in atimes['result']:
                for key, value in i.items():
                    if key not in blocked:
                        total.append(value)

            counts = {}
            for i in total:
                if i in counts.keys():
                    counts[i] += 1
                else:
                    counts[i] = 1
            finalResult = {'message': 'Successfully executed SQL query.',
                           'code': 280, 'result': []}

            for key, value in counts.items():
                if int(value) == interval:
                    selectKey = key
                    # print(selectKey)
                    for i in atimes['result']:
                        # print(i)
                        for key, value in i.items():
                            # print(key, value)
                            if value == selectKey and key not in blocked:
                                # print('here')
                                finalResult['result'].append(i)
                                # print('finalResult', finalResult)

            # print("Available Times: ", (available_times))
            # print("Number of time slots: ", len(available_times["result"]))
            # print("Available Times: ", str(available_times['result'][0]["appt_start"]))
            seen = set()
            result = {'message': 'Successfully executed SQL query.',
                      'code': 280, 'result': []}

            for dic in finalResult['result']:
                key = (dic['row_num'], dic['begin_time'])
                if key in seen:
                    continue

                result['result'].append(dic)
                seen.add(key)

            print(result['result'])
            return result


# get user tokens


class UserDetails(Resource):
    def get(self, user_id):
        print("In userDetails")
        response = {}
        items = {}
        print(user_id[0])

        with connect() as db:
            if user_id[0] == '1':
                query = (
                    """SELECT user_uid
                , email, first_name
                , last_name
                , google_auth_token
                , google_refresh_token FROM users WHERE user_uid = \'"""
                    + user_id
                    + """\' """
                )
                print(query)
                response = db.execute("""SELECT user_uid
                                    , email
                                    , first_name
                                    , last_name
                                    , google_auth_token
                                    , google_refresh_token FROM users WHERE user_uid = \'"""
                                      + user_id
                                      + """\' """)
            elif user_id[0] == '3':
                response = db.execute("""SELECT user_uid
                                    , email
                                    , first_name
                                    , last_name
                                    , google_auth_token
                                    , google_refresh_token FROM tenantProfileInfo t
                                    LEFT JOIN
                                    users u
                                     ON t.tenant_user_id = u.user_uid WHERE tenant_id = \'"""
                                      + user_id
                                      + """\' """)

            else:
                business_email = db.execute("""SELECT business_uid
                                    , business_email
                                    , business_name FROM businesses WHERE business_uid = \'"""
                                            + user_id
                                            + """\' """)
                print(business_email['result'][0])
                response = db.execute("""SELECT user_uid
                                    , email
                                    , first_name
                                    , last_name
                                    , google_auth_token
                                    , google_refresh_token FROM users WHERE email = \'"""
                                      + business_email['result'][0]['business_email']
                                      + """\' """)
            return response


class AvailableAppointmentsMaintenance(Resource):
    def get(self, date_value, duration, user_id, start_time, end_time):
        print("\nInside Available Appointments")
        with connect() as db:

            print("Inside try block", date_value,
                  duration,  user_id, start_time, end_time)
            h, m, s = duration.split(':')
            interval = math.ceil(
                ((int(h) * 3600 + int(m) * 60 + int(s))/60)/30)
            print(type(interval), interval)

            atimes = {'message': 'Successfully executed SQL query.',
                      'code': 280, 'result': []}
            for k in range(0, interval):
                print(k)
                query = ("""
                    -- AVAILABLE TIME SLOTS QUERY - WORKS
                    WITH ats AS (
                    -- CALCULATE AVAILABLE TIME SLOTS
                    SELECT
                        row_num,
                        cast(begin_datetime as time) AS begin_time,
                        cast(end_datetime as time) AS end_time
                    FROM(
                        -- GET TIME SLOTS
                        SELECT ts.*,
                            ROW_NUMBER() OVER() AS row_num,
                            TIME(ts.begin_datetime) AS ts_begin,
                            TIME(ts.end_datetime) AS ts_end,
                            meet_dur.*
                        FROM pm.time_slots ts
                        -- GET CURRENT APPOINTMENTS
                        LEFT JOIN (
                        SELECT -- *,
                            maintenance_request_uid,
                            scheduled_date,
                            scheduled_time AS start_time,
                            event_duation,
                            assigned_business AS business_id,
                            linked_tenant_id AS tenant_id,
                            ADDTIME(scheduled_time, event_duation) AS end_time,
                            cast(concat(scheduled_date, ' ', scheduled_time) as datetime) as start,
                            cast(concat(scheduled_date, ' ', ADDTIME(scheduled_time, event_duation)) as datetime) as end
                        FROM pm.maintenanceRequests
                        LEFT JOIN pm.maintenanceQuotes
                        ON linked_request_uid = maintenance_request_uid
                        LEFT JOIN pm.rentals
                        ON rental_property_id = property_uid
                        LEFT JOIN pm.leaseTenants
                        ON linked_rental_uid = rental_uid
                        WHERE scheduled_date = '"""
                         + date_value
                         + """' AND linked_tenant_id = '"""
                         + user_id
                         + """' ) AS meet_dur
                        ON TIME(ts.begin_datetime) = meet_dur.start_time
                            OR (TIME(ts.begin_datetime) > meet_dur.start_time AND TIME(end_datetime) <= ADDTIME(meet_dur.end_time,"0:29"))
                        )AS taadpa
                     WHERE ISNULL(taadpa.maintenance_request_uid) AND (taadpa.ts_begin BETWEEN '"""
                         + start_time
                         + """' AND '"""
                         + end_time
                         + """')
                    )

                    SELECT *
                    FROM (
                        SELECT  -- *,
                              row_num,
                              -- row_num_hr,
                              DATE_FORMAT(begin_time, '%T') AS "begin_time",
                              CASE
                                WHEN ISNULL(row_num_hr) THEN "0:29:59"
                                ELSE '""" + duration + """'
                              END AS available_duration
                        FROM (
                            SELECT *
                            FROM ats
                            LEFT JOIN (
                                SELECT
                                    row_num as row_num_hr,
                                    begin_time AS begin_time_hr,
                                    end_time AS end_time_hr
                                FROM ats) AS ats1
                            ON ats.row_num + """ + str(k) + """ = ats1.row_num_hr
                          ) AS atss) AS atsss
                    WHERE '""" + duration + """' <= available_duration; """)
                print(query)
                available_times = db.execute("""
                            WITH ats AS (
                            SELECT
                                row_num,
                                cast(begin_datetime as time) AS begin_time,
                                cast(end_datetime as time) AS end_time
                            FROM(SELECT ts.*,
                                    ROW_NUMBER() OVER() AS row_num,
                                    TIME(ts.begin_datetime) AS ts_begin,
                                    TIME(ts.end_datetime) AS ts_end,
                                    meet_dur.*
                                FROM pm.time_slots ts
                                LEFT JOIN (
                                    SELECT -- *,
                                        maintenance_request_uid,
                                        scheduled_date,
                                        scheduled_time AS start_time,
                                        event_duration,
                                        assigned_business AS business_id,
                                        ADDTIME(scheduled_time, event_duration) AS end_time,
                                        cast(concat(scheduled_date, ' ', scheduled_time) as datetime) as start,
                                        cast(concat(scheduled_date, ' ', ADDTIME(scheduled_time, event_duration)) as datetime) as end
                                    FROM pm.maintenanceRequests
                                    LEFT JOIN pm.maintenanceQuotes
                                    ON linked_request_uid = maintenance_request_uid
                                    WHERE scheduled_date = '"""
                                             + date_value
                                             + """' AND assigned_business = '"""
                                             + user_id
                                             + """') AS meet_dur
                                ON TIME(ts.begin_datetime) = meet_dur.start_time
                                    OR (TIME(ts.begin_datetime) > meet_dur.start_time AND TIME(end_datetime) <= ADDTIME(meet_dur.end_time,"0:29"))
                                )AS taadpa
                            WHERE ISNULL(taadpa.maintenance_request_uid) AND (taadpa.ts_begin BETWEEN '"""
                                             + start_time
                                             + """' AND '"""
                                             + end_time
                                             + """')
                            )
                            SELECT *
                            FROM (
                                SELECT row_num,
                                    DATE_FORMAT(begin_time, '%T') AS "begin_time",
                                    CASE
                                        WHEN ISNULL(row_num_hr) THEN "0:29:59"
                                        ELSE '"""
                                             + duration
                                             + """'
                                    END AS available_duration
                                FROM (
                                    SELECT *
                                    FROM ats
                                    LEFT JOIN (
                                        SELECT
                                            row_num as row_num_hr,
                                            begin_time AS begin_time_hr,
                                            end_time AS end_time_hr
                                        FROM ats) AS ats1
                                    ON ats.row_num + """ + str(k) + """ = ats1.row_num_hr
                                ) AS atss) AS atsss
                            WHERE '"""
                                             + duration
                                             + """' <= available_duration""")
                print(available_times)
                atimes['result'] = atimes['result'] + \
                    (available_times['result'])

            blocked = ["row_num_hr", "begin_time", "available_duration"]

            total = []
            for i in atimes['result']:
                for key, value in i.items():
                    if key not in blocked:
                        total.append(value)

            counts = {}
            for i in total:
                if i in counts.keys():
                    counts[i] += 1
                else:
                    counts[i] = 1
            finalResult = {'message': 'Successfully executed SQL query.',
                           'code': 280, 'result': []}

            for key, value in counts.items():
                if int(value) == interval:
                    selectKey = key
                    # print(selectKey)
                    for i in atimes['result']:
                        # print(i)
                        for key, value in i.items():
                            # print(key, value)
                            if value == selectKey and key not in blocked:
                                # print('here')
                                finalResult['result'].append(i)
                                # print('finalResult', finalResult)

            # print("Available Times: ", (available_times))
            # print("Number of time slots: ", len(available_times["result"]))
            # print("Available Times: ", str(available_times['result'][0]["appt_start"]))
            seen = set()
            result = {'message': 'Successfully executed SQL query.',
                      'code': 280, 'result': []}

            for dic in finalResult['result']:
                key = (dic['row_num'], dic['begin_time'])
                if key in seen:
                    continue

                result['result'].append(dic)
                seen.add(key)

            print(result['result'])
            return result
