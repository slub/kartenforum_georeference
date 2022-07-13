#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 09.03.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import logging
import os
import shutil
from georeference.jobs.actions.create_geo_image import run_process_geo_image
from georeference.jobs.actions.create_geo_image_test import create_test_data
from .create_tms import run_process_tms

# Initialize the logger
LOGGER = logging.getLogger(__name__)

def test_runProcessTMS_success():
    """ The proper working of the action for processing tms directories. """
    try:
        # Perform the test
        testData = create_test_data('test_runProcessTMS_success')
        testTmsDir = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                           '../../georeference_tests/data_output/test_tms_%s.tif' % 'test_runProcessTMS_success')
        pathGeoImage = run_process_geo_image(
            testData['transformationObj'],
            testData['srcPath'],
            testData['trgPath'],
            logger=LOGGER
        )

        tmsDir = run_process_tms(
            testTmsDir,
            pathGeoImage,
            logger=LOGGER,
            map_scale=10000000,
        )

        assert True == os.path.exists(pathGeoImage)
    finally:
        if os.path.exists(pathGeoImage):
            os.remove(pathGeoImage)
        if os.path.exists(tmsDir):
            shutil.rmtree(tmsDir)

def test_runProcessTMS_force_success():
    """ The proper working of the action for processing tms directories. """
    try:
        # Initial create the process
        testData = create_test_data('test_runProcessTMS_force_success')
        testTmsDir = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                           '../../georeference_tests/data_output/test_tms_%s.tif' % 'test_runProcessTMS_force_success')
        pathGeoImage = run_process_geo_image(
            testData['transformationObj'],
            testData['srcPath'],
            testData['trgPath'],
            logger=LOGGER
        )

        subject = run_process_tms(
            testTmsDir,
            pathGeoImage,
            logger=LOGGER,
            map_scale=10000000,
        )
        firstModificationTime = os.path.getmtime(subject)

        # If "runProcessGeoImage" is run a second time and the image already exists, the functions
        # skips the processing. We can check this by comparing modifications times
        subject = run_process_tms(
            testTmsDir,
            pathGeoImage,
            logger=LOGGER,
            map_scale=10000000,
        )
        secondModificationTime = os.path.getmtime(subject)

        # If "runProcessGeoImage" is run a third time and the image already exists, we use the "force" parameter
        # to overwrite a existing image. We can check this by comparing modifications times
        subject = run_process_tms(
            testTmsDir,
            pathGeoImage,
            logger=LOGGER,
            map_scale=10000000,
            force=True
        )
        thirdModificationTime = os.path.getmtime(subject)

        assert firstModificationTime == secondModificationTime
        assert firstModificationTime != thirdModificationTime
    finally:
        if os.path.exists(pathGeoImage):
            os.remove(pathGeoImage)
        if os.path.exists(subject):
            shutil.rmtree(subject)