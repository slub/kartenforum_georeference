#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by nicolas.looschen@pikobytes.de on 12.07.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package

from pydantic import NaiveDatetime
from sqlalchemy import ARRAY, Integer, Column
from sqlmodel import SQLModel, Field, Session, select, col, desc

from georeference.models import datetime_without_timezone
from georeference.utils.parser import from_public_mosaic_map_id


class MosaicMap(SQLModel, table=True):
    __tablename__ = "mosaic_maps"

    id: int = Field(primary_key=True)
    name: str
    raw_map_ids: list[int] = Field(sa_column=Column(ARRAY(Integer)))
    title: str
    title_short: str
    description: str
    time_of_publication: NaiveDatetime = datetime_without_timezone
    link_thumb: str
    map_scale: int
    last_change: NaiveDatetime = datetime_without_timezone
    last_service_update: NaiveDatetime = datetime_without_timezone
    last_overview_update: NaiveDatetime = datetime_without_timezone

    @classmethod
    def by_public_id(cls, public_id: str, session: Session):
        id = from_public_mosaic_map_id(public_id)
        return session.exec(select(MosaicMap).where(col(MosaicMap.id) == id)).first()

    @classmethod
    def by_id(cls, id: int, session: Session):
        return session.exec(select(MosaicMap).where(col(MosaicMap.id) == id)).first()

    @classmethod
    def all(cls, session: Session):
        return session.exec(select(MosaicMap).order_by(desc(MosaicMap.id))).all()
