#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 06.10.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import traceback
import logging
import os
import json
from pyramid.view import view_config
from sqlalchemy import desc
from pyramid.httpexceptions import HTTPInternalServerError, HTTPBadRequest
from georeference.models.transformations import Transformation
from georeference.models.metadata import Metadata
from georeference.models.original_maps import OriginalMap
from georeference.settings import GLOBAL_ERROR_MESSAGE

# For correct resolving of the paths we use derive the base_path of the file
BASE_PATH = os.path.dirname(os.path.realpath(__file__))

# Initialize the logger
LOGGER = logging.getLogger(__name__)

@view_config(route_name='transformations_users', renderer='json', request_method='GET', accept='application/json')
def GET_TransformationsForUserId(request):
    """ Endpoint for accessing all transformation created by a given user.

    :param user_id: Id of the user
    :type user_id: int
    :result: JSON array of georeference process enhanced with further metadata
    :rtype: {{
      user_id: str,
      items: {
        map_id: int,
        metadata: {
          time_publish: str,
          title: str,
        }
        transformation: {
            transformation_id: int,
            clip: GeoJSON,
            params: dict,
            submitted: str,
            overwrites: int,
            user_id: str,
        }
      }[],
    }}
    """
    try:
        if request.method != 'GET':
            return HTTPBadRequest('The endpoint only supports "GET" requests.')

        userId = request.matchdict['user_id']
        if userId == None:
            return HTTPBadRequest('Missing user_id.')

        # Create default response
        responseObj = {
            'user_id': userId,
            'items': []
        }

        # Return process for the georeference endpoint
        queryTransformations = request.dbsession.query(Transformation, OriginalMap, Metadata)\
            .join(OriginalMap, Transformation.original_map_id == OriginalMap.id)\
            .join(Metadata, Transformation.original_map_id == Metadata.mapid)\
            .filter(Transformation.user_id == userId)\
            .order_by(desc(Transformation.submitted))

        for record in queryTransformations:
            transformationObj = record[0]
            mapObj = record[1]
            metadataObj = record[2]
            responseObj['items'].append({
                'map_id': mapObj.id,
                'metadata': {
                    'time_publish': str(metadataObj.timepublish),
                    'title': metadataObj.title,
                },
                'transformation': {
                    'transformation_id': transformationObj.id,
                    'clip': json.loads(transformationObj.clip),
                    'params': transformationObj.getParamsAsDict(),
                    'submitted': str(transformationObj.submitted),
                    'overwrites': transformationObj.overwrites,
                    'user_id': transformationObj.user_id
                }
            })
        return responseObj

    except Exception as e:
        LOGGER.error('Error while trying to process GET request')
        LOGGER.error(e)
        LOGGER.error(traceback.format_exc())
        raise HTTPInternalServerError(GLOBAL_ERROR_MESSAGE)