"""生成可直接下载的表格（CSV/Excel）和 PPT（.pptx）。

PPT 设计原则（参照常见优秀模版）：
- 层次清晰：封面主标题 > 页标题 > 正文，字号与字重区分
- 留白充足：边距与段落间距统一，每页要点不超过 6 条
- 配色统一：主色、强调色、正文色、辅助色成体系，与 Excel 表格风格一致
- 可选用参考模板：将优质 .pptx 放入 data/templates/pptx_template.pptx，生成时将沿用其版式与主题
"""

import csv
import io
import json
import re
import sys
from typing import List, Dict, Any, Optional

from src.bot.ai_provider import get_ai_provider
from src.utils.config import get_settings
from src.utils.logger import log

try:
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.enum.text import PP_ALIGN
except ImportError:
    Presentation = Inches = Pt = RGBColor = MSO_SHAPE = PP_ALIGN = None


async def generate_table_data(prompt: str) -> List[Dict[str, str]]:
    """
    根据描述用 AI 生成表格数据，返回 list of dict（每行一个 dict，key 为列名）。
    """
    settings = get_settings()
    provider = get_ai_provider()
    system = """你是专业的表格数据生成助手。根据用户描述生成可直接使用的、高质量的表格数据。

要求：
1. 只输出一个合法的 JSON 数组，不要任何前后说明、不要 markdown 代码块、不要 ```。
2. 数组每个元素是一个对象，键为列名（中文或英文），值为该单元格的字符串或数字。同一列的类型必须一致（全是数字或全是字符串）。
3. 数据要真实、合理、多样：
   - 姓名/人名：使用多样化的中文姓名（如张三、李四、王芳、陈明等），不要重复或敷衍的“用户1、测试”。
   - 分数/成绩：在合理区间内（如 0–100），总分、平均分要按行正确计算。
   - 金额/数量：使用合理的整数或一位小数，单位与列名一致。
   - 日期：格式统一，如 2024-01-15 或 2024/1/15。
   - 部门/类别：与业务场景一致，如技术、产品、销售、市场等，多几类不要全一样。
4. 行数：一般 5–12 行；若用户明确要求“很多”或“大量”可生成 15–20 行。至少 5 行。
5. 列名清晰，与用户描述一致；若有“总分”“平均分”等，必须用数字填好并保证计算正确。

示例格式（仅作结构参考，请按用户描述生成实际内容）：
[{"姓名":"张三","部门":"技术","成绩":85},{"姓名":"李四","部门":"产品","成绩":92}]"""
    user = f"按下面描述生成表格，只输出一个 JSON 数组，不要其他任何文字：\n{prompt}"
    try:
        raw = await provider.generate_response(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.3,
            max_tokens=4000,
        )
        raw = raw.strip()
        # 去掉可能的 markdown 包裹
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
        if m:
            raw = m.group(1).strip()
        # 尝试直接找 [...] 段
        arr = re.search(r"\[[\s\S]*\]", raw)
        if arr:
            raw = arr.group(0)
        data = json.loads(raw)
        if not isinstance(data, list) or not data:
            raise ValueError("AI 未返回有效表格数组")
        if not isinstance(data[0], dict):
            raise ValueError("表格每行应为对象")
        return data
    except json.JSONDecodeError as e:
        log.error(f"Table JSON parse error: {e}, raw: {raw[:200]}")
        raise ValueError("生成内容不是有效 JSON，请重试或换一种描述") from e


