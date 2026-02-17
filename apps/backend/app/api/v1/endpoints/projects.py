from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import StreamingResponse, FileResponse
from starlette.background import BackgroundTask
from sqlalchemy.orm import Session
import zipfile
import io
import os
import subprocess
import tempfile
import httpx
from urllib.parse import quote

import shutil
import logging
import time

from app.api import deps
from app.models.project import Project, Episode
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectOut, EpisodeOut, EpisodeCreate, EpisodeUpdate
from app.core.config import settings
from app.utils.think_filter import sanitize_think_payload

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=List[ProjectOut])
def read_projects(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    获取当前用户的所有项目 (分页)
    """
    # 🔒 隔离：只查询 user_id == current_user.id
    projects = db.query(Project)\
        .filter(Project.user_id == current_user.id)\
        .offset(skip)\
        .limit(limit)\
        .all()
    return projects

@router.post("/", response_model=ProjectOut)
def create_project(
    *,
    db: Session = Depends(deps.get_db),
    project_in: ProjectCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    创建新项目
    """
    project = Project(
        name=project_in.name,
        description=project_in.description,
        user_id=current_user.id # 🔒 绑定给当前用户
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

@router.get("/{id}", response_model=ProjectOut)
def read_project(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    获取特定项目详情
    """
    project = db.query(Project).filter(
        Project.id == id, 
        Project.user_id == current_user.id # 🔒 隔离
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.put("/{id}", response_model=ProjectOut)
def update_project(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    project_in: ProjectUpdate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    更新项目信息
    """
    project = db.query(Project).filter(
        Project.id == id, 
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # 更新字段
    update_data = project_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
        
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

@router.delete("/{id}")
def delete_project(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    删除项目
    """
    project = db.query(Project).filter(
        Project.id == id, 
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    db.delete(project)
    db.commit()
    return {"status": "success", "id": id}

@router.get("/{project_id}/episodes", response_model=List[EpisodeOut])
def read_episodes(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    # 1. 确认项目属于该用户
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    return project.episodes

@router.post("/{project_id}/episodes", response_model=EpisodeOut)
def create_episode(
    project_id: int,
    episode_in: EpisodeCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    # 1. 确认项目属于该用户
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    episode = Episode(
        project_id=project_id,
        title=episode_in.title,
        status=episode_in.status
    )
    db.add(episode)
    db.commit()
    db.refresh(episode)
    return episode

@router.put("/{project_id}/episodes/{episode_id}", response_model=EpisodeOut)
def update_episode(
    project_id: int,
    episode_id: int,
    episode_in: EpisodeUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    try:
        # 1. 鉴权：确认项目属于当前用户
        project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # 2. 查找剧集
        episode = db.query(Episode).filter(Episode.id == episode_id, Episode.project_id == project_id).first()
        if not episode:
            raise HTTPException(status_code=404, detail="Episode not found")

        # 3. 动态更新字段
        # exclude_unset=True 确保只更新前端传过来的字段 (比如只传了 ai_config，就不动 title)
        update_data = episode_in.dict(exclude_unset=True)
        if "ai_config" in update_data:
            update_data["ai_config"] = sanitize_think_payload(update_data["ai_config"])
        for field, value in update_data.items():
            setattr(episode, field, value)

        db.add(episode)
        db.commit()
        db.refresh(episode)
        return episode
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{project_id}/episodes/{episode_id}")
def delete_episode(
    project_id: int,
    episode_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    # 1. 确认项目属于该用户
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    episode = db.query(Episode).filter(Episode.id == episode_id, Episode.project_id == project_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
        
    db.delete(episode)
    db.commit()
    return {"status": "success", "id": episode_id}


@router.get("/{id}/assets")
def get_project_assets(
    id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get aggregated characters and scenes from all episodes in a project.
    """
    project = db.query(Project).filter(
        Project.id == id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    characters = {}
    scenes = {}

    for episode in project.episodes:
        if episode.ai_config and "generated_script" in episode.ai_config:
            script_data = episode.ai_config["generated_script"]
            
            for char in script_data.get("characters", []):
                char_id = char.get("id")
                if char_id and char_id not in characters:
                    characters[char_id] = char

            for scene in script_data.get("scenes", []):
                scene_id = scene.get("id")
                if scene_id and scene_id not in scenes:
                    scenes[scene_id] = scene

    return {
        "characters": list(characters.values()),
        "scenes": list(scenes.values())
    }

import re

def sanitize_filename(name: str) -> str:
    # 移除非法字符，保留中文、字母、数字、下划线、空格
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

@router.get("/{project_id}/episodes/{episode_id}/export/assets")
async def export_episode_assets(
    project_id: int,
    episode_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    导出素材库：打包所有生成的图片和视频
    """
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    episode = db.query(Episode).filter(Episode.id == episode_id, Episode.project_id == project_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    tasks = [] # (url, folder, filename_base, trim)
    def add_task(url, folder, filename_base):
        if url:
            # 分离 URL Fragment (#t=...)
            clean_url = url
            trim_info = None
            if '#' in url:
                parts = url.split('#')
                clean_url = parts[0]
                if len(parts) > 1:
                    try:
                        fragment = parts[1]
                        if fragment.startswith('t='):
                            times = fragment[2:].split(',')
                            start = float(times[0]) if len(times) >= 1 else 0.0
                            end = float(times[1]) if len(times) >= 2 else None
                            if start > 0 or end is not None:
                                trim_info = (start, end)
                    except: pass

            basename = os.path.basename(clean_url)
            if not basename: return
            
            # 提取扩展名
            _, ext = os.path.splitext(basename)
            if not ext: ext = ".png" # Default fallback
            
            clean_name = sanitize_filename(filename_base)
            if not clean_name: clean_name = "untitled"
            
            # 限制长度
            clean_name = clean_name[:50]
            
            tasks.append({
                "url": clean_url,
                "folder": folder,
                "filename": f"{clean_name}{ext}",
                "trim": trim_info
            })


    config = episode.ai_config or {}
    script = config.get("generated_script", {})
    
    # 收集素材 - Characters
    logger.info(f"[Export] Starting export for episode {episode.title} (ID: {episode_id})")
    task_count = 0
    
    for i, char in enumerate(script.get("characters", [])):
        name = char.get("name") or f"character_{i+1}"
        add_task(char.get("image_url"), "characters", name)
        
    # 收集素材 - Scenes
    for i, scene in enumerate(script.get("scenes", [])):
        name = scene.get("location_name") or f"scene_{i+1}"
        add_task(scene.get("image_url"), "scenes", name)
        
    # 收集素材 - Storyboards
    for i, board in enumerate(script.get("storyboard", [])):
        shot = board.get("shot_type", "")
        action = board.get("action", "")
        name = f"{i+1}_{shot}_{action}"
        if not name.strip("_"): name = f"storyboard_{i+1}"
        
        add_task(board.get("image_url"), "storyboards", name)
        add_task(board.get("video_url"), "storyboards", f"{name}_video")
        
    # 从时间线中收集实际使用的视频
    timeline = config.get("timeline_data", [])
    for t_idx, track in enumerate(timeline):
        for i, item in enumerate(track.get("items", [])):
             if item.get("type") == "video":
                 name = item.get("name") or f"clip_{t_idx}_{i}"
                 add_task(item.get("src"), "timeline", name)

    logger.info(f"[Export] Total tasks collected: {len(tasks)}")
    
    zip_buffer = io.BytesIO()
    added_paths = set()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        async with httpx.AsyncClient() as client:
            for task in tasks:
                url = task["url"]
                folder = task["folder"]
                filename = task["filename"]
                trim = task.get("trim")
                
                try:
                    zip_path = f"{folder}/{filename}"
                    
                    # 处理重名
                    counter = 1
                    base, ext = os.path.splitext(filename)
                    while zip_path in added_paths:
                        new_filename = f"{base}_{counter}{ext}"
                        zip_path = f"{folder}/{new_filename}"
                        counter += 1
                    
                    added_paths.add(zip_path)

                    if url.startswith("/assets/"):
                        # 处理本地资源
                        clean_path = url.replace("/assets/", "", 1)
                        if ".." in clean_path: continue
                        local_path = os.path.abspath(os.path.join(settings.ASSETS_DIR, clean_path))
                        
                        if os.path.exists(local_path) and os.path.isfile(local_path):
                            logger.info(f"[Export] Packing local file: {local_path}")
                            # 如果需要裁剪且是 timeline 里的视频
                            if trim and folder == "timeline":
                                start, end = trim
                                with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp_file:
                                    tmp_out_path = tmp_file.name
                                try:
                                    cmd = ["ffmpeg", "-y"]
                                    
                                    if start > 0:
                                        cmd.extend(["-ss", str(start)])
                                    if end is not None:
                                        cmd.extend(["-to", str(end)])
                                        
                                    cmd.extend(["-i", local_path])
                                    
                                    cmd.extend(["-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", "-avoid_negative_ts", "1", tmp_out_path])
                                    
                                    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                                    zip_file.write(tmp_out_path, zip_path)
                                except Exception as e:
                                    logger.info(f"Trim failed for {url}: {e}. Packing original.")
                                    zip_file.write(local_path, zip_path)
                                finally:
                                    if os.path.exists(tmp_out_path):
                                        os.remove(tmp_out_path)
                            else:
                                zip_file.write(local_path, zip_path)
                        else:
                            logger.warning(f"[Export] Local file not found: {local_path} (Original URL: {url})")
                            
                    elif url.startswith("http"):


                        # 处理网络资源
                        logger.info(f"[Export] Downloading URL: {url}")
                        try:
                            resp = await client.get(url, follow_redirects=True, timeout=10.0)
                            if resp.status_code == 200:
                                # Use ZipInfo to ensure permissions are set correctly for Mac/Linux
                                zinfo = zipfile.ZipInfo(zip_path)
                                zinfo.date_time = time.localtime(time.time())[:6]
                                zinfo.compress_type = zipfile.ZIP_DEFLATED
                                zinfo.create_system = 3  # Unix
                                zinfo.external_attr = 0o100644 << 16  # -rw-r--r--
                                zip_file.writestr(zinfo, resp.content)
                            else:
                                logger.warning(f"[Export] Failed to download {url}, status: {resp.status_code}")
                        except Exception as dl_err:
                            logger.error(f"[Export] Download error for {url}: {dl_err}")
                    else:
                        logger.warning(f"[Export] Skipping unknown URL format: {url}")
                            
                except Exception as e:
                    logger.error(f"Error packing {url}: {e}")
                    
    zip_buffer.seek(0)
    file_content = zip_buffer.getvalue()
    filename = f"{episode.title}_assets.zip"
    encoded_filename = quote(filename)
    
    return Response(
        content=file_content, 
        media_type="application/zip", 
        headers={
            "Content-Disposition": f"attachment; filename*=utf-8''{encoded_filename}",
            "Content-Length": str(len(file_content))
        }
    )

@router.get("/{project_id}/episodes/{episode_id}/export/storyboard_data")
async def export_episode_storyboard_data(
    project_id: int,
    episode_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    导出分镜数据：以文件夹形式返回每个分镜的图片和 prompt.txt
    """
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    episode = db.query(Episode).filter(Episode.id == episode_id, Episode.project_id == project_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    config = episode.ai_config or {}
    script = config.get("generated_script", {})
    storyboards = script.get("storyboard", [])

    if not storyboards:
        raise HTTPException(status_code=400, detail="No storyboard data found")

    # 构建 ID -> Name 映射表
    entity_map = {}
    for char in script.get("characters", []):
        if char.get("id") and char.get("name"):
            entity_map[char["id"]] = char["name"]
    
    for scene in script.get("scenes", []):
        if scene.get("id") and scene.get("location_name"):
            entity_map[scene["id"]] = scene["location_name"]

    logger.info(f"[Export] Starting storyboard data export for episode {episode.title} (ID: {episode_id})")

    zip_buffer = io.BytesIO()
    
    async with httpx.AsyncClient() as client:
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for i, board in enumerate(storyboards):
                # 1. 构造文件夹名称
                shot = board.get("shot_type", "")
                action = board.get("action", "")
                prompt_text = board.get("visual_prompt", "")
                image_url = board.get("image_url", "")

                # 替换 prompt 中的 {id} 为名称
                if prompt_text:
                    def replace_entity(match):
                        key = match.group(1)
                        return entity_map.get(key, match.group(0))
                    prompt_text = re.sub(r'\{\{([^}]+)\}\}', replace_entity, prompt_text)

                folder_name = f"{i+1:03d}_{sanitize_filename(shot)}_{sanitize_filename(action)}"
                # 限制文件夹名长度，防止过长
                folder_name = folder_name[:50].strip("_")
                
                # 2. 写入 prompt.txt
                # 如果 prompt 为空，也创建一个空文件或写入提示
                zip_file.writestr(f"{folder_name}/prompt.txt", prompt_text or "")

                # 3. 处理图片
                if image_url:
                    # 获取扩展名
                    clean_url = image_url.split('#')[0]
                    basename = os.path.basename(clean_url)
                    _, ext = os.path.splitext(basename)
                    if not ext: ext = ".png"
                    
                    filename = f"image{ext}"
                    zip_path = f"{folder_name}/{filename}"

                    try:
                        if clean_url.startswith("/assets/"):
                            # 本地文件
                            local_path_rel = clean_url.replace("/assets/", "", 1)
                            if ".." not in local_path_rel:
                                local_abs_path = os.path.join(settings.ASSETS_DIR, local_path_rel)
                                if os.path.exists(local_abs_path):
                                    zip_file.write(local_abs_path, zip_path)
                                else:
                                    logger.warning(f"[Export] Local file missing: {local_abs_path}")
                        elif clean_url.startswith("http"):
                            # 网络文件
                            try:
                                resp = await client.get(clean_url, follow_redirects=True, timeout=10.0)
                                if resp.status_code == 200:
                                    zip_file.writestr(zip_path, resp.content)
                                else:
                                    logger.warning(f"[Export] Download failed: {clean_url} ({resp.status_code})")
                            except Exception as dl_err:
                                logger.error(f"[Export] Download error: {dl_err}")
                    except Exception as e:
                        logger.error(f"[Export] Error processing image for storyboard {i}: {e}")

    zip_buffer.seek(0)
    file_content = zip_buffer.getvalue()
    filename = f"{episode.title}_storyboard_data.zip"
    encoded_filename = quote(filename)
    
    return Response(
        content=file_content, 
        media_type="application/zip", 
        headers={
            "Content-Disposition": f"attachment; filename*=utf-8''{encoded_filename}",
            "Content-Length": str(len(file_content))
        }
    )

def cleanup_file(path: str):
    if os.path.exists(path):
        os.remove(path)

@router.get("/{project_id}/episodes/{episode_id}/export/video")
def export_episode_video(
    project_id: int,
    episode_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    导出视频：合并主轨道视频 (先处理分片再合并，解决音画同步和时间偏差问题)
    Note: 使用同步 def，让 FastAPI 在线程池中运行，避免 subprocess 阻塞 async loop
    """
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    episode = db.query(Episode).filter(Episode.id == episode_id, Episode.project_id == project_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
        
    config = episode.ai_config or {}
    timeline = config.get("timeline_data", [])
    # 查找主轨道 (id=1 或 type=video)
    main_track = next((t for t in timeline if t.get("id") == 1 or t.get("type") == "video"), None)
    
    if not main_track or not main_track.get("items"):
         raise HTTPException(status_code=400, detail="主轨道无视频内容")
         
    items = main_track["items"]
    
    # 创建临时工作目录
    work_dir = tempfile.mkdtemp()
    final_output_path = os.path.join(work_dir, f"final_{episode_id}_{int(os.path.getmtime(work_dir))}.mp4")
    
    def cleanup_work_dir():
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir)

    try:
        clip_paths = []
        
        for i, item in enumerate(items):
            src = item.get("src")
            if not src: continue
            
            # 1. 解析时间参数 (参考 export_episode_assets)
            clean_url = src
            start = 0.0
            end = None
            
            if '#' in src:
                parts = src.split('#')
                clean_url = parts[0]
                if len(parts) > 1:
                    try:
                        fragment = parts[1]
                        if fragment.startswith('t='):
                            times = fragment[2:].split(',')
                            if len(times) >= 1 and times[0]:
                                start = float(times[0])
                            if len(times) >= 2 and times[1]:
                                end = float(times[1])
                    except:
                        pass
            
            # 2. 获取输入路径
            input_path = clean_url
            if clean_url.startswith("/assets/"):
                clean_path = clean_url.replace("/assets/", "", 1)
                # 安全检查
                if ".." in clean_path: continue
                local_abs_path = os.path.abspath(os.path.join(settings.ASSETS_DIR, clean_path))
                # 只有当文件存在时才使用本地路径，否则尝试作为 URL 处理 (或跳过)
                if os.path.exists(local_abs_path):
                    input_path = local_abs_path
            
            # 3. 处理单个分片 (转码+裁剪)
            clip_name = f"clip_{i:04d}.mp4"
            clip_path = os.path.join(work_dir, clip_name)
            
            cmd = ["ffmpeg", "-y"]
            
            # 时间裁剪 (Input seeking，速度快)
            if start > 0:
                cmd.extend(["-ss", str(start)])
            if end is not None:
                cmd.extend(["-to", str(end)])
                
            cmd.extend(["-i", input_path])
            
            # 统一转码参数，确保格式一致以便合并
            # 使用 libx264 + aac, ultrafast 预设以提高速度
            cmd.extend([
                "-c:v", "libx264", 
                "-preset", "ultrafast", 
                "-c:a", "aac", 
                "-avoid_negative_ts", "1",
                clip_path
            ])
            
            # 执行转码
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            clip_paths.append(clip_path)

        if not clip_paths:
             raise HTTPException(status_code=400, detail="没有可导出的有效视频片段")

        # 4. 生成合并列表
        list_path = os.path.join(work_dir, "concat_list.txt")
        with open(list_path, "w", encoding="utf-8") as f:
            for cp in clip_paths:
                # 绝对路径，注意转义单引号
                safe_path = cp.replace("'", "'\\''")
                f.write(f"file '{safe_path}'\n")
        
        # 5. 合并视频 (Copy 流即可，因为前面已经统一了编码)
        cmd_concat = [
            "ffmpeg", 
            "-f", "concat", 
            "-safe", "0", 
            "-i", list_path, 
            "-c", "copy", 
            "-y", final_output_path
        ]
        
        subprocess.run(cmd_concat, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        filename = f"{episode.title}.mp4"
        encoded_filename = quote(filename)
        
        # 6. 返回结果，并注册清理任务
        return FileResponse(
            final_output_path, 
            filename=filename, 
            media_type="video/mp4",
            background=BackgroundTask(cleanup_work_dir),
            headers={"Content-Disposition": f"attachment; filename*=utf-8''{encoded_filename}"}
        )
        
    except subprocess.CalledProcessError as e:
        cleanup_work_dir()
        logger.info(f"FFmpeg error: {e.stderr.decode()}")
        raise HTTPException(status_code=500, detail=f"视频处理失败: {e.stderr.decode()}")
    except Exception as e:
        cleanup_work_dir()
        logger.info(f"Export error: {e}")
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")
