import pandas as pd  
import json  
import re  
import ast  

# 读取 Excel 文件  
excel_file_path = '/home/LH/code-llm/config/0330/retweet/根正苗红的贫农/3-user_info_with_exist_json.xlsx'  
df = pd.read_excel(excel_file_path)  

# 提取 json 列  
json_column = df['json'].tolist()  

# 转换为 Combined_Personas_154.json 的格式  
result = []  

for item in json_column:  
    # 移除不需要的说明文本  
    item = item.replace('说明：除了按要求设定的字段外，其余字段是根据合理推测和一般情况进行填写，以保证生成的json描述完整且符合逻辑。', '')  
    item = item.replace('说明：部分信息如年龄、gender等在给定内容中未提及，根据一般情况进行了合理假设，以满足任务要求中"其他字段自 行填写，不能为空"的要求。', '')  
    item = item.replace('<|templete|>：', '')  
    item = re.sub(r'(\s*(//|#).*)', '', item)  
    item = item.strip()  
    
    try:  
        # 首先尝试将字符串解析为Python字典  
        if isinstance(item, str):  
            # 检查是否已经是字典类型  
            if item.startswith('{') and item.endswith('}'):  
                try:  
                    # 使用ast.literal_eval安全地将字符串转换为字典  
                    dict_obj = ast.literal_eval(item)  
                    result.append(dict_obj)  
                except (SyntaxError, ValueError) as e:  
                    print(f"无法将字符串转换为字典: {e}")  
                    print(f"问题字符串: {item[:100]}...")  
            else:  
                # 尝试作为JSON字符串解析  
                json_obj = json.loads(item)  
                result.append(json_obj)  
        elif isinstance(item, dict):  
            # 如果已经是字典类型，直接添加  
            result.append(item)  
        else:  
            print(f"未知类型的数据: {type(item)}")  
            print(f"数据内容: {item}")  
    except Exception as e:  
        print(f"处理数据时出错: {e}")  
        print(f"问题数据: {item[:100]}...")  

# 保存为 JSON 文件  
json_file_path = '/home/LH/code-llm/config/0330/retweet/根正苗红的贫农/Combined_Personas_new.json'  
with open(json_file_path, 'w', encoding='utf-8') as f:  
    json.dump(result, f, ensure_ascii=False, indent=4)  

# 输出节点数量  
node_count = len(result)  
print(f"生成的 JSON 文件中的节点数量为: {node_count}")  
print(f"处理完成，结果已保存到 {json_file_path}")