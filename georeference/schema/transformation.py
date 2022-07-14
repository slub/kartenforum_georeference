#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 31.01.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package

from georeference.schema.general import two_dimensional_point

# Example:
#
# {
#     'clip': {
#         'type': 'Polygon',
#         'crs': {'type': 'name', 'properties': {'name': 'EPSG:4314'}},
#         'coordinates': [[[14.66364715, 50.899831877], [14.661734495, 50.799776765], [14.76482527, 50.800276974],
#                          [14.76601098, 50.800290518], [14.766134477, 50.790482954], [14.782466161, 50.790564091],
#                          [14.782294867, 50.800358074], [14.829388684, 50.800594678], [14.829132977, 50.900185772],
#                          [14.829130294, 50.900185772], [14.66364715, 50.899831877]]]
#     },
#     'params': {
#         'source': 'pixel',
#         'target': 'EPSG:4314',
#         'algorithm': 'tps',
#         'gcps': [{'source': [6700, 998], 'target': [14.809598142072, 50.897193140898]},
#                  {'source': [6656, 944], 'target': [14.808447338463, 50.898010359738]},
#                  {'source': [6687, 1160], 'target': [14.809553411787, 50.894672081543]},
#                  {'source': [6969, 3160], 'target': [14.816612768409, 50.863606051111]}],
#     },
#     'overwrites': 0,
#     'user_id': 'test'
# }

_base_transformation_schema = {
    "type": "object",
    "properties": {
        "clip": {
            "type": "object",
            "properties": {
                "type": {
                    "enum": ["Polygon"]
                },
                "coordinates": {
                    "type": "array",
                    "items": {
                        "type:": "array",
                        # at least 3 2-dimensional coordinates for a polygon
                        "minItems": 3,
                        "items": two_dimensional_point
                    }
                }
            },
            "required": ["type", "coordinates"],
            "additionalProperties": False
        },
        "params": {
            "type": "object",
            "properties": {
                "algorithm": {"enum": ["tps", "affine", "polynom"]},
                "gcps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "minItems": 3,
                        "properties": {
                            "source": two_dimensional_point,
                            "target": two_dimensional_point
                        }
                    }
                }
            },
            "required": ["algorithm", "gcps"],
            "additionalProperties": False
        }
    },
    "required": ["params"]
}

transformation_schema = {
    "allOf": [
        _base_transformation_schema,
        {
            "type": "object",
            "properties": {
                "overwrites": {"type": "number"},
                "user_id": {"type": "string"},
                "map_id": {"type": "string"}
            },
            "required": ["overwrites", "user_id", "map_id"]
        }
    ]
}

id_only_transformation_schema = {
    "type": "object",
    "properties": {
        "transformation_id": {"type": "number"}
    },
    "required": ["transformation_id"]
}
