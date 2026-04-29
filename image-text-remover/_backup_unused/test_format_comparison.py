#!/usr/bin/env python3
"""
对比测试 - 检查请求格式差异
"""

import requests
import json
import base64
import io
from pathlib import Path
from PIL import Image, ImageDraw

def create_test_request():
    """创建测试请求"""
    # 创建测试图片
    img = Image.new('RGB', (400, 300), color='white')
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 50, 350, 150], fill='lightblue', outline='blue', width=2)
    draw.text((100, 90), "TEST TEXT", fill='black')

    # 转换为 base64
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=95)
    buffer.seek(0)
    image_bytes = buffer.getvalue()
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')

    # 请求数据（简化测试中成功的格式）
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

    return request_data, image_base64

def test_adaptor_format():
    """测试适配器中的请求格式"""
    print("=" * 60)
    print("测试适配器请求格式")
    print("=" * 60)

    API_KEY = "sk-OYgGPxBYShs7halE6A2dZR8iaOgRrIoNZqqpGqCzG5upijVl"
    url = "https://linkapi.ai/v1beta/models/gemini-2.5-flash-image:generateContent"

    request_data, image_base64 = create_test_request()

    headers = {
        "x-goog-api-key": API_KEY,
        "Content-Type": "application/json"
    }

    print("请求数据结构:")
    print(json.dumps(request_data, indent=2, ensure_ascii=False)[:500] + "...")

    try:
        response = requests.post(url, headers=headers, json=request_data, timeout=60)
        print(f"\n状态码: {response.status_code}")

        if response.ok:
            data = response.json()
            print("[OK] 请求成功！")
            print(f"完成原因: {data.get('candidates', [{}])[0].get('finishReason')}")

            # 检查是否有图片
            parts = data.get('candidates', [{}])[0].get('content', {}).get('parts', [])
            for i, part in enumerate(parts):
                if 'inlineData' in part:
                    print(f"[OK] 找到图片数据 in part {i}")
                    return True
        else:
            print(f"[ERROR] 请求失败: {response.status_code}")
            try:
                error_data = response.json()
                print(f"错误信息: {error_data}")
            except:
                print(f"原始响应: {response.text[:500]}")

    except Exception as e:
        print(f"[ERROR] 异常: {e}")

    return False

if __name__ == "__main__":
    success = test_adaptor_format()
    print(f"\n测试结果: {'成功' if success else '失败'}")