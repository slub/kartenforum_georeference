#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 09.03.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import json

from loguru import logger

from georeference.jobs.actions.create_geo_image import run_process_geo_image
from georeference.jobs.actions.create_geo_services import run_process_geo_services
from georeference.jobs.actions.create_tms import run_process_tms
from georeference.jobs.actions.update_index import run_update_index
from georeference.models.georef_map import GeorefMap
from georeference.models.metadata import Metadata
from georeference.models.raw_map import RawMap
from georeference.models.transformation import Transformation
from georeference.utils.utils import (
    get_extent_as_geojson_polygon,
    get_mapfile_id,
    get_mapfile_path,
    get_tms_directory,
)


def run_enable_transformation(transformation_obj, es_index, dbsession):
    """Enables a given transformation. This means it process a geo image based on the transformation and creates/updates
        the GeorefMap object. Further it creates a tms directories and the mapfiles for serving WMS / WCS services. It also
        updates the elasticsearch index.

    :param transformation_obj: Transformation
    :type transformation_obj: georeference.models.transformations.Transformation
    :param es_index: Elsaticsearch client
    :type es_index: elasticsearch.Elasticsearch
    :param dbsession: Database session
    :type dbsession: sqlalchemy.orm.session.Session
    :result: Transformation
    :rtype: georeference.models.transformations.Transformation
    """
    if transformation_obj is None:
        raise ValueError("Transformation object is None!")

    logger.debug("Enable transformation %s ..." % transformation_obj.id)
    # Query original and georef  map obj
    raw_map_obj = RawMap.by_id(transformation_obj.raw_map_id, dbsession)
    georef_map_obj = GeorefMap.by_raw_map_id(transformation_obj.raw_map_id, dbsession)
    metadata_obj = Metadata.by_map_id(raw_map_obj.id, dbsession)

    # In case a georefMapObj does not exist, create a new one
    if georef_map_obj is None:
        logger.debug(
            "Create new georef map object for original map id %s." % raw_map_obj.id
        )
        georef_map_obj = GeorefMap.from_raw_map_and_transformation(
            raw_map_obj, transformation_obj
        )
        dbsession.add(georef_map_obj)
        dbsession.flush()

    # Make sure to process the geo image. We do not use the "force" parameter, which skips this
    # step in case a geo image already exists
    path_geo_image = run_process_geo_image(
        transformation_obj,
        raw_map_obj.get_abs_path(),
        georef_map_obj.get_abs_path(),
        force=True,
        clip=Transformation.get_valid_clip_geometry(
            georef_map_obj.transformation_id, dbsession=dbsession
        )
        if transformation_obj.clip is not None
        else None,
    )

    logger.debug("Update the extent of the georef map object ...")
    georef_map_obj.extent = json.dumps(
        get_extent_as_geojson_polygon(georef_map_obj.get_abs_path())
    )

    run_process_tms(get_tms_directory(raw_map_obj), path_geo_image, force=True)

    # Process the map file
    run_process_geo_services(
        get_mapfile_path(raw_map_obj),
        path_geo_image,
        get_mapfile_id(raw_map_obj),
        raw_map_obj.file_name,
        metadata_obj.title_short,
        with_wcs=True,
        force=True,
    )

    logger.info(f"{transformation_obj.id}")

    # Update the transformation_id
    georef_map_obj.transformation_id = transformation_obj.id

    # Make sure that all changes are persistet to the database
    dbsession.flush()

    # Write document to es
    run_update_index(es_index, raw_map_obj, georef_map_obj, dbsession)

    return transformation_obj
