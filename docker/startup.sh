#!/bin/sh
# startup.sh

# This starts up the daemon which checks for updates
/opt/kartenforum_georeference/python_env/bin/python /opt/kartenforum_georeference/georeference/daemon/runner.py

# This starts up the georeference service
/opt/kartenforum_georeference/python_env/bin/pserve production.ini