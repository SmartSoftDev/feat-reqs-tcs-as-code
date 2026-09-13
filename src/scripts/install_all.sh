#!/bin/bash
readonly SCRIPT_DIR=$(readlink -f $(dirname "${BASH_SOURCE[0]}"))
readonly REPO=$(readlink -f $(dirname "${BASH_SOURCE[0]}")/../../)
set -e
echo "REPO=$REPO"
sudo ln -s $REPO/src/bin/frtac.py /usr/bin/frtac