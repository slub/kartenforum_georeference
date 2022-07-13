#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 05.10.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
from georeference.settings import ROUTE_PREFIX

def test_GET_user_history_success(testapp):
    user_id = 'user_1'

    # Build test request
    res = testapp.get(ROUTE_PREFIX + '/user/%s/history' % user_id, status=200)
    assert res.status_int == 200
    assert len(res.json['georef_profile']) == 18