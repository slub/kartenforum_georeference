#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Created by nicolas.looschen@pikobytes.de on 22.07.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
from typing import Optional

from pydantic import BaseModel, NaiveDatetime

from georeference.models import datetime_without_timezone, varchar_255


class JobMixin(BaseModel):
    id: int
    submitted: NaiveDatetime = datetime_without_timezone
    type: str = varchar_255
    description: str
    state: str = varchar_255
    user_id: str = varchar_255
    comment: Optional[str] = varchar_255
