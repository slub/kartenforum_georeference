#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 10.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package

def isValidClipPolygon(obj):
    """ Checks if a given clip polygon is valid.

    :param obj: any
    :type obj: dict
    :result: Validation of the clip polygon
    :rtype: {[bool, str]}
    """
    if obj['type'] != 'Polygon':
        return [False, 'Only polygons are allowed for a clip polygon']
    if obj['crs'] == None:
        return [False, 'Missing crs information for the clip polygon']
    if obj['coordinates'] == None:
        return [False, 'Missing coordinates for the clip polygon']
    return [True, '']

def isValidTransformationParams(obj):
    """ Checks if a given params are valid transformation information.

    :param obj: any
    :type obj: dict
    :result: Validation of the clip polygon
    :rtype: {[bool, str]}
    """
    if obj['source'].lower() != 'pixel':
        return [False, 'Only "pixel" is allowed as source value for the georeference parameters']
    if 'epsg:' not in obj['target'].lower():
        return [False, 'Only EPSG notation is allowed as target value for the georeference parameters']
    if obj['algorithm'].lower() not in ['tps', 'polynom', 'affine']:
        return [False, 'Passed georeference algorithm is not supported. Supported values are "tps", "polynom" and "affine".']
    if obj['gcps'] == None:
        return [False, 'Missing gcps for georeference parameters']
    if obj['gcps'] != None and len(obj['gcps']) <= 3:
        return [False, 'Georeference process with less then 3 gcps are not allowed.']
    return [True, '']

def isValidTransformationRequest(obj):
    """ Function validates a given python dictionary, for matching a transformation request. If not it tries to produce
        an error message.

    :param obj: Dictionary containing the georef process information
    :type obj: Dict
    :result: Answer if it is a valid transformation request.
    :rtype: {{
        valid: bool,
        error_msg: str,
    }} """
    isValid = True
    errorMsg = ''

    # Parse parameter
    clipPolygon = obj['clip']
    georefParams = obj['params']
    overwrites = obj['overwrites']
    userId = obj['user_id']
    if clipPolygon != None:
        if clipPolygon['type'] != 'Polygon':
            isValid = False
            errorMsg = 'Only polygons are allowed for a clip polygon'
        if clipPolygon['crs'] == None:
            isValid = False
            errorMsg = 'Missing crs information for the clip polygon'
        if clipPolygon['coordinates'] == None:
            isValid = False
            errorMsg = 'Missing coordinates for the clip polygon'
    if georefParams == None:
        isValid = False
        errorMsg = 'Missing georeference parameters'
    if georefParams != None:
        if georefParams['source'].lower() != 'pixel':
            isValid = False
            errorMsg = 'Only "pixel" is allowed as source value for the georeference parameters'
        if 'epsg:' not in georefParams['target'].lower():
            isValid = False
            errorMsg = 'Only EPSG notation is allowed as target value for the georeference parameters'
        if georefParams['algorithm'].lower() not in ['tps', 'polynom', 'affine']:
            isValid = False
            errorMsg = 'Passed georeference algorithm is not supported. Supported values are "tps", "polynom" and "affine".'
        if georefParams['gcps'] == None:
            isValid = False
            errorMsg = 'Missing gcps for georeference parameters'
        if georefParams['gcps'] != None and len(georefParams['gcps']) <= 3:
            isValid = False
            errorMsg = 'Georeference process with less then 3 gcps are not allowed.'
    if isinstance(overwrites, int) == False:
        isValid = False
        errorMsg = 'Only integeter types are are supported as values for overwrites'
    if userId == None:
        isValid = False
        errorMsg = 'Missing "user_id".'

    return {
        'error_msg': errorMsg,
        'valid': isValid,
    }