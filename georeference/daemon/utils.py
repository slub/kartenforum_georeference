#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 12.10.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import traceback
import os
import json
from datetime import datetime
from georeference.models.original_maps import OriginalMap
from georeference.models.georef_maps import GeorefMap
from georeference.models.metadata import Metadata
from georeference.models.transformations import Transformation, ValidationValues
from georeference.settings import PATH_TMS_ROOT
from georeference.settings import TMP_DIR
from georeference.settings import GEOREFERENCE_TMS_PROCESSES
from georeference.settings import ES_INDEX_NAME
from georeference.scripts.es import generateDocument
from georeference.scripts.tms import calculateCompressedTMS
from georeference.utils.georeference import getExtentFromGeoTIFF
from georeference.utils.georeference import getSrsFromGeoTIFF
from georeference.utils.georeference import rectifyImageWithClipAndOverviews
from georeference.utils.parser import toGDALGcps

def _getExtentFromGeoTIFF(path):
    """ Extracts the extent from a geotiff file and returns a GeoJSON.

    :param path: Path to geotiff.
    :param path: str
    :result: GeoJSON representing the extent
    :rtype: GeoJSON """
    extent = getExtentFromGeoTIFF(path)
    srid = getSrsFromGeoTIFF(path)
    return {
        'type': 'Polygon',
        'coordinates': [[
            [extent[0], extent[1]],
            [extent[0], extent[3]],
            [extent[2], extent[3]],
            [extent[2], extent[1]],
            [extent[0], extent[1]],
        ]],
        'crs': {
            'type': 'name',
            'properties': {
                'name': srid,
            }
        }
    }

def _processGeoTransformation(transformationObj, originalMapObj, georefMapObj, dbsession, logger):
    """ Process the geo transformation for a given set of parameters

    :param transformationObj: Transformation
    :type transformationObj: georeference.models.transformations.Transformation
    :param originalMapObj: Original map
    :type originalMapObj: georeference.model.original_maps.OriginalMap
    :param georefMapObj: Georeference map
    :type georefMapObj: georeference.model.georef_maps.GeorefMap
    :param dbsession: Database session object
    :type dbsession: sqlalchemy.orm.session.Session
    :param logger: Logger
    :type logger: logging.Logger
    :result: True if performed successfully
    :rtype: bool
    """
    try:
        georefParams  = transformationObj.getParamsAsDict()
        clip = json.loads(transformationObj.clip)

        # Try processing a geo transformation
        logger.debug('Process transformation with id "%s" ...' % transformationObj.id)
        rectifyImageWithClipAndOverviews(
            originalMapObj.getAbsPath(),
            georefMapObj.getAbsPath(),
            georefParams['algorithm'],
            toGDALGcps(georefParams['gcps']),
            georefParams['target'],
            logger,
            TMP_DIR,
            clip
        )

        if not os.path.exists(georefMapObj.getAbsPath()):
            raise Exception('Something went wrong while trying to process georeference image')


        logger.debug('Update the extent of the georef map object ...')
        georefMapObj.extent = json.dumps(
            _getExtentFromGeoTIFF(georefMapObj.getAbsPath())
        )

        logger.debug('Process tile map service (TMS) ...')
        calculateCompressedTMS(
            georefMapObj.getAbsPath(),
            os.path.join(PATH_TMS_ROOT, str(originalMapObj.map_type).lower()),
            logger,
            GEOREFERENCE_TMS_PROCESSES,
            originalMapObj.map_scale
        )

        return True
    except Exception as e:
        logger.error('Error while trying to process geo transformation.')
        logger.error(e)
        logger.error(traceback.format_exc())

def disableTransformation(transformationObj, esIndex, dbsession, logger):
    """ Disables a given transformation.

    :param transformationObj: Transformation
    :type transformationObj: georeference.models.transformations.Transformation
    :param esIndex: Elsaticsearch client
    :type esIndex: elasticsearch.Elasticsearch
    :param dbsession: Database session
    :type dbsession: sqlalchemy.orm.session.Session
    :param logger: Logger
    :type logger: logging.Logger
    """
    # Query original and georef  map obj
    originalMapObj = OriginalMap.byId(transformationObj.original_map_id, dbsession)
    georefMapObj = GeorefMap.byTransformationId(transformationObj.id, dbsession)

    # Delete the georef object
    if georefMapObj != None:
        logger.debug('Delete georeference map object for original map id %s.' % georefMapObj.original_map_id)
        dbsession.delete(georefMapObj)

    # Write document to es
    logger.debug('Write search record for original map id %s to index ...' % (originalMapObj.id))
    searchDocument = generateDocument(
        originalMapObj,
        Metadata.byId(originalMapObj.id, dbsession),
        georefMapObj=None,
        logger=logger
    )
    logger.debug(searchDocument)
    esIndex.index(
        index=ES_INDEX_NAME,
        doc_type=None,
        id=searchDocument['map_id'],
        body=searchDocument
    )

def enableTransformation(transformationObj, esIndex, dbsession, logger):
    """ Enables a given transformation.

    :param transformationObj: Transformation
    :type transformationObj: georeference.models.transformations.Transformation
    :param esIndex: Elsaticsearch client
    :type esIndex: elasticsearch.Elasticsearch
    :param dbsession: Database session
    :type dbsession: sqlalchemy.orm.session.Session
    :param logger: Logger
    :type logger: logging.Logger
    """
    # Query original and georef  map obj
    originalMapObj = OriginalMap.byId(transformationObj.original_map_id, dbsession)
    georefMapObj = GeorefMap.byOriginalMapId(transformationObj.original_map_id, dbsession)

    # In case a georefMapObj does not exist, create a new one
    if georefMapObj == None:
        logger.debug('Create new georef map object for original map id %s.' % originalMapObj.id)
        georefMapObj = GeorefMap(
            original_map_id = originalMapObj.id,
            rel_path = './%s/%s.tif' % (originalMapObj.map_type.lower(), originalMapObj.file_name),
            transformation_id = transformationObj.id,
            last_processed = datetime.now().isoformat()
        )
        dbsession.add(georefMapObj)

    # Process the geo image
    _processGeoTransformation(
        transformationObj,
        originalMapObj,
        georefMapObj,
        dbsession,
        logger
    )

    # Update the transformation_id
    georefMapObj.transformation_id = transformationObj.id

    # Write document to es
    logger.debug('Write search record for original map id %s to index ...' % (originalMapObj.id))
    searchDocument = generateDocument(
        originalMapObj,
        Metadata.byId(originalMapObj.id, dbsession),
        georefMapObj=georefMapObj,
        logger=logger
    )
    logger.debug(searchDocument)
    esIndex.index(
        index=ES_INDEX_NAME,
        doc_type=None,
        id=searchDocument['map_id'],
        body=searchDocument
    )