def table_to_csv(rows: List[Dict[str, str]]) -> str:
    """将 list of dict 转为 CSV 字符串（UTF-8，含 BOM 便于 Excel 识别）。"""
    if not rows:
        return ""
    out = io.StringIO()
    out.write("\ufeff")  # BOM for Excel
    writer = csv.DictWriter(out, fieldnames=list(rows[0].keys()), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


def table_to_xlsx(rows: List[Dict[str, str]]) -> bytes:
    """将 list of dict 转为带样式的 .xlsx（表头加粗/底色、边框、列宽、斑马纹）。"""
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
        from openpyxl.utils import get_column_letter
    except ImportError:
        raise RuntimeError("请安装 openpyxl: pip install openpyxl")
    wb = openpyxl.Workbook()
    ws = wb.active
    if not rows:
        return io.BytesIO().getvalue()
    headers = list(rows[0].keys())
    # 表头样式：深灰底、白字、加粗、居中
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    thin = Side(style="thin", color="B4B4B4")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    # 表头行
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.border = border
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    # 数据行 + 斑马纹
    light_fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
    for r, row in enumerate(rows, 2):
        for c, h in enumerate(headers, 1):
            cell = ws.cell(row=r, column=c, value=row.get(h, ""))
            cell.border = border
            if (r - 2) % 2 == 1:
                cell.fill = light_fill
            cell.alignment = Alignment(vertical="center", wrap_text=True)
    # 冻结首行
    ws.freeze_panes = "A2"
    # 自动列宽（按内容，限制在 8–40 之间）
    for c, h in enumerate(headers, 1):
        col_letter = get_column_letter(c)
        max_w = len(str(h))
        for r in range(2, len(rows) + 2):
            val = rows[r - 2].get(h, "")
            max_w = min(40, max(max_w, len(str(val)) + 1))
        ws.column_dimensions[col_letter].width = max(8, max_w)
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()


def _parse_structured_slides(text: str) -> Optional[Dict[str, Any]]:
    """
    解析「幻灯片1：封面」+ 标题/副标题/日期/姓名，以及「幻灯片N：标题」+ 要点列表。
    成功时返回 {"title", "subtitle", "date_author", "outline"}，否则返回 None。
    """
    if not text or "幻灯片" not in text:
        return None
    blocks = re.split(r"\n```|\n###\s*", text)
    cover_title = None
    cover_subtitle = None
    date_author_parts = []
    outline = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        lines = [ln.strip() for ln in block.split("\n") if ln.strip()]
        if not lines:
            continue
        first = lines[0]
        m = re.match(r"幻灯片\s*\d*\s*[：:]\s*(.+)", first)
        if not m:
            continue
        slide_label = m.group(1).strip()
        rest_lines = lines[1:]
        if "标题：" in block or "标题:" in block:
            for ln in rest_lines:
                if re.match(r"标题\s*[：:]\s*", ln):
                    cover_title = re.sub(r"标题\s*[：:]\s*", "", ln, count=1).strip()
                elif re.match(r"副标题\s*[：:]\s*", ln):
                    cover_subtitle = re.sub(r"副标题\s*[：:]\s*", "", ln, count=1).strip()
                elif re.match(r"日期\s*[：:]\s*", ln):
                    date_author_parts.append("日期：" + re.sub(r"日期\s*[：:]\s*", "", ln, count=1).strip())
                elif re.match(r"姓名\s*[：:]\s*", ln):
                    date_author_parts.append("姓名：" + re.sub(r"姓名\s*[：:]\s*", "", ln, count=1).strip())
            if cover_title and not outline:
                continue
        points = []
        for ln in rest_lines:
            if ln.startswith("- ") or ln.startswith("-"):
                points.append(ln[1:].strip().lstrip("- "))
            elif ln.startswith("• ") or ln.startswith("•"):
                points.append(ln[1:].strip().lstrip("• "))
        if slide_label and (points or ("标题：" not in block and "标题:" not in block)):
            if "封面" in slide_label and (cover_title or cover_subtitle) and not points:
                continue
            outline.append({"title": slide_label, "points": points})
    if not outline and cover_title is None:
        return None
    if cover_title is None and outline:
        cover_title = outline[0].get("title", "汇报")
    date_author = "  |  ".join(date_author_parts) if date_author_parts else None
    return {
        "title": cover_title,
        "subtitle": cover_subtitle or None,
        "date_author": date_author,
        "outline": outline,
    }


async def generate_ppt_outline(title: str, topic: str) -> List[Dict[str, Any]]:
    """
    根据标题和主题用 AI 生成 PPT 大纲，返回 [{"title":"幻灯片标题","points":["要点1","要点2"]}, ...]。
    """
    provider = get_ai_provider()
    system = (
        "你是一个 PPT 大纲助手。用户给出汇报标题和主题，你只输出一个 JSON 数组，不要任何其他文字。"
        "数组的每个元素表示一页幻灯片：{\"title\":\"该页标题\",\"points\":[\"要点1\",\"要点2\",\"要点3\"]}。"
        "通常 5～8 页：封面/目录、背景/现状、分析/方案、数据/案例、总结/下一步等。"
        "只输出 JSON 数组。"
    )
    user = f"汇报标题：{title}\n主题/内容方向：{topic}\n请生成 PPT 大纲（JSON 数组）。"
    try:
        raw = await provider.generate_response(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.4,
            max_tokens=2000,
        )
        raw = raw.strip()
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
        if m:
            raw = m.group(1).strip()
        data = json.loads(raw)
        if not isinstance(data, list) or not data:
            raise ValueError("AI 未返回有效大纲")
        out = []
        for item in data:
            if isinstance(item, dict):
                out.append({
                    "title": str(item.get("title", "幻灯片")),
                    "points": [str(p) for p in item.get("points", []) if p],
                })
            else:
                out.append({"title": "幻灯片", "points": []})
        return out
    except json.JSONDecodeError as e:
        log.error(f"PPT outline JSON parse error: {e}, raw: {raw[:200]}")
        raise ValueError("生成内容不是有效 JSON，请重试") from e


def build_pptx_bytes(
    title: str,
    outline: List[Dict[str, Any]],
    subtitle: Optional[str] = None,
    date_author: Optional[str] = None,
) -> bytes:
    """根据标题和大纲生成 .pptx（内置版式：16:9、现代配色与排版，兼容且美观）。"""
    if Presentation is None:
        try:
            from pptx import Presentation as _P
            from pptx.util import Inches as _I, Pt as _Pt
            from pptx.dml.color import RGBColor as _R
            from pptx.enum.shapes import MSO_SHAPE as _M
            from pptx.enum.text import PP_ALIGN as _A
            globals()["Presentation"] = _P
            globals()["Inches"] = _I
            globals()["Pt"] = _Pt
            globals()["RGBColor"] = _R
            globals()["MSO_SHAPE"] = _M
            globals()["PP_ALIGN"] = _A
        except ImportError:
            raise RuntimeError(
                "未检测到 python-pptx。当前运行 Python："
                + sys.executable
                + " 。请在该环境中执行：pip install python-pptx，然后重启服务。"
            )

    # 16:9 幻灯片尺寸（更现代）
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    template_path = _get_pptx_template_path()
    if template_path:
        try:
            prs = Presentation(str(template_path))
            while len(prs.slides) > 0:
                i = len(prs.slides) - 1
                rId = prs.slides._sldIdLst[i].rId
                prs.part.drop_rel(rId)
                del prs.slides._sldIdLst[i]
            layouts = prs.slide_layouts
            title_lyt = layouts[0]
            content_lyt = layouts[1] if len(layouts) > 1 else layouts[0]
            s0 = prs.slides.add_slide(title_lyt)
            try:
                s0.shapes.title.text = title
            except Exception:
                pass
            if subtitle or date_author:
                sub_text = "\n".join([s for s in (subtitle, date_author) if s])
                try:
                    s0.placeholders[1].text = sub_text
                except (KeyError, IndexError):
                    pass
            for item in outline:
                s = prs.slides.add_slide(content_lyt)
                try:
                    s.shapes.title.text = item.get("title", "")
                except Exception:
                    pass
                points = item.get("points", [])[:6]
                try:
                    body = s.placeholders[1]
                    tf = body.text_frame
                    tf.clear()
                    for i, point in enumerate(points):
                        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
                        p.text = "●  " + (point if isinstance(point, str) else str(point))
                except (KeyError, IndexError):
                    pass
            buf = io.BytesIO()
            prs.save(buf)
            buf.seek(0)
            return buf.read()
        except Exception as e:
            log.warning(f"PPT 参考模板加载失败，改用内置设计: {e}")

    # 现代配色：深色主色 + 单一强调色 + 充足留白
    primary = RGBColor(0x0F, 0x17, 0x2A)      # 深靛蓝 - 主色
    accent = RGBColor(0x0E, 0xA5, 0xE9)       # 天蓝 - 强调
    white = RGBColor(0xFF, 0xFF, 0xFF)
    body_color = RGBColor(0x33, 0x44, 0x55)   # 正文
    muted = RGBColor(0x64, 0x72, 0x85)        # 副标题
    card_bg = RGBColor(0xF8, 0xFA, 0xFC)      # 卡片背景
    card_border = RGBColor(0xE2, 0xE8, 0xF0)  # 细边框
    title_bar_bg = RGBColor(0x1E, 0x29, 0x3B) # 顶条

    FONT_TITLE = "Microsoft YaHei"
    FONT_BODY = "Microsoft YaHei"

    def _set_font(run, size_pt: int, bold: bool = False, color=None):
        try:
            run.font.name = FONT_BODY
            run.font.size = Pt(size_pt)
            run.font.bold = bold
            if color is not None:
                run.font.color.rgb = color
        except Exception:
            pass

    blank = prs.slide_layouts[6]

    # ---------- 封面：左侧竖条 + 大标题 + 副标题，右侧留白 ----------
    slide = prs.slides.add_slide(blank)
    # 左侧竖条（装饰）
    left_bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(0.12), Inches(7.5)
    )
    left_bar.fill.solid()
    left_bar.fill.fore_color.rgb = accent
    left_bar.line.fill.background()
    # 标题区（居中偏左，留白多）
    tx = slide.shapes.add_textbox(Inches(1.2), Inches(2.6), Inches(10.8), Inches(1.6))
    tf = tx.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(44)
    p.font.bold = True
    p.font.color.rgb = primary
    try:
        p.font.name = FONT_TITLE
    except Exception:
        pass
    p.alignment = PP_ALIGN.LEFT
    p.space_after = Pt(16)
    if subtitle or date_author:
        sub_box = slide.shapes.add_textbox(Inches(1.2), Inches(4.4), Inches(10.8), Inches(1.2))
        stf = sub_box.text_frame
        stf.word_wrap = True
        for i, line in enumerate([s for s in (subtitle, date_author) if s]):
            sp = stf.paragraphs[0] if i == 0 else stf.add_paragraph()
            sp.text = line
            sp.font.size = Pt(16)
            sp.font.color.rgb = muted
            try:
                sp.font.name = FONT_BODY
            except Exception:
                pass
            sp.alignment = PP_ALIGN.LEFT
            sp.space_after = Pt(8)
    # 底部细线
    foot_line = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(1.2), Inches(7.0), Inches(2), Pt(2)
    )
    foot_line.fill.solid()
    foot_line.fill.fore_color.rgb = accent
    foot_line.line.fill.background()

    # ---------- 内容页：顶条 + 左竖条 + 标题 + 卡片 + 要点 ----------
    for item in outline:
        slide = prs.slides.add_slide(blank)
        # 顶条
        strip = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.14)
        )
        strip.fill.solid()
        strip.fill.fore_color.rgb = title_bar_bg
        strip.line.fill.background()
        # 标题左侧竖条
        vbar = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(0.5), Pt(4), Inches(0.65)
        )
        vbar.fill.solid()
        vbar.fill.fore_color.rgb = accent
        vbar.line.fill.background()
        # 页标题
        title_box = slide.shapes.add_textbox(Inches(0.85), Inches(0.42), Inches(11.5), Inches(0.9))
        tft = title_box.text_frame
        tft.word_wrap = True
        pt = tft.paragraphs[0]
        pt.text = item.get("title", "")
        pt.font.size = Pt(26)
        pt.font.bold = True
        pt.font.color.rgb = primary
        try:
            pt.font.name = FONT_TITLE
        except Exception:
            pass
        pt.space_after = Pt(4)
        # 内容卡片（圆角、浅底、细边）
        content_bg = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.55), Inches(1.35), Inches(12.2), Inches(5.75)
        )
        content_bg.fill.solid()
        content_bg.fill.fore_color.rgb = card_bg
        content_bg.line.color.rgb = card_border
        content_bg.line.width = Pt(0.5)
        # 要点
        points = item.get("points", [])[:6]
        body_box = slide.shapes.add_textbox(Inches(0.95), Inches(1.65), Inches(11.4), Inches(5.3))
        tfb = body_box.text_frame
        tfb.word_wrap = True
        for i, point in enumerate(points):
            p = tfb.paragraphs[0] if i == 0 else tfb.add_paragraph()
            p.space_before = Pt(18)
            p.space_after = Pt(8)
            r1 = p.add_run()
            r1.text = "  ◆  "
            _set_font(r1, 16, bold=False, color=accent)
            r2 = p.add_run()
            r2.text = point if isinstance(point, str) else str(point)
            _set_font(r2, 17, bold=False, color=body_color)

    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf.read()


