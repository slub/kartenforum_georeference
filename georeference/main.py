#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by nicolas.looschen@pikobytes.de on 24.07.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from georeference.config.logging_config import configure_logging
from georeference.config.paths import create_data_directories
from georeference.config.sentry import setup_sentry
from georeference.config.settings import get_settings
from georeference.routers import (
    user,
    statistics,
    jobs,
    map_view,
    maps,
    mosaic_maps,
    transformations,
)
from georeference.utils.init_helper import log_startup_information, enable_cors_middleware

# Initialization
logger = configure_logging()
setup_sentry()

logger.debug("Initialize settings")
settings = get_settings()
logger.debug(json.dumps(settings.model_dump(), indent=2))

logger.debug("Create data directories")
create_data_directories()

logger.debug("Initialize FastAPI...")
app = FastAPI()

# Setup CORS middleware, but just if it is enabled. In production setups CORS should be handled from the proxy service.
if (settings.CORS_ENABLED):
    enable_cors_middleware(app, settings)

# In case the FastAPI is started in dev_mode and with dev_mode_secret, print a big warning
log_startup_information(settings)

# Register routers
logger.debug("Initialize routes ...")
app.include_router(user.router, prefix="/user")
app.include_router(statistics.router, prefix="/statistics")
app.include_router(jobs.router, prefix="/jobs")
app.include_router(map_view.router, prefix="/map_view")
app.include_router(maps.router, prefix="/maps")
app.include_router(mosaic_maps.router, prefix="/mosaic_maps")
app.include_router(transformations.router, prefix="/transformations")

logger.debug("Initialization done.")
