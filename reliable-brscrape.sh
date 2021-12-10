#!/bin/bash

#while :; do
#    python3 brscrape.py "$1"
#     # Retry while return code is 2
#    if [ $? -ne 2 ]; then
#        break
#    fi
#done


while 
    python3 brscrape.py "$1"
     # Retry while return code is 2
    [ $? -eq 2 ]
do
    continue
done

