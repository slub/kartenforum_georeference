#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import List, Optional

# Created by nicolas.looschen@pikobytes.de on 24.07.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package

from pydantic import BaseModel


class User(BaseModel):
    username: str
    uid: int
    groups: List[str]


class UserResponse(BaseModel):
    valid: bool
    userData: Optional[User]
