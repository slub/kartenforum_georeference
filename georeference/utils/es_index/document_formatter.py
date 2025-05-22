#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by nicolas.looschen@pikobytes.de on 13.11.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
from datetime import date
import json
import os

from loguru import logger
from pydantic import NaiveDatetime

from georeference.config.templates import TEMPLATE_TMS_URLS
from georeference.utils.es_index.es_index_sync import (
    _get_online_resource_permalink,
    _get_online_resource_wms,
    _get_online_resource_wcs,
    _get_online_resource_wcs_for_download,
)
from georeference.utils.parser import to_public_map_id, to_public_mosaic_map_id


def parse_url(url: str):
    return str(url).replace("http:", "")


def to_time_period(datetime: NaiveDatetime):
    year = datetime.date().year
    time_period_start = date(year, 1, 1)
    time_period_end = date(year, 12, 31)

    return time_period_start, time_period_end


def generate_es_original_map_document(
    raw_map_obj, metadata_obj, georef_map_obj=None, geometry=None
):
    """Generates an elasticsearch document for an original_map.

    :param raw_map_obj: Original map
    :type raw_map_obj: georeference.models.raw_maps.RawMap
    :param metadata_obj: Metadata obj
    :type metadata_obj: georeference.models.metadata.Metadata
    :param georef_map_obj: Georef map
    :type georef_map_obj: georeference.models.original_maps.GeorefMap | None
    :param geometry: GeoJSON geometry
    :type geometry: dict
    :result: Document matching the es mapping
    :rtype: dict
    """
    try:
        # Necessary for creating the online ressource
        online_resources = [_get_online_resource_permalink(metadata_obj)]

        # We can only create georeference ressources if the absolute path exists
        if georef_map_obj is not None and os.path.exists(georef_map_obj.get_abs_path()):
            online_resources.append(_get_online_resource_wms(raw_map_obj.id))
            if raw_map_obj.allow_download:
                extent = json.loads(georef_map_obj.extent)
                online_resources.append(_get_online_resource_wcs(raw_map_obj))
                online_resources.append(
                    _get_online_resource_wcs_for_download(
                        georef_map_obj,
                        raw_map_obj.file_name,
                        extent,
                    )
                )

        # Create tms link
        tms_urls = []
        if georef_map_obj is not None and os.path.exists(georef_map_obj.get_abs_path()):
            for template in TEMPLATE_TMS_URLS:
                tms_urls.append(
                    template.format(
                        str(raw_map_obj.map_type).lower() + "/" + raw_map_obj.file_name
                    )
                )

        keywords = ";".join(
            list(
                filter(
                    lambda x: x is not None, [metadata_obj.type, metadata_obj.technic]
                )
            )
        )

        time_period_start, time_period_end = to_time_period(
            metadata_obj.time_of_publication
        )

        return {
            "map_id": to_public_map_id(raw_map_obj.id),
            "file_name": raw_map_obj.file_name,
            "description": metadata_obj.description,
            "map_scale": int(raw_map_obj.map_scale)
            if raw_map_obj.map_scale is not None
            else None,
            "zoomify_url": str(metadata_obj.link_zoomify).replace("http:", ""),
            "map_type": raw_map_obj.map_type.lower(),
            "keywords": keywords if keywords is not None else "",
            "title_long": metadata_obj.title,
            "title": metadata_obj.title_short,
            "permalink": metadata_obj.permalink,
            "slub_url": metadata_obj.permalink,
            "online_resources": online_resources,
            "tms_urls": tms_urls,
            "thumb_url": str(metadata_obj.link_thumb_small).replace("http:", ""),
            "geometry": geometry if geometry is not None else None,  #
            "has_georeference": georef_map_obj is not None,
            "time_period_start": time_period_start,
            "time_period_end": time_period_end,
            "time_published": metadata_obj.time_of_publication.date().isoformat(),  # TODO DEPRECATED, remove time_published in next deployment
            "external_content_url": None,
            "external_content_type": None,
            "type": "single_sheet",
        }
    except Exception as e:
        logger.warning(
            "Failed creating a es document for georef map %s." % raw_map_obj.id
        )
        logger.error(e)


