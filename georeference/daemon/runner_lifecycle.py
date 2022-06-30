#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 09.12.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import os
import logging
import time
import traceback
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from pyramid.paster import get_appsettings
from logging.handlers import TimedRotatingFileHandler

# For correct resolving of the paths we use derive the base_path of the file
BASE_PATH = os.path.dirname(os.path.realpath(__file__))
BASE_PATH_PARENT = os.path.abspath(os.path.join(BASE_PATH, '../../'))
sys.path.insert(0, BASE_PATH)
sys.path.append(BASE_PATH_PARENT)

from georeference.jobs.initialize_data import run_initialize_data
from georeference.jobs.process_create_map import run_process_create_map
from georeference.jobs.process_delete_map import run_process_delete_maps
from georeference.jobs.process_update_maps import run_process_update_maps
from georeference.jobs.process_create_mosaic_map import run_process_create_mosiac_map
from georeference.jobs.process_delete_mosaic_map import run_process_delete_mosiac_map
from georeference.jobs.process_transformation import run_process_new_transformation
from georeference.jobs.set_validation import run_process_new_validation
from georeference.models import Job
from georeference.models.jobs import EnumJobType, EnumJobState, JobHistory
from georeference.settings import DAEMON_LOGGER_SETTINGS
from georeference.utils import create_data_directories
from georeference.utils.es_index import get_es_index
from georeference.utils.logging import create_logger

from georeference.settings import ES_ROOT, ES_INDEX_NAME
from georeference.utils.utils import without_keys

job_run_handlers = {
    EnumJobType.MAPS_CREATE.value: run_process_create_map,
    EnumJobType.MAPS_UPDATE.value: run_process_update_maps,
    EnumJobType.MAPS_DELETE.value: run_process_delete_maps,
    EnumJobType.TRANSFORMATION_SET_VALID.value: run_process_new_validation,
    EnumJobType.TRANSFORMATION_SET_INVALID.value: run_process_new_validation,
    EnumJobType.TRANSFORMATION_PROCESS.value: run_process_new_transformation,
    EnumJobType.MOSAIC_MAP_CREATE: run_process_create_mosiac_map,
    EnumJobType.MOSAIC_MAP_DELETE: run_process_delete_mosiac_map
}


def _reset_logging(logger):
    list(map(logger.removeHandler, logger.handlers))
    list(map(logger.removeFilter, logger.filters))
    logging.shutdown()


def _initialize_database_session(ini_file):
    """ Functions loads and initialize a database session

    :param ini_file: File to production.ini
    :type ini_file: str
    :result: Database session object
    :rtype: sqlalchemy.orm.session.Session
    """
    # Create database engine from production.ini configuration
    dbengine = create_engine(
        get_appsettings(ini_file)['sqlalchemy.url'],
        encoding='utf8',
        # Set echo=True if te sqlalchemy.url logging output sould be displayed
        echo=False,
    )

    # Create and return session object
    db_sessionmaker = sessionmaker(bind=dbengine)
    Base = declarative_base()
    Base.metadata.bind = dbengine
    Base.metadata.create_all(dbengine)
    return db_sessionmaker()


def _initialize_logger():
    """ Function loads and create the logger for the daemon

    :result: Logger
    :rtype: `logging.Logger`
    """
    # Check if the file exists and if not create it
    if not os.path.exists(DAEMON_LOGGER_SETTINGS['file']):
        open(DAEMON_LOGGER_SETTINGS['file'], 'a').close()

    handler = TimedRotatingFileHandler(DAEMON_LOGGER_SETTINGS['file'], when='d', interval=1, backupCount=14)

    # Configure the handler as a TimeRotatingFileHander
    handler.setFormatter(
        logging.Formatter(DAEMON_LOGGER_SETTINGS['formatter'])
    )

    # Create and initialize the logger
    return create_logger(
        DAEMON_LOGGER_SETTINGS['name'],
        DAEMON_LOGGER_SETTINGS['level'],
        handler=handler,
    )


