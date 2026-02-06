import os
from ..utils.llm import stream_llm_response

name = "short-video-storyboard-maker"
description = "根据用户输入的剧本或梗概，自动拆分并生成分镜列表。"

input_schema = {
    "type": "object",
    "properties": {
        "prompt": {
            "type": "string",
            "description": "用户输入的剧情片段或梗概。",
        },
    },
    "required": ["prompt"],
}

def main(
    title=None,
    description=None,
    prompt=None,
    client=None,
    storyboard_count=5,
    shot_per_storyboard=6,
    model_name="gpt-4o",
):
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    knowledge_path = os.path.join(base_path, "knowledge")

    prompt_template = ""
    template_file = "storyboard_prompt.md"

    template_path = os.path.join(knowledge_path, template_file)
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()
    else:
        prompt_template = "暂无"

    system_prompt = f"""
    [角色]: 你是一位专业的分镜师。
    [任务]: 用户输入剧情片段或梗概，其中会包含场景和角色，将用户的剧本或梗概拆分为一系列分镜和分镜内的细分切片。
    [要求]:
    1. 基于你对镜头的理解，分镜类型可以是：全景、中景、近景、特写、大特写等，且时间码必须连续。
    2. 必要时允许包含人物心理、对话和场景细节描述。
    3. 严格按照以下格式输出：
    <|STORYBOARD|>
    ```json
    {{
        "storyboard": [
            {{
                "shot_id": 1,
                "duration": "15s",
                "shot_type": "特写/广角/中景",
                "action": "string (中文动作描述)",
                "visual_prompt": "{prompt_template}"
            }}
        ]
    }}
    ```
    <|STORYBOARD_END|>

    [重要约束]:
    1. **必须**将故事细化为**至少{storyboard_count}个**分镜，每个分镜控制在15秒以内，每个分镜内**至少切分{shot_per_storyboard}个**切片(shot)，至多{shot_per_storyboard + 2}个。
    2. **时间合理性**: 如果出现人物对话，请确保规定时间内可以完成，否则请选择精简对话或增加分镜时长，最长不超过15秒。
    3. **过渡镜头** 始终保留第一秒和最后一秒作为过渡镜头，不做任何对话或复杂动作。
    4. **保留占位符**用户输入中可能包含 {{char_id}} 或 {{scene_id}} 格式的引用，请在输出中正确使用,如果没有，请直接显示人名或场景。
    5. **必须**严格遵守上述的标签结构。
    6. **语言**: 剧情、对白、描述必须使用 **中文**。
    7. **JSON格式**: 确保标签内的 JSON 是合法且可解析的。
    """

    user_prompt = f"用户的剧本名称为：{title}，简介：{description}，请开始拆分剧本：{prompt}。"
    return stream_llm_response(client, model_name, system_prompt, user_prompt)

