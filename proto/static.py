import sys
import pyportus as portus
import datetime

class StaticFlow():
    INIT_RATE = 10 * 125000000 # Gbps travet to byteps, overflow when 30*125000000
    INIT_CWND = 10

    def __init__(self, datapath, datapath_info):
        self.datapath = datapath
        self.datapath_info = datapath_info

        self.init_cwnd = float(self.datapath_info.mss * StaticFlow.INIT_CWND)
        self.cwnd = self.init_cwnd

        self.rate = StaticFlow.INIT_RATE
        self.datapath.set_program("default", [("Rate", self.rate), ("Cwnd", int(self.cwnd)*1500)])
        
        self.avg_report_rate = 0
        self.report_count = 0

    def on_report(self, r):
        print("receive report: ", self.datapath_info.sock_id, self.datapath_info.src_ip, self.datapath_info.dst_ip)
        rate_mbps = r.rate/125000
        print("rate(Mbps): ", rate_mbps)
        self.report_count += 1

        self.avg_report_rate = (self.avg_report_rate*(self.report_count - 1) + rate_mbps) / self.report_count
        print("avg_rate = ", self.avg_report_rate)

        if((datetime.datetime.now()-self.timer).microseconds > 100*1000):
            print("receive report")
            self.timer = datetime.datetime.now()

class Static(portus.AlgBase):
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
                ))
                (when true
                    (:= Report.inflight Flow.packets_in_flight)
                    (:= Report.rtt Flow.rtt_sample_us)
                    (:= Report.acked (+ Report.acked Ack.bytes_acked))
                    (:= Report.sacked (+ Report.sacked Ack.packets_misordered))
                    (:= Report.loss Ack.lost_pkts_sample)
                    (:= Report.timeout Flow.was_timeout)
                    (:= Report.rate (max Report.rate (min Flow.rate_outgoing Flow.rate_incoming)))
                    (:= Report.curr_rate (/ Flow.bytes_in_flight Flow.rtt_sample_us))
                    (:= Report.count (+ Report.count 1))
                    (:= Report.accum_rate (+ Report.accum_rate Report.curr_rate))
                    (:= Report.avg_rate (/ Report.accum_rate Report.count))
                    (:= Report.rate (max Report.rate (min Flow.rate_outgoing Flow.rate_incoming)))
                    (fallthrough)
                )
                (when (> Micros 100000)
                    (report)
                    (:= Micros 0)
                )
            """
        }
    
    def new_flow(self, datapath, datapath_info):
        print("receive new flow: ", datapath_info.sock_id, datapath_info.src_ip, datapath_info.dst_ip)
        return StaticFlow(datapath, datapath_info)
