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
- [/propertiesOwner](#propertiesOwner)
- [/propertiesOwnerDetails](#propertiesOwnerDetails)
- [/propertyInfo](#propertyinfo)
- [/users](#users)
- [/UpdateAccessToken](#UpdateAccessToken/{user_id})
- [/UserDetails](#UserDetails/{user_id})
- [/UserToken](#UserToken/{user_email_id})
- [/login](#login)
- [/ownerProfileInfo](#ownerprofileinfo)
- [/managerProfileInfo](#managerprofileinfo)
- [/tenantProfileInfo](#tenantprofileinfo)
- [/businessProfileInfo](#businessprofileinfo)
- [/rentals](#rentals)
- [/endLease](#endLease)
- [/purchases](#purchases)
- [/createExpenses](#createExpenses)
- [/payments](#payments)
- [/businesses](#businesses)
- [/employees](#employees)
- [/maintenanceRequests](#maintenanceRequests)
- [/maintenanceQuotes](#maintenanceQuotes)
- [/applications](#applications)
- [/leaseTenants](#leaseTenants)
- [/availableProperties/{tenant_id}](#availableProperties/{tenant_id})
- [/maintenanceRequestsandQuotes](#maintenanceRequestsandQuotes)
- [/AvailableAppointmentsTenant](#AvailableAppointmentsTenant/{date_value}/{duration}/{user_id}/{start_time},{end_time})
- [/AvailableAppointmentsMaintenance](#AvailableAppointmentsMaintenance/{date_value}/{duration}/{user_id}/{start_time},{end_time})
- [/bills](#bills)

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

##### PUT

- user signup update add another role
- request JSON:

```
{
    "email": "owner@gmail.com",
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
    "phone_number":"1234567890",
    "email":"test@gmail.com",
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
    "phone_number":"1234567890",
    "email":"test@gmail.com",
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

### /endLease

##### PUT

- pm/tenant ends the lease
- updating rental_status in rentals to 'EXPIRED' and deleting future rents from PURCHASES
- send as multipart/form-data

- request JSON:

```
{
    "rental_uid": "300-000020",
    "rental_status": "EXPIRED",
    "rental_property_id":"200-000023"
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

### /contracts

##### GET

- with no args, return all contracts
- add args to endpoint to filter results (ex: /contracts?business_uid=600-000001)
- available filters
  - contract_uid
  - property_uid
  - business_uid
  - contract_name
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
  "contract_name": "",
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
  "contract_name": "",
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

### /createExpenses

##### POST

- create new expense from owner profile
- request JSON:

```
{
    "pur_property_id": "200-000023",
    "payer": "100-000006",
    "receiver": "200-000023",
    "purchase_type": "Maintenance",
    "description": "mortgage insurance",
    "amount_due": "180",
    "purchase_frequency": "Monthly",
    "payment_frequency": "Once a month",
    "next_payment": "2022-06-03"
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
  - request_created_by
  - request_type
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
        "scheduled_time": null,
        "frequency": "One time",
        "notes": null,
        "request_status": "PROCESSING",
        "request_created_date": "2022-02-25 16:58:49"
        "request_created_by":"100-000001",
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
    "request_created_by": "100-000001",
    "request_type":"REPAIR/MAINTENANCE",
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
    "scheduled_time": null,
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
    "result": [
        {
            "maintenance_quote_uid": "900-000006",
            "linked_request_uid": "800-000006",
            "quote_business_uid": "600-000005",
            "services_expenses": null,
            "earliest_availability": null,
            "event_type": null,
            'event_duration':null,
            "notes": null,
            "quote_status": "REQUESTED",
            "quote_created_date": "2022-05-02 16:35:27",
            "maintenance_request_uid": "800-000006",
            "property_uid": "200-000012",
            "title": "Toilet Clogged",
            "description": "Can't flush toilet",
            "images": "[\"https://s3-us-west-1.amazonaws.com/io-pm/maintenanceRequests/800-000006/img_0\"]",
            "request_type": null,
            "request_created_by": null,
            "priority": "High",
            "can_reschedule": 0,
            "assigned_business": null,
            "assigned_worker": null,
            "scheduled_date": null,
            "scheduled_time": null,
            "frequency": "One time",
            "mr.notes": null,
            "request_status": "PROCESSING",
            "request_created_date": "2022-05-02 16:20:41",
            "request_created_by":"100-000001",
            "business_uid": "600-000005",
            "business_type": "MAINTENANCE",
            "business_name": "Property Services 0422",
            "business_phone_number": "1231231231",
            "business_email": "maintainance0422@gmail.com",
            "business_ein_number": "12-12312322",
            "business_services_fees": "[{\"per\": \"hour\", \"charge\": \"50\", \"service_name\": \"Toilet Plumbing\"}, {\"per\": \"hour\", \"charge\": \"30\", \"service_name\": \"Kitchen Plumbing\"}]",
            "business_locations": "[{\"distance\": \"10\", \"location\": \"Santa Clara \"}]",
            "business_paypal": "maintainance0422@gmail.com",
            "business_apple_pay": null,
            "business_zelle": null,
            "business_venmo": null,
            "business_account_number": null,
            "business_routing_number": null,
            "p.property_uid": "200-000012",
            "owner_id": "100-000006",
            "manager_id": "",
            "address": "122 JKL Street",
            "unit": "",
            "city": "Bellflower",
            "state": "CA",
            "zip": "90706",
            "property_type": "Townhome",
            "num_beds": 3.0,
            "num_baths": 2.0,
            "area": 1700,
            "listed_rent": 3000,
            "deposit": 2000,
            "appliances": "{\"Dryer\": false, \"Range\": true, \"Washer\": false, \"Microwave\": true, \"Dishwasher\": true, \"Refrigerator\": false}",
            "utilities": "{\"Gas\": false, \"Wifi\": false, \"Trash\": true, \"Water\": true, \"Electricity\": false}",
            "pets_allowed": 1,
            "deposit_for_rent": 1,
            "p.images": "[\"https://s3-us-west-1.amazonaws.com/io-pm/properties/200-000012/img_cover\"]",
            "taxes": null,
            "mortgages": null,
            "linked_property_id": "200-000012",
            "linked_business_id": "600-000001",
            "linked_employee_id": null,
            "management_status": "ACCEPTED",
            "rentalInfo": [
                {
                    "rental_uid": "300-000010",
                    "rental_property_id": "200-000012",
                    "rent_payments": "[{\"of\": \"Gross Rent\", \"charge\": \"2000\", \"fee_name\": \"Deposit\", \"fee_type\": \"$\", \"frequency\": \"One-time\"}, {\"of\": \"Gross Rent\", \"charge\": \"3000\", \"fee_name\": \"Rent\", \"fee_type\": \"$\", \"frequency\": \"Monthly\"}]",
                    "lease_start": "2022-05-02",
                    "lease_end": "2022-05-28",
                    "rental_status": "ACTIVE",
                    "tenant_id": "100-000003",
                    "tenant_first_name": "Prashant",
                    "tenant_last_name": "Marathay",
                    "tenant_email": null,
                    "tenant_phone_number": null
                }
            ],
            "rental_status": "ACTIVE"
        },
        {
            "maintenance_quote_uid": "900-000008",
            "linked_request_uid": "800-000010",
            "quote_business_uid": "600-000005",
            "services_expenses": null,
            "earliest_availability": null,
            "event_type": null,
            'event_duration':null,
            "notes": null,
            "quote_status": "REQUESTED",
            "quote_created_date": "2022-05-05 04:04:22",
            "maintenance_request_uid": "800-000010",
            "property_uid": "200-000008",
            "title": "Wood working",
            "description": "---------------",
            "images": "[]",
            "request_type": null,
            "request_created_by": null,
            "priority": "Medium",
            "can_reschedule": 0,
            "assigned_business": null,
            "assigned_worker": null,
            "scheduled_date": null,
            "scheduled_time": null,
            "frequency": "One time",
            "mr.notes": null,
            "request_status": "PROCESSING",
            "request_created_date": "2022-05-05 04:04:04",
            "request_created_by":"100-000001",
            "business_uid": "600-000005",
            "business_type": "MAINTENANCE",
            "business_name": "Property Services 0422",
            "business_phone_number": "1231231231",
            "business_email": "maintainance0422@gmail.com",
            "business_ein_number": "12-12312322",
            "business_services_fees": "[{\"per\": \"hour\", \"charge\": \"50\", \"service_name\": \"Toilet Plumbing\"}, {\"per\": \"hour\", \"charge\": \"30\", \"service_name\": \"Kitchen Plumbing\"}]",
            "business_locations": "[{\"distance\": \"10\", \"location\": \"Santa Clara \"}]",
            "business_paypal": "maintainance0422@gmail.com",
            "business_apple_pay": null,
            "business_zelle": null,
            "business_venmo": null,
            "business_account_number": null,
            "business_routing_number": null,
            "p.property_uid": "200-000008",
            "owner_id": "100-000006",
            "manager_id": "",
            "address": "123 RS Street ",
            "unit": "",
            "city": "Long Beach",
            "state": "CA",
            "zip": "90706",
            "property_type": "Townhome",
            "num_beds": 3.0,
            "num_baths": 2.0,
            "area": 1700,
            "listed_rent": 2700,
            "deposit": 2000,
            "appliances": "{\"Dryer\": false, \"Range\": true, \"Washer\": false, \"Microwave\": false, \"Dishwasher\": true, \"Refrigerator\": true}",
            "utilities": "{\"Gas\": false, \"Wifi\": false, \"Trash\": true, \"Water\": false, \"Electricity\": false}",
            "pets_allowed": 1,
            "deposit_for_rent": 1,
            "p.images": "[\"https://s3-us-west-1.amazonaws.com/io-pm/properties/200-000008/img_cover\"]",
            "taxes": null,
            "mortgages": null,
            "linked_property_id": "200-000008",
            "linked_business_id": "600-000001",
            "linked_employee_id": null,
            "management_status": "ACCEPTED",
            "rentalInfo": [
                {
                    "rental_uid": "300-000007",
                    "rental_property_id": "200-000008",
                    "rent_payments": "[{\"of\": \"Gross Rent\", \"charge\": \"2000\", \"fee_name\": \"Deposit\", \"fee_type\": \"$\", \"frequency\": \"One-time\"}, {\"of\": \"Gross Rent\", \"charge\": \"2700\", \"fee_name\": \"Rent\", \"fee_type\": \"$\", \"frequency\": \"Monthly\"}]",
                    "lease_start": "2022-04-14",
                    "lease_end": "2022-04-30",
                    "rental_status": "ACTIVE",
                    "tenant_id": "100-000001",
                    "tenant_first_name": "tenant",
                    "tenant_last_name": "0413",
                    "tenant_email": "tenant0413@gmail.com",
                    "tenant_phone_number": "1111111112"
                }
            ],
            "rental_status": "ACTIVE"
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
    'event_duration':"1:59:59",
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
    "result": [
        {
            "application_uid": "020-000001",
            "message": "I would love to rent this apartment",
            "application_status": "NEW",
            "tenant_id": "100-000001",
            "tenant_first_name": "tenant111",
            "tenant_last_name": "0225",
            "tenant_email": null,
            "tenant_phone_number": null,
            "tenant_ssn": "111-12-2222",
            "tenant_current_salary": "150,000",
            "tenant_salary_frequency": "Annual",
            "tenant_current_job_title": "Machine Learning Engineer",
            "tenant_current_job_company": "Google",
            "tenant_drivers_license_number": "1212121212",
            "tenant_drivers_license_state": "CA",
            "tenant_current_address": "{\"zip\": \"89898\", \"city\": \"San Jose\", \"rent\": \"2400\", \"unit\": \"123\", \"state\": \"AR\", \"street\": \"123 Lincon st\", \"pm_name\": \"John Doe\", \"lease_end\": \"04/22\", \"pm_number\": \"9899989999\", \"lease_start\": \"01/21\"}",
            "tenant_previous_address": "{\"zip\": \"89989\", \"city\": \"San Jose\", \"rent\": \"2200\", \"unit\": \"234\", \"state\": \"--\", \"street\": \"342 Obama st\", \"pm_name\": \"Mathew\", \"lease_end\": \"01/20\", \"pm_number\": \"8888888888\", \"lease_start\": \"01/20\"}",
            "documents": "[]",
            "property_uid": "200-000001",
            "owner_id": "100-000004",
            "manager_id": "600-000017",
            "address": "101 Main St",
            "unit": "",
            "city": "San Jose",
            "state": "CA",
            "zip": "95120",
            "property_type": "Apartment",
            "num_beds": 2.0,
            "num_baths": 2.0,
            "area": 1000,
            "listed_rent": 2000,
            "deposit": 2000,
            "appliances": "{\"Dryer\": false, \"Range\": true, \"Washer\": false, \"Microwave\": true, \"Dishwasher\": false, \"Refrigerator\": true}",
            "utilities": "{\"Gas\": true, \"Wifi\": false, \"Trash\": false, \"Water\": true, \"Electricity\": true}",
            "pets_allowed": 1,
            "deposit_for_rent": 1,
            "images": "[\"https://s3-us-west-1.amazonaws.com/io-pm/properties/200-000001/img_cover\"]",
            "taxes": null,
            "mortgages": null
        },
        {
            "application_uid": "020-000005",
            "message": "Application has been rejected by the Property Mana",
            "application_status": "REJECTED",
            "tenant_id": "100-000001",
            "tenant_first_name": "tenant111",
            "tenant_last_name": "0225",
            "tenant_email": null,
            "tenant_phone_number": null,
            "tenant_ssn": "111-12-2222",
            "tenant_current_salary": "150,000",
            "tenant_salary_frequency": "Annual",
            "tenant_current_job_title": "Machine Learning Engineer",
            "tenant_current_job_company": "Google",
            "tenant_drivers_license_number": "1212121212",
            "tenant_drivers_license_state": "CA",
            "tenant_current_address": "{\"zip\": \"89898\", \"city\": \"San Jose\", \"rent\": \"2400\", \"unit\": \"123\", \"state\": \"AR\", \"street\": \"123 Lincon st\", \"pm_name\": \"John Doe\", \"lease_end\": \"04/22\", \"pm_number\": \"9899989999\", \"lease_start\": \"01/21\"}",
            "tenant_previous_address": "{\"zip\": \"89989\", \"city\": \"San Jose\", \"rent\": \"2200\", \"unit\": \"234\", \"state\": \"--\", \"street\": \"342 Obama st\", \"pm_name\": \"Mathew\", \"lease_end\": \"01/20\", \"pm_number\": \"8888888888\", \"lease_start\": \"01/20\"}",
            "documents": "[]",
            "property_uid": "200-000002",
            "owner_id": "100-000004",
            "manager_id": "600-000017",
            "address": "102 Test St",
            "unit": "",
            "city": "San Jose",
            "state": "CA",
            "zip": "95120",
            "property_type": "Apartment",
            "num_beds": 2.0,
            "num_baths": 2.0,
            "area": 1000,
            "listed_rent": 2000,
            "deposit": 2000,
            "appliances": "{\"Dryer\": false, \"Range\": false, \"Washer\": false, \"Microwave\": true, \"Dishwasher\": false, \"Refrigerator\": true}",
            "utilities": "{\"Gas\": false, \"Wifi\": false, \"Trash\": false, \"Water\": true, \"Electricity\": true}",
            "pets_allowed": 1,
            "deposit_for_rent": 1,
            "images": "[\"https://s3-us-west-1.amazonaws.com/io-pm/properties/200-000002/img_cover\"]",
            "taxes": null,
            "mortgages": null
        }
    ]
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

##### PUT

- update application when tenant accepts the application
- if multiple tenants, when only one of the tenant approves lease, its application_status will change to 'ACCEPTED' and the other will remain 'FORWARDED'. When the other tenant also approves, application_status for both the tenants changes to "RENTED" and the application_status for the rest of the tenants changes to 'REJECTED'. The rental_status in the rentals table changes to 'ACTIVE'
- request JSON:

```
{
    "application_uid": "020-000024",
    "application_status": "RENTED",
    "property_uid":"200-000015"
}
---

```

- response JSON:

```
{
    "message": "Successfully committed SQL query",
    "code": 200
}
```

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

---

### /availableProperties

##### GET

- get all available properties for a tenant
- route changes based on tenant_id (ex: /availableProperties)
- response JSON:

{
"message": "Successfully executed SQL query",
"code": 200,
"result": [
{
"property_uid": "200-000009",
"owner_id": "100-000025",
"manager_id": "600-000017",
"employee_id": null,
"management_status": null,
"address": "123 able st",
"unit": "123",
"city": "san jose",
"state": "CA",
"zip": "90909",
"property_type": "Apartment",
"num_beds": 2.0,
"num_baths": 2.0,
"area": 1100,
"listed_rent": 3001,
"deposit": 3001,
"appliances": "{\"Dryer\": false, \"Range\": true, \"Washer\": true, \"Microwave\": true, \"Dishwasher\": true, \"Refrigerator\": true}",
"utilities": "{\"Gas\": false, \"Wifi\": false, \"Trash\": false, \"Water\": false, \"Electricity\": false}",
"pets_allowed": 1,
"deposit_for_rent": 1,
"images": "[\"https://s3-us-west-1.amazonaws.com/io-pm/properties/200-000009/img_cover\"]",
"taxes": null,
"mortgages": null,
"owner_first_name": "owner",
"owner_last_name": "0316",
"owner_phone_number": "1231231231",
"owner_email": "owner0316@gmail.com",
"manager_business_name": "Property Management 0225",
"manager_phone_number": "1234567890",
"manager_email": "pm0225@gmail.com",
"rental_uid": null,
"rental_property_id": null,
"rent_payments": null,
"lease_start": null,
"lease_end": null,
"rental_status": null,
"tenant_id": null,
"tenant_first_name": null,
"tenant_last_name": null,
"tenant_email": null,
"tenant_phone_number": null,
"purchases": "[{\"payer\": \"[\\\"100-0000\", \"receiver\": \"200-000009\", \"amount_due\": 15.0, \"amount_paid\": 0.0, \"description\": \"Service Charge\", \"purchase_uid\": \"400-000033\", \"purchase_type\": \"RENT\", \"purchase_notes\": \"March\", \"pur_property_id\": \"200-000009\", \"purchase_status\": \"UNPAID\"}, {\"payer\": \"[\\\"100-0000\", \"receiver\": \"200-000009\", \"amount_due\": 10.0, \"amount_paid\": 0.0, \"description\": \"SC\", \"purchase_uid\": \"400-000034\", \"purchase_type\": \"RENT\", \"purchase_notes\": \"\", \"pur_property_id\": \"200-000009\", \"purchase_status\": \"UNPAID\"}]"
},
{
"property_uid": "200-000014",
"owner_id": "100-000004",
"manager_id": null,
"employee_id": null,
"management_status": null,
"address": "900 Old st",
"unit": "",
"city": "San Jose",
"state": "CA",
"zip": "98088",
"property_type": "Apartment",
"num_beds": 2.0,
"num_baths": 1.5,
"area": 1000,
"listed_rent": 2343,
"deposit": 2343,
"appliances": "{\"Dryer\": true, \"Range\": false, \"Washer\": false, \"Microwave\": false, \"Dishwasher\": false, \"Refrigerator\": true}",
"utilities": "{\"Gas\": false, \"Wifi\": true, \"Trash\": true, \"Water\": false, \"Electricity\": false}",
"pets_allowed": 1,
"deposit_for_rent": 1,
"images": "[\"https://s3-us-west-1.amazonaws.com/io-pm/properties/200-000007/img_cover\"]",
"taxes": null,
"mortgages": null,
"owner_first_name": "Owner",
"owner_last_name": "225",
"owner_phone_number": "(123)456-0225",
"owner_email": "owner225@gmail.com",
"manager_business_name": null,
"manager_phone_number": null,
"manager_email": null,
"rental_uid": null,
"rental_property_id": null,
"rent_payments": null,
"lease_start": null,
"lease_end": null,
"rental_status": null,
"tenant_id": null,
"tenant_first_name": null,
"tenant_last_name": null,
"tenant_email": null,
"tenant_phone_number": null,
"purchases": null
},
{
"property_uid": "200-000017",
"owner_id": "100-000038",
"manager_id": "600-000020",
"employee_id": null,
"management_status": "FORWARDED",
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
"mortgages": null,
"owner_first_name": "po",
"owner_last_name": "0325",
"owner_phone_number": "1234567890",
"owner_email": "po0325@gmail.com",
"manager_business_name": "PM Mar 25th",
"manager_phone_number": "1234567890",
"manager_email": "pm0325@gmail.com",
"rental_uid": null,
"rental_property_id": null,
"rent_payments": null,
"lease_start": null,
"lease_end": null,
"rental_status": null,
"tenant_id": null,
"tenant_first_name": null,
"tenant_last_name": null,
"tenant_email": null,
"tenant_phone_number": null,
"purchases": null
},
{
"property_uid": "200-000018",
"owner_id": "100-000027",
"manager_id": null,
"employee_id": null,
"management_status": null,
"address": "123 AK Street",
"unit": "3",
"city": "Bellflower",
"state": "CA",
"zip": "90706",
"property_type": "Townhome",
"num_beds": 3.0,
"num_baths": 2.5,
"area": 1700,
"listed_rent": 3000,
"deposit": 2000,
"appliances": "{\"Dryer\": false, \"Range\": true, \"Washer\": false, \"Microwave\": true, \"Dishwasher\": true, \"Refrigerator\": false}",
"utilities": "{\"Gas\": false, \"Wifi\": false, \"Trash\": true, \"Water\": true, \"Electricity\": false}",
"pets_allowed": 1,
"deposit_for_rent": 1,
"images": "[\"https://s3-us-west-1.amazonaws.com/io-pm/properties/200-000018/img_cover\"]",
"taxes": null,
"mortgages": null,
"owner_first_name": "AK",
"owner_last_name": "Owner",
"owner_phone_number": "2138581344",
"owner_email": "akowner@gmail.com",
"manager_business_name": null,
"manager_phone_number": null,
"manager_email": null,
"rental_uid": null,
"rental_property_id": null,
"rent_payments": null,
"lease_start": null,
"lease_end": null,
"rental_status": null,
"tenant_id": null,
"tenant_first_name": null,
"tenant_last_name": null,
"tenant_email": null,
"tenant_phone_number": null,
"purchases": null
}
]
}

---

### /maintenanceRequestsandQuotes

##### GET

- with no args, return all maintenance requests, along with their quotes
- add args to endpoint to filter results (ex: /property_uid=200-000012, manager_id=600-000001)

```

{
    "message": "Successfully executed SQL query",
    "code": 200,
    "result": [
        {
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
            "scheduled_time": null,
            "frequency": "One time",
            "notes": null,
            "request_status": "PROCESSING",
            "request_created_date": "2022-02-25 16:58:49",
            "request_created_by":"100-000001",
            "quotes": [
                {
                    "maintenance_quote_uid": "900-000001",
                    "linked_request_uid": "800-000001",
                    "quote_business_uid": "600-000016",
                    "services_expenses": "[{\"per\": \"Hour\", \"charge\": \"50\", \"service_name\": \"Paint\"}]",
                    "earliest_availability": "2022-02-25 00:00:00",
                    "event_type": null,
                    'event_duration':null,
                    "notes": null,
                    "quote_status": "ACCEPTED",
                    "quote_created_date": "2022-02-25 17:01:19"
                },
                {
                    "maintenance_quote_uid": "900-000002",
                    "linked_request_uid": "800-000001",
                    "quote_business_uid": "600-000001",
                    "services_expenses": null,
                    "earliest_availability": null,
                    "event_type": null,
                    'event_duration':null,
                    "notes": null,
                    "quote_status": "REQUESTED",
                    "quote_created_date": "2022-03-04 08:22:03"
                },
                {
                    "maintenance_quote_uid": "900-000003",
                    "linked_request_uid": "800-000001",
                    "quote_business_uid": "600-000002",
                    "services_expenses": null,
                    "earliest_availability": null,
                    "event_type": null,
                    'event_duration':null,
                    "notes": null,
                    "quote_status": "REQUESTED",
                    "quote_created_date": "2022-03-04 08:22:03"
                }
            ],
            "total_quotes": 3
        },
        {
            "maintenance_request_uid": "800-000002",
            "property_uid": "200-000001",
            "title": "kitchen",
            "description": "Kitchen wall needs repaint",
            "images": "[]",
            "priority": "Medium",
            "can_reschedule": 0,
            "assigned_business": null,
            "assigned_worker": null,
            "scheduled_date": null,
            "scheduled_time": null,
            "frequency": "One time",
            "notes": null,
            "request_status": "NEW",
            "request_created_date": "2022-02-25 18:13:15",
            "request_created_by":"100-000001",
            "quotes": [],
            "total_quotes": 0
        },
        {
            "maintenance_request_uid": "800-000003",
            "property_uid": "200-000001",
            "title": "Paint",
            "description": "Needs fresh coat of paint",
            "images": "[]",
            "priority": "Medium",
            "can_reschedule": 0,
            "assigned_business": null,
            "assigned_worker": null,
            "scheduled_date": null,
            "scheduled_time": null,
            "frequency": "One time",
            "notes": null,
            "request_status": "NEW",
            "request_created_date": "2022-04-01 09:36:52",
            "request_created_by":"100-000001",
            "quotes": [],
            "total_quotes": 0
        },
        {
            "maintenance_request_uid": "800-000004",
            "property_uid": "200-000012",
            "title": "paint ceiling",
            "description": "paint peeling off ",
            "images": "[\"https://s3-us-west-1.amazonaws.com/io-pm/maintenanceRequests/800-000004/img_0\"]",
            "priority": "Medium",
            "can_reschedule": 0,
            "assigned_business": "600-000021",
            "assigned_worker": null,
            "scheduled_date": null,
            "scheduled_time": null,
            "frequency": "One time",
            "notes": null,
            "request_status": "PROCESSING",
            "request_created_date": "2022-04-01 16:19:59",
            "request_created_by":"100-000001",
            "quotes": [
                {
                    "maintenance_quote_uid": "900-000004",
                    "linked_request_uid": "800-000004",
                    "quote_business_uid": "600-000019",
                    "services_expenses": null,
                    "earliest_availability": null,
                    "event_type": null,
                    'event_duration':null,
                    "notes": null,
                    "quote_status": "WITHDRAWN",
                    "quote_created_date": "2022-04-01 16:41:14"
                },
                {
                    "maintenance_quote_uid": "900-000005",
                    "linked_request_uid": "800-000004",
                    "quote_business_uid": "600-000021",
                    "services_expenses": null,
                    "earliest_availability": "2022-04-02 00:00:00",
                    "event_type": null,
                    'event_duration':null,
                    "notes": null,
                    "quote_status": "ACCEPTED",
                    "quote_created_date": "2022-04-01 16:41:14"
                }
            ],
            "total_quotes": 2
        },
        {
            "maintenance_request_uid": "800-000005",
            "property_uid": "200-000012",
            "title": "faucet leak",
            "description": "kitchen sink is leaking",
            "images": "[\"https://s3-us-west-1.amazonaws.com/io-pm/maintenanceRequests/800-000005/img_0\"]",
            "priority": "High",
            "can_reschedule": 0,
            "assigned_business": null,
            "assigned_worker": null,
            "scheduled_date": null,
            "scheduled_time": null,
            "frequency": "One time",
            "notes": null,
            "request_status": "NEW",
            "request_created_date": "2022-04-03 23:14:56",
            "request_created_by":"100-000001",
            "quotes": [],
            "total_quotes": 0
        },
        {
            "maintenance_request_uid": "800-000006",
            "property_uid": "200-000013",
            "title": "fence repair",
            "description": "outside fence broken needs repair",
            "images": "[\"https://s3-us-west-1.amazonaws.com/io-pm/maintenanceRequests/800-000006/img_0\"]",
            "priority": "Low",
            "can_reschedule": 0,
            "assigned_business": null,
            "assigned_worker": null,
            "scheduled_date": null,
            "scheduled_time": null,
            "frequency": "One time",
            "notes": null,
            "request_status": "NEW",
            "request_created_date": "2022-04-04 07:28:41",
            "request_created_by":"100-000001",
            "quotes": [],
            "total_quotes": 0
        },
        {
            "maintenance_request_uid": "800-000007",
            "property_uid": "200-000016",
            "title": "Re-tiling the bathroom",
            "description": "Bathroom in the first floor needs re-tiling",
            "images": "[\"https://s3-us-west-1.amazonaws.com/io-pm/maintenanceRequests/800-000007/img_0\"]",
            "priority": "Medium",
            "can_reschedule": 0,
            "assigned_business": "600-000021",
            "assigned_worker": null,
            "scheduled_date": null,
            "scheduled_time": null,
            "frequency": "One time",
            "notes": null,
            "request_status": "PROCESSING",
            "request_created_date": "2022-04-07 03:12:55",
            "request_created_by":"100-000001",
            "quotes": [
                {
                    "maintenance_quote_uid": "900-000006",
                    "linked_request_uid": "800-000007",
                    "quote_business_uid": "600-000021",
                    "services_expenses": "[{\"per\": \"Hour\", \"charge\": \"50\", \"service_name\": \"Tiling Fee\"}]",
                    "earliest_availability": "2022-04-09 00:00:00",
                    "event_type": null,
                    'event_duration':null,
                    "notes": null,
                    "quote_status": "ACCEPTED",
                    "quote_created_date": "2022-04-08 07:32:43"
                }
            ],
            "total_quotes": 1
        },
        {
            "maintenance_request_uid": "800-000008",
            "property_uid": "200-000016",
            "title": "Garage needs woodworking",
            "description": "Wood working services for garage",
            "images": "[]",
            "priority": "High",
            "can_reschedule": 0,
            "assigned_business": null,
            "assigned_worker": null,
            "scheduled_date": null,
            "scheduled_time": null,
            "frequency": "One time",
            "notes": null,
            "request_status": "PROCESSING",
            "request_created_date": "2022-04-08 07:38:35",
            "request_created_by":"100-000001",
            "quotes": [
                {
                    "maintenance_quote_uid": "900-000007",
                    "linked_request_uid": "800-000008",
                    "quote_business_uid": "600-000021",
                    "services_expenses": "[{\"per\": \"Hour\", \"charge\": \"100\", \"service_name\": \"Carpentry Fee\"}]",
                    "earliest_availability": "2022-04-16 00:00:00",
                    "event_type": null,
                    'event_duration':null,
                    "notes": null,
                    "quote_status": "REJECTED",
                    "quote_created_date": "2022-04-08 07:38:56"
                },
                {
                    "maintenance_quote_uid": "900-000008",
                    "linked_request_uid": "800-000008",
                    "quote_business_uid": "600-000021",
                    "services_expenses": null,
                    "earliest_availability": null,
                    "event_type": null,
                    'event_duration':null,
                    "notes": null,
                    "quote_status": "REJECTED",
                    "quote_created_date": "2022-04-08 07:41:34"
                }
            ],
            "total_quotes": 2
        },
        {
            "maintenance_request_uid": "800-000009",
            "property_uid": "200-000016",
            "title": "Lawn repair",
            "description": "Lawn need care and repair",
            "images": "[]",
            "priority": "Medium",
            "can_reschedule": 0,
            "assigned_business": "600-000021",
            "assigned_worker": null,
            "scheduled_date": null,
            "scheduled_time": null,
            "frequency": "One time",
            "notes": null,
            "request_status": "PROCESSING",
            "request_created_date": "2022-04-08 16:16:49",
            "request_created_by":"100-000001",
            "quotes": [
                {
                    "maintenance_quote_uid": "900-000009",
                    "linked_request_uid": "800-000009",
                    "quote_business_uid": "600-000021",
                    "services_expenses": "[{\"per\": \"Hour\", \"charge\": \"50\", \"service_name\": \"Mowing feee\"}]",
                    "earliest_availability": "2022-04-09 00:00:00",
                    "event_type": null,
                    'event_duration':null,
                    "notes": null,
                    "quote_status": "ACCEPTED",
                    "quote_created_date": "2022-04-08 16:17:23"
                }
            ],
            "total_quotes": 1
        },
        {
            "maintenance_request_uid": "800-000010",
            "property_uid": "200-000016",
            "title": "Toilet plumbing",
            "description": "Plumbing service in both bathrooms",
            "images": "[]",
            "priority": "High",
            "can_reschedule": 0,
            "assigned_business": null,
            "assigned_worker": null,
            "scheduled_date": null,
            "scheduled_time": null,
            "frequency": "One time",
            "notes": null,
            "request_status": "PROCESSING",
            "request_created_date": "2022-04-08 16:23:59",
            "request_created_by":"100-000001",
            "quotes": [
                {
                    "maintenance_quote_uid": "900-000010",
                    "linked_request_uid": "800-000010",
                    "quote_business_uid": "600-000016",
                    "services_expenses": null,
                    "earliest_availability": null,
                    "event_type": null,
                    'event_duration':null,
                    "notes": null,
                    "quote_status": "REQUESTED",
                    "quote_created_date": "2022-04-08 16:24:16"
                },
                {
                    "maintenance_quote_uid": "900-000011",
                    "linked_request_uid": "800-000010",
                    "quote_business_uid": "600-000019",
                    "services_expenses": null,
                    "earliest_availability": null,
                    "event_type": null,
                    'event_duration':null,
                    "notes": null,
                    "quote_status": "REQUESTED",
                    "quote_created_date": "2022-04-08 16:24:16"
                },
                {
                    "maintenance_quote_uid": "900-000012",
                    "linked_request_uid": "800-000010",
                    "quote_business_uid": "600-000021",
                    "services_expenses": null,
                    "earliest_availability": null,
                    "event_type": null,
                    'event_duration':null,
                    "notes": null,
                    "quote_status": "REQUESTED",
                    "quote_created_date": "2022-04-08 16:24:16"
                }
            ],
            "total_quotes": 3
        }
    ]
}

```

### /bills

##### GET

- with no args, return all bills, along with their quotes
- add args to endpoint to filter results (ex: /bill_property_id=200-000012, bill_created_by=600-000001)

```

{
    "message": "Successfully executed SQL query",
    "code": 200,
    "result": [
        {
            "bill_uid": "040-000001",
            "bill_description": "water bill",
            "bill_created_by": "600-000001",
            "bill_utility_type": "water",
            "bill_distribution_type": "2 ways",
            "bill_property_id": "200-000001",
            "purchase_uid": null,
            "linked_purchase_id": null,
            "pur_property_id": null,
            "payer": null,
            "receiver": null,
            "purchase_type": null,
            "description": null,
            "amount_due": null,
            "amount_paid": null,
            "purchase_notes": null,
            "purchase_date": null,
            "purchase_frequency": null,
            "purchase_status": null,
            "payment_frequency": null,
            "next_payment": null
        }
    ]
}

```

##### POST

- create new bill
- send as multipart/form-data
- request JSON:

```
bill_property_id:200-000001
bill_created_by:600-000001
bill_description:water bill
bill_utility_type:
bill_distribution_type:
```

- response JSON:

```
{
    "message": "Successfully committed SQL query",
    "code": 200
}
```
