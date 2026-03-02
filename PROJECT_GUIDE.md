# Claw Bot AI - 项目功能与代码结构说明

本文档描述项目的各功能板块、整体代码结构及实现方式。

---

## 一、项目概述

Claw Bot AI 是一个智能 AI 机器人框架，集成了：

- **AI 对话**：多模型支持（OpenAI / Anthropic / Groq / OpenRouter）
- **活动追踪**：从 GitHub 拉取 commits、PR，落库并统计
- **日报 / 周报**：基于活动记录自动生成结构化报告（支持 AI 归纳或规则兜底）
- **通知推送**：邮件、Telegram、WhatsApp
- **Web 前端**：日报 / 周报可视化页面

---

## 二、功能板块说明

### 1. AI 对话 (Chat)

| 功能 | 说明 |
|------|------|
| 多轮对话 | 支持带上下文的多轮对话，可指定 `conversation_id` 续聊 |
| 多模型 | 支持 OpenAI、Anthropic Claude、Groq、OpenRouter 等 |
| 对话管理 | 可列出、查看、删除对话 |

**实现位置**：`src/bot/claw_bot.py`、`src/bot/ai_provider.py`

---

### 2. 活动追踪 (Activity Tracking)

| 功能 | 说明 |
|------|------|
| GitHub 同步 | 从配置的仓库拉取 commits、PR，转为统一 `ActivityEvent` |
| 多仓库 | 支持 `.env` 中配置多个 `owner/repo`，一次同步全部 |
| 落库 | 使用 SQLite 存储，支持按用户、日期、项目查询 |

**实现位置**：`src/providers/github_provider.py`、`src/services/activity_service.py`、`src/models/activity_orm.py`

---

### 3. 日报 / 周报 (Reports)

| 功能 | 说明 |
|------|------|
| 日报生成 | 按用户 + 日期，从 DB 查活动，调用 AI 生成结构化日报 |
| 周报生成 | 按用户 + 日期范围，支持周报格式 |
| 兜底模式 | AI 调用失败时，自动降级为规则汇总，保证流程可跑通 |

**实现位置**：`src/services/report_service.py`

---

### 4. 通知推送 (Notifications)

| 功能 | 说明 |
|------|------|
| 邮件 | SMTP 发送，支持 HTML |
| Telegram | 文本、图片，可获取 updates 拿 chat_id |
| WhatsApp | 基于 Twilio 或 Business API |

**实现位置**：`src/utils/email_sender.py`、`src/utils/telegram_sender.py`、`src/utils/whatsapp_sender.py`

---

### 5. Web 前端 (Daily / Weekly Report UI)

| 功能 | 说明 |
|------|------|
| 日报视图 | 按项目分组展示当日 commits / PR |
| 周报视图 | 按日期 + 项目分组展示一周活动 |
| 同步 | 一键同步配置的 GitHub 仓库 |

**实现位置**：`static/activities.html`，访问路径 `/daily`

---

## 三、代码结构

```
claw-bot-ai/
├── main.py                    # 入口：启动 uvicorn
├── run_daily_report_once.py   # 一次性脚本：同步 + 生成日报
├── cli_client.py              # 命令行聊天客户端
│
├── src/
│   ├── __init__.py
│   ├── db.py                  # SQLAlchemy 引擎、Session、建表
│   │
│   ├── bot/                   # AI 对话
│   │   ├── ai_provider.py     # AI 提供商（OpenAI / Anthropic）
│   │   └── claw_bot.py        # 对话逻辑、上下文管理
│   │
│   ├── handlers/
│   │   └── api.py             # FastAPI 路由、所有 HTTP 接口
│   │
│   ├── models/                # 数据模型
│   │   ├── message.py         # BotRequest、BotResponse、Conversation
│   │   ├── notification.py    # 通知请求模型
│   │   ├── activity.py        # ActivityEvent、ActivityQuery
│   │   └── activity_orm.py    # activities 表 ORM
│   │
│   ├── providers/             # 外部数据源
│   │   └── github_provider.py # GitHub API → ActivityEvent
│   │
│   ├── services/             # 业务服务
│   │   ├── activity_service.py  # 活动落库、查询
│   │   └── report_service.py   # 日报 / 周报生成
│   │
│   └── utils/
│       ├── config.py         # 配置（Pydantic Settings）
│       ├── logger.py         # 日志
│       ├── email_sender.py
│       ├── telegram_sender.py
│       └── whatsapp_sender.py
│
├── static/
│   └── activities.html       # 日报 / 周报前端页面
│
├── tests/
├── examples/
├── logs/
└── *.md                      # 文档
```

