#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 26.11.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import json
from georeference.utils.parser import toPublicOAI

def toTransformationResponse(transformationObj, mapObj, metadataObj, isActive = False):
    """ Returns a transformation response.

    :param transformationObj: Transformation object
    :type transformationObj: georeference.models.transformations.Transformation
    :param mapObj: Original Map object
    :type mapObj: georeference.models.original_maps.OriginalMap
    :param metadataObj: Metadata object
    :type metadataObj: georeference.models.metadata.Metadata
    :param isActive: Signals of a transformation is currently used for an active georeference map.
    :type isActive: bool
    :result: Public api of a transformation
    :rtype: {{
        is_active: bool,
        transformation_id: int,
        clip: GeoJSON,
        params: dict,
        submitted: str,
        overwrites: int,
        user_id: str,
        map_id: str,
        metadata: {
          time_publish: str,
          title: str,
    }}
    """
    return {
        'is_active': isActive,
        'transformation_id': transformationObj.id,
        'clip': json.loads(transformationObj.clip) if transformationObj.clip != None else None,
        'params': transformationObj.getParamsAsDict(),
        'submitted': str(transformationObj.submitted),
        'overwrites': transformationObj.overwrites,
        'user_id': transformationObj.user_id,
        'map_id': toPublicOAI(mapObj.id),
        'validation': transformationObj.validation,
        'metadata': {
            'time_publish': str(metadataObj.time_of_publication),
            'title': metadataObj.title,
            'title_short': metadataObj.title_short
        },
    }
