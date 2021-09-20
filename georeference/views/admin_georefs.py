#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 10.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import traceback
import logging
import os
from pyramid.view import view_config
from sqlalchemy import desc
from sqlalchemy.sql.expression import or_
from pyramid.httpexceptions import HTTPInternalServerError, HTTPBadRequest
from georeference.models.georeference_process import GeoreferenceProcess
from georeference.models.metadata import Metadata
from georeference.utils.parser import toInt
from georeference.settings import GLOBAL_ERROR_MESSAGE
from georeference.settings import OAI_ID_PATTERN

# For correct resolving of the paths we use derive the base_path of the file
BASE_PATH = os.path.dirname(os.path.realpath(__file__))

# Initialize the logger
LOGGER = logging.getLogger(__name__)

@view_config(route_name='admin_georefs', renderer='json', request_method='POST', accept='application/json')
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
                .join(Metadata, GeoreferenceProcess.mapid == Metadata.mapid) \
                .filter(GeoreferenceProcess.mapid == toInt(request.params['map_id'])) \
                .order_by(desc(GeoreferenceProcess.id))

        # Generate response data via user_id
        elif 'user_id' in request.params:
            queryData = request.dbsession.query(GeoreferenceProcess, Metadata)\
                .join(Metadata, GeoreferenceProcess.mapid == Metadata.mapid) \
                .filter(GeoreferenceProcess.nutzerid == request.params['user_id']) \
                .order_by(desc(GeoreferenceProcess.id))

        # Generate response data via validation
        elif 'validation' in request.params:
            queryData = request.dbsession.query(GeoreferenceProcess, Metadata)\
                .join(Metadata, GeoreferenceProcess.mapid == Metadata.mapid) \
                .filter(GeoreferenceProcess.adminvalidation == request.params['validation']) \
                .order_by(desc(GeoreferenceProcess.id))

        # Generate response data via pending
        elif 'pending' in request.params:
            queryData = request.dbsession.query(GeoreferenceProcess, Metadata)\
                .join(Metadata, GeoreferenceProcess.mapid == Metadata.mapid) \
                .filter(or_(GeoreferenceProcess.adminvalidation == '', GeoreferenceProcess.adminvalidation == None)) \
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
                        'georef_params': georefObj.georefparams,
                        'id': georefObj.id,
                        'isActive': georefObj.isactive,
                        'processed': georefObj.processed,
                        'timestamp': str(georefObj.timestamp),
                        'type': georefObj.type,
                        'validation_status': georefObj.adminvalidation,
                        'user_id': georefObj.nutzerid
                    },
                    'metadata': {
                        'oai': OAI_ID_PATTERN % georefObj.mapid,
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

# @view_config(route_name='maps_georefs', renderer='json', request_method='POST', accept='application/json'):
# def postAdminGeorefs(request):
#     """ Admin endpoint for setting a georeference process validation status. Expects the following url pattern:
#
#             POST     {route_prefix}/admin/georefs
#
#         :param georef_id: Id of the georeference process
#         :type georef_id: int
#         :param validation_status: Validation state. Can be "invalid" or "valid"
#         :type validation_status:  "invalid" or "valid"
#         :result: JSON array of georeference process enhanced with further metadata
#         :rtype: {{
#           georef: {
#               clip_polygon: GeoJSON,
#               georef_params: *,
#               id: int,
#               isActive: bool,
#               processed: bool,
#               timestamp: str,
#               type: 'new' | 'update',
#               validation_status: str,
#               user_id: str,
#           },
#           metadata: {
#             oai: str,
#             time_publish: str,
#             title: str,
#           }
#         }}
#     """
#
#     try:
#         if request.method != 'GET':
#             return HTTPBadRequest('The endpoint only supports "GET" requests.')
#
#         # Try to query the data
#         queryData = None
#
#         # Generate response data via map_id
#         if 'map_id' in request.params:
#             queryData = request.dbsession.query(Georeferenzierungsprozess, Metadata) \
#                 .join(Metadata, Georeferenzierungsprozess.mapid == Metadata.mapid) \
#                 .filter(Georeferenzierungsprozess.mapid == toInt(request.params['map_id'])) \
#                 .order_by(desc(Georeferenzierungsprozess.id))
#
#         # Generate response data via user_id
#         elif 'user_id' in request.params:
#             queryData = request.dbsession.query(Georeferenzierungsprozess, Metadata) \
#                 .join(Metadata, Georeferenzierungsprozess.mapid == Metadata.mapid) \
#                 .filter(Georeferenzierungsprozess.nutzerid == request.params['user_id']) \
#                 .order_by(desc(Georeferenzierungsprozess.id))
#
#         # Generate response data via validation
#         elif 'validation' in request.params:
#             queryData = request.dbsession.query(Georeferenzierungsprozess, Metadata) \
#                 .join(Metadata, Georeferenzierungsprozess.mapid == Metadata.mapid) \
#                 .filter(Georeferenzierungsprozess.adminvalidation == request.params['validation']) \
#                 .order_by(desc(Georeferenzierungsprozess.id))
#
#         # Generate response data via pending
#         elif 'pending' in request.params:
#             queryData = request.dbsession.query(Georeferenzierungsprozess, Metadata) \
#                 .join(Metadata, Georeferenzierungsprozess.mapid == Metadata.mapid) \
#                 .filter(
#                 or_(Georeferenzierungsprozess.adminvalidation == '', Georeferenzierungsprozess.adminvalidation == None)) \
#                 .order_by(desc(Georeferenzierungsprozess.id))
#
#         if queryData == None:
#             return HTTPBadRequest(
#                 'Please pass values for one of the following query parameters: "map_id", "user_id", "pending", "validation"')
#         else:
#             response = []
#             for record in queryData:
#                 georefObj = record[0]
#                 metadataObj = record[1]
#                 dict = {
#                     'georef': {
#                         'clip_polygon': georefObj.getClipAsGeoJSON(request.dbsession),
#                         'georef_params': georefObj.georefparams,
#                         'id': georefObj.id,
#                         'isActive': georefObj.isactive,
#                         'processed': georefObj.processed,
#                         'timestamp': str(georefObj.timestamp),
#                         'type': georefObj.type,
#                         'validation_status': georefObj.adminvalidation,
#                         'user_id': georefObj.nutzerid
#                     },
#                     'metadata': {
#                         'oai': OAI_ID_PATTERN % georefObj.mapid,
#                         'time_publish': str(metadataObj.timepublish),
#                         'title': metadataObj.title,
#                     }
#                 }
#                 response.append(dict)
#
#             return response
#         return ""
#     except Exception as e:
#         LOGGER.error('Error while trying to process GET request')
#         LOGGER.error(e)
#         LOGGER.error(traceback.format_exc())
#         raise HTTPInternalServerError(GLOBAL_ERROR_MESSAGE)