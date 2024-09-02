#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by nicolas.looschen@pikobytes.de on 26.07.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
from enum import Enum
from typing import List, Any, Dict, Optional, Union

from geojson_pydantic import Polygon
from pydantic import NaiveDatetime, BaseModel, conlist


class EnumTransformationAlgorithms(str, Enum):
    AFFINE = "affine"
    POLYNOM = "polynom"
    TPS = "tps"


class GCP(BaseModel):
    source: conlist(float, min_length=2, max_length=2)
    target: conlist(float, min_length=2, max_length=2)


class TransformationParams(BaseModel):
    algorithm: EnumTransformationAlgorithms
    gcps: conlist(GCP, min_length=3)


class TransformationMetadata(BaseModel):
    time_of_publication: NaiveDatetime
    title: str
    title_short: str


class TransformationPolygon(Polygon):
    crs: Dict[str, Any]


class TransformationResponse(BaseModel):
    is_active: bool
    transformation_id: int
    clip: TransformationPolygon
    params: Dict
    submitted: NaiveDatetime
    overwrites: Optional[int]
    user_id: str
    map_id: str
    validation: str
    metadata: TransformationMetadata


class TransformationResponseAdditionalProperties(BaseModel):
    active_transformation_id: Optional[int]
    default_crs: str
    extent: Optional[Polygon]
    metadata: TransformationMetadata
    pending_jobs: bool


class TransformationResponseWithoutAdditionalProperties(BaseModel):
    transformations: List[TransformationResponse]


class TransformationResponseWithAdditionalProperties(BaseModel):
    transformations: List[TransformationResponse]
    additional_properties: TransformationResponseAdditionalProperties


class TransformationIdOnlyPayload(BaseModel):
    transformation_id: int


class TransformationPayloadComplete(BaseModel):
    clip: Optional[Polygon] = None
    params: TransformationParams
    overwrites: int
    map_id: str


TransformationPayload = Union[
    TransformationIdOnlyPayload, TransformationPayloadComplete
]
