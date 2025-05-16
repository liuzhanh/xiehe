from sim_agent import FullAgent, LiteAgent
from casevo import ModelBase, TotLog
from thread_send import ThreadSend
from tqdm import tqdm
import time

class SimModel(ModelBase):
    def __init__(self, tar_graph, person_list, llm, memory_path, offset=0):
        """
        初始化对话系统中的每个人物和他们的对话流程。

        :param tar_graph: 目标图，表示对话系统的结构。
        :param person_list: 人物列表，包含所有参与对话的人物信息。
        :param llm: 语言模型，用于生成对话内容。
        """
        
        super().__init__(tar_graph, llm, memory_path=memory_path, reflect_file='reflect.md', type_schedule=True)
        self.attitude_history = []  # 用于存储每个时间步的态度变化

        self.offset = offset


        #设置Agent 含full和lite       
        for cur_id in range(len(person_list)):
            cur_person = person_list[cur_id]
            if cur_person['type'] == 'lite':
                cur_agent = LiteAgent(cur_id, self, cur_person['args'])
            else:
                cur_agent = FullAgent(cur_id, self, cur_person['description'], None)
            self.add_agent(cur_agent, cur_id)

    
    def add_exp(self, offset):
        self.offset = offset
        for i in range(len(self.agent_list)):
            cur_agent = self.agent_list[i]
            cur_log = TotLog.get_agent_log(cur_agent.unique_id)
            if type(cur_agent) == FullAgent:
                last_id = -1
                long_memory = None
                for item in cur_log[::-1]:
                    if item['type'] == 'reflect':
                        last_id = item['item']['last_id']
                        long_memory = item['item']['new_opinion']
                        break
                cur_agent.memory.last_id = last_id
                cur_agent.memory.long_memory = long_memory
            
            if type(cur_agent) == LiteAgent:
                last_attitude = -1
                for item in cur_log[::-1]:
                    if item['type'] == 'reflect':
                        last_attitude = item['item']['new_attitude']
                        break
                cur_agent.attitude = last_attitude
        
    def generate_talk(self):

        cur_thread = ThreadSend(4)
        for cur_agent in self.agent_list:
            if type(cur_agent) == FullAgent:
                cur_thread.add_task(cur_agent.generate_talk, ())
        
        print('generate_talk ', cur_thread.get_task_num(), self.schedule.time + self.offset)
        self.pbar = tqdm(total=cur_thread.get_task_num(), desc="generate_talk by FullAgent")
        cur_thread.start_thread()
        self.pbar.close()

    def vote(self):
        cur_thread = ThreadSend(4)
        for cur_agent in self.agent_list:
            if type(cur_agent) == FullAgent:
                cur_thread.add_task(cur_agent.vote, ())
            else:
                cur_agent.vote()
        
        print('vote task num', cur_thread.get_task_num())
        self.pbar = tqdm(total=cur_thread.get_task_num(), desc="vote by AllAgent")
        cur_thread.start_thread()
        self.pbar.close()
    
    def reflect(self):
        cur_thread = ThreadSend(4)
        for cur_agent in self.agent_list:
            if type(cur_agent) == FullAgent:
                cur_thread.add_task(cur_agent.reflect, ())
            else:
                cur_agent.reflect()
        print('reflect task num', cur_thread.get_task_num())
        self.pbar = tqdm(total=cur_thread.get_task_num(), desc="reflect by AllAgent")
        cur_thread.start_thread()
        self.pbar.close()
        
    
    def reset(self):
        for cur_agent in self.agent_list:
            cur_agent.reset()

    def public_news(self):
        """
        所有Agent读取的公开微博。

        此函数模拟一次阅读微博的过程：
            首先打印出读取的开始时间
            然后读取当前微博的主题总结，
            接着让每个参与者（agent）听取主题总结。
            最后，将此次的内容记录到日志中，并打印出结束时间。
        
        该方法不接受任何参数，也没有返回值。
        """
        
        #获取微博文本
        cur_news_num = self.schedule.time + self.offset
        print('public_news: %d start' % cur_news_num)
        file_path = f'contents/{cur_news_num}.txt'
        try:
            with open(file_path, encoding='utf-8') as f:
                cur_news_summary = f.read()
        except FileNotFoundError:
            print(f"Error: File {file_path} not found.")
            return
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return
        
        # 单线程请求
        for cur_agent in tqdm(self.agent_list, desc="public_news for agents"):
            if isinstance(cur_agent, FullAgent):
                cur_agent.listen(cur_news_summary, 0, "public")
                
        # 事件加入日志
        log_item = {
            'news_content': cur_news_summary
        }
        TotLog.add_model_log(self.schedule.time, 'public_news', log_item)

        print('public_news: %d end' % self.schedule.time)   

    def step(self):
        st = time.time()

        # 记录每个代理的当前态度
        print('11:', self.schedule.time, self.offset)
        time_step = self.schedule.time + self.offset
        attitudes = [agent.attitude for agent in self.agent_list]
        self.attitude_history.append((time_step, attitudes))  # 保存时间戳和对应的态度值

        if time_step % 2 == 0:
            self.public_news()
        
        self.generate_talk()
        print('Node generate talk time: %.2f' % (time.time() - st))

        self.schedule.step_type(FullAgent)

        if attitudes:
            self.schedule.step_type(LiteAgent)

        self.schedule.step() # 新加
        
        st = time.time()
        print('Node Reflect %d' % (self.schedule.time + self.offset))
        # 节点反思
        self.reflect()
        print('Node Reflect time: %.2f' % (time.time() - st))
        
        st = time.time()
        print('Node Vote %d' % (self.schedule.time + self.offset))
        self.vote()
        print('Node Vote time: %.2f' % (time.time() - st))
        
        # 手动递增时间步
        self.schedule.time += 1  # 增加时间步

        self.reset()

        print('-------------------')
        return 0
    