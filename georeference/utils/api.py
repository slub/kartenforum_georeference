#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 26.11.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import json
from georeference.models.transformations import Transformation
from georeference.utils.parser import to_public_oai


def to_transformation_response(transformation_obj, map_obj, metadata_obj, dbsession, is_active=False):
    """ Returns a transformation response.

    :param transformation_obj: Transformation object
    :type transformation_obj: georeference.models.transformations.Transformation
    :param map_obj: Original Map object
    :type map_obj: georeference.models.raw_maps.RawMap
    :param metadata_obj: Metadata object
    :type metadata_obj: georeference.models.metadata.Metadata
    :param dbsession: Database session
    :type dbsession: sqlalchemy.orm.session.Session
    :param is_active: Signals of a transformation is currently used for an active georeference map.
    :type is_active: bool
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
    clip_geojson = Transformation.get_valid_clip_geometry(transformation_obj.id,
                                                          dbsession=dbsession) if transformation_obj.clip is not None else None
    if clip_geojson is not None and 'crs' not in clip_geojson:
        clip_geojson["crs"] = {"type": "name", "properties": {"name": "EPSG:4326"}}

    return {
        'is_active': is_active,
        'transformation_id': transformation_obj.id,
        'clip': clip_geojson,
        'params': transformation_obj.get_params_as_dict_in_epsg_4326(),
        'submitted': str(transformation_obj.submitted),
        'overwrites': transformation_obj.overwrites,
        'user_id': transformation_obj.user_id,
        'map_id': to_public_oai(map_obj.id),
        'validation': transformation_obj.validation,
        'metadata': {
            'time_publish': str(metadata_obj.time_of_publication),
            'title': metadata_obj.title,
            'title_short': metadata_obj.title_short
        },
    }
