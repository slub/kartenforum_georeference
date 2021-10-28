#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 07.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
from georeference.views.statistics import getStatistics

def test_getStatistics_success(app_request):
    subject = getStatistics(app_request)
    assert app_request.response.status_int == 200
    assert len(subject['georeference_points']) == 2
    assert subject['georeference_map_count'] == 6
    assert subject['not_georeference_map_count'] == 3
