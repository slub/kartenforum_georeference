#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Created by nicolas.looschen@pikobytes.de on 10.07.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import os

from georeference.config.settings import get_settings


# Get root params from settings
settings = get_settings()


# Template string for the public id of a single georefence map
TEMPLATE_PUBLIC_MAP_ID = "oai:de:slub-dresden:vk:id-{}"

if "{}" not in TEMPLATE_PUBLIC_MAP_ID:
    raise BaseException("Could not process TEMPLATE_PUBLIC_MAP_ID")

# Template string for the public id of a mosaic map
TEMPLATE_PUBLIC_MOSAIC_MAP_ID = "oai:de:slub-dresden:vk:mosaic:id-{}"

if "{}" not in TEMPLATE_PUBLIC_MOSAIC_MAP_ID:
    raise BaseException("Could not process TEMPLATE_PUBLIC_MOSAIC_MAP_ID")

PATH_MAPFILE_TEMPLATES = os.path.join(settings.PATH_BASE_ROOT, "./templates")

# Georeference TMS Cache url
TEMPLATE_TMS_URLS = settings.TEMPLATE_TMS_URLS

# Template for the public thumbnail images
TEMPLATE_PUBLIC_THUMBNAIL_URL = settings.TEMPLATE_THUMBNAIL_URL

# Template for the public wms service
TEMPLATE_PUBLIC_WMS_URL = settings.TEMPLATE_WMS_URL

# Template for the public wcs service
TEMPLATE_PUBLIC_WCS_URL = settings.TEMPLATE_WCS_URL

# Template for the public zoomify tiles
TEMPLATE_PUBLIC_ZOOMIFY_URL = settings.TEMPLATE_ZOOMIFY_URL

# WMS Service default url template
TEMPLATE_TRANSFORMATION_WMS_URL = settings.TEMPLATE_WMS_TRANSFORM_URL
