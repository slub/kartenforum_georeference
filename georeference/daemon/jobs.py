#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 16.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import traceback
import json
import os
from sqlalchemy import or_
from georeference.models.jobs import Job, TaskValues
from georeference.models.transformations import Transformation, ValidationValues
from georeference.daemon.utils import disableTransformation
from georeference.daemon.utils import enableTransformation
from georeference.daemon.utils import getGeometry
from georeference.daemon.utils import _processGeoTransformation
from georeference.models.georef_maps import GeorefMap
from georeference.models.original_maps import OriginalMap
from georeference.models.metadata import Metadata
from georeference.settings import ES_ROOT
from georeference.settings import ES_INDEX_NAME
from georeference.scripts.es import generateDocument
from georeference.scripts.es import getIndex
from georeference.settings import PATH_TMP_ROOT
from georeference.settings import PATH_GEOREF_ROOT
from georeference.settings import PATH_IMAGE_ROOT
from georeference.settings import PATH_TMS_ROOT
from georeference.settings import PATH_MAPFILE_ROOT
from georeference.utils import createPathIfNotExists

# Make sure that necessary directory exists
createPathIfNotExists(PATH_TMP_ROOT)
createPathIfNotExists(PATH_GEOREF_ROOT)
createPathIfNotExists(PATH_TMS_ROOT)
createPathIfNotExists(PATH_IMAGE_ROOT)
createPathIfNotExists(PATH_MAPFILE_ROOT)

def _getLastValidTransformation(overwriteId, dbsession, logger):
    """ This function goes down the overwrite chain and looks for the last valid
        transformation

    :param overwriteId: Last overwrite id
    :type overwriteId: int
    :param dbsession: Database session
    :type dbsession: sqlalchemy.orm.session.Session
    :param logger: Logger
    :type: logger: logging.Logger
    :result: Returns a valid georeference process if existing
    :rtype: georeference.models.transformations.Transformation|None
    """
    if overwriteId == 0:
        return None

    transformationObj = Transformation.byId(overwriteId, dbsession)
    if transformationObj.validation == ValidationValues.VALID.value or transformationObj.validation == ValidationValues.MISSING.value:
        return transformationObj
    elif transformationObj.overwrites > 0:
        return _getLastValidTransformation(transformationObj.overwrites, dbsession, logger)
    else:
        return None

def getUnprocessedJobs(dbsession, logger):
    """ Checks for unprocssed jobs, groups them and clears race condition for new transformations.

    :param dbsession: Database session
    :type dbsession: sqlalchemy.orm.session.Session
    :param logger: Logger
    :type logger: logging.Logger
    :result: Dictionary containing unprocessed jobs group by "process" and "validation"
    :rtype: {{
        process: Transformation[],
        validation: Transformation[]
    }}
    """
    try:
        # Extract all unprocessed jobs and group them
        rawProcess =  dbsession.query(Job).filter(Job.processed == False)\
            .filter(Job.task_name == TaskValues.TRANSFORMATION_PROCESS.value)\
            .all()
        rawValidation = dbsession.query(Job).filter(Job.processed == False)\
            .filter(or_(Job.task_name == TaskValues.TRANSFORMATION_SET_INVALID.value, Job.task_name == TaskValues.TRANSFORMATION_SET_VALID.value))\
            .all()

        # It is possible that there are race conditions between different raw process. A race condition means a case,
        # where are two unprocessed transformations for the same original_map_id. In this case, the last one should be transformed
        unique_process = {}
        for rp in rawProcess:
            logger.info("Job: %s | %s" % (rp.task_name, rp.task))

            # Query transformation and get mapId
            task = json.loads(rp.task)
            transformation = Transformation.byId(task['transformation_id'], dbsession)

            # Make sure that only on job of kind "transformation_process" is processed for each mapId
            if transformation != None:
                mapId = str(transformation.original_map_id)
                if mapId in unique_process:
                    if unique_process[mapId].submitted > rp.submitted:
                        # Hold the alreay registered process and set the new process to processed
                        rp.processed = True
                    else:
                        # Skip the current registered process and set it to processed
                        unique_process[mapId].processed = True
                        unique_process[mapId] = rp
                else:
                    unique_process[mapId] = rp
            else:
                # In this case a transformation could not be find for the rp and we mark it as processed
                rp.processed = True

        # Make sure to flush any database changes.
        dbsession.flush()

        return {
            'process': list(unique_process.values()),
            'validation': rawValidation,
        }
    except Exception as e:
        logger.error('Error while trying to extract unprocessed jobs.')
        logger.error(e)
        logger.error(traceback.format_exc())

