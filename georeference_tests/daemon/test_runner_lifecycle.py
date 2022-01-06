#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 09.12.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import os
import pytest
import logging
import lockfile
from georeference.settings import PATH_TMP_ROOT
from georeference.daemon.runner_lifecyle import main, onStart

# Initialize the logger
LOGGER = logging.getLogger(__name__)

@pytest.mark.skip(reason="Needs to long")
def test_onStart_success(dbsession_only):
    onStart(
        logger=LOGGER,
        dbsession=dbsession_only
    )
    assert True == True

@pytest.mark.skip(reason="Needs to long")
def test_main_success(dbsession_only):
    main(
        logger=LOGGER,
        dbsession=dbsession_only
    )
    assert True == True