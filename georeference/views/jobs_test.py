#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 06.10.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import json
from datetime import datetime
from georeference.models.jobs import Job, EnumJobType, EnumJobState
from georeference.settings import ROUTE_PREFIX


def test_GET_jobs_success_empty_result(testapp):
    res = testapp.get(ROUTE_PREFIX + '/jobs', status=200)
    assert res.status_int == 200
    assert len(res.json) == 0


def test_GET_jobs_success_all(testapp, dbsession):
    dbsession.add(
        Job(id=1, submitted=datetime.now().isoformat(), user_id='test',
            type=EnumJobType.TRANSFORMATION_PROCESS.value,
            description='{ "transformation_id": 123 }',
            state=EnumJobState.NOT_STARTED.value)
    )
    dbsession.add(
        Job(id=2, submitted=datetime.now().isoformat(), user_id='test',
            type=EnumJobType.TRANSFORMATION_PROCESS.value,
            description='{ "transformation_id": 123 }',
            state=EnumJobState.NOT_STARTED.value)
    )
    dbsession.flush()

    # Build test request
    res = testapp.get(ROUTE_PREFIX + '/jobs', status=200)
    assert res.status_int == 200
    assert len(res.json) == 2

    dbsession.rollback()


def test_GET_jobs_success_pending(testapp, dbsession):
    dbsession.add(
        Job(id=1, submitted=datetime.now().isoformat(), user_id='test',
            type=EnumJobType.TRANSFORMATION_PROCESS.value,
            description='{ "transformation_id": 123 }',
            state=EnumJobState.COMPLETED.value)
    )
    dbsession.add(
        Job(id=2, submitted=datetime.now().isoformat(), user_id='test',
            type=EnumJobType.TRANSFORMATION_PROCESS.value,
            description='{ "transformation_id": 123 }',
            state=EnumJobState.NOT_STARTED.value)
    )
    dbsession.flush()

    # Build test request
    res = testapp.get(ROUTE_PREFIX + '/jobs?pending=true', status=200)
    assert res.status_int == 200
    assert len(res.json) == 1

    dbsession.rollback()


def test_GET_jobs_success_limit(testapp, dbsession):
    dbsession.add(
        Job(id=1, submitted=datetime.now().isoformat(), user_id='test',
            type=EnumJobType.TRANSFORMATION_PROCESS.value,
            description='{ "transformation_id": 123 }',
            state=EnumJobState.COMPLETED.value)
    )
    dbsession.add(
        Job(id=2, submitted=datetime.now().isoformat(), user_id='test',
            type=EnumJobType.TRANSFORMATION_PROCESS.value,
            description='{ "transformation_id": 123 }',
            state=EnumJobState.NOT_STARTED.value)
    )
    dbsession.flush()

    # Build test request
    res = testapp.get(ROUTE_PREFIX + '/jobs?limit=1', status=200)
    assert res.status_int == 200
    assert len(res.json) == 1

    dbsession.rollback()


def test_POST_jobs_success_transformation_process(testapp, dbsession):
    # Create and perform test request
    params = {
        'user_id': 'test',
        'name': EnumJobType.TRANSFORMATION_PROCESS.value,
        'description': {
            'transformation_id': 123,
            'comment': 'test'
        }
    }

    # Build test request
    res = testapp.post(ROUTE_PREFIX + '/jobs', params=json.dumps(params),
                       content_type='application/json; charset=utf-8', status=200)

    # Check response
    assert res.status_int == 200
    assert res.json_body['job_id'] != None

    # First of all rollback session
    dbsession.rollback()
