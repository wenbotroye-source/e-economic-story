#!/usr/bin/env python3
"""
简化测试 LinkAPI.ai API 连接
"""

import requests
import json
import base64
import io
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def test_linkapi_connection():
    """测试 LinkAPI.ai API 连接"""
    print("=" * 60)
    print("测试 LinkAPI.ai API 连接")
    print("=" * 60)

    # API 配置
    API_KEY = "sk-OYgGPxBYShs7halE6A2dZR8iaOgRrIoNZqqpGqCzG5upijVl"
    BASE_URL = "https://linkapi.ai"
    MODEL = "gemini-2.5-flash-image"
    ENDPOINT = f"/v1beta/models/{MODEL}:generateContent"

    # 创建测试图片
    print("1. 创建测试图片...")
    img = Image.new('RGB', (400, 300), color='white')
    draw = ImageDraw.Draw(img)
    # 添加一些简单的图形和文字
    draw.rectangle([50, 50, 350, 150], fill='lightblue', outline='blue', width=2)
    draw.text((100, 90), "TEST TEXT", fill='black')
    img_path = Path("test_input.jpg")
    img.save(img_path)
    print(f"   测试图片已创建: {img_path}")

    # 转换为 base64
    print("2. 转换图片为 base64...")
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=95)
    buffer.seek(0)
    image_bytes = buffer.getvalue()
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
    print(f"   Base64长度: {len(image_base64)} 字符")

    # 构造请求
    print("3. 构造 API 请求...")
    url = f"{BASE_URL}{ENDPOINT}"

    # 尝试不同的请求格式
    request_data = {
        "contents": [{
            "role": "user",
            "parts": [
                {
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": image_base64
                    }
                },
                {
                    "text": "Remove text from image"
                }
            ]
        }],
        "generationConfig": {
            "responseModalities": ["IMAGE"]
        }
    }

    headers = {
        "x-goog-api-key": API_KEY,
        "Content-Type": "application/json"
    }

    print(f"   URL: {url}")
    print(f"   请求数据大小: {len(json.dumps(request_data))} 字符")

    # 发送请求
    print("4. 发送 API 请求...")
    try:
        response = requests.post(url, headers=headers, json=request_data, timeout=60)
        print(f"   状态码: {response.status_code}")

        # 解析响应
        try:
            data = response.json()
            print(f"   响应数据: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}...")
        except:
            print(f"   原始响应: {response.text[:500]}...")

        if response.ok:
            print("   [OK] API 请求成功！")

            # 检查响应内容
            candidates = data.get('candidates', [])
            if candidates:
                content = candidates[0].get('content', {})
                parts = content.get('parts', [])
                finish_reason = candidates[0].get('finishReason')

                print(f"   完成原因: {finish_reason}")
                print(f"   Parts 数量: {len(parts)}")

                # 检查是否有图片返回
                image_found = False
                for i, part in enumerate(parts):
                    print(f"   Part {i}: {list(part.keys())}")
                    if 'inlineData' in part or 'inline_data' in part:
                        image_found = True
                        print(f"   [OK] 找到图片数据！")

                if not image_found and finish_reason == 'NO_IMAGE':
                    print("   [INFO] API 返回 NO_IMAGE，可能输入图片无需处理")
                elif not image_found:
                    print("   [WARNING] 未找到图片数据，但请求成功")
        else:
            print(f"   [ERROR] API 请求失败: {response.status_code}")
            if 'error' in data:
                print(f"   错误信息: {data['error']}")

    except Exception as e:
        print(f"   [ERROR] 请求异常: {e}")
        import traceback
        traceback.print_exc()

    # 清理测试文件
    if img_path.exists():
        img_path.unlink()
        print(f"\n5. 清理测试文件: {img_path}")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_linkapi_connection()