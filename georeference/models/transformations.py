#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 01.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package.
import json
from georeference.models.meta import Base
from georeference.utils import EnumMeta
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, desc, func
from sqlalchemy.types import UserDefinedType

class ValidationValues(Enum, metaclass=EnumMeta):
    """ Enum for valid validations values. """
    MISSING = 'missing'
    VALID = 'valid'
    INVALID = 'invalid'

class ClipType(UserDefinedType):

    def get_col_spec(self):
        return "GEOMETRY"

    def bind_expression(self, bindvalue):
        return func.ST_GeomFromGeoJSON(bindvalue, type_=self)

    def column_expression(self, col):
        return func.ST_AsGeoJSON(col, type_=self)

class Transformation(Base):
    __tablename__ = 'transformations'
    __table_args__ = {'extend_existing':True}
    id = Column(Integer, primary_key=True)
    submitted = Column(DateTime(timezone=False))
    user_id = Column(String(255))
    validation = Column(String(20))
    params = Column(String)
    overwrites = Column(Integer)
    original_map_id = Column(Integer)
    comment = Column(String(255))
    clip = Column(ClipType)

    def getParamsAsDict(self):
        """ Returns the transformations parameters as a dict object.

        :result: Transformation parameters
        :rtype: dict
        """
        return json.loads(self.params)

    @classmethod
    def all(cls, session):
        """ Queries all transformations.

        :param dbsession: Database session
        :type dbsession: sqlalchemy.orm.session.Session
        :result: Transformations
        :rtype: georeference.models.transformations.Transformation[]
        """
        return session.query(Transformation).order_by(desc(Transformation.id))

    @classmethod
    def byId(cls, id, session):
        """ Returns transformation for id.

        :param id: Id of the transformation
        :type id: int
        :param dbsession: Database session
        :type dbsession: sqlalchemy.orm.session.Session
        :result: Transformations
        :rtype: georeference.models.transformations.Transformation
        """
        return session.query(Transformation).filter(Transformation.id == id).first()

    @classmethod
    def hasTransformation(cls, mapId, session):
        """ Queries all transformations.

        :param mapId: Id of the original map
        :type mapId: int
        :param dbsession: Database session
        :type dbsession: sqlalchemy.orm.session.Session
        :result: True or False signaling if there exist a valid transformation for the given original map id.
        :rtype: bool
        """
        transformation = session.query(Transformation).filter(Transformation.original_map_id == mapId)\
            .filter(Transformation.validation != ValidationValues.INVALID.value)\
            .order_by(desc(Transformation.submitted)).first()
        if transformation is None:
            return False
        return True