#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by nicolas.looschen@pikobytes.de on 18.01.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package.

from georeference.schema.general import two_dimensional_point

map_view_schema = {
    "type": "object",
    "properties": {
        # in order for the "additionalProperties" key to work correctly, all expected properties have to be defined here
        "activeBasemapId": {"type": "string"},
        "customBasemaps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "label": {"type": "string"},
                    "urls": {"type": "array"},
                    "type": {"type": "string"}
                },
                "required": ["id", "label", "urls"]
            }
        },
        "is3dEnabled": {"type": "boolean"},
        "mapView": {"type": "object"},
        "operationalLayers": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"enum": ["geojson", "historic_map"]},
                    "id": {"type": "string"},
                    "isVisible": {"type": "boolean"},
                    "opacity": {"type": "number"},
                    "properties": {"type": "object"},
                    "geojson": {"type": "object"},
                    "coordinates": {"type": "array"}
                },
                "if": {"properties": {"type": {"const": "geojson"}}, "required": ["type"]},
                "then": {
                    "properties": {
                        "geojson": {
                            "$ref": "https://geojson.org/schema/FeatureCollection.json"
                        },
                    },
                    "required": ["geojson"],
                },
                "else": {
                    "properties": {
                        "coordinates": {"type": "array"},
                    },
                    "required": ["coordinates"],
                },
                "additionalProperties": False
            },
        },
    },
    # further constraints on the properties can be defined here, for example the map view differs between 2d and 3d mode
    "if": {"properties": {"is3dEnabled": {"const": True}}},
    "then": {
        "properties": {
            "mapView": {
                "type": "object",
                "properties": {
                    "direction": {"type": "object", "properties": {"x": {"type": "number"}, "y": {"type": "number"},
                                                                   "z": {"type": "number"}},
                                  "additionalProperties": False},
                    "position": {"type": "object", "properties": {"x": {"type": "number"}, "y": {"type": "number"},
                                                                  "z": {"type": "number"}},
                                 "additionalProperties": False},
                    "up": {"type": "object",
                           "properties": {"x": {"type": "number"}, "y": {"type": "number"}, "z": {"type": "number"}},
                           "additionalProperties": False},
                    "right": {"type": "object",
                              "properties": {"x": {"type": "number"}, "y": {"type": "number"}, "z": {"type": "number"}},
                              "additionalProperties": False},
                },
                "required": ["direction", "position", "up", "right"]
            }
        },
    },
    "else": {
        "properties": {
            "mapView": {
                "type": "object",
                "properties": {
                    "center": two_dimensional_point,
                    "resolution": {"type": "number"},
                    "rotation": {"type": "number"},
                    "zoom": {"type": "number"},
                },
                "required": ["center", "zoom"]
            },
            "searchOptions": {"type": "string"}
        },
        "required": ["mapView"]
    },
    "additionalProperties": False
}

# Define the request schema for this endpoint
map_view_requestSchema = {
    "type": "object",
    "properties": {
        "user_id": {"type": "string"},
        "map_view_json": map_view_schema
    },
    "required": ["map_view_json", "user_id"],
    "additionalProperties": False
}
