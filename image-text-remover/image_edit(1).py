import requests
import json
import base64
import os

API_KEY = "sk-gNcpfR60ul6itd6TU7OnP2TIxBlOYXvRa77WIsKSCFTT6in6"
API_BASE = "https://own-jarvis-api.com"

image_dir = r'C:\Users\Fed\Desktop\图片接口\图片'
image_files = [
    '微信图片_20260424180008_1627_291.jpg',
    '微信图片_20260424180011_1628_291.jpg',
    '微信图片_20260424180017_1629_291.jpg',
]

# 构建多图片文件列表
files = []
for img_name in image_files:
    img_path = os.path.join(image_dir, img_name)
    files.append(('image', (img_name, open(img_path, 'rb'), 'image/jpeg')))

data = {
    'prompt': '将图片中的五个人物做成史诗级IP海报',
    'model': 'gpt-image-2',
    'n': '1',
    'size': '1024x1536',
}

headers = {
    'Authorization': f'Bearer {API_KEY}',
}

response = requests.post(
    f'{API_BASE}/v1/images/edits',
    headers=headers,
    data=data,
    files=files,
)

# 关闭文件句柄
for _, f_tuple in files:
    f_tuple[1].close()

result = response.json()

if "data" in result and len(result["data"]) > 0:
    for i, item in enumerate(result["data"]):
        if "b64_json" in item:
            img_data = base64.b64decode(item["b64_json"])
            out_path = os.path.join(image_dir, f"output_{i}.png")
            with open(out_path, 'wb') as f:
                f.write(img_data)
            print(f"图片已保存: {out_path}")
        elif "url" in item:
            print(f"图片URL: {item['url']}")
    print("生成完成!")
else:
    print("响应内容:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
