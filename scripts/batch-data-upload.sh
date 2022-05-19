#!/bin/bash
######################################################################
# @author      : nicolas (nicolas.looschen@pikobytes.de)
# @file        : batch-data-upload
# @created     : Mittwoch Mai 17.05, 2022 09:08:33 CEST
#
# @description : This utility allows for easy uploads to the new
#                import-api of the vkf.
#                It scans the given folder recursively for json and tif files,
#                and associates them by name:
#
#                map_a.json, map_a.tif
#
#
# @example-usage: ./batch-data-upload.sh -f -b username:password
#                 https://geo.test.kartenforum.slub-dresden.de/maps/?user_id=example_user
#                 path/to/upload/directory
######################################################################

while getopts "fb:" o; do
    case "${o}" in
    b)
        b=${OPTARG}
        ;;
    f)
        force=True
        ;;
    *)
        echo "Usage: $0 [-f] [-b username:password] import-api.de/maps/?user_id=test_user"
        exit 1
        ;;
    esac
done
shift "$((OPTIND - 1))"

upload_url="$1"
read_from_url="$2/*.json"

# initialize log file
log_file="uploaded.log"
touch $log_file

# set image extension
image_extension=".tif"

# allow recursive search for this session
shopt -s globstar

for metadata_file in $read_from_url; do
    echo
    echo "Found file $metadata_file"

    # skip if file was already downloaded
    if grep -q "$metadata_file" "$log_file"; then
        if [[ $force ]]; then
            echo "$metadata_file was already uploaded, but a reupload was forced"
        else
            echo "Skip file $metadata_file, because it was already uploaded."
            continue
        fi
    fi

    # build path to corresponding image file
    img_file=${metadata_file/.json/$image_extension}

    # check if the img_file exists
    if [ -f "$img_file" ]; then
        # in this case start upload process

        echo "Start upload for $metadata_file, $img_file"

        # Build request parameters
        args=(
            create
            -f "$img_file"
            -m "$metadata_file"
        )

        # Add basic auth data
        if [[ -n $b ]]; then
            args+=(-b "$b")
        fi

        # Add upload url
        args+=("$upload_url")

        # Make request
        res=$(./data-upload.sh "${args[@]}")

        # Check response
        body=${res::-3}
        status=$(printf "%s" "$res" | tail -c 3)

        if [ $status == '200' ]; then
            echo "$metadata_file - $img_file ($body)" >>$log_file
        else
            echo "Upload failed for $metadata_file."
            echo "$status - $body"
        fi
    else
        echo "Skip $metadata_file because no image file was found."
    fi
done
