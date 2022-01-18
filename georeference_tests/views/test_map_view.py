#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 09.09.21
#
# This file is subject to the terms and conditions defined in file
# 'LICENSE', which is part of this source code package
import json
from datetime import datetime
from georeference.models.original_maps import OriginalMap
from georeference.models.map_view import MapView
from georeference.models.transformations import Transformation, ValidationValues
from georeference.models.jobs import Job, TaskValues
from georeference.settings import ROUTE_PREFIX
from georeference.utils.parser import toPublicOAI


def test_POST_MapView_success_newMapView(testapp, dbsession):
    map_view_json = "{'test': 1}}"

    # Create and perform test request
    params = {
        'map_view_json': map_view_json,
        'user_id': 'test'
    }

    # Build test request
    res = testapp.post(ROUTE_PREFIX + '/map_views', params=json.dumps(params), content_type='application/json; charset=utf-8', status=200)

    # First of all rollback session
    dbsession.rollback()

    # Run tests
    assert res.status_int == 200
    assert res.json_body['transformation_id'] != None
    assert res.json_body['job_id'] != None
    assert res.json_body['points'] == 400







