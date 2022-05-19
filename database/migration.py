#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 18.10.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import datetime
import psycopg2
import sys
import os
import json

# Insert the parent directory as root directory
ROOT_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        os.pardir
    )
)

from georeference.models.jobs import EnumJobType

sys.path.append(ROOT_PATH)

def do_trg_db_clean(conn):
    """ Empties all fields from the target database. This function should be used carefully, because
        it deletes all entries from the database and should only be used in developing environments.

    :param conn: Database connection
    :type conn: psycopg2.connection
    """
    cur = None
    try:
        cur = conn.cursor()

        # Clears the databases
        cur.execute('TRUNCATE jobs CASCADE;')
        cur.execute('TRUNCATE georef_maps CASCADE;')
        cur.execute('TRUNCATE transformations CASCADE;')
        cur.execute('TRUNCATE metadata CASCADE;')
        cur.execute('TRUNCATE raw_maps CASCADE;')
        cur.execute('TRUNCATE map_view CASCADE;')

        print('Delete all entries from the target database.')
    finally:
        if cur != None:
            cur.close()


def do_migration_table_metadata(src_conn, trg_conn):
    """ Migrations the data the "metadata" from the src database to the target database. The migration of the table
        "original_maps" has to be finished.

    :param src_conn: Database connection to the source database
    :type src_conn: psycopg2.connection
    :param trg_conn: Database connection to the target database
    :type trg_conn: psycopg2.connection
    """
    print('Migrate database "metadata" ...')

    src_cur = None
    trg_cur = None
    try:
        src_cur = src_conn.cursor()
        trg_cur = trg_conn.cursor()

        # Query source database and write records into trg database
        src_cur.execute('select m.original_map_id, m.title , m.title_short , m.title_serie , m.description , m.measures , m."type", m.technic , m.ppn , m.permalink , m.license ,m."owner" , m.link_zoomify , m.link_thumb_small , m.link_thumb_mid, m.time_of_publication from metadata m')
        for row in src_cur.fetchall():
            insert_statement = "INSERT INTO metadata(raw_map_id, title, title_short, title_serie, description, " \
                              "measures, type, technic, ppn, permalink, license, owner, link_zoomify," \
                              " link_thumb_small, link_thumb_mid, time_of_publication) VALUES ({raw_map_id}, '{title}', '{title_short}', '{title_serie}', '{description}', " \
                              "'{measures}', '{type}', '{technic}', '{ppn}', '{permalink}', '{license}', '{owner}', '{link_zoomify}'," \
                              " '{link_thumb_small}', '{link_thumb_mid}', '{time_of_publication}')".format(
                raw_map_id=row[0],
                title=row[1].replace("\'", "\'\'"),
                title_short=row[2].replace("\'", "\'\'"),
                title_serie=row[3].replace("\'", "\'\'") if row[3] is not None else None,
                description=row[4].replace("\'", "\'\'") if row[3] is not None else None,
                measures=row[5],
                type=row[6],
                technic=row[7],
                ppn=row[8],
                permalink=row[9],
                license=row[10],
                owner=row[11],
                link_zoomify=row[12],
                link_thumb_small=row[13],
                link_thumb_mid=row[14],
                time_of_publication=row[15]
            )
            print(insert_statement)

            trg_cur.execute(insert_statement)

        # Commit writes
        trg_conn.commit()

        print('======================================================')
        print('Finished migration of database "metadata".')
        print('======================================================')
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if src_cur != None:
            src_cur.close()
        if trg_cur != None:
            trg_cur.close()

def do_migration_table_raw_maps(src_conn, trg_conn):
    """ Migrations the data "original_maps" from the src database to the target database.

    :param src_conn: Database connection to the source database
    :type src_conn: psycopg2.connection
    :param trg_conn: Database connection to the target database
    :type trg_conn: psycopg2.connection
    """
    print('Migrate database "raw_maps" ...')

    src_cur = None
    trg_cur = None
    try:
        src_cur = src_conn.cursor()
        trg_cur = trg_conn.cursor()

        # Query source database and write records into trg database
        src_cur.execute('SELECT om.id, om.file_name, om.enabled, om.map_type, om.default_srs, om.rel_path, om.map_scale, m.time_of_publication FROM original_maps om join metadata m on om.id = m.original_map_id  ;')
        for row in src_cur.fetchall():
            year_of_publication = int(str(row[7]).split('-')[0])

            # Insert values into database
            insert_statement = "INSERT INTO raw_maps(id, file_name, enabled, map_type, default_crs, rel_path, map_scale, allow_download) VALUES ({id}, '{file_name}', {enabled}, '{map_type}', {default_crs}, '{rel_path}', {map_scale}, {allow_download})".format(
                id=row[0],
                file_name=row[1],
                enabled=row[2],
                map_type=row[3],
                default_crs=row[4] if row[4] is not None else 'NULL',
                rel_path=row[5],
                map_scale=row[6] if row[6] is not None else 'NULL',
                allow_download=year_of_publication <= 1900
            )

            trg_cur.execute(insert_statement)
            print(insert_statement)

        # Because of insert statements the data hase to be connected
        trg_conn.commit()

        print('======================================================')
        print('Finished migration of database "original_maps".')
        print('======================================================')
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if src_cur != None:
            src_cur.close()
        if trg_cur != None:
            trg_cur.close()

