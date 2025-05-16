import sys
import os

# 将 src 目录添加到 sys.path 中
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))


from networkx.readwrite import json_graph
import networkx as nx
import json 
#import matplotlib.pyplot as plt
#from election_model import ElectionModel
from models import RetireModel
import argparse
# from baichuan import BaichuanLLM
from ollama_lib import OllamaLLM

import os
from casevo import TotLog

from plot_attitudes import  save_attitude_history
from agents import FullAgent, LiteAgent


API_KEY = 'aac7e5f2-63f9-410c-98b5-51a60ac1a8c3'

# API_KEY = 'sk-0ef7b289bf68695b75faa0d5b489460f'

parser = argparse.ArgumentParser(description='run the Mesa model.')

# 添加配置文件作为参数
#网络文件注释掉了，采用随机生成的小世界网络*******************************************
# parser.add_argument('graphfile', metavar='graph_file', type=str,
#                    help='The graph file for the sim')

parser.add_argument('personfile', metavar='person_file', type=str,
                   help='The person file for the sim')

parser.add_argument('round', metavar='round_num', type=int,
                   help='The round number of the sim')
parser.add_argument('exp', metavar='exp_name', type=str,
                   help='The exp name of the sim')

parser.add_argument('-e',action='store_true', help='event log flag')

parser.add_argument('-a',metavar='offset', type=int, help='addon previous sim')

#三个参数控制小世界网络生成********************************************************
parser.add_argument('-n', type=int, help='Number of nodes for small world network', default=100)
parser.add_argument('-k', type=int, help='Each node is connected to k nearest neighbors in ring topology', default=10)
parser.add_argument('-p', type=float, help='Rewiring probability of the edges', default=0.1)


args = parser.parse_args()

# tar_graph = args.graphfile
tar_person = args.personfile
exp_name = args.exp

# with open(tar_graph, 'r') as f:
#     config_graph = json.load(f) 

with open(tar_person, 'r') as f:
    config_person = json.load(f)     
    


tar_log = './log/%s/' % exp_name
tar_memory = './memory/%s/' % exp_name
tar_cache = './cache/%s.db' % exp_name


#获取配置
# G = json_graph.node_link_graph(config_graph)
# 生成小世界网络********************************************************************************
G = nx.watts_strogatz_graph(n=args.n, k=args.k, p=args.p)  # 使用Watts-Strogatz模型生成网络
# 打印网络信息
print(f"Generated small world network with {args.n} nodes, each connected to {args.k} neighbors, rewiring probability {args.p}")
print(f"Number of edges: {G.number_of_edges()}")

# person_list = config_file['person']
# llm = BaichuanLLM(API_KEY, 5, tar_cache)
# llm = BaichuanLLM(API_KEY, 5)

# llm = OllamaLLM(API_KEY)
llm=OllamaLLM(tar_len=5,api_key=API_KEY)


TotLog.init_log(len(config_person), if_event=args.e)

if not args.a:
    #初次实验    
    if os.path.exists(tar_log):
        raise Exception('Exp log file already exists')
    if os.path.exists(tar_memory):
        raise Exception('Exp memory file already exists')
    
    os.mkdir(tar_log)

    #引入模型
    model = RetireModel(G, config_person, llm, tar_memory)

    for i in range(args.round):
        model.step()


else:
    #附加实验
    if not os.path.exists(tar_log):
        raise Exception('Exp log file not exists')
    if not os.path.exists(tar_memory):
        raise Exception('Exp memory file not exists')

    offset = args.a

    TotLog.set_log(tar_log, offset)
    
    model = RetireModel(G, config_person, llm, tar_memory)
    
    print(offset)
    model.add_exp(offset)
    for i in range(offset,args.round):
        model.step()

#输出Log
#model.write_log('./log/%s/log' % exp_name) 
TotLog.write_log(tar_log)

# 将图像保存到文件
save_attitude_history(model.attitude_history, filename="experiment_attitude_test1_3_5.png")





