from chromadb import Documents, EmbeddingFunction, Embeddings
from casevo import LLM_INTERFACE
from cache import RequestCache
import requests
import time
import json

#API_KEY = 'sk-f900bdfa95dba3143546b63b73768e0e'

URL = 'https://api.baichuan-ai.com/v1/chat/completions'

EMBEDDING_URL = 'http://api.baichuan-ai.com/v1/embeddings'


class BaichuanEmbedding(EmbeddingFunction):
    def __init__(self,llm, tar_len):
        #super.__init__()
        self.SEND_LEN = tar_len
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


stop_words = ['政府','人民代表']

def filter_content(content):
    tmp_content = content
    for word in stop_words:
        tmp_content = tmp_content.replace(word, '')
    return tmp_content


class BaichuanLLM(LLM_INTERFACE):
    def __init__(self, tar_key, tar_len, cache_dir=None):
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + tar_key
        }
        self.embedding_len = tar_len
        self.embedding_function = BaichuanEmbedding(self, self.embedding_len)
        if cache_dir:
            self.cache = RequestCache(cache_dir)
        else:
            self.cache = None
    def send_message(self, prompt, json_flag=False):
        #print('send message')
        
        prompt = filter_content(prompt)
        
        if self.cache:
            tmp_content = self.cache.get_request_cache(prompt)
            if tmp_content:
                print('cache hit!')
                #print(prompt)
                #print(tmp_content)            
                return tmp_content
    
        data = {
            'model': 'Baichuan4-Air',
            'messages': [{'role':'user','content':prompt}],
            'temperature': 0.6,
            'top_p': 0.8,
            'max_tokens': 2048,
            'with_search_enhance': False
        }
        #print(prompt)
        response = requests.post(URL, headers=self.headers, json=data)
        while response.status_code == 429:
            print('API rate limit exceeded, waiting 10 seconds...')
            time.sleep(5)
            response = requests.post(URL, headers=self.headers, json=data)
        if response.status_code == 200:
            result = json.loads(response.text)
            add_flag = False
            
            if result['choices'][0]['finish_reason'] == 'content_filter':
                print('Content filtered, retrying...')
                print(prompt)
                print(result['choices'][0]['message']['content'].strip())
                print('---------------')
                
                time.sleep(5)

                data['model'] = 'Baichuan4-Turbo'

                response = requests.post(URL, headers=self.headers, json=data)
                result = json.loads(response.text)
                if result['choices'][0]['finish_reason'] == 'content_filter':
                    print('Content filtered Again, retrying...')
                    raise Exception("Content filtered Again Error")
                else:
                    add_flag = True

            else:
                add_flag = True
                
            tmp_content = result['choices'][0]['message']['content'].strip()
            #time.sleep(5)
            #print('finish')
            #print(tmp_content)
            if self.cache and add_flag:
                self.cache.add_request_cache(prompt, tmp_content)
                   
            return tmp_content
        else:
            #print('error')
            return None

    def send_embedding(self, text_list):
        data = {
            'model': 'Baichuan-Text-Embedding',
            'input': text_list
        }
        response = requests.post(EMBEDDING_URL, headers=self.headers, json=data)
        #print(response)
        while response.status_code == 429:
            print('API rate limit exceeded, waiting 10 seconds...')
            time.sleep(5)
            response = requests.post(EMBEDDING_URL, headers=self.headers, json=data)
        if response.status_code == 200:
            result = json.loads(response.text)
            return [item['embedding'] for item in result['data']]
        else:
            return None
    
    def get_lang_embedding(self):
        
        return self.embedding_function