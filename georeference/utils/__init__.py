#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 06.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import os
import enum

class EnumMeta(enum.EnumMeta):
    def __contains__(cls, item):
        return item in [v.value for v in cls.__members__.values()]

def createPathIfNotExists(path):
    """ Given a path, this functions make sure that the directory structure of
        the path is created if not exists.

    :param path: Path
    :type path: str
    """
    if not os.path.exists(path):
        os.makedirs(path)