#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 10.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
from georeference.settings import ROUTE_PREFIX

# def test_getAdminGeorefs_success_mapId(testapp):
#     # For clean test setup the test data should also be added to the database within this method
#     # @TODO
#     map_id = 10001556
#
#     # Build test request
#     res = testapp.get(ROUTE_PREFIX + '/admin/georefs?map_id=%s' % map_id, status=200)
#     assert res.status_int == 200
#     assert len(res.json) == 2
#
# def test_getAdminGeorefs_failed_missingParameter(testapp):
#     res = testapp.get(ROUTE_PREFIX + '/admin/georefs', status=400)
#     assert res.status_int == 400