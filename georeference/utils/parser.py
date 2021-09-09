#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 09.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package

def toInt(v):
    """ Tries to cast a given value to an int.

    :param v: Any value
    :type v: any
    :result: Value as int
    :rtype: int
    :raise: TypeError
    """
    if isinstance(int(v), int):
        return int(v)
    else:
        raise TypeError('The given values is not an integer.')