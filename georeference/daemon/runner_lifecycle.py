#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

# Created by jacob.mendt@pikobytes.de on 09.12.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import os
import sys
import time
import traceback

from loguru import logger

from georeference.config.db import get_session
from georeference.config.logging_config import parse_log_level
from georeference.config.paths import create_data_directories
from georeference.config.sentry import setup_sentry
from georeference.config.settings import get_settings
from georeference.jobs.initialize_data import run_initialize_data
from georeference.jobs.process_create_map import run_process_create_map
from georeference.jobs.process_create_mosaic_map import run_process_create_mosaic_map
from georeference.jobs.process_delete_map import run_process_delete_maps
from georeference.jobs.process_delete_mosaic_map import run_process_delete_mosaic_map
from georeference.jobs.process_transformation import run_process_new_transformation
from georeference.jobs.process_update_maps import run_process_update_maps
from georeference.jobs.set_validation import run_process_new_validation
from georeference.models.enums import EnumJobType, EnumJobState
from georeference.models.job import Job, JobHistory
from georeference.utils.es_index import get_es_index_from_settings
from georeference.utils.init_helper import log_startup_information

# For correct resolving of the paths we use derive the base_path of the file
BASE_PATH = os.path.dirname(os.path.realpath(__file__))
BASE_PATH_PARENT = os.path.abspath(os.path.join(BASE_PATH, "../../"))
sys.path.insert(0, BASE_PATH)
sys.path.append(BASE_PATH_PARENT)

job_run_handlers = {
    EnumJobType.MAPS_CREATE.value: run_process_create_map,
    EnumJobType.MAPS_UPDATE.value: run_process_update_maps,
    EnumJobType.MAPS_DELETE.value: run_process_delete_maps,
    EnumJobType.TRANSFORMATION_SET_VALID.value: run_process_new_validation,
    EnumJobType.TRANSFORMATION_SET_INVALID.value: run_process_new_validation,
    EnumJobType.TRANSFORMATION_PROCESS.value: run_process_new_transformation,
    EnumJobType.MOSAIC_MAP_CREATE.value: run_process_create_mosaic_map,
    EnumJobType.MOSAIC_MAP_DELETE.value: run_process_delete_mosaic_map,
}

settings = get_settings()


def _reset_logging(logger):
    list(map(logger.removeHandler, logger.handlers))
    list(map(logger.removeFilter, logger.filters))
    logging.shutdown()


def _initialize_logger():
    """Function loads and create the logger for the daemon"""

    # # Configure the handler as a TimeRotatingFileHander
    logger.remove()
    log_level = parse_log_level(settings.DAEMON_LOG_LEVEL)

    if settings.DAEMON_LOGFILE_PATH is not None:
        logger.add(
            settings.DAEMON_LOGFILE_PATH,
            level=log_level,
            rotation="daily",
            retention="14 days",
        )
    logger.add(sys.stderr, level=log_level, colorize=True)

    # Setup sentry sdk
    setup_sentry()
    logger.debug("Logger initialized")


def loop(dbsession, handlers, es_index):
    """Iteration holding the main functionality

    :param dbsession: Database session object
    :type dbsession: sqlalchemy.orm.session.Session
    :param handlers: Map job names to a handler
    :type handlers: dict<EnumJobName, function>
    :param es_index: Elasticsearch index object
    :type es_index: elasticsearch.client.IndicesClient
    """
    try:
        logger.info("Looking for pending jobs ...")

        for job in Job.query_not_started_jobs(
            [e.value for e in EnumJobType], dbsession
        ):
            job_id = job.id
            try:
                run = handlers.get(job.type)
                logger.info(
                    f"Start running job with id {job.id} of type {job.type} ..."
                )
                run(es_index, dbsession, job)

                logger.info(f"Job of type {job.type} was finished successful")
                job.state = EnumJobState.COMPLETED.value
            except Exception as e:
                logger.info(
                    f'Error while trying to process job {job_id} of type "{job.type}".'
                )

                if settings.DEV_MODE:
                    logger.error(traceback.format_exc())
                logger.error(e)

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
                job_history_entry = JobHistory(**job.model_dump())
                dbsession.add(job_history_entry)
                dbsession.commit()

                # remove job from job table
                dbsession.delete(job)
                logger.debug(job.model_dump())

                # commit session
                dbsession.commit()
            logger.info("Processed job with id %s." % job.id)

        logger.debug("Close database connection.")
        dbsession.close()

        logger.info("Processed all pending jobs.")
    except Exception as e:
        logger.info("Error while running the daemon")

        if settings.DEV_MODE:
            logger.error(traceback.format_exc())
        logger.error(e)


def on_start(dbsession=None):
    """Should be called once on daemon startup

    :param dbsession: Database session object
    :type dbsession: sqlalchemy.orm.session.Session
    """
    try:
        logger.info("Starting the daemon ...")

        logger.info("Make sure data directories are existing ...")
        create_data_directories()

        logger.info("Initialize geo and index data ...")
        run_initialize_data(dbsession)

        dbsession.commit()
        dbsession.close()
        logger.info("Initialization of the daemon has finished. Waiting for changes...")
    except Exception as e:
        logger.info("Error while starting the daemon")
        logger.error(e)


def main(wait_on_start=1, wait_on_loop=1):
    """Daemon main run.

    :param wait_on_start: Seconds to wait on startup
    :type wait_on_start: int
    :param wait_on_loop: Seconds to wait after each loop
    :type wait_on_loop: int
    """
    try:
        run_count = 0
        _initialize_logger()
        logger.info(f"Start logger but waiting for {wait_on_start} seconds ...")
        log_startup_information(settings)
        time.sleep(wait_on_start)

        # Handle start
        session = next(get_session())
        if session is None:
            logger.error(
                "Could not initialize database because of missing configuration file"
            )
            raise
        on_start(dbsession=session)
        session.close()

        while True:
            if run_count % settings.DAEMON_LOOP_HEARTBEAT_COUNT == 0:
                # send heartbeat to sentry
                logger.error("Sentry Heartbeat. Daemon is still running ...")
                run_count = 0

            # To prevent the daemon from having to long lasting logger handles or database session we reinitialize / reset
            # both before each loop
            logger.info("################################")
            logger.info("Starting new loop ...")

            logger.debug("Initialize database")
            # get the database session
            session = next(get_session())
            if session is None:
                logger.error(
                    "Could not initialize database because of missing configuration file"
                )
                raise

            logger.debug("Initialize search index")
            # get the elasticsearch index
            es_index = get_es_index_from_settings(False)
            if es_index is None:
                logger.error("Could not initialize elasticsearch index")
                raise

            loop(session, job_run_handlers, es_index)
            logger.info(f"Sleep for {wait_on_loop} seconds.")

            session.close()
            es_index.close()

            time.sleep(wait_on_loop)
            run_count += 1
    except Exception as e:
        logger.info("Error while running the daemon")
        logger.error(e)
    finally:
        logger.info("Clean up")
        logging.shutdown()


def run_without_daemon():
    main(
        wait_on_start=settings.DAEMON_WAIT_ON_STARTUP,
        wait_on_loop=settings.DAEMON_SLEEP_TIME,
    )


if __name__ == "__main__":
    logger.info("################################")
    logger.debug("Initialize database")
    session = next(get_session())
    es_index = get_es_index_from_settings(False)
    loop(session, job_run_handlers, es_index)
