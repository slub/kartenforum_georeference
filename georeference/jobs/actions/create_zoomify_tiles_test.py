#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 09.03.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import logging
import os
import shutil
from .create_zoomify_tiles import run_process_zoomify_tiles

# Initialize the logger
LOGGER = logging.getLogger(__name__)

def test_runProcessZoomifyTiles_success():
    """ The proper working of the action for processing zoomify-tiles raw images. """
    try:
        srcPath = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                           '../../__test_data/data_input/dd_stad_0000007_0015.tif')
        trgPath = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                           '../../__test_data/data_output/dd_stad_0000007_0015')
        subject = run_process_zoomify_tiles(
            srcPath,
            trgPath,
            logger=LOGGER,
            force=True
        )

        assert True == os.path.exists(subject)
    finally:
        if os.path.exists(subject):
            shutil.rmtree(subject)