#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 21.06.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import json
import logging
from datetime import datetime
from jsonschema import validate
from jsonschema.exceptions import ValidationError

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPInternalServerError, HTTPBadRequest, HTTPNotFound

from georeference.models.jobs import Job, EnumJobType, EnumJobState
from georeference.models.mosaic_maps import MosaicMap
from georeference.schema.mosaic_map import mosaic_map_schema_write
from georeference.utils.logging import log_error
from georeference.utils.parser import from_public_mosaic_map_id
from georeference.settings import GLOBAL_ERROR_MESSAGE
from georeference.utils.parser import to_public_map_id, to_public_mosaic_map_id, from_public_map_id
from georeference.utils.utils import without_keys

LOGGER = logging.getLogger(__name__)


@view_config(route_name='mosaic_map', renderer='json', request_method='GET')
def GET_mosaic_map(request):
    """
    Endpoint for GET mosaic_map data.

    :param request: Pyramid request object
    :type request: pyramid.request
    :result: JSON object describing the mosaic map object
    :rtype: Object according to the mosaic_map_schema_read
    """
    try:
        # Query data
        public_mosaic_map_id = request.matchdict['mosaic_map_id']
        mosaic_map_obj = MosaicMap.by_id(from_public_mosaic_map_id(public_mosaic_map_id), request.dbsession)

        if mosaic_map_obj is None:
            return HTTPNotFound(f'Could not find mosaic_map for id {public_mosaic_map_id}')

        return _create_mosaic_maps_response(mosaic_map_obj)
    except Exception as e:
        log_error(e, 'Error while trying to handle a GET mosaic map request')
        raise HTTPInternalServerError(GLOBAL_ERROR_MESSAGE)


@view_config(route_name='mosaic_map', renderer='json', request_method='DELETE')
def DELETE_mosaic_map(request):
    """
    Endpoint for DELETE mosaic_map data.

    :param request: Pyramid request object
    :type request: pyramid.request
    :result: JSON object with status "ok"
    :rtype: {{
        "status": string
    }}
    """
    try:
        # Query data
        public_mosaic_map_id = request.matchdict['mosaic_map_id']
        mosaic_map_obj = MosaicMap.by_id(from_public_mosaic_map_id(public_mosaic_map_id), request.dbsession)

        if mosaic_map_obj is None:
            return HTTPNotFound(f'Could not find mosaic_map for id {public_mosaic_map_id}')

        # Add job for DELETE the service
        _add_job(
            request.dbsession,
            mosaic_map_obj.id,
            mosaic_map_obj.name,
            is_delete=True
        )

        request.dbsession.delete(mosaic_map_obj)
        request.dbsession.flush()

        return { 'status': 'ok' }
    except Exception as e:
        log_error(e, 'Error while trying to handle a DELETE mosaic map request')
        raise HTTPInternalServerError(GLOBAL_ERROR_MESSAGE)


@view_config(route_name='mosaic_maps', renderer='json', request_method='POST', accept='application/json')
def POST_mosaic_maps(request):
    """
    Endpoint for POST mosaic_map data. Supports creation and updating.

    :param request: Pyramid request object
    :type request: pyramid.request
    :result: JSON object describing the mosaic map object
    :rtype: Object according to the mosaic_map_schema_read
    """
    try:
        return _handle_mosaic_map_create(
            request.json_body,
            request.dbsession
        )
    except ValidationError as e:
        err_msg = 'Error while tyring to validate the POST data for the mosaic map request.'
        raise HTTPBadRequest(f'{err_msg}{e.message}')
    except Exception as e:
        err_msg = 'Error while trying to handle a POST (create) mosaic map request'
        log_error(e, err_msg)
        raise HTTPInternalServerError(f'{err_msg}{e.message}')

@view_config(route_name='mosaic_map', renderer='json', request_method='POST', accept='application/json')
def POST_mosaic_map_update(request):
    """
    Endpoint for POST mosaic_map data. Supports creation and updating.

    :param request: Pyramid request object
    :type request: pyramid.request
    :result: JSON object describing the mosaic map object
    :rtype: Object according to the mosaic_map_schema_read
    """
    try:
        return _handle_mosaic_map_update(
            request.matchdict['mosaic_map_id'],
            request.json_body,
            request.dbsession
        )
    except ValidationError as e:
        err_msg = 'Error while tyring to validate the POST data for the mosaic map request.'
        raise HTTPBadRequest(f'{err_msg}{e.message}')
    except Exception as e:
        err_msg = 'Error while trying to handle a POST (update) mosaic map request'
        log_error(e, err_msg)
        raise HTTPInternalServerError(f'{err_msg}{e.message}')

@view_config(route_name='mosaic_map_refresh', renderer='json', request_method='POST')
def POST_mosaic_map_refresh(request):
    """
    Endpoint for POST a refresh signal for mosaic_map. It triggers the creation of CREATE/UPDATE job for the mosaic_map.

    :param request: Pyramid request object
    :type request: pyramid.request
    :result: JSON object with status "ok"
    :rtype: {{
        "status": string
    }}
    """
    try:
        # Check if the mosaic map exists
        public_mosaic_map_id = request.matchdict['mosaic_map_id']
        mosaic_map_obj = MosaicMap.by_id(from_public_mosaic_map_id(public_mosaic_map_id), request.dbsession)

        if mosaic_map_obj is None:
            return HTTPNotFound(f'Could not find mosaic_map for id {public_mosaic_map_id}')

        # Add job for CREATE/UPDATE the service
        _add_job(
            request.dbsession,
            mosaic_map_obj.id,
            mosaic_map_obj.name
        )

        return {'status': 'ok'}
    except Exception as e:
        err_msg = 'Error while trying to handle a POST refresh mosaic map request'
        log_error(e, err_msg)
        raise HTTPInternalServerError(f'{err_msg}{e.message}')


