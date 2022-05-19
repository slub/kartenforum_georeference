#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 09.03.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import json

from georeference.jobs.actions.enable_transformation import run_enable_transformation
from georeference.models.transformations import Transformation


def run_process_new_transformation(esIndex, dbsession, logger, job):
    """ Runs jobs of type "transformation_process"

    :param esIndex: Elasticsearch client
    :type esIndex: elasticsearch.Elasticsearch
    :param dbsession: Database session
    :type dbsession: sqlalchemy.orm.session.Session
    :param logger: Logger
    :type logger: logging.Logger
    :param job: Job which will be processed
    :type job: georeference.models.jobs.Job
    """
    logger.info('Start processing transformation job ...')
    # Query the associated transformation process
    transformation = Transformation.by_id(json.loads(job.description)['transformation_id'], dbsession)

    # Process the transformation
    transformation = run_enable_transformation(
        transformation,
        esIndex,
        dbsession,
        logger
    )
