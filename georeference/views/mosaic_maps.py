#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 21.06.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import logging

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPInternalServerError, HTTPNotFound

from georeference.models.mosaic_maps import MosaicMap
from georeference.utils.logging import log_error
from georeference.utils.parser import from_public_mosaic_map_id
from georeference.settings import GLOBAL_ERROR_MESSAGE
from georeference.utils.parser import to_public_map_id, to_public_mosaic_map_id, from_public_map_id
from georeference.utils.utils import without_keys

LOGGER = logging.getLogger(__name__)


@view_config(route_name='mosaic_maps', renderer='json', request_method='GET')
def GET_mosaic_map_id(request):
    """
    Endpoint for accessing mosaic_map metadata.

    :param: request - pyramid request object
    :result: JSON object describing the mosaic map object
    :rtype: {mosaic_map_schema}
    """
    try:
        # Query data
        public_mosaic_map_id = request.matchdict['mosaic_map_id']
        mosaic_map_obj = MosaicMap.by_id(from_public_mosaic_map_id(public_mosaic_map_id), request.dbsession)

        if mosaic_map_obj is None:
            return HTTPNotFound(f'Could not find mosaic_map for id {public_mosaic_map_id}')

        # Create response_obj and map the raw_map_ids to public raw_map_ids
        response_obj = without_keys(mosaic_map_obj.__dict__, ['_sa_instance_state'])
        response_obj['id'] = to_public_mosaic_map_id(response_obj['id'])
        response_obj['raw_map_ids'] = list(map(lambda x: to_public_map_id(x), response_obj['raw_map_ids']))

        return response_obj
    except Exception as e:
        log_error(e, 'Error while trying to return a GET mosaic map request')
        raise HTTPInternalServerError(GLOBAL_ERROR_MESSAGE)