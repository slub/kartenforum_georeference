#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 23.06.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import json
import logging
import os
import shutil
from datetime import datetime
from georeference.jobs.actions.create_geo_image import run_process_geo_image
from georeference.models.georef_maps import GeorefMap
from georeference.models.transformations import Transformation
from georeference.models.raw_maps import RawMap
from georeference.models.jobs import Job, EnumJobType, EnumJobState
from georeference.models.mosaic_maps import MosaicMap
from georeference.settings import ES_ROOT, ES_INDEX_NAME, PATH_MOSAIC_ROOT, PATH_MAPFILE_ROOT
from georeference.utils.es_index import get_es_index
from georeference.utils.mosaics import get_mosaic_dataset_path, get_mosaic_mapfile_path
from georeference.utils.parser import to_public_map_id, to_public_mosaic_map_id, from_public_map_id, from_public_mosaic_map_id
from .process_create_mosaic_map import run_process_create_mosiac_map

# Initialize the logger
LOGGER = logging.getLogger(__name__)

test_data = {
    "name": "test_service",
    "raw_map_ids": [to_public_map_id(10007521), to_public_map_id(10009405)],
    "title": "Test title",
    "title_short": "Test title_short",
    "time_of_publication": "1923-01-01T00:00:00",
    "link_thumb": "https://link.test.de",
    "map_scale": 25000,
    "last_change": datetime.now().isoformat()
}

def test_run_process_create_mosiac_map(dbsession):
    try:
        public_mosaic_id = to_public_mosaic_map_id(10)
        create_job = _create_test_data(
            dbsession=dbsession,
            mosaic_id=public_mosaic_id
        )

        # Get the index object
        es_index = get_es_index(ES_ROOT, ES_INDEX_NAME, force_recreation=True, logger=LOGGER)

        # Backup value for later assert control
        test_mosaic_map = MosaicMap.by_id(from_public_mosaic_map_id(public_mosaic_id), dbsession)
        last_service_update_before_test = test_mosaic_map.last_service_update

        # Run the test
        run_process_create_mosiac_map(
            es_index=es_index,
            dbsession=dbsession,
            logger=LOGGER,
            job=create_job
        )

        # Check if the index was pushed to the es
        assert es_index.exists(ES_INDEX_NAME, id=public_mosaic_id) == True

        # Check if the database object was updated correctly
        test_mosaic_map = MosaicMap.by_id(from_public_mosaic_map_id(public_mosaic_id), dbsession)
        assert last_service_update_before_test == None
        assert last_service_update_before_test != test_mosaic_map.last_service_update

        # Check if the mosaic dataset exist
        mosaic_dataset_path = get_mosaic_dataset_path(PATH_MOSAIC_ROOT, test_mosaic_map.name)
        assert os.path.exists(mosaic_dataset_path)

        # Check if the mosaic mapfiel exists
        mosaic_mapfile_path = get_mosaic_mapfile_path(PATH_MAPFILE_ROOT, test_mosaic_map.name)
        assert os.path.exists(mosaic_mapfile_path)

    finally:
        dbsession.rollback()

        if mosaic_dataset_path is not None and os.path.exists(mosaic_dataset_path):
            shutil.rmtree(os.path.dirname(mosaic_dataset_path))
        if mosaic_mapfile_path is not None and os.path.exists(mosaic_mapfile_path):
            os.remove(mosaic_mapfile_path)

def _create_test_data(dbsession, mosaic_id):
    # First make sure that the referenced geo image does exist, for all referenced maps
    for raw_map_id in test_data["raw_map_ids"]:
        raw_map_obj = RawMap.by_id(from_public_map_id(raw_map_id), dbsession)
        georef_map_obj = GeorefMap.by_raw_map_id(raw_map_obj.id, dbsession)

        if georef_map_obj != None and os.path.exists(raw_map_obj.get_abs_path()):
            transformation_obj = Transformation.by_id(georef_map_obj.transformation_id, dbsession)

            # Make sure to process the geo image. We do not use the "force" parameter, which skips this
            # step in case a geo image already exists
            path_geo_image = run_process_geo_image(
                transformation_obj,
                raw_map_obj.get_abs_path(),
                georef_map_obj.get_abs_path(),
                logger=LOGGER,
                clip=Transformation.get_valid_clip_geometry(georef_map_obj.transformation_id,
                                                            dbsession=dbsession) if transformation_obj.clip is not None else None
            )
            LOGGER.debug(path_geo_image)

    # Add the MosaicMap to the database
    mosaic_map = MosaicMap(
        id=from_public_mosaic_map_id(mosaic_id),
        name=test_data["name"],
        description="test",
        raw_map_ids=map(lambda x: from_public_map_id(x), test_data["raw_map_ids"]),
        title=test_data["title"],
        title_short=test_data["title_short"],
        time_of_publication=test_data["time_of_publication"],
        link_thumb=test_data["link_thumb"],
        map_scale=test_data["map_scale"],
        last_change=test_data["last_change"],
        last_service_update=None,
        last_overview_update=None,
    )
    dbsession.add(mosaic_map)

    # Add the job for creation to the database
    create_job = Job(
        description=json.dumps({
            'mosaic_map_id': mosaic_map.id,
            'mosaic_map_name': mosaic_map.name,
            }, ensure_ascii=False),
        type=EnumJobType.MOSAIC_MAP_CREATE.value,
        state=EnumJobState.NOT_STARTED.value,
        submitted=datetime.now().isoformat(),
        user_id='test_user'
    )
    dbsession.add(create_job)

    dbsession.flush()

    return create_job