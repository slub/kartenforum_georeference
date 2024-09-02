#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by nicolas.looschen@pikobytes.de on 25.04.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import json
import os.path
from urllib.parse import urlsplit, urlunsplit

from loguru import logger
from sqlmodel import delete, update

from georeference.config.constants import raw_map_keys
from georeference.config.paths import (
    PATH_IMAGE_ROOT,
    create_path_if_not_exists,
)
from georeference.config.templates import (
    TEMPLATE_PUBLIC_THUMBNAIL_URL,
    TEMPLATE_PUBLIC_ZOOMIFY_URL,
)
from georeference.jobs.actions.create_raw_image import run_process_raw_image
from georeference.jobs.actions.create_thumbnail import run_process_thumbnail
from georeference.jobs.actions.create_zoomify_tiles import run_process_zoomify_tiles
from georeference.jobs.actions.update_index import run_update_index
from georeference.models.georef_map import GeorefMap
from georeference.models.metadata import Metadata
from georeference.models.raw_map import RawMap
from georeference.models.transformation import Transformation
from georeference.utils.utils import (
    without_keys,
    get_thumbnail_path,
    get_zoomify_path,
    remove_if_exists,
)


def run_process_update_maps(es_index, dbsession, job):
    """Runs jobs of type "maps_update"

    :param es_index: Elasticsearch client
    :type es_index: elasticsearch.Elasticsearch
    :param dbsession: Database session
    :type dbsession: sqlalchemy.orm.session.Session
    :param job: Job which will be processed
    :type job: georeference.models.jobs.Job
    """
    logger.debug("Process maps_update job ...")
    description = json.loads(job.description)
    map_id = description["map_id"]
    metadata_updates = {}
    raw_map_object = RawMap.by_id(map_id, dbsession)

    if "metadata" in description and description["metadata"] is not None:
        metadata_updates = {**description["metadata"].copy(), **metadata_updates}

    # collect updates which should be written to db
    raw_map_updates = _get_defined_keys(metadata_updates, raw_map_keys)

    # Join metadata locally with already registered updates for further processing
    metadata = join_existing_metadata_with_updates(map_id, metadata_updates, dbsession)

    # Get current path
    processed_image_path = raw_map_object.get_abs_path()

    is_file_updated = "file" in description and description["file"] is not None
    logger.debug(f"Update file: {is_file_updated}")

    if is_file_updated:
        if not os.path.exists(PATH_IMAGE_ROOT):
            logger.warning(
                f"Configured PATH_IMAGE_ROOT ({PATH_IMAGE_ROOT}) does not exists."
            )

        # ensure all paths relative to the PATH_IMAGE_ROOT exists
        create_path_if_not_exists(os.path.dirname(processed_image_path))

        processed_image_path = run_process_raw_image(
            description["file"], processed_image_path, force=True
        )

        raw_map_updates["file_name"] = os.path.splitext(
            processed_image_path.split(os.sep)[-1]
        )[0]
        raw_map_updates["rel_path"] = os.path.relpath(
            processed_image_path, PATH_IMAGE_ROOT
        )

    # handle link updates if necessary
    internal_thumbnail_base_url = _get_base_url(TEMPLATE_PUBLIC_THUMBNAIL_URL)
    internal_zoomify_base_url = _get_base_url(TEMPLATE_PUBLIC_ZOOMIFY_URL)

    if _should_generate_files(
        metadata,
        metadata_updates,
        "link_zoomify",
        internal_zoomify_base_url,
        is_file_updated,
    ):
        metadata_updates["link_zoomify"] = generate_zoomify(
            processed_image_path, map_id
        )

    if _should_generate_files(
        metadata,
        metadata_updates,
        "link_thumb_small",
        internal_thumbnail_base_url,
        is_file_updated,
    ):
        metadata_updates["link_thumb_small"] = generate_thumbnail(
            processed_image_path, map_id, 120
        )

    if _should_generate_files(
        metadata,
        metadata_updates,
        "link_thumb_mid",
        internal_thumbnail_base_url,
        is_file_updated,
    ):
        metadata_updates["link_thumb_mid"] = generate_thumbnail(
            processed_image_path, map_id, 400
        )

    # Write updates to db
    if len(raw_map_updates) > 0:
        stmt = update(RawMap).where(RawMap.id == map_id).values(**raw_map_updates)
        dbsession.execute(stmt)

    if len(metadata_updates) > 0:
        metadata_updates = without_keys(metadata_updates, raw_map_keys)
        stmt = (
            update(Metadata)
            .where(Metadata.raw_map_id == map_id)
            .values(**metadata_updates)
        )
        dbsession.execute(stmt)

    dbsession.flush()

    # delete transformations and georef map
    georef_obj = None
    if is_file_updated:
        _reset_georef_state_for_map(map_id, dbsession)
    else:
        georef_obj = GeorefMap.by_raw_map_id(map_id, dbsession)

    # update index
    run_update_index(es_index, raw_map_object, georef_obj, dbsession)


