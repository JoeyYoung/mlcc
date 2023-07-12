#!/bin/bash

sudo tc qdisc del dev p1p1 root
sudo tc qdisc add dev p1p1 root tbf rate 20000mbit burst 10mb latency 50ms