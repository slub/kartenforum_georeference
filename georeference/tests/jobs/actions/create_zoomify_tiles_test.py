#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 09.03.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import os
import shutil

from georeference.config.paths import PATH_TMP_ROOT, PATH_IMAGE_ROOT
from georeference.jobs.actions.create_zoomify_tiles import run_process_zoomify_tiles


def test_run_process_zoomify_tiles_success():
    """The proper working of the action for processing zoomify-tiles raw images."""
    try:
        src_path = os.path.join(
            PATH_IMAGE_ROOT,
            "dd_stad_0000007_0015.tif",
        )
        trg_path = os.path.join(
            PATH_TMP_ROOT,
            "dd_stad_0000007_0015",
        )
        subject = run_process_zoomify_tiles(src_path, trg_path, force=True)

        assert os.path.exists(subject)
    finally:
        if os.path.exists(subject):
            shutil.rmtree(subject)
