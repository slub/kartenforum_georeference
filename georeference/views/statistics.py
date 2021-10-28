#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 01.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import traceback
import logging
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPInternalServerError
from sqlalchemy import desc
from sqlalchemy import func
from georeference.models.transformations import Transformation, ValidationValues
from georeference.models.georef_maps import GeorefMap
from georeference.models.original_maps import OriginalMap
from georeference.settings import GLOBAL_ERROR_MESSAGE

LOGGER = logging.getLogger(__name__)

@view_config(route_name='statistics', renderer='json')
def getStatistics(request):
    LOGGER.info('Request - Get georeference points.')
    LOGGER.debug(request)

    try:
        #
        # Create the database queries
        #

        # Query number of georeference processes for each user
        qPoints = request.dbsession.query(
                Transformation.user_id.label('user'), func.count(Transformation.user_id).label('occurrence')
            )\
            .filter(Transformation.validation != ValidationValues.INVALID.value)\
            .group_by(Transformation.user_id)\
            .subquery()

        # Query number of valid transformations for each user of type "new"
        qNew = request.dbsession.query(Transformation.user_id.label('user'), func.count(Transformation.params).label('transformations'))\
                    .filter(Transformation.validation != ValidationValues.INVALID.value)\
                    .filter(Transformation.overwrites == 0)\
                    .group_by(Transformation.user_id)\
                    .subquery()

        # Query number of valid transformations for each user of type "update"
        qUpdate = request.dbsession.query(Transformation.user_id.label('user'), func.count(Transformation.params).label('transformations'))\
                    .filter(Transformation.validation != ValidationValues.INVALID.value)\
                    .filter(Transformation.overwrites > 0)\
                    .group_by(Transformation.user_id)\
                    .subquery()

        # Query the data
        data = request.dbsession.query(qPoints.c.user, qPoints.c.occurrence, qNew.c.transformations, qUpdate.c.transformations)\
                .outerjoin(qNew, qPoints.c.user == qNew.c.user)\
                .outerjoin(qUpdate, qPoints.c.user == qUpdate.c.user)\
                .order_by(desc(qPoints.c.occurrence)).limit(20)

        # Create ranking list
        user_points = []
        for record in data:
            userid = record[0]
            points = record[1] * 20
            new = record[2] if record[2] is not None else 0
            update = record[3] if record[3] is not None else 0
            user_points.append({ 'user_id':userid, 'total_points': points, 'transformation_new': new, 'transformation_updates': update})

        LOGGER.debug('Get georeference map count')
        georeference_map_count = request.dbsession.query(GeorefMap.original_map_id).count()

        LOGGER.debug('Get missing georeference map count')
        missing_georeference_map_count = request.dbsession.query(OriginalMap)\
            .join(GeorefMap, GeorefMap.original_map_id == OriginalMap.id, full=True)\
            .filter(GeorefMap.original_map_id == None)\
            .count()

        return {'georeference_points': user_points, 'georeference_map_count': georeference_map_count, 'not_georeference_map_count':missing_georeference_map_count}
    except Exception as e:
        LOGGER.error('Error while trying to request georeference history information')
        LOGGER.error(e)
        LOGGER.error(traceback.format_exc())
        raise HTTPInternalServerError(GLOBAL_ERROR_MESSAGE)