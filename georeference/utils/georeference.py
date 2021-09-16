#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 06.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import uuid
import os
import subprocess
import json
import sys
from osgeo import gdal
from osgeo.gdalconst import GDT_Byte
from osgeo.gdalconst import GA_ReadOnly
from ..settings import GEOREFERENCE_PATH_GDALWARP
from ..settings import GEOREFERENCE_PATH_GDALADDO
from ..settings import SRC_DICT_WKT
from ..settings import TMP_DIR

def _addOverviews(dstFile, overviewLevels, logger):
    """ Function adds overview to given geotiff.

    :param dstFile: Path of the destination image to which overviews should be added
    :type dstFile: str
    :param overviewLevels: String describing the adding of overview levels
    :type overviewLevels: str
    :param logger: Logger
    :type logger: logging.Logger
    :return: str
    :raise: Exception """
    try:
        logger.debug('Adding overviews to raster %s'%dstFile)
        command = '%s --config GDAL_CACHEMAX 500 -r average %s %s' % (GEOREFERENCE_PATH_GDALADDO, dstFile, overviewLevels)
        subprocess.check_call(command, shell=True)
        return dstFile
    except:
        logger.error("%s - Unexpected error while trying add overviews to the raster: %s - with command - %s"%(sys.stderr,sys.exc_info()[0],command))
        raise Exception("Error while running subprocess via commandline!")


def _createVrt(srcDataset, dstFile):
    """ This functions creates a vrt for a corresponding, from gdal supported, source dataset.

    :type srcDataset: osgeo.gdal.Dataset
    :type dstFile: str
    :return: str """
    outputFormat = 'VRT'
    dstDriver = gdal.GetDriverByName(outputFormat)
    dstDataset = dstDriver.CreateCopy(dstFile, srcDataset,0)
    return dstDataset

def _getExtentFromDataset(dataset):
    """ Returns the extent of a given gdal dataset.

    :type gdal.Dataset: dataset
    :return: Boundingbox of the image
    :rtype: [number]
    """
    cols = dataset.RasterXSize
    rows = dataset.RasterYSize

    geotransform = dataset.GetGeoTransform()
    bb1 = originX = geotransform[0]
    bb4 = originY = geotransform[3]

    pixelWidth = geotransform[1]
    pixelHeight = geotransform[5]
    width = cols*pixelWidth
    height = rows*pixelHeight

    bb3 = originX + width
    bb2 = originY + height
    return [ bb1, bb2, bb3, bb4 ]

def getImageExtent(filePath):
    """ Returns the extent for a given georeference image.

    :param filePath: Path to the georeferenced image
    :type filePath: str
    :return: Extent of the georeference image
    :rtype: [number]
    """
    try:
        dataset = gdal.Open(filePath, GA_ReadOnly)
        return _getExtentFromDataset(dataset)
    except:
        raise
    finally:
        del dataset

