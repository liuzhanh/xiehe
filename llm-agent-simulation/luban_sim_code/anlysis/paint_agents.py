import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import json
import random

# 载入人员数据
with open('../config/facebook_combined/nodes_data_fl.json') as f:
    person_list = json.load(f)

agent_num = len(person_list)

# 用于保存所有 FullAgent 的投票历史数据
vote_list = []

# 遍历所有代理
for i in range(agent_num):
    # 读取每个代理的日志文件
    with open(f'../log/experiment_test1_3_5/agent_{i}.json') as f:
        cur_log = json.load(f)

    cur_vote = []

    # 遍历代理的投票日志
    for item in cur_log:
        if item['type'] == 'vote':
            cur_vote.append(item['item']['attitude'])  # 收集投票的态度值

    x = [j for j in range(len(cur_vote))]  # 生成时间步序列

    if person_list[i]['type'] == 'full':  # FullAgent画红色线
        vote_list.append(cur_vote)  # 将 FullAgent 的投票历史添加到列表中
    else:  # LiteAgent画蓝色线
        plt.plot(x, cur_vote, color='blue', alpha=0.7) 

# 绘制所有 FullAgent 的投票历史
for item in vote_list:
    plt.plot(x, item, color='red', alpha=0.7)  # FullAgent 用红色

plt.xlabel('Time Step')
plt.ylabel('Attitude')
plt.title('Attitude Change Over Time')

# 显示相关参数的值（alpha、N、k、p 等）
plt.text(0.95, 0.95, f'alpha = 0.1', ha='right', va='top', transform=plt.gca().transAxes)
plt.text(0.95, 0.90, f'N = {agent_num}, k = 10, p = 0.1,eta=0.5,noise=0.01', ha='right', va='top', transform=plt.gca().transAxes)

# 设置 Y 轴范围和网格
plt.ylim(-1, 1)  # 限制 Y 轴范围为 [-1, 1]
plt.grid(True)

# 保存
plt.savefig('test1_3_5.png')
print("Saved plot to test1_3_5.png")
