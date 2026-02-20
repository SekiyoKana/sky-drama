import sys
import importlib
import inspect
import os
import logging
from app.skills.utils.runnable import run_in_thread_and_stream

logger = logging.getLogger(__name__)

_SKILL_REGISTRY = {}

def load_skills():
    """Scan subdirectories in skills/ for main.py"""
    global _SKILL_REGISTRY
    
    _SKILL_REGISTRY = {}
    
    # 1. Manual registration for frozen mode (PyInstaller)
    # PyInstaller cannot scan filesystem effectively for dynamic imports in one-file mode
    # So we list known skills explicitly.
    known_skills = [
        "short_video_screenwriter",
        "short_video_storyboard_maker",
        "short_video_prompt_engineer",
        "short_video_sora2_prompt",
        "short_video_asset_generator",
        "novel_snowflake_planner",
        "novel_chapter_writer",
        "novel_expansion_assistant",
    ]
    
    for subdir in known_skills:
        try:
            module_name = f"app.skills.{subdir}.main"
            module = importlib.import_module(module_name)
            register_module(module, subdir)
        except Exception as e:
            logger.warning(f"Failed to load known skill '{subdir}': {e}")

    # 2. Dynamic scanning (Dev mode fallback)
    base_path = os.path.dirname(os.path.abspath(__file__))
    if os.path.exists(base_path) and not getattr(sys, 'frozen', False):
        try:
            items = os.listdir(base_path)
            subdirs = [d for d in items if os.path.isdir(os.path.join(base_path, d))]
            
            for subdir in subdirs:
                if subdir in ['utils', 'knowledge', '__pycache__', 'library', 'assets']: 
                    continue
                # Skip if already loaded
                if any(k.replace('-', '_') == subdir for k in _SKILL_REGISTRY.keys()):
                    continue
                    
                try:
                    module_name = f"app.skills.{subdir}.main"
                    module = importlib.import_module(module_name)
                    register_module(module, subdir)
                except Exception as e:
                    logger.info(f"❌ Error loading {subdir}: {e}")
        except Exception as e:
            logger.error(f"Dynamic skill scanning failed: {e}")

def register_module(module, subdir):
    if hasattr(module, "name") and hasattr(module, "description") and hasattr(module, "input_schema"):
        if not hasattr(module, "main"):
            logger.info(f"⚠️ Module {subdir} missing 'main' function")
            return

        skill_def = {
            "name": module.name,
            "description": module.description,
            "input_schema": module.input_schema,
            "module": module,
            "type": "function"
        }
        
        # Register with original name
        _SKILL_REGISTRY[skill_def['name']] = skill_def
        
        # Also register with hyphen/underscore swapped version if different
        alt_name = skill_def['name'].replace('_', '-')
        if alt_name != skill_def['name']:
            _SKILL_REGISTRY[alt_name] = skill_def
            
        alt_name_snake = skill_def['name'].replace('-', '_')
        if alt_name_snake != skill_def['name']:
            _SKILL_REGISTRY[alt_name_snake] = skill_def

        logger.info(f"✅ Loaded Python Skill: {skill_def['name']}")
    else:
        logger.info(f"⚠️ Module {subdir} missing metadata (name, description, input_schema)")

def execute_skill(tool_name: str, arguments: dict, client: any = None, model_name: any = None):
    """
    Execute Skill in thread
    """
    if tool_name not in _SKILL_REGISTRY:
        load_skills()
        if tool_name not in _SKILL_REGISTRY:
            raise ValueError(f"Skill not found: {tool_name}")
            
    skill_info = _SKILL_REGISTRY[tool_name]
    module = skill_info["module"]
    
    logger.info(f"\n⚡ [SKILL EXEC] Starting thread for: {tool_name}")
    
    if skill_info["type"] == "function":
        func = getattr(module, "main")
        sig = inspect.signature(func)
        call_args = arguments.copy()
        if 'client' in sig.parameters:
            call_args['client'] = client
        if 'model_name' in sig.parameters:
            call_args['model_name'] = model_name
            
        return run_in_thread_and_stream(func, **call_args)
    else:
        raise ValueError(f"Unknown skill type: {skill_info['type']}")
