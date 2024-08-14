"""
Created by nicolas.looschen@pikobytes.de on 08.07.2024.

This file is subject to the terms and conditions defined in
file 'LICENSE.txt', which is part of this source code package.
"""

import os
from functools import lru_cache
from typing import Annotated, Optional

from pydantic import AfterValidator
from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib3.util import parse_url

from georeference.config.paths import BASE_PATH


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
            os.path.join(BASE_PATH, "../", ".env"),
            os.path.join(BASE_PATH, "../", ".env.production"),
        ]
    )

    # Daemon setting
    DAEMON_PIDFILE_PATH: str = os.path.join(BASE_PATH, "../tmp/daemon.pid")
    DAEMON_PIDFILE_TIMEOUT: int = 5
    DAEMON_SLEEP_TIME: int = 10
    DAEMON_WAIT_ON_STARTUP: int = 1
    DAEMON_LOGFILE_PATH: Optional[str] = os.path.join(BASE_PATH, "../tmp/daemon.log")
    DAEMON_LOG_LEVEL: str = "DEBUG"
    DAEMON_LOOP_HEARTBEAT_COUNT: int = 10


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
