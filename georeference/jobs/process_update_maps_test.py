#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by nicolas.looschen@pikobytes.de on 25.04.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package

import json
import logging
import os
from datetime import datetime

from georeference.jobs.process_update_maps import run_process_update_maps
from georeference.models import Metadata
from georeference.models.jobs import Job, EnumJobType, EnumJobState
from georeference.models.raw_maps import RawMap
from georeference.settings import ES_ROOT, ES_INDEX_NAME, BASE_PATH, PATH_IMAGE_ROOT, TEMPLATE_PUBLIC_THUMBNAIL_URL, \
    TEMPLATE_PUBLIC_ZOOMIFY_URL
from georeference.utils.es import get_es_index
from georeference.utils.utils import remove_if_exists, get_zoomify_path, get_thumbnail_path

LOGGER = logging.getLogger(__name__)

test_metadata = json.loads("""{
  "description": "Update Test",
  "map_scale": 1,
  "owner": "Test Owner",
  "title_short": "Update Test"
}
""")


def test_run_process_update_maps_metadata_only(dbsession_only):
    """ The test checks the proper running of the update process jobs

    :param dbsession_only: Database session
    :type dbsession_only: sqlalchemy.orm.session.Session
    :return:
    """
    try:
        es_index = get_es_index(ES_ROOT, ES_INDEX_NAME, force_recreation=True, logger=LOGGER)
        map_id = 10007521

        update_job = Job(
            id=10000001,
            description=json.dumps({'map_id': map_id, 'metadata': test_metadata}, ensure_ascii=False),
            type=EnumJobType.MAPS_UPDATE.value,
            state=EnumJobState.NOT_STARTED.value,
            submitted=datetime.now().isoformat(),
            user_id='test'
        )
        dbsession_only.add(update_job)
        dbsession_only.flush()

        run_process_update_maps(es_index, dbsession_only, LOGGER, update_job)
        dbsession_only.flush()

        map_object = RawMap.by_id(map_id, dbsession_only)
        metadata_object = Metadata.by_map_id(map_id, dbsession_only)

        # check the elements still exist
        assert metadata_object is not None
        assert map_object is not None

        # check the values in the metadata and map object have been updated correctly
        assert metadata_object.description is not None and metadata_object.description == test_metadata['description']
        assert metadata_object.owner is not None and metadata_object.owner == test_metadata['owner']
        assert metadata_object.title_short is not None and metadata_object.title_short == test_metadata['title_short']
        assert map_object.map_scale is not None and map_object.map_scale == test_metadata['map_scale']

    finally:
        dbsession_only.rollback()


def test_run_process_update_maps_file_only(dbsession_only):
    """ The test checks the proper running of the update process jobs

    :param dbsession_only: Database session
    :type dbsession_only: sqlalchemy.orm.session.Session
    :return:
    """
    map_id = 10007521
    map_object = RawMap.by_id(map_id, dbsession_only)
    metadata_object = Metadata.by_map_id(map_id, dbsession_only)
    existing_path = os.path.join(BASE_PATH, PATH_IMAGE_ROOT, f'{map_object.file_name}.tif')
    expected_link_thumb_small = metadata_object.link_thumb_small
    expected_link_thumb_mid = metadata_object.link_thumb_mid
    expected_link_zoomify = metadata_object.link_zoomify
    expected_original_mtime = os.path.getmtime(existing_path)
    expected_filename = map_object.file_name

    try:
        es_index = get_es_index(ES_ROOT, ES_INDEX_NAME, force_recreation=True, logger=LOGGER)

        assert os.path.exists(existing_path)

        update_job = Job(
            id=10000001,
            description=json.dumps({'map_id': map_id, 'file': existing_path}, ensure_ascii=False),
            type=EnumJobType.MAPS_UPDATE.value,
            state=EnumJobState.NOT_STARTED.value,
            submitted=datetime.now().isoformat(),
            user_id='test'
        )
        dbsession_only.add(update_job)
        dbsession_only.flush()

        run_process_update_maps(es_index, dbsession_only, LOGGER, update_job)
        dbsession_only.flush()

        # Check the processed image file has been updated
        assert os.path.exists(existing_path)
        assert expected_original_mtime != os.path.getmtime(existing_path)

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
        dbsession_only.rollback()


def test_run_process_update_maps_file_and_metadata(dbsession_only):
    """ The Test checks proper update for new file and metadata.

    :param dbsession_only: Database session
    :type dbsession_only: sqlalchemy.orm.session.Session
    :return:
    """
    # let the system think link_thumb_small and link_zoomify are internal
    # => these should be regenerated
    update_metadata = {
        **test_metadata,
        'link_thumb_small': f'{TEMPLATE_PUBLIC_THUMBNAIL_URL}',
        'link_zoomify': f'{TEMPLATE_PUBLIC_ZOOMIFY_URL}'
    }
    _run_update_maps_file_and_metadata(dbsession_only, update_metadata)


def test_run_process_update_maps_links_null(dbsession_only):
    """ Test checks proper update for new file and metadata with the links set to null.

    :param dbsession_only: Database session
    :type dbsession_only: sqlalchemy.orm.session.Session
    :return:
    """
    update_metadata = {
        **test_metadata,
        'link_thumb_small': None,
        'link_zoomify': None
    }
    _run_update_maps_file_and_metadata(dbsession_only, update_metadata)


def _run_update_maps_file_and_metadata(dbsession_only, update_metadata):
    """ Execute test procedure for different metadata.

    :param dbsession_only: Database session
    :type dbsession_only: sqlalchemy.orm.session.Session
    :param update_metadata: Update metadata
    :type update_metadata: dict
    :return:
    """
    map_id = 10007521
    map_object = RawMap.by_id(map_id, dbsession_only)
    metadata_object = Metadata.by_map_id(map_id, dbsession_only)
    existing_path = os.path.join(BASE_PATH, PATH_IMAGE_ROOT, f'{map_object.file_name}.tif')
    expected_mtime = os.path.getmtime(existing_path)
    expected_filename = map_object.file_name
    expected_thumbnail_small_path = get_thumbnail_path(f'{map_id}_120x120.jpg')
    expected_link_thumb_small = TEMPLATE_PUBLIC_THUMBNAIL_URL.format('10007521_120x120.jpg')
    unexpected_thumbnail_mid_path = get_thumbnail_path(f'{map_id}_400x400.jpg')
    expected_link_thumb_mid = metadata_object.link_thumb_mid

    expected_zoomify_path = get_zoomify_path(f'{map_id}')
    expected_link_zoomify = TEMPLATE_PUBLIC_ZOOMIFY_URL.format('10007521')

    try:
        es_index = get_es_index(ES_ROOT, ES_INDEX_NAME, force_recreation=True, logger=LOGGER)

        input_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                  '../__test_data/data_input/dd_stad_0000007_0015.tif')

        assert os.path.exists(existing_path)

        update_job = Job(
            id=10000001,
            description=json.dumps({'map_id': map_id, 'file': input_path, 'metadata': update_metadata},
                                   ensure_ascii=False),
            type=EnumJobType.MAPS_UPDATE.value,
            state=EnumJobState.NOT_STARTED.value,
            submitted=datetime.now().isoformat(),
            user_id='test'
        )
        dbsession_only.add(update_job)
        dbsession_only.flush()

        run_process_update_maps(es_index, dbsession_only, LOGGER, update_job)
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
        paths = [expected_zoomify_path, expected_thumbnail_small_path, expected_zoomify_path]
        for path in paths:
            remove_if_exists(path)
        dbsession_only.rollback()
