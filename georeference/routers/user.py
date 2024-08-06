#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by nicolas.looschen@pikobytes.de on 12.07.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package

from fastapi import APIRouter

from georeference.routers import user_history

router = APIRouter()

router.include_router(user_history.router, prefix="/history", tags=["history"])
