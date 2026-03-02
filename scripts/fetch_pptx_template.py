#!/usr/bin/env python3
"""
从指定 URL 下载 .pptx 模板并保存到 data/templates/。
用法: python scripts/fetch_pptx_template.py <url> [filename]
示例: python scripts/fetch_pptx_template.py "https://github.com/onocom/powerpoint-template/raw/master/powerpoint-template.pptx" professional.pptx
"""
import sys
from pathlib import Path

try:
    import urllib.request
except ImportError:
    import urllib as urllib  # type: ignore

def main():
    if len(sys.argv) < 2:
        print("用法: fetch_pptx_template.py <url> [filename]")
        sys.exit(1)
    url = sys.argv[1].strip()
    if len(sys.argv) >= 3:
        name = sys.argv[2].strip()
        if not name.endswith(".pptx"):
            name += ".pptx"
    else:
        name = "downloaded_template.pptx"
    root = Path(__file__).resolve().parent.parent
    out_dir = root / "data" / "templates"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / name
    print(f"正在下载: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "ClawBot/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    out_path.write_bytes(data)
    print(f"已保存: {out_path} ({len(data)} bytes)")
    if name != "pptx_template.pptx":
        print("提示: 若要用作默认模板，请复制为 pptx_template.pptx")

if __name__ == "__main__":
    main()
