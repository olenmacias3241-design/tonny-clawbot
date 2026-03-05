"""根据文案生成海报图片：设计感、立体感、重点突出，而非简单文字堆砌。"""

import io
import uuid
from pathlib import Path
from typing import Optional, Tuple

from src.utils.config import get_settings
from src.utils.logger import log

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
except ImportError:
    Image = ImageDraw = ImageFont = ImageFilter = None


def _generated_dir() -> Path:
    root = Path(__file__).resolve().parent.parent.parent
    d = root / "data" / "generated"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _cjk_font_path() -> Optional[Path]:
    """返回可用于中文的字体路径，优先系统常见中文字体。"""
    candidates = []
    root = Path(__file__).resolve().parent.parent.parent
    # 项目内可选字体目录
    local_fonts = root / "data" / "fonts"
    if local_fonts.is_dir():
        for ext in ("ttf", "ttc", "otf"):
            for p in local_fonts.glob(f"*.{ext}"):
                candidates.append(p)
    # 常见系统路径（macOS / Linux / Windows）
    system_paths = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Supplemental/Songti.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
    ]
    for p in system_paths:
        candidates.append(Path(p))
    for p in candidates:
        if p.is_file():
            return p
    return None


def _wrap_text(lines: list, max_chars_per_line: int) -> list:
    """将多行文本按每行最多 max_chars_per_line 字换行。"""
    out = []
    for line in lines:
        line = (line or "").strip()
        if not line:
            continue
        while len(line) > max_chars_per_line:
            out.append(line[:max_chars_per_line])
            line = line[max_chars_per_line:]
        if line:
            out.append(line)
    return out if out else [""]


def _get_font(font_path: Optional[Path], size: int):
    if font_path:
        try:
            return ImageFont.truetype(str(font_path), size)
        except Exception:
            pass
    return ImageFont.load_default()


def _poster_text_trim(text: str, max_title_chars: int = 16, max_body_lines: int = 2, max_body_chars_per_line: int = 18):
    """海报只放标题一行 + 副文案最多 2 行，避免文字堆砌。返回 (title_str, body_lines_list)。"""
    raw = (text or "").replace("\r", "\n").strip()
    lines = [ln.strip() for ln in raw.split("\n") if ln.strip()]
    if not lines:
        return ("", [])
    first = lines[0]
    title = (first[: max_title_chars - 1] + "…") if len(first) > max_title_chars else first
    body = []
    rest = "\n".join(lines[1:]).replace("\n", "")
    for _ in range(max_body_lines):
        if not rest:
            break
        if len(rest) <= max_body_chars_per_line:
            body.append(rest)
            break
        body.append(rest[:max_body_chars_per_line] + "…")
        rest = rest[max_body_chars_per_line:]
    return (title, body)


