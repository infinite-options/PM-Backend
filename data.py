import pymysql
import datetime
import json

def connect():
    conn = pymysql.connect(
        host='io-mysqldb8.cxjnrciilyjq.us-west-1.rds.amazonaws.com',
        port=3306,
        user='admin',
        passwd='prashant',
        db='pm',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    return DatabaseConnection(conn)

def serializeJSON(unserialized):
    if type(unserialized) == list:
        serialized = []
        for entry in unserialized:
            serializedEntry = serializeJSON(entry)
            serialized.append(serializedEntry)
        return serialized
    elif type(unserialized) == dict:
        serialized = {}
        for entry in unserialized:
            serializedEntry = serializeJSON(unserialized[entry])
            serialized[entry] = serializedEntry
        return serialized
    elif type(unserialized) == datetime.datetime:
        return str(unserialized)
    elif type(unserialized) == bytes:
        return str(unserialized)
    else:
        return unserialized


class DatabaseConnection:
    def __init__(self, conn):
        self.conn = conn
    def disconnect(self):
        self.conn.close()

    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_value, traceback):
        self.disconnect()

    def execute(self, sql, args=[], cmd='get'):
        response = {}
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, args)
                if cmd == 'get':
                    result = cur.fetchall()
                    result = serializeJSON(result)
                    response['message'] = 'Successfully executed SQL query'
                    response['code'] = 200
                    response['result'] = result
                elif cmd == 'post':
                    self.conn.commit()
                    response['message'] = 'Successfully committed SQL query'
                    response['code'] = 200
        except Exception as e:
            print(e)
            response['message'] = 'Error occurred while executing SQL query'
            response['code'] = 500
            response['error'] = e
        return response

    def select(self, table, where={}):
        response = {}
        try:
            sql = f'SELECT * FROM {table}'
            for i, key in enumerate(where.keys()):
                if i == 0:
                    sql += ' WHERE '
                sql += f'{key} = %({key})s'
                if i != len(where.keys()) - 1:
                    sql += ', '
            response = self.execute(sql, where, 'get')
        except Exception as e:
            print(e)
        return response

    def insert(self, table, object):
        response = {}
        try:
            sql = f'INSERT INTO {table} SET '
            for i, key in enumerate(object.keys()):
                sql += f'{key} = %({key})s'
                if i != len(object.keys()) - 1:
                    sql += ', '
            response = self.execute(sql, object, 'post')
        except Exception as e:
            print(e)
        return response

    def update(self, table, primaryKey, object):
        response = {}
        try:
            sql = f'UPDATE {table} SET '
            for i, key in enumerate(object.keys()):
                sql += f'{key} = %({key})s'
                if i != len(object.keys()) - 1:
                    sql += ', '
            sql += f' WHERE '
            for i, key in enumerate(primaryKey.keys()):
                sql += f'{key} = %({key})s'
                object[key] = primaryKey[key]
                if i != len(primaryKey.keys()) - 1:
                    sql += ' AND '
            response = self.execute(sql, object, 'post')
        except Exception as e:
            print(e)
        return response

    def call(self, procedure, cmd='get'):
        response = {}
        try:
            sql = f'CALL {procedure}()'
            response = self.execute(sql, cmd=cmd)
        except Exception as e:
            print(e)
        return response