#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 09.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
from georeference.settings import ROUTE_PREFIX

def test_getMapsById_success_withoutGeorefId(testapp):
    # For clean test setup the test data should also be added to the database within this method
    # @TODO
    mapid = 10003265

    # Build test request
    res = testapp.get(ROUTE_PREFIX + '/maps/%s' % mapid, status=200)
    assert res.status_int == 200
    assert res.json['map_id'] == mapid
    assert res.json['transformation_id'] == None

def test_getMapsById_success_withGeorefId(testapp):
    # For clean test setup the test data should also be added to the database within this method
    # @TODO
    mapid = 10001556

    # Build test request
    res = testapp.get(ROUTE_PREFIX + '/maps/%s' % mapid, status=200)
    assert res.status_int == 200
    assert res.json['map_id'] == mapid
    assert res.json['transformation_id'] == 11823

def test_getMapsById_badrequest(testapp):
    # Build test request
    res = testapp.get(ROUTE_PREFIX + '/maps', status=404)
    assert res.status_int == 404

def test_getMapsById_notfound(testapp):
    res = testapp.get(ROUTE_PREFIX + '/maps', status=404)
    assert res.status_int == 404
