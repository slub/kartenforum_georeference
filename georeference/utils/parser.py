#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 09.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
from osgeo import gdal
from georeference.settings import OAI_ID_TEMPLATE

def fromPublicOAI(oai):
    """ Transforms a given oai to an internal mapId.

    :param oai: Public oai
    :type oai: str
    :result: Internal mapId
    :rtype: int
    """
    ns, mapId = oai.rsplit('-', 1)
    if ns != OAI_ID_TEMPLATE.rsplit('-', 1)[0]:
        raise TypeError('Can not process the given oai.')
    return int(mapId)

def toInt(v):
    """ Tries to cast a given value to an int.

    :param v: Any value
    :type v: any
    :result: Value as int
    :rtype: int
    :raise: TypeError
    """
    if isinstance(int(v), int):
        return int(v)
    else:
        raise TypeError('The given values is not an integer.')

def toGDALGcps(gcps):
    """ Transforms gcps in the service API notation to gdal gcps.

    :param gcps:  List of gcps
    :type gcps: { target: [number, number], source: [number, number] }[]
    :result: List of gdal.GCPs
    :rtype: [gdal.GCP]
    """
    return list(map(lambda gcp: gdal.GCP(gcp['target'][0], gcp['target'][1], 0, gcp['source'][0], gcp['source'][1]), gcps))

def toPublicOAI(mapId):
    """ Transforms a given id to a public.

    :param mapId: Number representing a internal id
    :type mapId: int
    :result: Public OAI
    :rtype: str
    """
    if '%s'not in OAI_ID_TEMPLATE:
        raise BaseException('Could not process OAI_ID_TEMPLATE')
    return OAI_ID_TEMPLATE % mapId