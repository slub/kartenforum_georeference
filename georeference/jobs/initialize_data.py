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
from georeference.jobs.process_create_mosaic_map import push_mosaic_to_es_index
from georeference.utils.es_index import generate_es_original_map_document, get_es_index
from georeference.utils.mosaics import get_mosaic_dataset_path
from georeference.utils.utils import get_extent_as_geojson_polygon, get_geometry, get_mapfile_id, get_mapfile_path, \
    get_tms_directory
from georeference.models.georef_maps import GeorefMap
from georeference.models.metadata import Metadata
from georeference.models.mosaic_maps import MosaicMap
from georeference.models.raw_maps import RawMap
from georeference.models.transformations import Transformation
from georeference.settings import PATH_MOSAIC_ROOT, ES_ROOT, ES_INDEX_NAME


def run_initialize_data(dbsession, logger):
    """ This job checks the database and initially builds the index and missing georeference images.

    :param dbsession: Database session object
    :type dbsession: sqlalchemy.orm.session.Session
    :param logger: Logger
    :type logger: logging.Logger
    :result: True if performed successfully
    :rtype: bool
    """
    try:
        logger.info('Run initialization job ...')
        logger.info('Create index ...')
        es_index = get_es_index(ES_ROOT, ES_INDEX_NAME, True, logger)

        logger.info('Start processing all single sheet maps ...')
        for raw_map_obj in RawMap.all(dbsession):
            logger.info(f'Initialize single sheet map with id {raw_map_obj.id} ...')
            georef_map_obj = GeorefMap.by_raw_map_id(raw_map_obj.id, dbsession)
            metadata_obj = Metadata.by_map_id(raw_map_obj.id, dbsession)

            # If a georef map is registered within the database, make sure that also a geo image, a tms cache and
            # geo service (mapfile) does exist.
            if georef_map_obj is not None and os.path.exists(raw_map_obj.get_abs_path()):
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
            try:
                logger.debug(f'Write search record for raw map id {raw_map_obj.id} to index ...')
                document = generate_es_original_map_document(
                    raw_map_obj,
                    Metadata.by_map_id(raw_map_obj.id, dbsession),
                    georef_map_obj=georef_map_obj if georef_map_obj is not None and os.path.exists(
                        georef_map_obj.get_abs_path()) else None,
                    logger=logger,
                    geometry=get_geometry(raw_map_obj.id, dbsession)
                )
                logger.debug(document)
                es_index.index(
                    index=ES_INDEX_NAME,
                    doc_type=None,
                    id=document['map_id'],
                    body=document
                )
            except Exception as e:
                logger.error('Error while trying to write single sheet document to index')
                logger.error(e)
                logger.error(traceback.format_exc())
        logger.info('Finish initializing single sheet maps.')

        logger.info('Start processing all mosaic maps ...')
        for mosaic_map_obj in MosaicMap.all(dbsession):
            logger.info(f'Initialize mosaic map with id {mosaic_map_obj.id} ...')
            try:
                trg_mosaic_dataset = get_mosaic_dataset_path(PATH_MOSAIC_ROOT, mosaic_map_obj.name)
                push_mosaic_to_es_index(
                    es_index=es_index,
                    mosaic_map_obj=mosaic_map_obj,
                    trg_mosaic_dataset=trg_mosaic_dataset,
                    logger=logger
                )
            except Exception as e:
                logger.error('Error while trying to mosaic document to index')
                logger.error(e)
                logger.error(traceback.format_exc())
        logger.info('Finish initializing mosaic maps.')

        logger.info('Finish initialization job.')
        return True
    except Exception as e:
        logger.error('Error while trying to process initialisation job.')
        logger.error(e)
        logger.error(traceback.format_exc())
