#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
