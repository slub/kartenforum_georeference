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

from sqlmodel import Session, delete

from georeference.config.paths import PATH_IMAGE_ROOT
from georeference.config.settings import get_settings
from georeference.jobs.process_delete_map import run_process_delete_maps
from georeference.models.enums import EnumJobType, EnumJobState
from georeference.models.job import Job
from georeference.models.metadata import Metadata
from georeference.models.raw_map import RawMap
from georeference.tests.jobs.process_create_map_test import insert_test_map_using_job
from georeference.utils.parser import to_public_map_id
from georeference.utils.utils import (
    remove_if_exists,
    get_thumbnail_path,
    get_zoomify_path,
)


def test_run_process_delete_maps_success(db_container, es_index):
    """The test checks the proper running of the process jobs"""
    # Create the test data

    with Session(db_container[1]) as session:
        paths = []
        job_id = 10000001
        create_job_id = 10000000
        try:
            # initialize maps and file system
            map_id = 42
            test_metadata = insert_test_map_using_job(session, es_index, map_id)

            thumbnail_path_small = get_thumbnail_path(f"{map_id}_120x120.jpg")
            thumbnail_path_mid = get_thumbnail_path(f"{map_id}_400x400.jpg")
            zoomify_path = get_zoomify_path(f"{map_id}")
            image_path = os.path.join(
                PATH_IMAGE_ROOT,
                f'{test_metadata["metadata"]["map_type"]}',
                f"{map_id}.tif",
            )

            paths = [image_path, thumbnail_path_small, thumbnail_path_mid, zoomify_path]

            # expect the map to exist
            res = RawMap.by_id(map_id, session)
            assert res is not None

            # expects metadata object to exist
            res = Metadata.by_map_id(map_id, session)
            assert res is not None

            # expect all paths to exist
            for path in paths:
                assert os.path.exists(path)

            # wait for index update
            time.sleep(2)

            settings = get_settings()
            index_res = es_index.search(
                index=settings.ES_INDEX_NAME,
                body={
                    "query": {
                        "bool": {"must": {"match": {"_id": to_public_map_id(map_id)}}}
                    }
                },
            )["hits"]["hits"]

            assert len(index_res) == 1

            # delete initialized state
            session.commit()

            delete_job = Job(
                id=job_id,
                description=json.dumps({"map_id": map_id}, ensure_ascii=False),
                type=EnumJobType.MAPS_DELETE.value,
                state=EnumJobState.NOT_STARTED.value,
                submitted=datetime.now(),
                user_id="test",
            )
            session.add(delete_job)
            session.commit()

            # run testing process
            run_process_delete_maps(es_index, session, delete_job)
            session.commit()

            # expect the map to be deleted after the job run
            res = RawMap.by_id(map_id, session)
            assert res is None

            # expects the metadata to be deleted after the job run
            res = Metadata.by_map_id(map_id, session)
            assert res is None

            # expect the paths to be deleted after the job run
            for path in paths:
                assert not os.path.exists(path)

            # wait for index to update
            time.sleep(2)

            index_res = es_index.search(
                index=settings.ES_INDEX_NAME,
                body={
                    "query": {
                        "bool": {"must": {"match": {"_id": to_public_map_id(map_id)}}}
                    }
                },
            )["hits"]["hits"]

            assert len(index_res) == 0

            es_index.close()

        finally:
            for path in paths:
                remove_if_exists(path)
            # the session is commited in the delete job, thus we have to manually rollback
            stmt1 = delete(Job).where(Job.id == job_id)
            stmt2 = delete(Job).where(Job.id == create_job_id)

            session.execute(stmt1)
            session.execute(stmt2)

            session.commit()
