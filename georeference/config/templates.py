#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from georeference.config.paths import BASE_PATH

# Created by nicolas.looschen@pikobytes.de on 10.07.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package

# Template string for the public id of a single georefence map
TEMPLATE_PUBLIC_MAP_ID = "oai:de:slub-dresden:vk:id-{}"

if "{}" not in TEMPLATE_PUBLIC_MAP_ID:
    raise BaseException("Could not process TEMPLATE_PUBLIC_MAP_ID")

# Template string for the public id of a mosaic map
TEMPLATE_PUBLIC_MOSAIC_MAP_ID = "oai:de:slub-dresden:vk:mosaic:id-{}"

if "{}" not in TEMPLATE_PUBLIC_MOSAIC_MAP_ID:
    raise BaseException("Could not process TEMPLATE_PUBLIC_MOSAIC_MAP_ID")
PATH_MAPFILE_TEMPLATES = os.path.join(BASE_PATH, "./templates")

# Georeference TMS Cache url
TEMPLATE_TMS_URLS = ["http://vk2-cdn.slub-dresden.de/tms2/{}"]

# Template for the public thumbnail images
TEMPLATE_PUBLIC_THUMBNAIL_URL = "https://thumbnail-slub.pikobytes.de/zoomify/{}"

# Template for the public wms service
TEMPLATE_PUBLIC_WMS_URL = "https://wms-slub.pikobytes.de/map/{}"

# Template for the public wcs service
TEMPLATE_PUBLIC_WCS_URL = "https://wcs-slub.pikobytes.de/map/{}"

# Template for the public zoomify tiles
TEMPLATE_PUBLIC_ZOOMIFY_URL = (
    "https://zoomify-slub.pikobytes.de/zoomify/{}/ImageProperties.xml"
)

# WMS Service default url template
TEMPLATE_TRANSFORMATION_WMS_URL = "http://localhost:8080/?map=/etc/mapserver/{}"
