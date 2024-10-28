#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by pouria.rezaei@pikobytes.de on 29.08.24
#
# This file is subject to the terms and conditions defined in file
# 'LICENSE', which is part of this source code package

import os

from loguru import logger

from georeference.config.paths import PATH_ZOOMIFY_ROOT, PATH_IMAGE_ROOT, create_path_if_not_exists
from georeference.jobs.actions.create_zoomify_tiles import run_process_zoomify_tiles


def process_zoomify_tile(image_path: str, target_directory: str) -> None:
    """
    Generate Zoomify tiles for a given image if they do not already exist.

    :param image_path: The path of the image file.
    :param target_directory: The directory where Zoomify tiles will be saved.
    """
    image_name = os.path.basename(image_path)
    zoomify_target = os.path.join(target_directory, os.path.splitext(image_name)[0])

    if not os.path.exists(zoomify_target):
        try:
            logger.info(f"Generating Zoomify tiles for '{image_name}'.")
            run_process_zoomify_tiles(image_path, zoomify_target, force=True)
            logger.info(f"Zoomify tiles for '{image_name}' created successfully.")
        except Exception as e:
            logger.error(f"Error generating Zoomify tiles: {str(e)}")
    else:
        logger.info(
            f"Zoomify tiles for '{image_name}' already exist, skipping creation."
        )


def initialize_zoomify_tiles(image_directory: str, zoomify_directory: str) -> None:
    """
    Process all images in the given directory to create Zoomify tiles
    only if they do not already exist.

    :param image_directory: The path of the directory containing images.
    :param zoomify_directory: The path of the directory where Zoomify tiles will be stored.
    """
    create_path_if_not_exists(zoomify_directory)
    logger.info(
        f"Processing images in '{image_directory}' to create Zoomify tiles in '{zoomify_directory}'."
    )

    for image_file in os.listdir(image_directory):
        image_path = os.path.join(image_directory, image_file)
        if os.path.isfile(image_path):
            process_zoomify_tile(image_path, zoomify_directory)


if __name__ == "__main__":
    logger.info("Starting zoomify tiles generation process.")

    initialize_zoomify_tiles(PATH_IMAGE_ROOT, PATH_ZOOMIFY_ROOT)
    logger.info("Zoomify tiles generation process completed.")
