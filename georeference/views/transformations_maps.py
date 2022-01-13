#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 09.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import traceback
import logging
import json
import os
from datetime import datetime
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPInternalServerError, HTTPBadRequest, HTTPNotFound
from georeference.utils.parser import toInt
from georeference.utils.validations import isValidTransformationRequest
from georeference.models.transformations import Transformation, ValidationValues
from georeference.models.original_maps import OriginalMap
from georeference.models.georef_maps import GeorefMap
from georeference.models.metadata import Metadata
from georeference.models.jobs import Job, TaskValues
from georeference.settings import GLOBAL_ERROR_MESSAGE
from georeference.utils.parser import fromPublicOAI, toPublicOAI
from georeference.utils.api import toTransformationResponse

# For correct resolving of the paths we use derive the base_path of the file
BASE_PATH = os.path.dirname(os.path.realpath(__file__))

# Initialize the logger
LOGGER = logging.getLogger(__name__)

@view_config(route_name='transformations_map', renderer='json', request_method='GET')
def GET_TransformationsForMapId(request):
    """ Endpoint for getting a list of all transformations for a given id of an original_map.

    :param map_id: Id of the original map object
    :type map_id: int
    :result: JSON object describing the map object
    :rtype: {{
      active_transformation_id: int,
      extent: Extent,
      default_srs: int,
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
      map_id: int,
      metadata: {
        time_publish: str,
        title: str,
      }
      pending_processes: boolean,
    }}
    """
    try:
        if request.method != 'GET':
            return HTTPBadRequest('The endpoint only supports "GET" requests.')

        if request.matchdict['map_id'] == None:
            return HTTPBadRequest('Missing map_id')

        # query map object and metadata
        mapId = toInt(fromPublicOAI(request.matchdict['map_id']))
        mapObj = OriginalMap.byId(mapId, request.dbsession)
        if mapObj is None:
            return HTTPBadRequest('There is no map object for the passed map id.')
        georefMapObj = GeorefMap.byOriginalMapId(mapObj.id, request.dbsession)
        metadataObj = Metadata.byId(mapObj.id, request.dbsession)

        # Create default response
        responseObj = {
            'active_transformation_id': georefMapObj.transformation_id if georefMapObj != None else None,
            'extent': json.loads(georefMapObj.extent) if georefMapObj != None else None,
            'default_srs': 'EPSG:%s' % mapObj.default_srs,
            'transformations': [],
            'map_id': toPublicOAI(mapObj.id),
            'metadata': {
                'time_publish': str(metadataObj.time_of_publication),
                'title': metadataObj.title,
            },
            'pending_jobs': Job.hasPendingJobsForMapId(request.dbsession, mapObj.id)
        }

        # Return process for the georeference endpoint
        returnAll = True if 'return_all' in request.params and request.params['return_all'].lower() == 'true' else False
        queryTransformations = request.dbsession.query(Transformation, GeorefMap) \
            .join(GeorefMap, Transformation.id == GeorefMap.transformation_id, isouter=True) \
            .filter(Transformation.original_map_id == mapObj.id)\
            .filter(Transformation.validation != ValidationValues.INVALID.value if returnAll == False else True == True)
        for record in queryTransformations:
            # Create a georeference process object
            responseObj['transformations'].append(
                toTransformationResponse(
                    record[0],
                    mapObj,
                    metadataObj,
                    True if record[1] != None else False
                )
            )

        return responseObj
    except Exception as e:
        LOGGER.error('Error while trying to process GET request')
        LOGGER.error(e)
        LOGGER.error(traceback.format_exc())
        raise HTTPInternalServerError(GLOBAL_ERROR_MESSAGE)

@view_config(route_name='transformations_map', renderer='json', request_method='POST', accept='application/json')
def POST_TransformationForMapId(request):
    """ Endpoint for POST a new transformation for a given id of an original map and creates a job for signaling the daemon
        to process it.

    :param map_id: Id of the map object
    :type map_id: int
    :param json_body: Json object containing the parameters
    :type json_body: {{
        clip: GeoJSON,
        params: *,
        overwrites: int,
        user_id: str,
    }}
    :result: JSON object describing the map object
    :rtype: {{
        transformation_id: int,
        job_id: int
    }}
    """
    try:
        # Validate request
        if request.method != 'POST':
            return HTTPBadRequest('The endpoint only supports "POST" requests.')
        if request.matchdict['map_id'] == None:
            return HTTPBadRequest('Missing map_id')

        # Validate input
        isValidRequest = isValidTransformationRequest(request.json_body)
        if isValidRequest['valid'] == False:
            return HTTPBadRequest(isValidRequest['error_msg'])

        # Check if original map exists for given id
        mapId = toInt(fromPublicOAI(request.matchdict['map_id']))
        mapObj = OriginalMap.byId(mapId, request.dbsession)
        if mapObj is None:
            return HTTPNotFound('Could not detect original map for passed map id.')

        clip = request.json_body['clip']
        params = request.json_body['params']
        overwrites = request.json_body['overwrites']
        userId = request.json_body['user_id']
        submitted = datetime.now().isoformat()

        # If overwrites == 0, we check if there is already a valid transformation registered for the original map id.
        hasTransformation = Transformation.hasTransformation(mapId, request.dbsession)
        if overwrites == 0 and hasTransformation:
            return HTTPBadRequest('It is forbidden to register a new transformation for an original map, which already has a transformation registered.')

        # Save to transformations
        newTransformation = Transformation(
            submitted=submitted,
            user_id=userId,
            params=json.dumps(params),
            clip=json.dumps(clip),
            validation=ValidationValues.MISSING.value,
            original_map_id=mapId,
            overwrites=overwrites,
            comment=None
        )
        request.dbsession.add(newTransformation)
        request.dbsession.flush()

        # Save to jobs
        newJob = Job(
            processed=False,
            task=json.dumps({
                'transformation_id': newTransformation.id
            }),
            task_name=TaskValues.TRANSFORMATION_PROCESS.value,
            submitted=submitted,
            user_id=userId,
            comment=None
        )
        request.dbsession.add(newJob)
        request.dbsession.flush()

        return {
            'transformation_id': newTransformation.id,
            'job_id': newJob.id,
            'points': int(len(params['gcps'])) * 5,
        }
    except Exception as e:
        LOGGER.error('Error while trying to process POST request')
        LOGGER.error(e)
        LOGGER.error(traceback.format_exc())
        raise HTTPInternalServerError(GLOBAL_ERROR_MESSAGE)



