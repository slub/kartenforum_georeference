#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by nicolas.looschen@pikobytes.de on 25.04.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package

import json
import os
from datetime import datetime

from sqlmodel import Session

from georeference.config.paths import (
    BASE_PATH,
    PATH_IMAGE_ROOT,
    PATH_TEST_INPUT_BASE,
)
from georeference.config.templates import (
    TEMPLATE_PUBLIC_THUMBNAIL_URL,
    TEMPLATE_PUBLIC_ZOOMIFY_URL,
)
from georeference.jobs.process_update_maps import run_process_update_maps
from georeference.models.enums import EnumJobType, EnumJobState
from georeference.models.job import Job
from georeference.models.metadata import Metadata
from georeference.models.raw_map import RawMap
from georeference.utils.utils import (
    remove_if_exists,
    get_zoomify_path,
    get_thumbnail_path,
)

test_metadata = json.loads("""{
  "description": "Update Test",
  "map_scale": 1,
  "owner": "Test Owner",
  "title_short": "Update Test"
}
""")


def test_run_process_update_maps_metadata_only(db_container, es_index):
    """The test checks the proper running of the update process jobs"""
    with Session(db_container[1]) as session:
        map_id = 10007521

        update_job = Job(
            id=10000001,
            description=json.dumps(
                {"map_id": map_id, "metadata": test_metadata}, ensure_ascii=False
            ),
            type=EnumJobType.MAPS_UPDATE.value,
            state=EnumJobState.NOT_STARTED.value,
            submitted=datetime.now(),
            user_id="test",
        )
        session.add(update_job)
        session.commit()

        run_process_update_maps(es_index, session, update_job)
        session.commit()

        map_object = RawMap.by_id(map_id, session)
        metadata_object = Metadata.by_map_id(map_id, session)

        # check the elements still exist
        assert metadata_object is not None
        assert map_object is not None

        # check the values in the metadata and map object have been updated correctly
        assert (
            metadata_object.description is not None
            and metadata_object.description == test_metadata["description"]
        )
        assert (
            metadata_object.owner is not None
            and metadata_object.owner == test_metadata["owner"]
        )
        assert (
            metadata_object.title_short is not None
            and metadata_object.title_short == test_metadata["title_short"]
        )
        assert (
            map_object.map_scale is not None
            and map_object.map_scale == test_metadata["map_scale"]
        )


def test_run_process_update_maps_file_only(db_container, es_index):
    """The test checks the proper running of the update process jobs"""
    with Session(db_container[1]) as session:
        map_id = 10007521
        map_object = RawMap.by_id(map_id, session)
        metadata_object = Metadata.by_map_id(map_id, session)
        existing_path = os.path.join(
            BASE_PATH, PATH_IMAGE_ROOT, f"{map_object.file_name}.tif"
        )
        expected_link_thumb_small = metadata_object.link_thumb_small
        expected_link_thumb_mid = metadata_object.link_thumb_mid
        expected_link_zoomify = metadata_object.link_zoomify
        expected_original_mtime = os.path.getmtime(existing_path)
        expected_filename = map_object.file_name

        assert os.path.exists(existing_path)

        update_job = Job(
            id=10000001,
            description=json.dumps(
                {"map_id": map_id, "file": existing_path}, ensure_ascii=False
            ),
            type=EnumJobType.MAPS_UPDATE.value,
            state=EnumJobState.NOT_STARTED.value,
            submitted=datetime.now(),
            user_id="test",
        )
        session.add(update_job)
        session.commit()

        run_process_update_maps(es_index, session, update_job)
        session.commit()

        # Check the processed image file has been updated
        assert os.path.exists(existing_path)
        assert expected_original_mtime != os.path.getmtime(existing_path)

        map_object = RawMap.by_id(map_id, session)

        # check the database object has been updated accordingly
        assert map_object.file_name == expected_filename
        assert map_object.rel_path == os.path.relpath(existing_path, PATH_IMAGE_ROOT)

        metadata_object = Metadata.by_map_id(map_id, session)

        # Expect these to still be the same, because they are external links
        assert metadata_object.link_thumb_small == expected_link_thumb_small
        assert metadata_object.link_thumb_mid == expected_link_thumb_mid
        assert metadata_object.link_zoomify == expected_link_zoomify


