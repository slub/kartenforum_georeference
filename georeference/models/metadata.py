#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Created by nicolas.looschen@pikobytes.de on 06.08.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package

from typing import Optional

from pydantic import NaiveDatetime
from sqlalchemy import Column, String
from sqlmodel import Field, SQLModel, Session, desc, select

from georeference.models import varchar_255, datetime_without_timezone


class Metadata(SQLModel, table=True):
    # required
    description: str = varchar_255
    license: str = varchar_255
    title: str = varchar_255
    title_short: str = Field(sa_column=Column(String(length=70)))
    time_of_publication: NaiveDatetime = datetime_without_timezone
    raw_map_id: int = Field(default=None, primary_key=True, foreign_key="raw_maps.id")

    # optional
    link_thumb_small: Optional[str] = varchar_255
    link_thumb_mid: Optional[str] = varchar_255
    link_zoomify: Optional[str] = varchar_255
    measures: Optional[str] = varchar_255
    owner: Optional[str] = varchar_255
    permalink: Optional[str] = varchar_255
    ppn: Optional[str] = varchar_255
    technic: Optional[str] = varchar_255
    title_serie: Optional[str] = varchar_255
    type: Optional[str] = varchar_255

    @classmethod
    def by_map_id(cls, map_id: int, dbsession: Session):
        statement = select(Metadata).where(Metadata.raw_map_id == map_id)

        return dbsession.exec(statement).first()

    @classmethod
    def all(cls, dbsession: Session):
        statement = select(Metadata).order_by(desc(Metadata.raw_map_id))
        return dbsession.exec(statement).all()
