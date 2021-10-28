#!/bin/sh
# startup.sh

# Clean up old daemon and tmp files
rm -r /opt/kartenforum_georeference/data/tmp/*
rm -r /opt/kartenforum_georeference/data/tms/*
rm -r /opt/kartenforum_georeference/data/geo/*

# This starts up the daemon which checks for updates
/opt/kartenforum_georeference/python_env/bin/python /opt/kartenforum_georeference/georeference/daemon/runner.py

# This starts up the georeference service
/opt/kartenforum_georeference/python_env/bin/pserve production.ini