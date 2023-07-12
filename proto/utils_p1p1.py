"""
    This file stores some settings: ip, job info, deployment...

    Servers: (50Gbps)
    g3: 10.28.1.18      g4: 10.28.1.19      g5: 10.28.1.20      
    g6: 10.28.1.21      g7: 10.28.1.22      g8: 10.28.1.23

    Links ID:
    g3-S: 0     g4-S: 1     g5-S: 2     
    g6-S: 3     g7-S: 4     g8-S: 5
"""
import collections

# configurable parameters in arguments
# the maximum # of schedule slots
K = 10
TIME_SLOT = 100
DECAY_FACTOR = 1
VOLUME_INCREASE_FACTOR = 1.6
REPORT_RATE_BIAS = 4000 
REPLAY_T = 4

# use the 50Gbps ip of g3 as the switch ip first
SWITCH_IP = "10.28.1.18"
SWITCH_PORT = "50051"

# Transfer ccp ip (u32) into real ip (string)
# Need to be profiled in advance
ip_transfer_table = {
    302062602 : "10.28.1.18",
    318839818 : "10.28.1.19",
    335617034 : "10.28.1.20",
    352394250 : "10.28.1.21",
    369171466 : "10.28.1.22",
    385948682 : "10.28.1.23",
    3900714442 : "202.45.128.232",
    3917491658 : "202.45.128.233"
}

# Store Job related info
# dict src_ip: dst_ip: [job type, tensor size]
flow_tensor_table = collections.defaultdict(dict)
flow_tensor_table["202.45.128.232"]["202.45.128.233"] = ("resnet50", 98)
flow_tensor_table["202.45.128.233"]["202.45.128.232"] = ("resnet50", 98)

flow_tensor_table["10.28.1.18"]["10.28.1.19"] = ("vgg19", 549)
flow_tensor_table["10.28.1.19"]["10.28.1.18"] = ("vgg19", 549)

flow_tensor_table["10.28.1.19"]["10.28.1.20"] = ("vgg16", 528)
flow_tensor_table["10.28.1.20"]["10.28.1.19"] = ("vgg16", 528)

flow_tensor_table["10.28.1.20"]["10.28.1.21"] = ("vgg19", 549)
flow_tensor_table["10.28.1.21"]["10.28.1.20"] = ("vgg19", 549)

flow_tensor_table["10.28.1.21"]["10.28.1.22"] = ("vgg16", 528)
flow_tensor_table["10.28.1.22"]["10.28.1.21"] = ("vgg16", 528)

flow_tensor_table["10.28.1.22"]["10.28.1.23"] = ("vgg19", 549)
flow_tensor_table["10.28.1.23"]["10.28.1.22"] = ("vgg19", 549)

flow_tensor_table["10.28.1.23"]["10.28.1.18"] = ("vgg16", 528)
flow_tensor_table["10.28.1.18"]["10.28.1.23"] = ("vgg16", 528)

# Store routing path info
# dict src_ip: dst_ip: [link1, link2, ...]
link_id_tabel = collections.defaultdict(dict)
# this is just an example: g12-g13, running a job
link_id_tabel["202.45.128.232"]["202.45.128.233"] = [9, 10]
link_id_tabel["202.45.128.233"]["202.45.128.232"] = [10, 9]

link_id_tabel["10.28.1.18"]["10.28.1.19"] = [0, 1]
link_id_tabel["10.28.1.19"]["10.28.1.18"] = [1, 0]

link_id_tabel["10.28.1.19"]["10.28.1.20"] = [1, 2]
link_id_tabel["10.28.1.20"]["10.28.1.19"] = [2, 1]

link_id_tabel["10.28.1.20"]["10.28.1.21"] = [2, 3]
link_id_tabel["10.28.1.21"]["10.28.1.20"] = [3, 2]

link_id_tabel["10.28.1.21"]["10.28.1.22"] = [3, 4]
link_id_tabel["10.28.1.22"]["10.28.1.21"] = [4, 3]

link_id_tabel["10.28.1.22"]["10.28.1.23"] = [4, 5]
link_id_tabel["10.28.1.23"]["10.28.1.22"] = [5, 4]

link_id_tabel["10.28.1.23"]["10.28.1.18"] = [5, 0]
link_id_tabel["10.28.1.18"]["10.28.1.23"] = [0, 5]

# store dependency related
# dict src_ip: dst_ip: (sip, dip)
# for ps job, boardcast flow's subseq is none
# for all reduce, its a ring loop, straggler matters
flow_subseq_table = collections.defaultdict(dict)
flow_subseq_table["202.45.128.232"]["202.45.128.233"] = ("202.45.128.233", "202.45.128.232")
flow_subseq_table["202.45.128.233"]["202.45.128.232"] = ("202.45.128.232", "202.45.128.233")

flow_subseq_table["10.28.1.18"]["10.28.1.19"] = ("10.28.1.19", "10.28.1.18")
flow_subseq_table["10.28.1.19"]["10.28.1.18"] = ("10.28.1.18", "10.28.1.19")

flow_subseq_table["10.28.1.19"]["10.28.1.20"] = ("10.28.1.20", "10.28.1.19")
flow_subseq_table["10.28.1.20"]["10.28.1.19"] = ("10.28.1.19", "10.28.1.20")

flow_subseq_table["10.28.1.20"]["10.28.1.21"] = ("10.28.1.21", "10.28.1.20")
flow_subseq_table["10.28.1.21"]["10.28.1.20"] = ("10.28.1.20", "10.28.1.21")

flow_subseq_table["10.28.1.21"]["10.28.1.22"] = ("10.28.1.22", "10.28.1.21")
flow_subseq_table["10.28.1.22"]["10.28.1.21"] = ("10.28.1.21", "10.28.1.22")

flow_subseq_table["10.28.1.22"]["10.28.1.23"] = ("10.28.1.23", "10.28.1.22")
flow_subseq_table["10.28.1.23"]["10.28.1.22"] = ("10.28.1.22", "10.28.1.23")

flow_subseq_table["10.28.1.23"]["10.28.1.18"] = ("10.28.1.18", "10.28.1.23")
flow_subseq_table["10.28.1.18"]["10.28.1.23"] = ("10.28.1.23", "10.28.1.18")
