from ..utils.llm import stream_llm_response
import logging

logger = logging.getLogger(__name__)

name = "sora-video-director"
description = "Sora 2 视觉导演 Agent。专注于 Image-to-Video 任务，应用'视觉锚定'策略，生成能完美延续首帧风格的 Sora 专用提示词。"

input_schema = {
    "type": "object",
    "properties": {
        "prompt": {
            "type": "string",
            "description": "画面内容的动态描述（支持中文）。描述画面中发生了什么，而不是画面长什么样。",
        },
        "category": {
            "type": "string",
            "enum": ["scene", "storyboard"],
            "description": "生成内容的类型。默认为 scene。",
        },
        "context_characters": {
            "type": "array",
            "items": {"type": "object"},
            "description": "可选：角色列表。仅用于确保角色动作符合人设，不做外貌的强制重定义（因为外貌已在首帧中）。",
        },
        "style_preset": {
            "type": "string",
            "description": "可选：仅在通过纯文本生成时使用。如果上传了首帧图，请留空，Agent 会自动设置为'跟随参考图'。",
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

    # --- 1. Style Strategy: The "Chameleon" Logic ---
    # 如果用户没有指定风格，默认为“严格跟随首帧图片”
    user_style = kwargs.get("style_preset")
    
    if user_style:
        # 用户强制指定了风格（Text-to-Video 模式）
        style_instruction = f"(Visual Style & Tone): {user_style}"
        style_constraint = f"Enforce the style: {user_style}."
    else:
        # 默认模式（Image-to-Video 模式）：风格跟随
        style_instruction = "(Visual Style & Tone): STRICTLY MATCH THE PROVIDED START FRAME."
        style_constraint = "Do NOT invent a new art style. Isolate the texture, lighting, and rendering style from the Reference Image/Start Frame and extend it seamlessly. Maintain visual consistency."

    # --- 2. Context Formatting ---
    context_instruction = ""
    if context_characters:
        char_list_str = "\n".join(
            [
                f"- Name: {c.get('name', 'Unknown')}, Role: {c.get('description', '')}" # 简化了，去掉了视觉描述，因为首帧决定了视觉
                for c in context_characters
            ]
        )
        context_instruction += f"\n[Character Context]:\n{char_list_str}\n"

    # --- 3. System Prompt Construction ---
    system_prompt = f"""
    [Role]: You are the **Sora 2 Visual Director**.
    [Task]: Create a prompt for an **Image-to-Video** generation task. The user provides a Start Frame (image), and your job is to describe the **MOTION** and **EVENTS** that happen next, while ensuring the style remains locked to the image.

    [Core Logic - Visual Anchor]:
    1. **Style Adherence (风格跟随)**: {style_constraint}
    2. **Visual Translation (去文学化)**: Translate abstract story descriptions into concrete visual actions.
    3. **Fluid Narrative (流体叙事)**: Use natural connectors ("The camera pans...", "Suddenly..."). No timecodes.
    4. **Mandarin Lip-sync**: If dialogue is present, mark as `[Character] speaks in Mandarin Chinese` and include visual padding (hesitation, breath) for timing.

    {context_instruction}

    [Output Template]:
    Strictly follow this structure. Output ONLY the English prompt text.
    
    > **Prompt:**
    >
    > **{style_instruction}** The video must seamlessly animate the provided image. High fidelity to the source material's aesthetics.
    >
    > **(Scene Action):** [Describe the movement, lighting changes, and character acting based on the user's input. Focus on HOW things move, not WHAT they look like, as the look is already defined].
    >
    > **(Narrative Sequence):**
    > 1. [Action 1]
    > 2. [Action 2]
    > 3. [Transition/End]
    >
    > **(Technical Specs):** Maintain style consistency, high coherence, fluid motion from start frame.

    [Constraints]:
    1. **Language**: Output MUST be **ENGLISH**.
    2. **Focus**: Focus on **Dynamics** (movement), not **Statics** (appearance), because the appearance is provided by the image.
    """

    logger.info(
        f"--- [Backend Debug] Generate Request Prompt (sora-video-director) --- \n{system_prompt}\n----------------------------------------------------\n"
    )
    
    user_prompt = f"Raw Story Input: {prompt}"
    
    return stream_llm_response(client, model_name, system_prompt, user_prompt)