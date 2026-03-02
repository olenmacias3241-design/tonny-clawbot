# PPT 参考模板

把**你觉得好看的 .pptx** 放到这里并命名为 **`pptx_template.pptx`**，龙虾生成 PPT 时会优先沿用它的版式与主题，只往里面填标题和要点。

## 已积累的模板

- **professional.pptx** — 来自 [onocom/powerpoint-template](https://github.com/onocom/powerpoint-template)（MIT），基础商务风格。若要作为默认参考，可复制为 `pptx_template.pptx`。
- 更多免费素材来源与下载方式见 **sources.md**。可用 `python scripts/fetch_pptx_template.py <url> 文件名.pptx` 拉取更多。

## 使用方式

1. 在 PowerPoint / WPS / Keynote 里做一页你喜欢的**标题页**和一页**标题+内容页**（或从网上下载一个现成模板）。
2. 删除模板里多余的幻灯片，只保留：
   - **第 1 个版式**：用作封面（有主标题、副标题位置即可）
   - **第 2 个版式**：用作内容页（有标题 + 正文/要点位置即可）
3. 另存为 `pptx_template.pptx`，放到本目录下（即 `data/templates/pptx_template.pptx`）。
4. 之后在聊天里说「做一份 PPT」，生成结果就会使用这个模板的样式。

若没有放模板，或模板加载失败，会自动退回使用内置设计（色条 + 圆角卡片）。

## 建议

- 模板里**幻灯片数量**可以为 0（只有版式），也可以留 1～2 页示例，程序会先清空再按你的内容生成新页。
- 版式顺序：`slide_layouts[0]` = 封面，`slide_layouts[1]` = 内容页；若你的模板顺序不同，可调整模板的版式顺序或联系开发改映射。
