#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 23.06.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import json
import os
from datetime import datetime

from sqlmodel import Session

from georeference.config.paths import PATH_MOSAIC_ROOT, PATH_MAPFILE_ROOT
from georeference.config.settings import get_settings
from georeference.jobs.process_delete_mosaic_map import run_process_delete_mosaic_map
from georeference.models.enums import EnumJobType, EnumJobState
from georeference.models.job import Job
from georeference.models.mosaic_map import MosaicMap
from georeference.utils.es_index import (
    generate_es_mosaic_map_document,
)
from georeference.utils.mosaics import get_mosaic_dataset_path, get_mosaic_mapfile_path
from georeference.utils.parser import (
    to_public_map_id,
    to_public_mosaic_map_id,
    from_public_map_id,
    from_public_mosaic_map_id,
)

test_data = {
    "name": "test_service",
    "raw_map_ids": [to_public_map_id(10007521), to_public_map_id(10009405)],
    "title": "Test title",
    "title_short": "Test title_short",
    "time_of_publication": "1923-01-01T00:00:00",
    "link_thumb": "https://link.test.de",
    "map_scale": 25000,
    "last_change": datetime.now().isoformat(),
}
test_mosaic_dataset_path = get_mosaic_dataset_path(PATH_MOSAIC_ROOT, test_data["name"])
test_mosaic_mapfile_path = get_mosaic_mapfile_path(PATH_MAPFILE_ROOT, test_data["name"])


def test_run_process_delete_mosaic_map(db_container, es_index):
    with Session(db_container[1]) as session:
        public_mosaic_id = to_public_mosaic_map_id(10)

        # Get the index object

        delete_job = _create_test_data(
            dbsession=session, mosaic_id=public_mosaic_id, es_index=es_index
        )

        # Run the test
        run_process_delete_mosaic_map(
            es_index=es_index, dbsession=session, job=delete_job
        )

        session.commit()

        settings = get_settings()
        # Check if the index was pushed to the es
        assert es_index.exists(settings.ES_INDEX_NAME, id=public_mosaic_id) is False

        # Check if the database object was updated correctly
        test_mosaic_map = MosaicMap.by_id(
            from_public_mosaic_map_id(public_mosaic_id), session
        )
        assert test_mosaic_map is None

        # Check that also the test files does not exist anymore
        assert os.path.exists(test_mosaic_dataset_path) is False
        assert os.path.exists(test_mosaic_mapfile_path) is False


def _create_test_data(dbsession, mosaic_id, es_index):
    # Add the MosaicMap to the database
    mosaic_map = MosaicMap(
        id=from_public_mosaic_map_id(mosaic_id),
        name=test_data["name"],
        description="test",
        raw_map_ids=map(lambda x: from_public_map_id(x), test_data["raw_map_ids"]),
        title=test_data["title"],
        title_short=test_data["title_short"],
        time_of_publication=datetime.now(),
        link_thumb=test_data["link_thumb"],
        map_scale=test_data["map_scale"],
        last_change=test_data["last_change"],
        last_service_update=datetime.now(),
        last_overview_update=None,
    )
    dbsession.add(mosaic_map)

    # Add the job for creation to the database
    delete_job = Job(
        description=json.dumps(
            {"mosaic_map_id": mosaic_map.id, "mosaic_map_name": mosaic_map.name},
            ensure_ascii=False,
        ),
        type=EnumJobType.MOSAIC_MAP_DELETE.value,
        state=EnumJobState.NOT_STARTED.value,
        submitted=datetime.now(),
        user_id="test_user",
    )
    dbsession.add(delete_job)
    dbsession.flush()

    # Create es index document
    es_document = generate_es_mosaic_map_document(
        mosaic_map_obj=mosaic_map,
        geometry=None,
    )
    settings = get_settings()
    es_index.index(
        index=settings.ES_INDEX_NAME,
        doc_type=None,
        id=es_document["map_id"],
        body=es_document,
    )
    # Create a temporary files
    if not os.path.exists(test_mosaic_dataset_path):
        os.makedirs(os.path.dirname(test_mosaic_dataset_path))
        with open(test_mosaic_dataset_path, "w"):
            pass

    if not os.path.exists(test_mosaic_mapfile_path):
        with open(test_mosaic_mapfile_path, "w"):
            pass

    return delete_job
