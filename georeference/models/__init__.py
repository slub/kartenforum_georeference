#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 01.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package

from sqlalchemy import String, DateTime
from sqlmodel import Field

# Reusable field type definitions

varchar_255 = Field(sa_type=String(length=255))

datetime_without_timezone = Field(sa_type=DateTime(timezone=False))
