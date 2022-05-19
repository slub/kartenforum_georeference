#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 09.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import traceback
import logging
from jsonschema import validate
import json
import uuid
from datetime import datetime
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPInternalServerError, HTTPBadRequest, HTTPNotFound
from georeference.models.map_view import MapView
from georeference.settings import GLOBAL_ERROR_MESSAGE
from georeference.schema.map_view import map_view_requestSchema

LOGGER = logging.getLogger(__name__)


@view_config(route_name='map_view', renderer='json')
def GET_mapview_for_id(request):
    """ Endpoint for accessing map views for a given id of a map view.

    :param map_view_id: Id of the mapView object
    :type map_view_id: int
    :result: JSON object describing the map object
    :rtype: {{
        map_view_json: map_view_schema
    }}
    """
    try:
        if request.method != 'GET' or request.matchdict['map_view_id'] == None:
            return HTTPBadRequest('Missing map_view_id')

        # query mapView object
        map_view_id = request.matchdict['map_view_id']
        map_obj = MapView.by_public_id(map_view_id, request.dbsession)

        if map_obj is None:
            return HTTPNotFound("The requested map view does not exist.")

        # Build basic json response
        response_obj = {
            'map_view_json': map_obj.map_view_json,
        }

        # update metadata
        MapView.query_by_public_id(map_view_id, request.dbsession).update(
            {MapView.last_request: datetime.now().isoformat(), MapView.request_count: map_obj.request_count + 1})
        request.dbsession.flush()

        return response_obj
    except Exception as e:
        LOGGER.error('Error while trying to return a GET map_view request')
        LOGGER.error(e)
        LOGGER.error(traceback.format_exc())
        raise HTTPInternalServerError(GLOBAL_ERROR_MESSAGE)


@view_config(route_name='map_view', renderer='json', request_method='POST', accept='application/json')
def POST_mapview(request):
    """ Endpoint to POST a new mapView

    :param json_body: Json object containing the parameters
    :type json_body: {{
        user_id: str,
        map_view_json: map_view_schema,
    }}
    :result: JSON object describing the map object
    :rtype: {{
        map_view_id: int,
    }}
    """
    try:
        if request.method != 'POST':
            return HTTPBadRequest('The endpoint only supports "POST" requests.')

        # Validate the request
        try:
            validate(request.json_body, map_view_requestSchema)
        except Exception as e:
            LOGGER.error(e)
            return HTTPBadRequest("Invalid request object at POST request")

        map_view_json = request.json_body['map_view_json']
        user_id = request.json_body['user_id']
        submitted = datetime.now().isoformat()
        public_id = str(uuid.uuid4())

        # if the id is not unique, regenerate public_id
        while MapView.query_by_public_id(public_id, request.dbsession).count() > 0:
            public_id = str(uuid.uuid4())

        # Save to MapView table
        new_map_view = MapView(
            map_view_json=json.dumps(map_view_json),
            last_request=None,
            request_count=0,
            submitted=submitted,
            user_id=user_id,
            public_id=public_id
        )
        request.dbsession.add(new_map_view)
        request.dbsession.flush()

        return {
            'map_view_id': new_map_view.public_id,
        }
    except Exception as e:
        LOGGER.error('Error while trying to process POST request')
        LOGGER.error(e)
        LOGGER.error(traceback.format_exc())
        raise HTTPInternalServerError(GLOBAL_ERROR_MESSAGE)
