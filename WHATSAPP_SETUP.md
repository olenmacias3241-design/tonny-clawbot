# 📱 WhatsApp 配置完整指南

本指南将帮助您快速配置 WhatsApp 消息发送功能。

---

## 🚀 方式 1: 使用 Twilio（推荐 - 简单快速）

### 为什么选择 Twilio？
- ✅ 注册简单，10分钟搞定
- ✅ 提供免费试用额度（$15）
- ✅ WhatsApp Sandbox 可立即测试
- ✅ 支持中国大陆注册

---

## 📋 详细配置步骤

### 步骤 1️⃣: 注册 Twilio 账号

1. **访问注册页面**
   ```
   https://www.twilio.com/try-twilio
   ```

2. **填写注册信息**
   - First Name: 您的名字
   - Last Name: 您的姓氏
   - Email: 您的邮箱
   - Password: 设置密码（至少12位）
   - 点击 "Start your free trial"

3. **验证邮箱**
   - 检查邮箱收件箱
   - 点击验证链接

4. **验证手机号**
   - 选择国家（China +86）
   - 输入您的手机号
   - 输入收到的验证码

### 步骤 2️⃣: 获取 Account SID 和 Auth Token

注册成功后，您会看到 Twilio Console 控制台：

1. **在控制台首页找到**
   ```
   Account Info
   ├── ACCOUNT SID: ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   └── AUTH TOKEN: ******************************** (点击"Show"查看)
   ```

2. **复制这两个值**
   - ACCOUNT SID: 以 `AC` 开头的长字符串
   - AUTH TOKEN: 点击 "Show" 显示后复制

### 步骤 3️⃣: 设置 WhatsApp Sandbox

1. **进入 WhatsApp Sandbox**
   - 在左侧菜单找到: `Messaging` → `Try it out` → `Send a WhatsApp message`
   - 或直接访问: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn

2. **您会看到类似这样的信息**
   ```
   Join your sandbox

   To: +1 415 523 8886
   Message: join <your-code>

   例如: join teacher-yellow
   ```

3. **使用您的 WhatsApp 加入 Sandbox**
   - 打开手机上的 WhatsApp
   - 添加联系人: `+1 415 523 8886`（Twilio 的 WhatsApp 号码）
   - 发送消息: `join teacher-yellow`（使用您看到的实际代码）
   - 等待回复确认加入成功

4. **记录 WhatsApp From 号码**
   - Sandbox 号码通常是: `whatsapp:+14155238886`
   - 或在页面上的 "From" 字段找到

### 步骤 4️⃣: 配置 Claw Bot AI

编辑 `/Users/taoyin/test2/claw-bot-ai/.env` 文件：

```bash
# WhatsApp Settings (Twilio)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
WHATSAPP_FROM=whatsapp:+14155238886
```

**重要说明：**
- `TWILIO_ACCOUNT_SID`: 从控制台复制的 Account SID
- `TWILIO_AUTH_TOKEN`: 从控制台复制的 Auth Token
- `WHATSAPP_FROM`: Twilio 的 WhatsApp 号码（通常是 +14155238886）

### 步骤 5️⃣: 重启服务器

```bash
cd /Users/taoyin/test2/claw-bot-ai
venv/bin/python main.py
```

### 步骤 6️⃣: 测试发送

```bash
curl -X POST "http://localhost:8000/send-whatsapp" \
  -H "Content-Type: application/json" \
  -d '{
    "to": "+86你的手机号",
    "message": "🤖 测试消息！Claw Bot AI WhatsApp 功能已激活！"
  }'
```

**注意：**
- 手机号格式: `+86` + 您的手机号（去掉前面的0）
- 例如: `+8613812345678`

---

## 📊 Twilio Sandbox 限制

### 免费试用账户限制：
- ✅ 可以发送消息
- ✅ $15 免费额度
- ⚠️ 只能发给加入了您 Sandbox 的号码
- ⚠️ 消息会带有测试前缀

### 如何添加更多接收者？
其他人也需要：
1. 添加 Twilio WhatsApp 号码 `+1 415 523 8886`
2. 发送 `join <your-code>` 加入您的 Sandbox

