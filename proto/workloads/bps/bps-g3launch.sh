# the launcher has problem, launch manually

cd /home/xyzhao/byteps/launcher

python dist_launcher.py --worker-hostfile /home/xyzhao/ccpdemo/pyversion/workload/bps/worker_hosts --server-hostfile /home/xyzhao/ccpdemo/pyversion/workload/bps/server_hosts \
        --scheduler-ip 10.28.1.18 --scheduler-port 1234 \
        --env LD_LIBRARY_PATH:/home/xyzhao/org-nccl/nccl/build/lib/ \
        --env DMLC_NUM_WORKER:2 \
        'echo this is $DMLC_ROLE; python /home/xyzhao/byteps/launcher/launch.py /home/xyzhao/byteps/example/pytorch/benchmark_byteps.py --model resnet50 --num-iters 10'