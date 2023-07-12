import sys
import pickle
import random
import pyportus as portus
import datetime
import argparse
from agent import Agent, Actor, Critic
from util import *

# increase cwnd and line rate, if NIC bandwidth increses
parser = argparse.ArgumentParser(description='Run DeepCC Agent')
parser.add_argument('--interval', type=int, default=50, metavar='T',
                    help='in online phase, the interval (ms) to change sending rate')
parser.add_argument('--init_cwnd', type=int, default=9000, metavar='W',
                    help='set a large window size (mss), so that cwnd will not the bottleneck.')
parser.add_argument('--line_rate', type=int, default=20, metavar='L',
                    help='set the line rate (Gbit/s) based on avaiable bandwidth (1 Mbit/s = 1e6/8 bytes/s)') # 125_000_000
parser.add_argument('--offline', action="store_true",
                    help='if offline, samples stored in pkl, and dont learn the model') # 125_000_000

def scale_up(a):
    high = parser.parse_args().line_rate * 125000000
    low = 0
    k = (high - low) / 2
    b = (high + low) / 2
    
    return a * k + b

def scale_down(a):
    high = parser.parse_args().line_rate * 125000000
    low = 0
    k = (high - low) / 2
    b = (high + low) / 2

    return (a - b) / k

class DeepFlow():
    def __init__(self, datapath, datapath_info, args):
        self.args = args
        print(args.offline)

        self.dp = datapath
        self.dp_info = datapath_info
        
        self.ddpg = Agent(**params)
        if args.offline is False:
            self.ddpg.load_trained_actor()
            print("Load Actor Model")

        # decide initial rate as line rate
        self.rate = int(args.line_rate * 125000000) # line rate 20Gbps
        self.cwnd = int(args.init_cwnd * self.dp_info.mss)

        self.dp.set_program("default", [("Rate", self.rate), ("Cwnd", self.cwnd), ("time_slot_us", args.interval * 1000)])
        
        self.s = None
        self.a = None

        self.exp_memory = []
        self.record = 20
        self.report_counter = 1

    def on_report(self, r):
        print("receive report: ", self.dp_info.sock_id, self.dp_info.src_ip, self.dp_info.dst_ip)
        self.report_counter += 1

        # fetch from report
        s_ = []
        s_.append(int(r.timeout))
        s_.append(r.loss)
        s_.append(r.rate)
        s_.append(r.lost_pkts_sample)
        s_.append(r.rtt)
        s_.append(r.sacked)
        s_.append(r.inflight)

        # compute reward
        r = r.rate / 125000000 / self.args.line_rate

        if self.args.offline is True:
            # set a random sending rate
            a_ = random.uniform(0, 1)
            new_rate = scale_up(a_)
            
            if self.s is not None:
                self.exp_memory.append( (self.s, self.a, r, s_) )
                if self.report_counter % self.record == 0:
                    with open(self.ddpg.exp_path, "wb") as fo:
                        self.buffer = pickle.dump(self.exp_memory, fo)
                        print("samples dump into pkl")

        else: # online
            # rescale to sending rate
            a_ = self.ddpg.act(s_)
            new_rate = scale_up(a_)

        self.dp.update_field("Rate", int(new_rate)) # udpate a_ into datapath

        self.s = s_
        self.a = a_ 
    
class DeepCC(portus.AlgBase):
    def __init__(self, args):
        portus.AlgBase.__init__(self)
        self.args = args
        print("DeepCC Agent Starts ...")

    def datapath_programs(self):
        return {
                "default" : """\
                (def (Report
                    (volatile acked 0)
                    (volatile sacked 0)
                    (volatile loss 0)
                    (volatile timeout false)
                    (volatile rtt 0)
                    (volatile inflight 0)
                    (volatile rate 0)
                    (volatile lost_pkts_sample 0)
                )
                (time_slot_us 0)
                )
                (when true
                    (:= Report.inflight Flow.bytes_in_flight)
                    (:= Report.rtt Flow.rtt_sample_us)
                    (:= Report.acked (+ Report.acked Ack.bytes_acked))
                    (:= Report.sacked (+ Report.sacked Ack.packets_misordered))
                    (:= Report.loss Ack.lost_pkts_sample)
                    (:= Report.timeout Flow.was_timeout)
                    (:= Report.rate (max Report.rate (min Flow.rate_outgoing Flow.rate_incoming)))
                    (:= Report.lost_pkts_sample Ack.lost_pkts_sample)
                    (fallthrough)
                )
                (when (> Micros time_slot_us)
                    (report)
                    (:= Micros 0)
                )
            """
        }


    def new_flow(self, datapath, datapath_info):
        print("receive new flow: ", datapath_info.sock_id, datapath_info.src_ip, datapath_info.dst_ip)
        return DeepFlow(datapath, datapath_info, self.args)


if __name__ == '__main__':
    args = parser.parse_args()

    agent = DeepCC(args)
    portus.start("netlink", agent)
