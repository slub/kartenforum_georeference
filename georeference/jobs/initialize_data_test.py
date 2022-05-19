#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Created by jacob.mendt@pikobytes.de on 09.03.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
# -*- coding: utf-8 -*-
import logging
from .initialize_data import run_initialize_data

# Initialize the logger
LOGGER = logging.getLogger(__name__)


def test_load_initial_data_success(dbsession_only):
    success = run_initialize_data(dbsession_only, LOGGER, overwrite_map_scale=True)
    assert success == True
