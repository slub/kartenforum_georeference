#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 09.03.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import os

from georeference.config.paths import PATH_IMAGE_ROOT, PATH_TMP_ROOT
from georeference.jobs.actions.create_raw_image import run_process_raw_image
from georeference.jobs.actions.create_thumbnail import run_process_thumbnail


# Initialize the logger


def test_run_create_process_thumbnail_success_image_1():
    """The proper working of the action for processing a thumbnail with the size 400x400"""
    try:
        src_path = os.path.join(
            PATH_IMAGE_ROOT,
            "test-ak.jpg",
        )
        trg_path = os.path.join(
            PATH_TMP_ROOT,
            "test-ak_400x400.jpg",
        )
        subject = run_process_thumbnail(
            src_path, trg_path, width=400, height=400, force=True
        )

        assert os.path.exists(subject)
    finally:
        if os.path.exists(subject):
            os.remove(subject)


def test_run_create_process_thumbnail_success_image_2():
    """The proper working of the action for processing a thumbnail with the size 120x120"""
    try:
        src_path = os.path.join(
            PATH_IMAGE_ROOT,
            "dd_stad_0000007_0015.tif",
        )
        trg_path = os.path.join(
            PATH_TMP_ROOT,
            "dd_stad_0000007_0015_120x120.jpg",
        )
        subject = run_process_thumbnail(
            src_path, trg_path, width=None, height=120, force=True
        )

        assert os.path.exists(subject)
    finally:
        if os.path.exists(subject):
            os.remove(subject)


def test_run_create_process_thumbnail_success_image_3():
    """The proper working of the action for processing a thumbnail with the size 120x120, but it uses a preprocess raw image."""
    subject_1 = ""
    subject_2 = ""
    try:
        src_path = os.path.join(
            PATH_IMAGE_ROOT,
            "dd_stad_0000007_0015.tif",
        )
        tmp_path = os.path.join(
            PATH_TMP_ROOT,
            "dd_stad_0000007_0015.tif",
        )
        trg_path = os.path.join(
            PATH_TMP_ROOT,
            "dd_stad_0000007_0015_120x120.jpg",
        )

        subject_1 = run_process_raw_image(src_path, tmp_path, force=True)

        subject_2 = run_process_thumbnail(
            tmp_path, trg_path, width=None, height=120, force=True
        )

        assert os.path.exists(subject_1)
    finally:
        if os.path.exists(subject_1):
            os.remove(subject_1)
        if os.path.exists(subject_2):
            os.remove(subject_2)
