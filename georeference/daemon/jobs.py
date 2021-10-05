#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 16.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import traceback
import os
from georeference.models.admin_jobs import AdminJobs
from georeference.models.georeference_process import GeoreferenceProcess
from georeference.models.map import Map
from georeference.models.metadata import Metadata
from georeference.settings import PATH_TMS_ROOT
from georeference.settings import TMP_DIR
from georeference.settings import GEOREFERENCE_TMS_PROCESSES
from georeference.settings import ES_ROOT
from georeference.settings import ES_INDEX_NAME
from georeference.scripts.es import generateDocument
from georeference.scripts.es import getIndex
from georeference.scripts.tms import calculateCompressedTMS
from georeference.utils.georeference import getExtentFromGeoTIFF
from georeference.utils.georeference import getSrsFromGeoTIFF
from georeference.utils.georeference import rectifyImageWithClipAndOverviews
from georeference.utils.parser import toGDALGcps

def _enableGeorefProcess(georefObj, mapObj, esIndex, dbsession, logger):
    """ Enables a given georeference process.

    :param georefObj: Georeference process
    :type georefObj: georeference.models.georeference_process.GeoreferenceProcess
    :param mapObj: Map object
    :type mapObj: georeference.models.map.Map
    :param esIndex: Elsaticsearch client
    :type esIndex: elasticsearch.Elasticsearch
    :param dbsession: Database session
    :type dbsession: sqlalchemy.orm.session.Session
    :param logger: Logger
    :type logger: logging.Logger
    """
    # Set the rel_georef_path. If we miss this, there will be no processing of new georeference processes
    if mapObj.georef_rel_path == None or len(mapObj.georef_rel_path) == 0:
        mapObj.georef_rel_path = './%s/%s.tif' % (str(mapObj.map_type).lower(), mapObj.file_name)

    _processMapObj(
        mapObj,
        georefObj,
        dbsession,
        logger,
        esIndex,
        forceProcessing=True
    )

    # Change the database
    mapObj.enalbeMap()
    georefObj.setActive()

def _disableGeorefProcess(georefObj, mapObj, esIndex, dbsession, logger):
    """ Disable a given georeference process.

    :param georefObj: Georeference process
    :type georefObj: georeference.models.georeference_process.GeoreferenceProcess
    :param mapObj: Map object
    :type mapObj: georeference.models.map.Map
    :param esIndex: Elsaticsearch client
    :type esIndex: elasticsearch.Elasticsearch
    :param dbsession: Database session
    :type dbsession: sqlalchemy.orm.session.Session
    :param logger: Logger
    :type logger: logging.Logger
    """
    mapObj.disableMap()
    georefObj.disableGeorefProcess()

    # Flush the changes for proper working of the index update
    dbsession.flush()
    esIndex.index(
        index=ES_INDEX_NAME,
        doc_type=None,
        id=mapObj.id,
        body=generateDocument(
            mapObj,
            Metadata.byId(mapObj.id, dbsession),
            None,
            dbsession=dbsession,
            logger=logger
        )
    )

def _getLastValidGeoreferenceProcess(overwriteId, dbsession, logger):
    """ This function goes down the overwrite chain and looks for the last valid
        georeference process

    :param overwriteId: Last overwrite id
    :type overwriteId: int
    :param dbsession: Database session
    :type dbsession: sqlalchemy.orm.session.Session
    :param logger: Logger
    :type: logger: logging.Logger
    :result: Returns a valid georeference process if existing
    :rtype: georeference.models.georeference_process.GeoreferenceProcess|None
    """
    georefProcess = GeoreferenceProcess.by_id(overwriteId, dbsession)
    if georefProcess.validation == 'valid' or georefProcess.validation == '':
        return georefProcess
    elif georefProcess.overwrites > 0:
        return _getLastValidGeoreferenceProcess(georefProcess.overwrites, dbsession, logger)
    else:
        return None

