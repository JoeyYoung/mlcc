/*************************************************************************
 * Copyright (c) 2015-2020, NVIDIA CORPORATION. All rights reserved.
 *
 * See LICENSE.txt for license information
 ************************************************************************/

#include "enqueue.h"
#include "mlcc.h"
#include "debug.h"
#include "core.h"

struct modelSize accumlSize;
bool shmInit;

bool isCrossMachine(ncclComm* comm){
  // we only use one channel for each connection
  int myRank = comm->channels[0].ring.index;
  int nextRank = comm->channels[0].ring.next;
  int preRank = comm->channels[0].ring.prev;
  INFO(NCCL_NET, "[all_reduce.cc] Process data: from rank %d (ip:%s) to peer rank %d (ip: %s).", myRank, myRankIP, nextRank, nextRankIP);
  if (strcmp(myRankIP, nextRankIP) != 0) return true;
  else return false;
}

// Note that M=1024*1024B
void accumulateTensorSize(ncclDataType_t datatype, size_t count){
  size_t dataSize = (size_t) ncclTypeSize(datatype) * count; // represented as bytes
  accumlSize.B += dataSize;
  // tune accumlSize to fit
  if(accumlSize.B >= (1024*1024)){
    accumlSize.M += (accumlSize.B/(1024*1024));
    accumlSize.B %= (1024*1024);
  }
  if(accumlSize.M >= 1024){
    accumlSize.G += (accumlSize.M/1024);
    accumlSize.M %= 1024;
  }
  INFO(NCCL_NET, "[all_reduce.cc] accumulate data sent: %zuG %zuM %zuB.", accumlSize.G, accumlSize.M, accumlSize.B);
}

NCCL_API(ncclResult_t, ncclAllReduce, const void* sendbuff, void* recvbuff, size_t count,
    ncclDataType_t datatype, ncclRedOp_t op, ncclComm* comm, cudaStream_t stream);
ncclResult_t ncclAllReduce(const void* sendbuff, void* recvbuff, size_t count,
    ncclDataType_t datatype, ncclRedOp_t op, ncclComm* comm, cudaStream_t stream) {
  NVTX3_FUNC_RANGE_IN(nccl_domain);
  struct ncclInfo info = { ncclFuncAllReduce, "AllReduce",
    sendbuff, recvbuff, count, datatype, op, 0, comm, stream, /* Args */
    ALLREDUCE_CHUNKSTEPS, ALLREDUCE_SLICESTEPS };

  // Judge whether this transmission cross machines
  if(isCrossMachine(comm)){
    // accumulate total data size transmitted
    accumulateTensorSize(datatype, count);
    // open shared memory, store based on shmKey (consider asyn? seems is efficiency enough)
    int shmID;
    if(!shmInit){
      shmID = shmget(shmKey, sizeof(struct modelSize), IPC_CREAT | 0666);
      shmctl(shmID, IPC_RMID, 0);
      shmInit = true;
    }
    shmID = shmget(shmKey, sizeof(struct modelSize), IPC_CREAT | 0666); // open shared memory
    if (shmID < 0) {
        // for case of error does not return a valid shmid
        int err = errno;
        printf("Error getting shared memory id %d %d\n", shmID, err);
        exit(EXIT_FAILURE);
    }
    INFO(NCCL_NET, "[all_reduce.cc] Open shared id: %d, shmkey: %d....", shmID, shmKey);
    struct modelSize* shmPtr;
    shmPtr = (struct modelSize *)shmat(shmID, NULL, 0); // attach memory
    shmPtr->G = accumlSize.G;
    shmPtr->M = accumlSize.M;
    shmPtr->B = accumlSize.B; // write accumulative size into memory
    
    // detech the ptr, wont delete the shared memory
    if (shmdt(shmPtr) == -1){
        printf("shmdt failed\n");
        exit(EXIT_FAILURE);
    }
  }
  // do nothing if its intra node peer

  // DL manages allreduce op as fifo, enqueue to kernel when call nccl op.
  // However, nccl use its own sized fifo to perform actual communication, which is hard to track
  // we argue: tensor level = iter level, just see transmission between two ranks in one iter as one ccp flow. 
  return ncclEnqueueCheck(&info);
}
