from chromadb import Documents, EmbeddingFunction, Embeddings  
from casevo import LLM_INTERFACE  
import time  
from llama_index.llms.ollama import Ollama  
from llama_index.embeddings.ollama import OllamaEmbedding  
from openai import OpenAI  
import numpy as np  
from sentence_transformers import SentenceTransformer   

VLLM_BASE_URL = "http://localhost:3000/"  
BASE_URL = "http://localhost:11434/"  

CHAT_MODEL = 'deepseek-r1:1.5b' #'qwen2.5:72b'
  
EMBEDDING_MODEL_TOKEN_MAX = 512  

# 加载 SentenceTransformer 模型  
sentence_transformer = SentenceTransformer('/home/LH/code-llm/models/BAAI_bge-large-zh-v1.5')  

class SentenceTransformerEmbedding(EmbeddingFunction):  
    """使用 SentenceTransformer 的嵌入函数"""  
    
    def __init__(self, model_path, token_max=512):  
        self.model = SentenceTransformer(model_path)  
        self.token_max = token_max  
    
    def __call__(self, input: Documents) -> Embeddings:  
        """  
        为每个输入文档生成一个嵌入向量。  
        如果文档太长，会分割成段落并取平均嵌入。  
        """  
        result_embeddings = []  
        
        for document in input:  
            # 处理单个文档  
            document_paragraphs = []  
            
            if len(document) > self.token_max:  
                # 按句号分割文本  
                paragraphs = document.split('。')  
                temp_paragraph = ""  
                for para in paragraphs:  
                    if len(temp_paragraph) + len(para) + 1 <= self.token_max:  # +1 考虑句号  
                        if temp_paragraph:  
                            temp_paragraph += "。" + para  
                        else:  
                            temp_paragraph = para  
                    else:  
                        if temp_paragraph:  
                            document_paragraphs.append(temp_paragraph)  
                        temp_paragraph = para  
                if temp_paragraph:  
                    document_paragraphs.append(temp_paragraph)  
            else:  
                document_paragraphs.append(document)  
            
            # 获取文档的所有段落的嵌入  
            if document_paragraphs:  
                # 使用 SentenceTransformer 生成嵌入  
                paragraphs_embeddings = self.model.encode(document_paragraphs)  
                
                # 如果有多个段落嵌入，计算平均值  
                if len(paragraphs_embeddings) > 1:  
                    avg_embedding = np.mean(paragraphs_embeddings, axis=0)  
                    result_embeddings.append(avg_embedding.tolist())  
                else:  
                    result_embeddings.append(paragraphs_embeddings[0].tolist())  
            else:  
                # 如果没有段落，添加一个零向量  
                embedding_dim = 1024  # BGE-large 的维度通常是 1024  
                result_embeddings.append([0.0] * embedding_dim)  
        
        return result_embeddings  


class MyEmbedding(EmbeddingFunction):  
    """  
    原始的 MyEmbedding 类，修改为使用 SentenceTransformer  
    """  
    def __init__(self, llm, tar_len):  
        self.SEND_LEN = tar_len  
        self.llm = llm  
    
    def __call__(self, input: Documents) -> Embeddings:  
        """  
        修改为使用 SentenceTransformer，确保每个文档只返回一个嵌入  
        """  
        # 直接调用 SentenceTransformerEmbedding 类  
        st_embedding = SentenceTransformerEmbedding('/home/LH/code-llm/models/BAAI_bge-large-zh-v1.5', EMBEDDING_MODEL_TOKEN_MAX)  
        return st_embedding(input)  


class OllamaLLM(LLM_INTERFACE):  
    def __init__(self, tar_len, vllm_flag=False):  
        self.llm = OpenAI(  
            api_key='cuc-fwj',  
            base_url=VLLM_BASE_URL,  
        )  
        # 使用 SentenceTransformerEmbedding 作为嵌入函数  
        self.embedding_function = SentenceTransformerEmbedding('/home/LH/code-llm/models/BAAI_bge-large-zh-v1.5')  
        
        self.chat_client = Ollama(model=CHAT_MODEL,  
                                base_url=BASE_URL,   
                                temperature=0.3,  
                                request_timeout=60)  
        
        # 默认情况下不再使用 Ollama 嵌入  
        # self.embedding_client = OllamaEmbedding(model_name=EMBEDDING_MODEL, base_url=BASE_URL)  
        
        self.vllm_flag = vllm_flag  
    
    def send_message_vllm(self, prompt):  
        if len(prompt) > 30000:  
            print("send_message_vllm:", len(prompt), prompt[:20])  
            prompt = prompt[-30000:]  
        outputs = self.llm.chat.completions.create(  
            model=VLLM_MODEL,  
            messages=[  
                {"role": "user", "content": prompt},  
            ]  
        )  
        if outputs:  
            return outputs.choices[0].message.content  
        else:  
            raise Exception('send message error')  

    def send_message(self, prompt, json_flag=False):  
        resp = None  
        i = -1  
        while True:  
            i += 1  
            try:  
                if self.vllm_flag:  
                    resp = self.send_message_vllm(prompt)  
                else:  
                    resp = self.chat_client.complete(prompt)  
                break  
            except Exception as e:  
                print(e)  
                print('Send Message Retry %d' % i)  
                time.sleep(1)  
        if resp:  
            if self.vllm_flag:  
                return resp  
            return resp.text  
        else:  
            raise Exception('send message error')  

    def send_embedding(self, text_list):  
        """  
        使用 SentenceTransformer 生成嵌入向量  
        """  
        try:  
            # 使用 SentenceTransformer 计算嵌入  
            embeddings = sentence_transformer.encode(text_list)  
            # 确保返回列表格式  
            return embeddings.tolist()  
        except Exception as e:  
            print(f"【send_embedding】Exception with SentenceTransformer: {e}")  
            # 返回空列表而不是抛出异常  
            print('【send_embedding】returning empty embeddings')  
            return []  
        
    def get_lang_embedding(self):  
        return self.embedding_function


