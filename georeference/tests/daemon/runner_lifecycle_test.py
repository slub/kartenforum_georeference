#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Created by jacob.mendt@pikobytes.de on 09.12.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
from datetime import datetime

import pytest
from sqlmodel import Session, select, asc

from georeference.daemon.runner_lifecycle import main, on_start, loop
from georeference.models.enums import EnumJobType, EnumJobState
from georeference.models.job import Job, JobHistory


def handler(u, v, job):
    print(job.id)


test_handlers = {
    EnumJobType.MAPS_CREATE.value: handler,
    EnumJobType.MAPS_UPDATE.value: handler,
    EnumJobType.MAPS_DELETE.value: handler,
    EnumJobType.TRANSFORMATION_SET_VALID.value: handler,
    EnumJobType.TRANSFORMATION_SET_INVALID.value: handler,
    EnumJobType.TRANSFORMATION_PROCESS.value: handler,
}


@pytest.mark.skip(reason="Needs to long")
def test_on_start_success(db_container):
    with Session(db_container[1]) as session:
        on_start(dbsession=session)
        assert True


@pytest.mark.skip(reason="Needs to long")
def test_main_success(db_container):
    main()
    assert True


def test_loop_completes_jobs(db_container, es_index):
    with Session(db_container[1]) as session:
        job_id = 10000001
        delete_job = Job(
            id=job_id,
            description="",
            type=EnumJobType.MAPS_DELETE.value,
            state=EnumJobState.NOT_STARTED.value,
            submitted=datetime.now(),
            user_id="test",
        )
        session.add(delete_job)
        session.commit()
        loop(session, test_handlers, es_index)

        res = Job.query_not_started_jobs([e.value for e in EnumJobType], session)

        assert len(res) == 0

        history = session.exec(select(JobHistory)).all()

        assert len(history) == 14

        completed_jobs = session.exec(
            select(JobHistory).where(JobHistory.state == EnumJobState.COMPLETED.value)
        ).all()

        assert len(completed_jobs) == 14


def test_loop_handles_failed_job(db_container, es_index):
    with Session(db_container[1]) as session:
        job_id = 10000001

        failing_delete_job = Job(
            id=job_id,
            description="",
            type=EnumJobType.MAPS_DELETE.value,
            state=EnumJobState.NOT_STARTED.value,
            submitted=datetime.now(),
            user_id="test",
        )
        session.add(failing_delete_job)
        session.commit()

        loop(
            session,
            {
                **test_handlers,
                EnumJobType.MAPS_DELETE.value: lambda u, v, x: (_ for _ in ()).throw(
                    Exception()
                ),
            },
            es_index,
        )

        res = Job.query_not_started_jobs([e.value for e in EnumJobType], session)

        assert len(res) == 0

        history = session.exec(select(JobHistory)).all()

        assert len(history) == 14

        failed_jobs = session.exec(
            select(JobHistory).where(JobHistory.state == EnumJobState.FAILED.value)
        ).all()

        assert len(failed_jobs) == 1
        assert failed_jobs[0].state == EnumJobState.FAILED.value


def test_loop_recovers_from_failed_job(db_container, es_index):
    with Session(db_container[1]) as session:
        job_id = 10000001

        failing_delete_job = Job(
            id=job_id,
            description="",
            type=EnumJobType.MAPS_DELETE.value,
            state=EnumJobState.NOT_STARTED.value,
            submitted=datetime.now(),
            user_id="test",
        )

        session.add(failing_delete_job)

        job_id_2 = 10000002

        update_job = Job(
            id=job_id_2,
            description="",
            type=EnumJobType.MAPS_UPDATE.value,
            state=EnumJobState.NOT_STARTED.value,
            submitted=datetime.now(),
            user_id="test",
        )

        session.add(update_job)
        session.commit()

        loop(
            session,
            {
                **test_handlers,
                EnumJobType.MAPS_DELETE.value: lambda u, v, w, x: (_ for _ in ()).throw(
                    Exception()
                ),
            },
            es_index,
        )

        res = Job.query_not_started_jobs([e.value for e in EnumJobType], session)

        assert len(res) == 0

        history = session.exec(select(JobHistory).order_by(asc(JobHistory.id))).all()

        assert len(history) == 15

        failed_jobs = session.exec(
            select(JobHistory).where(JobHistory.state == EnumJobState.FAILED.value)
        ).all()
        assert len(failed_jobs) == 1

        successful_jobs = session.exec(
            select(JobHistory).where(JobHistory.state == EnumJobState.COMPLETED.value)
        ).all()
        assert len(successful_jobs) == 14
