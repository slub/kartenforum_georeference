#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 10.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
from osgeo import gdal
from osgeo import osr
from osgeo.gdalconst import GA_ReadOnly
from string import Template

def parseGeoTiffMetadata(tiffPath):
    """ Functions parses the metadata from a geotiff and returns it.

    :param tiffPath: str
    :type tiffPath: Path to the tiff file
    :return: Dictionary containing relevant tiff metadata
    :rtype: dict """
    try:
        dataset = gdal.Open(tiffPath, GA_ReadOnly)

        # Parse epsg code / projection
        proj = dataset.GetProjection()
        srs = osr.SpatialReference()
        srs.SetFromUserInput(proj)

        # Parse extent
        xmin, xpixel, _, ymax, _, ypixel = dataset.GetGeoTransform()
        width, height = dataset.RasterXSize, dataset.RasterYSize
        xmax = xmin + width * xpixel
        ymin = ymax + height * ypixel

        return {
            'layerUnit': 'dd' if srs.GetAttrValue('UNIT', 0) == 'degree' else 'meters',
            'layerProjection': srs.GetAttrValue('AUTHORITY', 0) + ':' + srs.GetAttrValue('AUTHORITY', 1),
            'layerExtent': '%s %s %s %s' % (xmin, ymin, xmax, ymax),
            'layerBands': dataset.RasterCount,
            'layerSize': '%s %s' % (width, height),
            'layerResolution': '%s %s' % (xpixel, ypixel)
        }
    finally:
        del dataset

def writeMapfile(targetPath, templatePath, templateValues):
    """ Functions writes a mapfile. It replaces the template with the given params dict.

    :param targetPath: Path of the target file
    :type targetPath: str
    :param templatePath: Path to the template file
    :type templatePath: str
    :param templateValues: Dictionary containing the template values
    :type templateValues: Dict
    :return: Path to template file
    :rtype: str
    """

    # Create new template string
    content = None
    with open(templatePath, 'r') as f:
        src = Template(f.read())
        content = src.substitute(templateValues)

    if content != None:
        with open(targetPath, 'w') as f:
            f.write(content)
    return targetPath