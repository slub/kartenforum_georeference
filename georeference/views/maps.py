#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by nicolas.looschen@pikobytes.de on 20.04.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import json
import logging
import os
import shutil
import traceback
import uuid
from datetime import datetime
from jsonschema import validate
from osgeo import gdal

from pyramid.response import Response
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPInternalServerError, HTTPBadRequest

from georeference.jobs.process_update_maps import join_existing_metadata_with_updates
from georeference.utils.parser import to_int
from georeference.models.georef_maps import GeorefMap
from georeference.models.jobs import EnumJobType, EnumJobState, Job
from georeference.models.metadata import Metadata
from georeference.models.raw_maps import RawMap
from georeference.settings import GLOBAL_ERROR_MESSAGE, PATH_TMP_NEW_MAP_ROOT
from georeference.utils.parser import to_public_oai, from_public_oai
from georeference.schema.maps import maps_schema
from georeference.utils.utils import without_keys

LOGGER = logging.getLogger(__name__)


@view_config(route_name='maps', renderer='json', request_method='GET')
def GET_map_for_map_id(request):
    """
    Endpoint for accessing map metadata for a given id of an original map.

    :param: request - pyramid request object
    :result: JSON object describing the map object
    :rtype: {{
      file_name: str,
      transformation_id: int | None,
      map_id: int,
      map_type: str,
      title_long: str,
      title_short: str,
      zoomify_url: str,
    }}
    """
    try:
        if request.matchdict['map_id'] is None:
            return HTTPBadRequest('Missing map_id')

        # query map object and metadata
        map_id = to_int(from_public_oai(request.matchdict['map_id']))
        map_obj = RawMap.by_id(map_id, request.dbsession)
        metadata_obj = Metadata.by_map_id(map_obj.id, request.dbsession).__dict__

        # Building basic json response
        response_obj = without_keys(metadata_obj, ["raw_map_id", "_sa_instance_state"])

        # add in fields from map_obj
        response_obj["file_name"] = map_obj.file_name
        response_obj["map_id"] = to_public_oai(map_obj.id)
        response_obj["transformation_id"] = None
        response_obj["map_type"] = map_obj.map_type

        # In case there is currently an active georeference process for the map return the id
        georef_map_obj = GeorefMap.by_raw_map_id(map_obj.id, request.dbsession)
        if georef_map_obj is not None:
            response_obj['transformation_id'] = georef_map_obj.transformation_id

        return response_obj
    except Exception as e:
        _log_error(e, 'Error while trying to return a GET maps request')
        raise HTTPInternalServerError(GLOBAL_ERROR_MESSAGE)


@view_config(route_name='maps', request_method='DELETE')
def DELETE_map_for_map_id(request):
    """
    Endpoint for posting new maps.

    :param: request - pyramid request object
    :result: 200 if the deletion was successful
    """
    try:
        if request.matchdict['map_id'] is None or request.matchdict['map_id'] == '':
            return HTTPBadRequest('Path parameter map_id is required for the delete operation')

        try:
            map_id = to_int(from_public_oai(request.matchdict['map_id']))
        except Exception as e:
            err_message = 'Invalid map_id.'
            _log_error(e, err_message)
            return HTTPBadRequest(err_message)

        # check if a map with the supplied id exists
        err = _exists_map_id(request, map_id)
        if err is not None:
            return err

        user_id = _get_user_id_from_request(request)

        delete_job = Job(
            description=json.dumps({"map_id": map_id}),
            type=EnumJobType.MAPS_DELETE.value,
            state=EnumJobState.NOT_STARTED.value,
            submitted=datetime.now().isoformat(),
            user_id=user_id
        )

        request.dbsession.add(delete_job)
        request.dbsession.flush()

        return Response()

    except Exception as e:
        _log_error(e, 'Error while trying to handle a DELETE maps request')
        raise HTTPInternalServerError(GLOBAL_ERROR_MESSAGE)


@view_config(route_name='maps', renderer='json', request_method='POST', accept='multipart/form-data')
def POST_map(request):
    """
    Endpoint for posting new maps.

    :param: request - pyramid request object
    :result: Json object containing the map_id of the created/modified map.
        :rtype: {{
      map_id: str,
    }}
    """
    try:
        # if no map_id is present => add new map
        is_create = request.matchdict['map_id'] is None or request.matchdict['map_id'] == ''
        if is_create:
            return _handle_map_create(request)
        else:
            return _handle_map_update(request)

    except Exception as e:
        _log_error(e, 'Error while trying to handle a POST maps request')
        raise HTTPInternalServerError(GLOBAL_ERROR_MESSAGE)


def _add_job(request, metadata, file_path, upload_file_name, map_id, user_id='system', is_update=False):
    """
    Handles the job creation for adding/updating maps, based on the supplied values

    :param: request - pyramid request object
    :param: metadata - uploaded metadata as json object
    :param: file_path - path to the file in the directory system
    :param: upload_file_name - original name the file was uploaded with
    :param: map_id - id of the map
    :param: user_id - id of the user
    :param: is_update - flag if an existing map was updated or a new map was created
    """
    create_job = Job(
        description=json.dumps({
            'map_id': map_id,
            'metadata': metadata,
            'file': file_path,
            'original_file_name': upload_file_name
        }, ensure_ascii=False),
        type=EnumJobType.MAPS_UPDATE.value if is_update else EnumJobType.MAPS_CREATE.value,
        state=EnumJobState.NOT_STARTED.value,
        submitted=datetime.now().isoformat(),
        user_id=user_id
    )

    request.dbsession.add(create_job)
    request.dbsession.flush()


