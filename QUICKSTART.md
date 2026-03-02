# Claw Bot AI - 快速开始指南

## 🚀 5分钟快速上手

### 第一步：环境准备

确保已安装 Python 3.9 或更高版本：

```bash
python3 --version
```

### 第二步：进入项目目录

```bash
cd claw-bot-ai
```

### 第三步：配置 API 密钥

1. 复制环境变量模板：

```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，添加你的 AI API 密钥：

```bash
# 使用 OpenAI (推荐)
DEFAULT_AI_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-api-key-here

# 或者使用 Anthropic Claude
# DEFAULT_AI_PROVIDER=anthropic
# ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here
```

**获取 API 密钥：**
- OpenAI: https://platform.openai.com/api-keys
- Anthropic: https://console.anthropic.com/

### 第四步：安装依赖

#### 方法 1：使用快速启动脚本（推荐）

```bash
./start.sh
```

#### 方法 2：手动安装

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# 或 Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 第五步：启动服务器

```bash
# 如果使用了 start.sh，服务器已经启动
# 否则手动启动：
python3 main.py
```

服务器将在 `http://localhost:8000` 启动。

### 第六步：测试 Bot

#### 使用命令行客户端（推荐）

在新终端中运行：

```bash
cd claw-bot-ai
source venv/bin/activate
python cli_client.py
```

#### 使用 curl 测试

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "你好，请介绍一下你自己"}'
```

#### 使用浏览器

访问 API 文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📝 常见问题

### 问：如何切换 AI 提供商？

编辑 `.env` 文件中的 `DEFAULT_AI_PROVIDER`：

```bash
# 使用 OpenAI
DEFAULT_AI_PROVIDER=openai

# 或使用 Anthropic
DEFAULT_AI_PROVIDER=anthropic
```

### 问：如何修改 Bot 的性格和行为？

编辑 `config/bot_config.yaml` 文件：

```yaml
bot:
  name: "Claw Bot"
  personality: "helpful, harmless, and honest"
  system_prompt: |
    在这里自定义你的系统提示词...
```

### 问：API 密钥无效怎么办？

1. 确认 API 密钥正确无误
2. 检查 API 密钥是否有足够的配额
3. 查看日志文件 `logs/claw_bot.log` 获取详细错误信息

### 问：如何查看日志？

```bash
tail -f logs/claw_bot.log
```

## 🎯 下一步

现在你已经成功运行了 Claw Bot AI！接下来可以：

1. 阅读完整文档：`README.md`
2. 自定义 Bot 配置：`config/bot_config.yaml`
3. 开发自己的功能：查看 `src/` 目录结构
4. 集成到你的应用：使用 REST API

## 📚 示例代码

### Python 客户端示例

```python
import httpx
import asyncio

async def chat():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/chat",
            json={"message": "讲个笑话"}
        )
        print(response.json()["message"])

asyncio.run(chat())
```

### JavaScript 客户端示例

```javascript
fetch('http://localhost:8000/chat', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({message: '讲个笑话'})
})
.then(r => r.json())
.then(data => console.log(data.message));
```

## 💡 提示

- 保持对话上下文：使用相同的 `conversation_id`
- 调试模式：在 `.env` 中设置 `DEBUG=true`
- 日志级别：在 `.env` 中设置 `LOG_LEVEL=DEBUG`

需要帮助？查看 [README.md](README.md) 获取完整文档。
