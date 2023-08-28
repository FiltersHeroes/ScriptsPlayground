#!/bin/bash
if [ "$1" -lt 10 ]; then
    echo "0$1"
else
    echo "$1"
fi
