#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Created by jacob.mendt@pikobytes.de on 09.03.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
# -*- coding: utf-8 -*-
from sqlmodel import Session

from georeference.jobs.initialize_data import run_initialize_data


def test_load_initial_data_success(readonly_db_container):
    with Session(readonly_db_container[1]) as session:
        success = run_initialize_data(session)
        assert success


def test_load_initial_data_without_service_regeneration_success(readonly_db_container):
    with Session(readonly_db_container[1]) as session:
        success = run_initialize_data(session)
        assert success
