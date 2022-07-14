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

# For correct resolving of the paths we use derive the base_path of the file
BASE_PATH = os.path.dirname(os.path.realpath(__file__))
BASE_PATH_PARENT = os.path.abspath(os.path.join(BASE_PATH, '../../'))
sys.path.insert(0, BASE_PATH)
sys.path.append(BASE_PATH_PARENT)

from georeference.scripts import initialize_logger, initialize_database_session
from georeference.jobs.initialize_data import run_initialize_data

if __name__ == '__main__':
    LOGGER = initialize_logger(
        logging.StreamHandler()
    )

    LOGGER.info('Start syncing files and search documents...')
    try:
        dbsession = initialize_database_session(
            os.path.join(BASE_PATH, '../../production.ini')
        )
        run_initialize_data(
            dbsession=dbsession,
            logger=LOGGER
        )
        LOGGER.info('Finish sync.')
    except Exception as e:
        LOGGER.error('Error while syncing files and search documents-')
        LOGGER.error(e)
        LOGGER.error(traceback.format_exc())