def _processGeoref(georefParams, clip, srcPath, dstPath, logger):
    """ Process a given georeference process.

    :param georefParams: Georeference parameters as dict
    :type georefParams: dict
    :param clip: Clip polygon as GeoJSON dict
    :type clip: dict
    :param srcPath: Path to the source image
    :type srcPath: str
    :param dstPath: Path of the georeferenced image
    :type dstPath: str
    :param logger: Logger
    :type logger: logging.Logger
    """
    rectifyImageWithClipAndOverviews(
        srcPath,
        dstPath,
        georefParams['algorithm'],
        toGDALGcps(georefParams['gcps']),
        georefParams['target'],
        logger,
        TMP_DIR,
        clip
    )

    if not os.path.exists(dstPath):
        raise Exception('Something went wrong while trying to process georeference image')

    return True

def _syncMapObj(mapObj, georefObj, dbsession, logger):
    """ Syncs the georeference, tms and es record for a given mapObj.

    :param mapObj: Map object
    :type mapObj: georeference.model.map.Map
    :param georefObj: Georeference process object
    :type georefObj: georeference.model.georeferenzierungsprozess.Georeferenzierungsprozess
    :param dbsession: Database session object
    :type dbsession: sqlalchemy.orm.session.Session
    :param logger: Logger
    :type logger: logging.Logger
    :result: True if performed successfully
    :rtype: bool
    """
    try:
        georefFile = mapObj.getAbsGeorefPath()
        logger.debug('Process georefence process wit id "%s" ...' % georefObj.id)
        _processGeoref(
            georefObj.getGeorefParamsAsDict(),
            georefObj.getClipAsGeoJSON(dbsession),
            mapObj.getAbsImagePath(),
            mapObj.getAbsGeorefPath(),
            logger,
        )

        logger.debug('Update the boundingbox of the mapObj ...')
        mapObj.setExtent(
            getExtentFromGeoTIFF(georefFile),
            getSrsFromGeoTIFF(georefFile),
            dbsession
        )

        logger.debug('Process tile map service (TMS) ...')
        calculateCompressedTMS(
            georefFile,
            os.path.join(PATH_TMS_ROOT, str(mapObj.map_type).lower()),
            logger,
            GEOREFERENCE_TMS_PROCESSES,
            mapObj.map_scale
        )

        logger.debug('Finished.')
        return True
    except Exception as e:
        logger.error('Error while trying to snyc a map object.')
        logger.error(e)
        logger.error(traceback.format_exc())

def _processMapObj(mapObj, georefObj, dbsession, logger, esIndex, forceProcessing=False):
    """ Functions performs the processing of a georeference process for a given georefObj and mapObj.

    :param mapObj: Map object
    :type mapObj: georeference.models.map.Map
    :param georefObj: Georeference process. If passed, it syncs the georeference service to the given georeference process.
    :type georefObj: georeference.models.georeference_process.GeoreferenceProcess|None
    :param dbsession: Database session object
    :type dbsession: sqlalchemy.orm.session.Session
    :param logger: Logger
    :type logger: logging.Logger
    :param esIndex: Elsaticsearch client
    :type esIndex: elasticsearch.Elasticsearch
    :param forceProcessing: Signals that the georeference process should also be processed, if there is already a file existing.
    :type forceProcessing: bool
    """
    georefFile = mapObj.getAbsGeorefPath()
    logger.debug('%s %s' % (
        georefFile,
        'does not exist' if georefFile != None and (os.path.exists(georefFile) == False or forceProcessing) and georefObj != None else 'exist')
    )
    if georefFile != None and (os.path.exists(georefFile) == False or forceProcessing) and georefObj != None:
        logger.debug('Map %s is missing a georeference image' % mapObj.id)
        _syncMapObj(
            mapObj,
            georefObj,
            dbsession,
            logger
        )

    # Write documents to es
    logger.debug('Write mapObj %s to index ...' % (mapObj.id))
    searchDocument = generateDocument(
        mapObj,
        Metadata.byId(mapObj.id, dbsession),
        True if georefFile != None and os.path.exists(georefFile) else False,
        dbsession=dbsession,
        logger=logger
    )

    logger.debug(searchDocument)
    esIndex.index(
        index=ES_INDEX_NAME,
        doc_type=None,
        id=mapObj.id,
        body=searchDocument
    )

