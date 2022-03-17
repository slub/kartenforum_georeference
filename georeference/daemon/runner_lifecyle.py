#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 09.12.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import os
import logging
import time
import traceback
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from pyramid.paster import get_appsettings
from logging.handlers import TimedRotatingFileHandler
from georeference.settings import DAEMON_LOGGER_SETTINGS
from georeference.utils.logging import createLogger
from georeference.daemon.jobs import loadInitialData
from georeference.daemon.jobs import getUnprocessedJobs
from georeference.daemon.jobs import runProcessJobs
from georeference.daemon.jobs import runValidationJobs
from georeference.settings import ES_ROOT
from georeference.settings import ES_INDEX_NAME
from georeference.scripts.es import getIndex

def resetLogging_(logger):
    list(map(logger.removeHandler, logger.handlers))
    list(map(logger.removeFilter, logger.filters))
    logging.shutdown()

def initializeDatabaseSession_(iniFile):
    """ Functions loads and initialize a database session

    :param iniFile: File to production.ini
    :type iniFile: str
    :result: Database session object
    :rtype: sqlalchemy.orm.session.Session
    """
    # Create database engine from production.ini configuration
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

def initializeLogger_():
    """ Function loads and create the logger for the daemon

    :result: Logger
    :rtype: `logging.Logger`
    """
    # Check if the file exists and if not create it
    if not os.path.exists(DAEMON_LOGGER_SETTINGS['file']):
        open(DAEMON_LOGGER_SETTINGS['file'], 'a').close()

    handler = TimedRotatingFileHandler(DAEMON_LOGGER_SETTINGS['file'], when='d', interval=1, backupCount=14)

    # Configure the handler as a TimeRotatingFileHander
    handler.setFormatter(
        logging.Formatter(DAEMON_LOGGER_SETTINGS['formatter'])
    )

    # Create and initialize the logger
    return createLogger(
        DAEMON_LOGGER_SETTINGS['name'],
        DAEMON_LOGGER_SETTINGS['level'],
        handler = handler,
    )

def loop(dbsession, logger):
    """ Iteration holding the main functionality

    :param logger: Logger
    :type logger: logging.Logger
    :param dbsession: Database session object
    :type dbsession: sqlalchemy.orm.session.Session
    """
    try:
        logger.info('Looking for Looking for pending jobs ...')
        jobs = getUnprocessedJobs(
            dbsession=dbsession,
            logger=logger,
        )
        logger.info(jobs)

        # Check if there are process jobs to process
        if len(jobs['process']) > 0:
            esIndex = getIndex(ES_ROOT, ES_INDEX_NAME, forceRecreation=False, logger=logger)
            logger.info('Process %s jobs with task_name="transformation_process" ...' % jobs['process'])
            runProcessJobs(
                jobs['process'],
                esIndex,
                dbsession=dbsession,
                logger=logger
            )
            esIndex.close()
        dbsession.commit()

        # Check if there are validation jobs to process
        if len(jobs['validation']) > 0:
            esIndex = getIndex(ES_ROOT, ES_INDEX_NAME, forceRecreation=False, logger=logger)
            logger.info(
                'Process %s jobs with task_name="transformation_set_valid" or "transformation_set_invalid" ...' % jobs[
                    'validation'])
            runValidationJobs(
                jobs['validation'],
                esIndex,
                dbsession=dbsession,
                logger=logger
            )
            esIndex.close()
        dbsession.commit()

        logger.info('Close database connection.')
        dbsession.close()
    except Exception as e:
        logger.error('Error while running the daemon')
        logger.error(e)
        logger.error(traceback.format_exc())

def onStart(logger=None, dbsession=None):
    """Should be called once on daemon startup

    :param logger: Logger
    :type logger: logging.Logger
    :param dbsession: Database session object
    :type dbsession: sqlalchemy.orm.session.Session
    """
    try:
        logger.info('Starting the daemon ...')
        logger.info('Sync index and files ...')
        loadInitialData(dbsession, logger)
        dbsession.commit()
        dbsession.close()
        logger.info('Daemon finish starting and is listen for changes')
    except Exception as e:
        logger.error('Error while starting the daemon')
        logger.error(e)
        logger.error(traceback.format_exc())

def main(logger=None, dbsession=None, iniFile=None, waitOnStart=1, waitOnLoop=1):
    """ Daemon main run.

    :param logger: Logger
    :type logger: logging.Logger
    :param dbsession: Database session object
    :type dbsession: sqlalchemy.orm.session.Session
    :param iniFile: File to production.ini
    :type iniFile: str
    :param waitOnStart: Seconds to wait on startup
    :type waitOnStart: int
    :param waitOnLoop: Seconds to wait after each loop
    :type waitOnLoop: int
    """
    try:
        log = initializeLogger_() if logger == None else logger
        log.info('Start logger but waiting for %s seconds ...' % waitOnStart)
        time.sleep(waitOnStart)

        # Start the daemon
        db = initializeDatabaseSession_(iniFile) if iniFile != None else dbsession
        if db == None:
            logger.error("Could not initialize database because of missing configuration file")
            raise

        onStart(logger=log, dbsession=db)

        while True:
            if logger == None:
                # In the logger was passed external we skip the temporal shutdown
                resetLogging_(log)

            # To prevent the daemon from having to long lasting logger handles or database session we reinitialize / reset
            # both before each loop
            log = initializeLogger_() if logger == None else logger
            log.info('################################')
            log.debug('Initialize database')
            db = initializeDatabaseSession_(iniFile) if iniFile != None else dbsession
            loop(db, log)
            log.info('Sleep for %s seconds.' % waitOnLoop)
            time.sleep(waitOnLoop)
    except Exception as e:
        log.error('Error while running the daemon')
        log.error(e)
        log.error(traceback.format_exc())
    finally:
        log.info("Clean up")
        logging.shutdown()