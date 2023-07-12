import sys
import pyportus as portus
import time
import argparse
import sysv_ipc
import struct
import os
from proxy import Proxy
from utils_p1p1 import *

# increase cwnd and line rate, if NIC bandwidth increses
parser = argparse.ArgumentParser(description='Run CCP Agent')
parser.add_argument('--time_slot', type=int, default=80, metavar='T',
                    help='time interval of a slot (ms)')
parser.add_argument('--report_bias', type=int, default=4000, metavar='B',
                    help='Mbps, report rate > apply rate 4Gbps')
parser.add_argument('--estimate_e', action="store_true",
                    help='whether use bottleneck bandwidth or just use line rate as e to allocate')
parser.add_argument('--replay_slot', type=int, default=5, metavar='R',
                    help='estimate T previous slots to obtain estimation of avaialbale bandwidth')
parser.add_argument('--init_cwnd', type=int, default=9000, metavar='W',
                    help='set a large window size (mss), so that cwnd will not the bottleneck.')
parser.add_argument('--line_rate', type=int, default=20, metavar='L',
                    help='set the line rate (Gbit/s) based on avaiable bandwidth (1 Mbit/s = 1e6/8 bytes/s)') # 125_000_000

'''
    For persistent cross flows, we dont check specific socket,
    i.e., there are init flows and tensor flows. 
    We apply the same control logic, since init flows will complete soon (no report then).
'''
class MLCCFlow():
    def __init__(self, datapath, datapath_info, args):
        self.args = args

        # receive init args from user
        self.dp = datapath
        self.dp_info = datapath_info
        self.cwnd = int(args.init_cwnd * self.dp_info.mss) # transfer to size
        self.line_rate_byteps = int(args.line_rate * 125000000) # transfer to bytes/s
        self.time_slot_us = args.time_slot * 1000 # transfer to micro sec
    
        # flow datapath info, sck, ips, ports, u32
        self.sock_id = self.dp_info.sock_id
        self.src_ip = self.dp_info.src_ip
        self.dst_ip = self.dp_info.dst_ip

        # calculate shmKey used to interact with nccl
        self.phy_src_ip = ip_transfer_table[self.src_ip]
        self.phy_dst_ip = ip_transfer_table[self.dst_ip]
        self.shm_key = int(self.phy_src_ip.split('.')[3]) * int(self.phy_dst_ip.split('.')[3])

        # record current iteration
        self.iter_cur = 1

        # proxy used to request the switch
        self.proxy = Proxy(SWITCH_IP, SWITCH_PORT)
        self.bottle_e = self.line_rate_byteps

        # record rates in every report received
        self.report_count = 0
        self.replay_rates = []

        # the transmission is uniquelly identified by srcip and dstip
        # we move scheduling tasks to the switch
        start = time.time() 
        new_rate = self.proxy.fetch_newrate(self.phy_src_ip, self.phy_dst_ip, 0, self.bottle_e).new_rate
        end = time.time()
        print("new init rate", new_rate)
        print("proxy commu time %s ms" % ((end - start)*1000))
        # profile total processing time here, 10ms

        self.dp.set_program("default", [("Rate", new_rate), ("Cwnd", self.cwnd), ("time_slot_us", self.time_slot_us)])
    
    def on_report(self, r):
        print(f"=> Flow [sid:{self.sock_id}, sip:{self.src_ip}, dip:{self.dst_ip}] receives a report")
        '''
            transfer ip, open shm, check interation whether change new flow 
                - if mem empty: continue
                - if change: init schedule
                - if not: reschedule
        '''
        # self.cpu_interfernce()

        # caputure error and return, dont generate error report
        try:
            memory = sysv_ipc.SharedMemory(self.shm_key, flags=0)
        except sysv_ipc.ExistentialError: 
            return
        memory_value = memory.read(byte_count=0,offset=0)
        data = struct.unpack('LLL', memory_value)
        # G: data[0] M: data[1] B: data[0]

        report_rate_mbps = r.rate/125000
        tuned_rate_mbps = (report_rate_mbps - self.args.report_bias) if (report_rate_mbps - self.args.report_bias) > 0 else report_rate_mbps
        
        # add replay at most T slots to obtain estimated rate
        self.report_count += 1
        self.replay_rates.append(tuned_rate_mbps)
        
        if self.args.estimate_e is True:
            self.bottle_e = min(self.obtain_e_from_T(), self.line_rate_byteps) # bytesps, restrict rate not exceed line
            print("\tBottleneck bandwidth estimation is: ", self.bottle_e)
        else:
            self.bottle_e = self.line_rate_byteps

        if(self.is_next_iteration(data)):
            new_rate = self.proxy.fetch_newrate(self.phy_src_ip, self.phy_dst_ip, 0, self.bottle_e).new_rate
            self.dp.update_field("Rate", new_rate) # udpate rate into datapath
            print("\t========= New iteration flow with init rate: ", new_rate)
        else:
            new_rate = self.proxy.fetch_newrate(self.phy_src_ip, self.phy_dst_ip, 1, self.bottle_e).new_rate
            self.dp.update_field("Rate", new_rate) # udpate rate into datapath
            print("\tReschedule rate", new_rate)
            return        

    # judge whether its a new iteration flow
    def is_next_iteration(self, data):
        upper_volume = flow_tensor_table[self.phy_src_ip][self.phy_dst_ip][1] * self.iter_cur # M
        upper_m = int(upper_volume % 1024) # M
        upper_g = int(upper_volume / 1024) # G
        if (data[0] > upper_g) or (data[0] == upper_g and data[1] > upper_m): 
            self.iter_cur += 1
            return True
            
        return False

    # return unit byteps, int type
    def obtain_e_from_T(self):
        if self.report_count <= self.args.replay_slot:
            return int(max(self.replay_rates)*125000)
        else:
            return int(max(self.replay_rates[self.report_count-self.args.replay_slot:])*125000)

    def cpu_interfernce(self, arr):
        def partition(arr, low, high):
            i = (low-1)
            pivot = arr[high]
        
            for j in range(low, high):
                if arr[j] <= pivot:
                    i = i+1
                    arr[i], arr[j] = arr[j], arr[i]
        
            arr[i+1], arr[high] = arr[high], arr[i+1]
            return (i+1)

        def quickSort(arr, low, high):
            if len(arr) == 1:
                return arr
            if low < high:
                pi = partition(arr, low, high)
                quickSort(arr, low, pi-1)
                quickSort(arr, pi+1, high)

        n = len(arr)
        quickSort(arr, 0, n-1)

