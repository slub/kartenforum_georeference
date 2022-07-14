#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 09.09.21
#
# This file is subject to the terms and conditions defined in file
# 'LICENSE', which is part of this source code package
import json
from datetime import datetime
from georeference.models.raw_maps import RawMap
from georeference.models.map_view import MapView
from georeference.models.transformations import Transformation, EnumValidationValue
from georeference.models.jobs import Job, EnumJobType
from georeference.settings import ROUTE_PREFIX
from georeference.utils.parser import to_public_map_id


def test_GET_mapview_for_id_success(testapp, dbsession):
    # Insert an unprocessed job for the map_id
    dbsession.add(
        MapView(
            id=1,
            submitted=datetime.now().isoformat(),
            user_id='test',
            public_id="test_view",
            map_view_json="",
            request_count=0,
            last_request=datetime.now().isoformat(),
        )
    )

    dbsession.flush()
    res = testapp.get(ROUTE_PREFIX + "/map_view/" + "test_view", status=200)
    map_view_json = res.json_body["map_view_json"]

    assert res.status_int == 200
    assert map_view_json is not None
    assert map_view_json == ""

    dbsession.rollback()


def test_GET_mapview_for_id_failure(testapp):
    res = testapp.get(ROUTE_PREFIX + "/map_view/" + "test_view", status=404)

    assert res.status_int == 404


def test_POST_MapView_failure_invalid_json(testapp, dbsession):
    # Create and perform test request
    params = {
        'map_view_json': "{'test': 1}",
        'user_id': 'test'
    }

    res = testapp.post(ROUTE_PREFIX + '/map_view/', params=json.dumps(params),
                       content_type='application/json; charset=utf-8', status=400)

    # First of all rollback session
    dbsession.rollback()

    # Ensure that the status codes reflects a bad request
    assert res.status_int == 400


def test_POST_mapview_failure_missing_user(testapp, dbsession):
    minimal_working_example = {
        "activeBasemapId": "slub-osm",
        "is3dEnabled": False,
        "operationalLayers": [],
        "mapView": {
            "center": [1039475.3400097956, 6695196.931201956],
            "resolution": 1.194328566789627,
            "rotation": 0,
            "zoom": 11,
        },
    }

    # Create and perform test request
    params = {
        'map_view_json': minimal_working_example
    }

    res = testapp.post(ROUTE_PREFIX + '/map_view/', params=json.dumps(params),
                       content_type='application/json; charset=utf-8', status=400)

    # First of all rollback session
    dbsession.rollback()

    # Ensure that the status codes reflects a bad request
    assert res.status_int == 400


def test_POST_mapview_success(testapp, dbsession):
    minimal_working_example = {
        "activeBasemapId": "slub-osm",
        "is3dEnabled": False,
        "operationalLayers": [],
        "mapView": {
            "center": [1039475.3400097956, 6695196.931201956],
            "resolution": 1.194328566789627,
            "rotation": 0,
            "zoom": 11,
        },
    }

    # Create and perform test request
    params = {
        'map_view_json': minimal_working_example,
        'user_id': "test"
    }

    res = testapp.post(ROUTE_PREFIX + '/map_view/', params=json.dumps(params),
                       content_type='application/json; charset=utf-8', status=200)

    # First of all rollback session
    dbsession.rollback()

    # Ensure that the response is not empty
    public_map_id = res.json_body["map_view_id"]
    assert res.status_int == 200
    assert public_map_id is not None and public_map_id != ""
