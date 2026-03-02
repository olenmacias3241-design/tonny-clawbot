# Claw Bot AI - 快速参考卡

## 📋 常用命令

### 启动和停止

```bash
# 快速启动（自动安装依赖）
./start.sh

# 手动启动
source venv/bin/activate
python3 main.py

# 使用 Docker
docker-compose up -d
docker-compose down

# 查看日志
tail -f logs/claw_bot.log
```

### API 调用

```bash
# 健康检查
curl http://localhost:8000/health

# 发送消息
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "你的消息"}'

# 继续对话（使用相同的 conversation_id）
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "继续聊天", "conversation_id": "从上次响应获取的ID"}'

# 列出所有对话
curl http://localhost:8000/conversations

# 获取对话详情
curl http://localhost:8000/conversations/{conversation_id}

# 删除对话
curl -X DELETE http://localhost:8000/conversations/{conversation_id}
```

### 测试和开发

```bash
# 运行测试
pytest tests/

# 代码格式化
black src/

# 代码检查
flake8 src/

# 类型检查
mypy src/

# 命令行客户端
python cli_client.py
```

## 🔧 配置文件位置

| 文件 | 路径 | 用途 |
|------|------|------|
| 环境变量 | `.env` | API 密钥、服务器配置 |
| Bot 配置 | `config/bot_config.yaml` | Bot 行为、提示词 |
| 依赖 | `requirements.txt` | Python 包依赖 |
| Docker | `Dockerfile`, `docker-compose.yml` | 容器化部署 |

## 🔑 关键环境变量

```bash
# 在 .env 文件中配置

# AI 提供商（必需，二选一）
DEFAULT_AI_PROVIDER=openai          # 或 anthropic
OPENAI_API_KEY=sk-...               # OpenAI 密钥
ANTHROPIC_API_KEY=sk-ant-...        # Anthropic 密钥

# 服务器配置
HOST=0.0.0.0
PORT=8000
DEBUG=false

# 日志
LOG_LEVEL=INFO                      # DEBUG|INFO|WARNING|ERROR
LOG_FILE=logs/claw_bot.log

# Bot 设置
MAX_CONTEXT_MESSAGES=10             # 上下文消息数量
RESPONSE_TIMEOUT=30                 # 响应超时（秒）
```

## 📡 API 端点速查

| 方法 | 端点 | 说明 | 示例 |
|------|------|------|------|
| GET | `/` | 服务信息 | `curl http://localhost:8000/` |
| GET | `/health` | 健康检查 | `curl http://localhost:8000/health` |
| GET | `/docs` | Swagger UI | 浏览器访问 |
| GET | `/redoc` | ReDoc 文档 | 浏览器访问 |
| POST | `/chat` | 对话 | 见下方请求体 |
| GET | `/conversations` | 列出对话 | - |
| GET | `/conversations/{id}` | 对话详情 | - |
| DELETE | `/conversations/{id}` | 删除对话 | - |

### /chat 请求体格式

```json
{
  "message": "你好",                    // 必需
  "conversation_id": "uuid-string",   // 可选，用于继续对话
  "user_id": "user-123",              // 可选
  "metadata": {"key": "value"}        // 可选
}
```

### /chat 响应格式

```json
{
  "message": "Bot 的回复内容",
  "conversation_id": "uuid-string",
  "metadata": {
    "message_count": 4
  },
  "error": null
}
```

## 🐍 Python 客户端示例

```python
import httpx
import asyncio

async def chat(message, conversation_id=None):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/chat",
            json={
                "message": message,
                "conversation_id": conversation_id
            }
        )
        return response.json()

# 使用
result = asyncio.run(chat("你好"))
print(result["message"])
print(f"对话ID: {result['conversation_id']}")
```

## 🌐 JavaScript 客户端示例

```javascript
async function chat(message, conversationId = null) {
  const response = await fetch('http://localhost:8000/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: message,
      conversation_id: conversationId
    })
  });
  return await response.json();
}

// 使用
chat("你好").then(data => {
  console.log(data.message);
  console.log(`对话ID: ${data.conversation_id}`);
});
```

## 🐳 Docker 命令

```bash
# 构建镜像
docker build -t claw-bot-ai .

# 运行容器
docker run -d \
  --name claw-bot \
  -p 8000:8000 \
  --env-file .env \
  claw-bot-ai

# 查看日志
docker logs -f claw-bot

# 停止容器
docker stop claw-bot

# 删除容器
docker rm claw-bot

# 使用 Docker Compose
docker-compose up -d        # 启动
docker-compose logs -f      # 查看日志
docker-compose down         # 停止并删除
docker-compose restart      # 重启
```

## 🔍 故障排查

### 服务器无法启动

```bash
# 检查端口占用
lsof -i :8000              # macOS/Linux
netstat -ano | findstr :8000  # Windows

# 检查 Python 版本
python3 --version          # 需要 3.9+

# 检查依赖
pip list | grep fastapi
```

### API 调用失败

```bash
# 查看实时日志
tail -f logs/claw_bot.log

# 测试健康检查
curl http://localhost:8000/health

# 检查 API 密钥
grep API_KEY .env
```

### Docker 问题

```bash
# 查看容器状态
docker ps -a

# 查看容器日志
docker logs claw-bot

# 进入容器调试
docker exec -it claw-bot bash
```

## 📊 性能参数

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| MAX_CONTEXT_MESSAGES | 10 | 上下文消息数，越大消耗越多 token |
| RESPONSE_TIMEOUT | 30 | 响应超时时间（秒）|
| temperature | 0.7 | AI 创造性，0-2，越高越随机 |
| max_tokens | 2000 | 最大生成 token 数 |

## 📚 文档索引

- [QUICKSTART.md](QUICKSTART.md) - 5分钟快速上手
- [README.md](README.md) - 完整使用文档
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - 项目架构总结
- [INSTALLATION_CHECKLIST.md](INSTALLATION_CHECKLIST.md) - 安装检查清单

## 💡 最佳实践

1. **保持对话上下文**：使用相同的 conversation_id
2. **调试模式**：开发时设置 `DEBUG=true` 和 `LOG_LEVEL=DEBUG`
3. **生产环境**：使用 Docker 部署，设置环境变量而非硬编码
4. **API 密钥安全**：不要提交 .env 到版本控制
5. **性能优化**：根据需要调整 MAX_CONTEXT_MESSAGES

## 🆘 获取帮助

1. 查看日志文件：`logs/claw_bot.log`
2. 访问 API 文档：http://localhost:8000/docs
3. 检查环境配置：`.env` 和 `config/bot_config.yaml`
4. 运行测试：`pytest tests/ -v`

---

提示：按 Ctrl+F 可在此文档中快速搜索命令或配置项。
