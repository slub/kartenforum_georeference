#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 01.03.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
from georeference.schema.general import RegExLink


map_schema = {
    "type": "object",
    "properties": {
        # Allows the download of the raw data
        "allow_download": {"type": "boolean"},
        # Integer which represents an EPSG code. Null should be allowed.
        "default_crs": {"type": ["number", "null"]},
        # Description of the original map, e.g: Topographische Karte (Äquidistantenkarte) Sachsen; 5154,1892
        "description": {"type": ["string", "null"]},
        # License
        "license": {"type": "string"},
        # Link to the zoomify tiles (optional), e.g. https://fotothek.slub-dresden.de/zooms/df/dk/0010000/df_dk_0010001_5154_1892/ImageProperties.xml. All links should be https.
        "link_zoomify": {"oneOf": [
            {
                "type": "string",
                "pattern": RegExLink
            },
            { "type": "null" }
        ]},
        # Link to a thumbnail small 120x120 (optional), e.g. https://fotothek.slub-dresden.de/thumbs/df/dk/0010000/df_dk_0010001_5154_1892.jpg. All links should be https.
        "link_thumb_small": {"oneOf": [
            {
                "type": "string",
                "pattern": RegExLink
            },
            { "type": "null" }
        ]},
        # Link to a thumbnail mid 400x400 (optional, e.g. http://fotothek.slub-dresden.de/mids/df/dk/0010000/df_dk_0010001_5154_1892.jpg, All links should be https.
        "link_thumb_mid": {"oneOf": [
            {
                "type": "string",
                "pattern": RegExLink
            },
            { "type": "null" }
        ]},
        # AE = Äquidistantenkarte
        # AK = Andere Karten
        # CM = Stadtpläne / City maps
        # GL = Geologische Karten
        # MB = Meilenblätter
        # MTB = Messtischblätter
        # TK = Topographische Karte des Deutschen Reiches
        # TKX = Topographische Karten
        "map_type": {"enum": ["ae", "ak", "cm", "gl", "mb", "mtb", "tk", "tkx"]},
        # Scale of the map, e.g. a scale of 1:25000 = 25000
        "map_scale": {"type": "number"},
        # Measures of the original map, e.g. 48 x 45 cm
        "measures": {"type": ["string", "null"]},
        # Owner of the original map, e.g. SLUB
        "owner": {"type": ["string", "null"]},
        # Permalink
        "permalink": {"type": ["string", "null"]},
        # PPN number, e.g. ppn33592090X
        "ppn": {"type": ["string", "null"]},
        # Technic used to produce the original image, e.g. Lithografie & Umdruck
        "technic": {"type": ["string", "null"]},
        # Time at which the original map was publicated
        "time_of_publication": {"anyOf": [
            {"type": "string", "format": "date-time"},
            {"type": "string",
             "pattern": "^([\\+-]?\\d{4}(?!\\d{2}\\b))((-?)((0[1-9]|1[0-2])(\\3([12]\\d|0[1-9]|3[01]))?|W([0-4]\\d|5[0-2])(-?[1-7])?|(00[1-9]|0[1-9]\\d|[12]\\d{2}|3([0-5]\\d|6[1-6])))([T\\s]((([01]\\d|2[0-3])((:?)[0-5]\\d)?|24\\:?00)([\\.,]\\d+(?!:))?)?(\\17[0-5]\\d([\\.,]\\d+)?)?([zZ]|([\\+-])([01]\\d|2[0-3]):?([0-5]\\d)?)?)?)?$"
             }
        ]},
        # Title, e.g. "Äquidistantenkarte 107 : Section Zittau, 1892"
        "title": {"type": "string"},
        # Title, e.g. Topographische Karte (Äquidistantenkarte) Sachsen; 5154,1892
        "title_serie": {"type": ["string", "null"]},
        # Title, e.g. Section Zittau
        "title_short": {"type": "string"},
        # Type of the map e.g. Druckgraphic
        "type": {"type": ["string", "null"]},
    },
    "required": ["description", "license", "map_scale", "map_type", "time_of_publication", "title",
                 "title_short"]
}

# Keys which will be stored in the raw_map model
raw_map_keys = ['allow_download', 'default_crs', 'map_scale', 'map_type']

# Keys which will be stored in the metadata model
metadata_keys = [item for item in map_schema['properties'].keys() if item not in raw_map_keys]
