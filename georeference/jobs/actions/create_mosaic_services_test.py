#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 09.03.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import logging
import os
import shutil
from georeference.utils.mosaics import create_mosaic_dataset
from georeference.utils.mosaics_test import _create_test_data
from .create_mosaic_services import run_process_mosaic_services

# Initialize the logger
LOGGER = logging.getLogger(__name__)

def test_run_process_mosaic_services_success():
    try:
        tmp_dir = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            '../../__test_data/data_output',
            'test_run_process_mosaic_services_success'
        )
        geo_dataset = _create_test_mosaic(tmp_dir)
        test_mapfile = os.path.join(
            tmp_dir,
            'test_run_process_mosaic_services_success.map'
        )

        # Create the mapfile
        test_subject = run_process_mosaic_services(
            path_mapfile=test_mapfile,
            path_geo_image=os.path.abspath(geo_dataset),
            layer_name='my_layername',
            layer_title='my_layertitle',
            logger=LOGGER,
            force=True
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
        dataset_name='test_run_process_mosaic_services_success',
        target_dir=tmp_dir,
        geo_images=test_data_georef_images,
        target_crs=3857,
        logger=LOGGER
    )