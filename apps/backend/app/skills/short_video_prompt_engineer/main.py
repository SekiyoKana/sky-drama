import os
from ..utils.llm import stream_llm_response
import logging

logger = logging.getLogger(__name__)

name = "short-video-prompt-engineer"
description = "专业的提示词工程师 Agent。它接收原始的自然语言描述（角色/场景/分镜）和目标模型名称，从知识库中检索该模型的特定文档，生成最优化的 AI 提示词。"

input_schema = {
    "type": "object",
    "properties": {
        "prompt": {
            "type": "string",
            "description": "角色、场景或分镜的原始描述文本（支持中文）。",
        },
        "category": {
            "type": "string",
            "enum": ["character", "scene", "storyboard"],
            "description": "生成内容的类型（角色/场景/分镜）。",
        },
        "context_characters": {
            "type": "array",
            "items": {"type": "object"},
            "description": "可选：当前项目中的所有角色列表 (id, name, description)。",
        },
        "context_scenes": {
            "type": "array",
            "items": {"type": "object"},
            "description": "可选：当前项目中的所有场景列表 (id, location_name, mood)。",
        },
        "style": {
            "type": "object",
            "items": { "type": "object" },
            "description": "可选：用户指定的生成风格",
        },
    },
    "required": ["prompt"],
}


def main(
    prompt=None,
    category="scene",
    context_characters=None,
    context_scenes=None,
    client=None,
    model_name="gpt-4o",
    **kwargs,
):
    if not prompt and "raw_text" in kwargs:
        prompt = kwargs["raw_text"]

    if not prompt:
        prompt = ""


    # --- Context Formatting ---
    context_instruction = ""

    if context_characters:
        char_list_str = "\n".join(
            [
                f"- ID: {c.get('id', 'N/A')}, Name: {c.get('name', '未知')}, Desc: {c.get('description', '')}"
                for c in context_characters
            ]
        )
        context_instruction += f"\n[可用角色列表]:\n{char_list_str}\n"

    if context_scenes:
        scene_list_str = "\n".join(
            [
                f"- ID: {s.get('id', 'N/A')}, Name: {s.get('location_name', '未知')}, Mood: {s.get('mood', '')}"
                for s in context_scenes
            ]
        )
        context_instruction += f"\n[可用场景列表]:\n{scene_list_str}\n"

    if context_instruction:
        context_instruction += """
    [引用规则]:
    1. 如果生成的提示词中涉及上述[可用角色列表]中的角色，**必须**使用 `{{char_ID}}` 的格式替换角色名称（例如：`{{char_1}}`）。
    2. 如果涉及[可用场景列表]中的场景，**必须**使用 `{{scene_ID}}` 的格式替换场景名称（例如：`{{scene_2}}`）。
    3. 仅对列表中的已知角色/场景使用此标签，未知角色或泛指不需替换。
    """

    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    knowledge_path = os.path.join(base_path, "knowledge")

    prompt_template = ""
    template_file = "scene_prompt.md"  # Default

    if category == "character":
        template_file = "role_prompt.md"
    elif category == "scene":
        template_file = "scene_prompt.md"
    elif category == "storyboard":
        template_file = "storyboard_prompt.md"

    template_path = os.path.join(knowledge_path, template_file)
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()
    else:
        prompt_template = "暂无"

    system_prompt = f"""
    [角色]: 专业的 AI 提示词工程师
    [任务]: 将用户的“原始描述”转化为适用于目标的的高质量中文提示词。
    [类别]: {category} (角色/场景/分镜)
    {context_instruction}
    [生成模板]:
    {prompt_template}

    [约束条件]:
    1. **语言**: 输出必须是纯 **中文 (Chinese)**。
    2. **结构**: 严格按照**[生成模板]**的结构返回，不得自由发挥。
    3. **定位清晰**： 根据“类别”生成对应的提示词，生成角色时不要带有背景，生成场景时不要带有角色，分镜则没有限制。
    4. **输出**: 仅返回最终的提示词，不要包含任何解释或 markdown 代码块。
    5. **特殊规则**：如果对象是storyboard，请至少返回6个分镜，上限为8个。
    """
    logger.info(
        f"--- [Backend Debug] Generate Request Prompt (short-video-prompt-engineer) --- \n{system_prompt}\n----------------------------------------------------\n"
    )
    user_prompt = f"原始描述: {prompt}"
    return stream_llm_response(client, model_name, system_prompt, user_prompt)
