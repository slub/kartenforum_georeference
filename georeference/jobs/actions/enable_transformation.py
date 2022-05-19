#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 09.03.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import json
from georeference.jobs.actions.create_geo_image import run_process_geo_image
from georeference.jobs.actions.create_tms import run_process_tms
from georeference.jobs.actions.create_geo_services import run_process_geo_services
from georeference.jobs.actions.update_index import run_update_index
from georeference.utils.utils import get_extent_as_geojson_polygon, get_mapfile_id, get_mapfile_path, get_tms_directory
from georeference.models.georef_maps import GeorefMap
from georeference.models.metadata import Metadata
from georeference.models.raw_maps import RawMap
from georeference.models.transformations import Transformation


def run_enable_transformation(transformation_obj, es_index, dbsession, logger):
    """ Enables a given transformation. This means it process a geo image based on the transformation and creates/updates
        the GeorefMap object. Further it creates a tms directories and the mapfiles for serving WMS / WCS services. It also
        updates the elasticsearch index.

    :param transformation_obj: Transformation
    :type transformation_obj: georeference.models.transformations.Transformation
    :param es_index: Elsaticsearch client
    :type es_index: elasticsearch.Elasticsearch
    :param dbsession: Database session
    :type dbsession: sqlalchemy.orm.session.Session
    :param logger: Logger
    :type logger: logging.Logger
    :result: Transformation
    :rtype: georeference.models.transformations.Transformation
    """
    logger.debug('Enable transformation %s ...' % transformation_obj.id)
    # Query original and georef  map obj
    rawMapObj = RawMap.by_id(transformation_obj.raw_map_id, dbsession)
    georefMapObj = GeorefMap.by_raw_map_id(transformation_obj.raw_map_id, dbsession)
    metadataObj = Metadata.by_map_id(rawMapObj.id, dbsession)

    # In case a georefMapObj does not exist, create a new one
    if georefMapObj == None:
        logger.debug('Create new georef map object for original map id %s.' % rawMapObj.id)
        georefMapObj = GeorefMap.from_raw_map_and_transformation(rawMapObj, transformation_obj)
        dbsession.add(georefMapObj)
        dbsession.flush()

    # Make sure to process the geo image. We do not use the "force" parameter, which skips this
    # step in case a geo image already exists
    pathGeoImage = run_process_geo_image(
        transformation_obj,
        rawMapObj.get_abs_path(),
        georefMapObj.get_abs_path(),
        logger=logger,
        force=True,
        clip=Transformation.get_valid_clip_geometry(georefMapObj.transformation_id, dbsession=dbsession) if transformation_obj.clip is not None else None

    )

    logger.debug('Update the extent of the georef map object ...')
    georefMapObj.extent = json.dumps(
        get_extent_as_geojson_polygon(georefMapObj.get_abs_path())
    )

    run_process_tms(
        get_tms_directory(rawMapObj),
        pathGeoImage,
        logger=logger,
        map_scale=rawMapObj.map_scale,
        force=True
    )

    # Process the map file
    run_process_geo_services(
        get_mapfile_path(rawMapObj),
        pathGeoImage,
        get_mapfile_id(rawMapObj),
        rawMapObj.file_name,
        metadataObj.title_short,
        logger,
        with_wcs=True,
        force=True
    )

    logger.info(f'{transformation_obj.id}')

    # Update the transformation_id
    georefMapObj.transformation_id = transformation_obj.id

    # Make sure that all changes are persistet to the database
    dbsession.flush()

    # Write document to es
    run_update_index(
        es_index,
        rawMapObj,
        georefMapObj,
        dbsession,
        logger
    )

    return transformation_obj
