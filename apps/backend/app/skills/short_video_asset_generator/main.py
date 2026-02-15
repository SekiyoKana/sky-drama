import os
import base64
import time
from app.db.session import SessionLocal
from app.models.project import Episode

name = "short-video-asset-generator"
description = "资产生成器。自动识别 Prompt 类型（角色/场景/分镜），加载本地视觉模板，并结合数据库中的 AI 配置调用生图接口。"

input_schema = {
    "type": "object",
    "properties": {
        "prompt": {
            "type": "string",
            "description": "具体的画面描述提示词 (英文最佳)。",
        },
        "episode_id": {
            "type": "integer",
            "description": "当前剧集的 ID，用于从数据库读取 AI 配置。",
        },
    },
    "required": ["prompt", "episode_id"],
}


def main(prompt, episode_id, client=None, model_name="gpt-4o", **kwargs):
    def generator():
        yield {"type": "status", "content": "🔍 Classifying prompt type..."}

        # --- 1. 自动识别类型 ---
        def classify_prompt(text):
            text = text.lower()
            role_keywords = ["character", "man", "woman", "face", "portrait", "person"]
            scene_keywords = ["room", "street", "landscape", "view", "background"]
            board_keywords = ["shot", "angle", "camera", "close-up", "wide"]

            score_role = sum(1 for k in role_keywords if k in text)
            score_scene = sum(1 for k in scene_keywords if k in text)
            score_board = sum(1 for k in board_keywords if k in text)

            if score_board >= score_role and score_board >= score_scene:
                return "storyboard"
            if score_role >= score_scene:
                return "role"
            return "scene"

        asset_type = classify_prompt(prompt)
        time.sleep(0.5)

        yield {"type": "status", "content": f"📁 Loading template for {asset_type}..."}

        # --- 2. 加载本地模板 ---
        current_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(current_dir, "assets")
        template_path = os.path.join(assets_dir, f"{asset_type}.png")

        template_b64 = None
        if os.path.exists(template_path):
            with open(template_path, "rb") as image_file:
                template_b64 = base64.b64encode(image_file.read()).decode("utf-8")

        yield {"type": "status", "content": "⚙️ Fetching AI configuration..."}

        # --- 3. 读取数据库配置 ---
        db = SessionLocal()
        try:
            episode = db.query(Episode).filter(Episode.id == episode_id).first()
            if not episode or episode.ai_config is None:
                return "[Error] Episode config not found."
            img_config = episode.ai_config.get("image", {})
            target_model = img_config.get("model", "default-model")
        finally:
            db.close()

        yield {
            "type": "status",
            "content": f"🎨 Generating image with {target_model}...",
        }

        # --- 4. 模拟请求 ---
        time.sleep(2)
        mock_url = f"https://placehold.co/1024x576/1a1a1a/FFF?text={asset_type.upper()}+Generated"

        result_msg = f"""
        [Asset Generated]
        - **Type**: {asset_type.upper()}
        - **Model**: {target_model}
        - **Result**: ![Generated Image]({mock_url})
        """

        yield {"type": "token", "content": result_msg.strip()}
        return result_msg.strip()

    return generator()
