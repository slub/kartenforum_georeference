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
from georeference.models.georeference_process import GeoreferenceProcess
from georeference.models.map import Map
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

        # Query number of valide georeference processes for each user
        qPoints = request.dbsession.query(GeoreferenceProcess.user_id.label('user'),
                                          func.count(GeoreferenceProcess.user_id).label('occurrence'))\
            .filter(GeoreferenceProcess.validation != 'invalide')\
            .group_by(GeoreferenceProcess.user_id)\
            .subquery()

        # Query number of valide georeference processes for each user with type "new"
        qNew = request.dbsession.query(GeoreferenceProcess.user_id.label('user'), func.count(GeoreferenceProcess.type).label('type'))\
                    .filter(GeoreferenceProcess.validation != 'invalide')\
                    .filter(GeoreferenceProcess.type == 'new')\
                    .group_by(GeoreferenceProcess.user_id)\
                    .subquery()

        # Query number of valide georeference processes for each user with type "update"
        qUpdate = request.dbsession.query(GeoreferenceProcess.user_id.label('user'), func.count(GeoreferenceProcess.type).label('type'))\
                    .filter(GeoreferenceProcess.validation != 'invalide')\
                    .filter(GeoreferenceProcess.type == 'update')\
                    .group_by(GeoreferenceProcess.user_id)\
                    .subquery()

        # Query the data
        data = request.dbsession.query(qPoints.c.user, qPoints.c.occurrence, qNew.c.type, qUpdate.c.type)\
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
            user_points.append({'userid':userid, 'points': points, 'new': new, 'update': update})

        LOGGER.debug('Get georeference map count')
        queryData = request.dbsession.query(func.count(Map.enabled))\
            .filter(Map.georef_rel_path != None)\
            .filter(Map.enabled == True)
        georeference_map_count = []
        for record in queryData:
            georeference_map_count = record[0]

        LOGGER.debug('Get missing georeference map count')
        queryData = request.dbsession.query(func.count(Map.enabled))\
            .filter(Map.georef_rel_path == None)\
            .filter(Map.enabled == True)
        missing_georeference_map_count = []
        for record in queryData:
            missing_georeference_map_count = record[0]

        return {'georeference_points': user_points, 'georeference_map_count': georeference_map_count, 'not_georeference_map_count':missing_georeference_map_count}
    except Exception as e:
        LOGGER.error('Error while trying to request georeference history information')
        LOGGER.error(e)
        LOGGER.error(traceback.format_exc())
        raise HTTPInternalServerError(GLOBAL_ERROR_MESSAGE)