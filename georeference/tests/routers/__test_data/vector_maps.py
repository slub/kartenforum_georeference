#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by nicolas.looschen@pikobytes.de on 12.11.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package


empty_feature_collection = {"type": "FeatureCollection", "features": []}

vector_map_updated_metadata = {
    "title": "Updated title",
    "time_period": ["2000-01-01", "2000-01-31"],
    "description": "Updated description",
}

vector_map_metadata_missing_required_properties = {
    "description": "This is a test vector map",
    "link_thumb": "https://bla.bla",
}

vector_map_with_point = {
    "title": "Test Vector Map",
    "time_period": ["2000-01-01", "2000-01-31"],
    "description": "This is a test vector map",
    "geojson": {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "Point 1"},
                "geometry": {"type": "Point", "coordinates": [0, 0]},
            }
        ],
    },
}

vector_map_with_empty_feature_collection = {
    "title": "Test Vector Map",
    "time_period": ["2000-01-01", "2000-01-31"],
    "description": "This is a test vector map",
    "geojson": empty_feature_collection,
}

vector_map_with_missing_required_metadata_props = {
    "description": "This is a test vector map",
    "geojson": empty_feature_collection,
}


vector_map_patch_payload_with_metadata = {
    "metadata": vector_map_updated_metadata,
    "geojson": empty_feature_collection,
    "current_version": 1,
}

vector_map_patch_payload_with_invalidmetadata = {
    "metadata": vector_map_metadata_missing_required_properties,
    "geojson": empty_feature_collection,
    "current_version": 1,
}

vector_map_patch_payload_without_metadata = {
    "geojson": empty_feature_collection,
    "current_version": 0,
}

invalid_metadatas_time_period = [
    (
        {
            "time_period": [],
            "description": "TestDescription",
            "link_thumb": "https://testlinkthumb.test.bla",
            "title": "test",
        },
        "too_short",
    ),
    (
        {
            "time_period": ["2025-01-01", "2000-01-01", "2002-01-02"],
            "description": "TestDescription",
            "link_thumb": "https://testlinkthumb.test.bla",
            "title": "test",
        },
        "too_long",
    ),
    (
        {
            "time_period": ["2025-01-01", "2000-01-01"],  # start > end
            "description": "TestDescription",
            "link_thumb": "https://testlinkthumb.test.bla",
            "title": "test",
        },
        "value_error",
    ),
]

patch_payloads_metadata_only_invalid_time_period = [
    (
        {
            "metadata": {
                "title": "test",
                "time_period": [],
            },
            "current_version": 1,
        },
        "too_short",
    ),
    (
        {
            "metadata": {
                "title": "test",
                "time_period": ["2025-01-01", "2000-01-01", "2002-01-02"],
            },
            "current_version": 1,
        },
        "too_long",
    ),
    (
        {
            "metadata": {
                "title": "test",
                "time_period": ["2025-01-01", "2000-01-01"],  # start > end
            },
            "current_version": 1,
        },
        "value_error",
    ),
]

vector_maps_invalid_time_period = [
    (
        {
            "time_period": [],
            "description": "TestDescription",
            "link_thumb": "https://testlinkthumb.test.bla",
            "title": "test",
            "geojson": empty_feature_collection,
        },
        "too_short",
    ),
    (
        {
            "time_period": ["2025-01-01", "2000-01-01", "2002-01-02"],
            "description": "TestDescription",
            "link_thumb": "https://testlinkthumb.test.bla",
            "title": "test",
            "geojson": empty_feature_collection,
        },
        "too_long",
    ),
    (
        {
            "time_period": ["2025-01-01", "2000-01-01"],  # start > end
            "description": "TestDescription",
            "link_thumb": "https://testlinkthumb.test.bla",
            "title": "test",
            "geojson": empty_feature_collection,
        },
        "value_error",
    ),
]
