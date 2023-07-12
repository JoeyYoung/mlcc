#include <stdio.h>
#include <stdlib.h>
#include "socket.h"
#include <sys/shm.h>

// ip of current rank and next rank, obtained from bootstrap
extern char* myRankIP; 
extern char* nextRankIP;
extern char* preRankIP;

// the socket id used for tensor transmission, need to obtain for proxy->netsocket?
extern int* fdSend;

struct modelSize{
    size_t G;
    size_t M;
    size_t B;    
};
extern struct modelSize accumlSize;

// we use src_ip[laster region] * dst_ip[laster region] as the shmKey
extern int shmKey;
// if not init, delete existing shared memory
extern bool shmInit;
