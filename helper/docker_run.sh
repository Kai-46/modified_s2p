#!/usr/bin/env bash

# this is a handy script for running docker with specified usage
# usage: ./docker_run.sh <path/to/map/file> <other options> <image name>

fs_map=$1
if [ -f ${fs_map} ]; then
    str=""
    while read line; do
        str="${str} -v ${line}"
    done < ${fs_map}
    cmd="docker container run ${str} ${@:2}"
    echo ${cmd}
    eval ${cmd}
else
    echo "${fs_map} does not exist"
    exit
fi