#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by nicolas.looschen@pikobytes.de on 12.07.2024
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package

from typing import Any, Dict, List

from pydantic import RootModel

from georeference.models.job import Job
from georeference.models.mixins import JobMixin


class JobResponse(JobMixin):
    description: Dict[str, Any]

    @classmethod
    def from_sqlmodel(cls, item: Job):
        description_dict = cls.parse_description(item.description)
        new_data = item.model_dump()
        del new_data["description"]
        return cls(**new_data, description=description_dict)

    @staticmethod
    def parse_description(description: str) -> Dict[str, Any]:
        # Here you can define how to convert the string description to a dict
        # For example, if the string is a JSON string, you can do:
        import json

        try:
            return json.loads(description)
        except json.JSONDecodeError:
            # Handle the case where the string is not a valid JSON
            return {"error": "Invalid description format"}


JobsResponse = RootModel[List[JobResponse]]
