#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 21.06.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
from georeference.schema.general import reg_ex_link


mosaic_map_schema_write = {
    "type": "object",
    "properties": {
        # Name of the service"
        "name": {"type": "string"},
        # Ids of the associated raw maps
        "raw_map_ids":  {"type": "array", "items": { "type": "string" }},
        # Title, e.g. "Äquidistantenkarte Sachsen, 1892 bis 1900"
        "title": {"type": "string"},
        # Title, e.g. Äquidistantenkarte
        "title_short": {"type": "string"},
        # Publication date of the mosaic map
        "time_of_publication": {"type": "string", "format": "date-time"},
        # Thumbnail link of the mosaic map
        "link_thumb": {
            "type": "string",
            "pattern": reg_ex_link
        },
        # Map scale of the mosaic map
        "map_scale": {"type": "number"}
    },
    "required": ["name", "raw_map_ids", "title", "title_short", "time_of_publication", "link_thumb", "map_scale"]
}


mosaic_map_schema_read = {
    "allOf": [
        mosaic_map_schema_write,
        {
            "type": "object",
            "properties": {
                # Id of the mosaic_map
                "id": {"type": ["string", "null"]},
                "last_change": {"type": "string", "format": "date-time"},
                "last_service_update": {"anyOf": [
                    {"type": "string", "format": "date-time"},
                    {"type": "null" }
                    ]
                },
                "last_overview_update": {"anyOf": [
                    {"type": "string", "format": "date-time"},
                    {"type": "null" }
                    ]
                },
            },
            "required": ["id", "last_change", "last_service_update", "last_overview_update"]
        }
    ]
}