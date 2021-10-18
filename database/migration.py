#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 18.10.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import psycopg2

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
    """ Migrations the data from "metadata" table of the src database to the target database. The migration of the table
        "original_maps" has to be finished.

    :param srcConn: Database connection to the source database
    :type srcConn: psycopg2.connection
    :param trgConn: Database connection to the target database
    :type trgConn: psycopg2.connection
    """
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
    """ Migrations the data from the table "original_maps" of the src database to the target database.

    :param srcConn: Database connection to the source database
    :type srcConn: psycopg2.connection
    :param trgConn: Database connection to the target database
    :type trgConn: psycopg2.connection
    """
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

def doMigrationTableTransformations(srcConn, trgConn):
    """ Migrations the data for the "transformations" table from the src database to the target database. The migration of the table
        "original_maps" has to be finished.

    :param srcConn: Database connection to the source database
    :type srcConn: psycopg2.connection
    :param trgConn: Database connection to the target database
    :type trgConn: psycopg2.connection
    """
    srcCur = None
    trgCur = None
    try:
        srcCur = srcConn.cursor()
        trgCur = trgConn.cursor()

        # Query source database and write records into trg database
        srcCur.execute('SELECT id, timestamp, nutzerid, georefparams, adminvalidation, mapid, overwrites, comment, clip FROM georeferenzierungsprozess')
        for row in srcCur.fetchall():
            # Create insert statement for metadata table
            insertStatement = 'INSERT INTO transformations(id, submitted, user_id, params, validation, ' \
                              'original_map_id, overwrites, comment, clip) VALUES (%s, \'%s\', \'%s\', ' \
                              '\'%s\',\'%s\', %s, %s, %s, %s)' % (
                row[0],
                row[1],
                row[2],
                row[3],
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
        print('Migrate database "original_maps" ...')
        doMigrationTableOriginalMaps(srcConn, trgConn)
        print('Migrate database "metadata" ...')
        doMigrationTableMetadata(srcConn, trgConn)
        print('Migrate database "transformations" ...')
        doMigrationTableTransformations(srcConn, trgConn)
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if srcConn != None:
            srcConn.close()
            print('Close source database connection.')
        if trgConn != None:
            trgConn.close()
            print('Close target database connection.')
