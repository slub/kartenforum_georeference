#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Created by nicolas.looschen@pikobytes.de on 24.07.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package

import json
import os
import shutil

from osgeo import gdal, osr
from osgeo.gdalconst import GA_ReadOnly
from shapely.geometry import shape, mapping

from georeference.config.paths import (
    PATH_MAPFILE_ROOT,
    PATH_TMS_ROOT,
    PATH_THUMBNAIL_ROOT,
    PATH_ZOOMIFY_ROOT,
)
from georeference.models.georef_map import GeorefMap
from georeference.models.transformation import Transformation
from georeference.utils.georeference import _get_extent_from_dataset


def _same_coordinate(c1, c2):
    return c1[0] == c2[0] and c1[1] == c2[1]


def fix_polygon_geometry(geometry):
    """The function checks the given geometry for different typical failures, which leads
        to indexing problems for the geometry.

    :param geometry: GeoJSON geometry
    :type geometry: dict
    :result: GeoJSON geometry
    :rtype: dict
    """
    if geometry["type"] == "Polygon":
        corrected_coordinates = []
        for i in range(len(geometry["coordinates"][0])):
            coordinate = geometry["coordinates"][0][i]
            if i == 0:
                corrected_coordinates.append(coordinate)
            elif not _same_coordinate(coordinate, corrected_coordinates[-1]):
                corrected_coordinates.append(coordinate)
        return {"type": "Polygon", "coordinates": [corrected_coordinates]}
    elif geometry["type"] == "MultiPolygon":
        shapely_geom = shape(geometry)
        largest_polygon = max(shapely_geom.geoms, key=lambda a: a.area)
        return json.loads(json.dumps(mapping(largest_polygon)))
    else:
        return geometry


def get_extent_from_geotiff(file_path):
    """Parses the boundingbox from a georeference image

    :param file_path: Path the GeoTIFF
    :type file_path: str
    :result: Extent
    :rtype: number[]
    """
    try:
        dataset = gdal.Open(file_path, GA_ReadOnly)
        return _get_extent_from_dataset(dataset)
    finally:
        del dataset


def get_epsg_code_from_geotiff(path):
    """Returns the pure epsg code for a given GeoTIFF.

    :param path: Path to the geotiff
    :type path: str
    :result: EPSG code in the form "epsg:4324"
    :rtype: str
    """
    try:
        dataset = gdal.Open(path, GA_ReadOnly)
        proj = dataset.GetProjection()
        srs = osr.SpatialReference()
        srs.SetFromUserInput(proj)
        return srs.GetAttrValue("AUTHORITY", 0) + ":" + srs.GetAttrValue("AUTHORITY", 1)
    finally:
        del dataset


def get_extent_as_geojson_polygon(geo_tiff_path):
    """Extracts the extent from a geotiff file and returns a GeoJSON.

    :param geo_tiff_path: Path to geotiff.
    :param geo_tiff_path: str
    :result: GeoJSON representing the extent
    :rtype: GeoJSON"""
    extent = get_extent_from_geotiff(geo_tiff_path)
    srid = get_epsg_code_from_geotiff(geo_tiff_path)
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [extent[0], extent[1]],
                [extent[0], extent[3]],
                [extent[2], extent[3]],
                [extent[2], extent[1]],
                [extent[0], extent[1]],
            ]
        ],
        "crs": {
            "type": "name",
            "properties": {
                "name": srid,
            },
        },
    }


def get_geometry(map_id, dbsession):
    """This function helps to extract the geometry for a given georeferenced map in GeoJSON structure. It checks if a clip polygon
        is saved for a given GeorefMap and if yes returns the clip polygon as Geometry in GeoJSON structure. If no clip
        polygon is saved it uses the extent of the GeorefMap

    :param map_id: Id of a original map
    :type map_id: int
    :param dbsession: Database session
    :type dbsession: sqlalchemy.orm.session.Session
    :result: GeoJSON describing a geometry
    :rtype: dict
    """
    # Extract the GeorefMap object for the original map
    georef_map_obj = GeorefMap.by_raw_map_id(map_id, dbsession)

    if georef_map_obj is None:
        return None

    # Check if there is a clip polygon and if yes return it.
    clip_geometry = Transformation.get_valid_clip_geometry(
        georef_map_obj.transformation_id, dbsession
    )
    if clip_geometry:
        return fix_polygon_geometry(clip_geometry)
    else:
        return GeorefMap.get_extent_for_raw_map_id(map_id, dbsession)


