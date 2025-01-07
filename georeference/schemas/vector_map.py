#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by nicolas.looschen@pikobytes.de on 08.11.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import uuid
from typing import Optional, List

from geojson_pydantic import FeatureCollection
from pydantic import BaseModel, Field, NaiveDatetime, RootModel

from georeference.config.constants import regex_link
from georeference.models.vector_map import RoleEnum


class VectorMapMetadata(BaseModel):
    description: Optional[str] = None
    link_thumb: Optional[str] = Field(default=None, pattern=regex_link)
    title: str


class VectorMapPayload(VectorMapMetadata):
    geojson: FeatureCollection


class VectorMapMetadataUpdate(BaseModel):
    description: Optional[str] = None
    link_thumb: Optional[str] = Field(default=None, pattern=regex_link)
    title: Optional[str]


class VectorMapUpdatePayload(BaseModel):
    metadata: Optional[VectorMapMetadataUpdate] = None
    geojson: Optional[FeatureCollection] = None
    current_version: int


class VectorMapVersionPayload(BaseModel):
    geojson: FeatureCollection
    current_version: int


class VectorMapResponsePublic(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str] = None
    link_thumb: Optional[str] = None
    submitted: NaiveDatetime
    last_change: NaiveDatetime
    geojson: FeatureCollection


class VectorMapResponse(VectorMapResponsePublic):
    version: int
    user_role: Optional[str] = None

    @classmethod
    def to_public_response(cls, vector_map_response: "VectorMapResponse"):
        return vector_map_response.model_dump(exclude={"version", "user_role"})


class VectorMapVersionsResponseEntry(BaseModel):
    version: int
    submitted: NaiveDatetime
    created_by: str


VectorMapVersionsResponse = RootModel[List[VectorMapVersionsResponseEntry]]


class VectorMapRolePayload(BaseModel):
    user_id: str
    role: RoleEnum


class VectorMapRemoveRolePayload(BaseModel):
    user_id: str


class VectorMapUpdateRolesPayload(BaseModel):
    create_or_update: Optional[List[VectorMapRolePayload]] = None
    remove: Optional[List[VectorMapRemoveRolePayload]] = None


class VectorMapCreateResponse(BaseModel):
    id: uuid.UUID


class VectorMapVersionCreateResponse(BaseModel):
    version: int


class VectorMapVersionResponse(BaseModel):
    version: int
    submitted: NaiveDatetime
    created_by: str
    geojson: FeatureCollection


class EmptyResponse(BaseModel):
    pass
