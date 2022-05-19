#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 09.12.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
from datetime import datetime

import pytest
import logging

from sqlalchemy import asc

from georeference.daemon.runner_lifecycle import main, on_start, loop
from georeference.models.jobs import EnumJobType, EnumJobState, Job, JobHistory

handler = lambda u, v, w, x: print(x.id)

test_handlers = {
    EnumJobType.MAPS_CREATE.value: handler,
    EnumJobType.MAPS_UPDATE.value: handler,
    EnumJobType.MAPS_DELETE.value: handler,
    EnumJobType.TRANSFORMATION_SET_VALID.value: handler,
    EnumJobType.TRANSFORMATION_SET_INVALID.value: handler,
    EnumJobType.TRANSFORMATION_PROCESS.value: handler
}

# Initialize the logger
LOGGER = logging.getLogger(__name__)


@pytest.mark.skip(reason="Needs to long")
def test_on_start_success(dbsession_only):
    on_start(
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


def test_loop_completes_jobs(dbsession_only):
    try:
        job_id = 10000001
        delete_job = Job(
            id=job_id,
            description='',
            type=EnumJobType.MAPS_DELETE.value,
            state=EnumJobState.NOT_STARTED.value,
            submitted=datetime.now().isoformat(),
            user_id='test'
        )
        dbsession_only.add(delete_job)
        dbsession_only.commit()
        loop(dbsession_only, LOGGER, test_handlers)

        res = Job.query_not_started_jobs([e.value for e in EnumJobType], dbsession_only)

        assert len(res) == 0

        history = dbsession_only.query(JobHistory).all()

        assert len(history) == 1
        assert history[0].state == EnumJobState.COMPLETED.value

    finally:
        dbsession_only.query(JobHistory).filter(JobHistory.id == job_id).delete()
        dbsession_only.delete(delete_job)
        dbsession_only.commit()


def test_loop_handles_failed_job(dbsession_only):
    try:
        job_id = 10000001

        failing_delete_job = Job(
            id=job_id,
            description='',
            type=EnumJobType.MAPS_DELETE.value,
            state=EnumJobState.NOT_STARTED.value,
            submitted=datetime.now().isoformat(),
            user_id='test'
        )
        dbsession_only.add(failing_delete_job)
        dbsession_only.commit()

        loop(dbsession_only, LOGGER,
             {**test_handlers, EnumJobType.MAPS_DELETE.value: lambda u, v, w, x: (_ for _ in ()).throw(Exception())})

        res = Job.query_not_started_jobs([e.value for e in EnumJobType], dbsession_only)

        assert len(res) == 0

        history = dbsession_only.query(JobHistory).all()

        assert len(history) == 1
        assert history[0].state == EnumJobState.FAILED.value

    finally:
        dbsession_only.query(JobHistory).filter(JobHistory.id == job_id).delete()
        dbsession_only.delete(failing_delete_job)
        dbsession_only.commit()


def test_loop_recovers_from_failed_job(dbsession_only):
    try:
        job_id = 10000001

        failing_delete_job = Job(
            id=job_id,
            description='',
            type=EnumJobType.MAPS_DELETE.value,
            state=EnumJobState.NOT_STARTED.value,
            submitted=datetime.now().isoformat(),
            user_id='test'
        )

        dbsession_only.add(failing_delete_job)

        job_id_2 = 10000002

        update_job = Job(
            id=job_id_2,
            description='',
            type=EnumJobType.MAPS_UPDATE.value,
            state=EnumJobState.NOT_STARTED.value,
            submitted=datetime.now().isoformat(),
            user_id='test'
        )

        dbsession_only.add(update_job)
        dbsession_only.commit()

        loop(dbsession_only, LOGGER,
             {**test_handlers, EnumJobType.MAPS_DELETE.value: lambda u, v, w, x: (_ for _ in ()).throw(Exception())})

        res = Job.query_not_started_jobs([e.value for e in EnumJobType], dbsession_only)

        assert len(res) == 0

        history = dbsession_only.query(JobHistory).order_by(asc(JobHistory.id)).all()

        assert len(history) == 2
        assert history[0].state == EnumJobState.FAILED.value
        assert history[1].state == EnumJobState.COMPLETED.value


    finally:
        dbsession_only.query(JobHistory).filter(JobHistory.id == job_id).delete()
        dbsession_only.query(JobHistory).filter(JobHistory.id == job_id_2).delete()
        dbsession_only.delete(failing_delete_job)
        dbsession_only.delete(update_job)
        dbsession_only.commit()