def get_geometry_for_mosaic_map(mosaic_dataset):
    """This function helps to build a geometry for a mosaic map.

    :param mosaic_dataset: Path of the mosaic dataset
    :type mosaic_dataset: str
    :result: GeoJSON describing a geometry
    :rtype: dict
    """
    info = gdal.Info(mosaic_dataset, format="json")
    return info["wgs84Extent"]


def get_mapfile_id(raw_map_obj):
    """Function returns the mapfile id.

    :param raw_map_obj: RawMap
    :type raw_map_obj: georeference.models.raw_maps.RawMap
    :result: Id of the mapfile.
    :rtype: str"""
    return raw_map_obj.id


def get_mapfile_path(raw_map):
    """Function returns the mapfile.

    :param raw_map: RawMap
    :type raw_map: georeference.models.raw_maps.RawMap
    :result: Path to the mapfile
    :rtype: str"""
    return os.path.join(PATH_MAPFILE_ROOT, "%s.map" % get_mapfile_id(raw_map))


def get_tms_directory(raw_map_obj):
    """Function returns the tms directory.

    :param raw_map_obj: RawMap
    :type raw_map_obj: georeference.models.raw_maps.RawMap
    :result: Path to the tms directory
    :rtype: str"""
    return os.path.join(
        os.path.join(PATH_TMS_ROOT, str(raw_map_obj.map_type).lower()),
        raw_map_obj.file_name,
    )


def get_thumbnail_path(file_name):
    """Function returns a path for a thumbnail from a file name.

    :param file_name: Name
    :type file_name: str
    :result: Path to the tms directory
    :rtype: str"""

    return os.path.join(PATH_THUMBNAIL_ROOT, file_name)


def get_zoomify_path(zoomify_name):
    """Function returns a path for a thumbnail from a file name.

    :param zoomify_name: Name
    :type zoomify_name: str
    :result: Path to the tms directory
    :rtype: str"""

    return os.path.join(PATH_ZOOMIFY_ROOT, zoomify_name)


def remove_if_exists(subject):
    """
    Removes a path (directory or file) if it exists.

    :param: subject - file path
    """
    if subject is not None and os.path.exists(subject):
        if os.path.isdir(subject):
            shutil.rmtree(subject)
        else:
            os.remove(subject)


def without_keys(d, keys):
    """
    Return object without a set of keys.

    :param: d - object for which keys will be omitted
    :param: keys - keys which will be omitted
    """
    return {k: v for k, v in d.items() if k not in keys}


def bbox_position(bbox, container_bbox):
    xmin, ymin, xmax, ymax = bbox
    cxmin, cymin, cxmax, cymax = container_bbox

    # Prioritize the X-axis directions first
    if xmax < cxmin:
        return False, "west"  # Bounding box is to the west
    elif xmin < cxmin:
        return False, "west"  # Bounding box is partially to the west

    if xmin > cxmax:
        return False, "east"  # Bounding box is to the east
    elif xmax > cxmax:
        return False, "east"  # Bounding box is partially to the east

    # Now check the Y-axis directions
    if ymax < cymin:
        return False, "south"  # Bounding box is to the south
    elif ymin < cymin:
        return False, "south"  # Bounding box is partially to the south

    if ymin > cymax:
        return False, "north"  # Bounding box is to the north
    elif ymax > cymax:
        return False, "north"  # Bounding box is partially to the north

    # If none of the above, it's fully contained
    return True, None


def check_if_file_exists(file_name: str, directory: str) -> bool:
    """
    Check if a file exists in the given directory.

    :param file_name: The name of the file to check.
    :param directory: The directory in which to check for the file.
    :return: True if the file exists, False otherwise.
    """
    file_path = os.path.join(directory, file_name)
    return os.path.isfile(file_path)
