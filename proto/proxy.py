"""
    This is the proxy part used by ccp agent to communicate with switch
"""
import grpc
import switch_pb2
import switch_pb2_grpc

class Proxy():
    def __init__(self, switch_ip, switch_port):
        self.switch_ip = switch_ip
        self.switch_port = switch_port
    
    # we can move workload to switch for easy check
    def fetch_newrate(self, srcip, dstip, status, e):
        with grpc.insecure_channel(self.switch_ip + ":" + self.switch_port) as channel:
            stub = switch_pb2_grpc.ChannelStub(channel)
            response = stub.fetch(switch_pb2.request(srcip=srcip, dstip=dstip, status=status, e=e))    
        return response

    def send_schedule(self, schedule):
        with grpc.insecure_channel(self.switch_ip + ":" + self.switch_port) as channel:
            stub = switch_pb2_grpc.ChannelStub(channel)
            response = stub.sendSchedule(switch_pb2.schedRequest(schedule=schedule))    
        return response
        
    def fetch_obs(self, srcip, dstip):
        with grpc.insecure_channel(self.switch_ip + ":" + self.switch_port) as channel:
            stub = switch_pb2_grpc.ChannelStub(channel)
            response = stub.fetchObs(switch_pb2.obsRequest(srcip=srcip, dstip=dstip))
        return response
    