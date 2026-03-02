# 📧📱 Claw Bot AI - 消息通知配置指南

Bot 现在支持通过邮箱、Telegram 和 WhatsApp 自动发送消息！

---

## 🚀 快速开始

### 1. 配置凭证

编辑 `.env` 文件，添加你需要的服务凭证：

```bash
# 邮箱配置（使用 Gmail 示例）
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_FROM=your_email@gmail.com

# Telegram配置
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_DEFAULT_CHAT_ID=your_chat_id

# WhatsApp配置（Twilio）
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
WHATSAPP_FROM=whatsapp:+1234567890
```

### 2. 重启服务器

```bash
# 停止当前服务器（Ctrl+C）
# 重新启动
cd /Users/taoyin/test2/claw-bot-ai
venv/bin/python main.py
```

---

## 📧 邮箱配置详解

### Gmail 配置步骤

1. **启用两步验证**
   - 访问 https://myaccount.google.com/security
   - 启用"两步验证"

2. **生成应用专用密码**
   - 访问 https://myaccount.google.com/apppasswords
   - 选择"应用"→"其他"
   - 输入"Claw Bot"
   - 复制生成的16位密码

3. **配置 .env**
   ```bash
   SMTP_USERNAME=yourname@gmail.com
   SMTP_PASSWORD=abcd efgh ijkl mnop  # 16位应用密码
   EMAIL_FROM=yourname@gmail.com
   ```

### 发送邮件 API

```bash
curl -X POST "http://localhost:8000/send-email" \
  -H "Content-Type: application/json" \
  -d '{
    "to": "recipient@example.com",
    "subject": "测试邮件",
    "body": "这是来自 Claw Bot 的测试邮件！"
  }'
```

### Python 示例

```python
import httpx

response = httpx.post(
    "http://localhost:8000/send-email",
    json={
        "to": "user@example.com",
        "subject": "重要通知",
        "body": "<h1>你好！</h1><p>这是HTML邮件</p>",
        "html": True
    }
)
print(response.json())
```

---

## 📱 Telegram 配置详解

### 创建 Telegram Bot

1. **与 @BotFather 对话**
   - 在 Telegram 搜索 @BotFather
   - 发送 `/newbot`
   - 按提示设置 bot 名称
   - 复制 Bot Token（格式：`123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`）

2. **获取 Chat ID**
   - 向你的 bot 发送任意消息
   - 访问：`https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - 找到 `"chat":{"id":123456789}` 中的数字

   或使用我们的API：
   ```bash
   curl http://localhost:8000/telegram/updates
   ```

3. **配置 .env**
   ```bash
   TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
   TELEGRAM_DEFAULT_CHAT_ID=123456789
   ```

### 发送 Telegram 消息 API

```bash
curl -X POST "http://localhost:8000/send-telegram" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "*Claw Bot 通知*\n\n这是一条测试消息！",
    "parse_mode": "Markdown"
  }'
```

### Python 示例

```python
import httpx

response = httpx.post(
    "http://localhost:8000/send-telegram",
    json={
        "text": "🚀 *重要通知*\n\n交易完成！",
        "parse_mode": "Markdown"
    }
)
print(response.json())
```

### 发送图片

```bash
curl -X POST "http://localhost:8000/send-telegram-photo" \
  -H "Content-Type: application/json" \
  -d '{
    "photo_url": "https://example.com/image.jpg",
    "caption": "查看这张图片"
  }'
```

---

## 💬 WhatsApp 配置详解

### 方式 1：使用 Twilio（推荐）

1. **注册 Twilio**
   - 访问 https://www.twilio.com/try-twilio
   - 注册账号（有免费试用额度）

2. **设置 WhatsApp Sandbox**
   - 登录 Twilio Console
   - 导航到 Messaging → Try it out → Send a WhatsApp message
   - 按提示向 Twilio WhatsApp 号码发送加入代码

3. **获取凭证**
   - Account SID：在 Console 首页
   - Auth Token：在 Console 首页（点击显示）
   - WhatsApp From：格式 `whatsapp:+14155238886`

4. **配置 .env**
   ```bash
   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN=your_auth_token
   WHATSAPP_FROM=whatsapp:+14155238886
   ```

### 方式 2：WhatsApp Business API

1. **获取访问权限**
   - 访问 https://business.facebook.com/
   - 设置 WhatsApp Business API

2. **配置 .env**
   ```bash
   WHATSAPP_BUSINESS_TOKEN=your_access_token
   WHATSAPP_PHONE_ID=your_phone_number_id
   ```

### 发送 WhatsApp 消息 API

```bash
curl -X POST "http://localhost:8000/send-whatsapp" \
  -H "Content-Type: application/json" \
  -d '{
    "to": "+1234567890",
    "message": "你好！这是来自 Claw Bot 的 WhatsApp 消息"
  }'
