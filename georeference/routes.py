#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 01.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package

ROUTE_PREFIX = ''

def includeme(config):
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('summary_georeference', ROUTE_PREFIX + '/summary/georeference')
    config.add_route('summary_helloworld', ROUTE_PREFIX + '/')