import pandas as pd
import json
import subprocess
import re
from tqdm import tqdm  # 导入tqdm库以显示进度条

# 加载真实用户数据
real_data_path = '/home/LH/code-llm/config/0330/retweet/55/2-user_info_with_exist_test.xlsx'
real_data_df = pd.read_excel(real_data_path)

# 将生成的虚拟数据保存到新文件路径
generated_data_path = '/home/LH/code-llm/config/0330/retweet/55/3-user_info_with_exist_json.xlsx'
templete = {
    "age": 30,
    "occupation": "中资企业印尼分公司高管",
    "edu_level": "MBA",
    "income_level": "高",
    "marital_status": "已婚",
    "residence": "印尼雅加达",
    "personality": [
        "公正",
        "透明",
        "合作",
        "责任感"
    ],
    "values": [
        "公平",
        "诚信",
        "创新",
        "共赢"
    ],
    "motivation": "推动企业本土化发展，提升企业竞争力，同时促进印尼经济社会发展",
    "emotional_response": "面对挑战时保持冷静，注重长期利益而非短期得失",
    "decision_style": "理性分析，注重数据和信息，倾向于团队合作",
    "family_role": "家庭支柱",
    "job_role": [
        "决策者",
        "战略规划者",
        "团队领导者"
    ],
    "social_network": [
        "中资企业印尼分公司同事",
        "印尼政府官员",
        "印尼本地合作伙伴",
        "国际教育专家",
        "印尼社区领袖"
    ],
    "social_identity": "中印尼商业合作桥梁",
    "cultural_background": "苏迪曼出生于印尼的一个商人家庭，从小受到家族企业的影响，对商业有着浓厚的兴趣。他在印尼完成了本科教育，后赴中国深造获得MBA学位。他的价值观深受中印尼两国文化的影响，既注重印尼的传统美德，也认同中国的商业智慧。",
    "social_class": "中产阶级以上",
    "social_norms": "遵守印尼的商业法律和习俗，同时尊重中国的商业文化和习惯",
    "life_experience": "苏迪曼在商业领域拥有超过20年的经验，曾在中国和印尼的多家知名企业担任高管。他见证了中国和印尼经济的快速发展，也深刻理解两国合作的潜力和挑战。他的职业生涯中，成功推动多个大型项目落地，并在中印尼商业合作中发挥了重要作用。",
    "education_training": "印尼本地大学本科，中国知名商学院MBA，多次参加国际商业管理培训",
    "social_participation": "积极参与中印尼商业论坛和交流活动，推动两国企业合作",
    "opinion": "苏迪曼认为，鲁班工坊的建立对于印尼和中国来说都是一项双赢的合作。他支持鲁班工坊的发展，并愿意提供资源和经验，帮助印尼培养更多技术人才。他认为，通过鲁班工坊，可以加强中印尼两国的经济联系，促进两国文化的交流，为两国人民创造更多的就业机会和经济发展空间。"}

