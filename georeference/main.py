#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by nicolas.looschen@pikobytes.de on 24.07.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package

from contextlib import asynccontextmanager

from fastapi import FastAPI

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
    vector_map,
)
from georeference.utils.es_index.es_index_async import get_async_es_client
from georeference.utils.init_helper import (
    log_startup_information,
    enable_cors_middleware,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # Close connection to the es index
    es_client = get_async_es_client()
    await es_client.close()


# Initialization
logger = configure_logging()
setup_sentry()

logger.debug("Initialize settings")
settings = get_settings()

logger.debug("Create data directories")
create_data_directories()

logger.debug("Initialize FastAPI...")
app = FastAPI(
    docs_url=("/docs" if settings.SWAGGER_ENABLED else None),
    redoc_url=("/redoc" if settings.REDOC_ENABLED else None),
    openapi_url=("/openapi.json" if settings.OPENAPI_ENABLED else None),
    lifespan=lifespan,
)

# Setup CORS middleware, but just if it is enabled. In production setups CORS should be handled from the proxy service.
if settings.CORS_ENABLED:
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

app.include_router(vector_map.router, prefix="/vector_maps")

logger.debug("Initialization done.")
