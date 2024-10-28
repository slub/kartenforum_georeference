#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Created by nicolas.looschen@pikobytes.de on 25.04.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package

import json
import os
import time
from datetime import datetime

from sqlmodel import Session

from georeference.config.paths import PATH_IMAGE_ROOT
from georeference.config.settings import get_settings
from georeference.jobs.process_create_map import run_process_create_map
from georeference.models.enums import EnumJobType, EnumJobState
from georeference.models.job import Job
from georeference.models.raw_map import RawMap

# Initialize the logger
from georeference.utils.parser import to_public_map_id
from georeference.utils.utils import (
    remove_if_exists,
    get_thumbnail_path,
    get_zoomify_path,
)

test_metadata = json.loads("""{
"metadata": {
  "description": "Test",
  "license": "CC-0",
  "map_scale": 1,
  "map_type": "mtb",
  "owner": "Test Owner",
  "time_of_publication": "1923-01-01",
  "title": "Test",
  "title_short": "Test"
}}
""")


def insert_test_map_using_job(dbsession_only, es_index, map_id):
    file_path = os.path.join(
        PATH_IMAGE_ROOT,
        "dd_stad_0000007_0015.tif",
    )

    test_metadata["map_id"] = map_id
    test_metadata["file"] = file_path

    insert_job = Job(
        id=10000000,
        description=json.dumps(test_metadata, ensure_ascii=False),
        type=EnumJobType.MAPS_CREATE.value,
        state=EnumJobState.NOT_STARTED.value,
        submitted=datetime.now(),
        user_id="test",
    )
    dbsession_only.add(insert_job)
    dbsession_only.flush()

    # run testing process
    run_process_create_map(es_index, dbsession_only, insert_job)

    return test_metadata


def test_run_process_create_maps_success(db_container, es_index):
    """The test checks the proper running of the process jobs"""
    # Create the test data

    paths = []
    with Session(db_container[1]) as session:
        try:
            settings = get_settings()
            map_id = 42
            insert_test_map_using_job(session, es_index, map_id)
            session.commit()
            res = RawMap.by_id(map_id, session)

            assert res is not None

            thumbnail_path_small = get_thumbnail_path(f"{map_id}_120x120.jpg")
            thumbnail_path_mid = get_thumbnail_path(f"{map_id}_400x400.jpg")
            zoomify_path = get_zoomify_path(f"{map_id}")
            image_path = os.path.join(
                PATH_IMAGE_ROOT,
                f'{test_metadata["metadata"]["map_type"]}',
                f"{map_id}.tif",
            )

            paths = [image_path, thumbnail_path_small, thumbnail_path_mid, zoomify_path]

            print(image_path, thumbnail_path_small, thumbnail_path_mid, zoomify_path)
            for path in paths:
                assert os.path.exists(path)

            # wait for index update
            time.sleep(2)

            index_res = es_index.search(
                index=settings.ES_INDEX_NAME,
                body={
                    "query": {
                        "bool": {"must": {"match": {"_id": to_public_map_id(map_id)}}}
                    }
                },
            )["hits"]["hits"]

            assert len(index_res) == 1

        finally:
            for path in paths:
                remove_if_exists(path)
