#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 09.09.21
#
# This file is subject to the terms and conditions defined in file
# 'LICENSE', which is part of this source code package
import json
from georeference.settings import ROUTE_PREFIX

def test_getGereofs_success_emptyResult(testapp):
    # For clean test setup the test data should also be added to the database within this method
    # @TODO
    map_id = 10003265

    # Build test request
    res = testapp.get(ROUTE_PREFIX + '/maps/%s/georefs' % map_id, status=200)
    print(res.json)
    assert res.status_int == 200
    assert len(res.json['items']) == 0

def test_getGereofs_success_georefResults(testapp):
    # For clean test setup the test data should also be added to the database within this method
    # @TODO
    map_id = 10001556

    # Build test request
    res = testapp.get(ROUTE_PREFIX + '/maps/%s/georefs' % map_id, status=200)
    assert res.status_int == 200
    assert len(res.json['items']) == 2

def test_postGereofs_success_georefResults(testapp):
    # For clean test setup the test data should also be added to the database within this method
    # @TODO
    map_id = 10001556

    # Build test request
    res = testapp.post(ROUTE_PREFIX + '/maps/%s/georefs' % map_id, status=200)
    assert res.status_int == 200






