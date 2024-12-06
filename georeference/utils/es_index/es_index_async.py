#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by nicolas.looschen@pikobytes.de on 13.11.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package

from elasticsearch import AsyncElasticsearch

from georeference.config.settings import get_settings
from georeference.utils.es_index.es_index_sync import get_http_auth

settings = get_settings()

es_config = {
    "host": settings.ES_HOST,
    "port": settings.ES_PORT,
    "username": settings.ES_USERNAME,
    "password": settings.ES_PASSWORD,
    "ssl": settings.ES_SSL,
}

es = AsyncElasticsearch(
    [{"host": es_config["host"], "port": es_config["port"]}],
    http_auth=get_http_auth(es_config),
    use_ssl=es_config["ssl"],
    max_retries=10,
)


def get_async_es_client():
    return es
