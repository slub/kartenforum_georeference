#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 09.03.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import logging
import pytest
from datetime import datetime
from georeference.jobs.set_validation import run_process_new_validation
from georeference.models.georef_maps import GeorefMap
from georeference.models.jobs import Job, EnumJobType, EnumJobState
from georeference.models.raw_maps import RawMap
from georeference.models.transformations import Transformation, EnumValidationValue
from georeference.settings import ES_ROOT
from georeference.settings import ES_INDEX_NAME
from georeference.utils.es_index import get_es_index
from georeference.utils.parser import to_public_map_id

# Initialize the logger
LOGGER = logging.getLogger(__name__)


def test_run_validation_job_success_with_overwrite(dbsession_only):
    """ The test checks the proper processing of a validation job. The newer invalid transformation, should be replaced by an older
        valid transformation.

    :param dbsession_only: Database session
    :type dbsession_only: sqlalchemy.orm.session.Session
    :return:
    """
    # Create the test data
    map_id = 10007521
    transformation_id = 12187
    new_job = Job(
        id=10000001,
        state=EnumJobState.NOT_STARTED.value,
        submitted=datetime.now().isoformat(),
        user_id='test',
        type=EnumJobType.TRANSFORMATION_SET_INVALID.value,
        description=f'{{"transformation_id": {transformation_id} }}'
    )
    dbsession_only.add(new_job)
    dbsession_only.flush()

    # Normally the tms processing needs really long. To prevent this we temporary increase the map_scale of the RawMap
    # to trigger lower zoom levels
    raw_map_obj = RawMap.by_id(map_id, dbsession_only)
    raw_map_obj.map_scale = 1000000000
    dbsession_only.flush()

    # Get the index object
    es_index = get_es_index(ES_ROOT, ES_INDEX_NAME, force_recreation=True, logger=LOGGER)

    # Build test request
    run_process_new_validation(
        es_index,
        dbsession_only,
        LOGGER,
        new_job
    )

    dbsession_only.flush()

    # Query if the database was changed correctly
    t = dbsession_only.query(Transformation).filter(Transformation.id == transformation_id).first()
    assert t is not None
    assert t.validation == EnumValidationValue.INVALID.value

    # Check if the database changes are correct
    g = dbsession_only.query(GeorefMap).filter(GeorefMap.transformation_id == t.overwrites).first()
    assert g is not None
    assert g.transformation_id == t.overwrites

    # Check if the index was pushed to the es
    es_doc = es_index.get(ES_INDEX_NAME, id=to_public_map_id(map_id))
    assert es_doc is not None
    assert es_doc['_source']['geometry'] is not None

    dbsession_only.rollback()
    es_index.close()


def test_run_validation_job_success_without_overwrite(dbsession_only):
    """ The test checks the proper processing of a validation job. The transformation is set to invalid and there is no more valid transformation.

    :param dbsession_only: Database session
    :type dbsession_only: sqlalchemy.orm.session.Session
    :return:
    """
    # Create the test data
    map_id = 10009482
    transformation_id = 7912
    new_job = Job(
        id=10000001,
        state=EnumJobState.NOT_STARTED.value,
        submitted=datetime.now().isoformat(),
        user_id='test',
        type=EnumJobType.TRANSFORMATION_SET_INVALID.value,
        description=f'{{"transformation_id": {transformation_id} }}'
    )
    dbsession_only.add(new_job)
    dbsession_only.flush()

    # Normally the tms processing needs really long. To prevent this we temporary increase the map_scale of the RawMap
    # to trigger lower zoom levels
    raw_map_obj = RawMap.by_id(map_id, dbsession_only)
    raw_map_obj.map_scale = 1000000000
    dbsession_only.flush()

    # Get the index object
    es_index = get_es_index(ES_ROOT, ES_INDEX_NAME, force_recreation=True, logger=LOGGER)

    # Build test request
    run_process_new_validation(
        es_index,
        dbsession_only,
        logger=LOGGER,
        job=new_job
    )

    # Query if the database was changed correctly
    t = dbsession_only.query(Transformation).filter(Transformation.id == transformation_id).first()
    assert t is not None
    assert t.validation == EnumValidationValue.INVALID.value

    # Check if the database changes are correct
    g = dbsession_only.query(GeorefMap).filter(GeorefMap.raw_map_id == map_id).first()
    assert g is None

    # Check if the index was pushed to the es
    es_doc = es_index.get(ES_INDEX_NAME, id=to_public_map_id(map_id))
    assert es_doc is not None
    assert es_doc['_source']['geometry'] is None

    dbsession_only.rollback()
    es_index.close()