```

### Python 示例

```python
import httpx

response = httpx.post(
    "http://localhost:8000/send-whatsapp",
    json={
        "to": "+1234567890",
        "message": "🤖 Claw Bot 通知：任务完成！"
    }
)
print(response.json())
```

---

## 🔥 实用场景示例

### 场景 1：交易提醒

```python
import httpx

def notify_trade_complete(symbol, price, profit):
    message = f"""
🎯 交易完成

币种：{symbol}
价格：${price}
利润：${profit}
时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """

    # 发送到 Telegram
    httpx.post(
        "http://localhost:8000/send-telegram",
        json={"text": message}
    )

    # 同时发邮件
    httpx.post(
        "http://localhost:8000/send-email",
        json={
            "to": "trader@example.com",
            "subject": f"交易完成 - {symbol}",
            "body": message
        }
    )

# 使用
notify_trade_complete("BTC/USDT", 42000, 150)
```

### 场景 2：定时报告

```python
import httpx
import schedule

def send_daily_report():
    report = generate_trading_report()  # 你的报告生成函数

    # 发送到 WhatsApp
    httpx.post(
        "http://localhost:8000/send-whatsapp",
        json={
            "to": "+1234567890",
            "message": f"📊 每日报告\n\n{report}"
        }
    )

# 每天早上 9点发送
schedule.every().day.at("09:00").do(send_daily_report)
```

### 场景 3：错误警报

```python
import httpx

def alert_error(error_msg):
    # 紧急情况发送到所有渠道
    channels = [
        ("email", {
            "to": "admin@example.com",
            "subject": "🚨 系统错误",
            "body": error_msg
        }),
        ("telegram", {
            "text": f"🚨 *错误警报*\n\n{error_msg}",
            "parse_mode": "Markdown"
        }),
        ("whatsapp", {
            "to": "+1234567890",
            "message": f"🚨 系统错误：{error_msg}"
        })
    ]

    for channel, payload in channels:
        try:
            httpx.post(
                f"http://localhost:8000/send-{channel}",
                json=payload,
                timeout=5
            )
        except Exception as e:
            print(f"Failed to send {channel}: {e}")
```

---

## 📝 API 端点总结

| 端点 | 方法 | 功能 |
|------|------|------|
| `/send-email` | POST | 发送邮件 |
| `/send-telegram` | POST | 发送 Telegram 消息 |
| `/send-telegram-photo` | POST | 发送 Telegram 图片 |
| `/telegram/updates` | GET | 获取 Telegram 更新（用于获取 chat_id）|
| `/send-whatsapp` | POST | 发送 WhatsApp 消息 |
| `/send-whatsapp-template` | POST | 发送 WhatsApp 模板消息 |

---

## 🔐 安全建议

1. **保护凭证**
   - 不要提交 `.env` 到版本控制
   - 使用环境变量或密钥管理服务

2. **限制访问**
   - 只在需要时启用通知功能
   - 考虑添加 API 认证

3. **监控使用**
   - 查看日志：`tail -f logs/claw_bot.log`
   - 监控 API 配额

---

## 🚨 故障排查

### 邮件发送失败

- 检查 SMTP 凭证是否正确
- Gmail：确保使用应用专用密码
- 查看日志：`tail -f logs/claw_bot.log`

### Telegram 发送失败

- 确认 Bot Token 正确
- 确认已向 Bot 发送过至少一条消息
- 使用 `/telegram/updates` 端点检查配置

### WhatsApp 发送失败

- Twilio：确认已完成 Sandbox 设置
- 检查号码格式（需要包含国家代码）
- 确认账号有足够余额

---

## 💡 高级功能

### 批量发送

```python
recipients = ["user1@example.com", "user2@example.com", "user3@example.com"]

for email in recipients:
    httpx.post(
        "http://localhost:8000/send-email",
        json={
            "to": email,
            "subject": "批量通知",
            "body": "这是批量发送的消息"
        }
    )
```

### 结合 AI 生成内容

```python
# 先让 AI 生成消息内容
ai_response = httpx.post(
    "http://localhost:8000/chat",
    json={"message": "写一封感谢客户的邮件"}
)

email_content = ai_response.json()["message"]

# 然后发送邮件
httpx.post(
    "http://localhost:8000/send-email",
    json={
        "to": "customer@example.com",
        "subject": "感谢信",
        "body": email_content,
        "html": True
    }
)
```

---

需要帮助？查看主文档 [README.md](README.md) 或 [USAGE_GUIDE.md](USAGE_GUIDE.md)
