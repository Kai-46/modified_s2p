#!/usr/bin/env bash

cpu=$( { head -n1 /proc/stat;sleep 0.2;head -n1 /proc/stat; } | awk '/^cpu /{u=$2-u;s=$4-s;i=$5-i;w=$6-w}END{print int(0.5+100*(u+s+w)/(u+s+i+w))}' )
mem=$( free -m | awk 'NR==2 {print int($3*100/$2)}' )
echo "kai_cpu:"$( printf "%02d" ${cpu} )
echo "kai_mem:"$( printf "%02d" ${mem} )