def do_migration_table_jobs(srcConn, trgConn):
    """ Migrations the data "jobs" from the src database to the target database.

    :param srcConn: Database connection to the source database
    :type srcConn: psycopg2.connection
    :param trgConn: Database connection to the target database
    :type trgConn: psycopg2.connection
    """
    print('Migrate database "jobs" ...')

    src_cur = None
    trg_cur = None
    try:
        src_cur = srcConn.cursor()
        trg_cur = trgConn.cursor()

        # Query source database and write records into trg database
        src_cur.execute('SELECT id, task_name, task, processed, submitted, user_id, comment FROM jobs')
        for row in src_cur.fetchall():
            insert_statement = "INSERT INTO jobs(id, type, description, state, submitted, user_id, comment) VALUES ({id}, '{type}', '{description}', '{state}', '{submitted}', '{user_id}', '{comment}')".format(
                id=row[0],
                type=row[1],
                description=row[2],
                state='completed' if row[3] else 'not_started',
                submitted=row[4],
                user_id=row[5],
                comment=row[6]
            )
            trg_cur.execute(insert_statement)
            print(insert_statement)

        # Because of insert statements the data hase to be connected
        trgConn.commit()

        print('======================================================')
        print('Finished migration of database "jobs".')
        print('======================================================')
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if src_cur != None:
            src_cur.close()
        if trg_cur != None:
            trg_cur.close()

def do_migration_table_transformations(src_conn, trg_conn):
    """ Migrations the data for the "transformations" table from the src database to the target database. The migration of the table
        "original_maps" has to be finished.

    :param src_conn: Database connection to the source database
    :type src_conn: psycopg2.connection
    :param trg_conn: Database connection to the target database
    :type trg_conn: psycopg2.connection
    """
    print('Migrate database "transformations" ...')

    src_cur = None
    trg_cur = None
    try:
        src_cur = src_conn.cursor()
        trg_cur = trg_conn.cursor()

        # Query source database and write records into trg database
        src_cur.execute('SELECT id, original_map_id, submitted, user_id, params, ST_AsGeoJSON(st_transform(clip, 4326)), overwrites, validation, comment FROM transformations')
        for row in src_cur.fetchall():
            # extract target crs
            target_crs = int(json.loads(row[4])['target'].split(':')[1])
            insert_statement = "INSERT INTO transformations(id, raw_map_id, submitted, user_id, params, clip, overwrites, validation, comment, target_crs) " \
                               "VALUES ({id}, {raw_map_id}, '{submitted}', '{user_id}', '{params}', {clip}, {overwrites}, '{validation}', '{comment}', {target_crs})".format(
                id=row[0],
                raw_map_id=row[1],
                submitted=row[2],
                user_id=row[3],
                params=row[4],
                clip="ST_GeomFromGeoJSON('{}')".format(row[5]) if row[5] is not None else 'NULL',
                overwrites=row[6],
                validation=row[7],
                comment=row[8],
                target_crs=target_crs
            )
            print(insert_statement)
            trg_cur.execute(insert_statement)

        # Commit writes
        trg_conn.commit()

        print('======================================================')
        print('Finished migration of database "transformations".')
        print('======================================================')
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if src_cur != None:
            src_cur.close()
        if trg_cur != None:
            trg_cur.close()

def do_migration_table_georef_maps(src_conn, trg_conn):
    """ Migrations the data for the "georef_maps" table from the src database to the target database. The migration of the table
        "original_maps" has to be finished.

    :param src_conn: Database connection to the source database
    :type src_conn: psycopg2.connection
    :param trg_conn: Database connection to the target database
    :type trg_conn: psycopg2.connection
    """
    print('Migrate database "georef_maps" ...')

    src_cur = None
    trg_cur = None
    try:
        src_cur = src_conn.cursor()
        trg_cur = trg_conn.cursor()

        # Query source database and write records into trg database
        src_cur.execute('select original_map_id, transformation_id, rel_path, ST_AsGeoJSON(st_transform(extent, 4326)), last_processed from georef_maps')
        for row in src_cur.fetchall():
            insert_statement = "INSERT INTO georef_maps (raw_map_id, transformation_id, rel_path, extent, last_processed) VALUES ({raw_map_id}, {transformation_id}, '{rel_path}', {extent}, '{last_processed}')".format(
                raw_map_id=row[0],
                transformation_id=row[1],
                rel_path=row[2],
                extent="ST_GeomFromGeoJSON('{}')".format(row[3]) if row[3] is not None else 'NULL',
                last_processed=row[4]
            )
            print(insert_statement)
            trg_cur.execute(insert_statement)

        # Commit writes
        trg_conn.commit()

        print('======================================================')
        print('Finished migration of database "georef_maps".')
        print('======================================================')
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if src_cur != None:
            src_cur.close()
        if trg_cur != None:
            trg_cur.close()

