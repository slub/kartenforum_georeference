#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 09.03.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import os

from georeference.config.paths import PATH_TEST_INPUT_BASE, PATH_TEST_OUTPUT_BASE
from georeference.jobs.actions.create_raw_image import run_process_raw_image


def test_run_process_raw_image_success_image_1():
    """The proper working of the action for processing raw images."""
    try:
        src_path = os.path.join(
            PATH_TEST_INPUT_BASE,
            "df_dk_0000680.tif",
        )
        trg_path = os.path.join(
            PATH_TEST_OUTPUT_BASE,
            "df_dk_0000680.tif",
        )
        subject = run_process_raw_image(src_path, trg_path, force=True)

        assert os.path.exists(subject)
    finally:
        if os.path.exists(subject):
            os.remove(subject)


def test_run_process_raw_image_success_image_2():
    """The proper working of the action for processing raw images."""
    try:
        src_path = os.path.join(
            PATH_TEST_INPUT_BASE,
            "dd_stad_0000007_0015.tif",
        )
        trg_path = os.path.join(
            PATH_TEST_OUTPUT_BASE,
            "dd_stad_0000007_0015.tif",
        )
        subject = run_process_raw_image(src_path, trg_path, force=True)

        assert os.path.exists(subject)
    finally:
        if os.path.exists(subject):
            os.remove(subject)
