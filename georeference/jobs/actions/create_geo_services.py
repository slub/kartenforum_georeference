#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 09.03.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import os

from loguru import logger

from georeference.config.paths import (
    TEMPLATE_PUBLIC_WMS_URL,
    TEMPLATE_PUBLIC_WCS_URL,
    PATH_MAPFILE_TEMPLATES,
)
from georeference.utils.mapfile import write_mapfile
from georeference.utils.mapfile import parse_geo_tiff_metadata


def run_process_geo_services(
    path_mapfile,
    path_geo_image,
    mapfile_name,
    layer_name,
    layer_title,
    with_wcs=False,
    force=False,
):
    """This actions creates for a given geo image the mapfiles needed for publishing a WMS or WCS service.

    :param pathMapFile: Path to the mapfile
    :type pathMapFile: str
    :param path_geo_image: Path to the original geo image
    :type path_geo_image: str
    :param mapfile_name: Name of the mapfile
    :type mapfile_name: str
    :param layer_name: Name of the layer
    :type layer_name: str
    :param layer_title: Title of the layer
    :type layer_title: str
    :param with_wcs: Signals if the geo services should also have wcs functionality (Default: False)
    :type with_wcs: bool
    :param force: Signals if the function should overwrite an already existing mapfile (Default: False)
    :type force: bool
    :result: Path of the mapfile
    :rtype: str
    """
    if not os.path.exists(path_geo_image):
        logger.debug(
            f'Skip processing of map services for geo image "{path_geo_image}", because of missing geo image.'
        )
        return None

    if os.path.exists(path_mapfile) and force is False:
        logger.debug(
            f'Skip processing of map services for geo image "{path_geo_image}", because of an already existing mapfile. Use "force" parameter in case you want to overwrite it.'
        )
        return path_mapfile

    # Remove the mapfile if it exists
    if os.path.exists(path_mapfile):
        os.remove(path_mapfile)

    # Create the
    template_values = {
        **parse_geo_tiff_metadata(path_geo_image),
        **{
            "wmsUrl": TEMPLATE_PUBLIC_WMS_URL.format(mapfile_name),
            "wcsUrl": TEMPLATE_PUBLIC_WCS_URL.format(mapfile_name),
            "layerName": layer_name,
            "layerDataPath": path_geo_image,
            "layerTitle": layer_title,
        },
    }
    logger.debug(f"Use template values {template_values}")

    return write_mapfile(
        path_mapfile,
        os.path.join(
            PATH_MAPFILE_TEMPLATES,
            "./wms_wcs_static.map" if with_wcs is True else "./wms_static.map",
        ),
        template_values,
    )
