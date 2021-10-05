#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 10.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import json
from georeference.settings import ROUTE_PREFIX
from georeference.models.jobs import AdminJobs

def test_getAdminGeorefs_success_mapId(testapp):
    # For clean test setup the test data should also be added to the database within this method
    # @TODO
    map_id = 10001556

    # Build test request
    res = testapp.get(ROUTE_PREFIX + '/admin/georefs?map_id=%s' % map_id, status=200)
    assert res.status_int == 200
    assert len(res.json) == 2

def test_getAdminGeorefs_failed_missingParameter(testapp):
    res = testapp.get(ROUTE_PREFIX + '/admin/georefs', status=400)
    assert res.status_int == 400

def test_postAdminGeorefs_invalid_success(testapp, dbsession):
    georef_id = 18

    # Build and send request
    comentValue = 'test'
    stateValue = 'invalid'
    params = {
        'georef_id': georef_id,
        'user_id': 'user_1',
        'state': stateValue,
        'comment': comentValue
    }
    res = testapp.post(ROUTE_PREFIX + '/admin/georefs', json.dumps(params),
                       content_type='application/json; charset=utf-8', status=200)

    # Make sure that the correct status code is set
    assert res.status_int == 200
    assert res.json['job_id'] != None

    # Check if the admin jobs is withn the database
    subjectAdminJob = AdminJobs.by_id(res.json['job_id'], dbsession)
    assert subjectAdminJob.state == stateValue
    assert subjectAdminJob.comment == comentValue

    # Rollback session
    dbsession.rollback()

def test_postAdminGeorefs_valid_success(testapp, dbsession):
    georef_id = 18

    # Build and send request
    comentValue = 'test'
    stateValue = 'valid'
    params = {
        'georef_id': georef_id,
        'user_id': 'user_1',
        'state': stateValue,
        'comment': comentValue
    }
    res = testapp.post(ROUTE_PREFIX + '/admin/georefs', json.dumps(params),
                       content_type='application/json; charset=utf-8', status=200)

    # Make sure that the correct status code is set
    assert res.status_int == 200
    assert res.json['job_id'] != None

    # Check if the admin jobs is withn the database
    subjectAdminJob = AdminJobs.by_id(res.json['job_id'], dbsession)
    assert subjectAdminJob.state == stateValue
    assert subjectAdminJob.comment == comentValue

    # Rollback session
    dbsession.rollback()

def test_postAdminGeorefs_wrongState_failed(testapp, dbsession):
    georef_id = 18

    # Build and send request
    stateValue = 'valids'
    params = {
        'georef_id': georef_id,
        'user_id': 'user_1',
        'state': stateValue,
        'comment': ''
    }
    res = testapp.post(ROUTE_PREFIX + '/admin/georefs', json.dumps(params),
                       content_type='application/json; charset=utf-8', status=400)

    # Make sure that the correct status code is set
    assert res.status_int == 400

    # Rollback session
    dbsession.rollback()