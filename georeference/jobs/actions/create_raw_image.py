#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 20.04.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import os
import subprocess
from osgeo import gdal

# For a full list of all supported CO (creation opions) have a lock at https://gdal.org/drivers/raster/gtiff.html
CO_PARAMETER = [
    ("PROFILE", "BASELINE"),
    ("TILED", "NO"),
    ("INTERLEAVE", "BAND")
]

# For a full list supported metadata tags have a lock at https://gdal.org/drivers/raster/gtiff.html
MO_PARAMETER = [
    ("TIFFTAG_DATETIME", ""),
    ("TIFFTAG_DOCUMENTNAME", ""),
    ("TIFFTAG_IMAGEDESCRIPTION", ""),
    ("TIFFTAG_SOFTWARE", "")
]

def _get_pixel_data_type(path_to_image):
    """ The function checks the pixel type.

    :param path_to_image: Path to the source image
    :type path_to_image: str
    """
    try:
        datasource = gdal.Open(path_to_image)
        return gdal.GetDataTypeName(
            datasource.GetRasterBand(1).DataType
        )
    finally:
        if datasource != None:
            del datasource

def run_process_raw_image(path_src_raw_img, path_trg_raw_img, logger, force=False):
    """ This action preprocess a raw image used for further processing within the georeference service. As part of the
        preprocessing it resets different default tiff metadata fields, changes some creation options and checks if
        should change the pixel data type. All this is done by using the command line utility gdal_translate, see also
        https://gdal.org/programs/gdal_translate.html and https://gdal.org/drivers/raster/gtiff.html for more information.

    :param path_src_raw_img: Path to the source image.
    :type path_src_raw_img: str
    :param path_trg_raw_img: Path of the target image
    :type path_trg_raw_img: str
    :param logger: Logger
    :type logger: logging.Logger
    :param force: Signals if the function should overwrite an already existing target image (Default: False)
    :type force: bool
    :result: Path of the raw image
    :rtype: str
    """
    if not os.path.exists(path_src_raw_img):
        logger.debug('Could not find source raw image "%s".' % path_src_raw_img)
        return None

    if os.path.exists(path_trg_raw_img) and force == False:
        logger.debug('Skip processing of raw image "%s", because of an already existing image. Use "force" parameter in case you want to overwrite it.' % path_trg_raw_img)
        return path_trg_raw_img

    logger.info("Process raw image %s ..." % path_src_raw_img)

    # Normally the input tiffs will have a pixel type of "BYTE". In some cases in the past,
    # there was also an pixel type "UInt16" which leads to problem with the map server products
    # and should be detected and resolved.
    data_type = _get_pixel_data_type(path_src_raw_img)
    fixDataType = True if data_type == "UInt16" else False

    command = "gdal_translate -of GTIFF {fix_data_type} {set_creation_options} {set_metadata_options} {path_src} {path_trg}".format(
        fix_data_type="-ot Byte -scale 0 65635 0 255" if fixDataType else "",
        path_src=path_src_raw_img,
        path_trg=path_trg_raw_img,
        set_creation_options=" ".join(['-co "%s=%s"' % (el[0], el[1]) for el in CO_PARAMETER]),
        set_metadata_options=" ".join(['-mo "%s=%s"' % (el[0], el[1]) for el in MO_PARAMETER]),
    )

    logger.debug(command)
    subprocess.check_call(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )

    if not os.path.exists(path_trg_raw_img):
        raise Exception('Something went wrong while trying to process raw image.')

    return path_trg_raw_img