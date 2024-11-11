#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Created by jacob.mendt@pikobytes.de on 31.10.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import argparse
import logging
import os
import sys
import json
from loguru import logger

from georeference.config.db import get_session
from georeference.config.logging_config import parse_log_level
from georeference.config.settings import get_settings
from georeference.models.georef_map import GeorefMap
from georeference.models.transformation import Transformation
from georeference.models.raw_map import RawMap
from georeference.utils.utils import get_tms_directory
from georeference.jobs.actions.create_tms import run_process_tms

# For correct resolving of the paths we use derive the base_path of the file
BASE_PATH = os.path.dirname(os.path.realpath(__file__))
BASE_PATH_PARENT = os.path.abspath(os.path.join(BASE_PATH, "../../"))
sys.path.insert(0, BASE_PATH)
sys.path.append(BASE_PATH_PARENT)

# Define path of the process log
PATH_PROCESS_LOG = os.path.join(get_settings().PATH_DATA_ROOT, "tasks/process.log")


def _initialize_logger():
    """Function loads and create the logger for the daemon"""

    # # Configure the handler as a TimeRotatingFileHander
    logger.remove()
    log_level = parse_log_level(get_settings().LOG_LEVEL)

    logger.add(sys.stderr, level=log_level, colorize=True)
    logger.debug("Load logger.")


def _read_json_file(file):
    if os.path.exists(file) is False:
        return {}

    # Read and parse the JSON content from a given file path
    with open(file, "r") as f:
        return json.load(f)


def _write_json_file(file, json_content):
    # Write the JSON content to a given file path
    with open(file, "w") as f:
        json.dump(json_content, f, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Scripts for reprocessing all TMS for transformation with a target crs of 4314."
    )
    parser.add_argument(
        "--job_number",
        help="Number of jobs to process on one run.",
        type=int,
        default=1,
    )

    # Parse command-line arguments
    args = parser.parse_args(sys.argv[1:])

    try:
        _initialize_logger()

        logger.info("Load database session.")
        session = next(get_session())
        if session is None:
            logger.error(
                "Could not initialize database because of missing configuration file"
            )
            raise

        logger.info("Load process log.")
        process_log = _read_json_file(PATH_PROCESS_LOG)
        jobs = (
            process_log["jobs"]
            if "jobs" in process_log
            else {
                "pending": [],
                "pending_number": 0,
                "finished": [],
                "finished_number": 0,
            }
        )
        job_number = args.job_number

        # Generate job for all relevant georef maps
        if jobs["pending_number"] == 0 and jobs["finished_number"] == 0:
            logger.info("Generate job list")
            all_georef_maps = GeorefMap.all(session)
            for georef_map in all_georef_maps:
                transformation = Transformation.by_id(
                    georef_map.transformation_id, session
                )
                logger.debug(transformation.target_crs)
                if transformation.target_crs == 4314:
                    jobs["pending"].append(georef_map.raw_map_id)
                    jobs["pending_number"] += 1
        else:
            logger.info("Skip generation of job list. It already exists.")

        # Process the jobs
        counter_processed_jobs = 0
        for raw_map_id in jobs["pending"].copy():
            if counter_processed_jobs >= job_number:
                break

            logger.info("Process job with raw map id %s." % raw_map_id)
            raw_map = RawMap.by_id(raw_map_id, session)
            georef_map = GeorefMap.by_raw_map_id(raw_map_id, session)
            path_geo_image = georef_map.get_abs_path()
            path_tms_directory = get_tms_directory(raw_map)

            if raw_map_id in jobs["finished"]:
                logger.info(
                    "Skip job with raw map id %s, because it is already processed."
                    % raw_map_id
                )
                continue
            else:
                logger.info("Recalculate TMS for raw map id %s." % raw_map_id)
                counter_processed_jobs += 1
                run_process_tms(path_tms_directory, path_geo_image, force=True)
                jobs["finished"].append(raw_map_id)
                jobs["finished_number"] = len(jobs["finished"])
                jobs["pending"].remove(raw_map_id)
                jobs["pending_number"] = len(jobs["pending"])

    except Exception as e:
        logger.info("Error while running the fix tms script!")
        logger.error(e)
    finally:
        logger.info("=========================================================")
        logger.info(f"Pending jobs: {jobs['pending_number']}")
        logger.info(f"Finished jobs: {jobs['finished_number']}")

        # Write the json dictionary to the log file
        _write_json_file(PATH_PROCESS_LOG, {"jobs": jobs})

        logger.info("Clean up")
        if session is not None:
            session.close()
        logging.shutdown()
