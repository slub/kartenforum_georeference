#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 06.10.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import json
from datetime import datetime
from georeference.models.jobs import Job, TaskValues
from georeference.settings import ROUTE_PREFIX

def test_GET_Jobs_success_emptyResult(testapp):
    res = testapp.get(ROUTE_PREFIX + '/jobs' , status=200)
    assert res.status_int == 200
    assert len(res.json) == 0

def test_GET_Jobs_success_all(testapp, dbsession):
    dbsession.add(
        Job(id=1, processed=False, submitted=datetime.now().isoformat(), user_id='test',
            task_name=TaskValues.TRANSFORMATION_PROCESS.value,
            task='{ "transformation_id": 123 }')
    )
    dbsession.add(
        Job(id=2, processed=False, submitted=datetime.now().isoformat(), user_id='test',
            task_name=TaskValues.TRANSFORMATION_PROCESS.value,
            task='{ "transformation_id": 123 }')
    )
    dbsession.flush()

    # Build test request
    res = testapp.get(ROUTE_PREFIX + '/jobs', status=200)
    assert res.status_int == 200
    assert len(res.json) == 2

    dbsession.rollback()

def test_GET_Jobs_success_pending(testapp, dbsession):
    dbsession.add(
        Job(id=1, processed=True, submitted=datetime.now().isoformat(), user_id='test',
            task_name=TaskValues.TRANSFORMATION_PROCESS.value,
            task='{ "transformation_id": 123 }')
    )
    dbsession.add(
        Job(id=2, processed=False, submitted=datetime.now().isoformat(), user_id='test',
            task_name=TaskValues.TRANSFORMATION_PROCESS.value,
            task='{ "transformation_id": 123 }')
    )
    dbsession.flush()

    # Build test request
    res = testapp.get(ROUTE_PREFIX + '/jobs?pending=true', status=200)
    assert res.status_int == 200
    assert len(res.json) == 1

    dbsession.rollback()

def test_GET_Jobs_success_limit(testapp, dbsession):
    dbsession.add(
        Job(id=1, processed=True, submitted=datetime.now().isoformat(), user_id='test',
            task_name=TaskValues.TRANSFORMATION_PROCESS.value,
            task='{ "transformation_id": 123 }')
    )
    dbsession.add(
        Job(id=2, processed=False, submitted=datetime.now().isoformat(), user_id='test',
            task_name=TaskValues.TRANSFORMATION_PROCESS.value,
            task='{ "transformation_id": 123 }')
    )
    dbsession.flush()

    # Build test request
    res = testapp.get(ROUTE_PREFIX + '/jobs?limit=1', status=200)
    assert res.status_int == 200
    assert len(res.json) == 1

    dbsession.rollback()

def test_POST_Jobs_success_transformationProcess(testapp, dbsession):
    # Create and perform test request
    params = {
        'user_id': 'test',
        'task_name': TaskValues.TRANSFORMATION_PROCESS.value,
        'task': {
            'transformation_id': 123,
            'comment': 'test'
        }
    }

    # Build test request
    res = testapp.post(ROUTE_PREFIX + '/jobs', params=json.dumps(params), content_type='application/json; charset=utf-8', status=200)

    # Check response
    assert res.status_int == 200
    assert res.json_body['job_id'] != None

    # First of all rollback session
    dbsession.rollback()
