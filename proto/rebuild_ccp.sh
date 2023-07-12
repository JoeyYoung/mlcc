#!/bin/bash

# relaunch ccp kernel, or the datapath program will not change
cd /home/xyzhao/ccp-kernel
sudo ./ccp_kernel_unload
sudo ./ccp_kernel_load ipc=0
cd /home/xyzhao/ccpdemo/pyversion
