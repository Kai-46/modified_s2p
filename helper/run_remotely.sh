#!/usr/bin/env bash

# @kai
# this is a script to run something remotely on the cluster

user="kz298"
#abbr="ph29"
#abbr=$1
#id=${abbr:2:2}

declare -a usable
for id in {1..29}; do
    usable[$(( id - 1 ))]=0
done
echo ${usable[@]}

for id in {1..29}
do
    echo "id:"${id}
    #cmd="ssh -oStrictHostKeyChecking=no -T ${user}"@phoenix"${id}".cs.cornell.edu" << 'EOSSH'
    #    cpu=$( { head -n1 /proc/stat;sleep 0.2;head -n1 /proc/stat; } | awk '/^cpu /{u=$2-u;s=$4-s;i=$5-i;w=$6-w}END{print int(0.5+100*(u+s+w)/(u+s+i+w))}' )
    #    mem=$( free -m | awk 'NR==2 {print int($3*100/$2)}' )
    #    echo "kai_cpu:"$cpu
    #    echo "kai_mem:"$mem
    #EOSSH"

    str=$( ssh -o ConnectTimeout=10 -oStrictHostKeyChecking=no -T ${user}"@phoenix"$( printf "%02d" ${id} )".cs.cornell.edu" < ./cpu_mem_query.sh )
    cpu_usage=$( echo ${str} | grep -o 'kai_cpu:..' )
    cpu_usage=${cpu_usage:8:2}
    if [[ ${cpu_usage:0:1} -eq "0" ]]; then
        cpu_usage=${cpu_usage:1:1}
    fi
    echo "cpu:"${cpu_usage}
    mem_usage=$( echo ${str} | grep -o 'kai_mem:..' )
    mem_usage=${mem_usage:8:2}
    if [[ ${mem_usage:0:1} -eq "0" ]]; then
        mem_usage=${mem_usage:1:1}
    fi
    echo "mem:"${mem_usage}

    if [[ ${cpu_usage} -lt 50 ]] && [[ ${mem_usage} -lt 50 ]]; then
        usable[$(( id - 1 ))]=1
    fi
done

echo ${usable[@]}
# echo ${str}

