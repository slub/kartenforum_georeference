#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by nicolas.looschen@pikobytes.de on 11.07.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
from sqlmodel import Field, Session, select, asc, col, cast, SQLModel
from sqlalchemy import Integer

from datetime import datetime

from sqlalchemy.dialects.postgresql import JSON

from georeference.models.enums import EnumJobType, EnumJobState
from georeference.models.mixins import JobMixin
from georeference.models.transformation import Transformation
from georeference.schemas.job_payload import JobPayload


class Job(SQLModel, JobMixin, table=True):
    __tablename__ = "jobs"
    id: int = Field(default=None, sa_type=Integer, primary_key=True)

    @classmethod
    def all(cls, session: Session):
        return session.exec(select(Job)).all()

    @classmethod
    def has_not_started_jobs_for_map_id(cls, session: Session, map_id: int):
        """Checks if there are pending jobs for a given map id.

        :param session: Database session
        :type session: sqlalchemy.orm.session.Session
        :param map_id: Id of the original map
        :type map_id: int
        :result: True | False
        :rtype: bool
        """
        statement = (
            select(Job.id, Transformation.id)
            .join(
                Transformation,
                cast((cast(Job.description, JSON)["transformation_id"]).astext, Integer)
                == col(Transformation.id),
            )
            .where(Job.type == EnumJobType.TRANSFORMATION_PROCESS.value)
            .where(Transformation.raw_map_id == map_id)
        )

        result = session.exec(statement).first()

        return result is not None

    @classmethod
    def query_not_started_jobs(cls, job_types: list[EnumJobType], session: Session):
        """Query unprocessed jobs for a given list of job types.

        :param job_types: List of job types
        :type job_types: EnumJobName[]
        :param session: Database session
        :type session: sqlalchemy.orm.session.Session
        :param logger: Logger
        """
        statement = (
            select(Job)
            .where(Job.state == EnumJobState.NOT_STARTED.value)
            .where(col(Job.type).in_(job_types))
            .order_by(asc(Job.id))
        )

        return session.exec(statement).all()

    @classmethod
    def from_payload(cls, payload: JobPayload, user_id: str):
        return cls(
            submitted=datetime.now().isoformat(),
            type=payload.name.value,
            description=payload.description.model_dump_json(),
            state=EnumJobState.NOT_STARTED.value,
            user_id=user_id,
        )


class JobHistory(SQLModel, JobMixin, table=True):
    __tablename__ = "jobs_history"
    id: int = Field(default=None, sa_type=Integer, primary_key=True)
