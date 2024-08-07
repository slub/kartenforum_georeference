#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by nicolas.looschen@pikobytes.de on 11.07.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import logging
import sys

from loguru import logger

from georeference.config.settings import get_settings


def parse_log_level(log_level: str) -> int:
    numeric_level = getattr(logging, log_level.upper(), None)

    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")

    return numeric_level


def configure_logging():
    # Setup log level from settings
    settings = get_settings()
    log_level = settings.LOG_LEVEL
    numeric_level = parse_log_level(log_level)

    # Remove the default handler
    logger.remove(0)

    # Add new handler with min log level defined in the settings
    logger.add(sys.stderr, level=numeric_level, colorize=True)
    logger.debug(f"Logging configured with level {log_level}")
