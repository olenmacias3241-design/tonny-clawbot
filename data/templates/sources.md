# PPT 模板素材来源（可免费使用 / 学习）

以下来源提供免费 .pptx 模板，可下载后放入本目录并命名为 `pptx_template.pptx` 使用，或保留多份并自行选用。

## 官方 / 开源（可直接下载）

| 来源 | 说明 | 链接 |
|------|------|------|
| Microsoft Create | 官方免费模板，多种风格 | https://create.microsoft.com/en-us/powerpoint-templates |
| onocom/powerpoint-template | 基础模板，MIT 协议 | https://github.com/onocom/powerpoint-template |
| GBIF ppt-template | 含图标与图表工具包 | https://github.com/gbif/ppt-template |

## 第三方免费站（需在浏览器中下载）

| 来源 | 说明 |
|------|------|
| SlidesCarnival | 多风格免费 PPT/Google Slides 模板 |
| Slidesgo | 商务 / 科技 / 教育等主题 |
| Free-Power-Point-Templates.com | 现代商务、专业等 .pptx |
| MSLIDES | 简约风格，多页可编辑 |

## 使用本库中的模板

- 将任一 .pptx 放到本目录，命名为 **`pptx_template.pptx`** 即作为默认参考模板。
- 也可保留多个文件（如 `professional.pptx`、`minimal.pptx`），需要时复制为 `pptx_template.pptx` 再生成。

## 脚本拉取

项目根目录可运行：

```bash
python scripts/fetch_pptx_template.py <下载URL> [保存文件名]
```

会下载 .pptx 并保存到 `data/templates/`。示例：

```bash
python scripts/fetch_pptx_template.py "https://github.com/onocom/powerpoint-template/raw/master/powerpoint-template.pptx" professional.pptx
```
