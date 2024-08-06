#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by nicolas.looschen@pikobytes.de on 22.07.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package

from typing import Optional
from pydantic import BaseModel

from georeference.schemas.enums import EnumAllowedJobTypes


class JobDescription(BaseModel):
    transformation_id: int
    comment: Optional[str]


class JobPayload(BaseModel):
    # @TODO: This should probably be renamed to type, but check with frontend beforehand
    name: EnumAllowedJobTypes
    description: JobDescription
