#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 10.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
from georeference.settings import ROUTE_PREFIX

def test_getGeorefsForId_success_georefResults(testapp):
    # For clean test setup the test data should also be added to the database within this method
    # @TODO
    map_id = 10001556
    georef_id = 11823

    # Build test request
    res = testapp.get(ROUTE_PREFIX + '/maps/%s/georefs/%s' % (map_id, georef_id), status=200)
    assert res.status_int == 200

def test_getGeorefsForId_failed_notfound(testapp):
    # For clean test setup the test data should also be added to the database within this method
    # @TODO
    map_id = 10001556
    georef_id = 111823

    # Build test request
    res = testapp.get(ROUTE_PREFIX + '/maps/%s/georefs/%s' % (map_id, georef_id), status=404)
    assert res.status_int == 404