---

## 四、实现说明

### 4.1 AI 对话流程

```
用户请求 → BotRequest → ClawBot.process_message()
  → 取/建 Conversation → 取最近 N 条消息
  → AIProvider.generate_response() → 返回 BotResponse
```

- 对话存在内存中，重启会丢失
- `AIProvider` 抽象类，`OpenAIProvider`、`AnthropicProvider` 实现

### 4.2 活动追踪流程

```
GitHub API (commits, PRs) → GitHubProvider.fetch_repo_activities()
  → 转为 ActivityEvent 列表
  → ActivityService.upsert_activities() → 写入 activities 表
```

- `ActivityEvent` 统一结构：id、source、type、user_id、project_name、timestamp、url 等
- 支持多仓库：`Settings.get_github_repos()` 返回 `[(owner, repo), ...]`

### 4.3 日报生成流程

```
GET /activities?user_id=&date= → 从 DB 查 ActivityEvent
  → ReportService.generate_user_daily_report()
  → 构造 prompt → AIProvider 生成文本
  → 失败时 → _fallback_daily_report() 规则汇总
```

### 4.4 配置与多仓库

- 单仓库：`GITHUB_DEFAULT_OWNER` + `GITHUB_DEFAULT_REPO`
- 多仓库：`GITHUB_REPOS=owner1/repo1,owner2/repo2`（优先）

---

## 五、API 端点一览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 服务信息 |
| GET | `/health` | 健康检查 |
| GET | `/daily` | 日报 / 周报前端页面 |
| GET | `/config/github-repos` | 已配置的 GitHub 仓库列表 |
| | | |
| POST | `/chat` | AI 对话 |
| GET | `/conversations` | 列出对话 |
| GET | `/conversations/{id}` | 获取对话详情 |
| DELETE | `/conversations/{id}` | 删除对话 |
| | | |
| GET | `/activities` | 按 user_id、date（及 end_date）查活动 |
| POST | `/activities/github/sync` | 同步 GitHub 活动到 DB |
| | | |
| POST | `/reports/user/daily` | 手动传入活动列表生成日报 |
| GET | `/reports/user/daily/auto` | 从 DB 查活动并生成日报 |
| | | |
| POST | `/send-email` | 发邮件 |
| POST | `/send-telegram` | 发 Telegram 消息 |
| POST | `/send-telegram-photo` | 发 Telegram 图片 |
| GET | `/telegram/updates` | 获取 Telegram updates |
| POST | `/send-whatsapp` | 发 WhatsApp 消息 |
| POST | `/send-whatsapp-template` | 发 WhatsApp 模板消息 |

---

## 六、配置项速查

| 变量 | 说明 |
|------|------|
| `DEFAULT_AI_PROVIDER` | openai / anthropic |
| `OPENAI_API_KEY` | OpenAI / Groq / OpenRouter key |
| `ANTHROPIC_API_KEY` | Claude key |
| `GITHUB_TOKEN` | GitHub PAT（私有仓库需配置） |
| `GITHUB_REPOS` | 多仓库，逗号分隔 `owner/repo` |
| `GITHUB_DEFAULT_OWNER` | 单仓库 owner |
| `GITHUB_DEFAULT_REPO` | 单仓库 repo |
| `DATABASE_URL` | 默认 `sqlite:///./claw_bot.db` |

---

## 七、快速使用

```bash
# 启动服务
python3 main.py
# 或
uvicorn src.handlers.api:app --reload

# 访问
# - API 文档: http://localhost:8000/docs
# - 日报页面: http://localhost:8000/daily

# 一次性生成日报（脚本）
python run_daily_report_once.py --user-id your@email.com --date 2026-02-26
```

---

*最后更新：2026-02*
