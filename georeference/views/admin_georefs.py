#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 10.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import traceback
import logging
import os
from datetime import datetime
from pyramid.view import view_config
from sqlalchemy import desc
from sqlalchemy.sql.expression import or_
from pyramid.httpexceptions import HTTPInternalServerError, HTTPBadRequest, HTTPNotFound
from georeference.models.georeference_process import GeoreferenceProcess
from georeference.models.admin_jobs import AdminJobs
from georeference.models.metadata import Metadata
from georeference.utils.parser import toInt
from georeference.settings import GLOBAL_ERROR_MESSAGE
from georeference.settings import OAI_ID_PATTERN

# For correct resolving of the paths we use derive the base_path of the file
BASE_PATH = os.path.dirname(os.path.realpath(__file__))

# Initialize the logger
LOGGER = logging.getLogger(__name__)

@view_config(route_name='admin_georefs', renderer='json', request_method='GET', accept='application/json')
def getAdminGeorefs(request):
    """ Admin endpoint for querying different georefs process with further metadata. Expects the following url pattern:

        GET     {route_prefix}/admin/georefs?map_id={value}
        GET     {route_prefix}/admin/georefs?user_id={value}
        GET     {route_prefix}/admin/georefs?validation={value}
        GET     {route_prefix}/admin/georefs?pending={value}

    :param map_id: Id of the map object
    :type map_id: int
    :param user_id: Id of the user
    :type user_id: int
    :param validation: Validation value for a georef process
    :type validation: str
    :param pending: If set, returns all pending georeference processes
    :type pending: any
    :result: JSON array of georeference process enhanced with further metadata
    :rtype: {{
      georef: {
          clip_polygon: GeoJSON,
          georef_params: *,
          id: int,
          isActive: bool,
          processed: bool,
          timestamp: str,
          type: 'new' | 'update',
          validation_status: str,
          user_id: str,
      },
      metadata: {
        oai: str,
        time_publish: str,
        title: str,
      }
    }}
    """

    try:
        if request.method != 'GET':
            return HTTPBadRequest('The endpoint only supports "GET" requests.')

        # Try to query the data
        queryData = None

        # Generate response data via map_id
        if 'map_id' in request.params:
            queryData = request.dbsession.query(GeoreferenceProcess, Metadata)\
                .join(Metadata, GeoreferenceProcess.map_id == Metadata.mapid) \
                .filter(GeoreferenceProcess.map_id == toInt(request.params['map_id'])) \
                .order_by(desc(GeoreferenceProcess.id))

        # Generate response data via user_id
        elif 'user_id' in request.params:
            queryData = request.dbsession.query(GeoreferenceProcess, Metadata)\
                .join(Metadata, GeoreferenceProcess.map_id == Metadata.mapid) \
                .filter(GeoreferenceProcess.user_id == request.params['user_id']) \
                .order_by(desc(GeoreferenceProcess.id))

        # Generate response data via validation
        elif 'validation' in request.params:
            queryData = request.dbsession.query(GeoreferenceProcess, Metadata)\
                .join(Metadata, GeoreferenceProcess.map_id == Metadata.mapid) \
                .filter(GeoreferenceProcess.validation == request.params['validation']) \
                .order_by(desc(GeoreferenceProcess.id))

        # Generate response data via pending
        elif 'pending' in request.params:
            queryData = request.dbsession.query(GeoreferenceProcess, Metadata)\
                .join(Metadata, GeoreferenceProcess.map_id == Metadata.mapid) \
                .filter(or_(GeoreferenceProcess.validation == '', GeoreferenceProcess.validation == None)) \
                .order_by(desc(GeoreferenceProcess.id))

        if queryData == None:
            return HTTPBadRequest('Please pass values for one of the following query parameters: "map_id", "user_id", "pending", "validation"')
        else:
            response = []
            for record in queryData:
                georefObj = record[0]
                metadataObj = record[1]
                dict = {
                    'georef': {
                        'clip_polygon': georefObj.getClipAsGeoJSON(request.dbsession),
                        'georef_params': georefObj.getGeorefParamsAsDict(),
                        'id': georefObj.id,
                        'enabled': georefObj.enabled,
                        'processed': georefObj.processed,
                        'timestamp': str(georefObj.timestamp),
                        'type': georefObj.type,
                        'validation': georefObj.validation,
                        'user_id': georefObj.user_id
                    },
                    'metadata': {
                        'oai': OAI_ID_PATTERN % georefObj.map_id,
                        'time_publish': str(metadataObj.timepublish),
                        'title': metadataObj.title,
                    }
                }
                response.append(dict)

            return response
        return ""
    except Exception as e:
        LOGGER.error('Error while trying to process GET request')
        LOGGER.error(e)
        LOGGER.error(traceback.format_exc())
        raise HTTPInternalServerError(GLOBAL_ERROR_MESSAGE)

@view_config(route_name='admin_georefs', renderer='json', request_method='POST', accept='application/json')
def postAdminGeorefs(request):
    """ Admin endpoint for setting a georeference process validation status. Expects the following url pattern:

            POST     {route_prefix}/admin/georefs

        :param georef_id: Id of the georeference process
        :type georef_id: int
        :param user_id: Id of the user
        :type user_id: str
        :param state: Validation state
        :type state:  "invalid" or "valid"
        :param comment: Comment
        :type comment: str
        :result: JSON containing the job id
        :rtype: {{
          job_id: int
        }}
    """
    try:
        if request.method != 'POST':
            return HTTPBadRequest('The endpoint only supports "POST" requests.')

        if request.json['user_id'] == None:
            return HTTPBadRequest('Missing user_id')
        if request.json['georef_id'] == None:
            return HTTPBadRequest('Missing georef_id')
        if request.json['state'] == None or request.json['state'] not in ['invalid', 'valid']:
            return HTTPBadRequest('Missing state or wrong parameter. Only "invalid" or "valid" are supported as state values')
        if request.json['comment'] == None:
            return HTTPBadRequest('Missing comment. Should at least be an empty string.')

        # Query georefObj and return error if not exists
        georefObj = GeoreferenceProcess.byId(toInt(request.json['georef_id']), request.dbsession)
        if georefObj is None:
            return HTTPNotFound('Could not found georeference process for passegeoref_id')

        # Create new jobs
        newAdminJob = AdminJobs(
            georef_id=request.json['georef_id'],
            processed=False,
            state=request.json['state'],
            timestamp=datetime.now().isoformat(),
            comment=request.json['comment'],
            user_id=request.json['user_id']
        )
        request.dbsession.add(newAdminJob)

        # Flush the session to access the new admin job id
        request.dbsession.flush()

        return {
            'job_id': newAdminJob.id
        }
    except Exception as e:
        LOGGER.error('Error while trying to process POST request')
        LOGGER.error(e)
        LOGGER.error(traceback.format_exc())
        raise HTTPInternalServerError(GLOBAL_ERROR_MESSAGE)