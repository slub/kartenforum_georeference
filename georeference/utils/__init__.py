#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 06.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import os
import enum
from georeference.settings import PATH_GEOREF_ROOT, PATH_IMAGE_ROOT, PATH_MAPFILE_ROOT, PATH_TMS_ROOT, PATH_TMP_ROOT, \
    PATH_TMP_NEW_MAP_ROOT, PATH_THUMBNAIL_ROOT, PATH_ZOOMIFY_ROOT


class EnumMeta(enum.EnumMeta):
    def __contains__(cls, item):
        return item in [v.value for v in cls.__members__.values()]


def create_data_directories():
    """ This function makes sure, that all data directories used by the job function are existing. """
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
    """ Given a path, this functions make sure that the directory structure of
        the path is created if not exists.

    :param path: Path
    :type path: str
    """
    if not os.path.exists(path):
        os.makedirs(path)
