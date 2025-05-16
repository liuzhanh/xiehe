from huggingface_hub import snapshot_download  

# 正确的模型名称  
model_id = "BAAI/bge-large-zh-v1.5"  

print(f"开始下载模型: {model_id}...")  
snapshot_download(  
    repo_id="BAAI/bge-large-zh-v1.5",  
    local_dir=f"/home/LH/code-llm/models/{model_id.replace('/', '_')}",  # 保存到本地目录 
    local_dir_use_symlinks=False,  
    endpoint="https://hf-mirror.com"  # 使用镜像站点  
) 

print(f"模型下载完成，保存到: /home/LH/code-llm/models/{model_id.replace('/', '_')}")