#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by pouria.rezaei@pikobytes.de on 29.08.24
#
# This file is subject to the terms and conditions defined in file
# 'LICENSE', which is part of this source code package

import os
from typing import Tuple
from loguru import logger

from georeference.config.paths import PATH_IMAGE_ROOT, PATH_THUMBNAIL_ROOT, create_path_if_not_exists
from georeference.jobs.actions.create_thumbnail import run_process_thumbnail
from georeference.utils.utils import check_if_file_exists


def process_thumbnail(
        image_name: str, target_directory: str, sizes: Tuple[int, int]
) -> None:
    """
    Generate thumbnails for a given image in the specified sizes if they do not already exist.

    :param image_name: The name of the image file.
    :param target_directory: The directory where thumbnails will be saved.
    :param sizes: A tuple containing the thumbnail sizes to be generated.
    """

    for size in sizes:
        thumbnail_name = f"{os.path.splitext(image_name)[0]}_{size}x{size}.jpg"
        thumbnail_path = os.path.join(target_directory, thumbnail_name)

        if not check_if_file_exists(thumbnail_name, target_directory):
            logger.info(f"Generating thumbnail {thumbnail_name} of size {size}x{size}.")
            try:
                run_process_thumbnail(
                    os.path.join(PATH_IMAGE_ROOT, image_name),
                    thumbnail_path,
                    size,
                    size,
                    force=True,
                )
                logger.info(f"Thumbnail {thumbnail_name} created successfully.")
            except Exception as e:
                logger.error(f"Failed to create thumbnail {thumbnail_name}: {e}")
        else:
            logger.info(
                f"Thumbnail {thumbnail_name} already exists, skipping creation."
            )


def initialize_thumbnails(
        image_directory: str, thumbnail_directory: str, sizes: Tuple[int, int]
) -> None:
    """
    Process all images in the given directory to create thumbnails of specified sizes,
    only if they do not already exist.

    :param image_directory: The path of the directory containing images.
    :param thumbnail_directory: The path of the directory where thumbnails will be stored.
    :param sizes: A tuple containing the sizes of the thumbnails to be generated.
    """
    create_path_if_not_exists(thumbnail_directory)
    logger.info(
        f"Processing images in '{image_directory}' to create thumbnails in '{thumbnail_directory}'."
    )

    for image_file in os.listdir(image_directory):
        image_path = os.path.join(image_directory, image_file)
        if os.path.isfile(image_path):
            logger.info(f"Processing image file: {image_file}")
            process_thumbnail(image_file, thumbnail_directory, sizes)
        else:
            logger.warning(f"Skipping non-file item: {image_file}")


if __name__ == "__main__":
    logger.info("Starting thumbnail generation process.")
    initialize_thumbnails(PATH_IMAGE_ROOT, PATH_THUMBNAIL_ROOT, (120, 400))
    logger.info("Thumbnail generation process completed.")