### 升级到生产环境（付费）：
如果需要：
- 发给任意 WhatsApp 用户
- 移除测试前缀
- 使用自己的 WhatsApp Business 号码

需要完成：
1. Twilio 账号升级（添加信用卡）
2. 申请 WhatsApp Business Profile
3. Facebook Business Manager 验证

**费用参考：**
- 对话费用: $0.005 - $0.09 每条（根据国家）
- 中国大陆: 约 ¥0.30 每条

---

## 🌐 方式 2: WhatsApp Business API（高级）

### 适用场景：
- 需要发送给大量用户
- 需要官方 WhatsApp Business 认证
- 企业级应用

### 配置步骤：

1. **注册 Facebook Business Manager**
   ```
   https://business.facebook.com/
   ```

2. **创建 WhatsApp Business Account**
   - 需要企业营业执照
   - 需要实名认证

3. **获取凭证**
   - Access Token: 在 Meta for Developers 获取
   - Phone Number ID: WhatsApp Business 号码 ID

4. **配置 .env**
   ```bash
   # WhatsApp Business API
   WHATSAPP_BUSINESS_TOKEN=your_long_access_token
   WHATSAPP_PHONE_ID=your_phone_number_id
   ```

5. **使用 Business API 发送**
   ```bash
   curl -X POST "http://localhost:8000/send-whatsapp" \
     -H "Content-Type: application/json" \
     -d '{
       "to": "+8613812345678",
       "message": "测试消息",
       "use_business_api": true
     }'
   ```

---

## 🔍 故障排查

### 问题 1: "Failed to send WhatsApp"

**检查：**
```bash
# 查看日志
tail -f /Users/taoyin/test2/claw-bot-ai/logs/claw_bot.log
```

**常见原因：**
- ❌ 凭证配置错误
- ❌ 接收者未加入 Sandbox
- ❌ 手机号格式错误

### 问题 2: Twilio 返回 21211 错误

**原因：** 手机号无效

**解决：**
- 确保手机号格式: `+[国家代码][号码]`
- 例如中国: `+8613812345678`
- 确保去掉号码前的 0

### 问题 3: "Not authorized" 错误

**原因：** Auth Token 错误

**解决：**
1. 登录 Twilio Console
2. 重新复制 Auth Token（点击 "Show"）
3. 更新 `.env` 文件
4. 重启服务器

---

## 💡 最佳实践

### 1. 消息格式化
```python
message = """
🤖 Claw Bot 通知

订单状态: ✅ 已完成
金额: $150.00
时间: 2026-02-16 13:20

感谢您的使用！
"""
```

### 2. 错误处理
```python
try:
    response = httpx.post(
        "http://localhost:8000/send-whatsapp",
        json={"to": phone, "message": msg},
        timeout=10.0
    )
    if response.json()["success"]:
        print("✅ 发送成功")
except Exception as e:
    print(f"❌ 发送失败: {e}")
```

### 3. 批量发送
```python
for user in users:
    send_whatsapp(user["phone"], message)
    time.sleep(1)  # 避免速率限制
```

---

## 📞 获取帮助

### Twilio 支持
- 文档: https://www.twilio.com/docs/whatsapp
- 控制台: https://console.twilio.com/
- 支持: https://support.twilio.com/

### Claw Bot AI
- 查看日志: `tail -f logs/claw_bot.log`
- 测试连接: `curl http://localhost:8000/`
- 详细文档: [NOTIFICATIONS_GUIDE.md](NOTIFICATIONS_GUIDE.md)

---

## ✅ 快速检查清单

配置完成后检查：

- [ ] Twilio 账号已注册
- [ ] Account SID 已复制到 `.env`
- [ ] Auth Token 已复制到 `.env`
- [ ] WhatsApp Sandbox 已加入（发送 join 消息）
- [ ] `.env` 文件已保存
- [ ] 服务器已重启
- [ ] 测试消息发送成功
- [ ] 手机收到 WhatsApp 消息

全部完成？恭喜！🎉 WhatsApp 通知功能已激活！

---

需要帮助？查看 [NOTIFICATIONS_GUIDE.md](NOTIFICATIONS_GUIDE.md) 了解更多示例和用法。
