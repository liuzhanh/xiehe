import pandas as pd
import json
import re

# 读取 Excel 文件
excel_file_path = '3-user_info_with_exist_json.xlsx'
df = pd.read_excel(excel_file_path)

# 提取 json 列
json_column = df['json'].tolist()

# 转换为 Combined_Personas_154.json 的格式
result = []

for item in json_column:
    item = item.replace('说明：除了按要求设定的字段外，其余字段是根据合理推测和一般情况进行填写，以保证生成的json描述完整且符合逻辑。', '').replace('说明：部分信息如年龄、gender等在给定内容中未提及，根据一般情况进行了合理假设，以满足任务要求中“其他字段自 行填写，不能为空”的要求。', '').replace('<|templete|>：', '')
    item = re.sub(r'(\s*(//|#).*)', '', item)
    item = item.strip()
    try:
        # 尝试将每个单元格内容解析为 JSON 对象
        json_obj = json.loads(item)
        result.append(json_obj)
    except json.JSONDecodeError:
        print(f"无法解析以下内容为 JSON: {item}")

# 保存为 JSON 文件
json_file_path = 'Combined_Personas_new.json'
with open(json_file_path, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=4)

# 输出节点数量
node_count = len(result)
print(f"生成的 JSON 文件中的节点数量为: {node_count}")
print(f"处理完成，结果已保存到 {json_file_path}")