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

# Define variables
REMOTE_FILE_ONE="test_data_flat.tar.xz"
REMOTE_FILE_TWO="maps_epsg_4314.zip"
TARGET_DIR_ONE="./data/original"
TARGET_DIR_TWO="./data/tmp"
PASSWORD="8C2Kdpxc2lpUoYBX"

echo "Make sure target directories exists"
mkdir $TARGET_DIR_ONE
mkdir $TARGET_DIR_TWO

echo "Start downloading test data from remote source. Please make sure you have sshpass installed."

# Use sshpass to download the file
sshpass -p "$PASSWORD" scp -o "PubkeyAuthentication=no" "u279620-sub2@u279620-sub2.your-storagebox.de:/$REMOTE_FILE_ONE" "./"

# Check if the download was successful
if [ $? -eq 0 ]; then
    echo "File downloaded successfully."
else
    echo "File download failed."
fi

# Use sshpass to download the file
sshpass -p "$PASSWORD" scp -o "PubkeyAuthentication=no" "u279620-sub2@u279620-sub2.your-storagebox.de:/$REMOTE_FILE_TWO" "./"

# Check if the download was successful
if [ $? -eq 0 ]; then
    echo "File downloaded successfully."
else
    echo "File download failed."
fi

echo "Unpack $REMOTE_FILE_ON and place it to the directory $TARGET_DIR_ONE ..."
tar -xf "$REMOTE_FILE_ONE" -C "$TARGET_DIR_ONE"

echo "Unpack $REMOTE_FILE_TWO and place it to the directory $TARGET_DIR_TWO ..."
unzip "$REMOTE_FILE_TWO" -d "$TARGET_DIR_TWO"

echo "Clean up."
rm -f $REMOTE_FILE_ONE
rm -f $REMOTE_FILE_TWO

echo "Done."