#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 09.03.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import os
import shutil
from georeference.settings import GLOBAL_TMS_PROCESSES
from georeference.utils.tms import calculate_compressed_tms

def run_process_tms(path_tms_dir, path_geo_image, logger, map_scale, force = False):
    """ This actions generate a Tile Map Service (TMS) for a given geo services. It therefore heavily relies on the
        gdal utility tool, gdal2tiles. See also https://gdal.org/programs/gdal2tiles.html

    :param path_tms_dir: Root path of the tms cache directory
    :type path_tms_dir: str
    :param path_geo_image: Path of the geo image
    :type path_geo_image: str
    :param logger: Logger
    :type logger: logging.Logger
    :param map_scale: Scale of the map. Is necessary for guessing the correct number of zoom levels supported by the tms.
    :type map_scale: int
    :param force: Signals if the function should overwrite an already existing tms cache (Default: False)
    :type force: bool
    :result: Path of the tms cache directory
    :rtype: str
    """
    if not os.path.exists(path_geo_image):
        logger.debug('Skip processing of tms for geo image "%s", because of missing geo image.' % path_geo_image)
        return None

    if os.path.exists(path_tms_dir) and force == False:
        logger.debug('Skip processing of tms for geo image "%s", because of an already existing tms. Use "force" parameter in case you want to overwrite it.' % path_tms_dir)
        return path_tms_dir

    # In case a tms directory exist clean it
    if os.path.exists(path_tms_dir):
        shutil.rmtree(path_tms_dir)

    logger.debug('Process tile map service (TMS) ...')
    calculate_compressed_tms(
        path_geo_image,
        path_tms_dir,
        logger,
        GLOBAL_TMS_PROCESSES,
        map_scale
    )

    return path_tms_dir
