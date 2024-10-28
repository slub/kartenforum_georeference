#!/bin/bash
######################################################################
# @author      : PouriaRezz (pouria.rezaei@pikobytes.de)
# @file        : downscale-testdata
# @created     : Donnerstag August 29, 2024 10:28:33 CEST
#
# @description : Utility tool for downscale the test data
#
#
# @example-usage: ./downscale-testdata.sh -input-dir __test_data -output-dir __test_data_compressed -max-size 1000
######################################################################


# Function to display usage information
usage() {
    echo "Usage: $0 -input-dir <input_dir> -output-dir <output_dir> -max-size <max_size>"
    echo "  -input-dir <input_dir>  Base input directory"
    echo "  -output-dir <output_dir> Base output directory"
    echo "  -max-size <max_size>    Maximum output size for TIFF images (e.g., 1000)"
    exit 1
}

# Parse command-line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -input-dir) BASE_INPUT_DIR="$2"; shift ;;
        -output-dir) BASE_OUTPUT_DIR="$2"; shift ;;
        -max-size) MAX_SIZE="$2"; shift ;;
        *) usage ;;
    esac
    shift
done

# Check if required arguments are provided
if [ -z "$BASE_INPUT_DIR" ] || [ -z "$BASE_OUTPUT_DIR" ] || [ -z "$MAX_SIZE" ]; then
    usage
fi

# Remove the output directory if it exists and recreate it
if [ -d "$BASE_OUTPUT_DIR" ]; then
    echo "Removing existing directory: $BASE_OUTPUT_DIR"
    rm -rf "$BASE_OUTPUT_DIR"
fi

mkdir -p "$BASE_OUTPUT_DIR"

# Recursive directory processing
find "$BASE_INPUT_DIR" -print | while read -r item; do
    # Skip if the item is the base input directory itself
    [ "$item" == "$BASE_INPUT_DIR" ] && continue

    # Determine relative path and corresponding output path
    relative_path="${item#"$BASE_INPUT_DIR"/}"
    output_path="$BASE_OUTPUT_DIR/$relative_path"

    if [ -f "$item" ]; then
        # Handle files
        filename=$(basename "$item")
        extension="${filename##*.}"
        basename="${filename%.*}"

        if [[ "$extension" == "tif" || "$extension" == "tiff" ]]; then
            # Get image dimensions
            width=$(gdalinfo "$item" | grep "Size is" | awk '{print $3}' | tr -d ',')
            height=$(gdalinfo "$item" | grep "Size is" | awk '{print $4}')

            # Calculate new dimensions and round up
            if [ "$width" -gt "$height" ]; then
                new_width=$MAX_SIZE
                new_height=$(echo "scale=0; ($height * $MAX_SIZE + $width - 1) / $width" | bc)
            else
                new_height=$MAX_SIZE
                new_width=$(echo "scale=0; ($width * $MAX_SIZE + $height - 1) / $height" | bc)
            fi

            # Compress TIFF files
            output_file="$output_path"
            output_file="${output_file%.tif}.tif"
            echo "Resizing and compressing file: $item"
            mkdir -p "$(dirname "$output_file")" # Ensure the directory exists before creating file
            gdal_translate -co COMPRESS=DEFLATE -co TILED=YES -outsize "$new_width" "$new_height" "$item" "$output_file"
        else
            # Copy other file formats
            echo "Copying file: $item"
            mkdir -p "$(dirname "$output_path")" # Ensure the directory exists before copying file
            cp "$item" "$output_path"
        fi
    elif [ -d "$item" ]; then
        # Create corresponding directory structure in the output directory
        mkdir -p "$output_path"
    fi
done

echo "Processing complete. Files are stored in $BASE_OUTPUT_DIR."
