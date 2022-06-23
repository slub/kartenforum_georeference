#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 23.06.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import json

from georeference.jobs.actions.enable_transformation import run_enable_transformation
from georeference.models.transformations import Transformation


def run_process_create_mosiac_map(es_index, dbsession, logger, job):
    """ Runs jobs of type "mosaic_map_create"

    :param es_index: Elasticsearch client
    :type es_index: elasticsearch.Elasticsearch
    :param dbsession: Database session
    :type dbsession: sqlalchemy.orm.session.Session
    :param logger: Logger
    :type logger: logging.Logger
    :param job: Job which will be processed
    :type job: georeference.models.jobs.Job
    """
    logger.info('Start processing create mosaic job ...')

    # TODOs (Do not forget that create is also update
    # Precheck: In a higher order component it should make clear that, this job is only run once per daemon run
    # 1. Create the mosaic dataset in a tmp folder
    # 2. Create the map services in a tmp folder
    # 3. Copy (Replace old) the dataset and services to the target directory
    # 4. Update the index
    # 5. Update the job and mosaicmap database object


