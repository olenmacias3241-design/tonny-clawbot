# Claw Bot AI - 使用指南

## 🚀 如何让 Bot 干活

Claw Bot AI 提供多种使用方式，你可以根据需求选择最适合的方法。

### 聊天操控电脑（传统龙虾能力）

在聊天里可以说「**运行 pwd**」「**执行 ls**」「**帮我跑一下 date**」等，让龙虾在服务器所在机器上执行**白名单内**的命令，并把终端输出贴回给你。

- **开启**：在 `.env` 中设置 `ENABLE_COMPUTER_CONTROL=true`，并可配置 `ALLOWED_COMMANDS=ls,pwd,date,whoami`。重启服务后生效。
- **安全**：只执行白名单命令；超时 15 秒终止；工作目录为项目根。未开启时会提示如何开启。

---

## 方法 1：命令行交互客户端（推荐新手）

这是最简单直观的方式，适合快速测试和日常使用。

### 启动步骤

```bash
# 1. 打开新终端
# 2. 进入项目目录
cd /Users/taoyin/test2/claw-bot-ai

# 3. 激活虚拟环境
source venv/bin/activate

# 4. 运行客户端
python cli_client.py
```

### 使用示例

```
Claw Bot AI - Interactive Chat
Type 'exit' or 'quit' to end the conversation

You: 你好，请介绍一下你自己
Bot: 我是 Claw Bot，一个智能AI助手...

You: 帮我写一段Python代码
Bot: 当然可以...

You: exit
Goodbye!
```

---

## 方法 2：使用 curl 命令（适合脚本和测试）

直接通过 HTTP 请求与 Bot 交互。

### 基本用法

```bash
# 发送消息
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"你好\"}"

# 继续对话（使用 conversation_id）
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"继续上一个话题\", \"conversation_id\": \"从上次响应获取的ID\"}"
```

### 响应格式

```json
{
  "message": "Bot 的回复内容",
  "conversation_id": "abc-123-def",
  "metadata": {
    "message_count": 2
  },
  "error": null
}
```

---

## 方法 3：Python 代码集成

将 Bot 集成到你的 Python 项目中。

### 同步方式

```python
import httpx

def chat_with_bot(message, conversation_id=None):
    """与 Bot 对话"""
    response = httpx.post(
        "http://localhost:8000/chat",
        json={
            "message": message,
            "conversation_id": conversation_id
        },
        timeout=30.0
    )
    return response.json()

# 使用
result = chat_with_bot("你好，请帮我写一个函数")
print(result["message"])
print(f"对话ID: {result['conversation_id']}")

# 继续对话
result2 = chat_with_bot(
    "继续",
    conversation_id=result['conversation_id']
)
print(result2["message"])
```

### 异步方式

```python
import httpx
import asyncio

async def chat_async(message):
    """异步对话"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/chat",
            json={"message": message},
            timeout=30.0
        )
        return response.json()

# 使用
result = asyncio.run(chat_async("你好"))
print(result["message"])
```

---

## 方法 4：JavaScript/Node.js 集成

在前端或 Node.js 项目中使用。

### Fetch API（浏览器/Node.js）

```javascript
async function chatWithBot(message, conversationId = null) {
  const response = await fetch('http://localhost:8000/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      message: message,
      conversation_id: conversationId
    })
  });

  return await response.json();
}

// 使用
chatWithBot("你好，请帮我写代码").then(data => {
  console.log(data.message);
  console.log("对话ID:", data.conversation_id);

  // 继续对话
  return chatWithBot("继续", data.conversation_id);
}).then(data => {
  console.log(data.message);
});
```

### Axios（Node.js）

```javascript
const axios = require('axios');

async function chat(message) {
  try {
    const response = await axios.post('http://localhost:8000/chat', {
      message: message
    });
    return response.data;
  } catch (error) {
    console.error('错误:', error.message);
  }
}

// 使用
chat("你好").then(data => {
  console.log(data.message);
});
```

---

## 方法 5：Web 浏览器（API 文档界面）

最简单的测试方式，无需写代码。

### 访问 Swagger UI

1. 在浏览器打开：http://localhost:8000/docs
2. 找到 `POST /chat` 端点
3. 点击 "Try it out"
4. 输入消息内容
5. 点击 "Execute"
6. 查看响应

