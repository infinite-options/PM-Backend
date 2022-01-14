

# PropertyManagement backend

---

### All Routes

- [/properties](#properties)
- [/users](#users)
- [/login](#login)
- [/ownerProfileInfo](#ownerprofileinfo)
- [/managerProfileInfo](#managerprofileinfo)
- [/tenantProfileInfo](#tenantprofileinfo)
- [/businessProfileInfo](#businessprofileinfo)
- [/rentals](#rentals)
- [/purchases](#purchases)
- [/payments](#payments)

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
        "zip": "95120",
        "state": "CA",
        "type": "Apartment",
        "num_beds": 2.0,
        "num_baths": 1.0,
        "area": 1000,
        "listed_rent": 1800,
        "deposit": 800,
        "appliances": "[\"Microwave\", \"Refrigerator\"]",
        "utilities": "[\"Trash\", \"Gas\"]",
        "pets_allowed": 1,
        "deposit_for_rent": 1,
        "picture": "NULL",
        "city": "San Jose",
        "taxes": null,
        "mortgages": null
    }]
}
```

##### POST
- create new property
- request JSON:
```
{
    "owner_id": "100-000001",
    "manager_id": "100-000002",
    "address": "123 Main St",
    "city": "San Jose",
    "state": "CA",
    "zip": "95120",
    "type": "Apartment",
    "num_beds": 2,
    "num_baths": 1,
    "area": 1000,
    "listed_rent": 1800,
    "deposit": 800,
    "appliances": ["Microwave", "Refrigerator"],
    "utilities": ["Trash", "Gas"],
    "pets_allowed": true,
    "deposit_for_rent": true,
    "picture": "NULL"
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
    "previous_addresses": []
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
    "result": [{
        "rental_uid": "300-000001",
        "rental_property_id": "200-000001",
        "tenant_id": "100-000003",
        "actual_rent": "1800",
        "lease_start": "1/22",
        "lease_end": "1/23",
        "rental_status": "ACTIVE"
    }]
}
```

##### POST
- create new rental
- request JSON:
```
{
  "rental_property_id": "200-000001",
  "tenant_id": "100-000003",
  "actual_rent": "1800",
  "lease_start": "1/22",
  "lease_end": "1/23"
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
