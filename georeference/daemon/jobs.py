#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 16.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import traceback
import os
from ..models.georeferenzierungsprozess import Georeferenzierungsprozess
from ..models.map import Map
from ..settings import PATH_IMAGE_ROOT
from ..settings import PATH_GEOREF_ROOT
from ..utils.georeference import rectifyImageWithClipAndOverviews
from ..utils.parser import toGDALGcps
from .process import activate

def _processGeoref(georefObj, srcPath, dstPath, logger):
    """ Process a given georeference process.

    :param georefObj: Georeferenzierungsprozess
    :type georefObj: georeference.models.georeferenzierungsprozess.Georeferenzierungsprozess
    :param srcPath: Path to the source image
    :type srcPath: str
    :param dstPath: Path of the georeferenced image
    :type dstPath: str
    :param logger: Logger
    :type logger: logging.Logger
    """
    logger.debug('Process georefence process wit id "%s" ...' % georefObj.id)
    rectifyImageWithClipAndOverviews(
        srcPath,
        dstPath,
        georefObj.algorithm,
        toGDALGcps(georefObj)
    )
    if not os.path.exists(dstPath):
        raise Exception('Something went wrong while trying to process georeference image')

    logger.debug('Finished.')

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
        logger.info('Start processing all active maps ...')
        for mapObj in Map.allActive(dbsession):
            if not os.path.exists(mapObj.getAbsGeorefPath()):
                logger.debug('Map %s is missing a georeference image' % mapObj.id)
                georefObj = Georeferenzierungsprozess.getActualGeoreferenceProcessForMapId(mapObj.id, dbsession)
                _processGeoref(
                    georefObj,
                    mapObj.getAbsGeorefPath(),
                    logger,
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
        newJobs = Georeferenzierungsprozess.getUnprocessedObjectsOfTypeNew(dbsession)


        # Process the jobs
        counter = 0
        logger.info('Found %s new jobs. Start processing ...' % counter)
        for job in newJobs:
            logger.info('Process georeference process %s ("new") ...' % job.id)
            georefObj = Georeferenzierungsprozess.clearRaceConditions(job, dbsession)
            mapObj = Map.byId(georefObj.mapid, dbsession)
            activate(georefObj, mapObj, dbsession, logger)
            logger.info('Finish processing process %s ("new").' % job.id)
            counter += 1
        return counter
    except Exception as e:
        logger.error('Error while trying to process new jobs.')
        logger.error(e)
        logger.error(traceback.format_exc())
