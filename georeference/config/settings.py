#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Created by nicolas.looschen@pikobytes.de on 28.08.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package

import os
from functools import lru_cache
from typing import Annotated, Optional

from pydantic import AfterValidator
from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib3.util import parse_url

# For correct resolving of the paths we use derive the base_path of the file
# the base path is the application root, resolved in the following way:
#
# __file__ -> /georeference/config/paths.py
# os.path.dirname(os.path.realpath(__file__)) -> /georeference/config
# os.path.join(os.path.dirname(os.path.realpath(__file__)), "../") -> /georeference/
BASE_PATH = os.path.normpath(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), "../")
)


def is_https(value: str):
    parsed_uri = parse_url(value)
    if parsed_uri.scheme != "https":
        raise ValueError("URL has to be HTTPS!")
    return value


TYPO3_URL_TYPE = Annotated[str, AfterValidator(is_https)]


class Settings(BaseSettings):
    # Role configuration
    ADMIN_ROLE: str = "vk2-admin"
    USER_ROLE: str = "vk2-user"

    # CORS CONFIGURATION
    CORS_ENABLED: bool = True
    CORS_ALLOWED_ORIGINS: list[str] = [
        "https://ddev-kartenforum.ddev.site",
        "http://localhost:3000",
    ]

    # DEV MODE
    DEV_MODE: bool = False

    # DEV_MODE AUTH BYPASS SECRET
    DEV_MODE_SECRET: Optional[str] = None

    LOG_LEVEL: str = "WARNING"

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int

    # Settings for the database connection pool
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    # Elasticsearch settings
    ES_HOST: str = "localhost"
    ES_PORT: int = 9200
    ES_SSL: bool = False
    ES_USERNAME: Optional[str] = None
    ES_PASSWORD: Optional[str] = None

    # Name of the search index
    ES_INDEX_NAME: str = "vk20"

    # HAS TO BE HTTPS!
    TYPO3_URL: TYPO3_URL_TYPE = "https://ddev-kartenforum.ddev.site"

    # Gdal settings
    # GDAL_CACHEMAX - This setting can influence the georeference speed. For more information see https://gdal.org/user/configoptions.html
    GDAL_CACHEMAX: int = 1500

    # WARP_MEMORY - This setting can influence the georeference speed. For more information see https://gdal.org/programs/gdalwarp.html
    GDAL_WARP_MEMORY: int = 1500

    # GDAL_NUM_THREADS - This setting can influence the georeference speed. For more information see https://gdal.org/user/configoptions.html
    GDAL_NUM_THREADS: int = 3

    # TMS configuration
    GLOBAL_TMS_PROCESSES: int = 2

    # Sentry configuration
    SENTRY_DSN: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=[
            os.path.abspath(os.path.join(BASE_PATH, "../", ".env")),
            os.path.abspath(os.path.join(BASE_PATH, "../", ".env.production")),
        ]
    )

    # Upload limits
    MAX_FILE_SIZE: int = 1024 * 1024 * 1024 * 4  # = 4GB
    MAX_REQUEST_BODY_SIZE: int = MAX_FILE_SIZE + (1024 * 10)

    # Daemon setting
    DAEMON_PIDFILE_PATH: str = os.path.abspath(
        os.path.join(BASE_PATH, "../tmp/daemon.pid")
    )
    DAEMON_PIDFILE_TIMEOUT: int = 5
    DAEMON_SLEEP_TIME: int = 10
    DAEMON_WAIT_ON_STARTUP: int = 1
    DAEMON_LOGFILE_PATH: Optional[str] = os.path.abspath(
        os.path.join(BASE_PATH, "../tmp/daemon.log")
    )
    DAEMON_LOG_LEVEL: str = "DEBUG"
    DAEMON_LOOP_HEARTBEAT_COUNT: int = 10

    # Configuration of the data root directory
    PATH_BASE_ROOT: str = BASE_PATH
    PATH_DATA_ROOT: str = os.path.abspath(os.path.join(BASE_PATH, "../data"))

    # Configuration of link and id schemas
    TEMPLATE_TMS_URLS: list[str] = ["https://tms.ddev.site/{}"]
    TEMPLATE_WMS_URL: str = "https://wms.ddev.site/map/{}"
    TEMPLATE_WMS_TRANSFORM_URL: str = "https://wms-transform.ddev.site/map/{}"
    TEMPLATE_WCS_URL: str = "https://wcs.ddev.site/map/{}"
    TEMPLATE_ZOOMIFY_URL: str = "https://zoomify.ddev.site/{}/ImageProperties.xml"
    TEMPLATE_THUMBNAIL_URL: str = "https://thumbnails.ddev.site/{}"

    # Overwrites are used within the local development setup. In production, they should be set to null
    OVERWRITE_MAPFILE_TMP_PATH: str = ""


# For usage of the settings as dependency
@lru_cache
def get_settings():
    return Settings(_env_parse_none_str="null")


#
# Settings of the daemon. For more information regarding the supported log level see
# https://docs.python.org/3/library/logging.html#levels
#

# Settings for the georeference persistent
DAEMON_SETTINGS = {
    "stdin": os.path.join(BASE_PATH, "../tmp/null"),
    "stdout": os.path.join(BASE_PATH, "../tmp/tty"),
    "stderr": os.path.join(BASE_PATH, "../tmp/tty"),
}