def _handle_mosaic_map_create(json_body, dbsession):
    """
    Handles a request for adding a mosaic map.

    :param json_body: Json object containing the mosaic map
    :type json_body: mosaic_map_schema_write
    :param dbsession: Database session
    :type dbsession: sqlalchemy.orm.session.Session
    :result: JSON object describing the mosaic map object
    :rtype: Object according to the mosaic_map_schema_read
    """

    # Validate the request and check if it is valid
    validate(json_body, mosaic_map_schema_write)

    # Save mosaic map in database
    mosaic_map_obj = MosaicMap(
        name=json_body["name"],
        raw_map_ids=map(lambda x: from_public_map_id(x), json_body["raw_map_ids"]),
        title=json_body["title"],
        title_short=json_body["title_short"],
        time_of_publication=json_body["time_of_publication"],
        link_thumb=json_body["link_thumb"],
        map_scale=json_body["map_scale"],
        last_change=datetime.now().isoformat(),
        last_service_update=None,
        last_overview_update=None
    )
    dbsession.add(mosaic_map_obj)
    dbsession.flush()

    # Add job for CREATE/UPDATE the service
    _add_job(
        dbsession,
        mosaic_map_obj.id,
        mosaic_map_obj.name
    )

    # Create the response and return it
    return _create_mosaic_maps_response(mosaic_map_obj)


def _handle_mosaic_map_update(public_mosaic_map_id, json_body, dbsession):
    """
    Handles a request for adding a mosaic map.

    :param public_mosaic_map_id: Public mosaic map id
    :type public_mosaic_map_id: string
    :param json_body: Json object containing the mosaic map
    :type json_body: mosaic_map_schema_write
    :param dbsession: Database session
    :type dbsession: sqlalchemy.orm.session.Session
    :result: JSON object describing the mosaic map object
    :rtype: Object according to the mosaic_map_schema_read
    """

    # Validate the request and check if it is valid
    validate(json_body, mosaic_map_schema_write)

    # Query data
    mosaic_map_obj = MosaicMap.by_id(from_public_mosaic_map_id(public_mosaic_map_id), dbsession)
    if mosaic_map_obj is None:
        return HTTPNotFound(f'Could not find mosaic_map for id {public_mosaic_map_id}')

    # Update the mosaic map
    mosaic_map_obj.name = json_body["name"]
    mosaic_map_obj.raw_map_ids = map(lambda x: from_public_map_id(x), json_body["raw_map_ids"])
    mosaic_map_obj.title = json_body["title"]
    mosaic_map_obj.title_short = json_body["title_short"]
    mosaic_map_obj.time_of_publication = json_body["time_of_publication"]
    mosaic_map_obj.link_thumb = json_body["link_thumb"]
    mosaic_map_obj.map_scale = json_body["map_scale"]
    mosaic_map_obj.last_change = datetime.now().isoformat()
    dbsession.flush()

    # Add job for CREATE/UPDATE the service
    _add_job(
        dbsession,
        mosaic_map_obj.id,
        mosaic_map_obj.name
    )

    # Create the response and return it
    return _create_mosaic_maps_response(mosaic_map_obj)


def _add_job(dbsession, mosaic_map_id, service_name, user_id='system', is_delete=False):
    """
    Handles the job creation for adding/updating maps, based on the supplied values

    :param dbsession: Database session
    :type dbsession: sqlalchemy.orm.session.Session
    :param mosaic_map_id: Id of the mosaic_map
    :type mosaic_map_id: int
    :param service_name: Name of the service
    :type service_name: str
    :param user_id: id of the user
    :type user_id: str
    :param is_delete: Flag if an existing map was updated or a new map was created
    :type is_delete: bool
    """
    create_job = Job(
        description=json.dumps({
            'mosaic_map_id': mosaic_map_id,
            'service_name': service_name,
        }, ensure_ascii=False),
        type=EnumJobType.MOSAIC_MAP_DELETE.value if is_delete else EnumJobType.MOSAIC_MAP_CREATE.value,
        state=EnumJobState.NOT_STARTED.value,
        submitted=datetime.now().isoformat(),
        user_id=user_id
    )

    dbsession.add(create_job)
    dbsession.flush()

def _create_mosaic_maps_response(mosaic_map_obj):
    """ Creates a mosaic maps object.

    :param mosaic_map_obj: MosaicMap object
    :type mosaic_map_obj: georeference.models.mosaic_maps.MosaicMap
    :result: JSON object describing the mosaic map object
    :rtype: Object according to the mosaic_map_schema_read
    """

    # Create response_obj and map the raw_map_ids to public raw_map_ids
    response_obj = without_keys(mosaic_map_obj.__dict__, ['_sa_instance_state'])
    response_obj['id'] = to_public_mosaic_map_id(response_obj['id'])
    response_obj['raw_map_ids'] = list(map(lambda x: to_public_map_id(x), response_obj['raw_map_ids']))
    response_obj['last_service_update'] = response_obj[
        'last_service_update'] if 'last_service_update' in response_obj else None
    response_obj['last_overview_update'] = response_obj[
        'last_overview_update'] if 'last_overview_update' in response_obj else None
    return response_obj