#from chromadb import Documents, EmbeddingFunction, Embeddings
#from casevo import LLM_INTERFACE
#import time
#from llama_index.llms.ollama import Ollama
#from llama_index.embeddings.ollama import OllamaEmbedding
#from openai import OpenAI
#
#from sentence_transformers import SentenceTransformer 
#
#VLLM_BASE_URL = "http://localhost:3000/"
#BASE_URL = "http://localhost:11434/"
#
##VLLM_MODEL = 'qwen32-cuc'
#CHAT_MODEL = 'qwen2.5:72b'
#EMBEDDING_MODEL = 'znbang/bge:large-zh-v1.5-f16'
#VLLM_MODEL = SentenceTransformer('/home/LH/code-llm/models/BAAI_bge-large-zh-v1.5')
##EMBEDDING_MODEL = 'BAAI_bge-large-zh-v1.5'
#EMBEDDING_MODEL_TOKEN_MAX = 512
#
#
#class MyEmbedding(EmbeddingFunction):
#    def __init__(self, llm, tar_len):
#        # super.__init__()
#        self.SEND_LEN = tar_len
#
#        self.llm = llm
#    
#    def __call__(self, input: Documents) -> Embeddings:
#        # embed the documents somehow
#        res_list = []
#        cur_list = []
#        for item in input:
#            if len(item) > EMBEDDING_MODEL_TOKEN_MAX:
#                # 按句号分割文本
#                paragraphs = item.split('。')
#                temp_paragraph = ""
#                for para in paragraphs:
#                    if len(temp_paragraph) + len(para) + 1 <= 512:  # +1 考虑句号
#                        if temp_paragraph:
#                            temp_paragraph += "。" + para
#                        else:
#                            temp_paragraph = para
#                    else:
#                        if temp_paragraph:
#                            cur_list.append(temp_paragraph)
#                        temp_paragraph = para
#                if temp_paragraph:
#                    cur_list.append(temp_paragraph)
#            else:
#                cur_list.append(item)
#            
#            if len(cur_list) >= self.SEND_LEN:
#                res = self.llm.send_embedding(cur_list)
#                if res:
#                    res_list.extend(res)
#                cur_list = []
#
#        if len(cur_list) > 0:
#            res = self.llm.send_embedding(cur_list)
#            if res:
#                res_list.extend(res)
#
#        return res_list
#
#
#class OllamaLLM(LLM_INTERFACE):
#    def __init__(self, tar_len, vllm_flag=False):
#        self.llm = OpenAI(
#            api_key='cuc-fwj',
#            base_url=VLLM_BASE_URL,
#        )
#        self.embedding_function = MyEmbedding(self, tar_len)
#        self.chat_client = Ollama(model=CHAT_MODEL,
#                                    base_url=BASE_URL, 
#                                    temperature=0.3,
#                                    request_timeout=60)
#        self.embedding_client = OllamaEmbedding(model_name=EMBEDDING_MODEL,
#                                                base_url=BASE_URL)
#        self.vllm_flag = vllm_flag
#    
#    def send_message_vllm(self, prompt):
#        if len(prompt) > 30000:
#            print("send_message_vllm:", len(prompt), prompt[:20])
#            prompt = prompt[-30000:]
#        outputs = self.llm.chat.completions.create(
#            model=VLLM_MODEL,
#            messages=[
#                {"role": "user", "content": prompt},
#            ]
#        )
#        if outputs:
#            return outputs.choices[0].message.content
#        else:
#            raise Exception('send message error')
#
#    def send_message(self, prompt, json_flag=False):
#        resp = None
#        i = -1
#        while True:
#            i += 1
#            try:
#                if self.vllm_flag:
#                    resp = self.send_message_vllm(prompt)
#                else:
#                    resp = self.chat_client.complete(prompt)
#                break
#            except Exception as e:
#                print(e)
#                print('Send Message Retry %d' % i)
#                time.sleep(1)
#        if resp:
#            if self.vllm_flag:
#                return resp
#            return resp.text
#        else:
#            raise Exception('send message error')
#
#    def send_embedding(self, text_list):
#        
#        pass_embedding = None
#        i = -1
#        while True:
#            i += 1
#            try:
#                pass_embedding = self.embedding_client.get_text_embedding_batch(text_list)
#                break
#            except Exception as e:
#                print(f"【send_embedding】Exception occurred: {e}")
#                print(f"Attempting to get embeddings for {text_list} (try {i+1})")
#                print(f'【send_embedding】Send Embedding Retry {i}')
#                time.sleep(1)
#
#        if pass_embedding:
#            return pass_embedding
#        else:
#            print(text_list, pass_embedding)
#            print('【send_embedding】raise Exception: Send embedding error')
#            return []
#        
#    def get_lang_embedding(self):
#        return self.embedding_function
