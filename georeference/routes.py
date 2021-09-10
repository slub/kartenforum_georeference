#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 01.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
from .settings import ROUTE_PREFIX

def includeme(config):
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('maps', ROUTE_PREFIX + '/maps/{map_id}')
    config.add_route('maps_georefs', ROUTE_PREFIX + '/maps/{map_id}/georefs')
    config.add_route('maps_georefs_ids', ROUTE_PREFIX + '/maps/{map_id}/georefs/{georef_id}')
    config.add_route('maps_georefs_validate', ROUTE_PREFIX + '/maps/{map_id}/georefs_validate')
    config.add_route('user_history', ROUTE_PREFIX + '/user/{user_id}/history')
    config.add_route('statistics', ROUTE_PREFIX + '/statistics')
