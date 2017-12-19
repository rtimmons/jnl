#!/usr/bin/env bash

rex='dxx-(.*).txt'

_guid() {
    arr=(
        '0'  '1'  '2'  '3'  '4'  '5'  '6'  '7'  '8' 
        '9'  'A'  'B'  'C'  'D'  'E'  'F'  'G'  'H' 
        'J'  'K'  'M'  'N'  'P'  'Q'  'R'  'S'  'T' 
        'U'  'W'  'X'  'Y'  'Z' 
    )
    local out=""
    for I in `seq 21`; do
        rand=$[$RANDOM % ${#arr[@]}]
        out="${arr[rand]}${out}"
    done
    echo "$out"
}

pushd daily
    for I in *.txt; do
        if [[ "$I" =~ $rex ]]; then
            date="${BASH_REMATCH[1]}"
            guid="$(_guid)"
            echo -e "\n\n\n\nMy Reference: $guid  \n@ft @quick(daily/$date)  \n" \
                >> "$I"
            git mv "$I" ../worklogs/"$guid".txt
        fi
    done
popd