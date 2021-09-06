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

def rectifyPolynomWithVRT(srcFile, dstFile,  gcps, srs, logger, tmpDir, clipShp=None, order=None):
    """ Functions generates and clips an image and adds a geotransformation matrix to it but it uses a vrt
        for faster processing.

    :param srcFile: Source image path
    :type srcFile: str
    :param dstFile: Target image path
    :type dstFile: str
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
    :param order: Order of the polygon (1 is the same like affine)
    :type order: int (Default: None)
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
            raise ValueError("SRS with id - %s - is not supported"%srs)

        # save results in VRT and increase processing speed
        tmpFile = os.path.join(tmpDir, '%s.vrt'%tmpDataName)
        newDataset = _createVrt(gdal.Open(srcFile, GA_ReadOnly), tmpFile)
        newDataset.SetGCPs(gcps, geoProj)
        # newDataset.SetProjection(geoProj)
        # newDataset.SetGeoTransform(gdal.GCPsToGeoTransform(gcps))
        newDataset.FlushCache()

        # doing the rectification
        if os.path.exists(tmpFile):
            # doing a rectification of an image using a polynomial transformation
            # and a nearest neighbor resampling method
            logger.debug('Do georeferencing based on a polynom transformation ...')
            resampling = 'near'
            order = order if order in [1,2,3] else None
            command = '%s -overwrite --config GDAL_CACHEMAX 500 -r %s -wm 500 ' % (GEOREFERENCE_PATH_GDALWARP, resampling)

            # check if order is described
            if order is not None:
                command += '-order %s ' % order

            # check if clip shape is defined
            if clipShp is not None:
                command += '-cutline \'%s\' -crop_to_cutline ' % clipShp

            # append source and dest file
            command += ' %s %s' % (tmpFile, dstFile)

            # run the command
            subprocess.check_call(command, shell=True)
        return dstFile
    except:
        raise
    finally:
        if os.path.exists(tmpFile):
            os.remove(tmpFile)

        del newDataset