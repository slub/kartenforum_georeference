#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 17.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import argparse
import os
import shutil
import subprocess
import sys
import logging
from PIL import Image
from osgeo import gdal
from osgeo.gdalconst import GA_ReadOnly

BASE_PATH = os.path.dirname(os.path.realpath(__file__))
BASE_PATH_PARENT = os.path.abspath(os.path.join(BASE_PATH, os.pardir))
sys.path.insert(0, BASE_PATH)
sys.path.append(BASE_PATH_PARENT)

TMP_DIR = '/tmp'

LOGGER = logging.getLogger(__name__)

def addBaseTile(targetDir):
    """ Functions adds a basetile dir to a directory in case it doesn't exits.

    :type str: targetDir
    :return:
    """
    baseTileDir = os.path.join(targetDir, '0/0')
    baseTile = os.path.join(baseTileDir, '0.png')
    if not os.path.exists(baseTile):
        if not os.path.exists(baseTileDir):
            os.makedirs(baseTileDir)

        image = Image.new('RGBA', (256,256), (255, 0, 0, 0))
        image.save(baseTile, 'PNG')

def buildTMSCache(pathImage, targetPath, logger, processes, map_scale):
    """ Functions calculates a Tile Map Service cache for a given georeferenced source file.

    :param pathImage: Path to target image
    :type pathImage: str
    :param targetPath: Path of the target directory
    :type targetPath: str
    :param logger: Logger
    :type logger: logging.Logger
    :param processes: Number of processes used by gdal2tiles
    :type processes: int
    :param map_scale: Scale of the map as a number.
    :type map_scale: int
    :return: str  """
    logger.debug('------------------------------------------------------------------')
    file_name, file_extension = os.path.splitext(os.path.basename(pathImage))

    # extract epsg from source file
    logger.debug('Extract input projection ...')
    dataset = gdal.Open(pathImage, GA_ReadOnly)
    projection = dataset.GetProjectionRef()
    del dataset

    # check if target dir extist
    tms_target_dir = os.path.join(targetPath, file_name)
    if os.path.exists(tms_target_dir):
        logger.debug('Remove old tsm cache directory ...')
        shutil.rmtree(tms_target_dir)

    zoomLevel = '1-15'
    if map_scale != None and map_scale <= 5000 and map_scale > 0:
        zoomLevel = '1-17'
    elif map_scale != None and map_scale <= 15000 and map_scale > 5000:
        zoomLevel = '1-16'


    os.makedirs(tms_target_dir)
    if processes > 1:
        gdalScript = os.path.join(os.path.realpath(__file__), 'processing/gdal2tilesp.py')
        command = '%s -z %s -w none -s %s# --processes=%s -o tms %s %s'%(gdalScript, zoomLevel, processes, projection, pathImage, tms_target_dir)
    else:
        command = 'gdal2tiles.py -z %s -w none -s %s#  %s %s'%(zoomLevel, projection, pathImage, tms_target_dir)

    logger.debug('Execute - %s'%command)
    subprocess.call(
        command,
        shell = True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    print('------------------------------------------------------------------')

    return tms_target_dir

def calculateCompressedTMS(inputImage, targetDir, logger, processes=1, map_scale=25000):
    """ The following functions creates a compressed version of TMS cache.

    :param pathImage: Path to target image
    :type pathImage: str
    :param targetPath: Path of the target directory
    :type targetPath: str
    :param logger: Logger
    :type logger: logging.Logger
    :param processes: Number of processes used by gdal2tiles
    :type processes: int
    :param map_scale: Scale of the map as a number.
    :type map_scale: int
    :return:
    """
    logger.debug('Calculate tms cache ...')
    tmpCacheDir = buildTMSCache(inputImage, TMP_DIR, logger, processes, map_scale)

    logger.debug('Compress cache ...')
    compressTMSCache(tmpCacheDir, logger)

    # check if the target dir exits, if yes remove it
    tmsDir = os.path.join(targetDir, os.path.basename(inputImage).split('.')[0])
    if os.path.exists(tmsDir):
        logger.debug('Remove old target dir ...')
        shutil.rmtree(tmsDir)

    logger.debug('Check if base tile directory is add to cache and add it if not ...')
    addBaseTile(tmpCacheDir)

    logger.debug('Copy compressed cache to target dir ...')
    if not os.path.exists(os.path.dirname(targetDir)):
        os.makedirs(os.path.dirname(targetDir))
    subprocess.call(['rsync', '-rI', tmpCacheDir, targetDir])

    logger.debug('Clean up ...')
    shutil.rmtree(tmpCacheDir)

def compressTMSCache(path, logger):
    """ Functions runs a pngs compression on the given tms cache.

    :param path: Path to the directory containing the images
    :type path: path
    :param logger: Logger
    :type logger: logging.Logger
    :return:
    """
    logger.debug('Run png compression on %s ...' % path)
    pngs = getImageFilesInDirTree(path, 'png')
    for png in pngs:
        Image.open(png).convert('RGBA').quantize(method=2).save(png)

def getImageFilesInDirTree(baseDir, imageExtension):
    """ Functions iteratore of the baseDir and the subdirectory tree and and returns a list of image files paths found
        in the directory structure.

        :type str: baseDir
        :type str: imageExtension
        :return: list<str>
    """
    def getAllImagesFromFilesList(baseDir, files, imageExtension):
        """ Functions returns all images within a files list.

            :type str: baseDir
            :type list<str>: files
            :type str: imageExtension
            :return: list<str>
        """
        pngs = []
        for file in files:
            if os.path.splitext(file)[1][1:] == str(imageExtension).lower():
                pngs.append(os.path.join(baseDir, file))
        return pngs

    images = []
    for root, dirs, files in os.walk(baseDir):
        # first check that directory doesn't start with "."
        dirName = str(root).rsplit('/')[-1]
        # only look in directories which doesn't start with "."
        if dirName[0] != '.':
            images.extend(getAllImagesFromFilesList(root, files, imageExtension))
    return images


""" Main """
if __name__ == '__main__':
    script_name = 'updatetms.py'
    parser = argparse.ArgumentParser(description = 'Scripts tooks a input dir and processes for all tiff images within the \
        directory a TMS cache in the output dir.', prog = 'Script %s'%script_name)
    parser.add_argument('--target_dir', help='Directory where the TMS directories should be placed.')
    parser.add_argument('--source_dir', help='Source directory')
    arguments = parser.parse_args()

    # calculateCompressedTMS('/srv/vk/data/georef/gl/df_dk_0004678.tif', '/home/mendt/Desktop/Test')
    calculateCompressedTMS(arguments.source_dir, arguments.target_dir, LOGGER)