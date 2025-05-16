import json

# Read the Combined_Personas_new.json file
with open(r'Combined_Personas_new.json', 'r', encoding='utf-8') as f:
    combined_personas = json.load(f)

# Read the repo_4914095331742409_network.json file
with open(r'repo_4914095331742409_network.json', 'r', encoding='utf-8') as f:
    network = json.load(f)

original_ids = []
for item in combined_personas:
    try:
        original_ids.append(int(item['id']))
    except ValueError:
        print(f"Error converting {item['id']} to an integer.")

for node in network['nodes']:
    try:
        original_ids.append(int(node['id']))
    except ValueError:
        print(f"Error converting {node['id']} to an integer.")
print('1:',len(original_ids))
for link in network.get('links', []):
    source = link.get('source')
    target = link.get('target')
    if source is not None:
        try:
            original_ids.append(int(source))
        except ValueError:
            print(f"Error converting {source} to an integer.")
    if target is not None:
        try:
            original_ids.append(int(target))
        except ValueError:
            print(f"Error converting {target} to an integer.")

print('2:',len(original_ids))
# Remove duplicates
unique_original_ids = list(set(original_ids))
print('3:',len(unique_original_ids))

# Find the maximum value among the original IDs
max_original_id = max(unique_original_ids)
print('4:',max_original_id)

# Create an ID mapping table, starting from the maximum value plus 1
id_mapping = {original_id: new_id for new_id, original_id in enumerate(unique_original_ids, start=max_original_id + 1)}

# Update the IDs in Combined_Personas_565.json
for item in combined_personas:
    original_id = int(item['id'])
    new_id = id_mapping[original_id]
    item['id'] = new_id
    if 'description' in item and 'id' in item['description']:
        item['description']['id'] = str(new_id)

# Update the IDs in repo_4913201571694562_network.json
for node in network['nodes']:
    original_id = int(node['id'])
    new_id = id_mapping[original_id]
    node['id'] = new_id

# Update the IDs in the links
for link in network.get('links', []):
    if 'source' in link:
        link['source'] = id_mapping[int(link['source'])]
    if 'target' in link:
        link['target'] = id_mapping[int(link['target'])]

# Collect all updated IDs
updated_ids = []
for item in combined_personas:
    updated_ids.append(item['id'])
for node in network['nodes']:
    updated_ids.append(node['id'])
for link in network.get('links', []):
    updated_ids.extend([link.get('source'), link.get('target')])
print('5:',len(updated_ids))

# Remove duplicates
unique_updated_ids = sorted(set(updated_ids))
print('6:',len(unique_updated_ids))

# Create a new ID mapping table, starting from 0
new_id_mapping = {old_id: new_id for new_id, old_id in enumerate(unique_updated_ids)}

# Update the IDs in Combined_Personas_565.json again
for item in combined_personas:
    old_id = item['id']
    new_id = new_id_mapping[old_id]
    item['id'] = new_id
    if 'description' in item and 'id' in item['description']:
        item['description']['id'] = str(new_id)

# Update the IDs in repo_4913201571694562_network.json again
for node in network['nodes']:
    old_id = node['id']
    new_id = new_id_mapping[old_id]
    node['id'] = new_id

# Update the IDs in the links again
for link in network.get('links', []):
    if 'source' in link:
        link['source'] = new_id_mapping[link['source']]
    if 'target' in link:
        link['target'] = new_id_mapping[link['target']]

# Save the updated files
with open(r'Combined_Personas_1180_new.json', 'w', encoding='utf-8') as f:
    json.dump(combined_personas, f, ensure_ascii=False, indent=4)

with open(r'repo_4913201571694562_network_new.json', 'w', encoding='utf-8') as f:
    json.dump(network, f, ensure_ascii=False, indent=4)

print("Processing completed. New files have been generated.")