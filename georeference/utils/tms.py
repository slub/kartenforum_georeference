#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 17.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import argparse
import logging
import math
import os
import shutil
import subprocess
import sys

from PIL import Image
from loguru import logger
from osgeo import gdal

from georeference.config.paths import TMP_DIR

BASE_PATH = os.path.dirname(os.path.realpath(__file__))
BASE_PATH_PARENT = os.path.abspath(os.path.join(BASE_PATH, "../../"))
sys.path.insert(0, BASE_PATH)
sys.path.append(BASE_PATH_PARENT)


def _add_base_tile(target_dir):
    """Functions adds a basetile dir to a directory in case it doesn't exits.
    :type target_dir: str
    :return:
    """
    base_tile_dir = os.path.join(target_dir, "0/0")
    base_tile = os.path.join(base_tile_dir, "0.png")
    if not os.path.exists(base_tile):
        if not os.path.exists(base_tile_dir):
            os.makedirs(base_tile_dir)

        image = Image.new("RGBA", (256, 256), (255, 0, 0, 0))
        image.save(base_tile, "PNG")


def get_max_zoom_level(path_image):
    """This function calculates the best maximum zoom level for a given image based on https://wiki.openstreetmap.org/wiki/Zoom_levels

    :param path_image: Path to the target image
    :type path_image: str
    :return number
    """

    geo_tiff = gdal.Open(path_image)
    geo_transform = geo_tiff.GetGeoTransform()
    spatial_ref = geo_tiff.GetSpatialRef()
    coordinate_reference_system_unit = spatial_ref.GetAttrValue("UNIT", 0)

    # Constants
    radius = 6378137
    equator_circumference = 2 * math.pi * radius
    pixels_per_tile = 256
    max_zoom_level = 20

    # Calculate resolution based on spatial reference units
    try:
        if coordinate_reference_system_unit == "metre":
            resolution = geo_transform[1]

        else:
            # Approximate meters per degree at the equator
            meters_per_degree = equator_circumference / 360
            resolution = geo_transform[1] * meters_per_degree

        # Calculate the optimal zoom level
        zoom_level = math.log((equator_circumference / pixels_per_tile) / resolution, 2)
        optimal_max_zoom_level = min(math.floor(zoom_level), max_zoom_level)

        return optimal_max_zoom_level
    except Exception as e:
        raise ValueError(f"Error calculating the maximum zoom level: {e}")


def _build_tms_cache(path_image, target_root_path, processes):
    """Functions calculates a Tile Map Service cache for a given georeferenced source file.

    :param path_image: Path to target image
    :type path_image: str
    :param target_root_path: Path of the target directory, where to place the tms directory.
    :type target_root_path: str
    :param processes: Number of processes used by gdal2tiles
    :type processes: int
    :return: str"""
    logger.debug("------------------------------------------------------------------")
    logger.debug("Source image %s" % path_image)
    logger.debug("Target dir %s" % target_root_path)
    file_name, file_extension = os.path.splitext(os.path.basename(path_image))

    # check if target dir extist
    tms_target_dir = os.path.join(target_root_path, file_name)
    if os.path.exists(tms_target_dir):
        logger.debug("Remove old tsm cache directory ...")
        shutil.rmtree(tms_target_dir)

    max_zoom_level = get_max_zoom_level(path_image)
    zoom_level = f"0-{max_zoom_level}"
    os.makedirs(tms_target_dir)
    command = f"gdal2tiles.py --zoom={zoom_level} --processes={processes} --webviewer=none --resampling=average {path_image} {tms_target_dir}"

    try:
        logger.debug("Execute - %s" % command)
        subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        logger.error(e.output)
        raise
    return tms_target_dir


def _compress_tms_directory(path):
    """Functions runs a pngs compression on the given tms cache.

    :param path: Path to the directory containing the images
    :type path: path
    :return:
    """
    logger.debug("Run png compression on %s ..." % path)

    # Prevents pil from logs pollution
    logging.getLogger("PIL").setLevel(logging.WARNING)

    pngs = _get_all_image_paths_in_directory(path, "png")
    for png in pngs:
        Image.open(png).convert("RGBA").quantize(method=2).save(png)


def _get_all_image_paths_in_directory(base_dir, image_extension):
    """Functions iteratore of the baseDir and the subdirectory tree and and returns a list of image files paths found
    in the directory structure.

    :type str: baseDir
    :type str: imageExtension
    :return: list<str>
    """

    def _get_all_images_from_files_list(base_dir, files, image_extension):
        """Functions returns all images within a files list.

        :type str: baseDir
        :type list<str>: files
        :type str: imageExtension
        :return: list<str>
        """
        pngs = []
        for file in files:
            if os.path.splitext(file)[1][1:] == str(image_extension).lower():
                pngs.append(os.path.join(base_dir, file))
        return pngs

    images = []
    for root, dirs, files in os.walk(base_dir):
        # first check that directory doesn't start with "."
        dir_name = str(root).rsplit("/")[-1]
        # only look in directories which doesn't start with "."
        if dir_name[0] != ".":
            images.extend(_get_all_images_from_files_list(root, files, image_extension))
    return images


def calculate_compressed_tms(path_image, tms_path, processes=1):
    """The following functions creates a compressed version of TMS cache.

    :param path_image: Path to target image
    :type path_image: str
    :param tms_path: Path of the target directory
    :type tms_path: str
    :param processes: Number of processes used by gdal2tiles
    :type processes: int
    :return:
    """
    try:
        logger.debug("Calculate tms cache ...")
        tmp_cache_dir = _build_tms_cache(path_image, TMP_DIR, processes)

        logger.debug("Compress cache ...")
        _compress_tms_directory(tmp_cache_dir)

        # check if the target dir exits, if yes remove it
        if os.path.exists(tms_path):
            logger.debug("Remove old target dir ...")
            shutil.rmtree(tms_path)

        logger.debug(
            "Check if base tile directory is add to cache and add it if not ..."
        )
        _add_base_tile(tmp_cache_dir)

        logger.debug("Copy compressed cache to target dir ...")
        if not os.path.exists(tms_path):
            os.makedirs(tms_path)

        copy_command = f"rsync -rI {tmp_cache_dir}/ {tms_path}"
        logger.debug(copy_command)
        subprocess.check_output(copy_command, shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        logger.error(e.output)
        raise
    finally:
        if os.path.exists(tms_path):
            shutil.rmtree(tmp_cache_dir)


""" Main """
if __name__ == "__main__":
    script_name = "updatetms.py"
    parser = argparse.ArgumentParser(
        description="Scripts tooks a input dir and processes for all tiff images within the \
        directory a TMS cache in the output dir.",
        prog="Script %s" % script_name,
    )
    parser.add_argument(
        "--target_dir", help="Directory where the TMS directories should be placed."
    )
    parser.add_argument("--source_dir", help="Source directory")
    arguments = parser.parse_args()

    # calculateCompressedTMS('/srv/vk/data/georef/gl/df_dk_0004678.tif', '/home/mendt/Desktop/Test')
    calculate_compressed_tms(arguments.source_dir, arguments.target_dir)
