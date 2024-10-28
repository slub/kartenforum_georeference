#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Created by nicolas.looschen@pikobytes.de on 14.08.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
from georeference.schemas.map_view import HistoricMapLayer, GeoJsonLayer
from georeference.tests.__test_data import (
    historic_map_layer_test_data,
    geojson_layer_test_data,
)


def test_historic_map_layer():
    # Test if the HistoricMapLayer can be created
    HistoricMapLayer(**historic_map_layer_test_data)

    assert True


def test_historic_geojson_layer():
    # Test if the GeoJsonLayer can be created
    GeoJsonLayer(**geojson_layer_test_data)
    assert True
