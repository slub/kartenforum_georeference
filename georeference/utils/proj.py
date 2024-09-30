#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Created by jacob.mendt@pikobytes.de on 03.05.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import pyproj
from osgeo import gdal, osr
from pyproj import CRS
from pyproj.aoi import AreaOfInterest
from pyproj.database import query_utm_crs_info


def get_epsg_and_bbox_for_tif(tif_file):
    # Get the information in JSON format using gdal.Info
    info = gdal.Info(tif_file, format="json")

    # Extract the EPSG code
    epsg = None
    if "coordinateSystem" in info and "wkt" in info["coordinateSystem"]:
        srs = osr.SpatialReference()
        srs.ImportFromWkt(info["coordinateSystem"]["wkt"])
        epsg = int(srs.GetAuthorityCode(None)) if srs.GetAuthorityCode(None) else None

    # Extract the bounding box
    bbox = (
        info["cornerCoordinates"]["lowerLeft"] + info["cornerCoordinates"]["upperRight"]
    )

    return epsg, bbox


def get_crs_for_transformation_params(
    transformation_params, raw_map_obj, target_crs=None
):
    """Function transforms transformations params from a request to full transformation params for processing. This
        includes the following tasks:

        1.) Make sure a "target_crs" is passed or extracted
        2.) Make sure the target gcps coordinates are matching the "crs"

    :param transformation_params: Parameter describing a transformation.
    :type transformation_params: {{
        "crs": str | None,
        "source": str,
        "target": str,
        "algorithm": str,
        "gcps": { "source": [number, number], "target": [number, number] }[]
    }}
    :param raw_map_obj: RawMap
    :type raw_map_obj: georeference.models.raw_maps.RawMap
    :param target_crs: EPSG code of the target crs
    :type target_crs: str
    """

    # First make sure we have an CRS
    crs_string = target_crs

    # Try to get the crs_string from the default_crs field of the matching raw_map_obj
    if crs_string is None and raw_map_obj.default_crs is not None:
        crs_string = f"EPSG:{raw_map_obj.default_crs}"

    # As fallback guess the crs from the passed params
    if crs_string is None:
        crs_string = _guess_crs_for_transformation_params(transformation_params)

    # This is used as check for making sure the extract crs is valid at all
    CRS.from_string(crs_string)

    # In case the crs_string differs from the "target" parameter project to target coordinates
    return crs_string.upper()


def transform_to_params_to_target_crs(transformation_params, target_crs):
    """Function transforms a given set of params to the given target_crs.

    :param transformation_params: Parameter describing a transformation.
    :type transformation_params: {{
        "crs": str | None,
        "source": str,
        "target": str,
        "algorithm": str,
        "gcps": { "source": [number, number], "target": [number, number] }[]
    }}
    :param raw_map_obj: RawMap
    :type raw_map_obj: georeference.models.raw_maps.RawMap
    :param target_crs: EPSG code of the target crs
    :type target_crs: str
    :result: Corrected parameter describing a transformation.
    :rtype: Dict"""

    # In case the target_crs differs from the "target" parameter project to target coordinates
    if target_crs.upper() != str(transformation_params["target"]).upper():
        transformer = pyproj.Transformer.from_crs(
            transformation_params["target"], target_crs, always_xy=True
        )
        transformed_gcps = map(
            lambda p: {
                "source": p["source"],
                "target": transformer.transform(p["target"][0], p["target"][1]),
            },
            transformation_params["gcps"],
        )
        transformation_params["gcps"] = list(transformed_gcps)
        transformation_params["target"] = target_crs.upper()

    return transformation_params


def _guess_crs_for_transformation_params(transformation_params):
    """Guessing function for trying to extract a crs from the given transformation params.

    :param transformation_params: Parameter describing a transformation.
    :type transformation_params: {{
        "crs": str | None,
        "source": str,
        "target": str,
        "algorithm": str,
        "gcps": { "source": [number, number], "target": [number, number] }[]
    }}
    :result: EPSG code describing a valid crs
    :rtype: str"""

    # By default (see also Schema definition), we expect that the gcps target points are in EPSG:4326. Therefor we calculate
    # threshold values for the width and height to decide if we should try to detect a projected crs or fallback to a geographic one
    gcps = transformation_params["gcps"]
    min_lon = min(gcps, key=lambda p: p["target"][0])["target"][0]
    max_lon = max(gcps, key=lambda p: p["target"][0])["target"][0]
    min_lat = min(gcps, key=lambda p: p["target"][1])["target"][1]
    max_lat = max(gcps, key=lambda p: p["target"][1])["target"][1]
    delta_lon = abs(min_lon - max_lon)
    delta_lat = abs(min_lat - max_lat)
    delta_lon_threshold = 2
    delta_lat_threshold = 1.5

    # if one of the threshold exceeded we set EPSG:4326 as target crs. If not we try to guess the utm coordinates
    if delta_lat > delta_lat_threshold or delta_lon > delta_lon_threshold:
        return "EPSG:4326"
    else:
        utm_crs_list = query_utm_crs_info(
            datum_name="WGS 84",
            area_of_interest=AreaOfInterest(
                west_lon_degree=min_lon,
                south_lat_degree=min_lat,
                east_lon_degree=max_lon,
                north_lat_degree=max_lat,
            ),
        )
        utm_crs = CRS.from_epsg(utm_crs_list[0].code)
        return str(utm_crs).upper()
