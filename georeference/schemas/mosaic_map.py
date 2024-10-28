#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Created by nicolas.looschen@pikobytes.de on 25.07.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package

from typing import Optional, List

from pydantic import BaseModel, NaiveDatetime, RootModel, Field

from georeference.config.constants import regex_link, regex_alphanumeric_string
from georeference.models.mosaic_map import MosaicMap
from georeference.utils.parser import to_public_map_id, to_public_mosaic_map_id


class MosaicMapPayload(BaseModel):
    name: str = Field(pattern=regex_alphanumeric_string)
    raw_map_ids: list[str]
    title: str
    title_short: str
    description: str
    time_of_publication: NaiveDatetime
    link_thumb: str = Field(pattern=regex_link)
    map_scale: int


class MosaicMapResponse(BaseModel):
    id: str
    name: str
    raw_map_ids: list[str]
    title: str
    title_short: str
    description: str
    time_of_publication: NaiveDatetime
    link_thumb: str
    map_scale: int
    last_change: NaiveDatetime
    last_service_update: Optional[NaiveDatetime]
    last_overview_update: Optional[NaiveDatetime]

    @classmethod
    def from_model(cls, mosaic_map: MosaicMap):
        id = to_public_mosaic_map_id(mosaic_map.id)
        raw_map_ids = list(map(lambda x: to_public_map_id(x), mosaic_map.raw_map_ids))

        return cls(
            id=id,
            name=mosaic_map.name,
            raw_map_ids=raw_map_ids,
            title=mosaic_map.title,
            title_short=mosaic_map.title_short,
            description=mosaic_map.description,
            time_of_publication=mosaic_map.time_of_publication,
            link_thumb=mosaic_map.link_thumb,
            map_scale=mosaic_map.map_scale,
            last_change=mosaic_map.last_change,
            last_service_update=mosaic_map.last_service_update,
            last_overview_update=mosaic_map.last_overview_update,
        )


MosaicMapsResponse = RootModel[List[MosaicMapResponse]]
