#!/bin/bash

for i in "$@"; do
    echo "expired-domains/$i-expired.txt"
    echo "expired-domains/$i-unknown.txt"
    echo "expired-domains/$i-unknown_limit.txt"
    echo "expired-domains/$i-unknown_no_internet.txt"
done
