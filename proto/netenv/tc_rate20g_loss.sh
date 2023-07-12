#!/bin/bash

LOSS=$1

sudo tc qdisc del dev p1p1 root
sudo tc qdisc add dev p1p1 root handle 1:0 netem loss $LOSS # 0.2%
sudo tc qdisc add dev p1p1 parent 1:1 handle 10: tbf rate 20000mbit burst 10mb latency 50ms