class Agent(portus.AlgBase):
    def __init__(self, args):
        portus.AlgBase.__init__(self)
        self.args = args
        print("CCP Agent Starts ...")

        # remove previous shared memory
        info = os.popen("ipcs | grep xyzhao").read()
        if len(info) > 0:
            info_list = info.split('\n')
            shm_num = len(info_list) - 1
            for shm in range(shm_num):
                key = int(info_list[shm].split(' ')[1])
                os.system("ipcrm -m %d" % key)
        print("Clear all existing shared memory.")

    def datapath_programs(self):
        return {
                "default" : """\
                (def 
                    (Report
                        (volatile acked 0)
                        (volatile sacked 0)
                        (volatile loss 0)
                        (volatile timeout false)
                        (volatile rtt 0)
                        (volatile inflight 0)
                        (volatile rate 0)
                    )
                    (time_slot_us 0)
                )
                (when true
                    (:= Report.inflight Flow.packets_in_flight)
                    (:= Report.rtt Flow.rtt_sample_us)
                    (:= Report.acked (+ Report.acked Ack.bytes_acked))
                    (:= Report.sacked (+ Report.sacked Ack.packets_misordered))
                    (:= Report.loss Ack.lost_pkts_sample)
                    (:= Report.timeout Flow.was_timeout)
                    (:= Report.rate (max Report.rate (min Flow.rate_outgoing Flow.rate_incoming)))
                    (fallthrough)
                )
                (when (> Micros time_slot_us)
                    (report)
                    (:= Micros 0)
                )
            """
        }

    def new_flow(self, datapath, datapath_info):
        # judge whether is cross machine flow
        if (datapath_info.src_ip != datapath_info.dst_ip):
            print(f"receive new inter flow- sid:{datapath_info.sock_id}, sip:{datapath_info.src_ip}, dip:{datapath_info.dst_ip}")
            return MLCCFlow(datapath, datapath_info, self.args)
        # we only create MLCCFlow for cross machine flows
        # observe that intra rate is large, wont be affected by ccp option

if __name__ == '__main__':
    args = parser.parse_args()

    agent = Agent(args)
    portus.start("netlink", agent)
