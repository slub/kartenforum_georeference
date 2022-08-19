#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 09.03.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import json

from georeference.jobs.actions.disable_transformation import run_disable_transformation
from georeference.jobs.actions.enable_transformation import run_enable_transformation
from georeference.models.georef_maps import GeorefMap
from georeference.models.jobs import EnumJobType
from georeference.models.transformations import Transformation, EnumValidationValue


def run_process_new_validation(es_index, dbsession, logger, job):
    """ Runs jobs of type "transformation_process"

    :param es_index: Elasticsearch client
    :type es_index: elasticsearch.Elasticsearch
    :param dbsession: Database session
    :type dbsession: sqlalchemy.orm.session.Session
    :param logger: Logger
    :type logger: logging.Logger
    :param job: Job which will be processed
    :type job: georeference.models.jobs.Job
    """
    # Query the associated transformation process
    jobs_desc = json.loads(job.description)
    transformation_obj = Transformation.by_id(jobs_desc['transformation_id'], dbsession)

    # Update transformation object
    transformation_obj.validation = EnumValidationValue.VALID.value if job.type == EnumJobType.TRANSFORMATION_SET_VALID.value else EnumValidationValue.INVALID.value
    transformation_obj.comment = jobs_desc['comment'] if 'comment' in jobs_desc else None

    logger.debug('Set transformation %s to %s.' % (transformation_obj.id, transformation_obj.validation))

    # Check if there is a georef map registered for the given transformation and if not activate one. If
    # not we finish here simply with update the validation
    if job.type == EnumJobType.TRANSFORMATION_SET_VALID.value and GeorefMap.by_raw_map_id(transformation_obj.raw_map_id,
                                                                                    dbsession) is None:
        # In this case we have a valid transformation but not a GeorefMap object enabled. So based on the
        # valid transformation we enable one.
        run_enable_transformation(
            transformation_obj,
            es_index,
            dbsession,
            logger
        )

    elif job.type == EnumJobType.TRANSFORMATION_SET_INVALID.value:
        # Try to query a previous transformation
        prev_transformation_obj = Transformation.query_previous_valid_transformation(
            transformation_obj,
            dbsession,
            logger
        )

        # If there is no previous valid transformation, but a currently active georef map, then disable it.
        active_georef_map_obj = GeorefMap.by_transformation_id(transformation_obj.id, dbsession)
        if prev_transformation_obj is None and active_georef_map_obj is not None:
            logger.debug('Disable georef map for transformation with id %s ...' % transformation_obj.id)
            run_disable_transformation(
                transformation_obj,
                es_index,
                dbsession,
                logger
            )

        # If there is a previous valid transformation, enable it
        if prev_transformation_obj is not None and active_georef_map_obj is not None:
            logger.debug('Enable older transformation with id %s ...' % prev_transformation_obj.id)
            run_enable_transformation(
                prev_transformation_obj,
                es_index,
                dbsession,
                logger
            )
