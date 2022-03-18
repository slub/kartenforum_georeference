#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 12.10.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import traceback
import os
import json
import shutil
from datetime import datetime
from georeference.models.original_maps import OriginalMap
from georeference.models.georef_maps import GeorefMap
from georeference.models.metadata import Metadata
from georeference.models.transformations import Transformation
from georeference.settings import PATH_TMS_ROOT
from georeference.settings import PATH_MAPFILE_ROOT, PATH_MAPFILE_TEMPLATES
from georeference.settings import PATH_TMP_ROOT
from georeference.settings import GLOBAL_TMS_PROCESSES
from georeference.settings import GLOBAL_DOWNLOAD_YEAR_THRESHOLD
from georeference.settings import TEMPLATE_PUBLIC_WMS_URL
from georeference.settings import TEMPLATE_PUBLIC_WCS_URL
from georeference.settings import ES_INDEX_NAME
from georeference.scripts.es import generateDocument
from georeference.scripts.tms import calculateCompressedTMS
from georeference.utils.georeference import getExtentFromGeoTIFF
from georeference.utils.georeference import getSrsFromGeoTIFF
from georeference.utils.georeference import rectifyImageWithClipAndOverviews
from georeference.utils.parser import toGDALGcps
from georeference.utils.mapfile import writeMapfile
from georeference.utils.mapfile import parseGeoTiffMetadata

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

