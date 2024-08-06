#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

# Created by jacob.mendt@pikobytes.de on 01.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package

from sqlmodel import SQLModel, Field, desc, Session, select

from georeference.config.paths import PATH_IMAGE_ROOT
from georeference.models import varchar_255


class RawMap(SQLModel, table=True):
    __tablename__ = "raw_maps"
    id: int = Field(default=None, primary_key=True)
    file_name: str = varchar_255
    enabled: bool
    map_type: str = varchar_255
    default_crs: int
    rel_path: str = varchar_255
    map_scale: int
    allow_download: bool

    def get_abs_path(self):
        """Returns the absolute path to the raw image

        :return: Absolute path to raw image
        :rtype: str
        """
        return os.path.abspath(os.path.join(PATH_IMAGE_ROOT, self.rel_path))

    @classmethod
    def all(cls, dbsession: Session):
        """Equivalent to an 'SELECT * FROM original_maps;'

        :param dbsession: Session object
        :type dbsession: sqlalchemy.orm.session.Session
        :return: georeference.models.original_maps.OriginalMap[]
        """
        statement = select(RawMap).order_by(desc(RawMap.id))
        return dbsession.exec(statement)

    @classmethod
    def all_enabled(cls, dbsession: Session):
        """Equivalent to an 'SELECT * FROM original_maps WHERE enabled=True;'

        :param dbsession: Session object
        :type dbsession: sqlalchemy.orm.session.Session
        :return: georeference.models.original_maps.OriginalMap[]
        """
        statement = select(RawMap).where(RawMap.enabled).order_by(desc(RawMap.id))

        return dbsession.exec(statement).all()

    @classmethod
    def by_id(cls, map_id, dbsession: Session):
        """

        :param map_id: Id of the original map
        :type map_id: int
        :param dbsession: Session object
        :type dbsession: sqlalchemy.orm.session.Session
        :return: georeference.models.original_maps.OriginalMap[]
        """
        statement = select(RawMap).where(RawMap.id == map_id)
        return dbsession.exec(statement).first()
