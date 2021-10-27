#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 26.10.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
#
# This script can be used to initial synchronise the data:
# * Creates the georeference files if not exist
# * Create the tms services
# * Create the mapfiles for the wms / wcs services
# * Writes the es documents
import os
import logging
import traceback
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from pyramid.paster import get_appsettings
from logging.handlers import TimedRotatingFileHandler

# For correct resolving of the paths we use derive the base_path of the file
BASE_PATH = os.path.dirname(os.path.realpath(__file__))
BASE_PATH_PARENT = os.path.abspath(os.path.join(BASE_PATH, '../../'))
sys.path.insert(0, BASE_PATH)
sys.path.append(BASE_PATH_PARENT)

from georeference.settings import DAEMON_LOGGER_SETTINGS
from georeference.utils.logging import createLogger
from georeference.daemon.jobs import loadInitialData



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
        logging.Formatter(DAEMON_LOGGER_SETTINGS['formatter'])
    )

    # Create and initialize the logger
    return createLogger(
        DAEMON_LOGGER_SETTINGS['name'],
        DAEMON_LOGGER_SETTINGS['level'],
        handler = handler,
    )

#
# Initialize TimedRotatingFileHandler and LOGGER
#

LOGGER = initializeLogger(
    logging.StreamHandler()
)

LOGGER.info('Start syncing files and search documents...')
try:
    dbsession = initializeDatabaseSession()
    loadInitialData(
        dbsession=dbsession,
        logger=LOGGER
    )
    LOGGER.info('Finish sync.')
except Exception as e:
    LOGGER.error('Error while syncing files and search documents-')
    LOGGER.error(e)
    LOGGER.error(traceback.format_exc())