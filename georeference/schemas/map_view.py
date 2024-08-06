#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by nicolas.looschen@pikobytes.de on 22.07.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
from pydantic import BaseModel

from geojson_pydantic import FeatureCollection
from enum import Enum, EnumMeta
from typing import List, Optional, Union, Literal


class MapViewResponse(BaseModel):
    map_view_json: str


class CustomBasemap(BaseModel):
    id: str
    label: str
    urls: List[str]
    type: Optional[str]


class EnumOperationalLayerType(Enum, metaclass=EnumMeta):
    GEOJSON = "geojson"
    HISTORIC_MAP = "historic_map"


class OperationalLayerBase(BaseModel):
    id: str
    isVisible: bool
    opacity: float
    properties: dict


class GeoJsonLayer(OperationalLayerBase):
    type: Literal[EnumOperationalLayerType.GEOJSON.value]
    geojson: FeatureCollection


class HistoricMapLayer(OperationalLayerBase):
    type: Literal[EnumOperationalLayerType.HISTORIC_MAP.value]
    coordinates: List[float]


class ThreeDimensionalPoint(BaseModel):
    x: float
    y: float
    z: float


class TwoDimensionalPoint(BaseModel):
    x: float
    y: float


class ThreeDimensionalMapView(BaseModel):
    direction: ThreeDimensionalPoint
    position: ThreeDimensionalPoint
    up: ThreeDimensionalPoint
    right: ThreeDimensionalPoint


class TwoDimensionalMapView(BaseModel):
    center: List[float]
    resolution: float
    rotation: float
    zoom: float


class MapViewJsonBase(BaseModel):
    activeBasemapId: str
    customBasemaps: List[CustomBasemap]
    operationalLayers: List[Union[GeoJsonLayer, HistoricMapLayer]]


class TwoDimensionalMapViewJson(MapViewJsonBase):
    mapView: TwoDimensionalMapView
    is3dEnabled: Literal[False]
    searchOptions: Optional[str] = None


class ThreeDimensionalMapViewJson(MapViewJsonBase):
    mapView: ThreeDimensionalMapView
    is3dEnabled: Literal[True]
