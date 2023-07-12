"""
    Emulated switch.
"""
import time
import grpc
import argparse
import switch_pb2
import switch_pb2_grpc
from concurrent import futures
from utils_p1p1 import *
import math

# increase cwnd and line rate, if NIC bandwidth increses
parser = argparse.ArgumentParser(description='Run Switch Process')
parser.add_argument('--time_slot', type=int, default=80, metavar='T',
                    help='time interval of a slot (ms)')
parser.add_argument('--num_slot', type=int, default=10, metavar='K',
                    help='K, the number of furture time slots to schedule')
parser.add_argument('--increase_factor', type=float, default=1.6, metavar='I',
                    help='volume increase, let it transmit more instead of 0 to stop')
parser.add_argument('--decay_factor', type=float, default=1.0, metavar='D',
                    help='applied rate = compute rate * decay, avoid additonal report problem')
args = parser.parse_args()

TIME_SLOT = args.time_slot
K = args.num_slot
VOLUME_INCREASE_FACTOR = args.increase_factor
DECAY_FACTOR = args.decay_factor

# store schedule info of each srcip-dstip trans
class Schedule():
    def __init__(self, rates, T):
        self.rates = rates # K-dim {slot: rate}, bytes/s
        self.T = T # time when allocated        


class LoadTable():
    def __init__(self) -> None:
        # update the schedule of each transmission
        self.trans_schedule = collections.defaultdict(dict)
        # used for delta difference among dependent flow, reset when init, add when new rate
        self.trans_accumulate = collections.defaultdict(dict)

        for srcip in flow_tensor_table.keys():
            for dstip in flow_tensor_table[srcip].keys():
                self.trans_schedule[srcip][dstip] = Schedule({i: 0 for i in range(K)}, 0) # init
                self.trans_accumulate[srcip][dstip] = 0
 
    # return ( {t: Phi_t} t\in K )
    def generate_costs(self, s, d):
        links = link_id_tabel[s][d]
        base_time = int(float(str(time.time())[6:])*1000) # ms level
        # future K slots prices
        cost_bucket = {i: 0 for i in range(K)}
        # fit other trans traversing same links into the schedule bucket
        for srcip in self.trans_schedule.keys():
            for dstip in self.trans_schedule[srcip].keys():
                if srcip == s and dstip == d: continue
                if srcip != s and dstip != d: continue
                if srcip != s: continue

                schedule = self.trans_schedule[srcip][dstip]
                if base_time > (K * TIME_SLOT) + schedule.T:
                    continue # expire
                for link in link_id_tabel[srcip][dstip]:
                    if link in links:
                        # fit schedule into bucket
                        idx = int((base_time - schedule.T)/TIME_SLOT) # possible base-T <0, but small negative, still 0
                        i = idx
                        while(i < K):
                            cost_bucket[i - idx] = schedule.rates[i] 
                            i += 1
        return cost_bucket


class Proto():
    def __init__(self) -> None:
        self.work_dep_notify = False

    # based on current K buckets in switch, allocated rate volume into the schedule
    def greedy_allocate(self, buckets, bound, volume, schedule, offset):
        optimal_cost = math.inf
        optimal_schedule = None
        
        for possible_t in range(K):
            cost = 0
            for i in range(offset, K):
                schedule.rates[i] = 0
            for i in range(offset):
                buckets.pop(K-1-i)

            buckets_sort = sorted(buckets.items(), key = lambda buckets:(buckets[1], buckets[0]))
            remain = volume
            while(remain > 0 and len(buckets_sort) > (K - possible_t)):
                allocated = min(bound, remain)
                schedule.rates[buckets_sort[0][0]+offset] = allocated
                remain -= allocated
                cost += buckets_sort[0][0]
                buckets_sort.pop(0)
            if cost < optimal_cost:
                optimal_cost = cost
                optimal_schedule = schedule               

        if offset == 0:
            optimal_schedule.T = int(float(str(time.time())[6:])*1000)

    def init_scheduling(self, costs, e, rate_volume, schedule):
        offset = 0
        self.greedy_allocate(costs, e, rate_volume, schedule, offset)
        return schedule.rates[0]

    # reschedule logic, greedy + dependent, update trans_schedule{}
    def re_scheduling(self, costs, e, delta, untransmit, schedule):
        current_time = int(float(str(time.time())[6:])*1000)
        offset = int((current_time - schedule.T)/TIME_SLOT)
        if(offset >= K - 1):
            return e

        # dependency is not satisfied
        if delta > 0:
            # sending rate can’t be increased due to bottleneck 
            if delta > e:
                # set this slot rate e, (untransmit - e) rescheduled into future remaining slots
                self.greedy_allocate(costs, e, untransmit-e, schedule, offset + 1)
                self.work_dep_notify = True
                return e
            else:
                # set this slot rate delta, (untransmit - delta) reschedule into future remaining slots
                self.greedy_allocate(costs, e, untransmit-delta, schedule, offset + 1)
                return delta
        # dependency is satisfied
        else:
            self.greedy_allocate(costs, e, untransmit, schedule, offset)
            return schedule.rates[offset]
            # untransmit reschedule into future K with limit e.


