from agents import FullAgent, LiteAgent

# from mesa.time import BaseScheduler

from casevo import ModelBase, TotLog

from thread_send import ThreadSend

from tqdm import tqdm

import time
import matplotlib.pyplot as plt


class RetireModel(ModelBase):
    def __init__(self, tar_graph, person_list, llm, memory_path):
        """
        初始化对话系统中的每个人物和他们的对话流程。

        :param tar_graph: 目标图，表示对话系统的结构。
        :param person_list: 人物列表，包含所有参与对话的人物信息。
        :param llm: 语言模型，用于生成对话内容。
        """
        
        super().__init__(tar_graph, llm, memory_path=memory_path, reflect_file='reflect.md', type_schedule=True)
        self.attitude_history = []  # 用于存储每个时间步的态度变化

        self.offset = 0


        #设置Agent 含full和lite       
        for cur_id in range(len(person_list)):
            cur_person = person_list[cur_id]
            if cur_person['type'] == 'lite':
                cur_agent = LiteAgent(cur_id, self, cur_person['args'])
            else:
                cur_agent = FullAgent(cur_id, self, cur_person['description'], None)
            self.add_agent(cur_agent, cur_id)
       
    
    def add_exp(self, offset):
        #self.log.set_log(model_log, offset)
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
        
        print('generate_talk ', cur_thread.get_task_num())
        self.pbar = tqdm(total=cur_thread.get_task_num())
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
        self.pbar = tqdm(total=cur_thread.get_task_num())
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
        self.pbar = tqdm(total=cur_thread.get_task_num())
        cur_thread.start_thread()
        self.pbar.close()
    
    def reset(self):
        for cur_agent in self.agent_list:
            cur_agent.reset()


    def step(self):
        st = time.time()

        # 记录每个代理的当前态度
        time_step = self.schedule.time
        attitudes = [agent.attitude for agent in self.agent_list if isinstance(agent, LiteAgent)]
        self.attitude_history.append((time_step, attitudes))  # 保存时间戳和对应的态度值

        self.generate_talk()
        print('generate time: %.2f' % (time.time() - st))

        self.schedule.step_type(FullAgent)
        
        self.schedule.step_type(LiteAgent)

        self.schedule.step()#新加
        
        st = time.time()
        print('Node Reflect %d' % (self.schedule.time + self.offset))
        #节点反思
        self.reflect()
        print('Node Reflect time: %.2f' % (time.time() - st))
        
        st = time.time()
        print('Node Vote %d' % (self.schedule.time + self.offset))
        #print('Node Vote')
        self.vote()
        print('Node Vote time: %.2f' % (time.time() - st))
        
        # self.schedule.add_timestep()
        # 手动递增时间步
        self.schedule.time += 1  # 增加时间步

        self.reset()

        print('-------------------')
        return 0
    