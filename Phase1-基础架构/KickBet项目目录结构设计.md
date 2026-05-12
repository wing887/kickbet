# KickBet 项目目录结构设计

> Phase 1: 基础架构层 - 项目骨架规划

---

## 一、项目整体结构

```
kickbet/
├── backend/                    # Flask后端
│   ├── app/
│   │   ├── __init__.py        # Flask应用初始化
│   │   ├── config.py          # 配置管理
│   │   ├── extensions.py      # Flask扩展初始化
│   │   ├── routes/            # 路由模块
│   │   │   ├── __init__.py
│   │   │   ├── auth.py        # 认证相关路由
│   │   │   ├── matches.py     # 比赛数据路由
│   │   │   ├── predictions.py # 预测相关路由
│   │   │   ├── combo.py       # 组合投注路由
│   │   │   ├── tracker.py     # 投注追踪路由
│   │   │   ├── odds.py        # 赔率变动路由
│   │   │   ├── subscribe.py   # 订阅相关路由
│   │   │   └── learn.py       # 教育内容路由
│   │   ├── models/            # 数据模型
│   │   │   ├── __init__.py
│   │   │   ├── user.py        # 用户模型
│   │   │   ├── match.py       # 比赛模型
│   │   │   ├── prediction.py  # 预测模型
│   │   │   ├── odds.py        # 赔率模型
│   │   │   ├── tracker.py     # 投注追踪模型
│   │   │   └── subscription.py # 订阅模型
│   │   ├── services/          # 业务逻辑层
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── match_service.py
│   │   │   ├── prediction_service.py
│   │   │   ├── combo_service.py
│   │   │   ├── tracker_service.py
│   │   │   ├── odds_service.py
│   │   │   └── news_service.py
│   │   ├── utils/             # 工具函数
│   │   │   ├── __init__.py
│   │   │   ├── auth_decorators.py  # 权限装饰器
│   │   │   ├── rate_limiter.py     # Rate Limit工具
│   │   │   ├── response.py         # 响应格式化
│   │   │   └── validators.py       # 输入验证
│   │   └── external/          # 外部API封装
│   │   │   ├── __init__.py
│   │   │   ├── odds_api_io.py      # Odds-API.io封装
│   │   │   ├── football_data_org.py # Football-Data.org封装
│   │   │   ├── news_fetcher.py     # 新闻获取
│   │   │   └── llm_client.py       # LLM调用封装
│   ├── migrations/            # 数据库迁移(预留)
│   ├── tests/                 # 测试
│   │   ├── __init__.py
│   │   ├── test_auth.py
│   │   ├── test_predictions.py
│   │   └── test_api.py
│   ├── data/                  # SQLite数据库文件
│   │   ├── kickbet_users.db
│   │   ├── kickbet_predictions.db
│   │   └bet_news.db
│   │   └── kickbet_logs.db
│   ├── logs/                  # 日志文件
│   ├── requirements.txt       # Python依赖
│   ├── run.py                 # 启动脚本
│   └── wsgi.py                # 生产部署入口
│
├── frontend/                  # Vue.js前端
│   ├── public/
│   │   ├── index.html
│   │   ├── favicon.ico
│   │   └── manifest.json      # PWA配置
│   ├── src/
│   │   ├── main.js            # Vue入口
│   │   ├── App.vue            # 根组件
│   │   ├── router/            # 路由配置
│   │   │   ├── index.js
│   │   │   └ routes.js
│   │   ├── store/             # Pinia状态管理
│   │   │   ├── index.js
│   │   │   ├── modules/
│   │   │   │   ├── user.js    # 用户状态
│   │   │   │   ├── matches.js # 比赛状态
│   │   │   │   └predictions.js # 预测状态
│   │   ├── components/        # 组件
│   │   │   ├── common/        # 通用组件
│   │   │   │   ├── Header.vue
│   │   │   │   ├── Footer.vue
│   │   │   │   ├── Loading.vue
│   │   │   │   ├── Modal.vue
│   │   │   │   ├── Card.vue
│   │   │   │   ├── Button.vue
│   │   │   │   ├── OddsDisplay.vue
│   │   │   │   └ ConfidenceBadge.vue
│   │   │   ├── home/          # 首页组件
│   │   │   │   ├── DailyPick.vue
│   │   │   │   ├── LeagueTabs.vue
│   │   │   │   ├── MatchList.vue
│   │   │   │   ├── OddsCard.vue
│   │   │   ├── match/         # 比赛详情组件
│   │   │   │   ├── MatchHeader.vue
│   │   │   │   ├── OddsPanel.vue
│   │   │   │   ├── AnalysisL2.vue
│   │   │   │   ├── AnalysisL3.vue
│   │   │   │   ├── AnalysisL4.vue
│   │   │   │   ├── TeamStats.vue
│   │   │   │   ├── OddsHistory.vue
│   │   │   ├── combo/         # 组合投注组件
│   │   │   │   ├── MatchSelector.vue
│   │   │   │   ├── BudgetInput.vue
│   │   │   │   ├── KellyResult.vue
│   │   │   │   ├── ParlaySuggestion.vue
│   │   │   ├── tracker/       # 投注追踪组件
│   │   │   │   ├── RecordForm.vue
│   │   │   │   ├── RecordList.vue
│   │   │   │   ├── Statistics.vue
│   │   │   │   ├── ROICard.vue
│   │   │   ├── auth/          # 认证组件
│   │   │   │   ├── LoginForm.vue
│   │   │   │   ├── RegisterForm.vue
│   │   │   │   ├── SubscribeForm.vue
│   │   │   ├── profile/       # 用户中心组件
│   │   │   │   ├── ProfileHeader.vue
│   │   │   │   ├── Settings.vue
│   │   │   │   ├── History.vue
│   │   ├── views/             # 页面视图
│   │   │   ├── Home.vue       # 首页
│   │   │   ├── Matches.vue    # 比赛列表
│   │   │   ├── MatchDetail.vue # 比赛详情
│   │   │   ├── Combo.vue      # 组合投注
│   │   │   ├── Tracker.vue    # 投注追踪
│   │   │   ├── Learn.vue      # 教育中心
│   │   │   ├── Login.vue      # 登录
│   │   │   ├── Register.vue   # 注册
│   │   │   ├── Subscribe.vue  # 订阅
│   │   │   ├── Profile.vue    # 个人中心
│   │   ├── api/               # API调用封装
│   │   │   ├── index.js       # Axios配置
│   │   │   ├── auth.js
│   │   │   ├── matches.js
│   │   │   ├── predictions.js
│   │   │   ├── combo.js
│   │   │   ├── tracker.js
│   │   ├── styles/            # 样式
│   │   │   ├── variables.css  # CSS变量
│   │   │   ├── global.css     # 全局样式
│   │   │   ├── components/    # 组件样式
│   │   ├── utils/             # 工具函数
│   │   │   ├── format.js      # 格式化工具
│   │   │   ├── auth.js        # 认证工具
│   │   │   ├── date.js        # 日期工具
│   │   ├── assets/            # 静态资源
│   │   │   ├── images/
│   │   │   ├── icons/
│   │   ├── composables/       # Vue组合式函数
│   │   │   ├── useAuth.js
│   │   │   ├── useOdds.js
│   │   │   ├── usePrediction.js
│   ├── vite.config.js         # Vite配置
│   ├── package.json           # NPM依赖
│   ├── tsconfig.json          # TypeScript配置(可选)
│   └── pwa-assets.config.js   # PWA图标配置
│
├── predictor_engine/          # 预测引擎(独立模块)
│   ├── __init__.py
│   ├── poisson_predictor.py   # Poisson预测
│   ├── kelly_criterion.py     # Kelly公式
│   ├── probability_calculator.py # 概率计算
│   ├── match_analyzer.py      # 比赛分析
│   ├── confidence_estimator.py # 置信度评估
│   ├── analysis_generator.py  # 分析内容生成
│   │   ├── l2_generator.py    # L2初级分析
│   │   ├── l3_generator.py    # L3进阶分析
│   │   ├── l4_generator.py    # L4高阶分析
│   ├── combo_engine/          # 组合投注引擎
│   │   ├── kelly_allocator.py
│   │   ├── parlay_optimizer.py
│   │   ├── risk_manager.py
│   │   └ combo_generator.py
│   ├── tests/
│   │   ├── test_poisson.py
│   │   ├── test_kelly.py
│   │   └test_combo.py
│   ├── requirements.txt
│
├── odds_movement_engine/      # 赔率变动分析引擎
│   ├── __init__.py
│   ├── odds_tracker.py        # 赔率追踪
│   ├── news_fetcher.py        # 新闻获取
│   ├── news_analyzer.py       # AI新闻分析
│   ├── translator.py          # 英文翻译
│   ├── movement_explainer.py  # 变动解释生成
│   ├── news_sources/          # 新闻源封装
│   │   ├── __init__.py
│   │   ├── espn.py
│   │   ├── bbc_sport.py
│   │   ├── sky_sports.py
│   │   └ goal_com.py
│   ├── tests/
│   ├── requirements.txt
│
├── data_collector/            # 数据采集调度器
│   ├── __init__.py
│   ├── scheduler.py           # 定时调度
│   ├── odds_collector.py      # 赔率采集
│   ├── match_collector.py     # 比赛采集
│   ├── news_collector.py      # 新闻采集
│   ├── stats_collector.py     # 球队统计采集
│   ├── config.yaml            # 采集配置
│   ├── requirements.txt
│
├── docs/                      # 项目文档
│   ├── architecture/          # 架构文档
│   ├── api/                   # API文档
│   ├── database/              # 数据库文档
│   ├── deployment/            # 部署文档
│   └── development/           # 开发指南
│
├── scripts/                   # 工具脚本
│   ├── init_db.py             # 数据库初始化
│   ├── seed_data.py           # 测试数据填充
│   ├── backup.sh              # 备份脚本
│   ├── deploy.sh              # 部署脚本
│
├── docker/                    # Docker配置
│   ├── docker-compose.yml     # 本地开发环境
│   ├── Dockerfile.backend     # 后端镜像
│   ├── Dockerfile.frontend    # 前端镜像
│   ├── nginx.conf             # Nginx配置
│
├── .gitignore
├── README.md
└── LICENSE
```