def _processGeoTransformation(transformationObj, originalMapObj, georefMapObj, metadataObj, logger, forceReprocessing = False):
    """ Process the geo transformation for a given set of parameters

    :param transformationObj: Transformation
    :type transformationObj: georeference.models.transformations.Transformation
    :param originalMapObj: Original map
    :type originalMapObj: georeference.model.original_maps.OriginalMap
    :param georefMapObj: Georeference map
    :type georefMapObj: georeference.model.georef_maps.GeorefMap
    :param metadataObj: Metadata
    :type metadataObj: georeference.model.metadata.Metadata
    :param logger: Logger
    :type logger: logging.Logger
    :param forceReprocessing: Forces a reprocessing
    :type forceReprocessing: bool
    :result: True if performed successfully
    :rtype: bool
    """
    try:
        if not os.path.exists(originalMapObj.getAbsPath()):
            logger.info('Skip processing georeference transformation for map "%s", because of missing original image.' % originalMapObj.id)

        if os.path.exists(georefMapObj.getAbsPath()) == False or forceReprocessing:
            logger.debug('Process transformation with id "%s" ...' % transformationObj.id)
            georefParams  = transformationObj.getParamsAsDict()
            clip = json.loads(transformationObj.clip) if transformationObj.clip != None else None

            # Try processing a geo transformation
            rectifyImageWithClipAndOverviews(
                originalMapObj.getAbsPath(),
                georefMapObj.getAbsPath(),
                georefParams['algorithm'],
                toGDALGcps(georefParams['gcps']),
                georefParams['target'],
                logger,
                PATH_TMP_ROOT,
                clip
            )

        if not os.path.exists(georefMapObj.getAbsPath()):
            raise Exception('Something went wrong while trying to process georeference image')

        logger.debug('Update the extent of the georef map object ...')
        georefMapObj.extent = json.dumps(
            _getExtentFromGeoTIFF(georefMapObj.getAbsPath())
        )

        rootDirTms = os.path.join(PATH_TMS_ROOT, str(originalMapObj.map_type).lower())
        tmsDir = os.path.join(rootDirTms, os.path.basename(georefMapObj.getAbsPath()).split('.')[0])

        # If the reprocessing is forced we delete the tms dir
        if forceReprocessing and os.path.exists(tmsDir):
            shutil.rmtree(tmsDir)
        if not os.path.isdir(tmsDir):
            logger.debug('Process tile map service (TMS) ...')
            calculateCompressedTMS(
                georefMapObj.getAbsPath(),
                rootDirTms,
                logger,
                GLOBAL_TMS_PROCESSES,
                originalMapObj.map_scale
            )


        trgMapFile = os.path.join(PATH_MAPFILE_ROOT, '%s.map' % originalMapObj.id)
        # If the reprocessing is forced we delete the tms dir
        if forceReprocessing and os.path.exists(trgMapFile):
            os.remove(trgMapFile)
        if not os.path.exists(trgMapFile):
            logger.debug('Create mapfile for wms and wcs services ...')
            templateFile = os.path.join(PATH_MAPFILE_TEMPLATES, './wms_static.map')
            templateValues = {
                **parseGeoTiffMetadata(georefMapObj.getAbsPath()),
                **{
                    'wmsUrl': TEMPLATE_PUBLIC_WMS_URL % originalMapObj.id,
                    'wcsUrl': TEMPLATE_PUBLIC_WCS_URL % originalMapObj.id,
                    'layerName': originalMapObj.file_name,
                    'layerDataPath': georefMapObj.getAbsPath(),
                    'layerTitle': metadataObj.title_short
                }
            }
            logger.debug('Use template values %s' % templateValues)

            if metadataObj.time_of_publication.date().year <= GLOBAL_DOWNLOAD_YEAR_THRESHOLD:
                templateFile = os.path.join(PATH_MAPFILE_TEMPLATES, './wms_wcs_static.map')

            writeMapfile(
                trgMapFile,
                templateFile,
                templateValues,
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
        logger.debug('Delete tiff file for georeference map')
        if (os.path.exists(georefMapObj.getAbsPath())):
            os.remove(georefMapObj.getAbsPath())
        logger.debug('Delete georeference map object for original map id %s.' % georefMapObj.original_map_id)
        dbsession.delete(georefMapObj)
        dbsession.flush()

    # Check if there is a tms and if yes remove it
    rootDirTms = os.path.join(PATH_TMS_ROOT, str(originalMapObj.map_type).lower())
    tmsDir = os.path.join(rootDirTms, os.path.basename(georefMapObj.getAbsPath()).split('.')[0])
    if os.path.isdir(tmsDir):
        shutil.rmtree(tmsDir)

    # Check if there is a mapfile and remove it, if it exists
    trgMapFile = os.path.join(PATH_MAPFILE_ROOT, '%s.map' % originalMapObj.id)
    if os.path.exists(trgMapFile):
        os.remove(trgMapFile)

    # Write document to es
    logger.debug('Write search record for original map id %s to index ...' % (originalMapObj.id))
    dbsession.flush()

    try:
        searchDocument = generateDocument(
            originalMapObj,
            Metadata.byId(originalMapObj.id, dbsession),
            georefMapObj=None,
            logger=logger,
            geometry=getGeometry(originalMapObj.id, dbsession)
        )
        logger.debug(searchDocument)
        esIndex.index(
            index=ES_INDEX_NAME,
            doc_type=None,
            id=searchDocument['map_id'],
            body=searchDocument
        )
    except Exception as e:
        logger.error('Failed to write document to es for original map %s.' % originalMapObj.id)
        logger.error(searchDocument)
        logger.error(e)
        logger.error(traceback.format_exc())

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
    metadataObj = Metadata.byId(originalMapObj.id, dbsession)

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
        dbsession.flush()

    # Process the geo image
    _processGeoTransformation(
        transformationObj,
        originalMapObj,
        georefMapObj,
        metadataObj,
        logger,
        forceReprocessing=True
    )

    # Update the transformation_id
    georefMapObj.transformation_id = transformationObj.id

    # Write document to es
    logger.debug('Write search record for original map id %s to index ...' % (originalMapObj.id))
    dbsession.flush()

    try:
        searchDocument = generateDocument(
            originalMapObj,
            metadataObj,
            georefMapObj=georefMapObj,
            logger=logger,
            geometry=getGeometry(originalMapObj.id, dbsession)
        )
        logger.debug(searchDocument)
        esIndex.index(
            index=ES_INDEX_NAME,
            doc_type=None,
            id=searchDocument['map_id'],
            body=searchDocument
        )
    except Exception as e:
        logger.error('Failed to write document to es for original map %s.' % originalMapObj.id)
        logger.error(searchDocument)
        logger.error(e)
        logger.error(traceback.format_exc())

def getGeometry(originalMapId, dbsession):
    """ This function helps to extract the geometry for a given georeferenced map in GeoJSON structure. It checks if a clip polygon
        is saved for a given GeorefMap and if yes returns the clip polygon as Geometry in GeoJSON structure. If no clip
        polygon is saved it uses the extent of the GeorefMap

    :param originalMapId: Id of a original map
    :type originalMapId: int
    :param dbsession: Database session
    :type dbsession: sqlalchemy.orm.session.Session
    :returns: JSON
    """
    # Extract the GeorefMap object for the original map
    georefMapObj = GeorefMap.byOriginalMapId(originalMapId, dbsession)

    # Check if there is a clip polygon and if yes return it.
    if georefMapObj != None:
        clipGeometry = Transformation.getClipForTransformationId(georefMapObj.transformation_id, dbsession)
        if clipGeometry != None:
            return clipGeometry
    return GeorefMap.getExtentForMapId(originalMapId, dbsession)