#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 09.03.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import os

from georeference.jobs.actions.create_geo_image import run_process_geo_image
from georeference.jobs.actions.create_geo_services import run_process_geo_services
from .create_geo_image_test import create_test_data


def test_run_process_geo_services_success():
    """The proper working of the action for processing geo services for a geo images."""
    try:
        # Perform the test
        test_data = create_test_data("test_runProcessGeoServices_success")
        test_mapfile = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "../../georeference_tests/data_output/%s.map"
            % "test_runProcessGeoServices_success",
        )
        path_geo_image = run_process_geo_image(
            test_data["transformationObj"],
            test_data["srcPath"],
            test_data["trgPath"],
        )

        subject = run_process_geo_services(
            test_mapfile,
            path_geo_image,
            "test_runProcessGeoServices_success",
            "test_runProcessGeoServices_success",
            "Test",
            with_wcs=True,
        )

        assert subject is not None
        assert os.path.exists(subject)
    finally:
        if os.path.exists(path_geo_image):
            os.remove(path_geo_image)
        if os.path.exists(subject):
            os.remove(subject)
