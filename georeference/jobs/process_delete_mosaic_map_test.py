#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 23.06.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import json
import logging
import os
from datetime import datetime
from georeference.models.jobs import Job, EnumJobType, EnumJobState
from georeference.models.mosaic_maps import MosaicMap
from georeference.settings import ES_ROOT, ES_INDEX_NAME, PATH_MOSAIC_ROOT, PATH_MAPFILE_ROOT
from georeference.utils.es_index import get_es_index, generate_es_mosaic_map_document
from georeference.utils.mosaics import get_mosaic_dataset_path, get_mosaic_mapfile_path
from georeference.utils.parser import to_public_map_id, to_public_mosaic_map_id, from_public_map_id, from_public_mosaic_map_id
from .process_delete_mosaic_map import run_process_delete_mosiac_map

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
test_mosaic_dataset_path = get_mosaic_dataset_path(PATH_MOSAIC_ROOT, test_data['name'])
test_mosaic_mapfile_path = get_mosaic_mapfile_path(PATH_MAPFILE_ROOT, test_data['name'])

def test_run_process_delete_mosiac_map(dbsession_only):
    try:
        public_mosaic_id = to_public_mosaic_map_id(10)

        # Get the index object
        es_index = get_es_index(ES_ROOT, ES_INDEX_NAME, force_recreation=True, logger=LOGGER)

        delete_job = _create_test_data(
            dbsession=dbsession_only,
            mosaic_id=public_mosaic_id,
            es_index=es_index
        )

        # Run the test
        run_process_delete_mosiac_map(
            es_index=es_index,
            dbsession=dbsession_only,
            logger=LOGGER,
            job=delete_job
        )

        # Check if the index was pushed to the es
        assert es_index.exists(ES_INDEX_NAME, id=public_mosaic_id) == False

        # Check if the database object was updated correctly
        test_mosaic_map = MosaicMap.by_id(from_public_mosaic_map_id(public_mosaic_id), dbsession_only)
        assert test_mosaic_map is None

        # Check that also the test files does not exist anymore
        assert os.path.exists(test_mosaic_dataset_path) == False
        assert os.path.exists(test_mosaic_mapfile_path) == False
    finally:
        dbsession_only.rollback()

        # the session is commited in the delete job, thus we have to manually rollback
        dbsession_only.query(Job).filter(Job.id == delete_job.id).delete()
        dbsession_only.commit()


def _create_test_data(dbsession, mosaic_id, es_index):
    # Add the MosaicMap to the database
    mosaic_map = MosaicMap(
        id=from_public_mosaic_map_id(mosaic_id),
        name=test_data["name"],
        raw_map_ids=map(lambda x: from_public_map_id(x), test_data["raw_map_ids"]),
        title=test_data["title"],
        title_short=test_data["title_short"],
        time_of_publication=datetime.now(),
        link_thumb=test_data["link_thumb"],
        map_scale=test_data["map_scale"],
        last_change=test_data["last_change"],
        last_service_update=datetime.now().isoformat(),
        last_overview_update=None,
    )
    dbsession.add(mosaic_map)

    # Add the job for creation to the database
    delete_job = Job(
        description=json.dumps({
            'mosaic_map_id': mosaic_map.id,
            }, ensure_ascii=False),
        type=EnumJobType.MOSAIC_MAP_DELETE.value,
        state=EnumJobState.NOT_STARTED.value,
        submitted=datetime.now().isoformat(),
        user_id='test_user'
    )
    dbsession.add(delete_job)
    dbsession.flush()

    # Create es index document
    es_document = generate_es_mosaic_map_document(
        mosaic_map_obj=mosaic_map,
        logger=LOGGER,
        geometry=None,
    )
    es_index.index(
        index=ES_INDEX_NAME,
        doc_type=None,
        id=es_document['map_id'],
        body=es_document
    )
    # Create a temporary files
    if not os.path.exists(test_mosaic_dataset_path):
        os.makedirs(os.path.dirname(test_mosaic_dataset_path))
        with open(test_mosaic_dataset_path, 'w'): pass

    if not os.path.exists(test_mosaic_mapfile_path):
        with open(test_mosaic_mapfile_path, 'w'): pass

    return delete_job