def _setInValid(job, dbsession, logger, esIndex):
    """ This function sets a georeference process as 'invalid'.

    :param job: AdminJob
    :type job: georeference.models.admin_jobs.AdminJobs
    :param dbsession: Database session
    :type dbsession: sqlalchemy.orm.session.Session
    :param logger: Logger
    :type logger: logging.Logger
    :param esIndex: Elsaticsearch client
    :type esIndex: elasticsearch.Elasticsearch
    """
    logger.debug('Set georeference process for id %s to invalid ...' % job.georef_id)

    # Query georefObj and mapObj
    georefObj = GeoreferenceProcess.by_id(job.geref_id, dbsession)
    mapObj = Map.by_id(georefObj.map_id, dbsession)

    # If the georefObj is enabled disable it
    if georefObj.enabled == True:
        logger.debug('Disable georeference process for id %s ...' % job.georef_id)
        _disableGeorefProcess(
            georefObj,
            mapObj,
            esIndex,
            dbsession,
            logger
        )

    # If the georef process overwrites another active the old one.
    if georefObj.overwrites > 0:
        logger.debug('Enable overwriten georeference process ...')
        logger.debug('Check for a valid overwriten georeference process')
        overwritenGeorefObj = _getLastValidGeoreferenceProcess(georefObj.overwrites, dbsession, logger)

        if overwritenGeorefObj != None:
            logger.debug('Enable a overwriten georeference process with id %s.' % (overwritenGeorefObj.id))

            # Enable the georeference process
            _enableGeorefProcess(
                overwritenGeorefObj,
                mapObj,
                esIndex,
                dbsession,
                logger
            )

    logger.debug('Update validation state for georeference process %s.' % georefObj.id)
    georefObj.validation = job.state
    dbsession.flush()

def _setValid(job, dbsession, logger, esIndex):
    """ This function sets a georeference process as 'valid'.

    :param job: AdminJob
    :type job: georeference.models.admin_jobs.AdminJobs
    :param dbsession: Database session
    :type dbsession: sqlalchemy.orm.session.Session
    :param logger: Logger
    :type logger: logging.Logger
    :param esIndex: Elsaticsearch client
    :type esIndex: elasticsearch.Elasticsearch
    """
    logger.debug('Set georeference process for id %s to valid ...' % job.georef_id)

    # Query georefObj and mapObj
    georefObj = GeoreferenceProcess.by_id(job.geref_id, dbsession)
    mapObj = Map.by_id(georefObj.map_id, dbsession)

    # Query also current active georeference process
    activeGeorefObj = GeoreferenceProcess.getActualGeoreferenceProcessForMapId(georefObj.map_id, dbsession)

    if activeGeorefObj and activeGeorefObj.id >= georefObj.id:
        logger.debug('The georeference process with the id %s or younger process is already active for this map object.'% georefObj.id)
        pass
    elif activeGeorefObj and activeGeorefObj.id < georefObj.id:
        logger.info('Activate the is valide georeference process and deactive old one ...')
        _disableGeorefProcess(
            activeGeorefObj,
            mapObj,
            esIndex,
            dbsession,
            logger
        )
        _enableGeorefProcess(
            georefObj,
            mapObj,
            esIndex,
            dbsession,
            logger
        )
    else:
        logger.info('Activate georeference process %s for the map object %s ...' % (georefObj.id, georefObj.map_id))
        _enableGeorefProcess(
            georefObj,
            mapObj,
            esIndex,
            dbsession,
            logger
        )

    logger.debug('Update validation state for georeference process %s.' % georefObj.id)
    georefObj.validation = job.state
    dbsession.flush()

def runInitializationJob(dbsession, logger):
    """ This job checks the database and initially builds the index and missing georeference images.

    :param dbsession: Database session object
    :type dbsession: sqlalchemy.orm.session.Session
    :param logger: Logger
    :type logger: logging.Logger
    :result: True if performed successfully
    :rtype: bool
    """
    try:
        logger.info('Create index ...')
        esIndex = getIndex(ES_ROOT, ES_INDEX_NAME, True, logger)

        logger.info('Start processing all active maps ...')
        for mapObj in Map.allActive(dbsession):
            _processMapObj(
                mapObj,
                GeoreferenceProcess.getActualGeoreferenceProcessForMapId(mapObj.id, dbsession),
                dbsession,
                logger,
                esIndex
            )
        return True
    except Exception as e:
        logger.error('Error while trying to process initialisation job.')
        logger.error(e)
        logger.error(traceback.format_exc())

