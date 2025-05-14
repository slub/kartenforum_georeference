#!/bin/bash

# Copies files from project-root/scripts/geojson to project-root/data/geojson
# These files are served from geojson.ddev.site to provide a url for external vector maps

geojson_dir=geojson
geojson_path=$(dirname $0)/$geojson_dir

data_path=$(dirname $(dirname $(realpath $0)))/data

error_msg="Error. Example geojson files for external vector maps were not created"

if [ ! -d "$geojson_path" ]; then echo "$error_msg. Directory \"$geojson_path\" does not exist." &&  exit 1; fi
if [ -z "$(ls -A $geojson_path)" ]; then echo "$error_msg. No files found in \"$geojson_path\"." && exit 1; fi

if [ ! -d "$data_path/$geojson_dir" ]; then
    echo "Creating directory \"$data_path/$geojson_dir\"..."
    mkdir $data_path/$geojson_dir
fi

echo "Copying geojson files for external vector maps from \"$geojson_path\" to \"$data_path/$geojson_dir\"..."
cp -r $geojson_path/* $data_path/$geojson_dir

