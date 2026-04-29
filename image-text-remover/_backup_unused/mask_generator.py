"""
遮罩生成器 - 根据OCR结果生成修复遮罩
"""

from typing import List, Tuple
from PIL import Image, ImageDraw
import numpy as np

from .api_adapter import TextDetection
from .config import get_config


class MaskGenerator:
    """遮罩生成器"""

    def __init__(self):
        self.config = get_config()
        self.ecommerce_config = self.config.get_ecommerce_config()
        self.blocklist = self.config.get_blocklist()

        # 扩展屏蔽词（大小写变体）
        self.expanded_blocklist = self._expand_blocklist()

    def _expand_blocklist(self) -> List[str]:
        """扩展屏蔽词列表，包含大小写变体"""
        expanded = set()
        for word in self.blocklist:
            expanded.add(word.lower())
            expanded.add(word.upper())
            expanded.add(word)
        return list(expanded)

    def filter_detections(self, detections: List[TextDetection]) -> List[TextDetection]:
        """
        过滤OCR结果，只保留需要去除的文字

        Args:
            detections: OCR检测到的所有文字

        Returns:
            需要去除的文字列表
        """
        filtered = []

        # 配置参数
        min_height = self.ecommerce_config.get('smart_detect', {}).get('min_text_height', 8)
        conf_threshold = self.ecommerce_config.get('smart_detect', {}).get('confidence_threshold', 0.7)

        for det in detections:
            # 过滤小文字
            box_height = det.box[3] - det.box[1] if len(det.box) >= 4 else 0
            if box_height < min_height:
                continue

            # 过滤低置信度
            if det.confidence < conf_threshold:
                continue

            # 检查是否在屏蔽词列表中
            if self._should_remove(det.text):
                filtered.append(det)

        return filtered

    def _should_remove(self, text: str) -> bool:
        """判断文字是否应该被去除"""
        text_lower = text.lower()
        text_upper = text.upper()

        # 检查完全匹配
        for block_word in self.expanded_blocklist:
            if block_word in text or block_word in text_lower or block_word in text_upper:
                return True

        # 检查常见水印/版权符号
        special_chars = ['©', '®', '™', '℠', 'Ⓡ', 'ⓒ']
        for char in special_chars:
            if char in text:
                return True

        # 检查是否是纯数字（可能是价格）
        if text.isdigit() and len(text) >= 3:
            return True

        # 检查是否包含常见电商关键词
        ecommerce_keywords = [
            '天猫', '淘宝', '京东', '拼多多', '抖音', '快手',
            '旗舰店', '正品', '包邮', '促销', '折扣', '限时',
            'tmall', 'taobao', 'jd', 'pdd', 'discount', 'sale'
        ]
        for keyword in ecommerce_keywords:
            if keyword in text_lower:
                return True

        return False

    def create_mask(self, image_size: Tuple[int, int],
                    detections: List[TextDetection],
                    dilation: int = 5) -> Image.Image:
        """
        创建遮罩图

        Args:
            image_size: (width, height)
            detections: 需要去除的文字检测结果
            dilation: 边缘扩展像素数（确保完全覆盖文字）

        Returns:
            遮罩图（白色区域为需要修复的部分）
        """
        width, height = image_size

        # 创建黑色背景
        mask = Image.new('L', (width, height), 0)
        draw = ImageDraw.Draw(mask)

        for det in detections:
            box = det.box

            # 支持两种box格式：
            # 1. [x1, y1, x2, y2] - 两点格式
            # 2. [[x1,y1], [x2,y2], [x3,y3], [x4,y4]] - 四边形格式

            if len(box) == 4 and all(isinstance(x, (int, float)) for x in box):
                # 两点格式
                x1, y1, x2, y2 = map(int, box)
                # 扩展边缘
                x1 = max(0, x1 - dilation)
                y1 = max(0, y1 - dilation)
                x2 = min(width, x2 + dilation)
                y2 = min(height, y2 + dilation)
                draw.rectangle([x1, y1, x2, y2], fill=255)

            elif len(box) == 4 and all(isinstance(x, (list, tuple)) for x in box):
                # 四边形格式 - 转换为矩形
                xs = [p[0] for p in box]
                ys = [p[1] for p in box]
                x1, y1, x2, y2 = min(xs), min(ys), max(xs), max(ys)
                x1 = max(0, x1 - dilation)
                y1 = max(0, y1 - dilation)
                x2 = min(width, x2 + dilation)
                y2 = min(height, y2 + dilation)
                draw.rectangle([x1, y1, x2, y2], fill=255)

        return mask

    def create_visualization(self, image: Image.Image,
                           detections: List[TextDetection],
                           mask: Image.Image = None) -> Image.Image:
        """
        创建可视化结果（用于调试）

        Args:
            image: 原图
            detections: 检测到的文字
            mask: 遮罩图（可选）

        Returns:
            带标注的可视化图片
        """
        # 复制原图
        vis = image.copy().convert('RGBA')

        # 创建透明覆盖层
        overlay = Image.new('RGBA', vis.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # 绘制检测框
        for det in detections:
            box = det.box
            if len(box) == 4 and all(isinstance(x, (int, float)) for x in box):
                x1, y1, x2, y2 = map(int, box)
                # 红色半透明框
                draw.rectangle([x1, y1, x2, y2], outline=(255, 0, 0, 200), width=2)
                # 文字标签背景
                label = det.text[:20]  # 限制长度
                text_bbox = draw.textbbox((0, 0), label)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                draw.rectangle([x1, y1 - text_height - 4, x1 + text_width + 4, y1], fill=(255, 0, 0, 150))
                draw.text((x1 + 2, y1 - text_height - 2), label, fill=(255, 255, 255, 255))

        # 合并图层
        vis = Image.alpha_composite(vis, overlay)

        # 如果提供了mask，也显示出来
        if mask:
            # 将mask转为红色半透明
            mask_rgba = mask.convert('RGBA')
            mask_data = np.array(mask_rgba)
            # 白色区域变红色半透明
            mask_data[:, :, 0] = mask_data[:, :, 0]  # R
            mask_data[:, :, 1] = 0  # G
            mask_data[:, :, 2] = 0  # B
            mask_data[:, :, 3] = (mask_data[:, :, 3] * 0.3).astype(np.uint8)  # Alpha
            mask_img = Image.fromarray(mask_data)

            # 并排显示
            combined = Image.new('RGBA', (vis.width * 2, vis.height))
            combined.paste(vis, (0, 0))
            combined.paste(mask_img, (vis.width, 0))
            return combined

        return vis


def generate_mask(image_path: str, detections: List[TextDetection]) -> Image.Image:
    """
    快捷函数：生成遮罩

    Args:
        image_path: 图片路径
        detections: OCR检测结果

    Returns:
        遮罩图
    """
    generator = MaskGenerator()

    # 过滤需要去除的文字
    filtered = generator.filter_detections(detections)

    # 获取图片尺寸
    with Image.open(image_path) as img:
        size = img.size

    # 生成遮罩
    mask = generator.create_mask(size, filtered)

    return mask
