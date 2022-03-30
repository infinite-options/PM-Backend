# PropertyManagement backend

---

### URLs

- Development: http://localhost:5000
- Production: https://t00axvabvb.execute-api.us-west-1.amazonaws.com/dev

---

### All Routes

- [/properties](#properties)
- [/properties/{property_uid}](#properties/{property_uid})
- [/ownerProperties](#ownerproperties)
- [/managerProperties](#managerproperties)
- [/tenantProperties](#tenantproperties)
- [/propertyInfo](#propertyinfo)
- [/users](#users)
- [/login](#login)
- [/ownerProfileInfo](#ownerprofileinfo)
- [/managerProfileInfo](#managerprofileinfo)
- [/tenantProfileInfo](#tenantprofileinfo)
- [/businessProfileInfo](#businessprofileinfo)
- [/rentals](#rentals)
- [/purchases](#purchases)
- [/payments](#payments)
- [/businesses](#businesses)
- [/employees](#employees)
- [/maintenanceRequests](#maintenanceRequests)
- [/maintenanceQuotes](#maintenanceQuotes)
- [/applications](#applications)
- [/leaseTenants](#leaseTenants)

---

### /properties

##### GET

- with no args, return all properties
- add args to endpoint to filter results (ex: /properties?num_beds=1)
- available filters
  - property_uid
  - owner_id
  - manager_id
  - address
  - city
  - state
  - zip
  - type
  - num_beds
  - num_baths
  - area
  - listed_rent
  - deposit
  - appliances
  - utilities
  - pets_allowed
  - deposit_for_rent
- response JSON:

```
{
    "message": "Successfully executed SQL query",
    "code": 200,
    "result": [
        {
            "linked_property_id": "200-000017",
            "linked_business_id": "600-000020",
            "linked_employee_id": null,
            "management_status": "FORWARDED",
            "property_uid": "200-000017",
            "owner_id": "100-000038",
            "manager_id": "",
            "address": "965 Bush st",
            "unit": "122",
            "city": "San Jose",
            "state": "CA",
            "zip": "90808",
            "property_type": "Apartment",
            "num_beds": 2.0,
            "num_baths": 1.5,
            "area": 1100,
            "listed_rent": 2000,
            "deposit": 2000,
            "appliances": "{\"Dryer\": false, \"Range\": false, \"Washer\": true, \"Microwave\": false, \"Dishwasher\": true, \"Refrigerator\": false}",
            "utilities": "{\"Gas\": false, \"Wifi\": true, \"Trash\": true, \"Water\": false, \"Electricity\": false}",
            "pets_allowed": 1,
            "deposit_for_rent": 1,
            "images": "[\"https://s3-us-west-1.amazonaws.com/io-pm/properties/200-000017/img_cover\", \"https://s3-us-west-1.amazonaws.com/io-pm/properties/200-000017/img_0\"]",
            "taxes": null,
            "mortgages": null
        }
    ]
}
```

##### POST

- create new property
- send as multipart/form-data
- include image files as img_cover, img_0, img_1...
- request JSON:

```
{
    "owner_id": "100-000001",
    "manager_id": "100-000002",
    "address": "123 Main St",
    "unit": "#101",
    "city": "San Jose",
    "state": "CA",
    "zip": "95120",
    "property_type": "Apartment",
    "num_beds": 2,
    "num_baths": 1,
    "area": 1000,
    "listed_rent": 1800,
    "deposit": 800,
    "appliances": {
        "Dryer": false,
        "Range": false,
        "Washer": false,
        "Microwave": true,
        "Dishwasher": false,
        "Refrigerator": true,
        "Air Conditioner": true
    },
    "utilities": {
        "Gas": true,
        "Wifi": false,
        "Trash": true,
        "Water": false,
        "Electricity": false
    },
    "pets_allowed": true,
    "deposit_for_rent": true,
    "img_cover": "",
    "img_0": "",
    "img_1": ""
}
```

- response JSON:

```
{
    "message": "Successfully committed SQL query",
    "code": 200
}
```

##### PUT

- update property
- send as multipart/form-data
- include image files or links as img_cover, img_0, img_1...
- request JSON:

```
{
    "property_uid": "200-000001",
    "owner_id": "100-000001",
    "manager_id": "100-000002",
    "address": "123 Main St",
    "unit": "#101",
    "city": "San Jose",
    "state": "CA",
    "zip": "95120",
    "property_type": "Apartment",
    "num_beds": 2,
    "num_baths": 1,
    "area": 1000,
    "listed_rent": 1800,
    "deposit": 800,
    "appliances": {
        "Dryer": false,
        "Range": false,
        "Washer": false,
        "Microwave": true,
        "Dishwasher": false,
        "Refrigerator": true,
        "Air Conditioner": true
    },
    "utilities": {
        "Gas": true,
        "Wifi": false,
        "Trash": true,
        "Water": false,
        "Electricity": false
    },
    "pets_allowed": true,
    "deposit_for_rent": true,
    "img_cover": "",
    "img_0": "",
    "img_1": ""
}
```

- response JSON:

```
{
    "message": "Successfully committed SQL query",
    "code": 200
}
```

---

### /properties/{property_uid} \*\*\* deprecated, use /properties PUT

#### PUT

- update property
- route changes based on property_uid (ex: /properties/200-000001)
- send as multipart/form-data
- include image files or links as img_cover, img_0, img_1...
- request JSON:

```
{
    "owner_id": "100-000001",
    "manager_id": "100-000002",
    "address": "123 Main St",
    "unit": "#101",
    "city": "San Jose",
    "state": "CA",
    "zip": "95120",
    "property_type": "Apartment",
    "num_beds": 2,
    "num_baths": 1,
    "area": 1000,
    "listed_rent": 1800,
    "deposit": 800,
    "appliances": {
        "Dryer": false,
        "Range": false,
        "Washer": false,
        "Microwave": true,
        "Dishwasher": false,
        "Refrigerator": true,
        "Air Conditioner": true
    },
    "utilities": {
        "Gas": true,
        "Wifi": false,
        "Trash": true,
        "Water": false,
        "Electricity": false
    },
    "pets_allowed": true,
    "deposit_for_rent": true,
    "img_cover": "",
    "img_0": "",
    "img_1": ""
}
```

- response JSON:

```
{
    "message": "Successfully committed SQL query",
    "code": 200
}
```

---

### /ownerProperties

##### GET

- include JWT in header
- returns information for owner properties, including related manager and purchase info
- response JSON:

```
{
    "message": "Successfully executed SQL query",
    "code": 200,
    "result": [
        {
            "property_uid": "200-000001",
            "owner_id": "100-000001",
            "manager_id": "600-000001",
            "address": "101 Main St",
            "unit": "#30",
            "city": "San Jose",
            "state": "CA",
            "zip": "95120",
            "property_type": "Apartment",
            "num_beds": 2.0,
            "num_baths": 2.5,
            "area": 1000,
            "listed_rent": 1200,
            "deposit": 1000,
            "appliances": "{\"Dryer\": true, \"Range\": true, \"Washer\": true, \"Microwave\": false, \"Dishwasher\": false, \"Refrigerator\": true}",
            "utilities": "{\"Gas\": true, \"Wifi\": false, \"Trash\": false, \"Water\": true, \"Electricity\": false}",
            "pets_allowed": 0,
            "deposit_for_rent": 0,
            "images": "[]",
            "taxes": null,
            "mortgages": null,
            "owner_first_name": "Owner",
            "owner_last_name": "Test",
            "owner_phone_number": "(800)123-1231",
            "owner_email": "pm@gmail.com",
            "manager_business_name": "IO Management",
            "manager_phone_number": "(800)123-1234",
            "manager_email": "iomanagement@gmail.com",
            "rental_uid": "300-000001",
            "rental_property_id": "200-000001",
            "tenant_id": "100-000003",
            "rent_payments": "[{\"of\": \"Gross Rent\", \"charge\": \"2000\", \"fee_name\": \"Rent\", \"fee_type\": \"$\", \"frequency\": \"Monthly\"}]",
            "lease_start": "2022-02-01",
            "lease_end": "2022-03-01",
            "rental_status": "ACTIVE",
            "tenant_first_name": "Tenant",
            "tenant_last_name": "Test",
            "purchases": "[{\"payer\": \"100-000007\", \"receiver\": \"200-000004\", \"amount_due\": 2000.0, \"amount_paid\": 0.0, \"description\": \"Rent\", \"purchase_uid\": \"400-000010\", \"purchase_type\": \"RENT\", \"purchase_notes\": \"March\", \"pur_property_id\": \"200-000004\", \"purchase_status\": \"UNPAID\"}]"
        }
    ]
}
```

---

### /managerProperties

##### GET

- include JWT in header
- returns information for manager properties, including related owner and purchase info
- must be called by owner of manager business
- response JSON:

```
{
    "message": "Successfully executed SQL query",
    "code": 200,
    "result": [
        {
            "property_uid": "200-000001",
            "owner_id": "100-000001",
            "manager_id": "600-000001",
            "address": "101 Main St",
            "unit": "#30",
            "city": "San Jose",
            "state": "CA",
            "zip": "95120",
            "property_type": "Apartment",
            "num_beds": 2.0,
            "num_baths": 2.5,
            "area": 1000,
            "listed_rent": 1200,
            "deposit": 1000,
            "appliances": "{\"Dryer\": true, \"Range\": true, \"Washer\": true, \"Microwave\": false, \"Dishwasher\": false, \"Refrigerator\": true}",
            "utilities": "{\"Gas\": true, \"Wifi\": false, \"Trash\": false, \"Water\": true, \"Electricity\": false}",
            "pets_allowed": 0,
            "deposit_for_rent": 0,
            "images": "[]",
            "taxes": null,
            "mortgages": null,
            "owner_first_name": "Owner",
            "owner_last_name": "Test",
            "owner_phone_number": "(800)123-1231",
            "owner_email": "pm@gmail.com",
            "manager_business_name": "IO Management",
            "manager_phone_number": "(800)123-1234",
            "manager_email": "iomanagement@gmail.com",
            "rental_uid": "300-000001",
            "rental_property_id": "200-000001",
            "tenant_id": "100-000003",
            "rent_payments": "[{\"of\": \"Gross Rent\", \"charge\": \"2000\", \"fee_name\": \"Rent\", \"fee_type\": \"$\", \"frequency\": \"Monthly\"}]",
            "lease_start": "2022-02-01",
            "lease_end": "2022-03-01",
            "rental_status": "ACTIVE",
            "tenant_first_name": "Tenant",
            "tenant_last_name": "Test",
            "purchases": "[{\"payer\": \"100-000007\", \"receiver\": \"200-000004\", \"amount_due\": 2000.0, \"amount_paid\": 0.0, \"description\": \"Rent\", \"purchase_uid\": \"400-000010\", \"purchase_type\": \"RENT\", \"purchase_notes\": \"March\", \"pur_property_id\": \"200-000004\", \"purchase_status\": \"UNPAID\"}]"
        }
    ]
}
```

---

### /tenantProperties

##### GET

- include JWT in header
- returns information for tenant properties, including related owner/manager and purchase info
- response JSON:

```
{
    "message": "Successfully executed SQL query",
    "code": 200,
    "result": [
        {
            "property_uid": "200-000001",
            "owner_id": "100-000001",
            "manager_id": "600-000001",
            "address": "101 Main St",
            "unit": "#30",
            "city": "San Jose",
            "state": "CA",
            "zip": "95120",
            "property_type": "Apartment",
            "num_beds": 2.0,
            "num_baths": 2.5,
            "area": 1000,
            "listed_rent": 1200,
            "deposit": 1000,
            "appliances": "{\"Dryer\": true, \"Range\": true, \"Washer\": true, \"Microwave\": false, \"Dishwasher\": false, \"Refrigerator\": true}",
            "utilities": "{\"Gas\": true, \"Wifi\": false, \"Trash\": false, \"Water\": true, \"Electricity\": false}",
            "pets_allowed": 0,
            "deposit_for_rent": 0,
            "images": "[]",
            "taxes": null,
            "mortgages": null,
            "owner_first_name": "Owner",
            "owner_last_name": "Test",
            "owner_phone_number": "(800)123-1231",
            "owner_email": "pm@gmail.com",
            "manager_business_name": "IO Management",
            "manager_phone_number": "(800)123-1234",
            "manager_email": "iomanagement@gmail.com",
            "rental_uid": "300-000001",
            "rental_property_id": "200-000001",
            "tenant_id": "100-000003",
            "rent_payments": "[{\"of\": \"Gross Rent\", \"charge\": \"2000\", \"fee_name\": \"Rent\", \"fee_type\": \"$\", \"frequency\": \"Monthly\"}]",
            "lease_start": "2022-02-01",
            "lease_end": "2022-03-01",
            "rental_status": "ACTIVE",
            "tenant_first_name": "Tenant",
            "tenant_last_name": "Test",
            "purchases": "[{\"payer\": \"100-000007\", \"receiver\": \"200-000004\", \"amount_due\": 2000.0, \"amount_paid\": 0.0, \"description\": \"Rent\", \"purchase_uid\": \"400-000010\", \"purchase_type\": \"RENT\", \"purchase_notes\": \"March\", \"pur_property_id\": \"200-000004\", \"purchase_status\": \"UNPAID\"}]"
        }
    ]
}
```

---

### /propertyInfo

##### GET

- with no args, returns all properties and related information
- add args to endpoint to filter results (ex: /propertyInfo?manager_id=600-000001)
- available filters
  - property_uid
  - owner_id
  - manager_id
  - tenant_id
- response JSON:

```
{
    "message": "Successfully executed SQL query",
    "code": 200,
    "result": [
        {
            "property_uid": "200-000001",
            "owner_id": "100-000001",
            "manager_id": "600-000001",
            "address": "101 Main St",
            "unit": "#30",
            "city": "San Jose",
            "state": "CA",
            "zip": "95120",
            "property_type": "Apartment",
            "num_beds": 2.0,
            "num_baths": 2.5,
            "area": 1000,
            "listed_rent": 1200,
            "deposit": 1000,
            "appliances": "{\"Dryer\": true, \"Range\": true, \"Washer\": true, \"Microwave\": false, \"Dishwasher\": false, \"Refrigerator\": true}",
            "utilities": "{\"Gas\": true, \"Wifi\": false, \"Trash\": false, \"Water\": true, \"Electricity\": false}",
            "pets_allowed": 0,
            "deposit_for_rent": 0,
            "images": "[]",
            "taxes": null,
            "mortgages": null,
            "owner_first_name": "Owner",
            "owner_last_name": "Test",
            "owner_phone_number": "(800)123-1231",
            "owner_email": "pm@gmail.com",
            "manager_business_name": "IO Management",
            "manager_phone_number": "(800)123-1234",
            "manager_email": "iomanagement@gmail.com",
            "rental_uid": "300-000001",
            "rental_property_id": "200-000001",
            "tenant_id": "100-000003",
            "rent_payments": "[{\"of\": \"Gross Rent\", \"charge\": \"2000\", \"fee_name\": \"Rent\", \"fee_type\": \"$\", \"frequency\": \"Monthly\"}]",
            "lease_start": "2022-02-01",
            "lease_end": "2022-03-01",
            "rental_status": "ACTIVE",
            "tenant_first_name": "Tenant",
            "tenant_last_name": "Test",
            "purchases": "[{\"payer\": \"100-000007\", \"receiver\": \"200-000004\", \"amount_due\": 2000.0, \"amount_paid\": 0.0, \"description\": \"Rent\", \"purchase_uid\": \"400-000010\", \"purchase_type\": \"RENT\", \"purchase_notes\": \"March\", \"pur_property_id\": \"200-000004\", \"purchase_status\": \"UNPAID\"}]"
        }
    ]
}
```

---

### /users

##### GET

- with no args, return all users
- add args to endpoint to filter results (ex: /users?role=TENANT)
- available filters
  - user_uid
  - email
  - role
- response JSON:

```
{
    "message": "Successfully executed SQL query",
    "code": 200,
    "result": [
        {
            "user_uid": "100-000001",
            "first_name": "tenant",
            "last_name": "0225",
            "phone_number": "1231231231",
            "email": "tenant0225@gmail.com",
            "password_salt": "9328247596753792ecf11a77eef415ec7cf5235d389af98771c96819b4128f00",
            "password_hash": "844b08ac3253fdb2a5acade2085bb248eb81e536a9f8cab416913d4b59817ae7",
            "role": "TENANT",
            "created_date": "2022-02-25 16:32:43",
            "google_auth_token": null,
            "google_refresh_token": null,
            "social_id": null,
            "access_expires_in": null,
            "time_zone": null
        }
    ]
}
```

##### POST

- user signup
- request JSON:

```
{
    "first_name": "Owner",
    "last_name": "Test",
    "phone_number": "(800)000-0001",
    "email": "owner@gmail.com",
    "password": "test",
    "role": "OWNER"
}
```

- response JSON (success):

```
{
    "message": "Signup success",
    "code": 200,
    "result": {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTY0NjM3OTM1NywianRpIjoiNmVmZDAyZjYtY2Y5Mi00MWNlLWFhM2YtNjMyODk5ZDAwMmE3IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6eyJ1c2VyX3VpZCI6IjEwMC0wMDAwMDYiLCJmaXJzdF9uYW1lIjoiT3duZXIiLCJsYXN0X25hbWUiOiJUZXN0IiwicGhvbmVfbnVtYmVyIjoiKDEyMyk0NTYtMDAwMSIsImVtYWlsIjoib3duZXJAZ21haWwuY29tIiwicm9sZSI6Ik9XTkVSIiwiZ29vZ2xlX2F1dGhfdG9rZW4iOm51bGwsImJ1c2luZXNzZXMiOltdfSwibmJmIjoxNjQ2Mzc5MzU3LCJleHAiOjE2NDYzODI5NTd9.KWcVAe_OfC6tAHHiySTyFdxhtubnnUXl6Q-acVGR_fU",
        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTY0NjM3OTM1NywianRpIjoiYWViYzU3M2MtNGI4NC00ZGIyLTllZTItNDdhZjUxMTJmZWU2IiwidHlwZSI6InJlZnJlc2giLCJzdWIiOnsidXNlcl91aWQiOiIxMDAtMDAwMDA2IiwiZmlyc3RfbmFtZSI6Ik93bmVyIiwibGFzdF9uYW1lIjoiVGVzdCIsInBob25lX251bWJlciI6IigxMjMpNDU2LTAwMDEiLCJlbWFpbCI6Im93bmVyQGdtYWlsLmNvbSIsInJvbGUiOiJPV05FUiIsImdvb2dsZV9hdXRoX3Rva2VuIjpudWxsLCJidXNpbmVzc2VzIjpbXX0sIm5iZiI6MTY0NjM3OTM1NywiZXhwIjoxNjQ4OTcxMzU3fQ.y6nY70xLH-h6CBK0ES3j942FW9PL2dM05Lr2QAv2dlI",
        "user": {
            "user_uid": "100-000006",
            "first_name": "Owner",
            "last_name": "Test",
            "phone_number": "(123)456-0001",
            "email": "owner@gmail.com",
            "role": "OWNER",
            "google_auth_token": null,
            "businesses": []
        }
    }
}
```

- response JSON (email taken)

```
{
    "message": "Email taken",
    "code": 409
}
```

---

### /login

##### POST

- user login
- request JSON:

```
{
    "email": "owner@gmail.com",
    "password": "test"
}
```

- response JSON (success):

```
{
    "message": "Login successful",
    "code": 200,
    "result": {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTY0NjM3OTM1NywianRpIjoiNmVmZDAyZjYtY2Y5Mi00MWNlLWFhM2YtNjMyODk5ZDAwMmE3IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6eyJ1c2VyX3VpZCI6IjEwMC0wMDAwMDYiLCJmaXJzdF9uYW1lIjoiT3duZXIiLCJsYXN0X25hbWUiOiJUZXN0IiwicGhvbmVfbnVtYmVyIjoiKDEyMyk0NTYtMDAwMSIsImVtYWlsIjoib3duZXJAZ21haWwuY29tIiwicm9sZSI6Ik9XTkVSIiwiZ29vZ2xlX2F1dGhfdG9rZW4iOm51bGwsImJ1c2luZXNzZXMiOltdfSwibmJmIjoxNjQ2Mzc5MzU3LCJleHAiOjE2NDYzODI5NTd9.KWcVAe_OfC6tAHHiySTyFdxhtubnnUXl6Q-acVGR_fU",
        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTY0NjM3OTM1NywianRpIjoiYWViYzU3M2MtNGI4NC00ZGIyLTllZTItNDdhZjUxMTJmZWU2IiwidHlwZSI6InJlZnJlc2giLCJzdWIiOnsidXNlcl91aWQiOiIxMDAtMDAwMDA2IiwiZmlyc3RfbmFtZSI6Ik93bmVyIiwibGFzdF9uYW1lIjoiVGVzdCIsInBob25lX251bWJlciI6IigxMjMpNDU2LTAwMDEiLCJlbWFpbCI6Im93bmVyQGdtYWlsLmNvbSIsInJvbGUiOiJPV05FUiIsImdvb2dsZV9hdXRoX3Rva2VuIjpudWxsLCJidXNpbmVzc2VzIjpbXX0sIm5iZiI6MTY0NjM3OTM1NywiZXhwIjoxNjQ4OTcxMzU3fQ.y6nY70xLH-h6CBK0ES3j942FW9PL2dM05Lr2QAv2dlI",
        "user": {
            "user_uid": "100-000006",
            "first_name": "Owner",
            "last_name": "Test",
            "phone_number": "(123)456-0001",
            "email": "owner@gmail.com",
            "role": "OWNER",
            "google_auth_token": null,
            "businesses": []
        }
    }
}
```

- response JSON (email not found):

```
{
    "message": "Email not found",
    "code": 404
}
```

- response JSON (incorrect password):

```
{
    "message": "Incorrect password",
    "code": 401
}
```

---

### /ownerProfileInfo

##### GET

- requires JWT authorization
- return any owner info for user
- response JSON:

```
{
    "message": "Successfully executed SQL query",
    "code": 200,
    "result": [{
        "owner_id": "100-000001",
        "owner_first_name": "Owner",
        "owner_last_name": "Test",
        "owner_phone_number": "(800)000-0001",
        "owner_email": "owner@gmail.com",
        "owner_ein_number": "00-0000001",
        "owner_ssn": "000-00-0001",
        "owner_paypal": "owner@gmail.com",
        "owner_apple_pay": "(800)000-0001",
        "owner_zelle": "owner@gmail.com",
        "owner_venmo": "NULL",
        "owner_account_number": "NULL",
        "owner_routing_number": "NULL"
    }]
}
```

##### POST

- create new owner info
- requires JWT authorization
- request JSON:

```
{
    "first_name": "Owner",
    "last_name": "Test",
    "phone_number": "(800)000-0001",
    "email": "owner@gmail.com",
    "ein_number": "00-0000001",
    "ssn": "000-00-0001",
    "paypal": "owner@gmail.com",
    "apple_pay": "(800)000-0001",
    "zelle": "owner@gmail.com",
    "venmo": "NULL",
    "account_number": "NULL",
    "routing_number": "NULL"
}
```

- response JSON:

```
{
    "message": "Successfully committed SQL query",
    "code": 200
}
```

##### PUT

- update owner info
- requires JWT authorization
- request JSON:

```
{
    "first_name": "Owner",
    "last_name": "Test",
    "phone_number": "(800)000-0001",
    "email": "owner@gmail.com",
    "ein_number": "00-0000001",
    "ssn": "000-00-0001",
    "paypal": "owner@gmail.com",
    "apple_pay": "(800)000-0001",
    "zelle": "owner@gmail.com",
    "venmo": "NULL",
    "account_number": "NULL",
    "routing_number": "NULL"
}
```

- response JSON:

```
{
    "message": "Successfully committed SQL query",
    "code": 200
}
```

---

### /managerProfileInfo \*\*\* deprecated, use /businesses or /employees

##### GET

- requires JWT authorization
- return any manager info for user
- response JSON:

```
{
    "message": "Successfully executed SQL query",
    "code": 200,
    "result": [{
        "manager_id": "100-000002",
        "manager_first_name": "Manager",
        "manager_last_name": "Test",
        "manager_phone_number": "(800)000-0002",
        "manager_email": "manager@gmail.com",
        "manager_ein_number": "00-0000002",
        "manager_ssn": "000-00-0002",
        "manager_paypal": "manager@gmail.com",
        "manager_apple_pay": "NULL",
        "manager_zelle": "NULL",
        "manager_venmo": "manager@gmail.com",
        "manager_account_number": "1000000002",
        "manager_routing_number": "200000002",
        "manager_fees": "[{\"of\": \"Gross Rent\", \"charge\": \"10%\", \"fee_name\": \"Service Charge\", \"fee_type\": \"%\", \"frequency\": \"Monthly\"}]",
        "manager_locations": "[{\"city\": \"Pasadena\", \"state\": \"CA\", \"distance\": 5}]"
    }]
}
```

##### POST

- create new manager info
- requires JWT authorization
- request JSON:

```
{
    "first_name": "Manager",
    "last_name": "Test",
    "phone_number": "(800)000-0002",
    "email": "manager@gmail.com",
    "ein_number": "00-0000002",
    "ssn": "000-00-0002",
    "paypal": "manager@gmail.com",
    "apple_pay": "NULL",
    "zelle": "NULL",
    "venmo": "manager@gmail.com",
    "account_number": "1000000002",
    "routing_number": "200000002",
    "fees": [
      {
        "fee_name": "Service Charge",
        "fee_type": "%",
        "charge": "10%",
        "of": "Gross Rent",
        "frequency": "Monthly"
      }
    ],
    "locations": [
      {
        "city": "Pasadena",
        "state": "CA",
        "distance": 5
      }
    ]
}
```

- response JSON:

```
{
    "message": "Successfully committed SQL query",
    "code": 200
}
```

##### PUT

- update manager info
- requires JWT authorization
- request JSON:

```
{
    "first_name": "Manager",
    "last_name": "Test",
    "phone_number": "(800)000-0002",
    "email": "manager@gmail.com",
    "ein_number": "00-0000002",
    "ssn": "000-00-0002",
    "paypal": "manager@gmail.com",
    "apple_pay": "NULL",
    "zelle": "NULL",
    "venmo": "manager@gmail.com",
    "account_number": "1000000002",
    "routing_number": "200000002",
    "fees": [
      {
        "fee_name": "Service Charge",
        "fee_type": "%",
        "charge": "10%",
        "of": "Gross Rent",
        "frequency": "Monthly"
      }
    ],
    "locations": [
      {
        "city": "Pasadena",
        "state": "CA",
        "distance": 5
      }
    ]
}
```

- response JSON:

```
{
    "message": "Successfully committed SQL query",
    "code": 200
}
```

---

### /tenantProfileInfo

##### GET

- requires JWT authorization
- return any tenant info for user
- response JSON:

```
{
    "message": "Successfully executed SQL query",
    "code": 200,
    "result": [{
        "tenant_id": "100-000014",
        "tenant_first_name": "Tenant",
        "tenant_last_name": "Test",
        "tenant_ssn": "123-45-6789",
        "tenant_current_salary": "75000",
        "tenant_salary_frequency": "Annual",
        "tenant_current_job_title": "Software Engineer",
        "tenant_current_job_company": "Infinite Options",
        "tenant_drivers_license_number": "123456789",
        "tenant_drivers_license_state": "CA",
        "tenant_current_address": "{\"zip\": \"95120\", \"city\": \"San Jose\", \"rent\": \"\", \"unit\": \"\", \"state\": \"CA\", \"street\": \"101 Main St\", \"pm_name\": \"\", \"lease_end\": \"\", \"pm_number\": \"\", \"lease_start\": \"\"}",
        "tenant_previous_address": "null",
        "documents": "[{\"link\": \"https://s3-us-west-1.amazonaws.com/io-pm/tenants/100-000014/doc_0\", \"name\": \"Resume\", \"description\": \"document description\"}]"
    }]
}
```

##### POST

- create new tenant info
- requires JWT authorization
- send as multipart/form-data
- include document files as doc_0, doc_1...
- include documents array to supply name, description for files
- request JSON:

```
{
    "first_name": "Tenant",
    "last_name": "Test",
    "ssn": "000-00-0003",
    "drivers_license_number": "A0000003",
    "drivers_license_state": "CA",
    "current_salary": 75000,
    "salary_frequency": "Annually",
    "current_job_title": "Software Engineer",
    "current_job_company": "Infinite Options",
    "current_address": {
      "street": "123 Main St",
      "unit": "",
      "city": "San Jose",
      "state": "CA",
      "zip": "95120",
      "pm_name": "Manager Test",
      "pm_number": "00-0000002",
      "lease_start": "6/19",
      "lease_end": "1/22",
      "rent": 1800
    },
    "previous_address": [],
    "doc_0": "",
    "documents": [
      {
        "name": "Resume",
        "description": "My resume"
      }
    ]
}
```

- response JSON:

```
{
    "message": "Successfully committed SQL query",
    "code": 200
}
```

##### PUT

- update tenant info
- requires JWT authorization
- send as multipart/form-data
- include document files or links as doc_0, doc_1...
- include documents array to supply name, description for files
- request JSON:

```
{
    "first_name": "Tenant",
    "last_name": "Test",
    "ssn": "000-00-0003",
    "drivers_license_number": "A0000003",
    "drivers_license_state": "CA",
    "current_salary": 75000,
    "salary_frequency": "Annually",
    "current_job_title": "Software Engineer",
    "current_job_company": "Infinite Options",
    "current_address": {
      "street": "123 Main St",
      "unit": "",
      "city": "San Jose",
      "state": "CA",
      "zip": "95120",
      "pm_name": "Manager Test",
      "pm_number": "00-0000002",
      "lease_start": "6/19",
      "lease_end": "1/22",
      "rent": 1800
    },
    "previous_address": [],
    "doc_0": "",
    "documents": [
      {
        "name": "Resume",
        "description": "My resume"
      }
    ]
}
```

- response JSON:

```
{
    "message": "Successfully committed SQL query",
    "code": 200
}
```

---

### /businessProfileInfo \*\*\* deprecated, use /businesses or /employees

##### GET

- requires JWT authorization
- return any business info for user
- response JSON:

```
{
    "message": "Successfully executed SQL query",
    "code": 200,
    "result": [{
        "business_id": "100-000004",
        "business_name": "Hector's Plumbing",
        "business_ein_number": "00-0000004",
        "business_paypal": "NULL",
        "business_apple_pay": "NULL",
        "business_zelle": "NULL",
        "business_venmo": "NULL",
        "business_account_number": "1000000004",
        "business_routing_number": "200000004",
        "business_services": "[{\"per\": \"hour\", \"charge\": 75, \"service_name\": \"Toilet Plumbing\"}]",
        "business_contact": "[{\"email\": \"pm@gmail.com\", \"last_name\": \"Doe\", \"first_name\": \"John\", \"company_role\": \"Accounting\", \"phone_number\": \"(789)908-9087\"}]"
    }]
}
```

##### POST

- create new business info
- requires JWT authorization
- request JSON:

```
{
    "name": "Hector's Plumbing",
    "ein_number": "00-0000004",
    "paypal": "NULL",
    "apple_pay": "NULL",
    "zelle": "NULL",
    "venmo": "NULL",
    "account_number": "1000000004",
    "routing_number": "200000004",
    "services": [
      {
        "service_name": "Toilet Plumbing",
        "charge": 75,
        "per": "hour"
      }
    ],
    "contact": [
      {
        "first_name": "John",
        "last_name": "Doe",
        "company_role": "Accounting",
        "phone_number": "(789)908-9087",
        "email": "pm@gmail.com"
      }
    ]
}
```

- response JSON:

```
{
    "message": "Successfully committed SQL query",
    "code": 200
}
```

##### PUT

- update business info
- requires JWT authorization
- request JSON:

```
{
    "name": "Hector's Plumbing",
    "ein_number": "00-0000004",
    "paypal": "NULL",
    "apple_pay": "NULL",
    "zelle": "NULL",
    "venmo": "NULL",
    "account_number": "1000000004",
    "routing_number": "200000004",
    "services": [
      {
        "service_name": "Toilet Plumbing",
        "charge": 75,
        "per": "hour"
      }
    ],
    "contact": [
      {
        "first_name": "John",
        "last_name": "Doe",
        "company_role": "Accounting",
        "phone_number": "(789)908-9087",
        "email": "pm@gmail.com"
      }
    ]
}
```

- response JSON:

```
{
    "message": "Successfully committed SQL query",
    "code": 200
}
```

---

### /rentals

##### GET

- with no args, return all rentals
- add args to endpoint to filter results (ex: /rentals?property_id=200-000001)
- available filters
  - rental_uid
  - rental_property_id
  - tenant_id
  - rental_status
- response JSON:

```
{
    "message": "Successfully executed SQL query",
    "code": 200,
    "result": [
        {
            "rental_uid": "300-000001",
            "rental_property_id": "200-000001",
            "tenant_id": "100-000003",
            "actual_rent": 1800,
            "lease_start": "2022-02-01",
            "lease_end": "2022-03-01",
            "rental_status": "ACTIVE",
            "rent_payments": "[{\"of\": \"Gross Rent\", \"charge\": \"1800\", \"fee_name\": \"Monthly Rent\", \"fee_type\": \"$\", \"frequency\": \"Monthly\"}]",
            "assigned_contacts": "[{\"email\": \"pm@gmail.com\", \"last_name\": \"Test\", \"first_name\": \"Manager\", \"company_role\": \"Owner\", \"phone_number\": \"(800)123-1231\"}]",
            "documents": "[]"
        }
    ]
}
```

##### POST

- create new rental
- send as multipart/form-data
- include document files as doc_0, doc_1...
- include documents array to supply name, description for files
- request JSON:

```
{
  "rental_property_id": "200-000001",
  "tenant_id": "100-000003",
  "actual_rent": "1800",
  "lease_start": "2022-02-01",
  "lease_end": "2022-03-01",
  "rent_payments": [{
    "fee_name": "Monthly Rent",
    "fee_type": "$",
    "charge": 100,
    "of": "",
    "frequency": "Monthly"
  }],
  "assigned_contacts": [{
    "first_name": "Greg",
    "last_name": "Brewer",
    "company_role": "Manager",
    "phone_number": "(789)908-9087",
    "email": "greg@beverlyman.com"
  }],
  "rental_status":"PENDING",
  "doc_0": "",
  "documents": [
    {
      "name": "Resume",
      "description": "My resume"
    }
  ]
}
```

- response JSON:

```
{
    "message": "Successfully committed SQL query",
    "code": 200
}
```

##### PUT

- update rental
- send as multipart/form-data
- include document files or links as doc_0, doc_1...
- include documents array to supply name, description for files
- request JSON:

```
{
  "rental_uid": "300-000001",
  "actual_rent": "1800",
  "lease_start": "2022-02-01",
  "lease_end": "2023-02-01",
  "rent_payments": [{
    "fee_name": "Monthly Rent",
    "fee_type": "$",
    "charge": 100,
    "of": "",
    "frequency": "Monthly"
  }],
  "assigned_contacts": [{
    "first_name": "Greg",
    "last_name": "Brewer",
    "company_role": "Manager",
    "phone_number": "(789)908-9087",
    "email": "greg@beverlyman.com"
  }],
  "doc_0": "",
  "rental_status":"PENDING",
  "documents": [
    {
      "name": "Resume",
      "description": "My resume"
    }
  ]
}
```

- response JSON:

```
{
    "message": "Successfully committed SQL query",
    "code": 200
}
```

- request JSON(tenants accepts/rejects lease updating rental_status)

```
{
    "rental_uid":"300-000018",
    "rental_status":"PROCESSING"
}
```

---

### /contracts

##### GET

- with no args, return all contracts
- add args to endpoint to filter results (ex: /contracts?business_uid=600-000001)
- available filters
  - contract_uid
  - property_uid
  - business_uid
- response JSON:

```
{
    "message": "Successfully executed SQL query",
    "code": 200,
    "result": [
        {
            "contract_uid": "010-000003",
            "property_uid": "200-000001",
            "business_uid": "600-000001",
            "start_date": "2021-12-31",
            "end_date": "2022-03-01",
            "contract_fees": "[{\"of\": \"Gross Rent\", \"charge\": \"10\", \"fee_name\": \"Charge\", \"fee_type\": \"%\", \"frequency\": \"Weekly\"}]",
            "assigned_contacts": "[{\"email\": \"zacharywolfflind@gmail.com\", \"last_name\": \"Lind\", \"first_name\": \"Zach\", \"company_role\": \"CEO\", \"phone_number\": \"(925)984-0473\"}]",
            "documents": "[\"https://s3-us-west-1.amazonaws.com/io-pm/contracts/010-000003/doc_0\"]"
        }
    ]
}
```

##### POST

- create new contract
- send as multipart/form-data
- include document files as doc_0, doc_1...
- include documents array to supply name, description for files
- request JSON:

```
{
  "property_uid": "200-000001",
  "business_uid": "600-000001",
  "start_date": "1/22",
  "end_date": "1/23",
  "contract_fees": [{
    "title": "Monthly Rent",
    "charge_type": "$",
    "charge": 100,
    "frequency": "One-time"
  }],
  "assigned_contacts": [{
    "first_name": "Greg",
    "last_name": "Brewer",
    "company_role": "Manager",
    "phone_number": "(789)908-9087",
    "email": "greg@beverlyman.com"
  }],
  "doc_0": "",
  "documents": [
    {
      "name": "Resume",
      "description": "My resume"
    }
  ]
}
```

- response JSON:

```
{
    "message": "Successfully committed SQL query",
    "code": 200
}
```

##### PUT

- update contract
- send as multipart/form-data
- include document files or links as doc_0, doc_1...
- include documents array to supply name, description for files
- request JSON:

```
{
  "contract_uid": "010-000001",
  "property_uid": "200-000001",
  "business_uid": "600-000001",
  "start_date": "1/22",
  "end_date": "1/23",
  "contract_fees": [{
    "title": "Monthly Rent",
    "charge_type": "$",
    "charge": 100,
    "frequency": "One-time"
  }],
  "assigned_contacts": [{
    "first_name": "Greg",
    "last_name": "Brewer",
    "company_role": "Manager",
    "phone_number": "(789)908-9087",
    "email": "greg@beverlyman.com"
  }],
  "doc_0": "",
  "documents": [
    {
      "name": "Resume",
      "description": "My resume"
    }
  ]
}
```

- response JSON:

```
{
    "message": "Successfully committed SQL query",
    "code": 200
}
```

---

### /purchases

##### GET

- with no args, return all purchases
- add args to endpoint to filter results (ex: /purchases?linked_property_id=200-000001)
- available filters
  - purchase_uid
  - linked_purchase_id
  - pur_property_id
  - payer
  - receiver
- response JSON:

```
{
    "message": "Successfully executed SQL query",
    "code": 200,
    "result": [{
        "purchase_uid": "400-000001",
        "linked_purchase_id": null,
        "pur_property_id": "200-000001",
        "payer": "100-000001",
        "receiver": "200-000001",
        "purchase_type": "RENT",
        "description": "Rent",
        "amount_due": 2000.0,
        "amount_paid": 2000.0,
        "purchase_notes": "March",
        "purchase_date": "2022-03-04 00:00:00",
        "purchase_frequency": "Monthly",
        "purchase_status": "PAID"
    }]
}
```

##### POST

- create new purchase
- request JSON:

```
{
    "linked_purchase_id": null,
    "pur_property_id": "200-000001",
    "payer": "100-000003",
    "receiver": "100-000001",
    "purchase_type": "RENT",
    "description": "Rent for January 2022",
    "amount_due": "1800",
    "purchase_notes": "First month's rent",
    "purchase_date": "2022-03-04 00:00:00",
    "purchase_frequency": "Monthly"
}
```

- response JSON:

```
{
    "message": "Successfully committed SQL query",
    "code": 200
}
```

---

### /payments

##### GET

- with no args, return all payments
- add args to endpoint to filter results (ex: /payments?pay_purchase_id=400-000001)
- available filters
  - payment_uid
  - pay_purchase_id
- response JSON:

```
{
    "message": "Successfully executed SQL query",
    "code": 200,
    "result": [{
        "payment_uid": "500-000001",
        "pay_purchase_id": "400-000001",
        "amount": 2000.0,
        "payment_notes": "M4METEST",
        "charge_id": "pi_3KTMYpLMju5RPMEv0zFXZoFK",
        "payment_type": "STRIPE",
        "payment_date": "2022-01-10 16:05:29"
    }]
}
```

##### POST

- create new payment
- request JSON:

```
{
    "pay_purchase_id": "400-000001",
    "amount": 1800,
    "payment_notes": "M4METEST",
    "payment_type": "STRIPE",
    "charge_id": "pi_3KTMYpLMju5RPMEv0zFXZoFK"
}
```

- response JSON:

```
{
    "message": "Successfully committed SQL query",
    "code": 200
}
```

---

### /businesses

##### GET

- with no args, return all businesses
- add args to endpoint to filter results (ex: /businesses?business_type=MANAGEMENT)
- available filters
  - business_uid
  - business_type
  - business_name
- response JSON:

```
{
    "message": "Successfully executed SQL query",
    "code": 200,
    "result": [{
        "business_uid": "600-000016",
        "business_type": "MAINTENANCE",
        "business_name": "Maintenance 225",
        "business_phone_number": "(123)456-0225",
        "business_email": "maintenance225@gmail.com",
        "business_ein_number": "12-2252252",
        "business_services_fees": "[{\"per\": \"Hour\", \"charge\": \"20\", \"service_name\": \"Plumbing\"}]",
        "business_locations": "[{\"distance\": \"5\", \"location\": \"San Jose, CA\"}]",
        "business_paypal": "maintenance225@gmail.com",
        "business_apple_pay": null,
        "business_zelle": null,
        "business_venmo": null,
        "business_account_number": null,
        "business_routing_number": null
    }]
}
```

##### POST

- create new business
- request JSON (MANAGEMENT):

```
{
    "type": "MANAGEMENT",
    "name": "Infinite Options",
    "phone_number": "(800)123-1234",
    "email": "iomanagement@gmail.com",
    "ein_number": "12-1234567",
    "services_fees": [{
        "name": "Service Charge",
        "type": "%",
        "charge": 10,
        "of": "Gross Rent",
        "frequency": "Monthly"
    }],
    "locations": [{
      "location": "San Jose, CA"
      "distance": 5,
    }],
    "paypal": "maintenance225@gmail.com",
    "apple_pay": null,
    "zelle": null,
    "venmo": null,
    "account_number": null,
    "routing_number": null
}
```

- request JSON (MAINTENANCE):

```
{
    "type": "MAINTENANCE",
    "name": "Water Works",
    "phone_number": "(800)123-8000",
    "email": "waterworks@gmail.com",
    "ein_number": "12-8888888",
    "services_fees": [{
        "name": "Toilet Plumbing",
        "type": "$",
        "charge": 75,
        "of": "",
        "frequency": "Hourly"
    }],
    "locations": [{
      "location": "San Jose, CA"
      "distance": 5,
    }],
    "paypal": "waterworks@gmail.com",
    "apple_pay": null,
    "zelle": null,
    "venmo": null,
    "account_number": null,
    "routing_number": null
}
```

- response JSON:

```
{
    "message": "Successfully committed SQL query",
    "code": 200
}
```

##### PUT

- update business
- request JSON:

```
{
    "business_uid": "600-000001",
    "type": "MANAGEMENT",
    "name": "Infinite Options",
    "phone_number": "(800)123-1234",
    "email": "iomanagement@gmail.com",
    "ein_number": "12-1234567",
    "services_fees": [{
        "name": "Service Charge",
        "type": "%",
        "charge": 10,
        "of": "Gross Rent",
        "frequency": "Monthly"
    }],
    "locations": [{
      "location": "San Jose, CA"
      "distance": 5,
    }],
    "paypal": "maintenance225@gmail.com",
    "apple_pay": null,
    "zelle": null,
    "venmo": null,
    "account_number": null,
    "routing_number": null
}
```

- response JSON:

```
{
    "message": "Successfully committed SQL query",
    "code": 200
}
```

---

### /employees

##### GET

- with no args, return all employees
- add args to endpoint to filter results (ex: /businessAssociations?business_uid=700-0000001)
- available filters
  - employee_uid
  - user_uid
  - business_uid
  - employee_role
- response JSON:

```
{
    "message": "Successfully executed SQL query",
    "code": 200,
    "result": [{
        "employee_uid": "700-000001",
        "user_uid": "100-000001",
        "business_uid": "600-000001",
        "employee_role": "Accountant",
        "employee_first_name": "John",
        "employee_last_name": "Doe",
        "employee_phone_number": "(789)908-9087",
        "employee_email": "pm@gmail.com",
        "employee_ssn": "131-89-1839",
        "employee_ein_number": "12-1313131"
    }]
}
```

##### POST

- create new employee
- request JSON:

```
{
    "user_uid": "100-000001",
    "business_uid": "600-000001",
    "role": "Accountant",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "(789)908-9087",
    "email": "pm@gmail.com",
    "ssn": "131-89-1839",
    "ein_number": "12-1313131"
}
```

- response JSON:

```
{
    "message": "Successfully committed SQL query",
    "code": 200
}
```

##### PUT

- update employee
- request JSON:

```
{
    "employee_uid": "700-000001",
    "user_uid": "100-000001",
    "business_uid": "600-000001",
    "role": "Accountant",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "(789)908-9087",
    "email": "pm@gmail.com",
    "ssn": "131-89-1839",
    "ein_number": "12-1313131"
}
```

- response JSON:

```
{
    "message": "Successfully committed SQL query",
    "code": 200
}
```

---

### /maintenanceRequests

##### GET

- with no args, return all maintenance requests
- add args to endpoint to filter results (ex: /maintenanceRequests?property_uid=200-0000001)
- available filters
  - maintenance_request_uid
  - property_uid
  - priority
  - assigned_business
  - assigned_worker
  - request_status
- response JSON:

```
{
    "message": "Successfully executed SQL query",
    "code": 200,
    "result": [{
        "maintenance_request_uid": "800-000001",
        "property_uid": "200-000001",
        "title": "Paint",
        "description": "Living room ",
        "images": "[\"https://s3-us-west-1.amazonaws.com/io-pm/maintenanceRequests/800-000001/img_0\"]",
        "priority": "High",
        "can_reschedule": 0,
        "assigned_business": "600-000016",
        "assigned_worker": null,
        "scheduled_date": null,
        "frequency": "One time",
        "notes": null,
        "request_status": "PROCESSING",
        "request_created_date": "2022-02-25 16:58:49"
    }]
}
```

##### POST

- create new maintenance request
- send as multipart/form-data
- include image files as img_0, img_1...
- request JSON:

```
{
    "property_uid": "200-000001",
    "title": "Bathroom Leaking",
    "description": "The toilet plumbing is leaking at the base",
    "priority": "High",
    "img_0": "",
    "img_1": ""
}
```

- response JSON:

```
{
    "message": "Successfully committed SQL query",
    "code": 200
}
```

##### PUT

- update maintenance request
- send as multipart/form-data
- include image files or links as img_0, img_1...
- request JSON:

```
{
    "maintenance_request_uid": "800-000001",
    "title": "Bathroom Leaking",
    "description": "The toilet plumbing is leaking at the base",
    "priority": "High",
    "can_reschedule": true
    "assigned_business": "600-000001",
    "assigned_worker": "700-000005",
    "scheduled_date": "2022-03-06",
    "request_status": "SCHEDULED",
    "notes": "",
    "img_0": "",
    "img_1": "",
}
```

- response JSON:

```
{
    "message": "Successfully committed SQL query",
    "code": 200
}
```

---

### /maintenanceQuotes

##### GET

- with no args, return all maintenance quotes (joined with requests and businesses)
- add args to endpoint to filter results (ex: /maintenanceQuotes?status=REQUESTED)
- available filters
  - maintenance_quote_uid
  - linked_request_uid
  - quote_business_uid
  - quote_status
- response JSON:

```
{
    "message": "Successfully executed SQL query",
    "code": 200,
    "result": [{
            "maintenance_quote_uid": "900-000001",
            "linked_request_uid": "800-000001",
            "quote_business_uid": "600-000001",
            "services_expenses": "[{\"fees\": 30, \"payment_term\": \"One-time cost\", \"service_notes\": \"Sealing base - labor cost\"}]",
            "earliest_availability": "2022-01-03 00:00:00",
            "event_type": "2 hour job",
            "notes": null,
            "quote_status": "SENT",
            "quote_created_date": "2022-02-23 06:12:38",
            "maintenance_request_uid": "800-000001",
            "property_uid": "200-000001",
            "title": "Bathroom Leaking",
            "description": "The toilet plumbing is leaking at the base",
            "images": "[\"https://s3-us-west-1.amazonaws.com/io-pm/maintenanceRequests/800-000005/img_0\", \"https://s3-us-west-1.amazonaws.com/io-pm/maintenanceRequests/800-000005/img_0\", \"https://s3-us-west-1.amazonaws.com/io-pm/maintenanceRequests/800-000005/img_0\", \"https://s3-us-west-1.amazonaws.com/io-pm/maintenanceRequests/800-000005/img_0\", \"https://s3-us-west-1.amazonaws.com/io-pm/maintenanceRequests/800-000005/img_0\"]",
            "priority": "High",
            "can_reschedule": 1,
            "assigned_business": null,
            "assigned_worker": null,
            "scheduled_date": null,
            "frequency": "One time",
            "request.notes": null,
            "request_status": "COMPLETE",
            "request_created_date": "2022-02-23 06:12:14",
            "business_uid": "600-000001",
            "business_type": "MANAGEMENT",
            "business_name": "IO Management",
            "business_phone_number": "(800)123-1234",
            "business_email": "iomanagement@gmail.com",
            "business_ein_number": "12-1234567",
            "business_services_fees": "[{\"of\": \"Gross Rent\", \"name\": \"Service Charge\", \"type\": \"%\", \"charge\": 10, \"frequency\": \"Monthly\"}]",
            "business_locations": null,
            "business_paypal": null,
            "business_apple_pay": null,
            "business_zelle": null,
            "business_venmo": null,
            "business_account_number": null,
            "business_routing_number": null
        }
    ]
}
```

##### POST

- create new maintenance quote
- request JSON (manager requests quote from business):

```
{
    "linked_request_uid": "800-000001",
    "quote_business_uid": "600-000001"
}
```

- request JSON (multiple businesses)

```
{
    "linked_request_uid": "800-000001",
    "quote_business_uid": ["600-000001", "600-000002"]
}
```

- response JSON:

```
{
    "message": "Successfully committed SQL query",
    "code": 200
}
```

##### PUT

- update maintenance quote
- request JSON (maintenance sends quote):

```
{
    "maintenance_quote_uid": "900-000001",
    "services_expenses": [{
      "service_notes": "Sealing base - labor cost",
      "fees": 30,
      "payment_term": "One-time cost"
    }],
    "earliest_availability": "2022-01-03",
    "event_type": "2 hour job",
    "quote_status": "SENT"
}
```

- request JSON (maintenance refuses quote):

```
{
    "maintenance_quote_uid": "900-000001",
    "quote_status": "REFUSED",
    "notes": "No availability"
}
```

- request JSON (manager rejects quote):

```
{
    "maintenance_quote_uid": "900-000001",
    "quote_status": "REJECTED",
    "notes": "Price too high"
}
```

- request JSON (manager accepts quote):

```
{
    "maintenance_quote_uid": "900-000001",
    "quote_status": "ACCEPTED"
}
```

- response JSON:

```
{
    "message": "Successfully committed SQL query",
    "code": 200
}
```

---

### /applications

##### GET

- with no args, return all applications
- add args to endpoint to filter results (ex: /applications?tenant_id=100-000001)
- available filters
  - application_uid
  - property_uid
  - tenant_id
- response JSON:

```
{
    "message": "Successfully executed SQL query",
    "code": 200,
    "result": [{
        "application_uid": "020-000001",
        "property_uid": "200-000021",
        "tenant_id": "100-000003",
        "message": "Can I please rent this apartment",
        "application_status": "NEW",
        "application_date": "2022-02-22 07:36:40"
    }]
}
```

##### POST

- create new application
- requires JWT authorization
- request JSON:

```
{
    "property_uid": "200-000001",
    "message": "I would love to rent this apartment"
}
```

- response JSON:

```
{
    "message": "Successfully committed SQL query",
    "code": 200
}
```

##### PUT

- update application
- request JSON:

```
{
    "application_uid": "020-000001",
    "message": "Sorry, the apartment is no longer available",
    "application_status": "REJECTED"
}
```

- response JSON:

```
{
    "message": "Successfully committed SQL query",
    "code": 200
}
```

---

### /leaseTenants

##### GET

- with no args, return all leaseTenants
- add args to endpoint to filter results (ex: /leaseTenants?linked_tenant_id=100-000001)
- available filters
  - linked_tenant_id
- response JSON:

```
{
    "message": "Successfully executed SQL query",
    "code": 200,
    "result": [
        {
            "linked_tenant_id": "100-000001",
            "rental_uid": "300-000001",
            "rental_property_id": "200-000001",
            "tenant_id": "100-000001",
            "actual_rent": null,
            "lease_start": "2022-03-04",
            "lease_end": "2022-11-21",
            "rental_status": "ACTIVE",
            "rent_payments": "[{\"of\": \"Gross Rent\", \"charge\": \"2000\", \"fee_name\": \"Rent\", \"fee_type\": \"$\", \"frequency\": \"Monthly\"}]",
            "assigned_contacts": "[]",
            "documents": "[]"
        },
        {
            "linked_tenant_id": "100-000001",
            "rental_uid": "300-000003",
            "rental_property_id": "200-000003",
            "tenant_id": "",
            "actual_rent": null,
            "lease_start": "2022-02-01",
            "lease_end": "2022-03-01",
            "rental_status": "ACTIVE",
            "rent_payments": "[{\"of\": \"\", \"charge\": 1800, \"fee_name\": \"Monthly Rent\", \"fee_type\": \"$\", \"frequency\": \"Monthly\"}]",
            "assigned_contacts": "[]",
            "documents": "[]"
        }
    ]
}
```
