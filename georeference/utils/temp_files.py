#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import uuid

from loguru import logger

from georeference.config.paths import (
    PATH_TMP_TRANSFORMATION_ROOT,
    PATH_TMP_ROOT,
    TEMPLATE_TRANSFORMATION_WMS_URL,
    PATH_MAPFILE_TEMPLATES,
    PATH_TMP_TRANSFORMATION_DATA_ROOT,
)
from georeference.utils.georeference import rectify_image
from georeference.utils.mapfile import write_mapfile
from georeference.utils.parser import to_gdal_gcps


# Created by nicolas.looschen@pikobytes.de on 28.07.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package


def _create_temporary_georeference_image(
    trg_file_name, src_file, transformation_params, clip_geometry
):
    """Function creates a temporary georeference image.

    :param trg_file_name: Name of the target file
    :type trg_file_name: str
    :param src_file: Path to the source file
    :type src_file: str
    :param transformation_params: Transformation params
    :type transformation_params: dict
    :param clip_geometry: Clip geometry in GeoJSON syntax
    :type clip_geometry: dict
    :result: Path to the temporary georeference file
    :rtype: str
    """
    logger.debug("Create temporary validation result ...")
    gdal_gcps = to_gdal_gcps(transformation_params["gcps"])
    trg_file = os.path.abspath(
        os.path.join(PATH_TMP_TRANSFORMATION_ROOT, trg_file_name)
    )

    if os.path.exists(src_file) == False:
        logger.error("Could not found source file %s ..." % src_file)
        raise

    logger.debug("Start processing source file %s ..." % src_file)

    # Create a rectify image
    return rectify_image(
        src_file,
        trg_file,
        transformation_params["algorithm"],
        gdal_gcps,
        transformation_params["target"].lower(),
        PATH_TMP_ROOT,
        None if clip_geometry is None else clip_geometry,
    )


def _create_temporary_mapfile(raw_map_obj, trg_file_name, transformation_params):
    """Creates a temporary mapfile.

    :param raw_map_obj: RawMap
    :type raw_map_obj: georeference.models.raw_maps.RawMap
    :param trg_file_name: Name of the target file
    :type trg_file_name: str
    :param transformation_params: Transformation params
    :type transformation_params: dict
    :result: Link to the wms service
    :rtype: str
    """
    logger.debug("Create temporary map service ...")
    logger.debug(transformation_params)
    mapfile_name = f'wms_{str(uuid.uuid4()).replace("-", "_")}'
    wms_url = TEMPLATE_TRANSFORMATION_WMS_URL.format(mapfile_name)
    write_mapfile(
        os.path.join(PATH_TMP_TRANSFORMATION_ROOT, f"{mapfile_name}.map"),
        os.path.join(PATH_MAPFILE_TEMPLATES, "./wms_dynamic.map"),
        {
            "wmsAbstract": f"This wms is a temporary wms for {raw_map_obj.file_name}",
            "wmsUrl": wms_url,
            "layerName": raw_map_obj.file_name,
            "layerDataPath": PATH_TMP_TRANSFORMATION_DATA_ROOT.format(trg_file_name),
            "layerProjection": transformation_params["target"].lower(),
        },
    )
    return wms_url
