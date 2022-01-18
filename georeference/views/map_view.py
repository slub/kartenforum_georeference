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

from datetime import datetime
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPInternalServerError, HTTPBadRequest
from georeference.utils.parser import toInt
from georeference.models.map_view import MapView
from georeference.settings import GLOBAL_ERROR_MESSAGE
from georeference.utils.parser import toPublicOAI, fromPublicOAI
from georeference.schema.map_view import map_view_schema

LOGGER = logging.getLogger(__name__)


@view_config(route_name='map_views', renderer='json')
def GET_MapViewById(request):
    """ Endpoint for accessing map views for a given id of a map view.

    :param map_id: Id of the map object
    :type map_id: int
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
        if request.method != 'GET' or request.matchdict['map_view_id'] == None:
            return HTTPBadRequest('Missing map_view_id')

        # query map object and metadata
        map_view_id = toInt(fromPublicOAI(request.matchdict['map_view_id']))
        mapObj = MapView.byId(map_view_id, request.dbsession)

        # Building basic json response
        responseObj = {
            'map_view_json': mapObj.map_view_json,
        }

        return responseObj
    except Exception as e:
        LOGGER.error('Error while trying to return a GET map_view request')
        LOGGER.error(e)
        LOGGER.error(traceback.format_exc())
        raise HTTPInternalServerError(GLOBAL_ERROR_MESSAGE)


@view_config(route_name='map_views', renderer='json', request_method='POST', accept='application/json')
def POST_TransformationForMapId(request):
    """ Endpoint for POST a new transformation for a given id of an original map and creates a job for signaling the daemon
        to process it.

    :param json_body: Json object containing the parameters
    :type json_body: {{
        map_view_json: str,
        user_id: str,
    }}
    :result: JSON object describing the map object
    :rtype: {{
        map_view_id: int,
    }}
    """
    try:
        if request.method != 'POST':
            return HTTPBadRequest('The endpoint only supports "POST" requests.')

        map_view_json = request.json_body['map_view_json']
        userId = request.json_body['user_id']
        submitted = datetime.now().isoformat()

        validate(map_view_json, map_view_schema)

        # Save to transformations
        newMapView = MapView(
            map_view_json=json.dumps(map_view_json),
            last_request=None,
            request_count=0,
            submitted=submitted,
            user_id=userId,
        )
        request.dbsession.add(newMapView)
        request.dbsession.flush()

        return {
            'map_view_id': newMapView.id,
        }
    except Exception as e:
        LOGGER.error('Error while trying to process POST request')
        LOGGER.error(e)
        LOGGER.error(traceback.format_exc())
        raise HTTPInternalServerError(GLOBAL_ERROR_MESSAGE)