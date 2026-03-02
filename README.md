# Claw Bot AI

An intelligent AI bot framework built with FastAPI, supporting multiple AI providers (OpenAI, Anthropic Claude, Groq, OpenRouter).

## Features

- **AI Chat**: Multi-provider support (OpenAI, Anthropic, Groq, OpenRouter)
- **Activity Tracking**: Sync GitHub commits/PRs, store in SQLite
- **Daily/Weekly Reports**: Auto-generate reports from activity data (AI or rule-based)
- **Notifications**: Email, Telegram, WhatsApp
- **Web UI**: Daily/weekly report viewer at `/daily`
- RESTful API with FastAPI, configurable via `.env`

> 详细功能说明、代码结构及实现方式见 **[PROJECT_GUIDE.md](./PROJECT_GUIDE.md)**

## Project Structure

```
claw-bot-ai/
├── src/
│   ├── bot/                    # AI 对话
│   │   ├── ai_provider.py      # AI 提供商
│   │   └── claw_bot.py         # 对话逻辑
│   ├── handlers/api.py         # FastAPI 路由
│   ├── models/                 # 数据模型
│   ├── providers/              # 外部数据源（GitHub）
│   ├── services/               # 活动服务、报告服务
│   ├── utils/                  # 配置、日志、通知
│   └── db.py                   # 数据库
├── static/activities.html      # 日报/周报前端
├── main.py                     # 入口
├── run_daily_report_once.py    # 一次性日报脚本
└── PROJECT_GUIDE.md            # 功能与结构说明
```

## Installation

### 1. Create Virtual Environment

```bash
cd claw-bot-ai
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Copy the example environment file and configure your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
# Choose your AI provider
DEFAULT_AI_PROVIDER=openai

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# OR Anthropic Configuration
# ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

## Usage

### Start the Server

```bash
python3 main.py
```

The API will be available at `http://localhost:8000`

### API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### API Endpoints

#### 1. Chat with Bot

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, how are you?",
    "conversation_id": null
  }'
```

Response:
```json
{
  "message": "Hello! I'm doing well, thank you for asking. How can I assist you today?",
  "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
  "metadata": {
    "message_count": 2
  },
  "error": null
}
```

#### 2. List Conversations

```bash
curl "http://localhost:8000/conversations"
```

#### 3. Get Conversation Details

```bash
curl "http://localhost:8000/conversations/{conversation_id}"
```

#### 4. Delete Conversation

```bash
curl -X DELETE "http://localhost:8000/conversations/{conversation_id}"
```

## Configuration

### Environment Variables

See `.env.example` for all available configuration options.

Key settings:
- `DEFAULT_AI_PROVIDER`: Choose "openai" or "anthropic"
- `OPENAI_API_KEY`: Your OpenAI API key
- `ANTHROPIC_API_KEY`: Your Anthropic API key
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `MAX_CONTEXT_MESSAGES`: Number of messages to keep in context

### Bot Configuration

Edit `config/bot_config.yaml` to customize:
- Bot personality and system prompt
- AI generation parameters (temperature, max_tokens)
- Feature toggles
- Rate limiting settings

## Development

### Run in Debug Mode

```bash
# In .env file
DEBUG=true
LOG_LEVEL=DEBUG
```

### Run Tests

```bash
pytest tests/ -v
```

### Code Formatting

```bash
black src/
flake8 src/
mypy src/
```

## Architecture

### AI Provider Pattern

The bot uses a provider pattern to support multiple AI backends:

```python
from src.bot.ai_provider import get_ai_provider

# Use OpenAI
provider = get_ai_provider("openai")

# Use Anthropic
provider = get_ai_provider("anthropic")
```

### Conversation Management

Each conversation maintains its own context and message history:

```python
from src.bot.claw_bot import ClawBot
from src.models.message import BotRequest

bot = ClawBot()
request = BotRequest(message="Hello", conversation_id="123")
response = await bot.process_message(request)
```

## Examples

### Python Client Example

```python
import httpx
import asyncio

async def chat_with_bot():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/chat",
            json={
                "message": "Tell me about AI",
                "conversation_id": None
            }
        )
        data = response.json()
        print(f"Bot: {data['message']}")
        return data['conversation_id']

asyncio.run(chat_with_bot())
```

### JavaScript/Node.js Client Example

```javascript
const fetch = require('node-fetch');

async function chatWithBot() {
  const response = await fetch('http://localhost:8000/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: 'Tell me about AI',
      conversation_id: null
    })
  });

  const data = await response.json();
  console.log('Bot:', data.message);
  return data.conversation_id;
}

chatWithBot();
```

## Deployment

### Using Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "main.py"]
```

### Using systemd

Create a service file `/etc/systemd/system/claw-bot.service`:

```ini
[Unit]
Description=Claw Bot AI Service
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/claw-bot-ai
Environment="PATH=/path/to/claw-bot-ai/venv/bin"
ExecStart=/path/to/claw-bot-ai/venv/bin/python3 main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
