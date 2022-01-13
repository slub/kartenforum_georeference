#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 10.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import json
from georeference.settings import ROUTE_PREFIX
from georeference.utils.parser import toPublicOAI

def test_POST_POST_TransformationTryForMapId_success(testapp):
    map_id = 10001556
    params = {'source': 'pixel', 'target': 'EPSG:4314', 'algorithm': 'tps',
              'gcps': [{'source': [6700, 998], 'target': [14.809598142072, 50.897193140898]},
                       {'source': [6656, 944], 'target': [14.808447338463, 50.898010359738]},
                       {'source': [6687, 1160], 'target': [14.809553411787, 50.894672081543]},
                       {'source': [6687, 1160], 'target': [14.809553411787, 50.894672081543]}]}

    # Build test request
    res = testapp.post(ROUTE_PREFIX + '/transformations/try', json.dumps({ 'params': params, 'map_id': toPublicOAI(map_id)}), content_type='application/json; charset=utf-8', status=200)
    assert res.status_int == 200

def test_POST_POST_TransformationTryForMapIdWithClip_success(testapp):
    map_id = 10001556
    params = {'source': 'pixel', 'target': 'EPSG:4314', 'algorithm': 'tps',
              'gcps': [{'source': [6700, 998], 'target': [14.809598142072, 50.897193140898]},
                       {'source': [6656, 944], 'target': [14.808447338463, 50.898010359738]},
                       {'source': [6687, 1160], 'target': [14.809553411787, 50.894672081543]},
                       {'source': [6687, 1160], 'target': [14.809553411787, 50.894672081543]}]}
    clip = {
        'type': 'Polygon',
        'crs': {'type': 'name', 'properties': {'name': 'EPSG:4326'}},
        'coordinates': [[[14.66364715, 50.899831877], [14.661734495, 50.799776765], [14.76482527, 50.800276974], [14.76601098, 50.800290518], [14.766134477, 50.790482954], [14.782466161, 50.790564091], [14.782294867, 50.800358074], [14.829388684, 50.800594678], [14.829132977, 50.900185772], [14.829130294, 50.900185772], [14.66364715, 50.899831877]]]
    }

    # Build test request
    res = testapp.post(ROUTE_PREFIX + '/transformations/try', json.dumps({ 'params': params, 'map_id': toPublicOAI(map_id), 'clip': clip }), content_type='application/json; charset=utf-8', status=200)
    assert res.status_int == 200