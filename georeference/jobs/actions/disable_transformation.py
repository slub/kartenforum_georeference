#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 09.03.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import os
import shutil

from loguru import logger

from georeference.jobs.actions.update_index import run_update_index
from georeference.models.georef_map import GeorefMap
from georeference.models.raw_map import RawMap
from georeference.utils.utils import get_mapfile_path, get_tms_directory


def run_disable_transformation(transformation_obj, es_index, dbsession):
    """This actions takes a given transformation and makes sure that this transformation is not used. It also
        removes any active TMS directories and mapfiles for the image associated with the transformation. It also updates
        the search index.

        Careful, this function would also delete tms directories or mapfiles created through another transformation, but
        for the same raw image. This scenario has to be handled on a higher level function call.

    :param transformation_obj: Transformation
    :type transformation_obj: georeference.models.transformations.Transformation
    :param es_index: Elasticsearch client
    :type es_index: elasticsearch.Elasticsearch
    :param dbsession: Database session
    :type dbsession: sqlalchemy.orm.session.Session
    """
    # Query original and georef  map obj
    raw_map_obj = RawMap.by_id(transformation_obj.raw_map_id, dbsession)
    georef_map_obj = GeorefMap.by_transformation_id(transformation_obj.id, dbsession)

    # Delete the georef object
    if georef_map_obj is not None:
        logger.debug("Delete tiff file for georeference map")
        if os.path.exists(georef_map_obj.get_abs_path()):
            os.remove(georef_map_obj.get_abs_path())

        logger.debug(
            "Delete georeference map object for original map id %s."
            % georef_map_obj.raw_map_id
        )
        dbsession.delete(georef_map_obj)
        dbsession.flush()

    # Check if there is a tms and if yes remove it
    tms_dir = get_tms_directory(raw_map_obj)
    if os.path.isdir(tms_dir):
        shutil.rmtree(tms_dir)

    # Check if there is a mapfile and remove it, if it exists
    mapfile = get_mapfile_path(raw_map_obj)
    if os.path.exists(mapfile):
        os.remove(mapfile)

    # Update the database
    dbsession.flush()

    # Write document to es
    run_update_index(es_index, raw_map_obj, None, dbsession)
