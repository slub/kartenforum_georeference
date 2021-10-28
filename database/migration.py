#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 18.10.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
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

from georeference.models.jobs import TaskValues

sys.path.append(ROOT_PATH)

def doTrgDbClean(conn):
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
        cur.execute('TRUNCATE original_maps CASCADE;')

        print('Delete all entries from the target database.')
    finally:
        if cur != None:
            cur.close()


def doMigrationTableMetadata(srcConn, trgConn):
    """ Migrations the data the "metadata" from the src database to the target database. The migration of the table
        "original_maps" has to be finished.

    :param srcConn: Database connection to the source database
    :type srcConn: psycopg2.connection
    :param trgConn: Database connection to the target database
    :type trgConn: psycopg2.connection
    """
    print('Migrate database "metadata" ...')

    srcCur = None
    trgCur = None
    try:
        srcCur = srcConn.cursor()
        trgCur = trgConn.cursor()

        # Query source database and write records into trg database
        srcCur.execute('SELECT mapid, title, titleshort, serientitle, description, measures, scale, type, technic, ppn, apspermalink, imagelicence, imageowner, imagejpg, imagezoomify, timepublish, thumbssmall, thumbsmid FROM metadata')
        for row in srcCur.fetchall():
            # Create insert statement for metadata table
            insertStatement = 'INSERT INTO metadata(original_map_id, title, title_short, title_serie, description, ' \
                              'measures, scale, type, technic, ppn, permalink, license, owner, link_jpg, link_zoomify,' \
                              ' time_of_publication, link_thumb_small, link_thumb_mid) VALUES (\'%s\', \'%s\', \'%s\', ' \
                              '%s, \'%s\',\'%s\', \'%s\', \'%s\', \'%s\', \'%s\', \'%s\', \'%s\', \'%s\',\'%s\', ' \
                              '\'%s\', \'%s\', \'%s\',\'%s\')' % (
                row[0],
                row[1].replace('\'', '\'\''),
                row[2].replace('\'', '\'\''),
                '\'%s\'' % row[3] if len(row[3]) > 0 else 'Null',
                row[4].replace('\'', '\'\''),
                row[5],
                row[6],
                row[7],
                row[8],
                row[9],
                row[10],
                row[11],
                row[12],
                row[13].replace('http', 'https'),
                row[14].replace('http', 'https'),
                row[15],
                row[16].replace('http', 'https'),
                row[17].replace('http', 'https'),
            )
            print(insertStatement)
            trgCur.execute(insertStatement)

            # Update map_scale original_maps
            if len(row[6]) > 0 and ':' in row[6]:
                newScale = int(row[6].split(':')[1])
                updateStatement = 'UPDATE original_maps SET map_scale = %s WHERE id = %s' % (
                    newScale if newScale > 0 else 'Null',
                    row[0]
                )
                print(updateStatement)
                trgCur.execute(updateStatement)

        # Commit writes
        trgConn.commit()

        print('======================================================')
        print('Finished migration of database "metadata".')
        print('======================================================')
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if srcCur != None:
            srcCur.close()
        if trgCur != None:
            trgCur.close()

def doMigrationTableOriginalMaps(srcConn, trgConn):
    """ Migrations the data "original_maps" from the src database to the target database.

    :param srcConn: Database connection to the source database
    :type srcConn: psycopg2.connection
    :param trgConn: Database connection to the target database
    :type trgConn: psycopg2.connection
    """
    print('Migrate database "original_maps" ...')

    srcCur = None
    trgCur = None
    try:
        srcCur = srcConn.cursor()
        trgCur = trgConn.cursor()

        # Query source database and write records into trg database
        srcCur.execute('SELECT id, apsdateiname, istaktiv, maptype, recommendedsrid, originalimage FROM map')
        for row in srcCur.fetchall():
            # Transform path to relative path
            pathParts = row[5].split('/')
            newPath = './'+ '/'.join([pathParts[-2], pathParts[-1]])

            # Insert values into database
            insertStatement = 'INSERT INTO original_maps(id, file_name, enabled, map_type, default_srs, rel_path) VALUES (%s, \'%s\', %s, \'%s\', %s, \'%s\')' % (
                row[0],
                row[1],
                row[2],
                row[3],
                row[4],
                newPath
            )
            trgCur.execute(insertStatement)
            print(insertStatement)

        # Because of insert statements the data hase to be connected
        trgConn.commit()

        print('======================================================')
        print('Finished migration of database "original_maps".')
        print('======================================================')
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if srcCur != None:
            srcCur.close()
        if trgCur != None:
            trgCur.close()

