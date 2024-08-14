#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 09.03.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import os

from loguru import logger

from georeference.config.paths import PATH_TMP_ROOT
from georeference.utils.georeference import rectify_image_with_clip_and_overviews
from georeference.utils.parser import to_gdal_gcps
from georeference.utils.proj import transform_to_params_to_target_crs


def run_process_geo_image(
    transformation_obj, path_raw_image, path_geo_image, force=False, clip=None
):
    """This actions generates a persistent geo image for a given transformation object and a raw image.

    :param transformation_obj: Transformation
    :type transformation_obj: georeference.models.transformations.Transformation
    :param path_raw_image: Path of the raw image
    :type path_raw_image: str
    :param path_geo_image: Path of the geo image
    :type path_geo_image: str
    :param force: Signals if the function should overwrite an already existing geo image (Default: False)
    :type force: bool
    :param clip: GeoJSON clip geometry
    :type clip: dict
    :result: Path of the geo image
    :rtype: str
    """
    if not os.path.exists(path_raw_image):
        logger.debug(
            f'Skip processing of geo image for map "{transformation_obj.raw_map_id}", because of missing raw image ({path_raw_image}).'
        )
        return None

    if os.path.exists(path_geo_image) and force is False:
        logger.debug(
            'Skip processing of geo image for map "%s", because of an already existing geo image. Use "force" parameter in case you want to overwrite it.'
            % transformation_obj.raw_map_id
        )
        return path_geo_image

    # Parse georef parameters. Since newer version it is possible that the target crs of the gcps are different from
    # the target_crs of the transformation_obj. Because the rectification steps does only process the gcps, we make sure
    # that the target_crs of the gcps are the same as the target_crs from the transformation object
    georef_params = transformation_obj.get_params_as_dict()
    georef_params = transform_to_params_to_target_crs(
        transformation_obj.get_params_as_dict(),
        transformation_obj.get_target_crs_as_string()
        if transformation_obj.target_crs is not None
        else georef_params["target"],
    )

    # Try processing a geo transformation
    rectify_image_with_clip_and_overviews(
        path_raw_image,
        path_geo_image,
        georef_params["algorithm"],
        to_gdal_gcps(georef_params["gcps"]),
        georef_params["target"],
        PATH_TMP_ROOT,
        clip,
    )

    if not os.path.exists(path_geo_image):
        raise Exception(
            "Something went wrong while trying to process georeference image"
        )

    return path_geo_image
