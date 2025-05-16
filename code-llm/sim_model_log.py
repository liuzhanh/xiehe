import networkx as nx
from sim_agent import FullAgent, LiteAgent
from casevo import ModelBase, TotLog
from thread_send import ThreadSend
from tqdm import tqdm
import time


class NetworkAnalyzer:
    """负责网络分析的类，支持累积交互分析"""

    def __init__(self, model):
        self.model = model
        self.G = nx.Graph()  # 创建无向图
        self.edge_weights = {}  # 存储边的权重，表示交互次数

        # 初始化图，添加所有节点
        for agent in self.model.agent_list:
            self.G.add_node(agent.unique_id)

            # 记录已处理的日志ID，避免重复处理
        self.processed_logs = set()

    def update_network(self):
        """
        更新网络，累积所有交互关系
        不会清除之前的边，而是累积新的交互
        """
        # 获取当前时间步
        current_time = self.model.schedule.time

        # 从TotLog中获取当前步骤的所有listen记录
        for agent in self.model.agent_list:
            agent_logs = TotLog.get_agent_log(agent.unique_id)
            if not agent_logs:
                continue

            print(f"Agent {agent.unique_id} 日志数量: {len(agent_logs)}")
            # 打印两条日志的格式，帮助调试
            if agent_logs:
                print(f"日志示例第一条: {agent_logs[0]}")
                print(f"日志示例第二条: {agent_logs[1]}")
            # 筛选当前时间步的listen记录
            listen_logs = [log for log in agent_logs
                           if log['ts'] == current_time and log['type'] == 'listen']

            for log in listen_logs:
                # 创建唯一的日志标识符
                log_id = f"{agent.unique_id}_{log.get('id', current_time)}_{log.get('item', {}).get('source', '')}"

                # 检查是否已处理过此日志
                if log_id in self.processed_logs:
                    continue

                if 'source' in log['item'] and log['item']['source'] != 'public' and isinstance(log['item']['source'],
                                                                                                (int, str)):
                    source_id = log['item']['source']
                    edge = (agent.unique_id, source_id)

                    # 更新边权重（交互次数）
                    if edge in self.edge_weights:
                        self.edge_weights[edge] += 1
                    else:
                        self.edge_weights[edge] = 1

                        # 更新图中的边
                    self.G.add_edge(agent.unique_id, source_id, weight=self.edge_weights[edge])

                    # 标记此日志为已处理
                    self.processed_logs.add(log_id)

    def calculate_betweenness_centrality(self):
        """计算并返回排序后的介数中心性"""
        # 检查图是否有节点和边
        if len(self.G.nodes()) == 0 or len(self.G.edges()) == 0:
            return []

            # 计算介数中心性，考虑边权重
        bc = nx.betweenness_centrality(self.G, weight='weight', normalized=True)

        # 按中心性值从大到小排序
        sorted_bc = sorted(bc.items(), key=lambda x: x[1], reverse=True)

        return sorted_bc

    def print_top_betweenness_centrality(self, top_n=20):
        """打印前N个介数中心性最大的智能体"""
        sorted_bc = self.calculate_betweenness_centrality()

        if not sorted_bc:
            print("\n没有足够的网络连接来计算介数中心性")
            return

            # 获取智能体名称（如果有）
        agent_names = {}
        for agent in self.model.agent_list:
            if isinstance(agent, FullAgent) and hasattr(agent,
                                                        'description') and agent.description and 'name' in agent.description:
                agent_names[agent.unique_id] = agent.description['name']
            elif hasattr(agent, 'name'):
                agent_names[agent.unique_id] = agent.name
            else:
                agent_names[agent.unique_id] = f"Agent-{agent.unique_id}"

        print(f"\n----- 前{top_n}个介数中心性最大的智能体（从大到小）- 累积交互网络分析 -----")
        print(f"当前时间步: {self.model.schedule.time + self.model.offset}, 累积交互边数: {len(self.G.edges())}")

        # 只打印前top_n个
        for i, (agent_id, centrality) in enumerate(sorted_bc[:top_n]):
            agent_type = "FullAgent" if any(isinstance(agent, FullAgent) and agent.unique_id == agent_id
                                            for agent in self.model.agent_list) else "LiteAgent"
            agent_name = agent_names.get(agent_id, f"未命名-{agent_id}")

            # 计算当前智能体的连接数
            connection_count = len(list(self.G.neighbors(agent_id)))

            print(f"{i + 1}. ID: {agent_id}, 名称: {agent_name}, 类型: {agent_type}, "
                  f"连接数: {connection_count}, 中心性: {centrality:.4f}")

    def get_network_stats(self):
        """获取网络统计信息"""
        if len(self.G.nodes()) == 0 or len(self.G.edges()) == 0:
            return {
                "nodes": 0,
                "edges": 0,
                "density": 0,
                "average_clustering": 0,
                "average_path_length": float('inf')
            }

        stats = {
            "nodes": len(self.G.nodes()),
            "edges": len(self.G.edges()),
            "density": nx.density(self.G),
            "average_clustering": nx.average_clustering(self.G, weight='weight'),
        }

        # 计算平均路径长度（如果图是连通的）
        try:
            stats["average_path_length"] = nx.average_shortest_path_length(self.G, weight='weight')
        except nx.NetworkXError:  # 图不连通
            largest_cc = max(nx.connected_components(self.G), key=len)
            largest_subgraph = self.G.subgraph(largest_cc)
            stats["average_path_length"] = nx.average_shortest_path_length(largest_subgraph, weight='weight')
            stats["largest_component_size"] = len(largest_cc)

        return stats


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

        # 设置Agent 含full和lite
        for cur_id in range(len(person_list)):
            cur_person = person_list[cur_id]
            if cur_person['type'] == 'lite':
                cur_agent = LiteAgent(cur_id, self, cur_person['args'])
            else:
                cur_agent = FullAgent(cur_id, self, cur_person['description'], None)
            self.add_agent(cur_agent, cur_id)

            # 创建网络分析器
        self.network_analyzer = NetworkAnalyzer(self)

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

        # 获取微博文本
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

        self.schedule.step()  # 新加

        st = time.time()
        print('Node Reflect %d' % (self.schedule.time + self.offset))
        # 节点反思
        self.reflect()
        print('Node Reflect time: %.2f' % (time.time() - st))

        st = time.time()
        print('Node Vote %d' % (self.schedule.time + self.offset))
        self.vote()
        print('Node Vote time: %.2f' % (time.time() - st))

        # 更新网络并计算介数中心性
        st = time.time()
        print('Network Analysis %d' % (self.schedule.time + self.offset))
        self.network_analyzer.update_network()

        # 打印前20个介数中心性最大的智能体
        self.network_analyzer.print_top_betweenness_centrality(top_n=20)

        # 每10步打印一次网络统计信息
        if (self.schedule.time + self.offset) % 10 == 0:
            stats = self.network_analyzer.get_network_stats()
            print("\n----- 累积网络统计信息 -----")
            print(f"节点数: {stats['nodes']}")
            print(f"边数: {stats['edges']}")
            print(f"网络密度: {stats['density']:.4f}")
            print(f"平均聚类系数: {stats['average_clustering']:.4f}")
            print(f"平均路径长度: {stats['average_path_length']:.4f}")
            if 'largest_component_size' in stats:
                print(f"最大连通分量大小: {stats['largest_component_size']}")

        print('Network Analysis time: %.2f' % (time.time() - st))

        # 手动递增时间步
        self.schedule.time += 1  # 增加时间步

        self.reset()

        print('-------------------')
        return 0