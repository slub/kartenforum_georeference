#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by nicolas.looschen@pikobytes.de on 10.07.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package

import os

from loguru import logger

# For correct resolving of the paths we use derive the base_path of the file
# the base path is the application root, resolved in the following way:
#
# __file__ -> /georeference/config/paths.py
# os.path.dirname(os.path.realpath(__file__)) -> /georeference/config
# os.path.join(os.path.dirname(os.path.realpath(__file__)), "../") -> /georeference/
BASE_PATH = os.path.normpath(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), "../")
)

logger.debug(f"Resolved base path to: {BASE_PATH}")

# Path to the image root directory
PATH_IMAGE_ROOT = os.path.join(BASE_PATH, "./__test_data/data_input")

# Path to the georef root directory
PATH_GEOREF_ROOT = os.path.join(BASE_PATH, "../tmp/geo")

# Path to the mosaic root directory
PATH_MOSAIC_ROOT = os.path.join(BASE_PATH, "../tmp/mosaic")

# Path to the template directory

# Path to the mapfile directory
PATH_MAPFILE_ROOT = os.path.join(BASE_PATH, "../tmp/mapfiles")

# Path for the generated thumbnails
PATH_THUMBNAIL_ROOT = os.path.join(BASE_PATH, "../tmp/thumbnails")

# Service tmp
PATH_TMP_ROOT = os.path.join(BASE_PATH, "../tmp/tmp")

PATH_TMP_NEW_MAP_ROOT = os.path.join(BASE_PATH, "../tmp/imported_maps")

# Directory where the mapfiles for the validation process are saved
PATH_TMP_TRANSFORMATION_ROOT = os.path.join(BASE_PATH, "../tmp/tmp")

# The data root is used by the mapfile an can be accessed from the PATH_TMP_TRANSFORMATION_ROOT. This is
# necessary for proper working with the docker setup
PATH_TMP_TRANSFORMATION_DATA_ROOT = "/mapdata/{}"

# Path to the tms root directoy
PATH_TMS_ROOT = os.path.join(BASE_PATH, "../tmp/tms")

# Path to the test output directory
PATH_TEST_OUTPUT_BASE = os.path.join(BASE_PATH, "__test_data/data_output")

# Path to the test input directory
PATH_TEST_INPUT_BASE = os.path.join(BASE_PATH, "__test_data/data_input")

# Path to the zoomify files directory
PATH_ZOOMIFY_ROOT = os.path.join(BASE_PATH, "../tmp/zoomify")


def create_data_directories():
    """This function makes sure, that all data directories used by the job function are existing."""
    # Make sure that necessary directory exists
    create_path_if_not_exists(PATH_TMP_ROOT)
    create_path_if_not_exists(PATH_GEOREF_ROOT)
    create_path_if_not_exists(PATH_TMS_ROOT)
    create_path_if_not_exists(PATH_IMAGE_ROOT)
    create_path_if_not_exists(PATH_MAPFILE_ROOT)
    create_path_if_not_exists(PATH_ZOOMIFY_ROOT)
    create_path_if_not_exists(PATH_THUMBNAIL_ROOT)
    create_path_if_not_exists(PATH_TMP_NEW_MAP_ROOT)


def create_path_if_not_exists(path):
    """Given a path, this functions make sure that the directory structure of
        the path is created if not exists.

    :param path: Path
    :type path: str
    """
    if not os.path.exists(path):
        os.makedirs(path)


TMP_DIR = "/tmp"