def _generated_dir():
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent.parent
    d = root / "data" / "generated"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _get_pptx_template_path():
    """若存在参考模板 data/templates/pptx_template.pptx 则返回其 Path，否则返回 None。"""
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent.parent
    p = root / "data" / "templates" / "pptx_template.pptx"
    return p if p.is_file() else None


async def generate_table_and_save(prompt: str):
    """生成表格并保存为 CSV 和 Excel（若已安装 openpyxl），返回 (csv_name, xlsx_name 或 None)。"""
    import uuid
    log.info("generate_table_and_save: calling AI for table data")
    rows = await generate_table_data(prompt)
    log.info(f"generate_table_and_save: got {len(rows)} rows")
    uid = uuid.uuid4().hex[:12]
    base = _generated_dir()
    csv_name = f"table_{uid}.csv"
    csv_path = base / csv_name
    csv_path.write_text(table_to_csv(rows), encoding="utf-8-sig")
    log.info(f"generate_table_and_save: wrote {csv_path}")
    xlsx_name = None
    try:
        xlsx_name = f"table_{uid}.xlsx"
        (base / xlsx_name).write_bytes(table_to_xlsx(rows))
        log.info(f"generate_table_and_save: wrote xlsx {xlsx_name}")
    except Exception as e:
        log.warning(f"Excel 生成跳过（可安装 openpyxl 后重试）: {e}")
    return csv_name, xlsx_name


