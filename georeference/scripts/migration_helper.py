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

# For correct resolving of the paths we use derive the base_path of the file
BASE_PATH = os.path.dirname(os.path.realpath(__file__))
BASE_PATH_PARENT = os.path.abspath(os.path.join(BASE_PATH, '../../'))
sys.path.insert(0, BASE_PATH)
sys.path.append(BASE_PATH_PARENT)

from georeference.scripts import initialize_logger, initialize_database_session
from georeference.models.georef_maps import GeorefMap
from georeference.models.raw_maps import RawMap

def check_paths_original_images(dbsession, logger):
    """ Checks if the path exists.

    :param dbsession: Database session object
    :type dbsession: sqlalchemy.orm.session.Session
    :param logger: Logger
    :type logger: logging.Logger
    :result: True if performed successfully
    :rtype: bool
    """
    logger.info("Check for missing original images ...")
    foundImages = 0
    notFoundImages = []
    for mapObj in RawMap.all(dbsession):
        if os.path.exists(mapObj.get_abs_path()) != True and mapObj.enabled:
            notFoundImages.append(
                mapObj.get_abs_path()
            )
        else:
            foundImages += 1
    logger.info('Found %s images.' % foundImages)

    if len(notFoundImages) > 0:
        logger.info('Did not found the following images:')
        for img in notFoundImages:
            logger.info(img)
    else:
        logger.info('All images were found')

def check_paths_georef_images(dbsession, logger):
    """ Checks if the path exists.

    :param dbsession: Database session object
    :type dbsession: sqlalchemy.orm.session.Session
    :param logger: Logger
    :type logger: logging.Logger
    :result: True if performed successfully
    :rtype: bool
    """
    logger.info("Check for missing georef images ...")
    foundImages = 0
    notFoundImages = []
    for georefMapObj in GeorefMap.all(dbsession):
        if os.path.exists(georefMapObj.get_abs_path()) != True:
            notFoundImages.append(
                georefMapObj.get_abs_path()
            )
        else:
            foundImages += 1
    logger.info('Found %s images.' % foundImages)

    if len(notFoundImages) > 0:
        logger.info('Did not found the following images:')
        for img in notFoundImages:
            logger.info(img)
    else:
        logger.info('All images were found')

if __name__ == '__main__':
    LOGGER = initialize_logger(
        logging.StreamHandler()
    )

    LOGGER.info('Start running migration helper tasks...')
    try:
        dbsession = initialize_database_session(
            iniFile=os.path.join(BASE_PATH, '../../production.ini')
        )
        check_paths_original_images(dbsession, LOGGER)
        check_paths_georef_images(dbsession, LOGGER)
        LOGGER.info('Finish sync.')
    except Exception as e:
        LOGGER.error('Error while syncing files and search documents-')
        LOGGER.error(e)
        LOGGER.error(traceback.format_exc())