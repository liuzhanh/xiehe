# -*- coding: utf-8 -*-
import requests
import pandas as pd
import time
import random
from csv import writer, QUOTE_MINIMAL

def crawl_user_info(user_id, cookies, headers):
    """爬取用户基本信息和详细信息"""
    base_url = 'https://weibo.com/ajax/profile/info?uid='
    detail_url = 'https://weibo.com/ajax/profile/detail?uid='

    try:
        user_id = str(int(user_id))
        response_info = requests.get(base_url + str(user_id), cookies=cookies, headers=headers, timeout=10)
        response_detail = requests.get(detail_url + str(user_id), cookies=cookies, headers=headers, timeout=10)
        
        if response_info.status_code == 200 and response_detail.status_code == 200:
            data_info = response_info.json()
            data_detail = response_detail.json()
            user_info = data_info.get('data', {}).get('user', {})
            detail_data = data_detail.get('data', {})

            if user_info and detail_data:
                return {
                    "用户ID": user_id,
                    "用户名": user_info.get('screen_name', '未知'),
                    "所在地": user_info.get('location', '未知'),
                    "性别": "男" if user_info.get('gender') == 'm' else "女" if user_info.get('gender') == 'f' else "未知",
                    "认证状态": "已认证" if user_info.get('verified') else "未认证",
                    "认证类型": {
                        -1: "普通用户",
                        0: "名人",
                        1: "政府",
                        2: "企业",
                        3: "媒体",
                        4: "校园",
                        5: "网站",
                        6: "应用",
                        7: "团体（机构）"
                    }.get(user_info.get('verified_type'), '未知'),
                    "认证理由": user_info.get('verified_reason', '无'),
                    "个人描述": user_info.get('description', '无'),
                    "信用等级": detail_data.get('sunshine_credit', {}).get('level', '未知'),
                    "公司": detail_data.get('career', {}).get('company', '未知') or detail_data.get('company', '未知'),
                    "学校": detail_data.get('education', {}).get('school', '未知'),
                    "生日": detail_data.get('birthday', '未知'),
                    "创建时间": detail_data.get('created_at', '未知'),
                    "粉丝数": user_info.get('followers_count', '未知'),
                    "关注数": user_info.get('friends_count', '未知'),
                    "微博数": user_info.get('statuses_count', '未知'),
                    "获评转赞总数": user_info.get('status_total_counter', {}).get('total_cnt_format'),
                    "获评论数": user_info.get('status_total_counter', {}).get('comment_cnt'),
                    "获转发数": user_info.get('status_total_counter', {}).get('repost_cnt'),
                    "获点赞数": user_info.get('status_total_counter', {}).get('like_cnt'),
                }
            else:
                print(f"No user data found for UID {user_id}.")
                return None
        else:
            print(f"Failed to fetch data for UID {user_id}. HTTP Status Code: {response_info.status_code} or {response_detail.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching data for UID {user_id}: {e}")
        return None

# 读取Excel文件中的uid列
df = pd.read_excel(r'./user_id_4914095331742409.xlsx') #此处需要更换为你的文件路径与名称
user_ids = df['用户编号'].tolist()  # 'user_id'列放的是uid

# 记得更换cookies
cookies = {'Cookie': ''}  # 替换为实际的cookies
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0'  # 替换为实际的User-Agent
}


# 存储所有用户信息的列表
all_user_infos = []

# 将所有用户信息保存到一个新的CSV文件中
output_file = 'user_infos.csv'
with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
    dw = writer(f, quoting=QUOTE_MINIMAL)
    # 写入标题行
    csv_headers = ["用户ID", "用户名", "所在地", "性别", "认证状态", "认证类型", "认证理由", "个人描述", "信用等级", "公司", "学校", "生日", "创建时间", "粉丝数", "关注数", "微博数", "获评转赞总数", "获评论数", "获转发数", "获点赞数"]
    dw.writerow(csv_headers)  # 写入列名
    total_user_ids = len(user_ids)
    for index, user_id in enumerate(user_ids, start=1):
        user_info = crawl_user_info(user_id, cookies, headers)
        if user_info:
            dw.writerow(list(user_info.values()))  # 写入行数据，确保是列表
            print(f"爬取到第 {index} 个用户，共 {total_user_ids} 个用户")
        time.sleep(random.uniform(3, 5))  # 每次请求后暂停3-5秒

print(f"用户信息已保存到CSV文件：{output_file}，共爬取 {len(user_ids)} 个用户信息。")


