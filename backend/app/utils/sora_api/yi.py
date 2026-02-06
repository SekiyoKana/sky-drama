
import os
import re
import uuid
import json
import base64
import requests
from typing import Any, Dict, List
from .base import Base

class Yi(Base):
    """
    ApiYi (Sora 2) Formatter
    适配流式输出接口到轮询架构
    """
    name = "ApiYi"
    base_url_keyword = "https://api.apiyi.com/v1"
    
    # 用于缓存流式请求的最终结果，以适配 _query_status 的轮询机制
    # Key: task_id, Value: Result Dict
    _task_cache: Dict[str, Dict[str, Any]] = {}

    def create(self, base_url: str, apikey: str, model: str, prompt: str, seconds: int, size: str, watermark: bool, images: List[Any]) -> str:
        self.set_auth(base_url, apikey)
        
        # 1. 构造请求 URL
        # 注意：源文件写死为 api.apiyi.com，这里基于传入的 base_url 拼接
        api_url = f"{self._base_url}/chat/completions"
        
        # 2. 图片处理逻辑
        if not images:
            raise Exception("ApiYi requires at least one image.")
        
        image_path_or_url = images[0]
        image_url = ""

        if image_path_or_url.startswith(('http://', 'https://')):
            image_url = image_path_or_url
        else:
            if image_path_or_url.startswith('/'):
                image_url = f".{image_path_or_url}"
            # 本地文件转 Base64
            try:
                if os.path.exists(image_url):
                    with open(image_url, 'rb') as f:
                        image_data = base64.b64encode(f.read()).decode('utf-8')
                        ext = image_url.lower().split('.')[-1]
                        mime_type = f"image/{ext}" if ext in ['png', 'jpg', 'jpeg', 'gif', 'webp'] else "image/jpeg"
                        image_url = f"data:{mime_type};base64,{image_data}"
                else:
                    # 如果不是本地路径也不是http，假设用户传的就是base64或DataURI，直接透传
                    image_url = image_path_or_url
            except Exception as e:
                raise Exception(f"Image processing failed: {e}")

        # 3. 构造 Payload
        # 注意：Sora 2 API 似乎不接受 duration/seconds 参数，主要通过 model 控制 (如 hd, landscape)
        payload = {
            "model": model or "sora_video2",
            "stream": True,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        { "type": "text", "text": prompt },
                        { "type": "image_url", "image_url": { "url": image_url } }
                    ]
                }
            ]
        }

        # 4. 生成一个虚拟 Task ID
        task_id = str(uuid.uuid4())
        
        # 5. 执行流式请求并阻塞等待结果 (同步转伪异步)
        # 因为 API 是流式的，无法直接获得 ID 后去轮询，必须在这里读完流
        try:
            response = requests.post(api_url, headers=self._headers, json=payload, stream=True, timeout=600) # timeout 6000s from source
            response.raise_for_status()
            
            final_video_url = None
            error_message = None
            
            # 解析流式输出
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]
                        if data_str == '[DONE]':
                            break
                        try:
                            data_json = json.loads(data_str)
                            content = data_json.get('choices', [{}])[0].get('delta', {}).get('content', '')
                            
                            if content:
                                # 检查错误
                                if 'error' in content.lower() or '失败' in content:
                                    # 此时可能还没有换行，先暂存错误
                                    error_message = content.strip()
                                
                                # 提取视频链接
                                # 使用源文件中的正则
                                if '视频生成成功' in content:
                                    match = re.search(r'\[点击这里\]\((https?://[^\)]+)\)', content)
                                    if match:
                                        final_video_url = match.group(1)
                        except json.JSONDecodeError:
                            continue
            
            # 存入缓存
            if final_video_url:
                self._task_cache[task_id] = {
                    "status": "completed",
                    "video_url": final_video_url,
                    "progress": 100
                }
            else:
                self._task_cache[task_id] = {
                    "status": "failed",
                    "fail_reason": error_message or "Stream ended without URL",
                    "progress": 0
                }

        except Exception as e:
            self._task_cache[task_id] = {
                "status": "failed",
                "fail_reason": str(e),
                "progress": 0
            }

        return task_id

    def _query_status(self, task_id: str) -> Dict[str, Any]:
        # 从本地缓存读取结果
        result = self._task_cache.get(task_id)
        
        if not result:
            return {
                "status": "failed",
                "fail_reason": "Task ID not found in cache",
                "progress": 0
            }
            
        # 既然 create 已经阻塞完成了任务，这里直接返回结果
        return {
            "status": result["status"],
            "progress": result["progress"],
            "video_url": result.get("video_url"),
            "fail_reason": result.get("fail_reason"),
            "raw": result # 包含原始数据
        }