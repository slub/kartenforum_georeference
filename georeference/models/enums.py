#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Created by nicolas.looschen@pikobytes.de on 22.07.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package

from enum import Enum, EnumMeta


class EnumJobType(Enum, metaclass=EnumMeta):
    TRANSFORMATION_PROCESS = "transformation_process"
    TRANSFORMATION_SET_VALID = "transformation_set_valid"
    TRANSFORMATION_SET_INVALID = "transformation_set_invalid"
    MAPS_CREATE = "maps_create"
    MAPS_DELETE = "maps_delete"
    MAPS_UPDATE = "maps_update"
    MOSAIC_MAP_CREATE = "mosaic_map_create"
    MOSAIC_MAP_DELETE = "mosaic_map_delete"


class EnumJobState(Enum, metaclass=EnumMeta):
    COMPLETED = "completed"
    FAILED = "failed"
    NOT_STARTED = "not_started"
