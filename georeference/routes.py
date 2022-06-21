#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 01.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
from .settings import ROUTE_PREFIX

def includeme(config):
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('jobs', ROUTE_PREFIX + '/jobs')
    config.add_route('maps', ROUTE_PREFIX + '/maps/{map_id:.*}')
    config.add_route('mosaic_maps', ROUTE_PREFIX + '/mosaic_maps')
    config.add_route('mosaic_map', ROUTE_PREFIX + '/mosaic_map/{mosaic_map_id}')
    config.add_route('mosaic_map_refresh', ROUTE_PREFIX + '/mosaic_map/{mosaic_map_id}/refresh')
    config.add_route('statistics', ROUTE_PREFIX + '/statistics')
    config.add_route('transformations', ROUTE_PREFIX + '/transformations')
    config.add_route('user_history', ROUTE_PREFIX + '/user/{user_id}/history')
    config.add_route('map_view', ROUTE_PREFIX + '/map_view/{map_view_id:.*}')


