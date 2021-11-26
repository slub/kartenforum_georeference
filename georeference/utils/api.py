#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 26.11.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import json
from georeference.utils.parser import toPublicOAI

def toTransformationResponse(transformationObj, mapObj, metadataObj):
    """ Returns a transformation response.

    :param transformationObj: Transformation object
    :type transformationObj: georeference.models.transformations.Transformation
    :param mapObj: Original Map object
    :type mapObj: georeference.models.original_maps.OriginalMap
    :param metadataObj: Metadata object
    :type metadataObj: georeference.models.metadata.Metadata
    :result: Public api of a transformation
    :rtype: {{
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
        'transformation_id': transformationObj.id,
        'clip': json.loads(transformationObj.clip) if transformationObj.clip != None else None,
        'params': transformationObj.getParamsAsDict(),
        'submitted': str(transformationObj.submitted),
        'overwrites': transformationObj.overwrites,
        'user_id': transformationObj.user_id,
        'map_id': toPublicOAI(mapObj.id),
        'metadata': {
            'time_publish': str(metadataObj.time_of_publication),
            'title': metadataObj.title,
        },
    }