def do_migration_table_mapview(src_conn, trg_conn):
    """ Migrations the data for the "map_view" table from the src database to the target database. The migration of the table
        "raw_maps" has to be finished.

    :param src_conn: Database connection to the source database
    :type src_conn: psycopg2.connection
    :param trg_conn: Database connection to the target database
    :type trg_conn: psycopg2.connection
    """
    print('Migrate database "map_view" ...')

    src_cur = None
    trg_cur = None
    try:
        src_cur = src_conn.cursor()
        trg_cur = trg_conn.cursor()

        # Query source database and write records into trg database
        src_cur.execute('select id, map_view_json, public_id, submitted, request_count, last_request, user_id from map_view')
        for row in src_cur.fetchall():
            insert_statement = "INSERT INTO map_view (id, map_view_json, public_id, submitted, request_count, last_request, user_id) " \
                               "VALUES ({id}, '{map_view_json}', '{public_id}', '{submitted}', {request_count}, '{last_request}', '{user_id}')".format(
                id=row[0],
                map_view_json=row[1],
                public_id=row[2],
                submitted=row[3],
                request_count=row[4],
                last_request=row[5],
                user_id=row[6],
            )
            print(insert_statement)
            trg_cur.execute(insert_statement)

        # Commit writes
        trg_conn.commit()

        print('======================================================')
        print('Finished migration of database "map_view".')
        print('======================================================')
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if src_cur != None:
            src_cur.close()
        if trg_cur != None:
            trg_cur.close()

def update_sequences(trg_conn):
    """ Updates all sequences on the database.

    :param src_conn: Database connection to the source database
    :type src_conn: psycopg2.connection
    :param trg_conn: Database connection to the target database
    :type trg_conn: psycopg2.connection
    """
    print('Updates all sequences ...')

    trg_cur = None
    try:
        trg_cur = trg_conn.cursor()

        # Query source database and write records into trg database
        trg_cur.execute("SELECT setval('jobs_id_seq', max(id)) FROM jobs;")
        trg_cur.execute("SELECT setval('raw_maps_id_seq', max(id)) FROM raw_maps;")
        trg_cur.execute("SELECT setval('transformations_id_seq', max(id)) FROM transformations;")
        trg_cur.execute("SELECT setval('map_view_id_seq', max(id)) FROM map_view;")

        # Commit writes
        trg_conn.commit()

        print('Finished updating of sequences.')
        print('======================================================')
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if trg_cur != None:
            trg_cur.close()


def get_connection(conn_params):
    """ Returns a database connection for the given database params.

    :param conn_params: Database connection parameters
    :type conn_params: {{
        host: str,
        database: str,
        user: str,
        password: str
    }}
    :result: Database connection of the source database
    :rtype: psycopg2.connection
    """
    return psycopg2.connect(
        host=conn_params['host'],
        database=conn_params['database'],
        user=conn_params['user'],
        password=conn_params['password'],
    )


if __name__ == '__main__':
    src_conn = None
    trg_conn = None
    try:
        print('Initialize connections and clean the target database')
        src_conn = get_connection({
            'host':'localhost',
            'database':'vkdb_old',
            'user':'postgres',
            'password':'postgres'
        })
        trg_conn = get_connection({
            'host':'localhost',
            'database':'vkdb_new',
            'user':'postgres',
            'password':'postgres'
        })

        print('Clean up target database')
        do_trg_db_clean(trg_conn)

        print('Start migration ...')
        do_migration_table_mapview(src_conn, trg_conn)
        do_migration_table_raw_maps(src_conn, trg_conn)
        do_migration_table_metadata(src_conn, trg_conn)
        do_migration_table_transformations(src_conn, trg_conn)
        do_migration_table_jobs(src_conn, trg_conn)
        do_migration_table_georef_maps(src_conn, trg_conn)
        update_sequences(trg_conn)
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if src_conn != None:
            src_conn.close()
            print('Close source database connection.')
        if trg_conn != None:
            trg_conn.close()
            print('Close target database connection.')
