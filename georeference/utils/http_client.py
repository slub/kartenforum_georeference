#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created by tom.schulze@pikobytes.de on 30.04.25.

This file is subject to the terms and conditions defined in
file "LICENSE.txt", which is part of this source code package.
"""

from httpx import AsyncClient
from georeference.config.settings import get_settings

settings = get_settings()

config = {
    "headers": {"accept": "application/json"},
    # In development mode we don't verify the SSL certificate, because the ddev site uses a self-signed certificate
    # and setting it up to be trusted is a hassle.
    "verify": False if settings.DEV_MODE else True,
}

http_client = AsyncClient(headers=config["headers"], verify=config["verify"])


def get_http_client():
    return http_client
