"""
    This file stores some settings: ip, job info, deployment...

    Servers: (1Gbps)
    g3: 202.45.128.223      g4: 202.45.128.224      g5: 202.45.128.225      
    g6: 202.45.128.226      g7: 202.45.128.227      g8: 202.45.128.228
    g9: 202.45.128.229      g10:202.45.128.230      g11:202.45.128.231
    g12:202.45.128.232      g13:202.45.128.233

    Links ID:
    g3-S: 0     g4-S: 1     g5-S: 2     g6-S: 3
    g7-S: 4     g8-S: 5     g9-S: 6     g10-S:7
    g11-S:8     g12-S:9     g13-S:10
"""
import collections

# the maximum # of schedule slots
K = 15
# the time slot interval, ms
TIME_SLOT = 100
# use the 50Gbps ip of g3 as the switch ip first
SWITCH_IP = "10.28.1.18"
SWITCH_PORT = "50051"

# Transfer ccp ip (u32) into real ip (string)
# Need to be profiled in advance
ip_transfer_table = {
    3749719498 : "202.45.128.223",
    3766496714 : "202.45.128.224",
    3783273930 : "202.45.128.225",
    3800051146 : "202.45.128.226",
    3816828362 : "202.45.128.227",
    3833605578 : "202.45.128.228",
    3900714442 : "202.45.128.232",
    3917491658 : "202.45.128.233",
}


# Store Job related info
# dict src_ip: dst_ip: [job type, tensor size]
flow_tensor_table = collections.defaultdict(dict)
# this is just an example: g12-g13, running a all_reduce job resnet with 97M 516256B
flow_tensor_table["202.45.128.232"]["202.45.128.233"] = ("resnet50", 98)
flow_tensor_table["202.45.128.233"]["202.45.128.232"] = ("resnet50", 98)

flow_tensor_table["202.45.128.223"]["202.45.128.224"] = ("resnet50", 98)
flow_tensor_table["202.45.128.224"]["202.45.128.223"] = ("resnet50", 98)

flow_tensor_table["202.45.128.224"]["202.45.128.225"] = ("vgg16", 528)
flow_tensor_table["202.45.128.225"]["202.45.128.224"] = ("vgg16", 528)

flow_tensor_table["202.45.128.225"]["202.45.128.226"] = ("resnet50", 98)
flow_tensor_table["202.45.128.226"]["202.45.128.225"] = ("resnet50", 98)

flow_tensor_table["202.45.128.226"]["202.45.128.227"] = ("vgg16", 528)
flow_tensor_table["202.45.128.227"]["202.45.128.226"] = ("vgg16", 528)

flow_tensor_table["202.45.128.227"]["202.45.128.228"] = ("resnet50", 98)
flow_tensor_table["202.45.128.228"]["202.45.128.227"] = ("resnet50", 98)

flow_tensor_table["202.45.128.228"]["202.45.128.223"] = ("vgg16", 528)
flow_tensor_table["202.45.128.223"]["202.45.128.228"] = ("vgg16", 528)

# Store routing path info
# dict src_ip: dst_ip: [link1, link2, ...]
link_id_tabel = collections.defaultdict(dict)
link_id_tabel["202.45.128.232"]["202.45.128.233"] = [9, 10]
link_id_tabel["202.45.128.233"]["202.45.128.232"] = [10, 9]

link_id_tabel["202.45.128.223"]["202.45.128.224"] = [0, 1]
link_id_tabel["202.45.128.224"]["202.45.128.223"] = [1, 0]

link_id_tabel["202.45.128.224"]["202.45.128.225"] = [1, 2]
link_id_tabel["202.45.128.225"]["202.45.128.224"] = [2, 1]

link_id_tabel["202.45.128.225"]["202.45.128.226"] = [2, 3]
link_id_tabel["202.45.128.226"]["202.45.128.225"] = [3, 2]

link_id_tabel["202.45.128.226"]["202.45.128.227"] = [3, 4]
link_id_tabel["202.45.128.227"]["202.45.128.226"] = [4, 3]

link_id_tabel["202.45.128.227"]["202.45.128.228"] = [4, 5]
link_id_tabel["202.45.128.228"]["202.45.128.227"] = [5, 4]

link_id_tabel["202.45.128.228"]["202.45.128.223"] = [5, 0]
link_id_tabel["202.45.128.223"]["202.45.128.228"] = [0, 5]

# store dependency related
# dict src_ip: dst_ip: (sip, dip)
# for ps job, boardcast flow's subseq is none
# for all reduce, its a ring loop, straggler matters
flow_subseq_table = collections.defaultdict(dict)
flow_subseq_table["202.45.128.232"]["202.45.128.233"] = ("202.45.128.233", "202.45.128.232")
flow_subseq_table["202.45.128.233"]["202.45.128.232"] = ("202.45.128.232", "202.45.128.233")

flow_subseq_table["202.45.128.223"]["202.45.128.224"] = ("202.45.128.224", "202.45.128.223")
flow_subseq_table["202.45.128.224"]["202.45.128.223"] = ("202.45.128.223", "202.45.128.224")

flow_subseq_table["202.45.128.224"]["202.45.128.225"] = ("202.45.128.225", "202.45.128.224")
flow_subseq_table["202.45.128.225"]["202.45.128.224"] = ("202.45.128.224", "202.45.128.225")

flow_subseq_table["202.45.128.225"]["202.45.128.226"] = ("202.45.128.226", "202.45.128.225")
flow_subseq_table["202.45.128.226"]["202.45.128.225"] = ("202.45.128.225", "202.45.128.226")

flow_subseq_table["202.45.128.226"]["202.45.128.227"] = ("202.45.128.227", "202.45.128.226")
flow_subseq_table["202.45.128.227"]["202.45.128.226"] = ("202.45.128.226", "202.45.128.227")

flow_subseq_table["202.45.128.227"]["202.45.128.228"] = ("202.45.128.228", "202.45.128.227")
flow_subseq_table["202.45.128.228"]["202.45.128.227"] = ("202.45.128.227", "202.45.128.228")

flow_subseq_table["202.45.128.228"]["202.45.128.223"] = ("202.45.128.223", "202.45.128.228")
flow_subseq_table["202.45.128.223"]["202.45.128.228"] = ("202.45.128.228", "202.45.128.223")