class Channel(switch_pb2_grpc.ChannelServicer):
    def __init__(self) -> None:
        super().__init__()
        self.load_table = LoadTable()
        self.protocol = Proto()
        self.reduce_notify = collections.defaultdict(dict)
        for srcip in self.reduce_notify.keys():
            for dstip in self.reduce_notify[srcip].keys():
                self.reduce_notify[srcip][dstip] = False

    def fetch(self, request, context):
        # {t: Phi_t}, future K slots cost
        costs = self.load_table.generate_costs(request.srcip, request.dstip)

        # total rate to be allocated, depend on model size
        rate_volume = flow_tensor_table[request.srcip][request.dstip][1] * 1e9 / TIME_SLOT * VOLUME_INCREASE_FACTOR # bytes/s
        stale_schedule = self.load_table.trans_schedule[request.srcip][request.dstip]

        if(request.status == 0):
            # init new flow, reset accumulated list
            self.load_table.trans_accumulate[request.srcip][request.dstip] = 0

            # generate init scheduled 
            new_rate = self.protocol.init_scheduling(costs, request.e, rate_volume, stale_schedule)

            # add the applied rate to accumlated list
            self.load_table.trans_accumulate[request.srcip][request.dstip] += (new_rate * DECAY_FACTOR)

        elif(request.status == 1):
            # calculate accumlated rate for this flow and subsequent flow
            rate_accum = self.load_table.trans_accumulate[request.srcip][request.dstip]
            subseq_tuple = flow_subseq_table[request.srcip][request.dstip]
            rate_accum_subseq = self.load_table.trans_accumulate[subseq_tuple[0]][subseq_tuple[1]]
            
            # obtain difference, f should larger than its subsequent
            delta = rate_accum_subseq - rate_accum

            # obtain rate remained to be allocated
            untransmit = rate_volume - rate_accum

            # generate re scheduling, considering dependent flow
            new_rate = self.protocol.re_scheduling(costs, request.e, delta, untransmit, stale_schedule)
            if self.protocol.work_dep_notify:
                flow_subseq_table[request.srcip][request.dstip] = True    
            if self.reduce_notify[request.srcip][request.dstip]:
                new_rate = max(delta - request.e)
                self.reduce_notify[request.srcip][request.dstip] = False

            # add applied rate to accumlated list
            self.load_table.trans_accumulate[request.srcip][request.dstip] += (new_rate * DECAY_FACTOR)

        return switch_pb2.reply(new_rate = int(new_rate))


class Switch():
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port

    def run(self):
        print("Running Emulated Switch Process ...")
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=15))
        switch_pb2_grpc.add_ChannelServicer_to_server(Channel(), server)
        server.add_insecure_port(self.ip + ":" + self.port)
        server.start()

        server.wait_for_termination() # run to die

if __name__ == '__main__':
    switch = Switch(SWITCH_IP, SWITCH_PORT)
    switch.run()
    