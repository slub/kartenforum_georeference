#!/bin/bash

# Set the directory name and files to copy
directory_name="kartenforum_georeference"

# Create the directory
rm -r "$directory_name"
mkdir "$directory_name"

# Copy files
cp -r ../georeference "$directory_name"/georeference
rm -r "$directory_name"/georeference/__test_data
cp ../production.ini "$directory_name"/
cp ../setup.py "$directory_name"/

# Remove all __pycache__ directory
find "./$directory" -type d -name "__pycache__" -exec rm -rf {} \;

# Package directory
tar -czf georeference.tar.gz "$directory_name/"