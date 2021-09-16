#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 16.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import logging
from georeference.daemon.jobs import runInitializationJob
from georeference.daemon.jobs import runNewJobs

# Initialize the logger
LOGGER = logging.getLogger(__name__)

def test_runNewJobs_success(dbsession_only):
    jobCount = runNewJobs(dbsession_only, LOGGER)
    dbsession_only.rollback()
    assert jobCount == 1

def test_runInitializationJob_success(dbsession_only):
    success = runInitializationJob(dbsession_only, LOGGER)
    dbsession_only.rollback()
    assert success == True