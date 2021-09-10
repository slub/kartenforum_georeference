#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 06.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import uuid
import os
import subprocess
from osgeo import gdal
from osgeo.gdalconst import GDT_Byte
from osgeo.gdalconst import GA_ReadOnly
from ..settings import GEOREFERENCE_PATH_GDALWARP
from ..settings import SRC_DICT_WKT

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

def rectifyImage(srcFile, dstFile, algorithm, gcps, srs, logger, tmpDir, clipShp=None):
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
    :param clipShp: Path to the shapefile which is used for clipping
    :type clipShp: str (Default: None)
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
                command += '-order 1'

            # If a shapefile with a clip polygon is defined it is used.
            if clipShp is not None:
                command += '-cutline \'%s\' -crop_to_cutline ' % clipShp

            # append source and dest file
            command += ' %s %s' % (tmpFile, dstFile)

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