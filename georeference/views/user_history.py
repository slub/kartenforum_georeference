#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 06.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import traceback
import logging
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPInternalServerError, HTTPBadRequest
from sqlalchemy import desc

from georeference.models.transformations import Transformation, EnumValidationValue
from georeference.models.raw_maps import RawMap
from georeference.models.metadata import Metadata
from georeference.models.georef_maps import GeorefMap
from georeference.utils.parser import to_public_map_id

LOGGER = logging.getLogger(__name__)

GENERAL_ERROR_MESSAGE = 'Something went wrong while trying to process your requests. Please try again or contact the administrators of the Virtual Map Forum 2.0.'


@view_config(route_name='user_history', renderer='json', request_method='GET')
def GET_user_history(request):
    try:
        if request.matchdict['user_id'] is None:
            return HTTPBadRequest('Missing user_id')

        LOGGER.debug('Query georeference profile information from database for user %s' % request.matchdict['user_id'])
        query_data = request.dbsession.query(Transformation, Metadata, RawMap, GeorefMap) \
            .join(Metadata, Transformation.raw_map_id == Metadata.raw_map_id) \
            .join(RawMap, Transformation.raw_map_id == RawMap.id) \
            .join(GeorefMap, GeorefMap.transformation_id == Transformation.id, full=True) \
            .filter(Transformation.user_id == request.matchdict['user_id']) \
            .order_by(desc(Transformation.id))

        LOGGER.debug('Create response list')
        georef_profile = []
        points = 0
        for record in query_data:
            transformation_obj = record[0]
            metadata_obj = record[1]
            map_obj = record[2]
            georef_map_obj = record[3]

            # Create response
            response_record = {
                'file_name': map_obj.file_name,
                'is_transformed': True if georef_map_obj != None else False,
                'map_id': to_public_map_id(map_obj.id),
                'transformation': {
                    'id': transformation_obj.id,
                    'params': transformation_obj.get_params_as_dict(),
                    'submitted': str(transformation_obj.submitted),
                    'validation': transformation_obj.validation
                },
                'metadata': {
                    'thumbnail': metadata_obj.link_thumb_mid,
                    'time_published': str(metadata_obj.time_of_publication),
                    'title': metadata_obj.title,
                }
            }

            # calculate points
            if transformation_obj.validation != EnumValidationValue.INVALID.value:
                points += 20

            georef_profile.append(response_record)

        LOGGER.debug('Response: %s' % georef_profile)

        return {'georef_profile': georef_profile, 'points': points}
    except Exception as e:
        LOGGER.error('Error while trying to request georeference history information')
        LOGGER.error(e)
        LOGGER.error(traceback.format_exc())
        raise HTTPInternalServerError(GENERAL_ERROR_MESSAGE)
