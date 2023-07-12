# kill workers
ps -ef | awk '{print $2,$9}' | grep benchmark_byteps | awk '{print $1}' | xargs kill

