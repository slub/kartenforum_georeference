#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created by tom.schulze@pikobytes.de on 02.05.25.

This file is subject to the terms and conditions defined in
file "LICENSE.txt", which is part of this source code package.
"""

valid_vector_map = {
    "title": "TestTitle",
    "description": "TestDescription",
    "link_thumb": "https://testlinkthumb.test.bla",
    "link_content": "https://testlinkcontent.test.bla",
    "time_period": ["2025-01-01", "2025-02-01"],
}

invalid_vector_map = {
    "description": "TestDescription",
    "link_thumb": "https://testlinkthumb.test.bla",
}

invalid_vector_maps_time_period = [
    (
        {
            "time_period": [],
            "description": "TestDescription",
            "link_thumb": "https://testlinkthumb.test.bla",
            "link_content": "https://testlinkcontent.test.bla",
            "title": "test",
        },
        "too_short",
    ),
    (
        {
            "time_period": ["2025-01-01", "2000-01-01", "2002-01-02"],
            "description": "TestDescription",
            "link_thumb": "https://testlinkthumb.test.bla",
            "link_content": "https://testlinkcontent.test.bla",
            "title": "test",
        },
        "too_long",
    ),
    (
        {
            "time_period": ["2025-01-01", "2000-01-01"],  # start > end
            "description": "TestDescription",
            "link_thumb": "https://testlinkthumb.test.bla",
            "link_content": "https://testlinkcontent.test.bla",
            "title": "test",
        },
        "value_error",
    ),
]

empty_geojson = {"type": "FeatureCollection", "features": []}

invalid_geojson = {
    "type": "FeatureCollection",
    "features": [{"type": "Feature", "no": "more"}],
}