### 访问 ReDoc

更美观的文档界面：http://localhost:8000/redoc

---

## 实用示例

### 示例 1：让 Bot 写代码

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"请用Python写一个快速排序算法\"}"
```

### 示例 2：让 Bot 分析数据

```python
import httpx

# 准备数据
data = "销售额: [100, 200, 150, 300, 250]"
prompt = f"请分析以下数据并给出趋势: {data}"

# 发送请求
response = httpx.post(
    "http://localhost:8000/chat",
    json={"message": prompt}
)

print(response.json()["message"])
```

### 示例 3：多轮对话

```python
import httpx

conversation_id = None

def ask(question):
    global conversation_id
    result = httpx.post(
        "http://localhost:8000/chat",
        json={
            "message": question,
            "conversation_id": conversation_id
        }
    ).json()
    conversation_id = result['conversation_id']
    return result['message']

# 多轮对话
print(ask("我想做一个网站"))
print(ask("用什么技术栈比较好"))
print(ask("给我一个简单的示例"))
```

### 示例 4：批量处理

```python
import httpx

questions = [
    "什么是机器学习？",
    "什么是深度学习？",
    "两者有什么区别？"
]

for q in questions:
    result = httpx.post(
        "http://localhost:8000/chat",
        json={"message": q}
    ).json()
    print(f"Q: {q}")
    print(f"A: {result['message']}\n")
```

---

## 管理对话

### 查看所有对话

```bash
curl http://localhost:8000/conversations
```

### 获取特定对话详情

```bash
curl http://localhost:8000/conversations/{conversation_id}
```

### 删除对话

```bash
curl -X DELETE http://localhost:8000/conversations/{conversation_id}
```

---

## 高级用法

### 自定义元数据

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "你好",
    "user_id": "user_123",
    "metadata": {
      "source": "web",
      "language": "zh"
    }
  }'
```

### 流式处理（未来功能）

目前 Bot 返回完整响应，未来版本将支持流式输出。

---

## 常见任务示例

### 1. 代码生成

```python
prompt = "用Python写一个连接MySQL数据库的类，包含增删改查方法"
```

### 2. 文本翻译

```python
prompt = "请将以下文本翻译成英文：[你的中文文本]"
```

### 3. 数据分析

```python
prompt = "分析这些数据并给出建议：[数据内容]"
```

### 4. 问题解答

```python
prompt = "解释一下什么是Docker容器化技术"
```

### 5. 创意写作

```python
prompt = "写一个关于AI的科幻短篇故事"
```

---

## 故障排除

### Bot 没有响应

检查服务器是否运行：
```bash
curl http://localhost:8000/health
```

### 响应速度慢

- 检查网络连接
- 尝试使用更快的模型
- 减少 `max_tokens` 参数

### 错误处理

所有错误都会在响应的 `error` 字段中返回：
```json
{
  "message": "Sorry, I encountered an error...",
  "conversation_id": "error",
  "error": "具体错误信息"
}
```

---

## 模型配置问题

### 当前使用 OpenRouter

如果遇到模型不可用的错误，访问 https://openrouter.ai/models 查看可用的免费模型。

### 推荐的免费模型（2026年2月）

编辑 `/Users/taoyin/test2/claw-bot-ai/.env` 文件，尝试以下模型：

```bash
# 方案1：使用最新的免费模型（需要查看 OpenRouter 官网）
OPENAI_MODEL=<查看官网获取最新免费模型>

# 方案2：切换到官方 OpenAI（需要付费 API Key）
OPENAI_API_KEY=sk-proj-your-openai-key
OPENAI_MODEL=gpt-3.5-turbo
```

修改后重启服务器：
```bash
# 停止当前服务器（Ctrl+C）
# 重新启动
cd /Users/taoyin/test2/claw-bot-ai
venv/bin/python main.py
```

---

## 🎯 快速开始命令

```bash
# 终端 1：启动服务器
cd /Users/taoyin/test2/claw-bot-ai
venv/bin/python main.py

# 终端 2：使用命令行客户端
cd /Users/taoyin/test2/claw-bot-ai
source venv/bin/activate
python cli_client.py

# 或者用 curl 测试
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"你好\"}"
```

---

需要更多帮助？查看 [README.md](README.md) 或 [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
