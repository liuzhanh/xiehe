import pandas as pd

# 读取 user_id_4914095331742409.xlsx 和 user_infos.csv 文件
user_id_excel_path = 'user_id_4914095331742409.xlsx'
user_infos_csv_path = 'user_infos.csv'
df_user_id = pd.read_excel(user_id_excel_path)
df_user_infos = pd.read_csv(user_infos_csv_path)

# 过滤掉不需要的 '用户名' 列
if '用户名' in df_user_infos.columns:
    df_user_infos = df_user_infos.drop(columns=['用户名'])

# 合并两个 DataFrame，以 user_id 中的数据为主
merged_df = pd.merge(df_user_id, df_user_infos, how='left', left_on='用户编号', right_on='用户ID')

# 添加 exist 列，标记是否匹配
merged_df['exist'] = merged_df['用户ID'].notnull().map({True: 'yes', False: 'no'})

# 当 exist 为 no 时，清除从 user_infos 合并过来的列
for col in df_user_infos.columns:
    if col != '用户ID':
        merged_df[col] = merged_df.apply(lambda row: row[col] if row['exist'] == 'yes' else None, axis=1)

# 保存结果到新的文件
output_excel_path = '2-user_info_with_exist.xlsx'
merged_df.to_excel(output_excel_path, index=False)

print(f"处理完成，结果已保存到 {output_excel_path}")