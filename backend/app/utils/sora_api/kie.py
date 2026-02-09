import json
from app.utils.http_client import request as http_request
from typing import Any, Dict, List
from .base import Base
from app.utils.image_utils import to_base64

class Kie(Base):
    """
    Kie AI (Sora 2 Image-to-Video) Formatter
    API 文档: Kie AI Sora 2 Image-to-Video
    架构: 原生异步轮询 (Create -> TaskID -> Poll)
    """
    name = "Kie"
    base_url_keyword = "https://api.kie.ai/api/v1"

    def create(self, base_url: str, apikey: str, model: str, prompt: str, seconds: int, size: str, watermark: bool, images: List[Any]) -> str:
        """
        提交图生视频任务
        """
        self.set_auth(base_url, apikey)

        # 1. 构造请求 URL
        api_url = f"{self._base_url}/jobs/createTask"

        # 2. 参数处理
        
        # 2.1 图片处理 (Required)
        if not images:
            raise Exception("Kie image-to-video model requires at least one image.")
        
        # API 文档要求 image_urls 为数组，且通常需要公网 URL
        # 取第一张图片
        target_image_url = images[0]

        # 2.2 时长映射 (Default 15s)
        # 文档支持 "10" 或 "15"
        n_frames = "15" # 默认为 15s
        if seconds:
            try:
                sec_val = int(seconds)
                if sec_val <= 10:
                    n_frames = "10"
            except ValueError:
                pass

        # 2.3 尺寸映射
        # 文档支持 "landscape" (默认) 或 "portrait"
        aspect_ratio = "landscape"
        if size and ("9:16" in size or "portrait" in size.lower() or "vertical" in size.lower()):
            aspect_ratio = "portrait"

        # 2.4 模型默认值 (针对 Image-to-Video)
        target_model = "sora-2-image-to-video-stable"

        # 3. 构造 Payload
        payload = {
            "model": target_model,
            "input": {
                "prompt": prompt,
                "image_urls": [to_base64(target_image_url)], # 注意：文档要求是数组格式
                "aspect_ratio": aspect_ratio,
                "n_frames": n_frames,
                "upload_method": "s3"
            }
        }

        # 4. 发送创建请求
        try:
            response = http_request("POST", api_url, headers=self._headers, json=payload, timeout=30)
            response.raise_for_status()
            res_json = response.json()
            
            if res_json.get("code") != 200:
                raise Exception(f"Kie API Error: {res_json.get('message')}")
            
            task_id = res_json.get("data", {}).get("taskId")
            if not task_id:
                raise Exception("Failed to retrieve taskId from Kie response")
                
            return task_id

        except Exception as e:
            raise Exception(f"Kie Task Creation Failed: {str(e)}")

    def _query_status(self, task_id: str) -> Dict[str, Any]:
        """
        查询任务状态
        """
        api_url = f"{self._base_url}/jobs/recordInfo"
        
        try:
            response = http_request(
                "GET",
                api_url,
                headers=self._headers,
                params={"taskId": task_id},
                timeout=30,
            )
            response.raise_for_status()
            res_json = response.json()
            
            # API 返回非 200
            if res_json.get("code") != 200:
                return {
                    "status": "failed",
                    "fail_reason": res_json.get("message", "Unknown error"),
                    "progress": 0
                }

            data = res_json.get("data", {})
            state = data.get("state")
            
            # 状态映射
            # Kie States: waiting, queuing, generating, success, fail
            
            if state == "success":
                # 解析 resultJson (它是字符串化的 JSON)
                video_url = ""
                try:
                    result_str = data.get("resultJson")
                    if result_str:
                        result_obj = json.loads(result_str)
                        urls = result_obj.get("resultUrls", [])
                        if urls:
                            video_url = urls[0]
                except json.JSONDecodeError:
                    pass

                return {
                    "status": "completed",
                    "progress": 100,
                    "video_url": video_url,
                    "raw": data
                }
            
            elif state == "fail":
                return {
                    "status": "failed",
                    "fail_reason": data.get("failMsg") or "Generation failed",
                    "progress": 0,
                    "raw": data
                }
            
            else:
                # waiting, queuing, generating -> processing
                return {
                    "status": "processing",
                    "progress": 50, # 无法获取精确进度，返回 50
                    "raw": data
                }

        except Exception as e:
            return {
                "status": "failed",
                "fail_reason": f"Network or Parse Error: {str(e)}",
                "progress": 0
            }