def _draw_poster_pillow_only(
    text: str,
    style: Optional[str],
    width: int = 1024,
    height: int = 1024,
) -> bytes:
    """纯 Pillow：径向背景 + 大标题/副文案 + 强阴影与风格化强调色。"""
    if Image is None or ImageDraw is None:
        raise RuntimeError("请安装 Pillow: pip install Pillow")

    title_str, body_lines = _poster_text_trim(text)
    if not title_str and not body_lines:
        title_str = "海报"

    palettes = {
        "anime": {"bg1": (25, 20, 50), "bg2": (80, 40, 100), "accent": (255, 120, 180), "card": (35, 28, 55, 240)},
        "acg": {"bg1": (20, 25, 50), "bg2": (60, 70, 130), "accent": (100, 220, 255), "card": (30, 35, 60, 238)},
        "cyberpunk": {"bg1": (15, 10, 30), "bg2": (40, 20, 80), "accent": (0, 255, 200), "card": (25, 18, 45, 235)},
        "gufeng": {"bg1": (40, 32, 28), "bg2": (80, 60, 50), "accent": (200, 180, 120), "card": (55, 45, 40, 240)},
        "sci-fi": {"bg1": (10, 18, 35), "bg2": (30, 50, 90), "accent": (120, 200, 255), "card": (22, 35, 55, 238)},
        "healing": {"bg1": (50, 45, 65), "bg2": (120, 100, 140), "accent": (255, 200, 220), "card": (70, 62, 85, 242)},
        "shounen": {"bg1": (45, 15, 15), "bg2": (100, 40, 30), "accent": (255, 180, 60), "card": (60, 35, 35, 240)},
    }
    pal = palettes.get((style or "").strip().lower()) or {"bg1": (18, 22, 38), "bg2": (50, 58, 90), "accent": (78, 186, 255), "card": (28, 35, 52, 240)}

    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)
    cx, cy = width // 2, height // 2
    max_r = (width * width + height * height) ** 0.5 / 2
    step = 8
    for y in range(0, height, step):
        for x in range(0, width, step):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            t = min(1.0, d / max_r) ** 1.2
            r = int(pal["bg1"][0] + (pal["bg2"][0] - pal["bg1"][0]) * (1 - t))
            g = int(pal["bg1"][1] + (pal["bg2"][1] - pal["bg1"][1]) * (1 - t))
            b = int(pal["bg1"][2] + (pal["bg2"][2] - pal["bg1"][2]) * (1 - t))
            draw.rectangle([x, y, x + step, y + step], fill=(r, g, b))
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for y in range(height):
        a = int(55 * (0.2 + 0.8 * y / height))
        od.line([(0, y), (width, y)], fill=(0, 0, 0, a))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    font_path = _cjk_font_path()
    title_size, body_size = 56 if font_path else 58, 28 if font_path else 30
    font_title, font_body = _get_font(font_path, title_size), _get_font(font_path, body_size)
    try:
        bbox_t = draw.textbbox((0, 0), title_str, font=font_title)
        tw = bbox_t[2] - bbox_t[0]
    except Exception:
        tw = len(title_str) * title_size
    body_w = 0
    for line in body_lines:
        try:
            b = draw.textbbox((0, 0), line, font=font_body)
            body_w = max(body_w, b[2] - b[0])
        except Exception:
            body_w = max(body_w, len(line) * body_size)
    block_w = int(max(tw, body_w) + 100)
    line_ht = int(body_size * 1.5)
    block_h = int(title_size * 1.5 + len(body_lines) * line_ht + 60)
    card_x0 = (width - block_w) // 2
    card_y0 = (height - block_h) // 2
    card_x1, card_y1 = card_x0 + block_w, card_y0 + block_h

    shadow_img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow_img)
    for off in [16, 12, 8, 4]:
        sd.rounded_rectangle([card_x0 + off, card_y0 + off, card_x1 + off, card_y1 + off], radius=28, fill=(0, 0, 0, 35))
    img = Image.alpha_composite(img.convert("RGBA"), shadow_img).convert("RGB")
    draw = ImageDraw.Draw(img)
    card_surf = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card_surf)
    cr, cg, cb = pal["card"][0], pal["card"][1], pal["card"][2]
    ca = pal["card"][3] if len(pal["card"]) > 3 else 240
    cd.rounded_rectangle([card_x0, card_y0, card_x1, card_y1], radius=28, fill=(cr, cg, cb, ca), outline=(min(255, cr + 50), min(255, cg + 50), min(255, cb + 50)), width=2)
    img = Image.alpha_composite(img.convert("RGBA"), card_surf).convert("RGB")
    draw = ImageDraw.Draw(img)

    ac = pal["accent"]
    draw.rectangle([card_x0 + 24, card_y0 + 24, card_x0 + 32, card_y1 - 24], fill=ac)
    try:
        bbox_t = draw.textbbox((0, 0), title_str, font=font_title)
        title_w = bbox_t[2] - bbox_t[0]
    except Exception:
        title_w = len(title_str) * title_size
    line_x0, line_x1 = card_x0 + 48, card_x0 + 48 + min(title_w + 20, block_w - 96)
    draw.rectangle([line_x0, card_y0 + 28 + int(title_size * 1.2), line_x1, card_y0 + 32 + int(title_size * 1.2)], fill=ac)

    tx0, ty0 = card_x0 + 52, card_y0 + 32
    for dx, dy in [(-2, -2), (-2, 2), (2, -2), (2, 2), (0, -2), (0, 2), (-2, 0), (2, 0)]:
        draw.text((tx0 + dx, ty0 + dy), title_str, fill=(0, 0, 0), font=font_title)
    draw.text((tx0, ty0), title_str, fill=(255, 255, 255), font=font_title)
    y_cur = card_y0 + 32 + int(title_size * 1.45)
    for line in body_lines:
        if line:
            draw.text((card_x0 + 52, y_cur), line, fill=(220, 220, 230), font=font_body)
            y_cur += line_ht

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


async def _fetch_dalle_background(style: Optional[str]) -> Optional[bytes]:
    """若为原生 OpenAI API，则调用 DALL-E 生成海报背景图，返回 PNG 字节；否则返回 None。"""
    settings = get_settings()
    if not settings.openai_api_key:
        return None
    if settings.openai_api_key.startswith("sk-or-") or settings.openai_api_key.startswith("gsk_"):
        return None  # OpenRouter / Groq 不支持 Images API

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        style_desc = {
            "anime": "Japanese anime style poster, vibrant colors, dynamic composition, depth and layers",
            "acg": "ACG / anime game style poster, bright, catchy, with visual hierarchy and focal point",
            "cyberpunk": "Cyberpunk poster, neon lights, dark city, futuristic, strong depth and atmosphere",
            "gufeng": "Chinese traditional poster, ink painting style, elegant, minimal, subtle depth",
            "sci-fi": "Science fiction poster, space or tech, clean, modern, layered composition",
            "healing": "Healing style poster, soft, warm, pastel colors, cozy depth and layers",
            "shounen": "Shounen anime poster, energetic, bold colors, dynamic depth and impact",
        }.get((style or "").strip().lower(), "modern minimalist")

        prompt = (
            f"Advertisement or marketing poster image, {style_desc}. "
            "Single strong focal point, bold shapes or abstract decorative elements, "
            "clear center area left empty for text (no letters or words). "
            "Professional graphic design, high contrast, 1024x1024."
        )
        resp = await client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            response_format="b64_json",
            n=1,
        )
        if not resp.data or not resp.data[0].b64_json:
            return None
        import base64
        return base64.b64decode(resp.data[0].b64_json)
    except Exception as e:
        log.warning(f"DALL-E background failed: {e}")
        return None


