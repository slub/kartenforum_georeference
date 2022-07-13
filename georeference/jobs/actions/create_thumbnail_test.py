#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 09.03.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import logging
import os
from .create_raw_image import run_process_raw_image
from .create_thumbnail import run_process_thumbnail

# Initialize the logger
LOGGER = logging.getLogger(__name__)

def test_run_create_process_thumbnail_success_image_1():
    """ The proper working of the action for processing a thumbnail with the size 400x400 """
    try:
        srcPath = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               '../../__test_data/data_input/test-ak.jpg')
        trgPath = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               '../../__test_data/data_output/test-ak_400x400.jpg')
        subject = run_process_thumbnail(
            srcPath,
            trgPath,
            logger=LOGGER,
            width=400,
            height=400,
            force=True
        )

        assert True == os.path.exists(subject)
    finally:
        if os.path.exists(subject):
            os.remove(subject)


def test_run_create_process_thumbnail_success_image_2():
    """ The proper working of the action for processing a thumbnail with the size 120x120 """
    try:
        srcPath = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               '../../__test_data/data_input/dd_stad_0000007_0015.tif')
        trgPath = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               '../../__test_data/data_output/dd_stad_0000007_0015_120x120.jpg')
        subject = run_process_thumbnail(
            srcPath,
            trgPath,
            logger=LOGGER,
            width=None,
            height=120,
            force=True
        )

        assert True == os.path.exists(subject)
    finally:
        if os.path.exists(subject):
            os.remove(subject)

def test_run_create_process_thumbnail_success_image_3():
    """ The proper working of the action for processing a thumbnail with the size 120x120, but it uses a preprocess raw image."""
    try:
        srcPath = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               '../../__test_data/data_input/dd_stad_0000007_0015.tif')
        tmpPath = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               '../../__test_data/data_output/dd_stad_0000007_0015.tif')
        trgPath = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               '../../__test_data/data_output/dd_stad_0000007_0015_120x120.jpg')

        subject_1 = run_process_raw_image(
            srcPath,
            tmpPath,
            logger=LOGGER,
            force=True
        )

        subject_2 = run_process_thumbnail(
            tmpPath,
            trgPath,
            logger=LOGGER,
            width=None,
            height=120,
            force=True
        )

        assert True == os.path.exists(subject_1)
    finally:
        if os.path.exists(subject_1):
            os.remove(subject_1)
        if os.path.exists(subject_2):
            os.remove(subject_2)