#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 09.03.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import os

from loguru import logger

from georeference.config.settings import get_settings
from georeference.models.metadata import Metadata
from georeference.utils.es_index import generate_es_original_map_document
from georeference.utils.utils import get_geometry


def run_update_index(es_index, raw_map_obj, georef_map_obj, dbsession):
    """This action updates a search document within the elasticsearch based search index, based on the raw map and geo
        map objects. If the document does not exist, it creates it.

    :param es_index: Elasticsearch client
    :type es_index: elasticsearch.Elasticsearch
    :param raw_map_obj: RawMap
    :type raw_map_obj: georeference.models.raw_maps.RawMap
    :param georef_map_obj: GeorefMap
    :type georef_map_obj: georeference.models.georef_maps.GeorefMap
    :param dbsession: Database session
    :type dbsession: sqlalchemy.orm.session.Session

    :result: True if performed successfully
    :rtype: bool
    """
    # Synchronise the index with the current state of the raw map objects.
    logger.debug(
        "Write search record for raw map id %s to index ..." % (raw_map_obj.id)
    )
    document = generate_es_original_map_document(
        raw_map_obj,
        Metadata.by_map_id(raw_map_obj.id, dbsession),
        georef_map_obj=georef_map_obj
        if georef_map_obj is not None and os.path.exists(georef_map_obj.get_abs_path())
        else None,
        geometry=get_geometry(raw_map_obj.id, dbsession),
    )

    settings = get_settings()

    es_index.index(
        index=settings.ES_INDEX_NAME,
        doc_type=None,
        id=document["map_id"],
        body=document,
    )
