"""
图片工具模块 - 统一的图片加载和 base64 转换
所有适配器共用，新增 API 适配器直接调用此模块
"""

import io
import base64
from pathlib import Path
from typing import Optional, Tuple

import requests
from PIL import Image


def load_image(path_or_url: str, timeout: int = 60) -> Optional[Image.Image]:
    """
    加载图片（自动识别本地路径或URL）

    Args:
        path_or_url: 本地文件路径 或 网络图片URL
        timeout: URL下载超时秒数

    Returns:
        PIL Image，失败返回 None
    """
    try:
        path_obj = Path(path_or_url)
        if path_obj.exists():
            img = Image.open(path_or_url)
            print(f"[图片] 本地加载成功: {img.size} {img.mode} ({path_obj.stat().st_size / 1024:.1f} KB)")
            return img
        else:
            print(f"[图片] 本地不存在，尝试URL下载: {path_or_url[:80]}...")
            resp = requests.get(path_or_url, timeout=timeout)
            resp.raise_for_status()
            img = Image.open(io.BytesIO(resp.content))
            print(f"[图片] URL下载成功: {img.size} {img.mode} ({len(resp.content) / 1024:.1f} KB)")
            return img
    except Exception as e:
        print(f"[图片] 加载失败: {e}")
        return None


def image_to_base64(
    image: Image.Image,
    fmt: str = "JPEG",
    quality: int = 95
) -> Tuple[str, str]:
    """
    将 PIL Image 转为 base64 字符串

    Args:
        image: PIL Image 对象
        fmt: 输出格式 JPEG / PNG / WEBP
        quality: JPEG 质量 (1-100)

    Returns:
        (base64字符串, mime_type)
        例如: ("/9j/4AAQ...", "image/jpeg")
    """
    # 需要时转 RGB（JPEG 不支持 RGBA）
    if fmt.upper() in ("JPEG",) and image.mode in ("RGBA", "LA", "P"):
        image = image.convert("RGB")

    buffer = io.BytesIO()
    save_kwargs = {"format": fmt}
    if fmt.upper() == "JPEG":
        save_kwargs["quality"] = quality
        save_kwargs["optimize"] = True

    image.save(buffer, **save_kwargs)
    buffer.seek(0)

    b64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
    mime_map = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}
    mime_type = mime_map.get(fmt.upper(), "image/jpeg")

    print(f"[图片] 转base64完成: {len(b64_str)} 字符, 格式: {mime_type}")
    return b64_str, mime_type


def base64_to_image(b64_str: str) -> Optional[Image.Image]:
    """
    将 base64 字符串还原为 PIL Image

    Args:
        b64_str: base64 编码的图片数据

    Returns:
        PIL Image，失败返回 None
    """
    try:
        raw = base64.b64decode(b64_str)
        return Image.open(io.BytesIO(raw))
    except Exception as e:
        print(f"[图片] base64解码失败: {e}")
        return None


def load_and_encode(path_or_url: str, fmt: str = "JPEG", quality: int = 95) -> Optional[Tuple[str, str]]:
    """
    一步到位：加载图片 + 转 base64（最常用的组合操作）

    Args:
        path_or_url: 本地路径 或 URL
        fmt: 输出格式 JPEG / PNG / WEBP
        quality: JPEG 质量

    Returns:
        (base64字符串, mime_type)，失败返回 None
    """
    img = load_image(path_or_url)
    if img is None:
        return None
    return image_to_base64(img, fmt=fmt, quality=quality)
