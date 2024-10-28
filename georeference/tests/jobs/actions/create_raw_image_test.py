#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Created by jacob.mendt@pikobytes.de on 09.03.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import os

from georeference.config.paths import PATH_IMAGE_ROOT, PATH_TMP_ROOT
from georeference.jobs.actions.create_raw_image import (
    run_process_raw_image,
    _get_pixel_data_type,
)


def test_run_process_raw_image_success_image_1():
    """The proper working of the action for processing raw images."""
    try:
        src_path = os.path.join(
            PATH_TMP_ROOT,
            "df_dk_0000680_16_byte.tif",
        )
        trg_path = os.path.join(
            PATH_TMP_ROOT,
            "df_dk_0000680.tif",
        )
        subject = run_process_raw_image(src_path, trg_path, force=True)

        assert os.path.exists(subject)
        assert _get_pixel_data_type(subject) == "Byte"

    finally:
        if os.path.exists(subject):
            os.remove(subject)


def test_run_process_raw_image_success_image_2():
    """The proper working of the action for processing raw images."""
    try:
        src_path = os.path.join(
            PATH_IMAGE_ROOT,
            "dd_stad_0000007_0015.tif",
        )
        trg_path = os.path.join(
            PATH_TMP_ROOT,
            "dd_stad_0000007_0015.tif",
        )
        subject = run_process_raw_image(src_path, trg_path, force=True)

        assert os.path.exists(subject)
    finally:
        if os.path.exists(subject):
            os.remove(subject)
