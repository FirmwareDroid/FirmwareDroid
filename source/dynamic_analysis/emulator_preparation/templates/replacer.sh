#!/bin/bash
################################################################################
# This script is used to replace the target file with the existing file.
################################################################################


# Check if the correct number of arguments are provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <target_file> <existing_file>"
    exit 1
fi

# Assign arguments to variables
target_file="$2"
existing_file="$1"

echo "Overwrite: $target_file $existing_file"
cp "$existing_file" "$target_file"
rm "$existing_file"
