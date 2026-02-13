"""
Image utilities for compositing and processing
"""
import base64
import io
import os
import uuid
from app.utils.http_client import request as http_request, download_headers
from PIL import Image
from typing import List, Optional
from app.core.config import settings




def load_image_from_url_or_path(url: str) -> Image.Image:
    """
    Load an image from URL, local path, or base64 data URI.
    
    Args:
        url: Image source (http URL, /assets/ path, filesystem path, or data URI)
    
    Returns:
        PIL Image object
    """
    if url.startswith('data:image'):
        # Base64 data URI - extract and decode
        base64_data = url.split(',', 1)[1] if ',' in url else url
        img_data = base64.b64decode(base64_data)
        return Image.open(io.BytesIO(img_data))
    elif url.startswith('http://') or url.startswith('https://'):
        # Remote URL
        response = http_request("GET", url, timeout=30, headers=download_headers())
        return Image.open(io.BytesIO(response.content))
    elif url.startswith('/assets/'):
        # Local asset path - convert to filesystem path
        filename = url.replace('/assets/', '')
        filepath = os.path.join(settings.ASSETS_DIR, filename)
        return Image.open(filepath)
    else:
        # Assume filesystem path
        return Image.open(url)

def composite_reference_image(
    image_urls: List[str], 
    target_width: int = 1920, 
    target_height: int = 1080
) -> str:
    """
    Composite multiple images (storyboard, character, scene) into a single 16:9 image.
    
    Args:
        image_urls: List of image URLs (local paths like /assets/xxx, http URLs, or base64 data URIs)
        target_width: Target composite image width (default 1920 for 16:9)
        target_height: Target composite image height (default 1080 for 16:9)
    
    Returns:
        Base64 encoded string of the composite image with data URI prefix
    """
    if not image_urls:
        raise ValueError("No image URLs provided")
    
    print(f"\n[Image Composite] Starting composition of {len(image_urls)} image(s)")
    print(f"[Image Composite] Target size: {target_width}x{target_height}")
    
    images = []
    
    # Load all images
    for idx, url in enumerate(image_urls, 1):
        try:
            print(f"[Image Composite] [{idx}/{len(image_urls)}] Loading: {url[:80]}...")
            
            img = load_image_from_url_or_path(url)
            
            if url.startswith('data:image'):
                print(f"[Image Composite]   ✓ Loaded base64 image ({img.size[0]}x{img.size[1]}, {img.mode})")
            elif url.startswith('http://') or url.startswith('https://'):
                print(f"[Image Composite]   ✓ Loaded remote image ({img.size[0]}x{img.size[1]}, {img.mode})")
            else:
                # Local path
                filepath = url
                if url.startswith('/assets/'):
                    filename = url.replace('/assets/', '')
                    filepath = os.path.join(settings.ASSETS_DIR, filename)
                print(f"[Image Composite]   ✓ Loaded local image ({img.size[0]}x{img.size[1]}, {img.mode}) from {filepath}")
            
            # Convert to RGB if needed (remove alpha channel)
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
                print(f"[Image Composite]   → Converted to RGB")
            elif img.mode != 'RGB':
                img = img.convert('RGB')
                print(f"[Image Composite]   → Converted {img.mode} to RGB")
                
            images.append(img)
        except Exception as e:
            print(f"[Image Composite]   ✗ Failed to load image {url[:80]}: {e}")
            continue
    
    if not images:
        raise ValueError("Failed to load any images")
    
    print(f"\n[Image Composite] Successfully loaded {len(images)}/{len(image_urls)} image(s)")
    
    # Create composite canvas
    canvas = Image.new('RGB', (target_width, target_height), (255, 255, 255))
    print(f"[Image Composite] Created canvas: {target_width}x{target_height}")
    
    # Layout strategy: Arrange images horizontally with equal spacing
    num_images = len(images)
    
    if num_images == 1:
        # Single image - resize to fit canvas
        print(f"[Image Composite] Layout: Single image (centered)")
        img = images[0]
        img.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)
        x = (target_width - img.width) // 2
        y = (target_height - img.height) // 2
        canvas.paste(img, (x, y))
        print(f"[Image Composite]   - Image positioned at ({x}, {y}), size {img.width}x{img.height}")
    elif num_images == 2:
        # Two images - split canvas vertically
        print(f"[Image Composite] Layout: Two images (side-by-side)")
        available_width = target_width // 2 - 20  # 20px padding
        for i, img in enumerate(images):
            img.thumbnail((available_width, target_height - 40), Image.Resampling.LANCZOS)
            x = i * (target_width // 2) + (available_width - img.width) // 2 + 10
            y = (target_height - img.height) // 2
            canvas.paste(img, (x, y))
            print(f"[Image Composite]   - Image {i+1} positioned at ({x}, {y}), size {img.width}x{img.height}")
    else:
        # Three or more images - arrange in grid
        # Top row: characters and scenes (equally divided)
        # Bottom row: storyboard (full width)
        if num_images == 3:
            print(f"[Image Composite] Layout: Three images (2 top + 1 bottom)")
            # 2 images on top, 1 on bottom
            top_width = target_width // 2 - 20
            top_height = target_height // 2 - 20
            
            # Top two images
            for i in range(2):
                img = images[i]
                img.thumbnail((top_width, top_height), Image.Resampling.LANCZOS)
                x = i * (target_width // 2) + (top_width - img.width) // 2 + 10
                y = (top_height - img.height) // 2 + 10
                canvas.paste(img, (x, y))
                print(f"[Image Composite]   - Image {i+1} (top) positioned at ({x}, {y}), size {img.width}x{img.height}")
            
            # Bottom image (storyboard)
            img = images[2]
            img.thumbnail((target_width - 40, target_height // 2 - 20), Image.Resampling.LANCZOS)
            x = (target_width - img.width) // 2
            y = target_height // 2 + (target_height // 2 - img.height) // 2
            canvas.paste(img, (x, y))
            print(f"[Image Composite]   - Image 3 (bottom) positioned at ({x}, {y}), size {img.width}x{img.height}")
        else:
            # More than 3 images - simple grid layout
            cols = min(3, num_images)
            rows = (num_images + cols - 1) // cols
            print(f"[Image Composite] Layout: Grid ({rows}x{cols})")
            
            cell_width = target_width // cols - 20
            cell_height = target_height // rows - 20
            
            for idx, img in enumerate(images):
                row = idx // cols
                col = idx % cols
                
                img.thumbnail((cell_width, cell_height), Image.Resampling.LANCZOS)
                x = col * (target_width // cols) + (cell_width - img.width) // 2 + 10
                y = row * (target_height // rows) + (cell_height - img.height) // 2 + 10
                canvas.paste(img, (x, y))
                print(f"[Image Composite]   - Image {idx+1} positioned at ({x}, {y}), size {img.width}x{img.height}")
    
    # Convert to base64
    print(f"[Image Composite] Converting to base64...")
    buffer = io.BytesIO()
    canvas.save(buffer, format='PNG')
    buffer.seek(0)
    
    base64_str = base64.b64encode(buffer.read()).decode('utf-8')
    data_uri = f"data:image/png;base64,{base64_str}"
    print(f"[Image Composite] ✓ Composition complete! Data URI size: {len(data_uri)} characters\n")
    
    return data_uri

def to_base64(image_file: str) -> Optional[str]:
    # 1. First check if the file exists as-is (handles valid absolute paths and relative paths)
    if os.path.exists(image_file):
        pass
    # 2. If not, try stripping leading slash (handles /assets/... -> assets/...)
    elif image_file.startswith('/'):
        image_file = image_file.lstrip('/')

    # 3. Fallback: try relative to CWD if it still doesn't exist
    if not os.path.exists(image_file):
        image_file = os.path.join(os.getcwd(), image_file)
    
    if os.path.exists(image_file):
        with open(image_file, "rb") as file:
            encoded_string = base64.b64encode(file.read()).decode('utf-8')
            encoded_string = f"data:image/png;base64,{encoded_string}"
            return encoded_string
    else:
        return None

def _merge_images_list(img_objects, mode):
    if not img_objects: return None
    if mode == 'horizontal':
        total_width = sum(img.width for img in img_objects)
        max_height = max(img.height for img in img_objects)
        new_img = Image.new('RGBA', (total_width, max_height), (255, 255, 255, 0))
        current_x = 0
        for img in img_objects:
            new_img.paste(img, (current_x, 0))
            current_x += img.width
    else: # vertical
        max_width = max(img.width for img in img_objects)
        total_height = sum(img.height for img in img_objects)
        new_img = Image.new('RGBA', (max_width, total_height), (255, 255, 255, 0))
        current_y = 0
        for img in img_objects:
            new_img.paste(img, (0, current_y))
            current_y += img.height
    return new_img

def _get_compressed_stream(image, target_size_mb=2):
    target_bytes = target_size_mb * 1024 * 1024
    img_byte_arr = io.BytesIO()
    
    # 1. 尝试 PNG
    image.save(img_byte_arr, format='PNG', optimize=True)
    if img_byte_arr.tell() <= target_bytes:
        img_byte_arr.seek(0)
        return img_byte_arr, 'png', 'image/png'

    # 2. 转 JPEG 压缩
    rgb_image = Image.new("RGB", image.size, (255, 255, 255))
    rgb_image.paste(image, mask=image.split()[3] if image.mode == 'RGBA' else None)
        
    quality = 95
    while quality >= 10:
        img_byte_arr.seek(0)
        img_byte_arr.truncate()
        rgb_image.save(img_byte_arr, format='JPEG', quality=quality)
        if img_byte_arr.tell() <= target_bytes:
            img_byte_arr.seek(0)
            return img_byte_arr, 'jpg', 'image/jpeg'
        quality -= 5
    
    # 3. 缩放兜底
    scale = 0.9
    width, height = rgb_image.size
    while img_byte_arr.tell() > target_bytes and width > 100:
        width = int(width * scale)
        height = int(height * scale)
        resized = rgb_image.resize((width, height), Image.Resampling.LANCZOS)
        img_byte_arr.seek(0)
        img_byte_arr.truncate()
        resized.save(img_byte_arr, format='JPEG', quality=quality)
    
    img_byte_arr.seek(0)
    return img_byte_arr, 'jpg', 'image/jpeg'

def combine_image(images, direction='vertical', return_type='blob'):
    """
    组合图片 -> 压缩 -> 保存本地 -> 返回内存流或相对路径
    :param images: 嵌套图片列表
    :param direction: 最终合成方向
    :param return_type: 'blob' 返回内存流, 'path' 返回形式如 './assets/xxx.jpg' 的路径
    :return: 
        if return_type == 'blob': (io.BytesIO, str)
        if return_type == 'path': (str, str)
    """
    # base_path = os.getcwd() 
    group_images = []

    # 1. 组装逻辑
    for group in images:
        current_group_imgs = []
        for img_path in group['data']:
            try:
                # Use load_image_from_url_or_path for robust handling of URLs, assets, and absolute paths
                img = load_image_from_url_or_path(img_path)
                current_group_imgs.append(img)
            except Exception as e:
                print(f"Warning: 图片加载失败: {img_path} Error: {e}")
        
        if current_group_imgs:
            # 假设 _merge_images_list 是你定义的辅助函数
            group_images.append(_merge_images_list(current_group_imgs, group['direction']))

    if not group_images:
        raise ValueError("没有有效的图片可供拼接")

    # 2. 合成最终图片
    final_image_obj = _merge_images_list(group_images, direction)

    # 3. 压缩获取内存流 (假设 _get_compressed_stream 返回 stream, ext, mime)
    img_stream, ext, mime_type = _get_compressed_stream(final_image_obj)

    # 4. 保存本地副本
    output_dir = settings.ASSETS_DIR
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    filename = f"combine_{uuid.uuid4()}.{ext}"
    full_save_path = os.path.join(output_dir, filename)

    # 将内存流内容写入硬盘
    with open(full_save_path, 'wb') as f:
        f.write(img_stream.getvalue())

    # 5. 处理返回值
    if return_type == 'path':
        # Return path formatted as ./assets/filename.jpg
        formatted_path = f"./assets/{filename}"
        return formatted_path, mime_type
    else:
        # 重置指针给内存流模式使用
        img_stream.seek(0) 
        return img_stream, mime_type
