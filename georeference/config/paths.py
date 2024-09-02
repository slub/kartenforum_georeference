#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by nicolas.looschen@pikobytes.de on 10.07.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package

import os

from georeference.config.settings import get_settings

# Path to the data root directory
PATH_DATA_ROOT = get_settings().PATH_DATA_ROOT

#
# Paths to production directories
#

# Path to the image root directory
PATH_IMAGE_ROOT = os.path.join(PATH_DATA_ROOT, "./original")

# Path to the georef root directory
PATH_GEOREF_ROOT = os.path.join(PATH_DATA_ROOT, "./georef")

# Path to the mosaic root directory
PATH_MOSAIC_ROOT = os.path.join(PATH_DATA_ROOT, "./mosaic")

# Path to the template directory

# Path to the mapfile directory
PATH_MAPFILE_ROOT = os.path.join(PATH_DATA_ROOT, "./map_services")

# Path for the generated thumbnails
PATH_THUMBNAIL_ROOT = os.path.join(PATH_DATA_ROOT, "./thumbnails")

# Service tmp
PATH_TMP_ROOT = os.path.join(PATH_DATA_ROOT, "./tmp")

PATH_TMP_NEW_MAP_ROOT = os.path.join(PATH_DATA_ROOT, "./upload_tmp")

# Directory where the mapfiles for the validation process are saved
PATH_TMP_TRANSFORMATION_ROOT = os.path.join(PATH_DATA_ROOT, "./map_services_tmp")

# The data root is used by the mapfile an can be accessed from the PATH_TMP_TRANSFORMATION_ROOT. This is
# necessary for proper working with the docker setup
PATH_TMP_TRANSFORMATION_DATA_ROOT = "/mapdata/{}"

# Path to the tms root directoy
PATH_TMS_ROOT = os.path.join(PATH_DATA_ROOT, "./tms")

# Path to the zoomify files directory
PATH_ZOOMIFY_ROOT = os.path.join(PATH_DATA_ROOT, "./zoomify")


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
    create_path_if_not_exists(PATH_TMP_TRANSFORMATION_ROOT)


def create_path_if_not_exists(path):
    """Given a path, this functions make sure that the directory structure of
        the path is created if not exists.

    :param path: Path
    :type path: str
    """
    if not os.path.exists(path):
        os.makedirs(path)


TMP_DIR = "/tmp"
