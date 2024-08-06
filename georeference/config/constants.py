#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by nicolas.looschen@pikobytes.de on 11.07.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package

# Permalink resolver
GLOBAL_PERMALINK_RESOLVER = "http://digital.slub-dresden.de/"

GENERAL_ERROR_MESSAGE = "Something went wrong while trying to process your requests. Please try again or contact the administrators of the Virtual Map Forum 2.0."

# RegEx for checking https links
regex_link = "https:\\/\\/(www\\.)?[-a-zA-Z0-9@:%._\\+~#=]{2,256}\\.[a-z]{2,4}\\b([-a-zA-Z0-9@:%_\\+.~#?&//=]*)"

regex_alphanumeric_string = "^[a-z0-9]+(?:_[a-z0-9]+)*$"

# Keys which will be stored in the raw_map model
raw_map_keys = ["allow_download", "default_crs", "map_scale", "map_type"]