def rectifyImage(srcFile, dstFile, algorithm, gcps, srs, logger, tmpDir, clipGeoJSON=None):
    """ Functions generates and clips a georeferenced image based on a polynom transformation. This function heavily
    relies on the usage of [gdalwarp](https://gdal.org/programs/gdalwarp.html).

    :param srcFile: Source image path
    :type srcFile: str
    :param dstFile: Target image path
    :type dstFile: str
    :param algorithm: Transformation algorithm for the rectification
    :type algorithm: 'polynom', 'affine', 'tps'
    :param gcps: List of ground control points for rectifing the image
    :type gcps: List.<gdal.GCP>
    :param srs: EPSG code of the spatial reference system. Currently only EPSG:4314 is supported
    :type srs: int
    :param logger: Logger
    :type logger: logging.logger
    :param tmpDir: Path for temporary working directory
    :type tmpDir: str
    :param clipGeoJSON: Path to the GeoJSON which is used for clipping
    :type clipGeoJSON: str (Default: None)
    :raise: ValueError
    :result: Path to the target image
    :rtype: str
    """
    tmpFile = None
    try:
        # define tmp file path
        tmpDataName = uuid.uuid4()

        # get projection
        geoProj = SRC_DICT_WKT[srs]
        if geoProj is None:
            raise ValueError('The given srs "%s" is not supported' % srs)

        # Is algorithm supported
        if algorithm not in ['polynom', 'tps', 'affine']:
            raise ValueError('The given algorithm "%s" is not supported.' % algorithm)

        # Create a virtual raster dataset and add the GCP with the target geoprojection to it
        tmpFile = os.path.abspath(
            os.path.join(tmpDir, '%s.vrt' % tmpDataName)
        )
        newDataset = _createVrt(gdal.Open(srcFile, GA_ReadOnly), tmpFile)
        newDataset.SetGCPs(gcps, geoProj)
        newDataset.FlushCache()

        if os.path.exists(tmpFile):
            logger.info('Rectify image with a %s transformation ...' % (algorithm))
            # The rectification is done via gdalwarp command line utility. Therefor we first build the correct
            # string.
            command = '%s -overwrite --config GDAL_CACHEMAX 500 -r near -wm 500 ' % (GEOREFERENCE_PATH_GDALWARP)

            # In case the algorithm is tps we extend the command with -tps
            if algorithm == 'tps':
                command += '-tps '

            # In case the algorithm is affine we set order=1 to tell gdalwarp to use a polynom first order. If either
            # affine or tps, gdal uses a polynom by default
            if algorithm == 'affine':
                command += '-order 1 '

            # If a shapefile with a clip polygon is defined it is used.
            if clipGeoJSON is not None:
                command += '-crop_to_cutline -cutline \'%s\' ' % clipGeoJSON

            # append source and dest file
            command += '%s %s' % (tmpFile, dstFile)

            # run the command
            logger.debug(command)
            subprocess.check_call(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )
        return dstFile
    except Exception as e:
        logger.error(e)
        raise
    finally:
        if os.path.exists(tmpFile):
            os.remove(tmpFile)
        del newDataset

def rectifyImageWithClipAndOverviews(srcFile, dstFile, algorithm, gcps, gcps_srs, logger, tmpDir, clip=None):
    """ Function rectifies a image, clips it and adds overviews to it.

:param srcFile: Source image path
    :type srcFile: str
    :param dstFile: Target image path
    :type dstFile: str
    :param algorithm: Transformation algorithm for the rectification
    :type algorithm: 'polynom', 'affine', 'tps'
    :param gcps: List of ground control points for rectifing the image
    :type gcps: List.<gdal.GCP>
    :param gcps_srs: EPSG code of the spatial reference system of the gcps. Currently only EPSG:4314 is supported
    :type gcps_srs: int
    :param logger: Logger
    :type logger: logging.logger
    :param tmpDir: Path for temporary working directory
    :type tmpDir: str
    :param clip: Clip as a GeoJSON geometry
    :type clip: dict
    :raise: ValueError
    :result: Path to the target image
    :rtype: str """
    try:
        # Check if the target directory exists and if not create it
        if not os.path.exists(os.path.dirname(dstFile)):
            os.makedirs(os.path.dirname(dstFile))

        # Create the clip shapefile
        clipFile = None
        if clip != None:
            clipFile = os.path.join(tmpDir, '%s.geojson' % uuid.uuid4())
            with open(clipFile, "w") as jsonFile:
                jsonFile.write(json.dumps(clip))
                jsonFile.close()

        rectifyImage(
            srcFile,
            dstFile,
            algorithm,
            gcps,
            gcps_srs,
            logger,
            tmpDir,
            clipGeoJSON=clipFile,
        )

        if not os.path.exists(dstFile):
            raise Exception('Could not find result of rectifyImage.')
        else:
            logger.info('Add overviews to the image ...')
            _addOverviews(dstFile, '2 4 8 16 32', logger)

        return dstFile
    except Exception as e:
        logger.error('Something went wrong while trying to generate a permanent georeference result')
        logger.error(e)
        raise