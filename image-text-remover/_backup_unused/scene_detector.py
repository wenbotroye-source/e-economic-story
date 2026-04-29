"""
场景检测器 - 自动识别图片类型以选择最佳prompt
"""

from enum import Enum
from pathlib import Path
from typing import Tuple
from PIL import Image
import numpy as np


class SceneType(Enum):
    """场景类型"""
    DEFAULT = "default"
    WHITE_BACKGROUND = "white_background"
    LIFESTYLE = "lifestyle"
    SOLID_COLOR = "solid_color"
    FASHION = "fashion"
    FOOD = "food"
    ELECTRONICS = "electronics"


class SceneDetector:
    """场景检测器"""

    def __init__(self):
        # 背景颜色阈值
        self.white_threshold = 240  # 接近白色的阈值
        self.color_variance_threshold = 30  # 纯色背景方差阈值

    def detect(self, image_path: str) -> SceneType:
        """
        检测图片场景类型

        Returns:
            SceneType: 检测到的场景类型
        """
        image = Image.open(image_path)

        # 检测白底图
        if self._is_white_background(image):
            return SceneType.WHITE_BACKGROUND

        # 检测纯色背景
        if self._is_solid_color_background(image):
            return SceneType.SOLID_COLOR

        # 检测服装/模特图
        if self._is_fashion_image(image):
            return SceneType.FASHION

        # 检测食品图
        if self._is_food_image(image):
            return SceneType.FOOD

        # 检测电子产品
        if self._is_electronics_image(image):
            return SceneType.ELECTRONICS

        # 检测场景图（有复杂背景）
        if self._is_lifestyle_image(image):
            return SceneType.LIFESTYLE

        return SceneType.DEFAULT

    def _is_white_background(self, image: Image.Image) -> bool:
        """检测是否为白底图"""
        # 转换为RGB
        img = image.convert('RGB')
        arr = np.array(img)

        # 获取边缘区域（通常是背景）
        h, w = arr.shape[:2]
        edge_size = min(h, w) // 10

        # 检查四个角
        corners = [
            arr[:edge_size, :edge_size],  # 左上
            arr[:edge_size, -edge_size:],  # 右上
            arr[-edge_size:, :edge_size],  # 左下
            arr[-edge_size:, -edge_size:],  # 右下
        ]

        # 计算每个角的平均亮度和白色像素比例
        white_ratios = []
        for corner in corners:
            # 亮度 = (R + G + B) / 3
            brightness = np.mean(corner, axis=2)
            white_pixels = np.sum(brightness > self.white_threshold)
            white_ratio = white_pixels / brightness.size
            white_ratios.append(white_ratio)

        # 如果大部分角都是白色背景
        return np.mean(white_ratios) > 0.7

    def _is_solid_color_background(self, image: Image.Image) -> bool:
        """检测是否为纯色背景"""
        img = image.convert('RGB')
        arr = np.array(img)

        h, w = arr.shape[:2]
        edge_size = min(h, w) // 10

        # 检查边缘颜色方差
        edges = [
            arr[:edge_size, :],  # 上
            arr[-edge_size:, :],  # 下
            arr[:, :edge_size],  # 左
            arr[:, -edge_size:],  # 右
        ]

        variances = []
        for edge in edges:
            if edge.size > 0:
                # 计算颜色方差
                variance = np.var(edge, axis=(0, 1))
                variances.append(np.mean(variance))

        # 方差小说明是纯色
        return len(variances) > 0 and np.mean(variances) < self.color_variance_threshold

    def _is_fashion_image(self, image: Image.Image) -> bool:
        """检测是否为服装/模特图"""
        # 通过肤色检测和人体轮廓粗略判断
        img = image.convert('RGB')
        arr = np.array(img)

        # 简单肤色检测 (RGB范围)
        skin_lower = np.array([150, 100, 80])
        skin_upper = np.array([255, 200, 180])

        skin_mask = (
            (arr[:, :, 0] >= skin_lower[0]) & (arr[:, :, 0] <= skin_upper[0]) &
            (arr[:, :, 1] >= skin_lower[1]) & (arr[:, :, 1] <= skin_upper[1]) &
            (arr[:, :, 2] >= skin_lower[2]) & (arr[:, :, 2] <= skin_upper[2])
        )

        skin_ratio = np.sum(skin_mask) / skin_mask.size

        # 如果有一定比例的肤色像素，可能是人物/模特图
        return 0.05 < skin_ratio < 0.4

    def _is_food_image(self, image: Image.Image) -> bool:
        """检测是否为食品图"""
        # 食品通常有丰富的暖色调
        img = image.convert('RGB')
        arr = np.array(img)

        # 计算颜色分布
        r_mean = np.mean(arr[:, :, 0])
        g_mean = np.mean(arr[:, :, 1])
        b_mean = np.mean(arr[:, :, 2])

        # 食品图通常偏暖色 (红/橙/黄)
        is_warm = r_mean > g_mean and r_mean > b_mean
        has_good_saturation = np.std(arr) > 40

        return is_warm and has_good_saturation

    def _is_electronics_image(self, image: Image.Image) -> bool:
        """检测是否为电子产品图"""
        # 电子产品通常有金属光泽、冷色调、高对比度
        img = image.convert('RGB')
        arr = np.array(img)

        # 转换为灰度检查对比度
        gray = np.mean(arr, axis=2)
        contrast = np.std(gray)

        # 电子产品通常有高对比度和冷色调
        b_mean = np.mean(arr[:, :, 2])
        r_mean = np.mean(arr[:, :, 0])

        is_cool_toned = b_mean > r_mean * 0.9
        has_high_contrast = contrast > 50

        return is_cool_toned and has_high_contrast

    def _is_lifestyle_image(self, image: Image.Image) -> bool:
        """检测是否为场景图/生活方式图"""
        # 场景图通常有丰富的颜色变化
        img = image.convert('RGB')
        arr = np.array(img)

        # 颜色复杂度
        color_complexity = np.std(arr)

        # 场景图通常颜色丰富
        return color_complexity > 60


def detect_scene(image_path: str) -> str:
    """
    快捷函数：检测图片场景

    Returns:
        str: 场景类型名称
    """
    detector = SceneDetector()
    scene = detector.detect(image_path)
    return scene.value
