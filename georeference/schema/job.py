#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by nicolas.looschen@pikobytes.de on 21.02.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package.

# Example:
# {
#     user_id: "test",
#     task : {
#       transformation_id: 12,
#     },
#     task_name: "transformation_process"
# }

job_schema = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "user_id": {
            "type": "string"
        },
        "name": {
            "enum": ["transformation_process", "transformation_set_valid", "transformation_set_invalid"]
        },
        "description": {
            "type": "object",
            "properties": {
                "transformation_id": {
                    "type": "integer"
                },
                "comment": {
                    "type": "string"
                }
            },
            "additionalProperties": False,
            "required": ["transformation_id"]
        }
    },
    "required": ["user_id", "name", "description"]
}
