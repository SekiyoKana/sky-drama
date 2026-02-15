import os
import sys

def get_resource_path(relative_path: str) -> str:
    """
    获取资源的绝对路径，兼容 PyInstaller 打包（_MEIPASS）和开发环境。
    用于访问打包进去的静态资源，如 app/skills。
    """
    # PyInstaller 打包后的临时解压路径存储在 sys._MEIPASS
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    
    # 结合 Tauri 传入的环境变量
    work_dir = os.environ.get("APP_WORK_DIR")
    
    path = os.path.join(base_path, relative_path)
    
    # 如果临时路径下找不到，尝试从工作目录找（外部资源）
    if not os.path.exists(path) and work_dir:
        path = os.path.join(work_dir, relative_path)
        
    return path

def get_writable_path(relative_path: str) -> str:
    """
    获取可写目录的路径，用于存放数据库（SQLite）、日志等持久化文件。
    在打包后，这些文件应该放在用户 Application Support 目录下。
    """
    work_dir = os.environ.get("APP_WORK_DIR", os.path.abspath("."))
    return os.path.join(work_dir, relative_path)