async def generate_document_content(prompt: str) -> str:
    """根据用户描述用 AI 生成一篇文档正文（Markdown 格式）。"""
    provider = get_ai_provider()
    system = """你是文档撰写助手。用户会描述想要创建的文档主题或需求，你输出一篇结构清晰、可直接使用的 Markdown 文档正文。
要求：
- 使用 Markdown 语法：标题用 # ## ###，列表用 - 或 1.，段落之间空行。
- 若有标题，文档开头先写一个一级标题概括主题。
- 内容充实、分段合理，长度适中（一般 300～1500 字，按用户需求调整）。
- 只输出文档正文，不要输出「以下是文档」等前言。"""
    user = f"请根据以下描述生成一篇完整的 Markdown 文档：\n\n{prompt}"
    raw = await provider.generate_response(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.4,
        max_tokens=4000,
    )
    return (raw or "").strip()


async def generate_document_and_save(prompt: str) -> str:
    """生成文档并保存为 .md，返回文件名。"""
    import uuid
    log.info("generate_document_and_save: calling AI for document content")
    content = await generate_document_content(prompt)
    uid = uuid.uuid4().hex[:12]
    base = _generated_dir()
    name = f"doc_{uid}.md"
    base.joinpath(name).write_text(content, encoding="utf-8")
    log.info(f"generate_document_and_save: wrote {base / name}")
    return name