def runNewJobs(dbsession, logger):
    """ Checks in the database for new registered jobs and runs them.

    :param dbsession: Database session object
    :type dbsession: sqlalchemy.orm.session.Session
    :param logger: Logger
    :type logger: logging.Logger
    :result: Count of processed jobs
    :rtype: int
    """
    try:
        logger.info('Check for new jobs ...')
        newJobs = GeoreferenceProcess.getUnprocessedObjectsOfTypeNew(dbsession)

        logger.info('Get index ...')
        esIndex = getIndex(ES_ROOT, ES_INDEX_NAME, forceRecreation=False, logger=logger)

        # Process the jobs
        counter = 0
        logger.info('Found %s new jobs. Start processing ...' % counter)
        for job in newJobs:
            logger.info('Process georeference process %s ("new") ...' % job.id)
            mapObj = Map.byId(job.map_id, dbsession)
            georefObj = GeoreferenceProcess.clearRaceConditions(job, dbsession)

            # Enable the georeference process
            _enableGeorefProcess(
                georefObj,
                mapObj,
                esIndex,
                dbsession,
                logger
            )

            logger.info('Finish processing process %s ("new").' % job.id)
            counter += 1
        return counter
    except Exception as e:
        logger.error('Error while trying to process new jobs.')
        logger.error(e)
        logger.error(traceback.format_exc())

def runUpdateJobs(dbsession, logger):
    """ Checks in the database for update registered jobs and runs them.

    :param dbsession: Database session object
    :type dbsession: sqlalchemy.orm.session.Session
    :param logger: Logger
    :type logger: logging.Logger
    :result: Count of processed jobs
    :rtype: int
    """
    try:
        logger.info('Check for update jobs ...')
        newJobs = GeoreferenceProcess.getUnprocessedObjectsOfTypeUpdate(dbsession)

        logger.info('Get index ...')
        esIndex = getIndex(ES_ROOT, ES_INDEX_NAME, forceRecreation=False, logger=logger)

        # Process the jobs
        counter = 0
        logger.info('Found %s update jobs. Start processing ...' % counter)
        for job in newJobs:
            logger.info('Process georeference process %s ("update") ...' % job.id)
            mapObj = Map.byId(job.map_id, dbsession)
            georefObj = GeoreferenceProcess.clearRaceConditions(job, dbsession)

            # Check if there is an active georeference process and if yes disable it
            activeGeorefProcess = GeoreferenceProcess.getActualGeoreferenceProcessForMapId(job.map_id, dbsession)
            if activeGeorefProcess != None:
                logger.info('Deactivate georeference processes with id %s ...' % activeGeorefProcess.id)
                activeGeorefProcess.setDeactive()

            # Enable the georeference process
            _enableGeorefProcess(
                georefObj,
                mapObj,
                esIndex,
                dbsession,
                logger
            )

            logger.info('Finish processing process %s ("update").' % job.id)
            counter += 1
        return counter
    except Exception as e:
        logger.error('Error while trying to process update jobs.')
        logger.error(e)
        logger.error(traceback.format_exc())

def runAdminJobs(dbsession, logger):
    """ Checks in the database for new admin jobs and runs them.

    :param dbsession: Database session object
    :type dbsession: sqlalchemy.orm.session.Session
    :param logger: Logger
    :type logger: logging.Logger
    :result: Count of processed jobs
    :rtype: int
    """
    try:
        logger.info('Check for admin jobs ...')
        newJobs = AdminJobs.getUnprocessedJobs(dbsession)

        logger.info('Get index ...')
        esIndex = getIndex(ES_ROOT, ES_INDEX_NAME, forceRecreation=False, logger=logger)

        # Process the jobs
        counter = 0
        logger.info('Found %s update jobs. Start processing ...' % counter)
        for job in newJobs:
            if job.state == 'invalid':
                _setInValid(
                    job,
                    dbsession,
                    logger,
                    esIndex
                )
                job.processed = True
            elif job.state == 'valid':
                job.processed = True
            logger.info('Finish processing process %s ("admin").' % job.id)
            counter += 1
        return counter
    except Exception as e:
        logger.error('Error while trying to process admin jobs.')
        logger.error(e)
        logger.error(traceback.format_exc())