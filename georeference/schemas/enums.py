#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by nicolas.looschen@pikobytes.de on 22.07.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
from enum import Enum, EnumMeta

from georeference.models.enums import EnumJobType


class EnumAllowedJobTypes(Enum, metaclass=EnumMeta):
    TRANSFORMATION_PROCESS = EnumJobType.TRANSFORMATION_PROCESS.value
    TRANSFORMATION_SET_VALID = EnumJobType.TRANSFORMATION_SET_VALID.value
    TRANSFORMATION_SET_INVALID = EnumJobType.TRANSFORMATION_SET_INVALID.value
