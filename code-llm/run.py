import os
import time
# import networkx as nx
from networkx.readwrite import json_graph
import json 
from sim_model import SimModel
import argparse
from ollama_api import OllamaLLM
from casevo import TotLog
from plot_attitudes import  save_attitude_history

parser = argparse.ArgumentParser(description='run the Mesa model.')
st = time.time()
parser.add_argument('graphfile', metavar='graph_file', type=str,
                   help='The graph file for the sim')

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
parser.add_argument('-vllm', type=bool, help='VLLM API', default=False)


args = parser.parse_args()

tar_graph = args.graphfile
tar_person = args.personfile
exp_name = args.exp

with open(tar_graph, 'r') as f:
    config_graph = json.load(f) 

with open(tar_person, 'r', encoding='utf-8') as f:
    config_person = json.load(f)     
    


tar_log = './log/%s/' % exp_name
tar_memory = './memory/%s/' % exp_name
tar_cache = './cache/%s.db' % exp_name


#获取配置
G = json_graph.node_link_graph(config_graph, edges="links")
# 生成小世界网络********************************************************************************
# python .\run.py .\config\0326\Combined_Personas_154.json 3 exp_154 -n 154 -k 10 -p 0.1
# python .\run.py .\config\0327\Combined_Personas_3001.json 30 exp_3001-watts -n 3001 -k 10 -p 0.1
# G = nx.watts_strogatz_graph(n=args.n, k=args.k, p=args.p)  # 使用Watts-Strogatz模型生成网络
# python .\run.py .\config\0327\Combined_Personas_3001.json 3 exp_3001 -n 3001 -k 10
# G = nx.barabasi_albert_graph(args.n, args.k)  # BA网络
# 打印网络信息
# print(f"Generated small world network with {args.n} nodes, each connected to {args.k} neighbors, rewiring probability {args.p}")
# print(f"Number of edges: {G.number_of_edges()}")

llm=OllamaLLM(tar_len=15, vllm_flag=args.vllm)


TotLog.init_log(len(config_person), if_event=args.e)

if not args.a:
    #初次实验    
    if os.path.exists(tar_log):
        raise Exception('Exp log file already exists')
    if os.path.exists(tar_memory):
        raise Exception('Exp memory file already exists')
    
    os.mkdir(tar_log)

    #引入模型
    model = SimModel(G, config_person, llm, tar_memory)

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
    
    model = SimModel(G, config_person, llm, tar_memory, offset*2)
    
    print(offset*2)
    model.add_exp(offset*2)
    for i in range(offset, args.round):
        model.step()

#输出Log
TotLog.write_log(tar_log)

# 将图像保存到文件
save_attitude_history(model.attitude_history, filename=f"{exp_name}_experiment_attitude.png")

print('Total time consumed: %.2fs' % (time.time() - st))
