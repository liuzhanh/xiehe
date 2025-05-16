from casevo import AgentBase, TotLog, BaseStep, ScoreStep
import mesa
import numpy as np

import threading
import random

class ScoreTalkStep(ScoreStep):
    def pre_process(self, input, agent=None, model=None):
        cur_input = input['input']
        cur_input['content'] = input['last_response']

        return cur_input
    
#FullAgent类
class FullAgent(AgentBase):
    def __init__(self, unique_id, model, description, context):
        #初始化
        super().__init__(unique_id, model, description, context)

        #加载Prompt
        talk_prompt = self.model.prompt_factory.get_template("talk.md")
        score_prompt = self.model.prompt_factory.get_template("score.md")
        vote_prompt = self.model.prompt_factory.get_template("vote.md")
        reflect_prompt=self.model.prompt_factory.get_template("reflect.md")

        

        #设置CoT
        #issue_step = BaseStep(0, issue_prompt)
        talk_step = BaseStep(0, talk_prompt)
        score_step = ScoreTalkStep(1, score_prompt)
        vote_step = ScoreStep(2, vote_prompt)
        refelct_step=BaseStep(3,reflect_prompt)

        
        
        chain_dict = {
            'talk': [talk_step, score_step],
            'vote': [vote_step],
            'reflect':[refelct_step]

        }
        self.setup_chain(chain_dict)
        
        self.memory.long_memory = description['opinion']
            
        self.lock = threading.Lock()
    
    def listen(self, content, attitude, source):
        #self.lock.acquire()
        self.memory.add_short_memory(source.unique_id, self.component_id, 'listen', content)

        log_item = {
            'source': source.unique_id,
            'content': content
        }

        TotLog.add_agent_log(self.model.schedule.time,'listen', log_item, self.unique_id)

    # 生成对话内容
    def generate_talk(self):
        #self.lock.acquire()
        input_item = {
            'long_memory': self.memory.get_long_memory()
        }
        self.chains['talk'].set_input(input_item)
        #运行CoT
        self.chains['talk'].run_step()
        #处理输出
        self.talk_content = self.chains['talk'].get_output()['input']['content']
        self.talk_attitude = float(self.chains['talk'].get_output()['score'])

        #记录log
        log_item = {
            'content': self.talk_content,
            'attitude': self.talk_attitude
        }
        #self.log.add_log(self.model.schedule.time,'talk', log_item)
        TotLog.add_agent_log(self.model.schedule.time,'talk_content', log_item, self.unique_id)

        #print('talk %d --> %d mid' % (self.unique_id, tar_agent.unique_id))
        #print(self.talk_content)
        #目标Agent听取内容
        #self.lock.release()

        #tar_agent.listen(self.talk_content, self.component_id)
        
        self.model.pbar.update(1)
    def reflect(self):
        """
        执行反思过程。

        该方法在 agent 的执行周期结束后调用，用于反思其记忆中的长期意见。
        它通过比较反思前后的意见变化来记录和学习。

        参数:
        无

        返回值:
        无
        """
        self.lock.acquire()
        ori_opinion = self.memory.get_long_memory()
        #执行反思
        self.memory.reflect_memory()
        
        #记录Log
        log_item = {
            'ori_opinion': ori_opinion,
            'new_opinion': self.memory.get_long_memory(),
            'last_id': self.memory.last_id 
        }
        #self.log.add_log(self.model.schedule.time - 1,'reflect', log_item)
        TotLog.add_agent_log(self.model.schedule.time,'reflect', log_item, self.unique_id)
        
        self.model.pbar.update(1)
        self.lock.release()

    def vote(self):
        """
        执行投票过程。
        """
        print(f"FullAgent {self.unique_id} casting vote.")
        self.lock.acquire()
        input_item = {
            'long_memory': self.memory.get_long_memory()
        }
        self.chains['vote'].set_input(input_item)
        self.chains['vote'].run_step()
        vote_result = self.chains['vote'].get_output()['score']
        log_item = {
            'attitude': vote_result
        }
        #self.log.add_log(self.model.schedule.time - 1,'vote', vote_result)
        TotLog.add_agent_log(self.model.schedule.time,'vote', log_item, self.unique_id)

        self.model.pbar.update(1)
        self.lock.release()
    
    def reset(self):
        self.talk_content = None
        self.talk_attitude = None

    # def step(self):coding平台原版***********************************************
    #     neighbors = self.model.grid.get_neighbors(self.unique_id, include_center=False)
    #     for neighbor in neighbors:
    #         if  (neighbor) == FullAgent:
    #             if self.random.random() < 0.5:
    #                 neighbor.listen(self.talk_content, self.talk_attitude, self)
    #         else:
    #             neighbor.listen(self.talk_content, self.talk_attitude, self)
    def step(self):#修改后***********************************************************

        # 交互逻辑：与邻居交互
        neighbors = self.model.grid.get_neighbors(self.pos, include_center=False)
        if neighbors:
            neighbor = random.choice(neighbors)  # 随机选择一个邻居进行交互
            
            if type(neighbor) == LiteAgent:  # LiteAgent 与 FullAgent 交互
                print(f"FullAgent {self.unique_id} interacting with liteAgent {neighbor.unique_id}")
                full_agent_attitude=self.memory.get_long_memory()
                input_item={
                    'attitude':full_agent_attitude
                }
                self.chains['vote'].set_input(input_item)
                self.chains['vote'].run_step()
                new_attitude=self.chains['vote'].get_output()['score']
                print(f"FullAgent {self.unique_id} updates LiteAgent {neighbor.unique_id}'s attitude.")
                neighbor.listen(None, new_attitude,self)

            else:
                # FullAgent 之间的交互
                neighbor.listen(self.talk_content, self.talk_attitude, self)
                print(f"FullAgent {self.unique_id} interacting with FullAgent {neighbor.unique_id}")


          
