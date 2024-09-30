#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 25.09.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import json
from loguru import logger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from georeference.config.settings import Settings


def enable_cors_middleware(app: FastAPI, settings: Settings):
    logger.debug("Setup CORS settings ...")
    allowed_origins = settings.CORS_ALLOWED_ORIGINS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

def log_startup_information(settings: Settings):
    # Information regarding the used configuration
    logger.debug("Service is start with the following configuration:")
    logger.debug("")
    logger.debug(json.dumps(settings.model_dump(), indent=2))
    logger.debug("")

    # Warning in case of dangerous configuration
    if settings.DEV_MODE and settings.DEV_MODE_SECRET:
        logger.warning("=============================================")
        logger.warning("=============================================")
        logger.warning("Please be aware that the FastAPI is started in DEV_MODE with a configured DEV_MODE_SECRET!")
        logger.warning("Do not use this in production deployments! It's a backdoor!!!")
        logger.warning("=============================================")
        logger.warning("=============================================")