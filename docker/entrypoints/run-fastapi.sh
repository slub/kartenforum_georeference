#!/bin/bash

poetry install
poetry run python3 -m debugpy --listen 0.0.0.0:5678 -m uvicorn georeference.main:app --host 0.0.0.0 --port 8000 --reload
