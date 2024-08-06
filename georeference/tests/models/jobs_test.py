#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by nicolas.looschen@pikobytes.de on 11.07.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
from datetime import datetime

from sqlalchemy import delete
from sqlmodel import Session

from georeference.models.job import Job
from georeference.models.enums import EnumJobType, EnumJobState
from georeference.models.transformation import Transformation, EnumValidationValue


class TestJob:
    map_id = 10007521

    def test_query_not_started_jobs_success(self, db_container):
        """The test checks if the function "queryUnprocessedJobs" returns the correct jobs and clears the race conditions.

        :param dbsession_only: Database session
        :type dbsession_only: sqlalchemy.orm.session.Session
        :return:
        """
        with Session(db_container[1]) as session:
            # Clear the database for this test
            session.execute(delete(Job))
            session.flush()
            initial_jobs = Job.query_not_started_jobs(
                [EnumJobType.TRANSFORMATION_PROCESS.value], session
            )
            initial_job_count = len(initial_jobs)
            assert initial_job_count == 0

            # Create the test data
            session.add(
                Transformation(
                    id=10000000,
                    submitted=datetime.now().isoformat(),
                    user_id="test",
                    params="",
                    target_crs=4326,
                    validation=EnumValidationValue.MISSING.value,
                    raw_map_id=self.map_id,
                    overwrites=0,
                    comment=None,
                )
            )
            session.add(
                Transformation(
                    id=10000001,
                    submitted=datetime.now().isoformat(),
                    user_id="test",
                    params="",
                    target_crs=4326,
                    validation=EnumValidationValue.MISSING.value,
                    raw_map_id=self.map_id,
                    overwrites=0,
                    comment=None,
                )
            )
            session.flush()
            session.add(
                Job(
                    id=10000000,
                    submitted=datetime.now().isoformat(),
                    user_id="test",
                    type=EnumJobType.TRANSFORMATION_PROCESS.value,
                    description='{ "transformation_id": 10000000 }',
                    state=EnumJobState.COMPLETED.value,
                )
            )
            session.add(
                Job(
                    id=10000001,
                    submitted=datetime.now().isoformat(),
                    user_id="test",
                    type=EnumJobType.TRANSFORMATION_PROCESS.value,
                    description='{ "transformation_id": 10000001 }',
                    state=EnumJobState.NOT_STARTED.value,
                )
            )
            session.add(
                Job(
                    id=10000002,
                    submitted=datetime.now().isoformat(),
                    user_id="test",
                    type=EnumJobType.TRANSFORMATION_PROCESS.value,
                    description='{ "transformation_id": 10000001 }',
                    state=EnumJobState.COMPLETED.value,
                )
            )
            session.add(
                Job(
                    id=10000003,
                    submitted=datetime.now().isoformat(),
                    user_id="test",
                    type=EnumJobType.TRANSFORMATION_SET_VALID.value,
                    description='{ "transformation_id": 10000001  }',
                    state=EnumJobState.NOT_STARTED.value,
                )
            )
            session.flush()

            # Build test
            subject = Job.query_not_started_jobs(
                [EnumJobType.TRANSFORMATION_PROCESS.value], session
            )
            assert len(subject) == 1
            assert subject[0].id == 10000001

            subject = Job.query_not_started_jobs(
                [
                    EnumJobType.TRANSFORMATION_SET_VALID.value,
                    EnumJobType.TRANSFORMATION_SET_INVALID.value,
                ],
                session,
            )
            assert len(subject) == 1
            assert subject[0].id == 10000003

    def test_has_not_started_jobs(self, db_container):
        """The test checks if the function "queryUnprocessedJobs" returns the correct jobs and clears the race conditions.

        :param db_container: Database session
        :type db_container: sqlalchemy.orm.session.Session
        :return:
        """

        with Session(db_container[1]) as session:
            # In the beginning there should be no started jobs for this map
            assert not Job.has_not_started_jobs_for_map_id(session, self.map_id)

            # add not started job for map
            session.add(
                Transformation(
                    id=10000001,
                    submitted=datetime.now().isoformat(),
                    user_id="test",
                    params="",
                    target_crs=4326,
                    validation=EnumValidationValue.MISSING.value,
                    raw_map_id=self.map_id,
                    overwrites=0,
                    comment=None,
                )
            )
            session.flush()
            session.add(
                Job(
                    id=10000001,
                    submitted=datetime.now().isoformat(),
                    user_id="test",
                    type=EnumJobType.TRANSFORMATION_PROCESS.value,
                    description='{ "transformation_id": 10000001 }',
                    state=EnumJobState.NOT_STARTED.value,
                )
            )
            session.flush()

            assert Job.has_not_started_jobs_for_map_id(session, self.map_id)
