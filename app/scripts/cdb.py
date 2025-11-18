import os
import psycopg2
import pandas as pd
from ._global import GLOBAL_CONFIG
from .util import load_yaml_file

def bioDBRadar():
    auth_file = os.path.join(
            GLOBAL_CONFIG['config_dir'],
            'auth', 'biodb'
        )
    auth = load_yaml_file(auth_file)
    conn = psycopg2.connect(**auth)
    conn.autocommit = True
    cursor = conn.cursor()
    return cursor, conn

def executeSQLCmd(sqlCmd, args=None):
    cursor, conn = bioDBRadar()

    if args is None:
        cursor.execute(sqlCmd)
    else:
        cursor.execute(sqlCmd, args)

    cursor.close()
    conn.close()
    return 0

def queryDB_pd_df(sqlQuery, args=None):
    cursor, conn = bioDBRadar()

    if args is None:
        df = pd.read_sql_query(sqlQuery, conn)
    else:
        df = pd.read_sql_query(
                sqlQuery, conn, params=args
            )

    cursor.close()
    conn.close()
    return df

def queryDB_json(sqlQuery, args=None):
    cursor, conn = bioDBRadar()

    if args is None:
        cursor.execute(sqlQuery)
    else:
        cursor.execute(sqlQuery, args)

    res = convert2json(cursor)
    cursor.close()
    conn.close()
    return res

def convert2json(cursor):
    row_headers = [x[0] for x in cursor.description]
    result = cursor.fetchall()

    json_data = []
    for res in result:
        json_data.append(
                dict(zip(row_headers, res))
            )

    return json_data