def runProcessJobs(jobs, esIndex, dbsession, logger):
    """ Runs jobs of type "transformation_process"

    :param jobs: Jobs
    :type jobs: georeference.models.jobs.Job
    :param esIndex: Elasticsearch client
    :type esIndex: elasticsearch.Elasticsearch
    :param dbsession: Database session
    :type dbsession: sqlalchemy.orm.session.Session
    :param logger: Logger
    :type logger: logging.Logger
    :result: Dictionary containing processed jobs
    :rtype: {{
        process: Transformation[],
    }}
    """
    try:
        processed_transformations = []
        for job in jobs:
            # Query the associated transformation process
            task = json.loads(job.task)
            transformation = Transformation.byId(task['transformation_id'], dbsession)

            # Process the transformation
            enableTransformation(
                transformation,
                esIndex,
                dbsession,
                logger
            )

            processed_transformations.append(transformation)
            job.processed = True

        return {
            'processed_transformations': processed_transformations,
        }
    except Exception as e:
        logger.error('Error while trying to process jobs of type "transformation_process".')
        logger.error(e)
        logger.error(traceback.format_exc())

def runValidationJobs(jobs, esIndex, dbsession, logger):
        """ Runs jobs of type "transformation_set_valid" or "transformation_set_invalid"

        :param jobs: Jobs
        :type jobs: georeference.models.jobs.Job
        :param esIndex: Elasticsearch client
        :type esIndex: elasticsearch.Elasticsearch
        :param dbsession: Database session
        :type dbsession: sqlalchemy.orm.session.Session
        :param logger: Logger
        :type logger: logging.Logger
        :result: Dictionary containing processed jobs
        :rtype: {{
            process: Transformation[],
        }}
        """
        try:
            validation_transformations = []
            for job in jobs:
                # Query the associated transformation process
                task = json.loads(job.task)
                transformation = Transformation.byId(task['transformation_id'], dbsession)

                if job.task_name == TaskValues.TRANSFORMATION_SET_VALID.value:
                    logger.debug('Set transformation %s to valid.' % transformation.id)
                    transformation.validation = ValidationValues.VALID.value
                    transformation.comment = task['comment'] if 'comment' in task else None

                    # Check if there is a georef map registered for the given transformation and if not activate one. If
                    # not we finish here simply with update the validation
                    if GeorefMap.byOriginalMapId(transformation.original_map_id, dbsession) == None:
                        # Process the transformation
                        enableTransformation(
                            transformation,
                            esIndex,
                            dbsession,
                            logger
                        )

                    validation_transformations.append(transformation)
                    job.processed = True
                elif job.task_name == TaskValues.TRANSFORMATION_SET_INVALID.value:
                    logger.info('Set transformation %s to invalid.' % transformation.id)
                    transformation.validation = ValidationValues.INVALID.value
                    transformation.comment = task['comment'] if 'comment' in task else None

                    # Query older georeference process
                    olderValidTransformationObj = _getLastValidTransformation(
                        transformation.overwrites,
                        dbsession,
                        logger
                    )

                    # If there is no older valid transformation make sure that there is no georeference map
                    if GeorefMap.byTransformationId(transformation.id, dbsession) != None and olderValidTransformationObj == None:
                        logger.info('Disable georef map for transformation with id %s ...' % transformation.id)
                        disableTransformation(
                            transformation,
                            esIndex,
                            dbsession,
                            logger
                        )

                    # If there is an older valid transformation for the georeference process enable it
                    if GeorefMap.byTransformationId(transformation.id, dbsession) != None and olderValidTransformationObj != None:
                        logger.info('Enable older transformation with id %s ...' % olderValidTransformationObj.id)
                        enableTransformation(
                            olderValidTransformationObj,
                            esIndex,
                            dbsession,
                            logger
                        )


                    validation_transformations.append(transformation)
                    job.processed = True
                    logger.info("Processed job %s." % job.id)

            return {
                'validation_transformations': validation_transformations,
            }
        except Exception as e:
            logger.error('Error while trying to process jobs of type "transformation_process".')
            logger.error(e)
            logger.error(traceback.format_exc())

def loadInitialData(dbsession, logger):
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
        for originalMapObj in dbsession.query(OriginalMap).filter(OriginalMap.enabled == True):
            georefMapObj = GeorefMap.byOriginalMapId(originalMapObj.id, dbsession)
            metadataObj = Metadata.byId(originalMapObj.id, dbsession)

            if georefMapObj != None and os.path.exists(originalMapObj.getAbsPath()):
                _processGeoTransformation(
                    Transformation.byId(georefMapObj.transformation_id, dbsession),
                    originalMapObj,
                    georefMapObj,
                    metadataObj,
                    logger
                )


            # Write document to es
            logger.debug('Write search record for original map id %s to index ...' % (originalMapObj.id))
            try:
                searchDocument = generateDocument(
                    originalMapObj,
                    Metadata.byId(originalMapObj.id, dbsession),
                    georefMapObj=georefMapObj if georefMapObj != None and os.path.exists(
                        georefMapObj.getAbsPath()) else None,
                    logger=logger,
                    geometry=getGeometry(originalMapObj.id, dbsession)
                )
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
        return True
    except Exception as e:
        logger.error('Error while trying to process initialisation job.')
        logger.error(e)
        logger.error(traceback.format_exc())


