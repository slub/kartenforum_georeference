#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 23.06.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import json
import os
import shutil
import tempfile
from datetime import datetime
from georeference.jobs.actions.create_mosaic_services import run_process_mosaic_services
from georeference.models.georef_maps import GeorefMap
from georeference.models.jobs import EnumJobType
from georeference.models.mosaic_maps import MosaicMap
from georeference.settings import ES_ROOT, ES_INDEX_NAME, PATH_MAPFILE_ROOT, PATH_MOSAIC_ROOT, PATH_TMP_ROOT
from georeference.utils.es_index import generate_es_mosaic_map_document, get_es_index
from georeference.utils.mosaics import create_mosaic_dataset
from georeference.utils.utils import get_geometry_for_mosaic_map


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
    logger.debug('Start processing create mosaic job ...')

    if job.type != EnumJobType.MOSAIC_MAP_CREATE.value:
        raise Exception(f'The job type {job.type} is not supported through this function.')

    # Parse job information
    job_desc = json.loads(job.description)
    mosaic_map_obj = MosaicMap.by_id(job_desc['mosaic_map_id'], dbsession)

    # TODOs (Do not forget that create is also update
    # Precheck: In a higher order component it should make clear that, this job is only run once per daemon run

    try:
        # 1. Create a tmp folder where to place the mosaic dataset
        logger.debug('Start creating mosaic dataset')
        tmp_dir = os.path.abspath(
            tempfile.mkdtemp(
                prefix='run_process_create_mosiac_map',
                dir=PATH_TMP_ROOT
            )
        )

        # 2. Extract paths of geo_images
        geo_images = []
        for raw_map_id in mosaic_map_obj.raw_map_ids:
            georef_map_obj = GeorefMap.by_raw_map_id(raw_map_id, dbsession)
            if georef_map_obj is not None:
                geo_images.append(georef_map_obj.get_abs_path())

        # 3. Create the mosaic dataset in a tmp folder
        logger.debug('Create mosaic dataset in tmp directory ...')
        tmp_mosaic_dataset = create_mosaic_dataset(
            dataset_name=mosaic_map_obj.name,
            target_dir=tmp_dir,
            geo_images=geo_images,
            target_crs=3857,
            logger=logger
        )

        # 4. Create the target directory of the mosaic dataset and mosaic service
        mosaic_file_part = tmp_mosaic_dataset.replace(tmp_dir, '.')
        trg_mosaic_dataset = os.path.abspath(
            os.path.join(
                PATH_MOSAIC_ROOT,
                mosaic_file_part
            )
        )

        # 5. Copy or replace current mosaic dataset
        logger.debug('Copy or replace current mosaic dataset ...')
        _copy_mosaic_dataset(tmp_mosaic_dataset, trg_mosaic_dataset)

        # 6. Create the mapfile in a tmp folder
        logger.debug('Create mosaic service in tmp directory ...')
        trg_mosaic_service = run_process_mosaic_services(
            path_mapfile=os.path.abspath(
                os.path.join(
                    PATH_MAPFILE_ROOT,
                    f'{mosaic_map_obj.name}.map'
                )
            ),
            path_geo_image=trg_mosaic_dataset,
            layer_name=mosaic_map_obj.name,
            layer_title=mosaic_map_obj.title_short,
            logger=logger,
            force=True
        )

        # 7. Update the search index
        logger.debug('Update the search index ...')
        _push_to_es_index(
            es_index=es_index,
            mosaic_map_obj=mosaic_map_obj,
            trg_mosaic_dataset=trg_mosaic_dataset,
            logger=logger
        )

        # 8. Update the database fields
        mosaic_map_obj.last_service_update = datetime.now().isoformat()
        dbsession.flush()
    finally:
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)

def _copy_mosaic_dataset(source_path, target_path):
    source_parent_dir = os.path.dirname(source_path)
    target_parent_dir = os.path.dirname(target_path)

    if os.path.exists(target_parent_dir):
        shutil.rmtree(target_parent_dir)

    shutil.copytree(source_parent_dir, target_parent_dir)

def _push_to_es_index(es_index, mosaic_map_obj, trg_mosaic_dataset, logger):
    """ Creates/Updates the document for a mosaic_map_obj at the es_index.

    :param es_index: Elasticsearch client
    :type es_index: elasticsearch.Elasticsearch
    :param mosaic_map_obj: MosaicMap object
    :type mosaic_map_obj: georeference.models.mosaic_maps.MosaicMap
    :param trg_mosaic_dataset: Path to the mosaic dataset
    :type trg_mosaic_dataset: str
    :param logger: Logger
    :type logger: logging.Logger
    """
    search_geometry = get_geometry_for_mosaic_map(trg_mosaic_dataset)
    es_document = generate_es_mosaic_map_document(
        mosaic_map_obj=mosaic_map_obj,
        logger=logger,
        geometry=search_geometry,
    )
    es_document_id = es_document['map_id']
    logger.debug(f'Push document with id {es_document_id} to index: {es_document} ...')
    es_index.index(
        index=ES_INDEX_NAME,
        doc_type=None,
        id=es_document_id,
        body=es_document
    )