def _exists_map_id(request, map_id):
    """
    Checks if the supplied map_id exists in the database.

    :param: request - pyramid request object
    :param: map_id - id of the map
    """
    (exists,), *rest = request.dbsession.execute(
        f'SELECT CASE WHEN EXISTS (SELECT * FROM raw_maps WHERE id = {map_id}) THEN CAST (1 AS BIT) ELSE CAST (0 AS BIT) END')

    if exists == '0':
        return HTTPBadRequest('There exists no map with the supplied id.')


def _get_user_id_from_request(request):
    """
    Gets a valid user_id from a request object.

    :param: request - pyramid request object
    """
    user_id = request.params.get('user_id')
    return 'system' if user_id is None or user_id == "" else user_id


def _handle_map_create(request):
    """
    Handles a request for adding a map.

    Expects metadata and file as input.

    :param: request - pyramid request object
    """
    # check if metadata and file field are present
    if 'metadata' not in request.POST:
        return HTTPBadRequest('The metadata form field is required.')

    if 'file' not in request.POST:
        return HTTPBadRequest('The file form field is required.')

    # validate metadata
    metadata = json.loads(request.POST['metadata'])
    err = validate_metadata(metadata)

    if err is not None:
        return err

    file = request.POST['file'].file

    file_path = _write_file(file)

    err = _validate_file(file_path)

    if err is not None:
        # make sure the new file is delete afterwards
        os.remove(file_path)
        return err

    # Get map id from sequence (which will be assigned to the map, when its written to the db)
    (map_id,), *rest = request.dbsession.execute('SELECT nextval(\'public.raw_maps_id_seq\') AS map_id')

    _add_job(request, metadata, file_path, request.POST['file'].filename, map_id, _get_user_id_from_request(request),
             False)

    return {'map_id': to_public_oai(map_id)}


def _handle_map_update(request):
    """
    Handles a request for updating a map.

    Expects metadata, file or both as input.

    :param: request - pyramid request object
    """
    try:
        map_id = to_int(from_public_oai(request.matchdict['map_id']))
    except Exception as e:
        err_message = 'Invalid map_id.'
        _log_error(e, err_message)
        return HTTPBadRequest(err_message)

    err = _exists_map_id(request, map_id)
    if err is not None:
        return err

    if 'metadata' not in request.POST and 'file' not in request.POST:
        return HTTPBadRequest('Either the metadata form field or the file form field is required.')

    metadata = None
    file_path = None

    if 'metadata' in request.POST and request.POST['metadata'] != '':
        metadata_updates = json.loads(request.POST['metadata'])
        metadata = join_existing_metadata_with_updates(map_id, metadata_updates, request.dbsession)
        err = validate_metadata(metadata)
        if err is not None:
            return err

    if 'file' in request.POST:
        file = request.POST['file'].file
        file_path = _write_file(file)
        err = _validate_file(file_path)

        if err is not None:
            # make sure the new file is delete afterwards
            os.remove(file_path)
            return err

    _add_job(request, metadata, file_path, None if file_path is None else request.POST['file'].filename, map_id,
             _get_user_id_from_request(request), True)

    return {'map_id': to_public_oai(map_id)}


def _log_error(e, message):
    """
    Forward an error to the logger

    :param: e - error that triggered the logger invocation
    :param: message - a custom message supplied to the logger
    """
    LOGGER.error(message)
    LOGGER.error(e)
    LOGGER.error(traceback.format_exc())


def _validate_file(path_to_file):
    """
    Check if the file is really a geotiff file.
    :param path_to_file: file path
    :type path_to_file: str
    """
    try:
        gtif = gdal.Open(path_to_file)
        driver_name = None if gtif is None else gtif.GetDriver().ShortName
        if driver_name != "GTiff":
            LOGGER.error("Invalid file format.")
            raise RuntimeError()
    except RuntimeError as e:
        err_message = 'Invalid file object at POST request.'
        _log_error(e, err_message)
        return HTTPBadRequest(err_message)


def validate_metadata(metadata):
    """
    Validate the maps metadata

    :param: metadata - uploaded metadata as json object
    """
    try:
        LOGGER.debug(f'Validate metadata {metadata} for map.')
        validate(metadata, maps_schema)
    except Exception as e:
        err_message = 'Invalid metadata object at POST request.'
        _log_error(e, err_message)
        return HTTPBadRequest(err_message)


def _write_file(file):
    """
    Writes an input file to a configurable directory with a generated unique name.

    Expects a valid tif file.

    :param: file - a binary file uploaded by the user (tif)
    """
    unique_id = str(uuid.uuid4())

    # move file to directory (https://docs.pylonsproject.org/projects/pyramid-cookbook/en/latest/forms/file_uploads.html)
    file_path = os.path.join(PATH_TMP_NEW_MAP_ROOT, f'{unique_id}.tif')

    # use tmp file to prevent access to incomplete files
    tmp_file_path = file_path + '~'

    file.seek(0)
    with open(tmp_file_path, 'wb') as output_file:
        shutil.copyfileobj(file, output_file)

    os.rename(tmp_file_path, file_path)
    return file_path