def loop(dbsession, logger, handlers):
    """ Iteration holding the main functionality

    :param logger: Logger
    :type logger: logging.Logger
    :param dbsession: Database session object
    :type dbsession: sqlalchemy.orm.session.Session
    :param handlers: Map job names to a handler
    :type handlers: dict<EnumJobName, function>
    """
    try:
        logger.info('Looking for pending jobs ...')
        es_index = get_es_index(ES_ROOT, ES_INDEX_NAME, force_recreation=False, logger=logger)

        for job in Job.query_not_started_jobs([e.value for e in EnumJobType], dbsession):
            job_id = job.id
            try:
                run = handlers.get(job.type)
                logger.info(f'Start running job with id {job.id} of type {job.type} ...')
                run(es_index, dbsession, logger, job)

                logger.info(f'Job of type {job.type} was finished successful')
                job.state = EnumJobState.COMPLETED.value
            except Exception as e:
                logger.error(f'Error while trying to process job {job_id} of type "{job.type}".')
                logger.error(e)
                logger.error(traceback.format_exc())

                # Rollback previous changes, as the job could not be completed successfully
                dbsession.rollback()

                # Update job state
                job = dbsession.query(Job).filter(Job.id == job_id).first()
                job.state = EnumJobState.FAILED.value

                # assign the error including message to the comment field
                # one might pass custom error messages by raising custom exceptions in the job runners
                job.comment = str(e)

            finally:
                # add job to job_history table
                job_history_entry = JobHistory(**without_keys(job.__dict__, ["_sa_instance_state"]))
                dbsession.add(job_history_entry)
                dbsession.commit()

                # remove job from job table
                dbsession.delete(job)
                logger.debug(job.__dict__)

                # commit session
                dbsession.commit()
            logger.info("Processed job with id %s." % job.id)

        # Close es connection
        es_index.close()

        logger.debug('Close database connection.')
        dbsession.close()

        logger.info('Processed all pending jobs.')
    except Exception as e:
        logger.error('Error while running the daemon')
        logger.error(e)
        logger.error(traceback.format_exc())


def on_start(logger=None, dbsession=None):
    """Should be called once on daemon startup

    :param logger: Logger
    :type logger: logging.Logger
    :param dbsession: Database session object
    :type dbsession: sqlalchemy.orm.session.Session
    """
    try:
        logger.info('Starting the daemon ...')

        logger.info('Make sure data directories are existing ...')
        create_data_directories()

        logger.info('Initialize geo and index data ...')
        run_initialize_data(dbsession, logger)

        dbsession.commit()
        dbsession.close()
        logger.info('Initialization of the daemon has finished. Waiting for changes...')
    except Exception as e:
        logger.error('Error while starting the daemon')
        logger.error(e)
        logger.error(traceback.format_exc())


def main(logger=None, dbsession=None, ini_file=None, wait_on_start=1, wait_on_loop=1):
    """ Daemon main run.

    :param logger: Logger
    :type logger: logging.Logger
    :param dbsession: Database session object
    :type dbsession: sqlalchemy.orm.session.Session
    :param ini_file: File to production.ini
    :type ini_file: str
    :param wait_on_start: Seconds to wait on startup
    :type wait_on_start: int
    :param wait_on_loop: Seconds to wait after each loop
    :type wait_on_loop: int
    """
    try:
        log = _initialize_logger() if logger is None else logger
        log.info('Start logger but waiting for %s seconds ...' % wait_on_start)
        time.sleep(wait_on_start)

        # Start the daemon
        db = _initialize_database_session(ini_file) if ini_file is not None else dbsession
        if db is None:
            logger.error("Could not initialize database because of missing configuration file")
            raise

        on_start(logger=log, dbsession=db)

        while True:
            if logger is None:
                # In the logger was passed external we skip the temporal shutdown
                _reset_logging(log)

            # To prevent the daemon from having to long lasting logger handles or database session we reinitialize / reset
            # both before each loop
            log = _initialize_logger() if logger is None else logger
            log.info('################################')
            log.debug('Initialize database')
            db = _initialize_database_session(ini_file) if ini_file is not None else dbsession
            loop(db, log, job_run_handlers)
            log.info('Sleep for %s seconds.' % wait_on_loop)
            time.sleep(wait_on_loop)
    except Exception as e:
        log.error('Error while running the daemon')
        log.error(e)
        log.error(traceback.format_exc())
    finally:
        log.info("Clean up")
        logging.shutdown()

if __name__ == '__main__':
    ini_file = os.path.join(BASE_PATH, '../../development.ini')
    log = logging.getLogger(__name__)
    log.info('################################')
    log.debug('Initialize database')
    db = _initialize_database_session(ini_file)
    loop(db, log, job_run_handlers)