def test_run_process_update_maps_file_and_metadata(db_container, es_index):
    """The Test checks proper update for new file and metadata."""
    # let the system think link_thumb_small and link_zoomify are internal
    # => these should be regenerated
    update_metadata = {
        **test_metadata,
        "link_thumb_small": f"{TEMPLATE_PUBLIC_THUMBNAIL_URL}",
        "link_zoomify": f"{TEMPLATE_PUBLIC_ZOOMIFY_URL}",
    }

    with Session(db_container[1]) as session:
        _run_update_maps_file_and_metadata(session, update_metadata, es_index)


def test_run_process_update_maps_links_null(db_container, es_index):
    """Test checks proper update for new file and metadata with the links set to null."""
    update_metadata = {**test_metadata, "link_thumb_small": None, "link_zoomify": None}
    with Session(db_container[1]) as session:
        _run_update_maps_file_and_metadata(session, update_metadata, es_index)


def _run_update_maps_file_and_metadata(dbsession_only, update_metadata, es_index):
    """Execute test procedure for different metadata.

    :param dbsession_only: Database session
    :type dbsession_only: sqlalchemy.orm.session.Session
    :param update_metadata: Update metadata
    :type update_metadata: dict
    :return:
    """
    map_id = 10007521
    map_object = RawMap.by_id(map_id, dbsession_only)
    metadata_object = Metadata.by_map_id(map_id, dbsession_only)
    existing_path = os.path.join(
        BASE_PATH, PATH_IMAGE_ROOT, f"{map_object.file_name}.tif"
    )
    expected_mtime = os.path.getmtime(existing_path)
    expected_filename = map_object.file_name
    expected_thumbnail_small_path = get_thumbnail_path(f"{map_id}_120x120.jpg")
    expected_link_thumb_small = TEMPLATE_PUBLIC_THUMBNAIL_URL.format(
        "10007521_120x120.jpg"
    )
    unexpected_thumbnail_mid_path = get_thumbnail_path(f"{map_id}_400x400.jpg")
    expected_link_thumb_mid = metadata_object.link_thumb_mid

    expected_zoomify_path = get_zoomify_path(f"{map_id}")
    expected_link_zoomify = TEMPLATE_PUBLIC_ZOOMIFY_URL.format("10007521")

    try:
        input_path = os.path.join(
            PATH_TEST_INPUT_BASE,
            "dd_stad_0000007_0015.tif",
        )

        assert os.path.exists(existing_path)

        update_job = Job(
            id=10000001,
            description=json.dumps(
                {"map_id": map_id, "file": input_path, "metadata": update_metadata},
                ensure_ascii=False,
            ),
            type=EnumJobType.MAPS_UPDATE.value,
            state=EnumJobState.NOT_STARTED.value,
            submitted=datetime.now(),
            user_id="test",
        )
        dbsession_only.add(update_job)
        dbsession_only.flush()

        run_process_update_maps(es_index, dbsession_only, update_job)
        dbsession_only.flush()

        # Check the processed image file has been updated
        assert os.path.exists(existing_path)
        assert os.path.exists(expected_thumbnail_small_path)
        assert os.path.exists(expected_zoomify_path)
        assert not os.path.exists(unexpected_thumbnail_mid_path)
        assert os.path.getmtime(existing_path) != expected_mtime

        map_object = RawMap.by_id(map_id, dbsession_only)

        # check the database object has been updated accordingly
        assert map_object.file_name == expected_filename
        assert map_object.rel_path == os.path.relpath(existing_path, PATH_IMAGE_ROOT)

        metadata_object = Metadata.by_map_id(map_id, dbsession_only)

        # Expect these to still be the same, because they are external links
        assert metadata_object.link_thumb_small == expected_link_thumb_small
        assert metadata_object.link_thumb_mid == expected_link_thumb_mid
        assert metadata_object.link_zoomify == expected_link_zoomify

    finally:
        # cleanup
        paths = [
            expected_zoomify_path,
            expected_thumbnail_small_path,
            expected_zoomify_path,
        ]
        for path in paths:
            remove_if_exists(path)
        dbsession_only.rollback()
