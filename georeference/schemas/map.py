#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by nicolas.looschen@pikobytes.de on 24.07.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package

from typing import Optional

from pydantic import BaseModel, NaiveDatetime


class MetadataPayload(BaseModel):
    description: Optional[str] = None
    license: Optional[str] = None
    link_thumb_small: Optional[str] = None
    link_thumb_mid: Optional[str] = None
    link_zoomify: Optional[str] = None
    measures: Optional[str] = None
    owner: Optional[str] = None
    permalink: Optional[str] = None
    ppn: Optional[str] = None
    technic: Optional[str] = None
    time_of_publication: Optional[NaiveDatetime] = None
    title: Optional[str] = None
    title_short: Optional[str] = None
    title_serie: Optional[str] = None
    type: Optional[str] = None


class MapResponse(BaseModel):
    description: str
    license: str
    title: str
    title_short: str
    time_of_publication: NaiveDatetime

    link_thumb_small: Optional[str]
    link_thumb_mid: Optional[str]
    link_zoomify: Optional[str]
    measures: Optional[str]
    owner: Optional[str]
    permalink: Optional[str]
    ppn: Optional[str]
    technic: Optional[str]
    title_serie: Optional[str]
    type: Optional[str]

    file_name: str
    map_id: str
    transformation_id: Optional[int] = None
    map_type: Optional[str]
    allow_download: bool
    map_scale: Optional[int]