topic = {
    "#张雪峰# 邹振东诚邀张雪峰：来厦门请你吃沙茶面@张雪峰老师 #弱传播# 1、 首先我不建议把谁打晕，因为打晕了，那就真的不清醒了。2、 可以关切张雪峰的质疑，但不必害怕他的破坏力。张雪峰只不过是一家之言，谁都可以发表选什么专业的看法。要相信绝大多数学生和家长，他们会有头脑，有理性，不会把自己砸晕，而是会用脚投票，做出他们的选择。更不要说什么“张雪峰动了谁的奶酪？”你的奶酪万一少了，甚至不在了，大概率不是别人动了你的，而是你自己丢掉的。如果新闻传播专业自己行，一万个张雪峰说它不行，也没有用。反过来，如果新闻传播专业自己不行，没一个人说它，它也会完蛋。打垮新闻传播专业的只有自己，不可能是别人。3、 值得反思张雪峰提出的问题，却不要轻信他的结论。一个给排水专业毕业的自媒体人，他的粉丝比传播学的教授还要多，既要谦卑地承认这是现实，更要虚心地向人家学习，但由此得出新闻传播专业不值得选，在逻辑上是有问题的。非经济类专业的毕业生做经济的比比皆是，学文学的，学历史的，学哲学的，做大老板的大有人在。这并不影响那些把企业家作为人生追求的学子，热情报考经济类专业。马云毕业于杭州师范学院外语系，那些梦想再造一个阿里巴巴的年轻人，不会蜂拥选择外语专业。同样，张雪峰的粉丝千万，未来想做自媒体的同学，大概率也不会把给排水专业当做自己的志愿首选。4、 张雪峰的答案不必信，但张雪峰的发问值得警醒。一个新闻传播学专业的老师，如果他上的课没人听，写的文章没人看，人家有理由怀疑：你，真的懂传播吗？当然，不排除真的有这样的学者，他的课没人选，他的文章没人看，却的确是货真价实的大学问家。不过，让人家弱弱地怀疑一下，再按下确认键，还是应该允许的。这不是要求教新闻传播的老师都必须成为网红，正如不能要求苏炳添的教练跑得过苏炳添。但新闻传播学界脱离实际、脱离业界的现象，理应警惕。5、 学术界自嗨自乐的现象，在很多学科都存在。如今在一些学术群里，有一个怪现象，如果谁在顶级刊物发表了一篇文章，大家纷纷祝贺，但鲜有人关心这位学者，到底有了什么发现？提出了什么不一样观点？推动了什么理论创新？如果这位学者不过是又发表了一篇正确的废话，我为他悲哀；如果这位学者真的有思想有创见，我更为他悲凉。这和我们在20世纪80年代读书的时候很不一样，那时候无论是老师还是师生，谁关心你发什么刊物啊，大家热烈讨论的都是李泽厚又提出了什么理论，林兴宅又发表了什么新见。6、 新闻理想过于理想，考研比例真的很卷，求职之路难免艰难——对于新闻传播专业的老师，这是我们个人难以改变却无法回避的现实，我们不必画饼，无须承诺，更不要轻佻背书，除了尊重考生与家长现实的关切与考量，剩下唯一可做的就是：想起那些或无怨无悔，或误打误撞，却用超高分数考进新闻传播专业的学生，我们每一次走上讲台，都要摸摸自己的良心，对得起台下那一双双闪闪亮亮的眼睛吗？7、 最后，谢谢网友们对新闻传播专业的关注和讨论。如果张雪峰有机会来厦门，我特别想请他吃碗沙茶面，然后就着海风，清茶一杯，人间清醒、心平气和地听他畅谈对新闻传播专业的所思所想。我相信，即使被家长打晕了，还矢志不渝选择新闻传播专业的学子，还是会希望他们的老师，多听听传播实践者的不同声音，即便是气话狠话过头话，也谦卑寻找其间的金玉良言。"}


def call_large_model(real_data, templete, topic):
    # 准备输入数据，提取所需信息
    prompt = f"根据以下用户的部分身份信息:{real_data},请你进行思考和推测，来生成该用户的其他身份、性格等信息，进行下面中括号内的数据扩展填充，具体需要你模拟生成的信息如下（你推测后进行填空,并将字段名称一并输出，小括号内是我给你的注释，你的结果中不需要输出小括号内的内容）：[age:__(年龄，可以根据其生日来推断，如果真实数据中没有生日信息，则根据其他信息随机填一个10-70的年龄),edu_level:__(此处填教育水平，有学校信息可以根据学校推断，没有则按照其他推断),income_leve:__(收入水平),marital_status:__(婚姻状态),occupation:__(职业),motivation:__(动机),emotional_response:__(情感反应),decision_style:__(决策风格),family_role:__(家庭角色),job_role:__(工作角色),social_network:__(社交网络),social_identity:__(社会身份),cultural_background:__(文化背景),social_class:__(社会阶层),social_norms:__(社会规范),life_experience:__(生活经历),education_training:__(教育培训),social_participation:__(社会参与),opinion:__(观点)]。其中opinion字段为该用户对某个话题的态度，而话题内容是：{topic}，注意，该话题内容是该用户看到的一篇微博内容，而不是关于该用户的身份信息。请注意，你来填充这些信息时，每个信息都必须填充，不能空着，其次填充的字段的文字的形式请参考样例：{templete}，只参考填写形式而不参考样例中的背景内容,同时不要漏掉字段，不要修改字段名称。最后你输出时，只输出这个样例中的json格式的内容。"

    # 使用 subprocess 调用本地模型
    result = subprocess.run(['ollama', 'run', 'deepseek-r1:32b', prompt],
                            capture_output=True, text=True)

    # 返回模型输出
    return result.stdout.strip()  # 去除多余空白


