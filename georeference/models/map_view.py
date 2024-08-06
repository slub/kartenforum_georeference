#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by nicolas.looschen@pikobytes.de on 12.07.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package

from datetime import datetime
from typing import Optional

from pydantic import NaiveDatetime
from sqlmodel import SQLModel, Field, Session, select, col, desc

from georeference.models import datetime_without_timezone


class MapView(SQLModel, table=True):
    __tablename__ = "map_view"
    id: int = Field(primary_key=True, default=None)
    public_id: str
    map_view_json: str
    submitted: NaiveDatetime = datetime_without_timezone
    request_count: int
    last_request: Optional[NaiveDatetime] = datetime_without_timezone
    user_id: str

    def update_last_access(self, session: Session):
        self.request_count += 1
        self.last_request = datetime.now()
        session.add(self)
        session.commit()
        session.refresh(self)

    @classmethod
    def by_id(cls, id: int, session: Session):
        return session.exec(select(MapView).where(col(MapView.id) == id)).first()

    @classmethod
    def by_public_id(cls, public_id: str, session: Session):
        return session.exec(
            select(MapView).where(col(MapView.public_id) == public_id)
        ).first()

    @classmethod
    def all(cls, session: Session):
        return session.exec(select(MapView).order_by(desc(MapView.id))).all()