---

## 二、后端模块职责

### routes/ - 路由层

| 文件 | 职责 | 对应API |
|-----|------|---------|
| auth.py | 用户认证 | /auth/* |
| matches.py | 比赛数据 | /matches/*, /leagues/* |
| predictions.py | 预测分析 | /predictions/* |
| combo.py | 组合投注 | /combo/* |
| tracker.py | 投注追踪 | /tracker/* |
| odds.py | 赔率变动 | /odds-movement/* |
| subscribe.py | 订阅支付 | /subscribe/* |
| learn.py | 教育内容 | /learn/* |

### services/ - 业务逻辑层

| 文件 | 职责 |
|-----|------|
| auth_service.py | 注册、登录、JWT管理、权限校验 |
| match_service.py | 比赛查询、赔率聚合 |
| prediction_service.py | 预测生成、分析内容组装 |
| combo_service.py | Kelly分配、串关生成 |
| tracker_service.py | 投注记录管理、统计计算 |
| odds_service.py | 赔率历史、变动检测 |
| news_service.py | 新闻获取、AI分析、翻译 |

### external/ - 外部API封装

| 文件 | 职责 |
|-----|------|
| odds_api_io.py | Odds-API.io调用、Rate Limit管理 |
| football_data_org.py | Football-Data.org调用 |
| news_fetcher.py | ESPN/BBC/SkySports新闻获取 |
| llm_client.py | OpenAI/DeepSeek调用封装 |

---

## 三、前端模块职责

### views/ - 页面

| 页面 | 路径 | 说明 |
|-----|------|------|
| Home.vue | / | 首页：每日推荐 + 赔率列表 |
| Matches.vue | /matches | 比赛列表页 |
| MatchDetail.vue | /match/:id | 比赛详情 + 预测分析 |
| Combo.vue | /combo | 组合投注页面 |
| Tracker.vue | /tracker | 投注追踪页面 |
| Learn.vue | /learn | 教育中心 |
| Login.vue | /login | 登录页 |
| Register.vue | /register | 注册页 |
| Subscribe.vue | /subscribe | 订阅页 |
| Profile.vue | /profile | 个人中心 |

### components/ - 组件分类

| 目录 | 内容 |
|-----|------|
| common/ | 通用UI组件（Header、Footer、Modal、Card等） |
| home/ | 首页专用组件（DailyPick、LeagueTabs等） |
| match/ | 比赛详情组件（OddsPanel、AnalysisL2/L3/L4等） |
| combo/ | 组合投注组件（MatchSelector、KellyResult等） |
| tracker/ | 投注追踪组件（RecordForm、Statistics等） |
| auth/ | 认证组件（LoginForm、RegisterForm等） |
| profile/ | 用户中心组件 |

---

## 四、CSS变量定义

```css
/* styles/variables.css */

