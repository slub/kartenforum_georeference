#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Created by jacob.mendt@pikobytes.de on 20.04.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import os
import subprocess

from loguru import logger


def run_process_thumbnail(
    path_src_raw_img, path_thumbnail, width=None, height=None, force=False
):
    """This actions creates thumbnails for a given input image. For producing the thumbnail it uses the
        libvips tools. See also https://www.libvips.org/API/current/Using-vipsthumbnail.md.html.

    :param path_src_raw_img: Path to the source image.
    :type path_src_raw_img: str
    :param path_thumbnail: Path of the target image
    :type path_thumbnail: str
    :param width: Width of the output thumbnail in pixel
    :type width: int
    :param height: Height of the output thumbnail in pixel
    :type height: int
    :param force: Signals if the function should overwrite an already existing target image (Default: False)
    :type force: bool
    :result: Path of the geo image
    :rtype: str
    """
    if not os.path.exists(path_src_raw_img):
        logger.debug('Could not find source raw image "%s".' % path_src_raw_img)
        return None

    if os.path.exists(path_thumbnail) and force is False:
        logger.debug(
            'Skip processing of thumbnail "%s", because file already exists. Use "force" parameter in case you want to overwrite it.'
            % path_thumbnail
        )
        return path_thumbnail
    elif os.path.exists(path_thumbnail) and force:
        os.remove(path_thumbnail)

    # Check if a height or width is given. If not a thumbnail can be created because of missing information
    if width is None and height is None:
        raise Exception(
            "Can not create a thumbnail, because width and height are both missing."
        )

    logger.info("Process thumbnail %s ..." % path_src_raw_img)

    command = (
        "vipsthumbnail {path_src} -o {path_trg}[strip] --size {width}x{height}".format(
            path_src=path_src_raw_img,
            path_trg=path_thumbnail,
            width=width if width is not None else "",
            height=height if height is not None else "",
        )
    )

    try:
        logger.debug(command)
        subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        logger.error(e.output)
        raise

    if not os.path.exists(path_thumbnail):
        raise Exception("Something went wrong while trying to process thumbnail.")

    return path_thumbnail