def generate_thumbnail(base_image_path, map_id, size):
    """
    Generates a thumbnail from a specific base_image.

    :param base_image_path: Path to the base image
    :type base_image_path: path like
    :param map_id: Map Id
    :type map_id: int
    :param size: size of the image:
    :type size: int
    :result: Public url of the thumbnail
    :rtype: path like
    """
    thumbnail_target = get_thumbnail_path(f"{map_id}_{size}x{size}.jpg")
    thumbnail_target = run_process_thumbnail(
        base_image_path, thumbnail_target, size, size, force=True
    )

    return TEMPLATE_PUBLIC_THUMBNAIL_URL.format(os.path.basename(thumbnail_target))


def generate_zoomify(base_image_path, map_id):
    """
    Generates zoomify tiles from a specific base_image.

    :param base_image_path: Path to the base image
    :type base_image_path: path like
    :param map_id: Map Id
    :type map_id: int
    :result: Public url of the thumbnail
    :rtype: path like
    """
    # in case the urls in metadata do not exist or in case they are hosted on this system update them
    zoomify_target = get_zoomify_path(str(map_id))
    zoomify_target = run_process_zoomify_tiles(
        base_image_path, zoomify_target, force=True
    )
    return TEMPLATE_PUBLIC_ZOOMIFY_URL.format(os.path.basename(zoomify_target))


def _get_base_url(url):
    """
    Returns the base of a path
    :param url: Url for which the base will be determined
    :type url: str
    """
    scheme, location, *rest = urlsplit(url)
    return urlunsplit((scheme, location, "", "", ""))


def _get_defined_keys(obj, keys):
    result = {}
    for key in keys:
        if key in obj and obj[key] is not None:
            result[key] = obj[key]
    return result


def join_existing_metadata_with_updates(map_id, metadata_updates, dbsession):
    """
    Joins metadata updates with the base metadata retrieved from the db.

    :param map_id: Map Id
    :type map_id: int
    :param metadata_updates: Updates applied to the metadata
    :type metadata_updates: dict
    :param dbsession: Database session
    :type dbsession: sqlalchemy.orm.session.Session
    :result: Merged dicts of the metadata
    :rtype: dict
    """
    metadata_obj = Metadata.by_map_id(map_id, dbsession)
    metadata = without_keys(
        metadata_obj.__dict__,
        ["raw_map_id", "_sa_instance_state", "time_of_publication"],
    )
    metadata = {
        **metadata,
        **_get_defined_keys(
            RawMap.by_id(map_id, dbsession).__dict__,
            ["map_type", "default_crs", "map_scale"],
        ),
        **{"time_of_publication": metadata_obj.time_of_publication.isoformat()},
    }
    return {**metadata, **metadata_updates}


def _reset_georef_state_for_map(map_id, dbsession):
    """
    Resets the georef state for a specific RawMap.

    :param map_id: Map Id
    :type map_id: int
    :param dbsession: Database session
    :type dbsession: sqlalchemy.orm.session.Session
    """
    georef_map_object = GeorefMap.by_raw_map_id(map_id, dbsession)

    # remove georef map from file system
    if georef_map_object is not None:
        georef_path = georef_map_object.get_abs_path()
        remove_if_exists(georef_path)

        # remove georef map from db
        dbsession.delete(georef_map_object)

        # Delete all related transformations
        stmt = delete(Transformation).where(Transformation.raw_map_id == map_id)
        dbsession.execute(stmt)


def _should_generate_files(metadata, metadata_updates, key, base_url, is_file_updated):
    """
    Determines whether a specific link has to be updated and the corresponding files have to be generated.

    :param metadata: Base metadata
    :type metadata: dict
    :param metadata_updates: Updates applied to the metadata
    :type metadata_updates: dict
    :param key: Key in metadata
    :type key: string
    :param is_file_updated: switch determining if the file has been updated
    :param is_file_updated: bool
    :result: Information if files have to be updated
    :rtype: bool
    """

    # in case the field is undefined, a file has to be generated no matter what
    if metadata[key] is None:
        return True

    is_internal_url = metadata[key].startswith(base_url)

    if key in metadata_updates:
        # in case the link was updated and its null or an internal url => regenerate file
        return metadata_updates[key] is None or is_internal_url
    else:
        # in case the link was not updated, check if the file was updated and if it is an internal url
        return is_file_updated and is_internal_url
