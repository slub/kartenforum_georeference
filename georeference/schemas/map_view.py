#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by nicolas.looschen@pikobytes.de on 22.07.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
from enum import Enum, EnumMeta
from typing import List, Optional, Union, Literal

from geojson_pydantic import FeatureCollection, Polygon
from pydantic import BaseModel, conlist


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
    geometry: Optional[Polygon] = None


class GeoJsonLayer(OperationalLayerBase):
    type: Literal[EnumOperationalLayerType.GEOJSON.value]
    geojson: FeatureCollection


class HistoricMapLayer(OperationalLayerBase):
    type: Literal[EnumOperationalLayerType.HISTORIC_MAP.value]


class CameraOptions(BaseModel):
    bearing: float
    center: conlist(float, min_length=2, max_length=2)
    pitch: float
    zoom: float


# New Mapview does not have distinction between 2d and 3d view mode in camera options
class MapViewJsonBase(BaseModel):
    activeBasemapId: str
    customBasemaps: Optional[List[CustomBasemap]] = []
    operationalLayers: List[Union[GeoJsonLayer, HistoricMapLayer]]
    is3dEnabled: Optional[bool]
    cameraOptions: CameraOptions


class MapViewPayload(BaseModel):
    map_view_json: Union[MapViewJsonBase]


class LegacyMapViewJsonBase(BaseModel):
    activeBasemapId: str
    customBasemaps: Optional[List[CustomBasemap]] = []
    operationalLayers: List[Union[GeoJsonLayer, HistoricMapLayer]]


# Deprecated, only here for informational purposes
class LegacyThreeDimensionalPoint(BaseModel):
    x: float
    y: float
    z: float


class LegacyThreeDimensionalMapView(BaseModel):
    direction: LegacyThreeDimensionalPoint
    position: LegacyThreeDimensionalPoint
    up: LegacyThreeDimensionalPoint
    right: LegacyThreeDimensionalPoint


class LegacyTwoDimensionalMapView(BaseModel):
    center: List[float]
    resolution: float
    rotation: float
    zoom: float


class LegacyTwoDimensionalMapViewJson(LegacyMapViewJsonBase):
    mapView: LegacyTwoDimensionalMapView
    is3dEnabled: Optional[Literal[False]] = False


class LegacyThreeDimensionalMapViewJson(LegacyMapViewJsonBase):
    mapView: LegacyThreeDimensionalMapView
    is3dEnabled: Literal[True]