def _markdown_to_docx_bytes(md_text: str) -> bytes:
    """将 Markdown 文本转为 .docx 字节（标题、段落、列表），中文字体+行距避免乱码与显示不全。"""
    try:
        from docx import Document
        from docx.oxml.ns import qn
        from docx.enum.text import WD_LINE_SPACING
    except ImportError:
        raise RuntimeError("请安装 python-docx: pip install python-docx")
    doc = Document()
    # 中英文统一用同一字体，避免混排时行高不一致导致中文被裁切；宋体在 Windows/macOS 较常见
    cjk_font = "SimSun"  # 宋体

    def set_run_cjk_font(run):
        """设置 run 的 ascii/hAnsi/eastAsia 为同一中文字体，避免显示不全或乱码。"""
        try:
            run.font.name = cjk_font
            rPr = run._element.get_or_add_rPr()
            rFonts = rPr.get_or_add_rFonts()
            rFonts.set(qn("w:eastAsia"), cjk_font)
            rFonts.set(qn("w:ascii"), cjk_font)
            rFonts.set(qn("w:hAnsi"), cjk_font)
        except Exception:
            pass

    def set_style_cjk_font(style):
        try:
            style.font.name = cjk_font
            if style._element.rPr is not None:
                rFonts = style._element.rPr.get_or_add_rFonts()
                rFonts.set(qn("w:eastAsia"), cjk_font)
                rFonts.set(qn("w:ascii"), cjk_font)
                rFonts.set(qn("w:hAnsi"), cjk_font)
        except Exception:
            pass

    def set_paragraph_line_spacing(paragraph, multiplier=1.15):
        """设置段落行距，避免中文上下被裁切。"""
        try:
            paragraph.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
            paragraph.paragraph_format.line_spacing = multiplier
        except Exception:
            pass

    for style_name in ("Normal", "Heading 1", "Heading 2", "Heading 3"):
        if style_name in doc.styles:
            set_style_cjk_font(doc.styles[style_name])

    lines = md_text.split("\n")
    i = 0
    in_ul = False
    in_ol = False
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            if in_ul or in_ol:
                in_ul = in_ol = False
            i += 1
            continue
        if stripped.startswith("###"):
            if in_ul or in_ol:
                in_ul = in_ol = False
            doc.add_heading(stripped.lstrip("#").strip(), level=3)
            para = doc.paragraphs[-1]
            for run in para.runs:
                set_run_cjk_font(run)
            set_paragraph_line_spacing(para, 1.2)
            i += 1
            continue
        if stripped.startswith("##"):
            if in_ul or in_ol:
                in_ul = in_ol = False
            doc.add_heading(stripped.lstrip("#").strip(), level=2)
            para = doc.paragraphs[-1]
            for run in para.runs:
                set_run_cjk_font(run)
            set_paragraph_line_spacing(para, 1.2)
            i += 1
            continue
        if stripped.startswith("#"):
            if in_ul or in_ol:
                in_ul = in_ol = False
            doc.add_heading(stripped.lstrip("#").strip(), level=1)
            para = doc.paragraphs[-1]
            for run in para.runs:
                set_run_cjk_font(run)
            set_paragraph_line_spacing(para, 1.2)
            i += 1
            continue
        if re.match(r"^[\-\*]\s+", stripped) or stripped.startswith("- ") or stripped.startswith("* "):
            text = re.sub(r"^[\-\*]\s+", "", stripped, count=1)
            p = doc.add_paragraph(style="List Bullet")
            r = p.add_run(text)
            set_run_cjk_font(r)
            set_paragraph_line_spacing(p, 1.15)
            in_ul = True
            in_ol = False
            i += 1
            continue
        if re.match(r"^\d+\.\s+", stripped):
            text = re.sub(r"^\d+\.\s+", "", stripped, count=1)
            p = doc.add_paragraph(style="List Number")
            r = p.add_run(text)
            set_run_cjk_font(r)
            set_paragraph_line_spacing(p, 1.15)
            in_ol = True
            in_ul = False
            i += 1
            continue
        in_ul = in_ol = False
        p = doc.add_paragraph(stripped)
        for run in p.runs:
            set_run_cjk_font(run)
        set_paragraph_line_spacing(p, 1.15)
        i += 1
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.read()


