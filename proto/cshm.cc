#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <sys/types.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <unistd.h>
#include <stdbool.h>
#include <errno.h>

typedef signed int INT32;
#define  NOT_READY  -1
#define  FILLED     0
#define  TAKEN      1

struct Memory {
    size_t  status;
    size_t  pkt_index;
    size_t  data_cnt;
    size_t  data[4];
};

int main(){
    key_t          ShmKEY=123456;
    int            ShmID;
    struct Memory  *ShmPTR;
    size_t arr[4] = {4,3,2,1};
    int err=0;
    int sec_cnt = 0;

    ShmID = shmget(ShmKEY, sizeof(struct Memory), IPC_CREAT | 0666); // 已存在则直接get
    if (ShmID < 0) {
        // for case of error does not return a valid shmid
        err = errno;
        printf("Error getting shared memory id %d %d\n",ShmID,err);
        if(err == EEXIST) printf("memory exist for this key\n");
        exit(1);
    }

    ShmPTR = (struct Memory *) shmat(ShmID, NULL, 0);

    ShmPTR->status = NOT_READY;
    ShmPTR->pkt_index = 1024;
    ShmPTR->data_cnt = 4;
    ShmPTR->data[0]  = arr[0];
    ShmPTR->data[1]  = arr[1];
    ShmPTR->data[2]  = arr[2];
    ShmPTR->data[3]  = arr[3];
    printf("Server has filled %d %d %d %d to shared memory...\n",
        ShmPTR->data[0], ShmPTR->data[1], 
        ShmPTR->data[2], ShmPTR->data[3]);
    ShmPTR->status = FILLED;

    while (ShmPTR->status != TAKEN)
    {
        printf("\r%d %d %d sleeping ...",sec_cnt,ShmPTR->status,ShmPTR->pkt_index);
        fflush(stdout);
        sec_cnt += 1;
        sleep(1);
    }

    shmdt((void *) ShmPTR);
    printf("Server has detached its shared memory...\n");
    shmctl(ShmID, IPC_RMID, NULL);
    printf("Server has removed its shared memory...\n");
    printf("Server exits...\n");
}
