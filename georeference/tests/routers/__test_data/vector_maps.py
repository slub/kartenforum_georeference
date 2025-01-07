#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by nicolas.looschen@pikobytes.de on 12.11.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package


empty_feature_collection = {"type": "FeatureCollection", "features": []}

vector_map_with_point = {
    "title": "Test Vector Map",
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
    "description": "This is a test vector map",
    "geojson": empty_feature_collection,
}


vector_map_updated_metadata = {
    "title": "Updated title",
    "description": "Updated description",
}


vector_map_patch_payload_with_metadata = {
    "metadata": vector_map_updated_metadata,
    "geojson": empty_feature_collection,
    "current_version": 1,
}

vector_map_patch_payload_without_metadata = {
    "geojson": empty_feature_collection,
    "current_version": 0,
}