def generate_es_mosaic_map_document(mosaic_map_obj, geometry=None):
    """Generates an elasticsearch document for a mosaic_map.

    :param mosaic_map_obj: Mosaic map
    :type mosaic_map_obj: georeference.models.mosaic_maps.MosaicMap
    :param geometry: GeoJSON geometry
    :type geometry: dict
    :result: Document matching the es mapping
    :rtype: dict
    """
    try:
        # Necessary for creating the online ressource
        online_resources = [_get_online_resource_wms(mosaic_map_obj.name)]

        time_period_start, time_period_end = to_time_period(
            mosaic_map_obj.time_of_publication
        )

        return {
            "map_id": to_public_mosaic_map_id(mosaic_map_obj.id),
            "file_name": None,
            "description": mosaic_map_obj.description,
            "map_scale": int(mosaic_map_obj.map_scale)
            if mosaic_map_obj.map_scale is not None
            else None,
            "zoomify_url": None,
            "map_type": None,
            "keywords": "",
            "title_long": mosaic_map_obj.title,
            "title": mosaic_map_obj.title_short,
            "permalink": None,
            "slub_url": None,
            "online_resources": online_resources,
            "tms_urls": [],
            "thumb_url": str(mosaic_map_obj.link_thumb).replace("http:", ""),
            "geometry": geometry if geometry is not None else None,  #
            "has_georeference": True,
            "time_period_start": time_period_start,
            "time_period_end": time_period_end,
            "time_published": mosaic_map_obj.time_of_publication.date().isoformat(),  # TODO DEPRECATED, remove time_published in next deployment
            "external_content_url": None,
            "external_content_type": None,
            "type": "mosaic",
        }
    except Exception as e:
        logger.warning(
            "Failed creating a es document for mosaic map %s." % mosaic_map_obj.id
        )
        logger.error(e)


def generate_es_vector_map_document(vector_map_obj, geometry=None):
    """Generates an elasticsearch document for vector maps and external vector maps.

    :param vector_map_obj: external vector map or vector map
    :type vector_map_obj: georeference.models.vector_map.VectorMapExternal | georeference.models.vector_map.VectorMap
    :param geometry: GeoJSON geometry
    :type geometry: dict
    :result: Document matching the es mapping
    :rtype: dict
    """
    time_period = vector_map_obj.time_period
    time_period_start = time_period[0]
    time_period_end = time_period[1]

    external_content_url = getattr(vector_map_obj, "link_content", None)
    if external_content_url is not None:
        external_content_url = parse_url(external_content_url)

    external_content_type = getattr(vector_map_obj, "content_type", None)

    try:
        return {
            "map_id": vector_map_obj.public_id,
            "file_name": None,
            "description": vector_map_obj.description,
            "map_scale": None,
            "zoomify_url": None,
            "map_type": None,
            "keywords": "",
            "title_long": vector_map_obj.title,
            "title": vector_map_obj.title,
            "permalink": None,
            "slub_url": None,
            "online_resources": [],
            "tms_urls": [],
            "thumb_url": str(vector_map_obj.link_thumb).replace("http:", "")
            if vector_map_obj.link_thumb is not None
            else "",
            "geometry": geometry if geometry is not None else None,
            "has_georeference": True,
            "time_period_start": time_period_start,
            "time_period_end": time_period_end,
            "time_published": vector_map_obj.submitted.date().isoformat(),  # TODO DEPRECATED, remove time_published in next deployment
            "external_content_url": external_content_url,
            "external_content_type": external_content_type,
            "type": "vector",
        }
    except Exception as e:
        logger.warning(
            "Failed creating a es document for vector map %s." % vector_map_obj.id
        )
        logger.error(e)
