#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 09.03.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import logging
import os
from .create_raw_image import run_process_raw_image

# Initialize the logger
LOGGER = logging.getLogger(__name__)

def test_runProcessRawImage_success_image_1():
    """ The proper working of the action for processing raw images. """
    try:
        srcPath = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                           '../../__test_data/data_input/df_dk_0000680.tif')
        trgPath = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                           '../../__test_data/data_output/df_dk_0000680.tif')
        subject = run_process_raw_image(
            srcPath,
            trgPath,
            logger=LOGGER,
            force=True
        )

        assert True == os.path.exists(subject)
    finally:
        if os.path.exists(subject):
            os.remove(subject)

def test_runProcessRawImage_success_image_2():
    """ The proper working of the action for processing raw images. """
    try:
        srcPath = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                           '../../__test_data/data_input/dd_stad_0000007_0015.tif')
        trgPath = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                           '../../__test_data/data_output/dd_stad_0000007_0015.tif')
        subject = run_process_raw_image(
            srcPath,
            trgPath,
            logger=LOGGER,
            force=True
        )

        assert True == os.path.exists(subject)
    finally:
        if os.path.exists(subject):
            os.remove(subject)
