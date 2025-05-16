import mesa  
import networkx as nx  # 添加导入  
from casevo.memory import MemeoryFactory  
from casevo.prompt import PromptFactory  
from casevo.util.thread_send import ThreadSend  

class OrederTypeActivation(mesa.time.RandomActivationByType):  
    def add_timestemp(self):  
        self.time += 1  
        self.steps += 1  

#模型定义基类  
class ModelBase(mesa.Model):  
    def __init__(self, tar_graph, llm, context=None, prompt_path='./prompt/', memory_path=None, memory_num=10, reflect_file='reflect.txt', type_schedule=False, top_n_centrality=5):  
        super().__init__()  
        #设置网络  
        self.grid = mesa.space.NetworkGrid(tar_graph)  
    
        #Agent调度器  
        if type_schedule:  
            self.schedule = OrederTypeActivation(self)  
        else:  
            self.schedule = mesa.time.RandomActivation(self)  

        #上下文信息  
        self.context = context  
        
        #设置基座模型  
        self.llm = llm  

        #设置prompt工厂  
        self.prompt_factory = PromptFactory(prompt_path, self.llm)  
        
        #反思prompt  
        reflect_prompt = self.prompt_factory.get_template(reflect_file)  

        #设置memory工厂  
        self.memory_factory = MemeoryFactory(self.llm, memory_num, reflect_prompt, self, memory_path)  

        #初始化agent列表  
        self.agent_list = []  
        
        # 添加交互网络图  
        self.interaction_graph = nx.Graph()  
        
        # 设置用于输出中心性的顶点数量  
        self.top_n_centrality = top_n_centrality  
        
        # 用于进度条显示  
        self.pbar = None  
    
    def add_agent(self, tar_agent, node_id):  
        """  
        将一个新的代理添加到系统中。  

        此方法将代理添加到代理列表中，将其加入调度器，并将其放置在指定的节点上。  

        参数:  
        - tar_agent: 要添加的代理对象。  
        - node_id: 代理将被放置的节点ID。  
        """  
        # 将新代理添加到代理列表中  
        self.agent_list.append(tar_agent)  
        # 将代理添加到调度器中，以便它可以被调度和执行任务  
        self.schedule.add(tar_agent)  
        # 在网格中的指定节点上放置代理  
        self.grid.place_agent(tar_agent, node_id)  
        
        # 将节点添加到交互网络中  
        self.interaction_graph.add_node(tar_agent.unique_id)  
    
    def calculate_betweenness_centrality(self, n=20):  
        """  
        计算并输出前n个介数中心性最高的节点  
        
        参数:  
        - n: 要输出的节点数量，如果为None则使用默认值  
        """  
        if n is None:  
            n = self.top_n_centrality  
            
        # 如果图中节点数少于2个，无法计算中心性  
        if len(self.interaction_graph.nodes) < 2:  
            print("Network too small to calculate betweenness centrality.")  
            return  
            
        # 计算介数中心性  
        betweenness = nx.betweenness_centrality(self.interaction_graph)  
        
        # 按中心性值排序  
        sorted_betweenness = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)  
        
        # 输出前n个  
        print(f"\n--- Top {n} nodes by betweenness centrality ---")  
        for i, (node, centrality) in enumerate(sorted_betweenness[:n]):  
            print(f"Rank {i+1}: Node {node} - Betweenness Centrality: {centrality:.6f}")  
        print("-------------------------------------------\n")  
        
        return sorted_betweenness[:n]  
    
    def get_network_metrics(self):  
        """获取网络的各种指标"""  
        metrics = {  
            'nodes': len(self.interaction_graph.nodes()),  
            'edges': len(self.interaction_graph.edges()),  
            'density': nx.density(self.interaction_graph)  
        }  
        
        # 如果图足够大，计算其他指标  
        if len(self.interaction_graph.nodes) > 1:  
            try:  
                metrics['avg_clustering'] = nx.average_clustering(self.interaction_graph)  
                
                # 获取最大连通分量  
                if not nx.is_connected(self.interaction_graph):  
                    largest_cc = max(nx.connected_components(self.interaction_graph), key=len)  
                    largest_cc_subgraph = self.interaction_graph.subgraph(largest_cc)  
                    metrics['largest_cc_size'] = len(largest_cc)  
                    
                    if len(largest_cc) > 1:  
                        metrics['average_shortest_path'] = nx.average_shortest_path_length(largest_cc_subgraph)  
                else:  
                    metrics['largest_cc_size'] = len(self.interaction_graph.nodes)  
                    metrics['average_shortest_path'] = nx.average_shortest_path_length(self.interaction_graph)  
                    
            except Exception as e:  
                print(f"Error calculating some metrics: {e}")  
                
        return metrics  
    
    def step(self):  
        """  
        执行模拟步骤。  
        
        此方法推进模拟时间的一个步骤，并管理所有调度对象的更新。它不接受任何参数，也不返回任何有意义的值，  
        主要是为了触发模拟过程的推进。  
        
        Returns:  
            int: 始终返回0，作为步骤执行的结果指示。  
        """  
        self.schedule.step()  
        
        # 在每一步后计算并输出介数中心性  
        self.calculate_betweenness_centrality()  
        
        return 0