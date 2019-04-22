#!/bin/bash
# set -x

if [ $# -eq 0 ]
then
    printf "Trebuie specificata o zi pentru preluare date"
else
    start=$1
    end=$1
    if [ $# -gt 1 ]
    then
        end=$2
    fi

    for i in `seq $start $end`
    do
        printf -v workDate "2019-01-%02d" $i
        # echo $workDate
        ./preiaZi.bat workDate:$workDate
    done
fi