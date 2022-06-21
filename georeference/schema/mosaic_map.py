#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 21.06.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
from georeference.schema.general import RegExLink


mosaic_map_schema = {
    "type": "object",
    "properties": {
        # Id of the mosaic_map
        "id": {"type": "string"},
        # Name of the service"
        "name": {"type": "string"},
        # Ids of the associated raw maps
        "raw_map_ids":  {"type": "string", "items": { "type": "string" }},
        # Title, e.g. "Äquidistantenkarte Sachsen, 1892 bis 1900"
        "title": {"type": "string"},
        # Title, e.g. Äquidistantenkarte
        "title_short": {"type": "string"},
        # Publication date of the mosaic map
        "time_of_publication": {"type": "string", "format": "date-time"},
        # Thumbnail link of the mosaic map
        "link_thumb": {
            "type": "string",
            "pattern": RegExLink
        },
        # Map scale of the mosaic map
        "map_scale": {"type": "number"},
        "last_change": {"type": "string", "format": "date-time"},
        "last_service_update": {"type": "string", "format": "date-time"},
        "last_overview_update": {"type": "string", "format": "date-time"},
    },
    "required": ["id", "name", "raw_map_ids", "title", "title_short", "time_of_publication", "link_thumb", "map_scale"]
}
