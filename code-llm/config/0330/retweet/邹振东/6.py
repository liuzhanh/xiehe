import json
import pandas as pd

# 读取 user_infos.csv 文件
user_infos = pd.read_csv('user_infos.csv')
valid_ids = set(int(id) for id in user_infos['用户ID'].tolist())

# 读取 repo_4914095331742409_network.json 文件
with open(r'repo_4914095331742409_network.json', 'r', encoding='utf-8') as f:
    network = json.load(f)

# 过滤 nodes 中的无效 id
valid_nodes = []
for node in network['nodes']:
    node_id = int(node['id'])
    if node_id in valid_ids:
        valid_nodes.append(node)
    else:
        valid_ids.add(node_id)
        valid_nodes.append(node)
        print(f"Node ID {node_id} not found in user_infos.csv, discarded.")

# 过滤 links 中的无效 id
valid_links = []
for link in network.get('links', []):
    source = int(link.get('source'))
    target = int(link.get('target'))
    if source in valid_ids and target in valid_ids:
        valid_links.append(link)
    else:
        print(f"Link with source {source} and target {target} not found in user_infos.csv, discarded.")

# 更新 network 中的 nodes 和 links
network['nodes'] = valid_nodes
network['links'] = valid_links

# 第一次映射，使用负数作为临时 id
original_ids = []
for node in network['nodes']:
    original_ids.append(int(node['id']))
for link in network['links']:
    source = int(link.get('source'))
    target = int(link.get('target'))
    original_ids.extend([source, target])

# 去重
unique_original_ids = list(set(original_ids))

# 创建第一次 ID 映射表，使用负数作为临时 id
first_id_mapping = {original_id: -i - 1 for i, original_id in enumerate(unique_original_ids)}
if 1164 in first_id_mapping:
    print(f"第一次映射中，1164 被替换为 {first_id_mapping[1164]}")

# 第一次更新 nodes 中的 id
for node in network['nodes']:
    original_id = int(node['id'])
    new_id = first_id_mapping[original_id]
    node['id'] = new_id

# 第一次更新 links 中的 id
for link in network['links']:
    if 'source' in link:
        link['source'] = first_id_mapping[int(link['source'])]
    if 'target' in link:
        link['target'] = first_id_mapping[int(link['target'])]

# 第二次映射，从 0 开始重新编号
temp_ids = []
for node in network['nodes']:
    temp_ids.append(int(node['id']))
for link in network['links']:
    source = int(link.get('source'))
    target = int(link.get('target'))
    temp_ids.extend([source, target])

# 去重
unique_temp_ids = list(set(temp_ids))

# 创建第二次 ID 映射表，从 0 开始
second_id_mapping = {temp_id: new_id for new_id, temp_id in enumerate(unique_temp_ids)}
if 1164 in second_id_mapping:
    print(f"第二次映射中，1164 被替换为 {second_id_mapping[1164]}")
# 第二次更新 nodes 中的 id
for node in network['nodes']:
    temp_id = int(node['id'])
    new_id = second_id_mapping[temp_id]
    node['id'] = new_id

# 第二次更新 links 中的 id
for link in network['links']:
    if 'source' in link:
        link['source'] = second_id_mapping[int(link['source'])]
    if 'target' in link:
        link['target'] = second_id_mapping[int(link['target'])]

# 保存更新后的文件
with open(r'repo_4914095331742409_network_new.json', 'w', encoding='utf-8') as f:
    json.dump(network, f, ensure_ascii=False, indent=4)

print("Processing completed. New file has been generated.")