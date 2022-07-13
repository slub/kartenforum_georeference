#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 09.03.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import logging
import os
from .create_geo_image import run_process_geo_image
from .create_geo_image_test import create_test_data
from .create_geo_services import run_process_geo_services

# Initialize the logger
LOGGER = logging.getLogger(__name__)

def test_runProcessGeoServices_success():
    """ The proper working of the action for processing geo services for a geo images. """
    try:
        # Perform the test
        testData = create_test_data('test_runProcessGeoServices_success')
        testMapfile = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                           '../../georeference_tests/data_output/%s.map' % 'test_runProcessGeoServices_success')
        pathGeoImage = run_process_geo_image(
            testData['transformationObj'],
            testData['srcPath'],
            testData['trgPath'],
            logger=LOGGER
        )

        subject = run_process_geo_services(
            testMapfile,
            pathGeoImage,
            "test_runProcessGeoServices_success",
            "test_runProcessGeoServices_success",
            "Test",
            LOGGER,
            with_wcs = True
        )

        assert True == os.path.exists(subject)
    finally:
        if os.path.exists(pathGeoImage):
            os.remove(pathGeoImage)
        if os.path.exists(subject):
            os.remove(subject)