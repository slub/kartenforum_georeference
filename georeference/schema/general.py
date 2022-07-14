#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by nicolas.looschen@pikobytes.de on 21.02.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package.

# RegEx for checking https links
reg_ex_link = 'https:\\/\\/(www\\.)?[-a-zA-Z0-9@:%._\\+~#=]{2,256}\\.[a-z]{2,4}\\b([-a-zA-Z0-9@:%_\\+.~#?&//=]*)'

# Schema definition for a 2D-ppoint
two_dimensional_point = {
    "type": "array",
    "items": {
        "type": "number"
    },
    # 2-dimensional coordinates representing a point
    "minItems": 2,
    "maxItems": 2
}