# 提取 JSON 内容的函数
def extract_json_from_markdown(text):
    # 使用正则表达式匹配 ```json 和 ``` 之间的内容
    json_pattern = r'```json\s*([\s\S]*?)\s*```'
    match = re.search(json_pattern, text)

    if match:
        json_str = match.group(1)
        return json_str.strip()

        # 如果没有找到 Markdown 格式的 JSON，尝试直接查找 JSON 对象
    json_obj_pattern = r'(\{[\s\S]*\})'
    match = re.search(json_obj_pattern, text)
    if match:
        return match.group(1).strip()

    return None


# 处理数据生成虚拟数据
virtual_data_list = []
for idx, row in tqdm(real_data_df.iterrows(), total=real_data_df.shape[0], desc="Processing"): 
    # 创建用于模型的字典，包含列标题和对应值
    real_data = {col: row[col] for col in real_data_df.columns}
    # 创建虚拟数据字典
    virtual_data = {
        "id": row.get("用户ID", idx + 1),  # 假设真实数据中有userID字段
        "type": "full",
        "description": {
            "id": str(row.get("用户ID", idx + 1)),  # 与真实数据中的用户ID对应
            "name": row.get("用户名", ""),  # 用户名
            "gender": row.get("性别", ""),  # 性别
            "residence": row.get("所在地", ""),  # 地点
            # 以下字段根据模型生成
            "age": "",  # 年龄
            "occupation": "",  # 职业
            "edu_level": "",  # 教育水平
            "income_level": "",  # 收入水平
            "marital_status": "",  # 婚姻状态
            "motivation": "",  # 动机
            "emotional_response": "",  # 情感反应
            "decision_style": "",  # 决策风格
            "family_role": "",  # 家庭角色
            "job_role": [],  # 工作角色
            "social_network": [],  # 社交网络
            "social_identity": "",  # 社会身份
            "cultural_background": "",  # 文化背景
            "social_class": "",  # 社会阶层
            "social_norms": "",  # 社会规范
            "life_experience": "",  # 生活经历
            "education_training": "",  # 教育培训
            "social_participation": "",  # 社会参与
            "opinion": ""  # 从模型生成的观点
        }
    }

    # 调用大模型生成其他字段
    model_output = call_large_model(real_data, templete, topic)
    #print("model_output 类型:", type(model_output))
    #print("model_output 内容:", repr(model_output))
    # 提取 JSON 内容
    json_str = extract_json_from_markdown(model_output)

    if json_str:
        try:
            model_data = json.loads(json_str)
            #print("JSON 解析成功!")
        except json.JSONDecodeError as e:
            print(f"JSON 解析错误: {e}")
            print(f"提取的 JSON 字符串: {json_str[:100]}...")
            # 尝试修复常见的 JSON 格式问题
            json_str = json_str.replace('\n', ' ').replace('\r', '')
            try:
                model_data = json.loads(json_str)
                print("修复后 JSON 解析成功!")
            except json.JSONDecodeError:
                print("无法修复 JSON，使用空字典")
                model_data = {}
    else:
        print("无法从输出中提取 JSON 内容")
        model_data = {}
    for key in model_data:
        if key in virtual_data["description"]:
            virtual_data["description"][key] = model_data[key]

    virtual_data_list.append(virtual_data)

# 将生成的虚拟数据保存到DataFrame
virtual_df = pd.DataFrame({"json": virtual_data_list})

# 数据保存到新Excel文件
virtual_df.to_excel(generated_data_path, index=False)