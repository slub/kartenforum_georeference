#!/bin/bash
######################################################################
# @author      : jacmendt (jacob.mendt@pikobytes.de)
# @file        : download-testdata
# @created     : Dienstag August 13, 2024 09:08:33 CEST
#
# @description : Utility tool for download the test data from a remote source
#
#
# @example-usage: ./download-testdata.sh
######################################################################

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Define variables
REMOTE_FILE_NAME="vkf_test_data_20240923"
TARGET_DIR="$PROJECT_ROOT/data"
PASSWORD="8C2Kdpxc2lpUoYBX"

# Make sure that the data directory exits
mkdir -p $TARGET_DIR

echo "Start downloading test data from remote source. Please make sure you have sshpass installed."

# Use sshpass to download the file
sshpass -p "$PASSWORD" scp -o "PubkeyAuthentication=no" "u279620-sub2@u279620-sub2.your-storagebox.de:/$REMOTE_FILE_NAME.zip" "./"

# Check if the download was successful
if [ $? -eq 0 ]; then
    echo "File downloaded successfully."
else
    echo "File download failed."
fi

echo "Unpack $REMOTE_FILE_NAME and place it to the directory $TARGET_DIR ..."
unzip "$REMOTE_FILE_NAME"
mv $REMOTE_FILE_NAME/* "$TARGET_DIR"

echo "Clean up."
rm -f $REMOTE_FILE_NAME.zip
rm -rf $REMOTE_FILE_NAME

echo "Done."