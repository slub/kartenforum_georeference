#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import os
from datetime import datetime

from pydantic import NaiveDatetime
# Created by nicolas.looschen@pikobytes.de on 10.07.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package

from sqlalchemy import func, Column
from sqlalchemy.sql.type_api import UserDefinedType
from sqlmodel import SQLModel, Field, Session, desc, select

from georeference.config.paths import PATH_GEOREF_ROOT
from georeference.models import varchar_255, datetime_without_timezone


class ExtentType(UserDefinedType):
    # Always make sure that only EPSG:4326 is saved into the database.
    def get_col_spec(self):
        return "GEOMETRY"

    def bind_expression(self, bindvalue):
        return func.ST_Transform(
            func.ST_GeomFromGeoJSON(bindvalue, type_=self), 4326, type_=self
        )

    def column_expression(self, col):
        return func.ST_AsGeoJSON(func.ST_Transform(col, 4326, type_=self), type_=self)


class GeorefMap(SQLModel, table=True):
    __tablename__ = "georef_maps"

    raw_map_id: int = Field(default=None, primary_key=True, foreign_key="raw_maps.id")
    transformation_id: int = Field(foreign_key="transformations.id")
    rel_path: str = varchar_255
    extent: str = Field(sa_column=Column(ExtentType))
    last_processed: NaiveDatetime = datetime_without_timezone

    @classmethod
    def all(cls, dbsession: Session):
        """Equivalent to an 'SELECT * FROM georef_maps;'

        :param dbsession: Session object
        :type dbsession: sqlalchemy.orm.session.Session
        :result: All georeference maps.
        :rtype: georeference.models.georef_maps.GeorefMap[]
        """
        statement = select(GeorefMap).order_by(desc(GeorefMap.raw_map_id))

        return dbsession.exec(statement).all()

    def get_abs_path(self):
        """Returns the absolute path to the georeference image

        :result: Absolute path to georeference image
        :rtype: str
        """
        return os.path.abspath(os.path.join(PATH_GEOREF_ROOT, self.rel_path))

    @classmethod
    def by_raw_map_id(cls, map_id, dbsession: Session):
        """Returns the georef map for a given map id.

        :param map_id: Original map id
        :type map_id: int
        :param dbsession: Database session
        :type dbsession: sqlalchemy.orm.session.Session
        :result: None or reference on the georeference map associated to the original map
        :rtype: georeference.models.georef_maps.GeorefMap
        """
        statement = select(GeorefMap).where(GeorefMap.raw_map_id == map_id)

        return dbsession.exec(statement).first()

    @classmethod
    def by_transformation_id(cls, transformation_id, dbsession: Session):
        """Returns the georef map for a given transformation id.

        :param transformation_id: Transformation id
        :type transformation_id: int
        :param dbsession: Database session
        :type dbsession: sqlalchemy.orm.session.Session
        :result: None or reference on the georeference map associated to the original map
        :rtype: georeference.models.georef_maps.GeorefMap
        """
        statement = select(GeorefMap).where(
            GeorefMap.transformation_id == transformation_id
        )

        return dbsession.exec(statement).first()

    @classmethod
    def get_extent_for_raw_map_id(cls, map_id, dbsession: Session):
        """Returns the extent for a given map id

        :param map_id: Original map id
        :type map_id: int
        :param dbsession: Database session
        :type dbsession: sqlalchemy.orm.session.Session
        :result: GeoJSON  in EPSG:4326
        :rtype: GeoJSON
        """
        query = f"SELECT st_asgeojson(st_envelope(st_transform(extent, 4326))) FROM georef_maps WHERE raw_map_id = {map_id}"
        response = dbsession.execute(query).fetchone()
        if response is not None:
            return json.loads(response[0])
        return None

    @classmethod
    def from_raw_map_and_transformation(cls, raw_map_obj, transformation_obj):
        """Creates a GeorefMap object from a given RawMap and Transformation.

        :param raw_map_obj: RawMap
        :type raw_map_obj: georeference.models.raw_maps.RawMap
        :param transformation_obj: Transformation
        :type transformation_obj: georeference.models.transformations.Transformation
        :result: GeorefMap
        :rtype: georeference.models.georef_maps.GeorefMap
        """
        return GeorefMap(
            raw_map_id=raw_map_obj.id,
            rel_path="./%s/%s.tif"
            % (raw_map_obj.map_type.lower(), raw_map_obj.file_name),
            transformation_id=transformation_obj.id,
            last_processed=datetime.now().isoformat(),
        )
