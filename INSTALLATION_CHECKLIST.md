# Claw Bot AI - 安装检查清单

使用此清单确保正确安装和配置 Claw Bot AI。

## ✅ 安装前检查

- [ ] Python 3.9+ 已安装
  ```bash
  python3 --version
  ```

- [ ] pip 已安装并更新到最新版本
  ```bash
  pip --version
  pip install --upgrade pip
  ```

- [ ] 获得 AI API 密钥（至少一个）
  - [ ] OpenAI API Key: https://platform.openai.com/api-keys
  - [ ] Anthropic API Key: https://console.anthropic.com/

## ✅ 安装步骤

### 1. 项目设置

- [ ] 已进入项目目录
  ```bash
  cd claw-bot-ai
  ```

- [ ] 已创建虚拟环境
  ```bash
  python3 -m venv venv
  ```

- [ ] 已激活虚拟环境
  ```bash
  source venv/bin/activate  # macOS/Linux
  # 或
  venv\Scripts\activate     # Windows
  ```

### 2. 依赖安装

- [ ] 已安装所有依赖
  ```bash
  pip install -r requirements.txt
  ```

- [ ] 验证关键包已安装
  ```bash
  pip list | grep -E "fastapi|openai|anthropic|uvicorn"
  ```

### 3. 配置

- [ ] 已创建 .env 文件
  ```bash
  cp .env.example .env
  ```

- [ ] 已在 .env 中配置 AI 提供商
  - [ ] 设置 `DEFAULT_AI_PROVIDER`
  - [ ] 添加对应的 API Key

- [ ] 已创建 logs 目录
  ```bash
  mkdir -p logs
  ```

### 4. 配置验证

- [ ] .env 文件包含必需的配置项
  - [ ] `DEFAULT_AI_PROVIDER` (openai 或 anthropic)
  - [ ] `OPENAI_API_KEY` 或 `ANTHROPIC_API_KEY`
  - [ ] 其他配置项已根据需要调整

## ✅ 功能测试

### 1. 启动测试

- [ ] 服务器成功启动
  ```bash
  python3 main.py
  ```

- [ ] 看到启动日志
  ```
  🤖 Starting Claw Bot AI...
  INFO: Application startup complete.
  INFO: Uvicorn running on http://0.0.0.0:8000
  ```

### 2. API 测试

- [ ] 健康检查端点正常
  ```bash
  curl http://localhost:8000/health
  # 期望输出: {"status":"healthy"}
  ```

- [ ] 根端点正常
  ```bash
  curl http://localhost:8000/
  # 期望输出包含 "name" 和 "version"
  ```

- [ ] API 文档可访问
  - [ ] Swagger UI: http://localhost:8000/docs
  - [ ] ReDoc: http://localhost:8000/redoc

### 3. 聊天功能测试

- [ ] 发送测试消息成功
  ```bash
  curl -X POST http://localhost:8000/chat \
    -H "Content-Type: application/json" \
    -d '{"message": "Hello, test message"}'
  ```

- [ ] 收到有效的 Bot 响应
  - [ ] 响应包含 "message" 字段
  - [ ] 响应包含 "conversation_id"
  - [ ] 没有 "error" 字段

### 4. 命令行客户端测试

- [ ] 命令行客户端可以启动
  ```bash
  python cli_client.py
  ```

- [ ] 可以与 Bot 对话
- [ ] 可以正常退出（输入 exit）

## ✅ 高级功能测试（可选）

### Docker 测试

- [ ] Docker 镜像构建成功
  ```bash
  docker build -t claw-bot-ai .
  ```

- [ ] Docker 容器运行正常
  ```bash
  docker run -p 8000:8000 --env-file .env claw-bot-ai
  ```

- [ ] Docker Compose 启动成功
  ```bash
  docker-compose up -d
  ```

### 单元测试

- [ ] 所有测试通过
  ```bash
  pytest tests/ -v
  ```

## ✅ 日志检查

- [ ] 日志文件已创建
  ```bash
  ls -l logs/claw_bot.log
  ```

- [ ] 日志内容正常
  ```bash
  tail -20 logs/claw_bot.log
  ```

- [ ] 没有严重错误（ERROR 或 CRITICAL）

## ✅ 性能检查

- [ ] 服务器启动时间 < 5 秒
- [ ] 单次请求响应时间合理（通常 2-10 秒，取决于 AI 提供商）
- [ ] 内存使用正常（< 500MB）

## ✅ 安全检查

- [ ] .env 文件未提交到版本控制
  ```bash
  git status  # .env 应该被 .gitignore 忽略
  ```

- [ ] API 密钥未在代码中硬编码
- [ ] 日志文件不包含敏感信息

## 🚨 常见问题排查

### 问题：服务器无法启动

检查项：
- [ ] Python 版本正确
- [ ] 虚拟环境已激活
- [ ] 所有依赖已安装
- [ ] 端口 8000 未被占用
  ```bash
  lsof -i :8000  # macOS/Linux
  netstat -ano | findstr :8000  # Windows
  ```

### 问题：API 调用失败

检查项：
- [ ] API 密钥正确
- [ ] API 密钥有足够配额
- [ ] 网络连接正常
- [ ] 查看日志获取详细错误
  ```bash
  tail -f logs/claw_bot.log
  ```

### 问题：响应速度慢

检查项：
- [ ] AI 提供商服务正常
- [ ] 网络延迟正常
- [ ] `MAX_CONTEXT_MESSAGES` 设置合理

## ✅ 完成确认

如果以上所有关键检查项都已完成，恭喜！Claw Bot AI 已成功安装并可以使用。

### 下一步

- [ ] 阅读 [QUICKSTART.md](QUICKSTART.md) 了解基本使用
- [ ] 阅读 [README.md](README.md) 了解完整功能
- [ ] 查看 [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) 了解架构
- [ ] 根据需要自定义 `config/bot_config.yaml`
- [ ] 开始集成到你的应用中

---

安装日期：__________
安装者：__________
备注：__________
