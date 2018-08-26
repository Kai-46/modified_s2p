#!/usr/bin/env bash

# example: ssh_login.sh ph#
# where # is the numbering of the host

# note: make this script executable first

user="kz298"
abbr=$1
id=${abbr:2:2}
ssh ${user}"@phoenix"${id}".cs.cornell.edu"
