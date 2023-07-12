# MLCC
Codes for "Dynamic Flow Scheduling for DNN Training Workloads in Data Centers".

## Install
### Softwares
| Dependency | Version |
| :-----| :---- |
| OS | Ubuntu-18.04 | 
| OS Kernel | Linux 5.4.0-77-generic |
| GCC | gcc 7.5.0 |
| CUDA-Toolkit | cuda 10.2|
| OpenMPI | openmpi 4.1.1 |
| Horovod | v0.22.0 |
| BytePS | v0.2.4 |
| Python | python3.6 | 
| Rust | rustc 1.58.0-nightly |
| NCCL | Custormized based on v2.11.4 |

The software dependency is listed in the table above. All can be downloaded from official repositories. 

See `./proto/nccl_patch` for the customizations of nccl.

### Testbed
6 servers each with two GTX 1080Ti GPUs.

### Launch datapath program in kernel space
`cd ./proto/kernel && make && sudo ./ccp_kernel_load ipc=0`

use `sh ./proto/rebuild_ccp.sh` to rebuild if the datapath program changes.

## Start
On a dedicated server, use `switch.py` to start an emulated switch with rpc services.

On each server, run distributed agent with `ccp.py`.

Inject workloads with template scripts in `./proto/workloads`.

Tune the network environment with template scripts in `./proto/netenv`

See `./bbr` `./reno-cubic` `./deepcc` for part of baseline implementations.