class LiteAgent(mesa.Agent):
# class LiteAgent(AgentBase):

    def __init__(self, unique_id, model, args):
        super().__init__(unique_id, model)

        # lite_prompt =self.model.prompt_factory.get_template("lite_talk.md")
        # lite_talk_step=BaseStep(0,lite_prompt)
        self.attitude = args['attitude']
        self.ori_attitude = self.attitude
        
        self.difficulty = args['difficulty']
        self.will = args['will']

        self.listen_list = []

    def listen(self, content, attitude, source):
        # logging.debug(f"LiteAgent {self.unique_id} listens to Agent {source.unique_id} with attitude {attitude}")
        self.listen_list.append(attitude)
        log_item = {
            'source': source.unique_id,
            'attitude': attitude, 
        }
        TotLog.add_agent_log(self.model.schedule.time,'listen', log_item, self.unique_id)


    def clac_attitude(self):
        if len(self.listen_list) > 0:
            #原版：
            tar_len = len(self.listen_list)
            ori_attitude = self.attitude
            tot = self.attitude
            for i in range(tar_len):
                tot += self.listen_list[i]
                    
            update = self.difficulty * self.ori_attitude + (1.0 - self.difficulty) * (tot / (tar_len + 1)) 
            self.attitude = update

            # 记录Log
            log_item = {
                'ori_attitude':self.ori_attitude,
                'difficulty': self.difficulty,
                'last_attitude': ori_attitude,
                'new_attitude': update,
                'attitude_list': self.listen_list,
            }
            #self.log.add_log(self.model.schedule.time - 1,'reflect', log_item)
            TotLog.add_agent_log(self.model.schedule.time,'update', log_item, self.unique_id)
            self.listen_list = [] #清空听取列表


    def reflect(self):
        # self.clac_attitude()
        if len(self.listen_list) > 0:
            tar_len = len(self.listen_list)
            ori_attitude = self.attitude
            #tot = self.attitude
            tot = 0
            for i in range(tar_len):
                tot += self.listen_list[i]
                    
            #update = self.difficulty * self.ori_attitude + (1.0 - self.difficulty) * (tot / (tar_len + 1)) 
            update = self.difficulty * self.attitude + (1.0 - self.difficulty) * (tot / tar_len)
            self.attitude = update

            # logging.debug(f"LiteAgent {self.unique_id} reflected attitude from {ori_attitude} to {update}. Listen list: {self.listen_list}") 

            #记录Log
            log_item = {
                'ori_attitude':self.ori_attitude,
                'difficulty': self.difficulty,
                'last_attitude': ori_attitude,
                'new_attitude': update,
                'attitude_list': self.listen_list,
            }
            #self.log.add_log(self.model.schedule.time - 1,'reflect', log_item)
            TotLog.add_agent_log(self.model.schedule.time,'reflect', log_item, self.unique_id)
            self.listen_list = []
        #self.model.pbar.update(1)
        
    def vote(self):
        # logging.debug(f"LiteAgent {self.unique_id} casting vote with attitude: {self.attitude}")
        log_item = {
            'attitude': self.attitude
        }
        TotLog.add_agent_log(self.model.schedule.time,'vote', log_item, self.unique_id)
        #self.model.pbar.update(1)
    
    def reset(self):
        # logging.debug(f"LiteAgent {self.unique_id} reset its listen list.")

        self.listen_list = []
    
    def step(self):
        # logging.debug(f"LiteAgent {self.unique_id} is stepping with current attitude: {self.attitude}")
        self.clac_attitude()#更新态度
        neighbors = self.model.grid.get_neighbors(self.unique_id, include_center=False)
        for neighbor in neighbors:
            if type(neighbor) == LiteAgent:
                # if self.random.random() < self.will:
                neighbor.listen(None, self.attitude, self)
                print(f"LiteAgent {self.unique_id} interacting with liteAgent {neighbor.unique_id}")
        
            

       

                    
            

        
        
        
        
