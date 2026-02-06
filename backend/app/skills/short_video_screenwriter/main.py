import json
import os
from ..utils.llm import stream_llm_response

name = "short-video-screenwriter"
description = "专业的短视频编剧引擎。作为一个虚拟创意总监，它负责规划剧本结构、风格和分镜，并输出指令指导生成完整的剧本内容。"

input_schema = {
    "type": "object",
    "properties": {
        "prompt": {
            "type": "string",
            "description": "用户输入的短视频或短剧的核心梗概。",
        },
        "existing_data": {
            "type": "object",
            "description": "可选的 JSON 对象，包含预定义的素材。",
        },
    },
    "required": ["title", "description"],
}


def main(
    prompt=None,
    title="未命名项目",
    description=None,
    client=None,
    model_name="gpt-4o",
    **kwargs,
):
    system_prompt = f"""
    [角色]: 你是一位经验丰富的短视频编剧和导演，擅长创作节奏紧凑、情感丰富的爆款短剧。
    [任务]: 根据用户输入，创作完整的剧本方案。
    [用户输入]：{description if description else prompt}
    
    [输出要求]:
    请按照严格的 JSON 格式输出，内容必须包裹在特定的标签中。你需要将输出分为五个部分：
    
    1. 元数据
    <|META|>
    ```json
    {{
        "meta": {{
            "project_title": "string (项目标题)",
            "core_premise": "基于用户输入的短视频或短剧的核心梗概"
        }}
    }}
    ```
    <|META_END|>

    2. 本章节大纲
    <|OUTLINE|>
    ```json
    {{
        "outline": {{
            "setup": "string (铺垫 - 中文)",
            "confrontation": "string (对抗 - 中文)",
            "resolution": "string (结局 - 中文)"
        }}
    }}
    ```
    <|OUTLINE_END|>
    
    3. 角色列表
    <|CHARACTERS|>
    ```json
    {{
        "characters": [
            {{
                "name": "string (角色名)",
                "role": "主角/反派/配角",
                "description": "string (中文详细描述)",
                "visual_prompt": ""
            }}
        ]
    }}
    ```
    <|CHARACTERS_END|>

    4. 场景列表，最多3个场景
    <|SCENES|>
    ```json
    {{
        "scenes": [
            {{
                "location_name": "string (地点名)",
                "mood": "string (氛围)",
                "visual_prompt": ""
            }}
        ]
    }}
    ```
    <|SCENES_END|>

    5. 分镜表，最多10个镜头
    <|STORYBOARD|>
    ```json
    {{
        "storyboard": [
            {{
                "shot_id": 1,
                "duration": "3s",
                "shot_type": "特写/广角/中景",
                "action": "string (中文动作描述)",
                "visual_prompt": ""
            }}
        ]
    }}
    ```
    <|STORYBOARD_END|>
    
    [重要约束]:
    1. **必须**严格遵守上述的标签结构。
    2. **语言**: 剧情、对白、描述必须使用 **中文**。
    3. **视觉提示词**: 所有 `visual_prompt` 字段必须保持为空字符串 `""`。不要生成任何英文提示词，这将在后续步骤中完成。
    4. **允许断章**: 只需根据用户输入进行创作，不要添加额外内容，不虚构不存在的结局，输入部分可能只是小节，非完整剧本。
    5. **JSON格式**: 确保标签内的 JSON 是合法且可解析的。
    """

    user_prompt = f"请开始创作《{title}》的剧本。"
    return stream_llm_response(client, model_name, system_prompt, user_prompt)
