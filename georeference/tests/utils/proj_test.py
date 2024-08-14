#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

# Created by jacob.mendt@pikobytes.de on 03.05.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import pytest
from pyproj.exceptions import CRSError

from georeference.jobs.actions.create_geo_image import run_process_geo_image
from georeference.models.raw_map import RawMap
from georeference.tests.jobs.actions.create_geo_image_test import create_test_data
from georeference.utils.proj import (
    get_crs_for_transformation_params,
    transform_to_params_to_target_crs,
    get_epsg_and_bbox_for_tif,
)


def _get_transformation_params():
    return {
        "source": "pixel",
        "target": "EPSG:4314",
        "algorithm": "tps",
        "gcps": [
            {"source": [6700, 998], "target": [14.809598142072, 50.897193140898]},
            {"source": [6656, 944], "target": [14.808447338463, 50.898010359738]},
            {"source": [6687, 1160], "target": [14.809553411787, 50.894672081543]},
            {"source": [6687, 1160], "target": [14.809553411787, 50.894672081543]},
        ],
    }


def test_get_crs_from_request_params_use_passed_crs(readonly_db_session):
    raw_map = RawMap.by_id(10001556, readonly_db_session)
    subject = get_crs_for_transformation_params(
        _get_transformation_params(), raw_map, target_crs="EPSG:4326"
    )
    assert subject == "EPSG:4326"


def test_get_crs_for_params_use_passed_crs_successful_fails(readonly_db_session):
    raw_map = RawMap.by_id(10001556, readonly_db_session)
    with pytest.raises(CRSError):
        get_crs_for_transformation_params(
            _get_transformation_params(), raw_map, target_crs="EPSG:NOTEXISTING"
        )


def test_get_crs_for_params_use_default_crs(readonly_db_session):
    raw_map = RawMap.by_id(10001556, readonly_db_session)
    subject = get_crs_for_transformation_params(_get_transformation_params(), raw_map)
    assert subject == "EPSG:4314"


def test_get_crs_for_params_guess_crs_projected(readonly_db_session):
    raw_map = RawMap.by_id(10001556, readonly_db_session)
    raw_map.default_crs = None
    subject = get_crs_for_transformation_params(_get_transformation_params(), raw_map)
    assert subject == "EPSG:32633"

    # Clean up test
    readonly_db_session.rollback()


def test_get_crs_for_params_guess_crs_geographic(readonly_db_session):
    raw_map = RawMap.by_id(10001556, readonly_db_session)
    raw_map.default_crs = None
    transformation_params = {
        "source": "pixel",
        "target": "EPSG:4314",
        "algorithm": "tps",
        "gcps": [
            {"source": [6700, 998], "target": [12.809598142072, 48.897193140898]},
            {"source": [6656, 944], "target": [14.808447338463, 50.898010359738]},
            {"source": [6687, 1160], "target": [14.809553411787, 50.894672081543]},
            {"source": [6687, 1160], "target": [15.809553411787, 51.894672081543]},
        ],
    }
    subject = get_crs_for_transformation_params(transformation_params, raw_map)
    assert subject == "EPSG:4326"

    # Clean up test
    readonly_db_session.rollback()


def test_transform_to_params_to_target_crs_4314(readonly_db_session):
    target_crs = "EPSG:4314"
    params = _get_transformation_params()
    subject = transform_to_params_to_target_crs(params, target_crs)
    assert subject["target"] == target_crs
    assert round(subject["gcps"][0]["target"][0], 6) == round(
        subject["gcps"][0]["target"][0], 6
    )
    assert round(subject["gcps"][0]["target"][1], 6) == round(
        subject["gcps"][0]["target"][1], 6
    )


def test_transform_to_params_to_target_crs_4326(readonly_db_session):
    target_crs = "EPSG:4326"
    params = _get_transformation_params()
    subject = transform_to_params_to_target_crs(params, target_crs)
    assert round(subject["gcps"][0]["target"][0], 6) == round(14.807667264759935, 6)
    assert round(subject["gcps"][0]["target"][1], 6) == round(50.89598748103341, 6)


def test_transform_to_params_to_target_crs_32633(readonly_db_session):
    target_crs = "EPSG:32633"
    params = _get_transformation_params()
    subject = transform_to_params_to_target_crs(params, target_crs)
    assert subject["target"] == target_crs
    assert round(subject["gcps"][0]["target"][0], 6) == round(486473.94242257654, 6)
    assert round(subject["gcps"][0]["target"][1], 6) == round(5638276.023935849, 6)


def test_transform_to_params_to_target_crs_4314_to_4326(readonly_db_session):
    target_crs = "EPSG:4326"
    params = {
        "source": "pixel",
        "target": "EPSG:4314",
        "algorithm": "tps",
        "gcps": [
            {"source": [5549, 5002], "target": [13.740504826908, 51.049994444427]},
            {"source": [7801, 4766], "target": [13.764599582931, 51.0390818907]},
        ],
    }
    subject = transform_to_params_to_target_crs(params, target_crs)
    assert round(subject["gcps"][1]["target"][0], 6) == round(13.762824893617337, 6)
    assert round(subject["gcps"][1]["target"][1], 6) == round(51.03784991326232, 6)


def test_transform_to_params_to_target_crs_4326_to_32633(readonly_db_session):
    target_crs = "EPSG:32633"
    params = {
        "source": "pixel",
        "target": "EPSG:4326",
        "algorithm": "tps",
        "gcps": [
            {"source": [5549, 5002], "target": [13.762824893617337, 51.03784991326232]},
        ],
    }
    subject = transform_to_params_to_target_crs(params, target_crs)
    assert round(subject["gcps"][0]["target"][0], 6) == round(413259.97307796835, 6)
    assert round(subject["gcps"][0]["target"][1], 6) == round(5654762.176309784, 6)


def test_get_epsg_and_bbox_for_tif():
    try:
        # Initial create the process
        test_data = create_test_data("test_runProcessTMS_force_success")

        path_geo_image = run_process_geo_image(
            test_data["transformationObj"],
            test_data["srcPath"],
            test_data["trgPath"],
        )

        epsg, bbox = get_epsg_and_bbox_for_tif(path_geo_image)

        assert epsg == 4314
        assert bbox == [14.6431112, 50.7671757, 14.8489897, 50.9130298]

    finally:
        if os.path.exists(path_geo_image):
            os.remove(path_geo_image)


def test_get_epsg_and_bbox_for_tif_3857():
    try:
        # Initial create the process
        test_data = create_test_data(
            "test_runProcessTMS_force_success", target_epsg="EPSG:3857"
        )

        path_geo_image = run_process_geo_image(
            test_data["transformationObj"],
            test_data["srcPath"],
            test_data["trgPath"],
        )

        epsg, bbox = get_epsg_and_bbox_for_tif(path_geo_image)

        assert epsg == 3857
        assert bbox == [14.6431112, 50.7671757, 14.8489897, 50.9130298]

    finally:
        if os.path.exists(path_geo_image):
            os.remove(path_geo_image)
