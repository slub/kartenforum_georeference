#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 09.03.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import json
import os
import traceback
from georeference.jobs.actions.create_geo_image import run_process_geo_image
from georeference.jobs.actions.create_tms import run_process_tms
from georeference.jobs.actions.create_geo_services import run_process_geo_services
from georeference.utils.utils import get_extent_as_geojson_polygon, get_geometry, get_mapfile_id, get_mapfile_path, \
    get_tms_directory
from georeference.models.georef_maps import GeorefMap
from georeference.models.metadata import Metadata
from georeference.models.raw_maps import RawMap
from georeference.models.transformations import Transformation
from georeference.settings import ES_ROOT, ES_INDEX_NAME
from georeference.utils.es import generate_es_document, get_es_index


def run_initialize_data(dbsession, logger, overwrite_map_scale=False):
    """ This job checks the database and initially builds the index and missing georeference images.

    :param dbsession: Database session object
    :type dbsession: sqlalchemy.orm.session.Session
    :param logger: Logger
    :type logger: logging.Logger
    :param overwrite_map_scale: Allows a default setting of the map_scale used for tms cache generation. In production
        this parameter should be skipped. In testing this parameter can be used for allow faster test excution, because
        the tms generation is a long running process. (Default: False)
    :type overwrite_map_scale: bool
    :result: True if performed successfully
    :rtype: bool
    """
    try:
        logger.info('Run initialization job ...')
        logger.debug('Create index ...')
        es_index = get_es_index(ES_ROOT, ES_INDEX_NAME, True, logger)

        logger.debug('Start processing all active maps ...')
        for raw_map_obj in RawMap.all(dbsession):
            georef_map_obj = GeorefMap.by_raw_map_id(raw_map_obj.id, dbsession)
            metadata_obj = Metadata.by_map_id(raw_map_obj.id, dbsession)

            # If a georef map is registered within the database, make sure that also an geo image, a tms cache and
            # geo service (mapfile) does exist.
            if georef_map_obj != None and os.path.exists(raw_map_obj.get_abs_path()):
                transformation_obj = Transformation.by_id(georef_map_obj.transformation_id, dbsession)

                # Make sure to process the geo image. We do not use the "force" parameter, which skips this
                # step in case a geo image already exists
                path_geo_image = run_process_geo_image(
                    transformation_obj,
                    raw_map_obj.get_abs_path(),
                    georef_map_obj.get_abs_path(),
                    logger=logger,
                    clip=Transformation.get_valid_clip_geometry(georef_map_obj.transformation_id,
                                                                dbsession=dbsession) if transformation_obj.clip is not None else None
                )

                logger.debug('Update the extent of the georef map object ...')
                georef_map_obj.extent = json.dumps(
                    get_extent_as_geojson_polygon(georef_map_obj.get_abs_path())
                )

                # Process the tms cache
                run_process_tms(
                    get_tms_directory(raw_map_obj),
                    path_geo_image,
                    logger=logger,
                    map_scale=10000000 if overwrite_map_scale == True else raw_map_obj.map_scale,
                )

                # Process the map file
                run_process_geo_services(
                    get_mapfile_path(raw_map_obj),
                    path_geo_image,
                    get_mapfile_id(raw_map_obj),
                    raw_map_obj.file_name,
                    metadata_obj.title_short,
                    logger,
                    with_wcs=True
                )

            # Synchronise the index with the current state of the raw map objects.
            logger.debug(f'Write search record for raw map id {raw_map_obj.id} to index ...')
            document = generate_es_document(
                raw_map_obj,
                Metadata.by_map_id(raw_map_obj.id, dbsession),
                georef_map_obj=georef_map_obj if georef_map_obj is not None and os.path.exists(
                    georef_map_obj.get_abs_path()) else None,
                logger=logger,
                geometry=get_geometry(raw_map_obj.id, dbsession)
            )
            es_index.index(
                index=ES_INDEX_NAME,
                doc_type=None,
                id=document['map_id'],
                body=document
            )

        logger.info('Finish initalization job.')
        return True
    except Exception as e:
        logger.error('Error while trying to process initialisation job.')
        logger.error(e)
        logger.error(traceback.format_exc())
