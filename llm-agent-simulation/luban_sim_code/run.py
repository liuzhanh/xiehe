import sys
import os
import argparse
import json
import yaml

import networkx as nx
from networkx.readwrite import json_graph

# 引入模型与辅助函数
from models import RetireModel
from ollama_lib import OllamaLLM
from casevo import TotLog
from plot_attitudes import save_attitude_history
from agents import FullAgent, LiteAgent

# 读取配置文件 config.yml
with open("config.yml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# 设置命令行参数，命令行参数的优先级高于config.yml中的默认值
parser = argparse.ArgumentParser(description='Run the Mesa model with configuration from config.yml.')

parser.add_argument('--personfile', type=str, default=config.get("person_file"),
                    help='人物身份信息文件路径（json格式）')
parser.add_argument('--round', type=int, default=config.get("round_num"),
                    help='模拟的回合数')
parser.add_argument('--exp', type=str, default=config.get("exp_name"),
                    help='本次测试结果存放文件夹名')
parser.add_argument('-e', action='store_true', help='事件日志标记')
parser.add_argument('-a', metavar='offset', type=int, help='附加之前模拟的偏移回合')

# 小世界网络生成参数，默认值为config.yml中的配置
parser.add_argument('--n', type=int, default=config.get("n", 127),
                    help='小世界网络中的节点数')
parser.add_argument('--k', type=int, default=config.get("k", 10),
                    help='每个节点在环形拓扑中连接到最近的k个邻居')
parser.add_argument('--p', type=float, default=config.get("p", 0.1),
                    help='边重连的概率')

args = parser.parse_args()

# 从命令行或配置文件中获得关键参数
tar_person = args.personfile
round_num = args.round
exp_name = args.exp


# 打印本次实验的参数
print(f"Experiment Parameters:")
print(f"  Person file: {tar_person}")
print(f"  Round number: {round_num}")
print(f"  Experiment name: {exp_name}")
# print(f"  Event log: {args.e}")
# print(f"  Offset: {args.a}")
print(f"  Small world network parameters: n={args.n}, k={args.k}, p={args.p}")

# 读取人物配置文件（身份信息）
with open(tar_person, 'r', encoding="utf-8") as f:
    config_person = json.load(f)

# 根据实验名称构建日志、内存、缓存路径
tar_log = os.path.join('.', 'log', exp_name)
tar_memory = os.path.join('.', 'memory', exp_name)
tar_cache = os.path.join('.', 'cache', f"{exp_name}.db")

# 使用 Watts-Strogatz 模型生成小世界网络
G = nx.watts_strogatz_graph(n=args.n, k=args.k, p=args.p)
print(f"Generated small world network with {args.n} nodes, each connected to {args.k} neighbors, rewiring probability {args.p}")
print(f"Number of edges: {G.number_of_edges()}")

# 初始化 llm 对象，传入 config 中的对话模型、嵌入模型、base url 以及部署方式
llm = OllamaLLM(
    tar_len=5,
    api_key=config.get("api_key"),
    chat_model=config.get("chat_model"),
    embedding_model=config.get("embedding_model"),
    base_url=config.get("base_url"),
    deployment_method=config.get("deployment_method")
)




# 初始化日志，参数：人物数量和事件日志标识
TotLog.init_log(len(config_person), if_event=args.e)

if args.a is None:
    # 初次实验
    if os.path.exists(tar_log):
        raise Exception('Experiment log folder already exists.')
    if os.path.exists(tar_memory):
        raise Exception('Experiment memory folder already exists.')
    
    os.mkdir(tar_log)

    # 引入并运行模型
    model = RetireModel(G, config_person, llm, tar_memory)
    for i in range(round_num):
        model.step()
else:
    # 附加实验：必须已有日志和内存文件
    if not os.path.exists(tar_log):
        raise Exception('Experiment log folder does not exist.')
    if not os.path.exists(tar_memory):
        raise Exception('Experiment memory folder does not exist.')
    
    offset = args.a
    TotLog.set_log(tar_log, offset)
    
    model = RetireModel(G, config_person, llm, tar_memory)
    print(f"Starting simulation from offset {offset}")
    model.add_exp(offset)
    for i in range(offset, round_num):
        model.step()

# 输出日志并保存态度历史图像
TotLog.write_log(tar_log)
save_attitude_history(model.attitude_history, filename="experiment_attitude_test1_3_5.png")
