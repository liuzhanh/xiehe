from chromadb import Documents, EmbeddingFunction, Embeddings
from casevo import LLM_INTERFACE
import requests
import time
import json
#from litellm import completion
import sys
sys.path.append("/home/susu/social_sim-agent-mesa/myenv/lib/python3.10/site-packages")
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from model_client import ModelClient

# API_KEY = 'sk-f900bdfa95dba3143546b63b73768e0e'

# BASE_URL = 'http://169.254.57.191:25000'
# BASE_URL = 'http://10.178.179.32:25000'
BASE_URL = "http://127.0.0.1:11434"

# CHAT_MODEL = 'lgkt/llama3-chinese-alpaca:latest'
# EMBEDDING_MODEL= 'znbang/bge:large-zh-v1.5-f16'

CHAT_MODEL = "deepseek-r1-250120"
EMBEDDING_MODEL = "quentinz/bge-large-zh-v1.5:latest"


# Add this before OllamaLLM
class APIChatClient:
    def __init__(self, model, api_key):
        self.client = ModelClient(model=model, api_key=api_key)
    
    def complete(self, prompt):
        class Response:
            def __init__(self, text):
                self.text = text
        return Response(self.client.generate(prompt))

class MyEmbedding(EmbeddingFunction):
    def __init__(self,llm, tar_len):
        #super.__init__()
        self.SEND_LEN = tar_len
        # self.SEND_LEN = int(tar_len)  #强制转化为整数

        self.llm = llm
    
    def __call__(self, input: Documents) -> Embeddings:
        # embed the documents somehow
        res_list = []
        cur_list = []
        for item in input:
            cur_list.append(item)
            if len(cur_list) >= self.SEND_LEN:
                res = self.llm.send_embedding(cur_list)
                res_list.extend(res)
                cur_list = []
        if len(cur_list) > 0:
            res = self.llm.send_embedding(cur_list)
            res_list.extend(res)

        return res_list


class OllamaLLM(LLM_INTERFACE):
    def __init__(self, tar_len,api_key):
        
        self.embedding_len = tar_len

        self.api_key=api_key          #保存api_key
        
        self.embedding_function = MyEmbedding(self, self.embedding_len)
        # self.chat_client = Ollama(model=CHAT_MODEL, 
        #                           base_url=BASE_URL, 
        #                           temperature=0.3,
        #                           request_timeout=60)
        self.chat_client = APIChatClient(model=CHAT_MODEL, api_key=self.api_key)
        self.embedding_client = OllamaEmbedding(model_name=EMBEDDING_MODEL,
                                                base_url=BASE_URL)
    
    def send_message(self, prompt, json_flag=False):
        #print(prompt)
        resp = None
        for i in range(2):
            try:
                # resp = self.chat_client.complete(prompt)
                resp = self.chat_client.complete(prompt)
                break
            except Exception as e:
                print(e)
                print('Send Message Retry %d' % i)
                #time.sleep(1)
        #print(resp.text)
        #print('-----------')
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
                #time.sleep(1)

        if pass_embedding:
            return pass_embedding
        else:
            raise Exception('Send embedding error')
        #print(response)
        
    def get_lang_embedding(self):
        
        return self.embedding_function