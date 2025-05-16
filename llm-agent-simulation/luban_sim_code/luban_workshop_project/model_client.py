'''
Author: Junwen Yang
Date: 2025-02-18 12:37:10
LastEditors: Junwen Yang
LastEditTime: 2025-03-19 07:49:33
Description: Deepseek-R1满血版调用代码，使用火山引擎API
'''
import httpx
from volcenginesdkarkruntime import Ark
from typing import Optional, Union, Generator
import os

class ModelClient:
    def __init__(
        self,
        model: str = "deepseek-r1-250120",
        api_key: Optional[str] = os.environ.get("ARK_API_KEY"),
        ak: Optional[str] = None,
        sk: Optional[str] = None,
        timeout: int = 1800,
        max_retries: int = 3
    ):  
        self.model = model
        self.client = Ark(
            api_key=api_key,
            ak=ak,
            sk=sk,
            timeout=httpx.Timeout(timeout=timeout),
        )
        self.max_retries = max_retries

    def _handle_response(self, response: Union[dict, Generator]) -> str:
        content = ""
        for chunk in response:
            if not chunk.choices:
                continue

            content += chunk.choices[0].delta.content
                # print(chunk.choices[0].delta.content, end="")
        return content

    def generate(
        self,
        prompt: str,
        stream: bool = True,
        temperature: float = 0.3,
        max_tokens: int = 2000
    ) -> str:
        messages = [{"role": "user", "content": prompt}]
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    stream=stream,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return self._handle_response(response)
                # return response
            except (httpx.ConnectTimeout, httpx.ReadTimeout) as e:
                if attempt == self.max_retries - 1:
                    raise RuntimeError(f"API timeout after {self.max_retries} retries") from e
            except Exception as e:
                raise RuntimeError(f"API error: {str(e)}") from e
        return ""

if __name__ == "__main__":
    client = ModelClient(api_key=os.environ.get("ARK_API_KEY"), model="ep-20250217094500-4s2n9")
    content = client.generate("常见的十字花科植物有哪些？")
    print(content)