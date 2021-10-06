#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 10.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import json
from georeference.settings import ROUTE_PREFIX

def test_POST_POST_TransformationTryForMapId_success(testapp):
    map_id = 10001556
    params = {'source': 'pixel', 'target': 'EPSG:4314', 'algorithm': 'tps',
              'gcps': [{'source': [6700, 998], 'target': [14.809598142072, 50.897193140898]},
                       {'source': [6656, 944], 'target': [14.808447338463, 50.898010359738]},
                       {'source': [6687, 1160], 'target': [14.809553411787, 50.894672081543]},
                       {'source': [6687, 1160], 'target': [14.809553411787, 50.894672081543]}]}

    # Build test request
    res = testapp.post(ROUTE_PREFIX + '/maps/%s/transformations/try' % map_id, json.dumps(params), content_type='application/json; charset=utf-8', status=200)
    assert res.status_int == 200