async def generate_docx_and_save(prompt: str) -> str:
    """根据用户描述用 AI 生成文档并保存为 .docx，返回文件名。"""
    import uuid
    log.info("generate_docx_and_save: calling AI for document content")
    content = await generate_document_content(prompt)
    docx_bytes = _markdown_to_docx_bytes(content)
    uid = uuid.uuid4().hex[:12]
    base = _generated_dir()
    name = f"word_{uid}.docx"
    (base / name).write_bytes(docx_bytes)
    log.info(f"generate_docx_and_save: wrote {base / name}")
    return name


async def generate_ppt_and_save(title: str, topic: str):
    """根据标题和主题用 AI 生成大纲并保存 .pptx。"""
    import uuid
    outline = await generate_ppt_outline(title, topic)
    content = build_pptx_bytes(title, outline)
    uid = uuid.uuid4().hex[:12]
    base = _generated_dir()
    name = f"ppt_{uid}.pptx"
    (base / name).write_bytes(content)
    return name


def generate_ppt_from_structured_text(text: str) -> Optional[str]:
    """
    若文本为「幻灯片1：封面」+ 标题/副标题/日期/姓名 及 幻灯片N + 要点 的格式，则解析并生成 .pptx，返回文件名；否则返回 None。
    """
    parsed = _parse_structured_slides(text)
    if not parsed or not parsed.get("outline"):
        return None
    import uuid
    content = build_pptx_bytes(
        parsed["title"],
        parsed["outline"],
        subtitle=parsed.get("subtitle"),
        date_author=parsed.get("date_author"),
    )
    uid = uuid.uuid4().hex[:12]
    base = _generated_dir()
    name = f"ppt_{uid}.pptx"
    (base / name).write_bytes(content)
    return name
