import random
import json

# 生成一个节点的数据
def generate_node(id):
    return {
        "id": id,
        "type": "lite",
        "args": {
            'attitude': random.uniform(-1, 1),  # 从 [-1, 1] 区间均匀采样 attitude
        }
    }

# 生成100个节点的数据集
def generate_nodes(num_nodes=100):
    nodes = []
    for i in range(1, num_nodes + 1):
        node = generate_node(i)
        nodes.append(node)
    return nodes

# 将生成数据保存为 JSON 文件
def save_nodes_to_file(filename="nodes_data.json", num_nodes=100):
    nodes = generate_nodes(num_nodes)
    with open(filename, 'w') as f:
        json.dump(nodes, f, indent=4)  


save_nodes_to_file()