def _overlay_text_on_image(image_bytes: bytes, text: str, style: Optional[str] = None) -> bytes:
    """在 DALL-E 图上叠加：标题+最多2行副文案 + 半透明卡片 + 强调条。"""
    if Image is None or ImageDraw is None:
        raise RuntimeError("请安装 Pillow: pip install Pillow")

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    width, height = img.size
    title_str, body_lines = _poster_text_trim(text)
    if not title_str and not body_lines:
        title_str = "海报"

    font_path = _cjk_font_path()
    title_size = min(56, max(36, width // 18))
    body_size = min(32, max(20, width // 28))
    font_title = _get_font(font_path, title_size)
    font_body = _get_font(font_path, body_size)
    draw_temp = ImageDraw.Draw(img)
    try:
        bbox_t = draw_temp.textbbox((0, 0), title_str, font=font_title)
        tw = bbox_t[2] - bbox_t[0]
    except Exception:
        tw = len(title_str) * title_size
    body_w = 0
    line_heights = []
    for line in body_lines:
        try:
            b = draw_temp.textbbox((0, 0), line, font=font_body)
            body_w = max(body_w, b[2] - b[0])
        except Exception:
            body_w = max(body_w, len(line) * body_size)
        line_heights.append(body_size * 1.4)
    total_h = int(title_size * 1.5 + sum(line_heights) + 52)
    block_w = int(max(tw, body_w) + 80)
    block_h = total_h
    card_x0 = (width - block_w) // 2
    card_y0 = (height - block_h) // 2
    card_x1, card_y1 = card_x0 + block_w, card_y0 + block_h
    ac = (100, 200, 255)
    if style:
        accents = {"anime": (255, 120, 180), "acg": (100, 220, 255), "cyberpunk": (0, 255, 200), "gufeng": (200, 180, 120), "sci-fi": (120, 200, 255), "healing": (255, 200, 220), "shounen": (255, 180, 60)}
        ac = accents.get(style.strip().lower(), ac)
    shadow_img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow_img)
    for off in [14, 10, 6]:
        sd.rounded_rectangle([card_x0 + off, card_y0 + off, card_x1 + off, card_y1 + off], radius=22, fill=(0, 0, 0, 40))
    img = Image.alpha_composite(img.convert("RGBA"), shadow_img).convert("RGB")
    draw = ImageDraw.Draw(img)
    card_surf = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card_surf)
    cd.rounded_rectangle([card_x0, card_y0, card_x1, card_y1], radius=22, fill=(18, 22, 38, 228), outline=(60, 75, 100), width=2)
    img = Image.alpha_composite(img.convert("RGBA"), card_surf).convert("RGB")
    draw = ImageDraw.Draw(img)
    draw.rectangle([card_x0 + 20, card_y0 + 20, card_x0 + 28, card_y1 - 20], fill=ac)
    try:
        bbox_t = draw.textbbox((0, 0), title_str, font=font_title)
        title_w = bbox_t[2] - bbox_t[0]
    except Exception:
        title_w = len(title_str) * title_size
    draw.rectangle([card_x0 + 44, card_y0 + 24 + int(title_size * 1.15), card_x0 + 44 + min(title_w + 16, block_w - 88), card_y0 + 28 + int(title_size * 1.15)], fill=ac)
    tx0, ty0 = card_x0 + 48, card_y0 + 24
    for dx, dy in [(-2, -2), (-2, 2), (2, -2), (2, 2), (0, -2), (0, 2), (-2, 0), (2, 0)]:
        draw.text((tx0 + dx, ty0 + dy), title_str, fill=(0, 0, 0), font=font_title)
    draw.text((tx0, ty0), title_str, fill=(255, 255, 255), font=font_title)
    y_cur = card_y0 + 24 + int(title_size * 1.45)
    for i, line in enumerate(body_lines):
        if line:
            draw.text((card_x0 + 48, y_cur), line, fill=(230, 230, 240), font=font_body)
            y_cur += line_heights[i] if i < len(line_heights) else body_size * 1.4
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


async def generate_poster(copy_text: str, style: Optional[str] = None) -> Tuple[str, bytes]:
    """
    根据文案生成海报图。优先尝试 DALL-E 背景 + 叠字，失败则用纯 Pillow 渐变 + 文案。
    返回 (filename, png_bytes)。
    """
    copy_text = (copy_text or "").strip()
    if not copy_text:
        raise ValueError("文案内容不能为空")

    bg_bytes = await _fetch_dalle_background(style)
    if bg_bytes:
        png_bytes = _overlay_text_on_image(bg_bytes, copy_text, style=style)
    else:
        png_bytes = _draw_poster_pillow_only(copy_text, style)

    name = f"poster_{uuid.uuid4().hex[:12]}.png"
    path = _generated_dir() / name
    path.write_bytes(png_bytes)
    log.info(f"Poster saved: {path}")
    return name, png_bytes
