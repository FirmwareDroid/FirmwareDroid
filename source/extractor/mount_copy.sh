#!/bin/bash

FILE_PATH=$1
MOUNT_PATH=$2
EXTRACTED_PATH=$3

echo "MOUNT_PATH: $MOUNT_PATH EXTRACTED_PATH: $EXTRACTED_PATH FILE_PATH: $FILE_PATH"

extract_files() {
    mount $FILE_PATH $MOUNT_PATH
    if [ $? -ne 0 ]; then
        echo "Error: Failed to mount $FILE_PATH to $MOUNT_PATH"
        exit 1
    fi

    # Best effort copy
    cp -r $MOUNT_PATH/* $EXTRACTED_PATH
    chown -RP www:www $EXTRACTED_PATH

    umount $MOUNT_PATH
    if [ $? -ne 0 ]; then
        echo "Error: Failed to unmount $MOUNT_PATH"
        exit 1
    fi
}

if file "$FILE_PATH" | grep -q "EROFS"; then
    echo "$FILE_PATH is an EROFS file."
    fsck.erofs --device="$FILE_PATH" --extract="$EXTRACTED_PATH" --no-preserve
    if [ $? -eq 0 ]; then
        echo "fsck.erofs completed successfully."
    else
        extract_files
    fi
else
    extract_files
fi

echo "Successfully extracted files from $FILE_PATH to $EXTRACTED_PATH"
exit 0