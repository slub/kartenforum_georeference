#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created by tom.schulze@pikobytes.de on 29.04.25.

This file is subject to the terms and conditions defined in
file "LICENSE.txt", which is part of this source code package.
"""

from datetime import datetime, date
from typing import Annotated, Optional
import uuid
from pydantic import AfterValidator, BaseModel, Field, NaiveDatetime, conlist

from georeference.config.constants import regex_link
from georeference.models.vector_map_external import (
    ExternalContentTypeEnum,
    VectorMapExternal,
)


def validate_start_and_end_date(value: list[date]) -> list[date]:
    start = value[0]
    end = value[1]
    if start > end:
        raise ValueError(f"{start} is > {end}")
    return value


class VectorMapExternalPayload(BaseModel):
    description: Optional[str] = None
    link_thumb: Optional[str] = Field(default=None, pattern=regex_link)
    title: str
    content_type: ExternalContentTypeEnum
    link_content: str = Field(pattern=regex_link)
    time_period: Annotated[
        conlist(item_type=date, min_length=2, max_length=2),
        AfterValidator(validate_start_and_end_date),
    ]


class VectorMapExternalCreate(VectorMapExternalPayload):
    def to_db_model(self):
        return VectorMapExternal(
            title=self.title,
            description=self.description,
            link_thumb=self.link_thumb,
            link_content=self.link_content,
            time_period=self.time_period,
            content_type=self.content_type,
            submitted=datetime.now(),
            last_change=datetime.now(),
        )


class VectorMapExternalResponse(BaseModel):
    description: Optional[str] = None
    link_thumb: Optional[str] = None
    id: uuid.UUID
    title: str
    link_content: str
    content_type: str
    time_period: conlist(item_type=date, min_length=2, max_length=2)
    submitted: NaiveDatetime
    last_change: NaiveDatetime


class VectorMapExternalIdResponse(BaseModel):
    id: uuid.UUID
