

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

---

### /properties

##### GET
- with no args, return all properties
- add args to endpoint to filter results (ex: /properties?num_beds=1)
- available filters
  - property_uid
  - owner_id
  - manager_business
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
    "result": [{
            "property_uid": "200-000001",
            "owner_id": "100-000001",
            "manager_id": "100-000002",
            "address": "123 Main St",
            "unit": "#35",
            "city": "San Jose",
            "state": "CA",
            "zip": "95120",
            "property_type": "Apartment",
            "num_beds": 2.0,
            "num_baths": 2.0,
            "area": 1000,
            "listed_rent": 1800,
            "deposit": 800,
            "appliances": "{\"Dryer\": false, \"Range\": false, \"Washer\": false, \"Microwave\": true, \"Dishwasher\": false, \"Refrigerator\": true, \"Air Conditioner\": true}",
            "utilities": "{\"Gas\": true, \"Wifi\": false, \"Trash\": true, \"Water\": false, \"Electricity\": false}",
            "pets_allowed": 1,
            "deposit_for_rent": 1,
            "images": "[\"https://s3-us-west-1.amazonaws.com/io-pm/properties/200-000001/img_cover\", \"https://s3-us-west-1.amazonaws.com/io-pm/properties/200-000001/img_0\"]",
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
- include image files as img_cover, img_0, img_1...
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

### /properties/{property_uid}

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
            "actual_rent": 1800,
            "lease_start": "2022-02-01",
            "lease_end": "2022-03-01",
            "rental_status": "ACTIVE",
            "tenant_first_name": "Tenant",
            "tenant_last_name": "Test",
            "purchases": "[{\"payer\": \"100-000003\", \"amount\": 1800.0, \"receiver\": \"100-000001\", \"description\": \"Rent for January 2022\", \"purchase_uid\": \"400-000001\", \"purchase_type\": \"RENT\", \"purchase_notes\": \"First month's rent\", \"pur_property_id\": \"200-000001\"}, {\"payer\": \"100-000001\", \"amount\": 40.0, \"receiver\": \"100-000004\", \"description\": \"Toilet Plumbing\", \"purchase_uid\": \"400-000002\", \"purchase_type\": \"MAINTENANCE\", \"purchase_notes\": null, \"pur_property_id\": \"200-000001\"}]"
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
            "actual_rent": 1800,
            "lease_start": "2022-02-01",
            "lease_end": "2022-03-01",
            "rental_status": "ACTIVE",
            "tenant_first_name": "Tenant",
            "tenant_last_name": "Test",
            "purchases": "[{\"payer\": \"100-000003\", \"amount\": 1800.0, \"receiver\": \"100-000001\", \"description\": \"Rent for January 2022\", \"purchase_uid\": \"400-000001\", \"purchase_type\": \"RENT\", \"purchase_notes\": \"First month's rent\", \"pur_property_id\": \"200-000001\"}, {\"payer\": \"100-000001\", \"amount\": 40.0, \"receiver\": \"100-000004\", \"description\": \"Toilet Plumbing\", \"purchase_uid\": \"400-000002\", \"purchase_type\": \"MAINTENANCE\", \"purchase_notes\": null, \"pur_property_id\": \"200-000001\"}]"
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
            "actual_rent": 1800,
            "lease_start": "2022-02-01",
            "lease_end": "2022-03-01",
            "rental_status": "ACTIVE",
            "tenant_first_name": "Tenant",
            "tenant_last_name": "Test",
            "purchases": "[{\"payer\": \"100-000003\", \"amount\": 1800.0, \"receiver\": \"100-000001\", \"description\": \"Rent for January 2022\", \"purchase_uid\": \"400-000001\", \"purchase_type\": \"RENT\", \"purchase_notes\": \"First month's rent\", \"pur_property_id\": \"200-000001\"}, {\"payer\": \"100-000001\", \"amount\": 40.0, \"receiver\": \"100-000004\", \"description\": \"Toilet Plumbing\", \"purchase_uid\": \"400-000002\", \"purchase_type\": \"MAINTENANCE\", \"purchase_notes\": null, \"pur_property_id\": \"200-000001\"}]"
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
    "result": [{
            "user_uid": "100-000001",
            "first_name": "Owner",
            "last_name": "Test",
            "phone_number": "(800)000-0001",
            "email": "owner@gmail.com",
            "password_salt": "9803f419b4e0f81dbd443e526c074351b91f2cb43a91bb16cdea6ccb1523388f",
            "password_hash": "600d7cf7e13fef382e4377b6290f55a52194e400c2690c22dd0dd23af2ce6d9a",
            "role": "OWNER",
            "created_date": "2022-01-05 08:00:01"
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
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTY0MTM2OTYwMSwianRpIjoiMzYxYWE0ZGQtOWU3OS00ODJiLWE2MGQtNzBiNDg3MDNlM2VkIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6eyJ1c2VyX2lkIjoiMTAwLTAwMDAwMSIsImZ1bGxfbmFtZSI6Ik93bmVyIFRlc3QiLCJwaG9uZV9udW1iZXIiOiIoODAwKTAwMC0wMDAxIiwiZW1haWwiOiJvd25lckBnbWFpbC5jb20iLCJyb2xlIjoiT1dORVIifSwibmJmIjoxNjQxMzY5NjAxLCJleHAiOjE2NDEzNzA1MDF9.wucRiHI7XzC7WSEzC0U_oGm3ysY5l2FVLFNj-Dvmz9s",
        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTY0MTM2OTYwMSwianRpIjoiYTdkOWM4YjMtNWYyOC00M2VhLWI2NGEtMWQwZWI2NjMzN2NmIiwidHlwZSI6InJlZnJlc2giLCJzdWIiOnsidXNlcl9pZCI6IjEwMC0wMDAwMDEiLCJmdWxsX25hbWUiOiJPd25lciBUZXN0IiwicGhvbmVfbnVtYmVyIjoiKDgwMCkwMDAtMDAwMSIsImVtYWlsIjoib3duZXJAZ21haWwuY29tIiwicm9sZSI6Ik9XTkVSIn0sIm5iZiI6MTY0MTM2OTYwMSwiZXhwIjoxNjQzOTYxNjAxfQ.HQ83n6Ux45O4IYTxzNHF_eXM8xWzZefQF9TgjsFZE-E",
        "user": {
            "user_uid": "100-000001",
            "first_name": "Owner",
            "last_name": "Test",
            "phone_number": "(800)000-0001",
            "email": "owner@gmail.com",
            "role": "OWNER"
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
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTY0MTM2OTY2MiwianRpIjoiZjczZTY5MGEtMTNmMi00YzVkLTkxYzMtMGEyMzgwZWVhMzFiIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6eyJ1c2VyX2lkIjoiMTAwLTAwMDAwMSIsImZ1bGxfbmFtZSI6Ik93bmVyIFRlc3QiLCJwaG9uZV9udW1iZXIiOiIoODAwKTAwMC0wMDAxIiwiZW1haWwiOiJvd25lckBnbWFpbC5jb20iLCJyb2xlIjoiT1dORVIifSwibmJmIjoxNjQxMzY5NjYyLCJleHAiOjE2NDEzNzA1NjJ9.wSCK6FKNVsPpgTBFBB_DqZ85EEw6DaNsEPIuZFR_WW4",
        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTY0MTM2OTY2MiwianRpIjoiNjBlNTgzZGQtZTEyMy00NWI1LTkzNjEtNGNlMTYxYzBlOGMyIiwidHlwZSI6InJlZnJlc2giLCJzdWIiOnsidXNlcl9pZCI6IjEwMC0wMDAwMDEiLCJmdWxsX25hbWUiOiJPd25lciBUZXN0IiwicGhvbmVfbnVtYmVyIjoiKDgwMCkwMDAtMDAwMSIsImVtYWlsIjoib3duZXJAZ21haWwuY29tIiwicm9sZSI6Ik9XTkVSIn0sIm5iZiI6MTY0MTM2OTY2MiwiZXhwIjoxNjQzOTYxNjYyfQ.BgTTlZ2Smq3ZFWoBvdtfuXxi-thulojBDT7xVbpk7SM",
        "user": {
            "user_uid": "100-000001",
            "first_name": "Owner",
            "last_name": "Test",
            "phone_number": "(800)000-0001",
            "email": "owner@gmail.com",
            "role": "OWNER"
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

### /managerProfileInfo

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
        "tenant_id": "100-000003",
        "tenant_first_name": "Tenant",
        "tenant_last_name": "Test",
        "tenant_ssn": "000-00-0003",
        "tenant_current_salary": 75000,
        "tenant_salary_frequency": "Annually",
        "tenant_current_job_title": "Software Engineer",
        "tenant_current_job_company": "Infinite Options",
        "tenant_drivers_license_number": "A0000003",
        "tenant_current_address": "{\"zip\": \"95120\", \"city\": \"San Jose\", \"rent\": 1800, \"unit\": \"\", \"state\": \"CA\", \"street\": \"123 Main St\", \"pm_name\": \"Manager Test\", \"lease_end\": \"1/22\", \"pm_number\": \"00-0000002\", \"lease_start\": \"6/19\"}",
        "tenant_previous_addresses": null
    }]
}
```

##### POST
- create new tenant info
- requires JWT authorization
- request JSON:
```
{
    "first_name": "Tenant",
    "last_name": "Test",
    "ssn": "000-00-0003",
    "drivers_license_number": "A0000003",
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
    "previous_address": []
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
- request JSON:
```
{
    "first_name": "Tenant",
    "last_name": "Test",
    "ssn": "000-00-0003",
    "drivers_license_number": "A0000003",
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
    "previous_address": []
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

### /businessProfileInfo

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
- request JSON:
```
{
  "rental_property_id": "200-000001",
  "tenant_id": "100-000003",
  "actual_rent": "1800",
  "lease_start": "1/22",
  "lease_end": "1/23",
  "rent_payments": [{
    "title": "Monthly Rent",
    "charge_type": "$",
    "charge": 100,
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
  "doc_1": ""
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
- include document files as doc_0, doc_1...
- request JSON:
```
{
  "rental_uid": "300-000001",
  "actual_rent": "1800",
  "lease_start": "1/22",
  "lease_end": "1/23",
  "rent_payments": [{
    "title": "Monthly Rent",
    "charge_type": "$",
    "charge": 100,
    "frequency": "Monthly"
  }],
  "contact_details": [{
    "first_name": "Greg",
    "last_name": "Brewer",
    "company_role": "Manager",
    "phone_number": "(789)908-9087",
    "email": "greg@beverlyman.com"
  }],
  "doc_0": "",
  "doc_1": ""
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
  "doc_1": ""
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
- include document files as doc_0, doc_1...
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
  "doc_1": ""
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
        "pay_property_id": "200-000001",
        "payer": "100-000003",
        "receiver": "100-000001",
        "purchase_type": "RENT",
        "description": "Rent for January 2022",
        "amount": 1800.0,
        "purchase_notes": "First month's rent",
        "purchase_date": "2022-01-10 07:19:16",
        "purchase_status": "UNPAID"
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
    "amount": "1800",
    "purchase_notes": "First month's rent"
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
        "subtotal": 1800.0,
        "amount_discount": 0.0,
        "service_fee": 0.0,
        "taxes": 0.0,
        "amount_due": 1800.0,
        "amount_paid": 1800.0,
        "cc_num": "1234-5678-9012-3456",
        "cc_exp_date": "3/24",
        "cc_cvv": "123",
        "cc_zip": "12345",
        "charge_id": null,
        "payment_type": "CARD",
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
    "subtotal": 1800,
    "amount_discount": 0,
    "service_fee": 0,
    "taxes": 0,
    "amount_due": 1800,
    "amount_paid": 1800,
    "cc_num": "1234-5678-9012-3456",
    "cc_exp_date": "3/24",
    "cc_cvv": "123",
    "cc_zip": "12345",
    "payment_type": "CARD"
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
        "business_uid": "600-000001",
        "business_type": "MANAGEMENT",
        "business_name": "Infinite Options",
        "business_phone_number": "(800)123-1234",
        "business_email": "iomanagement@gmail.com",
        "business_ein_number": "12-1234567",
        "business_services_fees": "[{\"of\": \"Gross Rent\", \"name\": \"Service Charge\", \"type\": \"%\", \"charge\": 10, \"frequency\": \"Monthly\"}]"
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
    }]
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
    }]
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
    }]
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
    "employee_role": "Accountant",
    "employee_first_name": "John",
    "employee_last_name": "Doe",
    "employee_phone_number": "(789)908-9087",
    "employee_email": "pm@gmail.com",
    "employee_ssn": "131-89-1839",
    "employee_ein_number": "12-1313131"
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
  - status
- response JSON:
```
{
    "message": "Successfully executed SQL query",
    "code": 200,
    "result": [{
        "maintenance_request_uid": "800-000001",
        "property_uid": "200-000001",
        "title": "Bathroom Leaking",
        "description": "The toilet plumbing is leaking at the base",
        "images": "[]",
        "priority": "High",
        "can_reschedule": 0,
        "assigned_business": null,
        "assigned_worker": null,
        "scheduled_date": null,
        "frequency": "One time",
        "notes": null,
        "status": "NEW"
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
- include image files as img_0, img_1...
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
    "status": "SCHEDULED",
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
- with no args, return all maintenance quotes
- add args to endpoint to filter results (ex: /maintenanceQuotes?status=REQUESTED)
- available filters
  - maintenance_quote_uid
  - maintenance_request_uid
  - business_uid
  - status
- response JSON:
```
{
    "message": "Successfully executed SQL query",
    "code": 200,
    "result": [{
        "maintenance_quote_uid": "900-000001",
        "maintenance_request_uid": "800-000001",
        "business_uid": "600-000001",
        "services_expenses": "[{\"fees\": 30, \"payment_term\": \"One-time cost\", \"service_notes\": \"Sealing base - labor cost\"}]",
        "earliest_availability": "2022-01-03 00:00:00",
        "event_type": "2 hour job",
        "notes": null,
        "status": "SENT"
    }]
}
```

##### POST
- create new maintenance quote
- request JSON (manager requests quote from business):
```
{
    "maintenance_request_uid": "800-000001",
    "business_uid": "600-000001"
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
    "status": "SENT"
}
```
- request JSON (manager rejects quote):
```
{
    "maintenance_quote_uid": "900-000001",
    "status": "REJECTED",
    "notes": "Price too high"
}
```
- request JSON (manager accepts quote):
- follow with PUT /maintenanceRequests/{maintenance_request_uid} (update assigned_business)
```
{
    "maintenance_quote_uid": "900-000001",
    "status": "ACCEPTED"
}
```
- response JSON:
```
{
    "message": "Successfully committed SQL query",
    "code": 200
}
```
