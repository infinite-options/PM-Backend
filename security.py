
from datetime import datetime
from hashlib import sha256
from flask_jwt_extended import create_access_token, create_refresh_token
from businesses import getEmployeeBusinesses
from tenantProfileInfo import getTenantProfileInfo


def getHash(value):
    base = str(value).encode()
    return sha256(base).hexdigest()


def createSalt():
    return getHash(datetime.now())


def createHash(password, salt):
    return getHash(password+salt)


def createTokens(user):
    print('IN CREATETOKENS')
    print('IN CREATETOKENS', user)
    businesses = getEmployeeBusinesses(user)['result']
    tenant_user_id = getTenantProfileInfo(user)['result']
    print('IN CREATETOKENS', businesses)
    userInfo = {
        'user_uid': user['user_uid'],
        'first_name': user['first_name'],
        'last_name': user['last_name'],
        'phone_number': user['phone_number'],
        'email': user['email'],
        'role': user['role'],
        'google_auth_token': user['google_auth_token'],
        'businesses': businesses,
        'tenant_id': tenant_user_id
    }
    print('IN CREATETOKENS', userInfo)
    return {
        'access_token': create_access_token(userInfo),
        'refresh_token': create_refresh_token(userInfo),
        'user': userInfo
    }
