#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 09.03.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
from datetime import datetime
from georeference.models.jobs import Job, EnumJobType, EnumJobState
from georeference.models.transformations import Transformation, EnumValidationValue


def test_query_not_started_jobs_success(dbsession_only):
    """ The test checks if the function "queryUnprocessedJobs" returns the correct jobs and clears the race conditions.

    :param dbsession_only: Database session
    :type dbsession_only: sqlalchemy.orm.session.Session
    :return:
    """
    # Create the test data
    map_id = 10007521
    dbsession_only.add(
        Transformation(
            id=10000000,
            submitted=datetime.now().isoformat(),
            user_id='test',
            params="",
            target_crs=4326,
            validation=EnumValidationValue.MISSING.value,
            raw_map_id=map_id,
            overwrites=0,
            comment=None
        )
    )
    dbsession_only.add(
        Transformation(
            id=10000001,
            submitted=datetime.now().isoformat(),
            user_id='test',
            params="",
            target_crs=4326,
            validation=EnumValidationValue.MISSING.value,
            raw_map_id=map_id,
            overwrites=0,
            comment=None
        )
    )
    dbsession_only.flush()
    dbsession_only.add(
        Job(
            id=10000000,
            submitted=datetime.now().isoformat(),
            user_id='test',
            type=EnumJobType.TRANSFORMATION_PROCESS.value,
            description='{ "transformation_id": 10000000 }',
            state=EnumJobState.COMPLETED.value
        )
    )
    dbsession_only.add(
        Job(
            id=10000001,
            submitted=datetime.now().isoformat(),
            user_id='test',
            type=EnumJobType.TRANSFORMATION_PROCESS.value,
            description='{ "transformation_id": 10000001 }',
            state=EnumJobState.NOT_STARTED.value
        )
    )
    dbsession_only.add(
        Job(
            id=10000002,
            submitted=datetime.now().isoformat(),
            user_id='test',
            type=EnumJobType.TRANSFORMATION_PROCESS.value,
            description='{ "transformation_id": 10000001 }',
            state=EnumJobState.COMPLETED.value
        )
    )
    dbsession_only.add(
        Job(
            id=10000003,
            submitted=datetime.now().isoformat(),
            user_id='test',
            type=EnumJobType.TRANSFORMATION_SET_VALID.value,
            description='{ "transformation_id": 10000001  }',
            state=EnumJobState.NOT_STARTED.value
        )
    )
    dbsession_only.flush()

    # Build test
    subject = Job.query_not_started_jobs([EnumJobType.TRANSFORMATION_PROCESS.value], dbsession_only)
    assert len(subject) == 1
    assert subject[0].id == 10000001

    subject = Job.query_not_started_jobs(
        [EnumJobType.TRANSFORMATION_SET_VALID.value, EnumJobType.TRANSFORMATION_SET_INVALID.value], dbsession_only)
    assert len(subject) == 1
    assert subject[0].id == 10000003
    dbsession_only.rollback()
