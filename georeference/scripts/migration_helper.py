#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 15.12.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
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

from georeference.models.original_maps import OriginalMap
from georeference.settings import DAEMON_LOGGER_SETTINGS
from georeference.utils.logging import createLogger


def initializeDatabaseSession_():
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

def initializeLogger_(handler):
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

def checkPaths(dbsession, logger):
    """ Checks if the path exists.

    :param dbsession: Database session object
    :type dbsession: sqlalchemy.orm.session.Session
    :param logger: Logger
    :type logger: logging.Logger
    :result: True if performed successfully
    :rtype: bool
    """
    logger.info("Check for missing original images ...")
    for mapObj in OriginalMap.all(dbsession):
        if os.path.exists(mapObj.getAbsPath()) != True:
            logger.info(mapObj.getAbsPath())

#
# Initialize TimedRotatingFileHandler and LOGGER
#

LOGGER = initializeLogger_(
    logging.StreamHandler()
)

LOGGER.info('Start running migration helper tasks...')
try:
    dbsession = initializeDatabaseSession_()
    checkPaths(dbsession, LOGGER)
    LOGGER.info('Finish sync.')
except Exception as e:
    LOGGER.error('Error while syncing files and search documents-')
    LOGGER.error(e)
    LOGGER.error(traceback.format_exc())