#!/bin/bash

# Check if a directory is provided as an argument
if [ -z "$1" ]; then
  echo "Usage: $0 <directory>"
  exit 1
fi

# Output file for 16-bit TIFF files
output_file="16bit_files.txt"
> "$output_file"  # Clear the output file if it exists

# Counters for total and 16-bit files
total_files=0
bit16_files=0

# Use a for loop instead of a while loop with a pipe
for file in $(find "$1" -type f -name "*.tif"); do
  total_files=$((total_files + 1))

  # Use gdalinfo to get the data type information and grep for "Type="
  data_type=$(gdalinfo "$file" | grep "Type=")

  # Check if the data type contains "UInt16"
  if echo "$data_type" | grep -q "UInt16"; then
    echo "$file" >> "$output_file"
    bit16_files=$((bit16_files + 1))
  fi
done

# Output results
echo "Total number of TIFF files: $total_files"
echo "Number of 16-bit TIFF files: $bit16_files"
echo "List of 16-bit TIFF files saved in: $output_file"
