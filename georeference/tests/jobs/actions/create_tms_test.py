#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 09.03.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import os
import shutil

from georeference.config.paths import PATH_TEST_OUTPUT_BASE
from georeference.jobs.actions.create_geo_image import run_process_geo_image
from georeference.jobs.actions.create_tms import run_process_tms
from georeference.tests.jobs.actions.create_geo_image_test import create_test_data


def test_run_process_tms_success():
    """The proper working of the action for processing tms directories."""
    try:
        # Perform the test
        test_data = create_test_data("test_runProcessTMS_success")
        test_tms_dir = os.path.join(
            PATH_TEST_OUTPUT_BASE,
            "test_runProcessTMS_success.tif",
        )
        path_geo_image = run_process_geo_image(
            test_data["transformationObj"],
            test_data["srcPath"],
            test_data["trgPath"],
        )

        tms_dir = run_process_tms(
            test_tms_dir,
            path_geo_image,
        )

        assert os.path.exists(path_geo_image)
        assert os.path.exists(tms_dir)
    finally:
        if os.path.exists(path_geo_image):
            os.remove(path_geo_image)
        if os.path.exists(tms_dir):
            shutil.rmtree(tms_dir)


def test_run_process_tms_force_success():
    """The proper working of the action for processing tms directories."""
    try:
        # Initial create the process
        test_data = create_test_data("test_runProcessTMS_force_success")
        test_tms_dir = os.path.join(
            PATH_TEST_OUTPUT_BASE,
            "test_runProcessTMS_force_success.tif",
        )

        path_geo_image = run_process_geo_image(
            test_data["transformationObj"],
            test_data["srcPath"],
            test_data["trgPath"],
        )

        subject = run_process_tms(
            test_tms_dir,
            path_geo_image,
        )
        first_modification_time = os.path.getmtime(subject)

        # If "runProcessGeoImage" is run a second time and the image already exists, the functions
        # skips the processing. We can check this by comparing modifications times
        subject = run_process_tms(
            test_tms_dir,
            path_geo_image,
        )
        second_modification_time = os.path.getmtime(subject)

        # If "runProcessGeoImage" is run a third time and the image already exists, we use the "force" parameter
        # to overwrite a existing image. We can check this by comparing modifications times
        subject = run_process_tms(test_tms_dir, path_geo_image, force=True)
        third_modification_time = os.path.getmtime(subject)

        assert first_modification_time == second_modification_time
        assert first_modification_time != third_modification_time
    finally:
        if os.path.exists(path_geo_image):
            os.remove(path_geo_image)
        if os.path.exists(subject):
            shutil.rmtree(subject)


def test_run_process_tms_epsg_4314_bit_raster():
    try:
        test_data = create_test_data(
            "test_run_process_tms_epsg_4314_bit_raster", "../data_input_georef/df_dk_0010001_3077"
        )
        test_tms_dir = os.path.join(
            PATH_TEST_OUTPUT_BASE,
            "test_runProcessTMS_success.tif",
        )
        path_geo_image = test_data["srcPath"]

        tms_dir = run_process_tms(
            test_tms_dir,
            path_geo_image,
        )

        assert os.path.exists(path_geo_image)
        assert os.path.exists(tms_dir)
    finally:
        if os.path.exists(tms_dir):
            shutil.rmtree(tms_dir)
