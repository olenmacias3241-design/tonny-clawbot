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

---

# 视频讲解人物图（路飞等）

在「根据聊天内容生成视频」并勾选「同时生成视频文件」时，若希望画面是**人物在讲解**（例如海贼王路飞），可在此目录放入一张人物图：

- 将图片命名为 **`video_avatar.png`** 或 **`video_avatar.jpg`**
- 放在本目录下：`data/templates/video_avatar.png`（或 .jpg）

生成视频时：
- **若已安装 SadTalker**：会用人物图 + 配音生成**口播视频**（人物会动嘴），再叠字幕。
- **若未安装或 SadTalker 失败**：则以该图作为静态画面（缩放并居中铺满 1280×720），叠配音和字幕。
- 若未放置该文件，则使用深色纯色背景 + 字幕。

建议使用**竖版或方形、主体居中**的动漫/真人半身图，效果更好。

### 口播动嘴（SadTalker，可选）

若已安装 **SadTalker**，程序会优先用「人物图 + 配音」生成**会动嘴**的口播视频，再叠字幕；未安装或失败时自动退回为「静态人物图 + 字幕」。

**安装步骤：**

1. 克隆仓库并安装依赖（需 Python 3.8+、建议 GPU）。**建议使用独立 conda/venv**，避免与项目主环境的 torch/torchvision 冲突（否则易报 `No module named 'torchvision.transforms.functional_tensor'`）：
   ```bash
   cd /path/to/claw-bot-ai
   git clone https://github.com/OpenTalker/SadTalker.git
   cd SadTalker
   conda create -n sadtalker python=3.8 -y && conda activate sadtalker
   pip install torch torchvision
   pip install -r requirements.txt
   ```
   安装后，**启动本应用前**设置：`export SADTALKER_PYTHON=/path/to/conda/envs/sadtalker/bin/python`（或你的 venv 里 `bin/python`），再启动 claw-bot-ai。生成视频时会用该 Python 调 SadTalker。
2. **下载模型**（任选一种方式）：
   - **推荐（Linux/macOS）**：在 SadTalker 目录下执行一键脚本：
     ```bash
     cd SadTalker
     bash scripts/download_models.sh
     ```
   - **手动下载**：从下方任选一个渠道下载「预训练模型」压缩包，解压后把里面的 `checkpoints/`、`gfpgan/` 等放到 SadTalker 目录下（即解压后目录结构为 `SadTalker/checkpoints/...`、`SadTalker/gfpgan/...`）。
     - [GitHub Releases](https://github.com/OpenTalker/SadTalker/releases)（找 Pre-Trained Models 或 gfpgan 相关资源）
     - [Google Drive 预训练模型](https://drive.google.com/file/d/1gwWh45pF7aelNP_P78uDJL8Sycep-K7j/view?usp=sharing)
     - [百度云盘](https://pan.baidu.com/s/1kb1BCPaLOWX1JJb9Czbn6w?pwd=sadt)（密码：`sadt`）  
     GFPGAN 人脸增强为可选，单独下载：[Google Drive](https://drive.google.com/file/d/19AIBsmfcHW6BRJmeqSFlG5fL445Xmsyi?usp=sharing) / [Releases](https://github.com/OpenTalker/SadTalker/releases) / [百度云](https://pan.baidu.com/s/1P4fRgk9gaSutZnn8YW034Q?pwd=sadt)（密码：`sadt`），解压到 `SadTalker/gfpgan/`。
3. 指定 SadTalker 路径（二选一）：
   - 将 SadTalker 放在项目根目录下并命名为 `SadTalker` 或 `sadtalker`，程序会自动检测；
   - 或设置环境变量：`export SADTALKER_DIR=/绝对路径/SadTalker`。

完成后，生成视频时若存在 `video_avatar.png`/`.jpg`，将自动调用 SadTalker 生成口播视频。若页面上提示「本次为静态人物图」且带 SadTalker 报错，多为依赖冲突，请用独立 conda/venv 安装并设置 `SADTALKER_PYTHON` 后重试。
