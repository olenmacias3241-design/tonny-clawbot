# 设置 Groq 免费 API（推荐）

Groq 提供**完全免费**的高速 AI API，支持多种开源模型。

## 步骤 1：获取 API Key

1. 访问 https://console.groq.com/keys
2. 使用 Google/GitHub 账号登录（免费，无需信用卡）
3. 点击 "Create API Key"
4. 复制生成的密钥（格式：`gsk_...`）

## 步骤 2：配置密钥

编辑 `.env` 文件：

```bash
OPENAI_API_KEY=gsk_你的Groq密钥
OPENAI_MODEL=llama-3.1-70b-versatile
```

## 步骤 3：更新代码支持 Groq

编辑 `src/bot/ai_provider.py`，在第 32 行后添加：

```python
# Check if using Groq (key starts with gsk_)
elif settings.openai_api_key.startswith("gsk_"):
    client_kwargs["base_url"] = "https://api.groq.com/openai/v1"
    log.info("Using Groq API endpoint")
```

完整的修改后代码：

```python
# Support OpenRouter and other OpenAI-compatible APIs
client_kwargs = {"api_key": settings.openai_api_key}

# Check if using OpenRouter (key starts with sk-or-)
if settings.openai_api_key.startswith("sk-or-"):
    client_kwargs["base_url"] = "https://openrouter.ai/api/v1"
    log.info("Using OpenRouter API endpoint")
# Check if using Groq (key starts with gsk_)
elif settings.openai_api_key.startswith("gsk_"):
    client_kwargs["base_url"] = "https://api.groq.com/openai/v1"
    log.info("Using Groq API endpoint")

self.client = AsyncOpenAI(**client_kwargs)
```

## 步骤 4：重启服务器

```bash
# 停止当前服务器（如果在运行）
# 然后重启
cd /Users/taoyin/test2/claw-bot-ai
venv/bin/python main.py
```

## 步骤 5：测试

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "你好！"}'
```

## 可用的 Groq 模型

- `llama-3.1-70b-versatile` - 最强大（推荐）
- `llama-3.1-8b-instant` - 最快
- `mixtral-8x7b-32768` - 长上下文
- `gemma2-9b-it` - Google 的模型

## 优势

✅ **完全免费** - 无需信用卡
✅ **极快速度** - 世界上最快的推理
✅ **高限额** - 每分钟 30 次请求
✅ **优秀质量** - Llama 3.1 70B 性能接近 GPT-4

---

获取密钥后告诉我，我立即帮你配置！
