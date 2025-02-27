import os
import re
import markdown2
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import boto3
import datetime
import time
from botocore.client import Config
from botpy.ext.cog_yaml import read


# 从配置文件读取 config.yaml，配置 R2 连接信息
test_config = read(os.path.join(os.path.dirname(__file__), "config.yaml"))
R2_ENDPOINT = test_config["R2_ENDPOINT"]
R2_ACCESS_KEY = test_config["R2_ACCESS_KEY"]
R2_SECRET_KEY = test_config["R2_SECRET_KEY"]
R2_BUCKET_NAME = test_config["R2_BUCKET_NAME"]
R2_REGION = test_config["R2_REGION"]

current_dir = os.path.dirname(__file__)
CHROMEDRIVER_PATH = os.path.join(current_dir, "resources", "chromedriver.exe")
KATEX_DIR = os.path.join(current_dir, "resources", "katex")
OUTPUT_IMAGE = os.path.join(current_dir, "cache", "output.png")
FIRACODE_DIR = os.path.join(current_dir, "resources", "fonts", "FiraCode-Regular.ttf")
HARMONY_DIR = os.path.join(current_dir, "resources", "fonts", "HarmonyOS_Sans_SC_Regular.ttf")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Render Markdown and Math</title>
    <link rel="stylesheet" href="{katex_css}">
    <script src="{katex_js}"></script>
    <style>
        @font-face {{
            font-family: "Fira Code";
            src: url(FIRACODE_DIR) format("truetype");
            font-weight: normal;
            font-style: normal;
        }}
        @font-face {{
            font-family: "Harmony Sans";
            src: url(HARMONY_DIR) format("truetype");
            font-weight: normal;
            font-style: normal;
        }}
        body {{
            font-family: "Harmony Sans", "Liberation Sans", "WenQuanYi Zen Hei", "Noto Sans CJK SC", sans-serif;
            line-height: 1.6;
            font-size: 18px;
            margin: 20px;
            color: #333;
            background: white;
        }}
        .math {{
            font-size: 1.2em;
            color: #333;
            font-family: "STIX Math", "Latin Modern Math", "STIX", "DejaVu Math TeX Gyre", serif;
        }}
        pre code {{
            background-color: #f4f4f4;
            padding: 10px;
            border-radius: 5px;
            font-family: "Fira Code", monospace;
            font-size: 14px;
            display: block;
        }}
        h1 {{
            font-size: 2.5em;
            color: #ffffff;
            background-color: #0078d7;
            padding: 10px 20px;
            border-radius: 5px;
        }}
        h2 {{
            font-size: 2em;
            color: #444;
            background-color: #f0f0f0;
            padding: 8px 15px;
            border-radius: 5px;
        }}
        /* 新增表格样式 */
        table {{
            border-collapse: collapse;
            margin: 1.5rem 0;
            width: 100%;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12);
        }}
        th {{
            background-color: #0078d7;
            color: white;
            font-weight: 600;
            padding: 12px 15px;
            text-align: left;
        }}
        td {{
            padding: 10px 15px;
            border-bottom: 1px solid #e0e0e0;
        }}
        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        tr:hover {{
            background-color: #f1f1f1;
        }}
        @media (max-width: 768px) {{
            table {{
                display: block;
                overflow-x: auto;
            }}
        }}
    </style>
</head>
<body>
    <div id="content">
        {content}
    </div>
    <script>
        document.querySelectorAll('.math').forEach(el => {{
            katex.render(el.textContent, el, {{ 
                throwOnError: false,
                displayMode: el.classList.contains('display-math')
            }});
        }});
    </script>
</body>
</html>
"""

s3_client = boto3.client(
    's3',
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY,
    config=Config(signature_version='s3v4'),
    region_name="auto"
)


def load_response():
    try:
        with open("response_output.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "请先创建测试文件 response_output.txt"


def process_math_formulas(html_content):
    # 处理公式
    html_content = re.sub(r'\\\[(.+?)\\\]', r'<span class="math display-math">\1</span>', html_content, flags=re.DOTALL)
    html_content = re.sub(r'\\\((.+?)\\\)', r'<span class="math inline-math">\1</span>', html_content)
    html_content = re.sub(r'\$\$(.+?)\$\$', r'<span class="math display-math">\1</span>', html_content, flags=re.DOTALL)
    html_content = re.sub(r'\$(.+?)\$', r'<span class="math inline-math">\1</span>', html_content)

    return html_content


def generate_image_from_html(html_content, output_path):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--force-color-profile=srgb")

    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # 生成调试文件
    with open("debug.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    driver.get(f"file://{os.path.abspath('debug.html')}")

    # 计算合适的高度并截图
    height = driver.execute_script("return document.body.scrollHeight")
    driver.set_window_size(1200, height + 10)
    driver.execute_script("document.body.style.background = 'white';")

    # 等待渲染完成
    time.sleep(1)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    driver.save_screenshot(output_path)
    driver.quit()

    print(f"图片已生成: {output_path}")


def upload_file_and_get_url(file_path, object_name):
    try:
        s3_client.upload_file(file_path, R2_BUCKET_NAME, object_name)
        return f"{R2_REGION}{object_name}" # 替换为你的R2域名
    except Exception as e:
        print(f"上传失败: {e}")
        return None


def generate_pic_url(text, output_image_path, env):
    # 处理Markdown转换
    processed_text = process_math_formulas(text)
    
    html_content = markdown2.markdown(
        processed_text,
        extras=["fenced-code-blocks", "tables"]
    )


    # 生成完整HTML
    full_html = HTML_TEMPLATE.format(
        katex_css=f"file://{os.path.abspath(os.path.join(KATEX_DIR, 'katex.min.css'))}",
        katex_js=f"file://{os.path.abspath(os.path.join(KATEX_DIR, 'katex.min.js'))}",
        content=html_content
    )

    # 生成图片
    generate_image_from_html(full_html, output_image_path)

    # 处理上传逻辑
    current_time = datetime.datetime.now().strftime("%Y.%m.%d.%H:%M:%S.%f")
    object_name = f"uploads/{current_time}.png"

    return upload_file_and_get_url(output_image_path, object_name) if env == "group" else output_image_path


if __name__ == "__main__":
    # 测试用例
    markdown_text = load_response()
    output_path = os.path.join(current_dir, "cache", "test_output.png")
    generate_pic_url(markdown_text, output_path, "test")