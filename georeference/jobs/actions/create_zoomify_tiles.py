#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Created by jacob.mendt@pikobytes.de on 20.04.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import os
import shutil
import subprocess

from loguru import logger


def run_process_zoomify_tiles(path_src_raw_img, path_zoomify_tiles, force=False):
    """This actions creates zoomify tiles for a given input image. For producing the zoomify tiles it uses the
        libvips tools. See also https://www.libvips.org/API/current/Making-image-pyramids.md.html.

    :param path_src_raw_img: Path to the source image.
    :type path_src_raw_img: str
    :param path_zoomify_tiles: Path of the target image
    :type path_zoomify_tiles: str
    :param logger: Logger
    :type logger: logging.Logger
    :param force: Signals if the function should overwrite an already existing target image (Default: False)
    :type force: bool
    :result: Path of the geo image
    :rtype: str
    """
    if not os.path.exists(path_src_raw_img):
        logger.debug('Could not find source raw image "%s".' % path_src_raw_img)
        return None

    if os.path.exists(path_zoomify_tiles) and force is False:
        logger.debug(
            'Skip processing of zoomify tiles for raw image "%s", because of an already existing tiles. Use "force" parameter in case you want to overwrite it.'
            % path_zoomify_tiles
        )
        return path_zoomify_tiles
    elif os.path.exists(path_zoomify_tiles) and force:
        shutil.rmtree(path_zoomify_tiles)

    logger.info("Process zoomify tiles %s ..." % path_src_raw_img)
    command = "vips dzsave %(path_src)s %(path_trg)s --layout zoomify" % {
        "path_src": path_src_raw_img,
        "path_trg": path_zoomify_tiles,
    }

    try:
        logger.debug(command)
        subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        logger.error(e.output)
        raise

    if not os.path.exists(path_zoomify_tiles):
        raise Exception("Something went wrong while trying to process zoomify tiles.")

    return path_zoomify_tiles
