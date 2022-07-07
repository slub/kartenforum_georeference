#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 07.07.22
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

from datetime import datetime
from georeference.models.mosaic_maps import MosaicMap
from georeference.utils.mosaics import create_mosaic_overviews, get_mosaic_dataset_path
from georeference.scripts import initialize_logger, initialize_database_session
from georeference.settings import PATH_MOSAIC_ROOT

def add_overviews_to_mosaics(dbsession, mosaic_root_dir, logger):
    """ Function queries all mosaic maps from the database and checks if an mosaic map has
        updated since the last processing of overviews. If this is the case the function triggers
        an update of the overviews for the mosaics.

    :param dbsession: Database session
    :type dbsession: sqlalchemy.orm.session.Session
    :param mosaic_root_dir: Path to the mosaic root directory
    :type mosaic_root_dir: str
    :param logger: Logger
    :type logger: logging.Logger
    """

    # Query all mosaic maps and find the mosaic maps for which an update of the overviews
    # should be processed.
    for mosaic_map_obj in MosaicMap.all(dbsession):
        mosaic_dataset = get_mosaic_dataset_path(mosaic_root_dir, mosaic_map_obj.name)

        if mosaic_map_obj.last_overview_update is None or mosaic_map_obj.last_overview_update < mosaic_map_obj.last_service_update or _has_overview(mosaic_dataset) == False:
            new_datetime = datetime.now()

            dataset_overviews = create_mosaic_overviews(
                target_dataset=mosaic_dataset,
                logger=logger,
                overview_levels='4 8 16 32 64 128 256 512'
            )

            if not os.path.exists(dataset_overviews):
                error_msg = f'Something went wrong while trying to process overviews for mosaic with id {mosaic_map_obj.id}'
                logger.error(error_msg)
                raise Exception(error_msg)

            mosaic_map_obj.last_overview_update = new_datetime
            dbsession.commit()

def _has_overview(mosaic_dataset):
    """ Checks if overviews are existing for this mosaic_dataset.

    :param mosaic_dataset: Path to the mosaic dataset
    :type mosaic_dataset: str
    :result: True if an overview file exists
    :rtype: str
    """
    return os.path.exists(mosaic_dataset + '.ovr')

if __name__ == '__main__':
    LOGGER = initialize_logger(
        logging.StreamHandler()
    )

    LOGGER.info('Start running processing of overviews for mosaic maps...')
    try:
        dbsession = initialize_database_session(
            os.path.join(BASE_PATH, '../../production.ini')
        )
        add_overviews_to_mosaics(
            dbsession=dbsession,
            mosaic_root_dir=PATH_MOSAIC_ROOT,
            logger=LOGGER,
        )

        LOGGER.info('All mosaic overviews are up to date.')
    except Exception as e:
        LOGGER.error('Error while trying to calculate overviews for mosaics')
        LOGGER.error(e)
        LOGGER.error(traceback.format_exc())