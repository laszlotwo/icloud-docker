# 🏠 家庭AI助理

一个**自托管、隐私优先**的中文家庭AI助理，支持语音对话，可部署在 NAS（群晖/威联通）的 Docker 环境中。

敏感数据（账号密码）全部本地加密存储，**密码内容永不发送给 AI**。

---

## ✨ 功能

| 模块 | 说明 |
|------|------|
| 💬 **文字对话** | 与 AI 自然对话，自动调用下面各模块的能力 |
| 🎤 **语音对话** | 中文语音识别（Whisper）+ 中文语音合成（edge-tts），按住说话 |
| 📖 **设备说明书** | 存储家电使用说明，全文搜索，"扫地机器人怎么用？"直接问 |
| 🔐 **密码库** | AES-256-GCM 加密存储账号密码，主密码不落盘 |
| 📍 **物品位置** | 记录家中物品存放位置，"护照放在哪？"直接问 |
| 💰 **开销记录** | 记账与消费统计，"这个月花了多少钱？"直接问 |
| ⏰ **提醒闹钟** | 一次性/每天/每周/Cron 定时提醒，容器重启后自动恢复 |

---

## 🛠 技术栈

- **后端**：FastAPI + SQLAlchemy + Alembic（SQLite）
- **AI**：Google Gemini 或 Anthropic Claude（可配置切换）
- **语音识别**：faster-whisper（本地运行，中文）
- **语音合成**：edge-tts（免费微软中文语音）
- **定时任务**：APScheduler（持久化到 SQLite）
- **加密**：cryptography（PBKDF2 + AES-256-GCM）
- **前端**：纯 HTML/CSS/JS（无构建步骤）
- **容器**：Docker 多架构（amd64 + arm64）

---

## 🚀 快速开始（NAS 部署）

### 1. 获取代码

把 `home-ai-assistant/` 文件夹上传到 NAS，例如 `/volume1/docker/home-ai-assistant/`。

### 2. 创建配置文件

```bash
cd /volume1/docker/home-ai-assistant
cp .env.example .env
```

编辑 `.env`，填写必要项：

```env
# AI 提供商：gemini 或 claude
AI_PROVIDER=gemini

# Gemini API Key（从 https://aistudio.google.com/apikey 获取，有免费额度）
GEMINI_API_KEY=AIza你的key
GEMINI_MODEL=gemini-2.0-flash

# 会话加密密钥（生成方法：openssl rand -hex 32）
SECRET_KEY=你生成的随机字符串

# 数据存储路径（NAS 上的实际路径）
DATA_PATH=/volume1/docker/home-ai-assistant/data

# 访问端口
HOST_PORT=8080

# 语音识别模型：tiny（最快）/ base（推荐）/ small（最准）
WHISPER_MODEL=base

# 时区
TZ=Asia/Shanghai
```

> 如果用 Claude，把 `AI_PROVIDER=claude` 并填 `ANTHROPIC_API_KEY`。

### 3. 启动

**命令行（SSH 到 NAS）：**

```bash
docker compose up -d --build      # 首次构建需几分钟，会下载 Whisper 模型
docker compose logs -f            # 查看日志
```

**群晖 Container Manager：**
项目 → 新增 → 选择本目录 → 自动读取 `docker-compose.yml` → 完成。

### 4. 访问

浏览器打开 `http://NAS的IP:8080`，例如 `http://192.168.1.100:8080`。

---

## ⚙️ 配置项说明

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `AI_PROVIDER` | `gemini` | AI 提供商：`gemini` 或 `claude` |
| `GEMINI_API_KEY` | - | Gemini API Key |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Gemini 模型 |
| `ANTHROPIC_API_KEY` | - | Claude API Key（用 Claude 时填） |
| `SECRET_KEY` | - | 会话加密密钥（**必填**） |
| `WHISPER_MODEL` | `base` | 语音识别模型大小 |
| `TTS_VOICE` | `zh-CN-XiaoxiaoNeural` | 中文语音（女声）|
| `HOST_PORT` | `8080` | 对外端口 |
| `TZ` | `Asia/Shanghai` | 时区 |
| `VAULT_SESSION_TIMEOUT_MINUTES` | `30` | 密码库解锁后自动锁定时间 |

### Whisper 模型按 NAS 性能选择

| NAS CPU | 推荐模型 |
|---------|---------|
| ARM（低功耗，如 J 系列） | `tiny` |
| Intel Celeron/Atom（如 DS923+） | `base` |
| Intel Core i 系列 | `small` |

### Gemini 模型选择

| 模型 | 说明 |
|------|------|
| `gemini-2.0-flash` | 默认推荐，快、免费额度大 |
| `gemini-2.5-flash` | 更新更强（如可用） |
| `gemini-1.5-flash` | 老牌稳定 |

---

## 🔒 隐私与安全

- **密码库**：用主密码经 PBKDF2（48万次迭代）派生密钥，AES-256-GCM 加密每条记录；主密码只存在于内存，不写入磁盘、不进日志、不发送给 AI。
- **AI 工具**：AI 只能看到密码库条目的**标题**，无法读取任何密码内容。
- **数据本地化**：所有数据存储在你 NAS 上的 `DATA_PATH`，不上云。仅对话文本会发送给所选 AI 提供商（Gemini/Claude）。

---

## 🌐 反向代理（可选，HTTPS + 域名）

群晖：控制面板 → 登录门户 → 高级 → 反向代理服务器 → 新增

| 项 | 值 |
|----|----|
| 来源协议/主机/端口 | HTTPS / `home.你的域名.com` / 443 |
| 目标协议/主机/端口 | HTTP / `localhost` / 8080 |

⚠️ 务必勾选 **启用 WebSocket**（语音功能依赖）。

---

## 🧰 常用维护命令

```bash
docker compose ps                 # 查看状态
docker compose logs -f            # 查看日志
docker compose down               # 停止
docker compose up -d --build      # 更新代码后重建
cp -r data/ data_backup_$(date +%Y%m%d)/   # 备份数据
```

---

## 🧪 本地开发

```bash
pip install -r requirements-dev.txt
PYTHONPATH=. python -m pytest tests/ -v        # 运行测试
PYTHONPATH=. uvicorn app.main:app --reload --port 8080   # 本地启动
```

---

## 📁 项目结构

```
home-ai-assistant/
├── app/
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置
│   ├── database.py          # 数据库 + FTS5 全文搜索
│   ├── models/              # 数据模型
│   ├── schemas/             # 请求/响应模型
│   ├── routers/             # API 路由（chat/voice/manuals/vault/...）
│   ├── services/
│   │   ├── ai.py            # AI 提供商门面（gemini/claude 分发）
│   │   ├── gemini_client.py # Gemini 对话循环
│   │   ├── claude_client.py # Claude 对话循环
│   │   ├── tool_definitions.py  # AI 工具定义 + 系统提示词
│   │   ├── tool_handlers.py # 工具的实际执行逻辑
│   │   ├── encryption.py    # 密码库加密
│   │   ├── stt.py / tts.py  # 语音识别/合成
│   │   └── scheduler.py     # 定时提醒
│   └── static/              # 前端页面
├── alembic/                 # 数据库迁移
├── tests/                   # 测试
├── Dockerfile
├── docker-compose.yml
└── .env.example
```