def doMigrationTableJobs(srcConn, trgConn):
    """ Migrations the data "jobs" from the src database to the target database.

    :param srcConn: Database connection to the source database
    :type srcConn: psycopg2.connection
    :param trgConn: Database connection to the target database
    :type trgConn: psycopg2.connection
    """
    print('Migrate database "jobs" ...')

    srcCur = None
    trgCur = None
    try:
        srcCur = srcConn.cursor()
        trgCur = trgConn.cursor()

        # Query source database and write records into trg database
        srcCur.execute('SELECT id, processed, georefid, setto, timestamp, userid, comment FROM adminjobs')
        for row in srcCur.fetchall():
            # Insert values into database
            insertStatement = 'INSERT INTO jobs(id, processed, task, task_name, submitted, user_id) VALUES (%s, %s, \'%s\', \'%s\', \'%s\', \'%s\')' % (
                row[0],
                row[1],
                json.dumps({
                    'transformation_id': row[2],
                    'comment': row[6]
                }),
                TaskValues.TRANSFORMATION_SET_VALID.value if row[3] == 'isvalide' else TaskValues.TRANSFORMATION_SET_INVALID.value,
                row[4],
                row[5]
            )
            trgCur.execute(insertStatement)
            print(insertStatement)

        # Because of insert statements the data hase to be connected
        trgConn.commit()

        print('======================================================')
        print('Finished migration of database "jobs".')
        print('======================================================')
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if srcCur != None:
            srcCur.close()
        if trgCur != None:
            trgCur.close()

def doMigrationTableTransformations(srcConn, trgConn):
    """ Migrations the data for the "transformations" table from the src database to the target database. The migration of the table
        "original_maps" has to be finished.

    :param srcConn: Database connection to the source database
    :type srcConn: psycopg2.connection
    :param trgConn: Database connection to the target database
    :type trgConn: psycopg2.connection
    """
    print('Migrate database "transformations" ...')

    srcCur = None
    trgCur = None
    try:
        srcCur = srcConn.cursor()
        trgCur = trgConn.cursor()

        # Query source database and write records into trg database
        srcCur.execute('SELECT id, timestamp, nutzerid, georefparams, adminvalidation, mapid, overwrites, comment, clip, algorithm FROM georeferenzierungsprozess')
        for row in srcCur.fetchall():
            params = json.loads(row[3])
            params['algorithm'] = row[9]
            # Create insert statement for metadata table
            insertStatement = 'INSERT INTO transformations(id, submitted, user_id, params, validation, ' \
                              'original_map_id, overwrites, comment, clip) VALUES (%s, \'%s\', \'%s\', ' \
                              '\'%s\',\'%s\', %s, %s, %s, %s)' % (
                row[0],
                row[1],
                row[2],
                json.dumps(params),
                'valid' if row[4] == 'isvalide' else 'invalid' if row[4] == 'invalide' else 'missing',
                row[5],
                row[6],
                '\'%s\'' % row[7] if row[7] != None else 'Null',
                '\'%s\'' % row[8] if row[8] != None else 'Null',
            )
            print(insertStatement)
            trgCur.execute(insertStatement)

        # Commit writes
        trgConn.commit()

        print('======================================================')
        print('Finished migration of database "transformations".')
        print('======================================================')
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if srcCur != None:
            srcCur.close()
        if trgCur != None:
            trgCur.close()

def doMigrationTableGeorefMaps(srcConn, trgConn):
    """ Migrations the data for the "georef_maps" table from the src database to the target database. The migration of the table
        "original_maps" has to be finished.

    :param srcConn: Database connection to the source database
    :type srcConn: psycopg2.connection
    :param trgConn: Database connection to the target database
    :type trgConn: psycopg2.connection
    """
    print('Migrate database "georef_maps" ...')

    srcCur = None
    trgCur = None
    try:
        srcCur = srcConn.cursor()
        trgCur = trgConn.cursor()

        # Query source database and write records into trg database
        srcCur.execute('select m.id as original_map_id, g.id as transformation_id, m.georefimage, m.boundingbox, g.timestamp from georeferenzierungsprozess g, map m where g.isactive = true and g.mapid  = m.id')
        for row in srcCur.fetchall():
            # Transform path to relative path
            pathParts = row[2].split('/')
            newPath = './'+ '/'.join([pathParts[-2], pathParts[-1]])

            # Create insert statement for metadata table
            insertStatement = 'INSERT INTO georef_maps(original_map_id, transformation_id, rel_path, extent, last_processed) VALUES (%s, %s, \'%s\', \'%s\', \'%s\')' % (
                row[0],
                row[1],
                newPath,
                row[3],
                row[4],
            )
            print(insertStatement)
            trgCur.execute(insertStatement)

        # Commit writes
        trgConn.commit()

        print('======================================================')
        print('Finished migration of database "georef_maps".')
        print('======================================================')
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if srcCur != None:
            srcCur.close()
        if trgCur != None:
            trgCur.close()

def getConnection(conn_params):
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
    srcConn = None
    trgConn = None
    try:
        print('Initialize connections and clean the target database')
        srcConn = getConnection({
            'host':'localhost',
            'database':'vkdb-migration',
            'user':'postgres',
            'password':'postgres'
        })
        trgConn = getConnection({
            'host':'localhost',
            'database':'vkdb-new',
            'user':'postgres',
            'password':'postgres'
        })

        print('Clean up target database')
        doTrgDbClean(trgConn)

        print('Start migration ...')
        doMigrationTableOriginalMaps(srcConn, trgConn)
        doMigrationTableMetadata(srcConn, trgConn)
        doMigrationTableTransformations(srcConn, trgConn)
        doMigrationTableJobs(srcConn, trgConn)
        doMigrationTableGeorefMaps(srcConn, trgConn)
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if srcConn != None:
            srcConn.close()
            print('Close source database connection.')
        if trgConn != None:
            trgConn.close()
            print('Close target database connection.')
