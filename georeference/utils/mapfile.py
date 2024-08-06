#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 10.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import os
from osgeo import gdal
from osgeo import osr
from osgeo.gdalconst import GA_ReadOnly
from string import Template


def parse_geo_tiff_metadata(tiff_path):
    """Functions parses the metadata from a geotiff and returns it.

    :param tiff_path: str
    :type tiff_path: Path to the tiff file
    :return: Dictionary containing relevant tiff metadata
    :rtype: dict"""
    try:
        dataset = gdal.Open(tiff_path, GA_ReadOnly)

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
            "layerUnit": "dd" if srs.GetAttrValue("UNIT", 0) == "degree" else "meters",
            "layerProjection": srs.GetAttrValue("AUTHORITY", 0)
            + ":"
            + srs.GetAttrValue("AUTHORITY", 1),
            "layerExtent": "%s %s %s %s" % (xmin, ymin, xmax, ymax),
            "layerBands": dataset.RasterCount,
            "layerSize": "%s %s" % (width, height),
            "layerResolution": "%s %s" % (xpixel, ypixel),
        }
    finally:
        del dataset


def write_mapfile(target_path, template_path, template_values):
    """Functions writes a mapfile. It replaces the template with the given params dict.

    :param target_path: Path of the target file
    :type target_path: str
    :param template_path: Path to the template file
    :type template_path: str
    :param template_values: Dictionary containing the template values
    :type template_values: Dict
    :return: Path to the new mapfile
    :rtype: str
    """

    # Create new template string
    content = None
    with open(template_path, "r") as f:
        src = Template(f.read())
        content = src.substitute(template_values)

    if content is not None:
        with open(target_path, "w") as f:
            f.write(content)
    return os.path.abspath(target_path)
