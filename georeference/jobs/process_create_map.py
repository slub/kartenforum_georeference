#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by nicolas.looschen@pikobytes.de on 25.04.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import json
import os.path

from georeference.jobs.actions.create_raw_image import run_process_raw_image
from georeference.jobs.actions.update_index import run_update_index
from georeference.jobs.process_update_maps import generate_thumbnail, generate_zoomify
from georeference.models import RawMap, Metadata
from georeference.settings import PATH_IMAGE_ROOT
from georeference.utils import create_path_if_not_exists
from georeference.utils.utils import without_keys, remove_if_exists


def run_process_create_map(es_index, dbsession, logger, job):
    """ Runs jobs of type "maps_create"

    :param es_index: Elasticsearch client
    :type es_index: elasticsearch.Elasticsearch
    :param dbsession: Database session
    :type dbsession: sqlalchemy.orm.session.Session
    :param logger: Logger
    :type logger: logging.Logger
    :param job: Job which will be processed
    :type job: georeference.models.jobs.Job
    """

    # initialize file paths
    thumbnail_target_small = None
    thumbnail_target_mid = None
    processed_image_path = None
    zoomify_target = None

    try:
        # Query the associated transformation process
        description = json.loads(job.description)
        map_id = description['map_id']
        metadata = description['metadata'].copy()
        # generate path for the processed image
        processed_image_path = os.path.join(PATH_IMAGE_ROOT, metadata['map_type'], f'{map_id}.tif')

        if not os.path.exists(PATH_IMAGE_ROOT):
            logger.error(f'Configured PATH_IMAGE_ROOT ({PATH_IMAGE_ROOT}) does not exists.')

        # ensure all paths relative to the PATH_IMAGE_ROOT exists
        create_path_if_not_exists(os.path.dirname(processed_image_path))

        # 1. Process raw image
        processed_image_path = run_process_raw_image(description['file'], processed_image_path, logger, force=False)

        # 2. If not present, generate zoomify tiles
        if 'link_zoomify' not in metadata:
            metadata['link_zoomify'] = generate_zoomify(processed_image_path, map_id, logger)

        # 3. If not present, generate thumbnails
        if 'link_thumb_mid' not in metadata:
            metadata['link_thumb_mid'] = generate_thumbnail(processed_image_path, map_id, 400, logger)

        if 'link_thumb_small' not in metadata:
            metadata['link_thumb_small'] = generate_thumbnail(processed_image_path, map_id, 120, logger)

        # 4. Insert Raw Map
        file_name = os.path.splitext(processed_image_path.split(os.sep)[-1])[0]
        rel_path = os.path.relpath(processed_image_path, PATH_IMAGE_ROOT)

        raw_map_obj = RawMap(id=description['map_id'],
                             allow_download=False if 'allow_download' not in metadata else metadata[
                                 'allow_download'], file_name=file_name, enabled=True,
                             map_type=metadata['map_type'],
                             default_crs=None if 'default_crs' not in metadata else metadata['default_crs'],
                             rel_path=rel_path,
                             map_scale=metadata['map_scale'])
        dbsession.add(raw_map_obj)
        dbsession.flush()

        # 5. Insert Metadata
        dbsession.add(
            Metadata(raw_map_id=raw_map_obj.id,
                     **without_keys(metadata, ['allow_download', 'default_srs', 'map_scale', 'map_type'])))

        # 6. Update Metadata
        run_update_index(es_index, raw_map_obj, None, dbsession, logger)

    except Exception as e:
        # cleanup leftover files
        remove_if_exists(processed_image_path)
        remove_if_exists(thumbnail_target_mid)
        remove_if_exists(thumbnail_target_small)
        remove_if_exists(zoomify_target)
        raise e
