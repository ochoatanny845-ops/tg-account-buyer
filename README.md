# Telegram 账号收购机器人

自动化收购 Telegram 账号的机器人系统。

## 功能特性

### 用户功能
- ✅ 接码登录（手动输入验证码）
- ✅ 上传 Session 文件
- ✅ 查询收购价格（按国家）
- ✅ 余额查询
- ✅ 提现申请（TRC20）

### 管理员功能
- ✅ 审核用户上传的账号
- ✅ 动态调整收购价格
- ✅ 提现审核
- ✅ 系统统计

## 技术栈

- Python 3.12+
- python-telegram-bot 22.5
- Telethon (Telegram Client)
- SQLite 数据库
- Cryptography (Session 加密)

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 到 `.env` 并填写配置：

```bash
cp .env.example .env
```

配置说明：
```env
# Telegram Bot Token (从 @BotFather 获取)
BOT_TOKEN=your_bot_token_here

# Telegram API 配置 (从 https://my.telegram.org 获取)
API_ID=your_api_id
API_HASH=your_api_hash

# 管理员配置
ADMIN_GROUP_ID=-100xxxxxxxxxx  # 管理员群组 ID
ADMIN_USER_IDS=123456789,987654321  # 管理员用户 ID（逗号分隔）

# 数据库配置
DATABASE_URL=sqlite:///buyer_bot.db

# 提现配置
MIN_WITHDRAWAL=10  # 最低提现金额 (USDT)
WITHDRAWAL_FEE=1   # 提现手续费 (USDT)

# 默认收购价格
DEFAULT_PRICE=0.2  # 默认价格 (USDT)
```

### 3. 运行机器人

```bash
python main.py
```

## 代码质量检查

在提交代码前，建议运行代码质量检查：

### Windows
```cmd
pre-commit-check.bat
```

### Linux/Mac
```bash
python check_code.py
```

这将检查：
- ✅ 语法错误
- ✅ 重复定义的函数
- ✅ 已删除函数的调用
- ✅ 导入错误

## 项目结构

```
tg-account-buyer/
├── main.py                 # 主程序入口
├── bot/                    # 机器人核心代码
│   ├── __init__.py
│   ├── config.py           # 配置管理
│   ├── database.py         # 数据库模型
│   ├── handlers/           # 命令处理器
│   │   ├── __init__.py
│   │   ├── user.py         # 用户功能
│   │   ├── admin.py        # 管理员功能
│   │   └── session.py      # Session 处理
│   ├── utils/              # 工具函数
│   │   ├── __init__.py
│   │   ├── validator.py    # Session 验证
│   │   ├── country.py      # 国家/区号映射
│   │   └── crypto.py       # 加密工具
│   └── keyboards/          # 键盘布局
│       ├── __init__.py
│       ├── user_kb.py      # 用户键盘
│       └── admin_kb.py     # 管理员键盘
├── sessions/               # Session 文件存储目录
├── requirements.txt        # Python 依赖
├── .env.example            # 环境变量示例
├── .gitignore              # Git 忽略规则
└── README.md               # 项目文档
```

## 使用指南

### 用户端

1. **开始使用**：发送 `/start` 启动机器人
2. **查看价格**：点击"💰 查看价格"按钮
3. **上传账号**：
   - 方式 1：点击"📱 接码登录"，输入手机号和验证码
   - 方式 2：点击"📤 上传 Session"，发送 session 文件
4. **查看余额**：点击"💵 我的余额"
5. **申请提现**：
   - 点击"💸 申请提现"
   - 输入 TRC20 地址
   - 输入提现金额

### 管理员端

1. **审核账号**：
   - 机器人会自动转发用户上传的 Session 到管理群
   - 点击 [✅ 通过] 或 [❌ 拒绝] 按钮
   - 通过后用户余额自动增加

2. **管理价格**：
   - 发送 `/price` 查看所有价格
   - 发送 `/setprice +86 1.5` 设置中国账号价格为 1.5 USDT
   - 发送 `/setprice +1 0.8` 设置美国账号价格为 0.8 USDT

3. **处理提现**：
   - 收到提现申请通知
   - 手动转账到用户提供的 TRC20 地址
   - 点击 [✅ 已付款] 完成审核

## 数据库结构

### users 表
- user_id: 用户 Telegram ID
- username: 用户名
- balance: 余额 (USDT)
- trc20_address: TRC20 地址
- created_at: 注册时间

### sessions 表
- id: 自增 ID
- user_id: 提交用户 ID
- phone: 手机号
- country_code: 国家区号
- session_file: Session 文件路径
- status: 状态 (pending/approved/rejected)
- price: 收购价格
- created_at: 提交时间
- reviewed_at: 审核时间
- reviewer_id: 审核人 ID

### prices 表
- country_code: 国家区号 (+86, +1, +44...)
- country_name: 国家名称
- flag_emoji: 国旗 Emoji
- price: 收购价格 (USDT)
- updated_at: 更新时间

### withdrawals 表
- id: 自增 ID
- user_id: 用户 ID
- amount: 提现金额
- fee: 手续费
- trc20_address: TRC20 地址
- status: 状态 (pending/completed/rejected)
- created_at: 申请时间
- completed_at: 完成时间
- admin_id: 处理管理员 ID

## 安全特性

- ✅ Session 文件加密存储
- ✅ 2FA 验证检查
- ✅ 国家区号验证
- ✅ 管理员权限验证
- ✅ 提现金额限制
- ✅ 防重复提交

## 部署

### 本地部署
```bash
python main.py
```

### Docker 部署
```bash
docker build -t tg-buyer-bot .
docker run -d --env-file .env tg-buyer-bot
```

### 系统服务部署
```bash
# 创建 systemd 服务
sudo nano /etc/systemd/system/tg-buyer-bot.service

# 启动服务
sudo systemctl start tg-buyer-bot
sudo systemctl enable tg-buyer-bot
```

## 常见问题

### Q: Session 文件验证失败？
A: 确保：
- Session 文件是有效的 Telethon session
- 账号已开启 2FA
- API_ID 和 API_HASH 配置正确

### Q: 如何添加新国家？
A: 管理员发送：`/setprice +新区号 价格`，系统会自动创建

### Q: 提现多久到账？
A: 取决于管理员审核速度，通常 24 小时内

## 更新日志

### v1.0.0 (2026-04-01)
- ✅ 初始版本发布
- ✅ 用户上传 Session 功能
- ✅ 接码登录功能
- ✅ 价格查询和管理
- ✅ 提现申请和审核
- ✅ 管理员审核系统

## 许可证

MIT License

## 作者

ochoatanny845-ops

## 支持

如有问题，请联系管理员。
