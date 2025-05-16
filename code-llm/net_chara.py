import networkx as nx
from networkx.readwrite import json_graph
import json 

# tar_graph = r'.\config\0330\retweet\根正苗红的贫农\repo_4913201571694562_network_new.json'

tar_graph = r'.\config\0330\retweet\邹振东\repo_4913201571694562_network_new.json'

with open(tar_graph, 'r') as f:
    config_graph = json.load(f) 


#获取配置
G = json_graph.node_link_graph(config_graph, edges="links")

print(f"节点：{len(G.nodes)}, 边：{len(G.edges)}")
import networkx as nx
if G.is_multigraph():
    # Convert multigraph to a simple graph
    G = nx.Graph(G)

# 1. 平均度
def average_degree(graph):
    degrees = [degree for node, degree in graph.degree()]
    return sum(degrees) / len(degrees) if degrees else 0

average_deg = average_degree(G)
print(f"Average Degree: {average_deg}")

# 2. 匹配系数（也称为边密度）
def matching_coefficient(graph):
    return nx.density(graph)

matching_coeff = matching_coefficient(G)
print(f"Matching Coefficient (Density): {matching_coeff}")

# 3. 集聚系数（平均集聚系数）
clustering_coeff = nx.average_clustering(G)
print(f"Average Clustering Coefficient: {clustering_coeff}")

# 4. 平均最短路径长度
# 首先确保图是连通的，为此可以获取最大的连通子图
if nx.is_connected(G):
    avg_shortest_path = nx.average_shortest_path_length(G)
    print(f"Average Shortest Path Length: {avg_shortest_path}")
else:
    # 如果图不是连通的，可以对最大的连通子图进行计算
    largest_cc = max(nx.connected_components(G), key=len)
    subgraph = G.subgraph(largest_cc)
    avg_shortest_path = nx.average_shortest_path_length(subgraph)
    print(f"Average Shortest Path Length (for largest connected component): {avg_shortest_path}")