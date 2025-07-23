#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created by tom.schulze@pikobytes.de on 29.04.25.

This file is subject to the terms and conditions defined in
file "LICENSE.txt", which is part of this source code package.
"""

from enum import Enum
from typing import Optional
import uuid
from pydantic import NaiveDatetime
from sqlalchemy.dialects.postgresql import ARRAY, UUID, DATE
from sqlmodel import Field, SQLModel, select, col, Column, Enum as sqlmodelEnum


from georeference.models import datetime_without_timezone


class ExternalContentTypeEnum(str, Enum):
    VKF = "vkf:geojson-spec-v1"
    IDOHIST = "idohist:idohist-v1"


class VectorMapExternal(SQLModel, table=True):
    __tablename__: str = "vector_maps_external"  # type: ignore
    id: int = Field(primary_key=True, default=None)
    public_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Field(UUID(as_uuid=True), unique=True, nullable=False, index=True),
    )
    title: str
    description: Optional[str]
    link_thumb: Optional[str]
    link_content: str
    content_type: ExternalContentTypeEnum = Field(
        default=ExternalContentTypeEnum.VKF.value,
        sa_column=Column(
            sqlmodelEnum(
                ExternalContentTypeEnum,
                native_enum=False,
                values_callable=lambda x: [e.value for e in x],
            )
        ),
    )
    time_period: list = Field(sa_column=Column(ARRAY(DATE), nullable=False))
    submitted: NaiveDatetime = datetime_without_timezone
    last_change: NaiveDatetime = datetime_without_timezone
    request_count: int = Field(default=0)
    last_request: Optional[NaiveDatetime] = datetime_without_timezone

    @classmethod
    def all(cls, session):
        return session.exec(select(VectorMapExternal)).all()

    @classmethod
    def by_public_id(cls, public_id: uuid.UUID, session) -> "VectorMapExternal":
        return session.exec(
            select(VectorMapExternal).where(
                col(VectorMapExternal.public_id) == public_id
            )
        ).first()
