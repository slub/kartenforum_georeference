#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Created by jacob.mendt@pikobytes.de on 09.03.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import os
import shutil
from pathlib import Path

from loguru import logger

from georeference.config.constants import EPSG_4314_BOUNDS
from georeference.config.paths import TMP_DIR
from georeference.config.settings import get_settings
from georeference.utils.georeference import reproject_image_from_4314_15869_to_3857
from georeference.utils.proj import get_epsg_and_bbox_for_tif
from georeference.utils.tms import calculate_compressed_tms
from georeference.utils.utils import bbox_position


def run_process_tms(path_tms_dir, path_geo_image, force=False):
    """This actions generate a Tile Map Service (TMS) for a given geo services. It therefore heavily relies on the
        gdal utility tool, gdal2tiles. See also https://gdal.org/programs/gdal2tiles.html

    :param path_tms_dir: Root path of the tms cache directory
    :type path_tms_dir: str
    :param path_geo_image: Path of the geo image
    :type path_geo_image: str
    :param force: Signals if the function should overwrite an already existing tms cache (Default: False)
    :type force: bool
    :result: Path of the tms cache directory
    :rtype: str
    """

    tmp_geo_file = None
    if not os.path.exists(path_geo_image):
        logger.debug(
            'Skip processing of tms for geo image "%s", because of missing geo image.'
            % path_geo_image
        )
        return None

    if os.path.exists(path_tms_dir) and force is False:
        logger.debug(
            'Skip processing of tms for geo image "%s", because of an already existing tms. Use "force" parameter in case you want to overwrite it.'
            % path_tms_dir
        )
        return path_tms_dir

    # In case a tms directory exist clean it
    if os.path.exists(path_tms_dir):
        shutil.rmtree(path_tms_dir)

    logger.debug("Process tile map service (TMS) ...")
    settings = get_settings()

    try:
        logger.debug(f"Detecting srs and bounding box for {path_geo_image}")
        srs, bounds = get_epsg_and_bbox_for_tif(path_geo_image)

        logger.debug(f"Determined following srs for {path_geo_image}: {srs}")
        if srs == 4314:
            logger.debug(
                "Detected EPSG 4314. Checking if the bounding box is contained in the EPSG 4314 bounding box."
            )
            is_contained, direction = bbox_position(
                bounds,
                EPSG_4314_BOUNDS,
            )
            logger.debug(f"Is contained: {is_contained}, direction: {direction}")

            # 3. If that is the case reproject the image to 3857 and use it as base for the tms calculation
            if not is_contained:
                if direction != "east":
                    raise Exception(
                        "The bounding box is not contained in the EPSG 4314 bounding box and not to the east of it."
                    )
                else:
                    logger.warning(
                        "The bounding box is not contained in the EPSG 4314 bounding box but to the east of it."
                    )
                    logger.warning("Reprojecting the image to EPSG 3857.")

                    file_name = Path(path_geo_image).name
                    tmp_geo_file = os.path.join(TMP_DIR, file_name)
                    path_geo_image = reproject_image_from_4314_15869_to_3857(
                        path_geo_image, tmp_geo_file
                    )

        logger.debug(f"Calculate compressed tms for {path_geo_image}")
        calculate_compressed_tms(
            path_geo_image,
            path_tms_dir,
            settings.GLOBAL_TMS_PROCESSES,
        )

        return path_tms_dir
    except Exception as e:
        logger.error(e)
        raise
    finally:
        # Remove the reprojected file afterward
        if tmp_geo_file is not None and os.path.exists(tmp_geo_file):
            os.remove(tmp_geo_file)
