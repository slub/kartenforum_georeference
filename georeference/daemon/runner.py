#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 07.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import os
import logging
import time
import signal
import daemon
import lockfile
import traceback
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from pyramid.paster import get_appsettings
from logging.handlers import TimedRotatingFileHandler
from georeference.settings import GEOREFERENCE_DAEMON_LOGGER
from georeference.settings import GEOREFERENCE_DAEMON_SETTINGS
from georeference.utils.logging import createLogger
from georeference.daemon.jobs import runInitializationJob
from georeference.daemon.jobs import runNewJobs
from georeference.daemon.jobs import runUpdateJobs

# For correct resolving of the paths we use derive the base_path of the file
BASE_PATH = os.path.dirname(os.path.realpath(__file__))

def initializeDatabaseSession():
    """ Functions loads and initialize a database session

    :result: Database session object
    :rtype: sqlalchemy.orm.session.Session
    """
    # Create database engine from production.ini configuration
    iniFile = os.path.join(BASE_PATH, '../../production.ini')
    dbengine = create_engine(
        get_appsettings(iniFile)['sqlalchemy.url'],
        encoding='utf8',
        # Set echo=True if te sqlalchemy.url logging output sould be displayed
        echo=False,
    )

    # Create and return session object
    db_sessionmaker = sessionmaker(bind=dbengine)
    Base = declarative_base()
    Base.metadata.bind = dbengine
    Base.metadata.create_all(dbengine)
    return db_sessionmaker()

def initializeLogger(handler):
    """ Function loads and create the logger for the daemon

    :param handler: Handler which should be used by the logger
    :type handler: TimedRotatingFileHandler
    :result: Logger
    :rtype: `logging.Logger`
    """
    # Configure the handler as a TimeRotatingFileHander
    handler.setFormatter(
        logging.Formatter(GEOREFERENCE_DAEMON_LOGGER['formatter'])
    )

    # Create and initialize the logger
    return createLogger(
        GEOREFERENCE_DAEMON_LOGGER['name'],
        GEOREFERENCE_DAEMON_LOGGER['level'],
        handler = handler,
    )

#
# Initialize TimedRotatingFileHandler and LOGGER
#

# Check if the file exists and if not create it
if not os.path.exists(GEOREFERENCE_DAEMON_LOGGER['file']):
    open(GEOREFERENCE_DAEMON_LOGGER['file'], 'a').close()

HANDLER = TimedRotatingFileHandler(GEOREFERENCE_DAEMON_LOGGER['file'], when='d', interval=1, backupCount=14)
LOGGER = initializeLogger(HANDLER)

# Make sure that the stdin/stdout/stderr paths exists and if not produce
if not os.path.exists(GEOREFERENCE_DAEMON_SETTINGS['stderr']):
    open(GEOREFERENCE_DAEMON_SETTINGS['stderr'], 'a').close()
if not os.path.exists(GEOREFERENCE_DAEMON_SETTINGS['stdout']):
    open(GEOREFERENCE_DAEMON_SETTINGS['stdout'], 'a').close()
if not os.path.exists(GEOREFERENCE_DAEMON_SETTINGS['stdin']):
    open(GEOREFERENCE_DAEMON_SETTINGS['stdin'], 'a').close()

def onStartUp():
    try:
        LOGGER.info('Starting the daemon ...')
        LOGGER.info('Sync index and files ...')
        dbsession = initializeDatabaseSession()
        runInitializationJob(
            dbsession=dbsession,
            logger=LOGGER
        )
        dbsession.commit()
        dbsession.close()
        LOGGER.info('Daemon finish starting and is listen for changes')
    except Exception as e:
        LOGGER.error('Error while starting the daemon')
        LOGGER.error(e)
        LOGGER.error(traceback.format_exc())

def main():
    try:
        timeToWait = GEOREFERENCE_DAEMON_SETTINGS['wait_on_startup'] if GEOREFERENCE_DAEMON_SETTINGS['wait_on_startup'] > 0 else 1
        LOGGER.info('Start logger but waiting for %s seconds ...' % timeToWait)
        time.sleep(timeToWait)

        # Start the daemon
        onStartUp()

        LOGGER.info('################################')

        while True:
            LOGGER.info('Looking for Looking for pending georeference processes ...')
            dbsession = initializeDatabaseSession()
            LOGGER.info('Check for new processes ...')
            runNewJobs(
                dbsession=dbsession,
                logger=LOGGER
            )
            dbsession.commit()
            LOGGER.info('Check for update processes ...')
            runUpdateJobs(
                dbsession=dbsession,
                logger=LOGGER
            )
            dbsession.commit()
            LOGGER.info('Go to sleep ...')
            dbsession.close()
            time.sleep(GEOREFERENCE_DAEMON_SETTINGS['sleep_time'])
    except Exception as e:
        LOGGER.error('Error while running the daemon')
        LOGGER.error(e)
        LOGGER.error(traceback.format_exc())

pidFileLock = '%s.lock' % GEOREFERENCE_DAEMON_SETTINGS['pidfile_path']
pidFile = lockfile.FileLock(GEOREFERENCE_DAEMON_SETTINGS['pidfile_path'])

def onCleanUp(a, b):
    LOGGER.info("Clean up")
    if os.path.exists(pidFileLock):
        pidFile.release()

# Initialize the daemon context
context = daemon.DaemonContext(
    # stderr=open(GEOREFERENCE_DAEMON_SETTINGS['stderr'], 'a'),
    # stdin=open(GEOREFERENCE_DAEMON_SETTINGS['stdin'], 'a'),
    # stdout=open(GEOREFERENCE_DAEMON_SETTINGS['stdout'], 'a'),
    pidfile=lockfile.FileLock(GEOREFERENCE_DAEMON_SETTINGS['pidfile_path']),
    files_preserve=[HANDLER.stream],
)

# Define shutdown behavior
context.signal_map = {
    signal.SIGTERM: onCleanUp,
    signal.SIGHUP: 'terminate',
}

if os.path.exists(pidFileLock):
    raise Exception('Please make sure old daemons are cancelled first and remove the pidfile %s.' % GEOREFERENCE_DAEMON_SETTINGS['pidfile_path'])

# Starts the daemon
with context:
    main()