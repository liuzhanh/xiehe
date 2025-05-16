from chromadb import Documents, EmbeddingFunction, Embeddings
from casevo import LLM_INTERFACE
import requests
import time
import json
import sys

# 添加本地包路径（根据实际环境调整）
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from model_client import ModelClient

# APIChatClient 通过 API 方式调用大模型（部署方式选择"api"时使用）
class APIChatClient:
    def __init__(self, model, api_key):
        self.client = ModelClient(model=model, api_key=api_key)
    
    def complete(self, prompt):
        class Response:
            def __init__(self, text):
                self.text = text
        return Response(self.client.generate(prompt))

# MyEmbedding 实现了 EmbeddingFunction 接口，封装了对大模型嵌入输出的分批处理
class MyEmbedding(EmbeddingFunction):
    def __init__(self, llm, tar_len):
        self.SEND_LEN = tar_len
        self.llm = llm
    
    def __call__(self, input: Documents) -> Embeddings:
        res_list = []
        cur_list = []
        for item in input:
            cur_list.append(item)
            if len(cur_list) >= self.SEND_LEN:
                res = self.llm.send_embedding(cur_list)
                res_list.extend(res)
                cur_list = []
        if cur_list:
            res = self.llm.send_embedding(cur_list)
            res_list.extend(res)
        return res_list

# OllamaLLM 实现了 LLM_INTERFACE 接口
#
# 构造函数参数说明：
#   tar_len          : 嵌入处理时每次发送的文本数量
#   api_key          : API调用密钥
#   chat_model       : 对话模型名称
#   embedding_model  : 嵌入模型名称
#   base_url         : 模型服务的 base url
#   deployment_method: 部署方式，"ollama" 表示调用 Ollama()，"api" 表示调用 APIChatClient
class OllamaLLM(LLM_INTERFACE):
    def __init__(self, tar_len, api_key, chat_model, embedding_model, base_url, deployment_method):
        self.embedding_len = tar_len
        self.api_key = api_key
        self.embedding_function = MyEmbedding(self, self.embedding_len)
        # 根据 deployment_method 选择调用方式
        if deployment_method.lower() == "ollama":
            # 使用 Ollama() 部署方式，通过 HTTP 请求调用部署好的大模型
            self.chat_client = Ollama(model=chat_model,
                                       base_url=base_url,
                                       temperature=0.3,
                                       request_timeout=60)
        elif deployment_method.lower() == "api":
            # 使用 APIChatClient 方式，通过 API 接口调用大模型（见上文注释）
            self.chat_client = APIChatClient(model=chat_model, api_key=self.api_key)
        else:
            raise ValueError("Unknown deployment method: must be 'ollama' or 'api'")
        
        self.embedding_client = OllamaEmbedding(model_name=embedding_model,
                                                base_url=base_url)
    
    def send_message(self, prompt, json_flag=False):
        resp = None
        for i in range(2):
            try:
                resp = self.chat_client.complete(prompt)
                break
            except Exception as e:
                print(e)
                print('Send Message Retry %d' % i)
        if resp:
            return resp.text
        else:
            raise Exception('send message error')
    
    def send_embedding(self, text_list):
        pass_embedding = None
        for i in range(2):
            try:
                pass_embedding = self.embedding_client.get_text_embedding_batch(text_list)
                break
            except Exception as e:
                print(e)
                print('Send Embedding Retry %d' % i)
        if pass_embedding:
            return pass_embedding
        else:
            raise Exception('Send embedding error')
    
    def get_lang_embedding(self):
        return self.embedding_function
