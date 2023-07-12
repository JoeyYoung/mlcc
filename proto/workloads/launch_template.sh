NCCL_ALGO=RING NCCL_PROTO=SIMPLE NCCL_NSOCKS_PERTHREAD=1 NCCL_MAX_NCHANNELS=1 NCCL_IB_DISABLE=1 \
horovodrun -np 2 -H 10.28.1.18:1,10.28.1.19:1 \
--start-timeout 300 --network-interface p1p1 --verbose \
CUDA_VISIBLE_DEVICES=0 python /home/xyzhao/ccpdemo/pyversion/workload/pytorch_synthetic.py --model vgg19 --num-iters 100 