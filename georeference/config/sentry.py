#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Created by nicolas.looschen@pikobytes.de on 06.08.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package

import sentry_sdk
from loguru import logger

from georeference.config.settings import get_settings


def setup_sentry():
    settings = get_settings()

    if settings.SENTRY_DSN and len(settings.SENTRY_DSN) > 10:
        logger.info("Initialize sentry...")
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            # Set traces_sample_rate to 1.0 to capture 100%
            # of transactions for performance monitoring.
            # We recommend adjusting this value in production.
            traces_sample_rate=1.0,
            environment=settings.SENTRY_ENVIRONMENT,
        )
    else:
        logger.info("Sentry is not enabled.")
