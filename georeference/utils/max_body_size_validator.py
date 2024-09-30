#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Created by nicolas.looschen@pikobytes.de on 28.08.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
from georeference.config.settings import get_settings

settings = get_settings()
MAX_FILE_SIZE = settings.MAX_FILE_SIZE
MAX_REQUEST_BODY_SIZE = settings.MAX_REQUEST_BODY_SIZE


class MaxBodySizeException(Exception):
    def __init__(self, body_len: str):
        self.body_len = body_len


class MaxBodySizeValidator:
    def __init__(self, max_size: int):
        self.body_len = 0
        self.max_size = max_size

    def __call__(self, chunk: bytes):
        self.body_len += len(chunk)
        if self.body_len > self.max_size:
            raise MaxBodySizeException(body_len=self.body_len)
