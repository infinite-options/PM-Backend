

from flask import request, current_app
from flask_restful import Resource

from data import connect
import json
from datetime import datetime


class LeaseTenants(Resource):

    def get(self):
        filters = ['linked_tenant_id']
        where = {}
        for filter in filters:
            filterValue = request.args.get(filter)
            if filterValue is not None:
                where[filter] = filterValue
        with connect() as db:
            sql = 'SELECT  FROM leaseTenants lt LEFT JOIN rentals r ON lt.linked_rental_uid = r.rental_uid'
            cols = 'linked_tenant_id, r.*'
            tables = 'leaseTenants lt LEFT JOIN rentals r ON lt.linked_rental_uid = r.rental_uid'
            response = db.select(cols=cols, tables=tables, where=where)
        return response
