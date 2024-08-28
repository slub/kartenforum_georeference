#!/usr/bin/env python
# -*- coding: utf-8 -*-
from fastapi import HTTPException
from loguru import logger
from osgeo import gdal

from georeference.config.templates import (
    TEMPLATE_PUBLIC_MAP_ID,
    TEMPLATE_PUBLIC_MOSAIC_MAP_ID,
)


# Created by nicolas.looschen@pikobytes.de on 10.07.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package


def from_public_map_id(public_id):
    """Transforms a public map id to an internal map_id.

    :param public_id: Public map id
    :type public_id: str
    :result: Internal map_id
    :rtype: int
    """
    ns, map_id = public_id.rsplit("-", 1)
    if ns != TEMPLATE_PUBLIC_MAP_ID.rsplit("-", 1)[0]:
        raise TypeError("Can not process the given public map_id.")
    return int(map_id)


def to_public_map_id(map_id):
    """Transforms a given map_id to a public map id.

    :param map_id: Internal map_id
    :type map_id: int
    :result: Public map id.
    :rtype: str
    """
    return TEMPLATE_PUBLIC_MAP_ID.format(map_id)


def to_int(v):
    """Tries to cast a given value to an int.

    :param v: Any value
    :type v: any
    :result: Value as int
    :rtype: int
    :raise: TypeError
    """
    if isinstance(int(v), int):
        return int(v)
    else:
        raise TypeError("The given values is not an integer.")


def to_public_mosaic_map_id(mosaic_map_id):
    """Transforms a given mosaic_map_id to a public mosaic map id.

    :param mosaic_map_id: Internal mosaic_id
    :type mosaic_map_id: int
    :result: Public map id.
    :rtype: str
    """
    return TEMPLATE_PUBLIC_MOSAIC_MAP_ID.format(mosaic_map_id)


def from_public_mosaic_map_id(public_id):
    """Transforms a public mosaic map id to an internal mosaic_id.

    :param public_id: Public oai
    :type public_id: str
    :result: Internal mosaic_id
    :rtype: int
    """
    ns, mosaic_id = public_id.rsplit("-", 1)
    if ns != TEMPLATE_PUBLIC_MOSAIC_MAP_ID.rsplit("-", 1)[0]:
        raise TypeError("Can not process the given public mosaic_id.")
    return int(mosaic_id)


def to_gdal_gcps(gcps):
    """Transforms gcps in the service API notation to gdal gcps.

    :param gcps:  List of gcps
    :type gcps: { target: [number, number], source: [number, number] }[]
    :result: List of gdal.GCPs
    :rtype: [gdal.GCP]
    """
    return list(
        map(
            lambda gcp: gdal.GCP(
                gcp["target"][0],
                gcp["target"][1],
                0,
                gcp["source"][0],
                gcp["source"][1],
            ),
            gcps,
        )
    )


def parse_public_map_id(map_id: str):
    try:
        return to_int(from_public_map_id(map_id))
    except Exception as e:
        logger.warning(f"Error while parsing map_id {map_id}")
        logger.error(e)
        raise HTTPException(status_code=400, detail="Invalid map_id")
