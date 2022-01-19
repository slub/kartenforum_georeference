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
from georeference.utils.parser import toInt
from georeference.models.map_view import MapView
from georeference.settings import GLOBAL_ERROR_MESSAGE
from georeference.utils.parser import toPublicOAI, fromPublicOAI
from georeference.schema.map_view import map_view_schema

LOGGER = logging.getLogger(__name__)


@view_config(route_name='map_view', renderer='json')
def GET_MapViewById(request):
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
        mapObj = MapView.byPublicId(map_view_id, request.dbsession)

        if mapObj is None:
            return HTTPNotFound("The requested map view does not exist.")

        # Build basic json response
        responseObj = {
            'map_view_json': mapObj.map_view_json,
        }

        # update metadata
        MapView.queryByPublicId(map_view_id, request.dbsession).update({MapView.last_request: datetime.now().isoformat(), MapView.request_count: mapObj.request_count + 1})
        request.dbsession.flush()

        return responseObj
    except Exception as e:
        LOGGER.error('Error while trying to return a GET map_view request')
        LOGGER.error(e)
        LOGGER.error(traceback.format_exc())
        raise HTTPInternalServerError(GLOBAL_ERROR_MESSAGE)


@view_config(route_name='map_view', renderer='json', request_method='POST', accept='application/json')
def POST_MapView(request):
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

        # Define the request schema for this endpoint
        request_schema = {
            "type": "object",
            "properties": {
                "user_id": { "type": "string"},
                "map_view_json": map_view_schema
            },
            "required": ["map_view_json", "user_id"],
            "additionalProperties": False
        }


        # Validate the request
        try:
            validate(request.json_body, request_schema)
        except Exception as e:
            LOGGER.error(e)
            return HTTPBadRequest("Invalid request object at POST request")

        map_view_json = request.json_body['map_view_json']
        userId = request.json_body['user_id']
        submitted = datetime.now().isoformat()
        public_id = str(uuid.uuid4())

        # if the id is not unique, regenerate public_id
        while MapView.queryByPublicId(public_id, request.dbsession).count() > 0:
            public_id = str(uuid.uuid4())
        

        # Save to MapView table
        newMapView = MapView(
            map_view_json=json.dumps(map_view_json),
            last_request=None,
            request_count=0,
            submitted=submitted,
            user_id=userId,
            public_id=public_id
        )
        request.dbsession.add(newMapView)
        request.dbsession.flush()

        return {
            'map_view_id': newMapView.public_id,
        }
    except Exception as e:
        LOGGER.error('Error while trying to process POST request')
        LOGGER.error(e)
        LOGGER.error(traceback.format_exc())
        raise HTTPInternalServerError(GLOBAL_ERROR_MESSAGE)