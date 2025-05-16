#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Author: Your Name
Date: 2025-03-15
Description:
  1. 读取 Generated_Personas.json (含 full/brief agent)
  2. 找到所有 ID 的最大值
  3. 在 [0, max_id] 范围内，对缺失的 ID 生成 lite agent
  4. 输出到 Combined_Personas.json
"""

import json
import random

def generate_lite_agent(agent_id: int) -> dict:
    """
    根据给定的 agent_id, 生成一个 'lite' 类型的代理信息.
    attitude 在 [-1, 1] 区间随机。
    """
    return {
        "id": agent_id,
        "type": "lite",
        "args": {
            "attitude": random.uniform(-1, 1),  # 保留4位小数或按需
            "will": random.uniform(0, 1),       # 保留4位小数或按需
            "difficulty": random.randint(1, 5), # 难度在 [1, 5] 之间
        }
    }

def main():
    input_file = "Generated_Personas.json"     # 你的原始文件
    output_file = "Combined_Personas.json"     # 输出的新文件

    # 1. 读取原有的 full/brief agent 列表
    with open(input_file, "r", encoding="utf-8") as f:
        original_agents = json.load(f)

    # 2. 收集已有的所有 ID，并保存到一个映射中 agent_map[id] = agent_data
    agent_map = {}
    for item in original_agents:
        # item["id"] 有时是字符串，有时是整数，看你的数据而定，这里统一转成 int
        item_id = int(item["id"])
        agent_map[item_id] = item

    # 3. 找到最大 ID
    max_id = max(agent_map.keys()) if agent_map else 0
    print(f"Max ID in original data = {max_id}")

    # 4. 从 0 ~ max_id 逐个检查，如果没在 agent_map 中，则生成 lite agent
    for i in range(max_id + 1):
        if i not in agent_map:
            agent_map[i] = generate_lite_agent(i)

    # 5. 按照升序 ID 排列，构建最终列表
    final_list = [agent_map[i] for i in sorted(agent_map.keys())]

    # 6. 写出到新的 JSON 文件
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_list, f, indent=4, ensure_ascii=False)

    print(f"Combined data saved to {output_file}")
    print(f"Total agents: {len(final_list)}")

if __name__ == "__main__":
    main()
