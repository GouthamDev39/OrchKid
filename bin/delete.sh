#!/bin/bash

FILENAME=$1 
CURRENT_DIR=$(pwd)
#SANITIZED_DIR=$(echo "$CURRENT_DIR" | sed 's:/:_:g')


#Use tail -1 to restore the fil
echo "$CURRENT_DIR/" >> $FILENAME

mkdir -p /home/batman/recycle_bin


mv $FILENAME /home/batman/recycle_bin

cd /home/batman/recycle_bin