:root {
  /* 背景色 */
  --bg-primary: #08090a;
  --bg-card: #121314;
  --bg-hover: #1a1b1c;
  --bg-input: #0d0e0f;
  
  /* 文字色 */
  --text-primary: #ffffff;
  --text-secondary: #8b8b8b;
  --text-muted: #5a5a5a;
  
  /* 边框色 */
  --border: #2a2b2c;
  --border-light: #3a3b3c;
  
  /* 强调色 */
  --accent-success: #00d4aa;
  --accent-warning: #ff6b6b;
  --accent-neutral: #ffa500;
  --accent-info: #4a90d9;
  
  /* 字体 */
  --font-main: 'Inter', -apple-system, sans-serif;
  --font-mono: 'Roboto Mono', monospace;
  --font-code: 'Fira Code', monospace;
  
  /* 间距 */
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;
  
  /* 圆角 */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  
  /* 动画 */
  --transition-fast: 150ms ease;
  --transition-normal: 300ms ease;
}
```

---

## 五、开发启动步骤

### 1. 后端初始化

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python scripts/init_db.py

# 启动开发服务器
python run.py
```

### 2. 前端初始化

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

---

## 六、下一步

Phase 1 细化完成后，将创建：

1. `backend/app/__init__.py` - Flask应用骨架
2. `backend/app/config.py` - 配置文件
3. `backend/scripts/init_db.py` - 数据库初始化脚本
4. `frontend/src/main.js` - Vue入口
5. `frontend/src/router/index.js` - 路由配置