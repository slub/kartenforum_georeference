#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Created by nicolas.looschen@pikobytes.de on 25.04.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import json
import os.path
import shutil

from loguru import logger

from georeference.config.settings import get_settings
from georeference.models.georef_map import GeorefMap
from georeference.models.raw_map import RawMap
from georeference.utils.parser import to_public_map_id
from georeference.utils.utils import get_thumbnail_path, get_zoomify_path


def run_process_delete_maps(es_index, dbsession, job):
    """Runs jobs of type "maps_delete"

    :param es_index: Elasticsearch client
    :type es_index: elasticsearch.Elasticsearch
    :param dbsession: Database session
    :type dbsession: sqlalchemy.orm.session.Session
    :param job: Job which will be processed
    :type job: georeference.models.jobs.Job
    """
    message = "The delete failed before the map has been delete from the database."
    try:
        logger.debug(f"Start processing delete_map job with id {job.id}")
        description = json.loads(job.description)
        map_id = description["map_id"]

        # 1. Make sure to preserve the current georef map path
        georef_map = GeorefMap.by_raw_map_id(map_id, dbsession)
        georef_map_path = None
        if georef_map is not None:
            georef_map_path = georef_map.get_abs_path()

        # 2. Delete raw map and through cascade also the georef map, the transformations and the metadata
        raw_map = RawMap.by_id(map_id, dbsession)
        raw_map_path = None
        if raw_map is not None:
            raw_map_path = raw_map.get_abs_path()
        dbsession.delete(raw_map)

        # already commit this changes here, so the db session does not get rolled back if something
        # happens when deleting the files
        logger.debug(f"Successfully deleted information from db for Map {map_id}")
        dbsession.commit()

        message = "The delete has been written to the database, but the filesystem is not in sync."

        # 3. Delete document from index
        settings = get_settings()
        es_index.delete(
            index=settings.ES_INDEX_NAME, doc_type=None, id=to_public_map_id(map_id)
        )

        # 4. Delete files
        # 4 a) delete thumbnails
        path_thumb_small = get_thumbnail_path(f"{map_id}_120x120.jpg")
        if os.path.exists(path_thumb_small):
            os.remove(path_thumb_small)

        path_thumb_mid = get_thumbnail_path(f"{map_id}_400x400.jpg")
        if os.path.exists(path_thumb_mid):
            os.remove(path_thumb_mid)

        # 4 b) delete zoomify
        path_zoomify = get_zoomify_path(f"{map_id}")
        if os.path.exists(path_zoomify):
            shutil.rmtree(path_zoomify)

        # 4 c) delete georef map
        if georef_map_path is not None and os.path.exists(georef_map_path):
            os.remove(georef_map_path)

        # 4 d) delete preprocessed map file
        if raw_map_path is not None and os.path.exists(raw_map_path):
            os.remove(raw_map_path)

        logger.debug("Finished processing delete_map job.")

    except Exception as e:
        logger.info("Error while running the daemon")
        logger.error(e)
        raise Exception(message)
