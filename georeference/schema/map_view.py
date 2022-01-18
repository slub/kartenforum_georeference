#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by nicolas.looschen@pikobytes.de on 18.01.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package.


map_view_schema = {
    "type": "object",
    "properties": {
        "activeBasemapId": {"type": "string"},
        "is3dEnabled": {"type": "boolean"},
        "operationalLayers": {
            "type": "array",
            "items": {
                "anyOf": [
                    {
                        "type": "object",
                        "properties": {
                            "type": {"enum": ["geojson", "historic_map"]},
                            "id": {"type": "string"},
                            "isVisible": {"type": "boolean"},
                            "opacity": {"type": "number"},
                            "properties": {
                                "type": "object",
                            },
                            "coordinates": {"type": "array"},
                        },
                        "required": ["coordinates", "id", "type"],
                    },
                    {
                        "type": "object",
                        "properties": {
                            "type": {"enum": ["geojson", "historic_map"]},
                            "id": {"type": "string"},
                            "isVisible": {"type": "boolean"},
                            "opacity": {"type": "number"},
                            "properties": {"type": "object"},
                            "geojson": {
                                "$ref": "https://geojson.org/schema/FeatureCollection.json"
                            },
                        },
                    },
                ]
            },
        },
    },
    "if": {"properties": {"is3dEnabled": {"const": True}}},
    "then": {
        "properties": {
            "mapview": {
                "type": "object",
                "properties": {
                    "direction": {"type": "array"},
                    "direction": {"type": "array"},
                    "up": {"type": "array"},
                    "right": {"type": "array"},
                },
            }
        },
        "else": {
            "properties": {
                "mapView": {
                    "type": "object",
                    "properties": {
                        "center": {"type": "array"},
                        "resolution": {"type": "number"},
                        "rotation": {"type": "number"},
                        "zoom": {"type": "number"},
                    },
                }
            }
        },
    },
}
