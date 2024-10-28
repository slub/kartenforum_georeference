#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Created by nicolas.looschen@pikobytes.de on 12.07.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package

from typing import Optional

from enum import Enum
import json
from pydantic import NaiveDatetime
from sqlalchemy import func, Column, text
from sqlalchemy.sql.type_api import UserDefinedType
from sqlmodel import Field, SQLModel, select, desc, Session

from georeference.models import datetime_without_timezone, varchar_255
from georeference.utils.proj import transform_to_params_to_target_crs


class EnumValidationValue(str, Enum):
    MISSING = "missing"
    VALID = "valid"
    INVALID = "invalid"


class ClipType(UserDefinedType):
    # Always make sure that only EPSG:4326 is saved into the database.
    def get_col_spec(self):
        return "GEOMETRY"

    def bind_expression(self, bindvalue):
        return func.ST_Transform(
            func.ST_GeomFromGeoJSON(bindvalue, type_=self), 4326, type_=self
        )

    def column_expression(self, col):
        return func.ST_AsGeoJSON(func.ST_Transform(col, 4326, type_=self), type_=self)


class Transformation(SQLModel, table=True):
    __tablename__ = "transformations"

    id: Optional[int] = Field(default=None, primary_key=True)
    submitted: NaiveDatetime = datetime_without_timezone
    user_id: str = varchar_255
    validation: EnumValidationValue = varchar_255
    params: str
    target_crs: int
    overwrites: int
    raw_map_id: int = Field(foreign_key="raw_maps.id")
    comment: str = varchar_255
    clip: str = Field(sa_column=Column(ClipType))

    def get_params_as_dict(self):
        """Returns the transformations parameters as a dict object.

        :result: Transformation parameters
        :rtype: dict
        """
        return json.loads(self.params)

    def get_params_as_dict_in_epsg_4326(self):
        """Returns the transformations parameters as a dict object, but makes also sure that the coordinates are
            in epsg:4326.

        :result: Transformation parameters
        :rtype: dict
        """
        transformation_params = self.get_params_as_dict()
        target_crs = "epsg:4326"

        if transformation_params["target"].lower() == target_crs:
            return transformation_params
        else:
            return transform_to_params_to_target_crs(transformation_params, target_crs)

    def get_target_crs_as_string(self):
        """Returns the target crs in epsg string syntax.

        :result: EPSG syntax of the target crs
        :rtype: str
        """
        return f"EPSG:{self.target_crs}"

    @classmethod
    def all(cls, dbsession: Session):
        """Queries all transformations.

        :param dbsession: Database session
        :type dbsession: sqlalchemy.orm.session.Session
        :result: Transformations
        :rtype: georeference.models.transformations.Transformation[]
        """
        statement = select(Transformation).order_by(desc(Transformation.id))
        return dbsession.query(statement).all()

    @classmethod
    def by_id(cls, id, dbsession: Session):
        """Returns transformation for id.

        :param id: Id of the transformation
        :type id: int
        :param dbsession: Database session
        :type dbsession: sqlalchemy.orm.session.Session
        :result: Transformations
        :rtype: georeference.models.transformations.Transformation
        """
        statement = select(Transformation).where(Transformation.id == id)
        return dbsession.exec(statement).first()

    @classmethod
    def get_valid_clip_geometry(self, transformation_id, dbsession: Session):
        """Returns a valid clip geometry. It could be possible that the user generates artefacts at the edges of the
            clip polygons, which would lead to MultiPolygons by ST_MakeValid. We fix this behavior by use a special
            query function for accessing the clip polygon.

        :param transformation_id: Id of the transformation
        :type transformation_id: int
        :param dbsession: Database session
        :type dbsession: sqlalchemy.orm.session.Session
        :result: GeoJSON geometry.
        :rtype: dict
        """
        query = text(
            f"select st_asgeojson(st_geometryn(st_makevalid(clip), generate_series(1, st_numgeometries(st_makevalid(clip))))), "
            f"st_area(st_geometryn(st_makevalid(clip), generate_series(1, st_numgeometries(st_makevalid(clip))))) as area "
            f"from transformations t where id = {transformation_id} order by area desc"
        )
        response = dbsession.execute(query).fetchone()
        if response is not None:
            return json.loads(response[0])
        return None

    @classmethod
    def has_transformation(cls, map_id, session: Session):
        """Queries all transformations.

        :param map_id: Id of the original map
        :type map_id: int
        :param dbsession: Database session
        :type dbsession: sqlalchemy.orm.session.Session
        :result: True or False signaling if there exist a valid transformation for the given original map id.
        :rtype: bool
        """
        statement = (
            select(Transformation)
            .where(Transformation.raw_map_id == map_id)
            .where(Transformation.validation != EnumValidationValue.INVALID.value)
            .order_by(desc(Transformation.submitted))
        )

        transformation = session.exec(statement).first()

        if transformation is None:
            return False
        return True

    @classmethod
    def query_previous_valid_transformation(cls, transformation_obj, dbsession):
        """This function walks up the overwrites id tree for a transformation and looks if it find a
            valid transformation

        :param transformation_obj: Transformation
        :type transformation_obj: georeference.models.transformation.Transformation
        :param dbsession: Database session
        :type dbsession: sqlalchemy.orm.session.Session
        :param logger: Logger
        :type: logger: logging.Logger
        :result: Returns a valid georeference process if existing
        :rtype: georeference.models.transformations.Transformation|None
        """
        if transformation_obj.overwrites == 0:
            return None

        prev_transformation_object = Transformation.by_id(
            transformation_obj.overwrites, dbsession
        )

        if (
            prev_transformation_object.validation == EnumValidationValue.VALID.value
            or prev_transformation_object.validation
            == EnumValidationValue.MISSING.value
        ):
            return prev_transformation_object
        elif prev_transformation_object.overwrites > 0:
            return Transformation.query_previous_valid_transformation(
                Transformation.by_id(prev_transformation_object.overwrites, dbsession),
                dbsession,
            )
        else:
            return None
