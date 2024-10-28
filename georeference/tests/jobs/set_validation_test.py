#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Created by jacob.mendt@pikobytes.de on 09.03.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
from datetime import datetime

from sqlmodel import Session, select

from georeference.config.settings import get_settings
from georeference.jobs.set_validation import run_process_new_validation
from georeference.models.enums import EnumJobState, EnumJobType
from georeference.models.georef_map import GeorefMap
from georeference.models.job import Job
from georeference.models.raw_map import RawMap
from georeference.models.transformation import Transformation, EnumValidationValue
from georeference.utils.parser import to_public_map_id


def test_run_validation_job_success_with_overwrite(db_container, es_index):
    """
    The test checks the proper processing of a validation job. The newer invalid transformation, should be replaced by an older
    valid transformation.
    """

    with Session(db_container[1]) as session:
        # Create the test data
        map_id = 10007521
        transformation_id = 12187
        new_job = Job(
            id=10000001,
            state=EnumJobState.NOT_STARTED.value,
            submitted=datetime.now(),
            user_id="test",
            type=EnumJobType.TRANSFORMATION_SET_INVALID.value,
            description=f'{{"transformation_id": {transformation_id} }}',
        )
        session.add(new_job)
        session.commit()

        # Normally the tms processing needs really long. To prevent this we temporary increase the map_scale of the RawMap
        # to trigger lower zoom levels
        raw_map_obj = RawMap.by_id(map_id, session)
        raw_map_obj.map_scale = 1000000000
        session.commit()

        # Build test request
        run_process_new_validation(es_index, session, new_job)

        session.commit()

        # Query if the database was changed correctly
        t = session.exec(
            select(Transformation).where(Transformation.id == transformation_id)
        ).first()

        assert t is not None
        assert t.validation == EnumValidationValue.INVALID.value

        # Check if the database changes are correct
        g = session.exec(
            select(GeorefMap).where(GeorefMap.transformation_id == t.overwrites)
        ).first()

        assert g is not None
        assert g.transformation_id == t.overwrites

        # Check if the index was pushed to the es
        settings = get_settings()
        es_doc = es_index.get(settings.ES_INDEX_NAME, id=to_public_map_id(map_id))
        assert es_doc is not None
        assert es_doc["_source"]["geometry"] is not None


def test_run_validation_job_success_without_overwrite(db_container, es_index):
    """The test checks the proper processing of a validation job. The transformation is set to invalid and there is no more valid transformation."""
    # Create the test data
    with Session(db_container[1]) as session:
        map_id = 10009482
        transformation_id = 7912
        new_job = Job(
            id=10000001,
            state=EnumJobState.NOT_STARTED.value,
            submitted=datetime.now(),
            user_id="test",
            type=EnumJobType.TRANSFORMATION_SET_INVALID.value,
            description=f'{{"transformation_id": {transformation_id} }}',
        )
        session.add(new_job)
        session.commit()

        # Normally the tms processing needs really long. To prevent this we temporary increase the map_scale of the RawMap
        # to trigger lower zoom levels
        raw_map_obj = RawMap.by_id(map_id, session)
        raw_map_obj.map_scale = 1000000000
        session.commit()

        # Build test request
        run_process_new_validation(es_index, session, job=new_job)

        # Query if the database was changed correctly
        t = session.exec(
            select(Transformation).where(Transformation.id == transformation_id)
        ).first()

        assert t is not None
        assert t.validation == EnumValidationValue.INVALID.value

        # Check if the database changes are correct
        g = session.exec(
            select(GeorefMap).where(GeorefMap.raw_map_id == map_id)
        ).first()
        assert g is None

        # Check if the index was pushed to the es
        settings = get_settings()
        es_doc = es_index.get(settings.ES_INDEX_NAME, id=to_public_map_id(map_id))
        assert es_doc is not None
        assert es_doc["_source"]["geometry"] is None
