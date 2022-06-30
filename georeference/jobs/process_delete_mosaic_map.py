#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 23.06.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import json
import os
import shutil
import traceback
from georeference.models.jobs import EnumJobType
from georeference.models.mosaic_maps import MosaicMap
from georeference.settings import ES_INDEX_NAME, PATH_MAPFILE_ROOT, PATH_MOSAIC_ROOT
from georeference.utils.mosaics import get_mosaic_dataset_path, get_mosaic_mapfile_path
from georeference.utils.parser import to_public_mosaic_map_id


def run_process_delete_mosiac_map(es_index, dbsession, logger, job):
    """ Runs jobs of type "mosaic_map_delete"

    :param es_index: Elasticsearch client
    :type es_index: elasticsearch.Elasticsearch
    :param dbsession: Database session
    :type dbsession: sqlalchemy.orm.session.Session
    :param logger: Logger
    :type logger: logging.Logger
    :param job: Job which will be processed
    :type job: georeference.models.jobs.Job
    """
    logger.debug('Start processing delete mosaic job ...')

    if job.type != EnumJobType.MOSAIC_MAP_DELETE.value:
        raise Exception(f'The job type {job.type} is not supported through this function.')

    # Parse job information
    job_desc = json.loads(job.description)
    mosaic_map_id = job_desc['mosaic_map_id']
    mosaic_map_name = None

    try:
        # 1. Check if mosaic map exists and if yes delete it
        mosaic_map_obj = MosaicMap.by_id(mosaic_map_id, dbsession)

        if mosaic_map_obj is not None:
            mosaic_map_name = mosaic_map_obj.name
            dbsession.delete(mosaic_map_obj)
            logger.debug(f'Successfully delete mosaic map {mosaic_map_id} from database.')
            dbsession.commit()
        else:
            logger.debug(f'Could not find mosaic map with id {mosaic_map_id} in database.')

        # 2. Remove mosaic map from index
        logger.debug(f'Remove mosaic map with id {mosaic_map_id} from search index.')
        es_index.delete(index=ES_INDEX_NAME, doc_type=None, id=to_public_mosaic_map_id(mosaic_map_id))

        if mosaic_map_name is not None:
            # Remove mosaic map services
            mosaic_mapfile_path = get_mosaic_mapfile_path(PATH_MAPFILE_ROOT, mosaic_map_obj.name)
            logger.debug(f'Remove mosaic mapfile {mosaic_mapfile_path} ...')
            if os.path.exists(mosaic_mapfile_path):
                os.remove(mosaic_mapfile_path)

            # Remove mosaic map dataset
            trg_mosaic_dataset = get_mosaic_dataset_path(PATH_MOSAIC_ROOT, mosaic_map_name)
            logger.debug(f'Remove mosaic dataset {trg_mosaic_dataset} ...')
            if os.path.exists(trg_mosaic_dataset):
                shutil.rmtree(os.path.dirname(trg_mosaic_dataset))

    except Exception as e:
        logger.error('Error while running the daemon')
        logger.error(e)
        logger.error(traceback.format_exc())
        raise


