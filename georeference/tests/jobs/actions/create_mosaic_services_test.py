#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 09.03.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import os
import shutil

from georeference.config.paths import PATH_TEST_OUTPUT_BASE
from georeference.tests.utils.mosaics_test import _create_test_data
from georeference.utils.mosaics import create_mosaic_dataset
from georeference.jobs.actions.create_mosaic_services import run_process_mosaic_services


def test_run_process_mosaic_services_success():
    try:
        tmp_dir = os.path.join(
            PATH_TEST_OUTPUT_BASE,
            "test_run_process_mosaic_services_success",
        )
        geo_dataset = _create_test_mosaic(tmp_dir)
        test_mapfile = os.path.join(
            tmp_dir, "test_run_process_mosaic_services_success.map"
        )

        # Create the mapfile
        test_subject = run_process_mosaic_services(
            path_mapfile=test_mapfile,
            path_geo_image=os.path.abspath(geo_dataset),
            layer_name="my_layername",
            layer_title="my_layertitle",
            force=True,
        )
        assert test_subject is not None
        assert os.path.exists(test_subject)
    finally:
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)


def _create_test_mosaic(tmp_dir):
    # Setup the test data. This also contains the process of creating test georeference images.
    test_data_georef_images = _create_test_data(tmp_dir)

    # Create the mosaic dataset
    return create_mosaic_dataset(
        dataset_name="test_run_process_mosaic_services_success",
        target_dir=tmp_dir,
        geo_images=test_data_georef_images,
        target_crs=3857,
    )
