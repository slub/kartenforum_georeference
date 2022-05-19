#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 01.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package.
from sqlalchemy import func
from sqlalchemy.types import UserDefinedType


class Geometry(UserDefinedType):

    def get_col_spec(self):
        return "GEOMETRY"

    def bind_expression(self, bindvalue, srid=-1):
        return func.ST_GeomFromText(bindvalue, srid, type_=self)

    def column_expression(self, col):
        return func.ST_AsText(col, type_=self)
