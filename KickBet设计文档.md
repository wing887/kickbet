# 足球博彩平台完整设计文档

> 版本: 1.0.0
> 创建日期: 2026-05-07
> 状态: 设计阶段

---

## 目录

1. [产品概述](#1-产品概述)
2. [技术架构](#2-技术架构)
3. [数据库设计](#3-数据库设计)
4. [API接口设计](#4-api接口设计)
5. [前端设计](#5-前端设计)
6. [关键业务流程](#6-关键业务流程)
7. [安全设计](#7-安全设计)
8. [运维设计](#8-运维设计)
9. [开发计划](#9-开发计划)

---

## 1. 产品概述

### 1.1 产品定位

**产品名称**: 暂定 "KickBet" (足球博彩平台)

**目标市场**: 东南亚地区（菲律宾为主，多语言支持）

**用户定位**: 大众用户（新手友好，20-100美元投注区间）

**核心功能**: 
- 足球博彩（赛前投注 + Live Betting）
- Crash游戏（Aviator风格）

### 1.2 产品特色

| 特色 | 优先级 | 实现方式 |
|------|--------|----------|
| 新手友好 | P0 | 3步完成投注、引导流程、简化界面 |
| 快速体验 | P1 | WebSocket实时推送、秒级赔率更新 |
| 移动优先 | P1 | PWA应用、离线支持、响应式设计 |
| 公平验证 | P2 | Provably Fair算法（Crash游戏） |

### 1.3 核心用户场景

#### 场景1: 新用户首次投注
```
1. 用户打开网站 → 看到热门赛事推荐
2. 点击感兴趣的赛事 → 展示赔率选项
3. 选择结果 + 输入金额 → 点击投注
4. 支付（电子钱包）→ 注单确认
5. 查看注单状态 → 收到结果通知
```

#### 场景2: Live Betting体验
```
1. 用户进入Live Betting页面
2. 实时看到比赛进度 + 赔率变化
3. 比赛进行中随时投注
4. 比赛结束 → 秒级结算
5. 钱包余额自动更新
```

#### 场景3: Crash游戏
```
1. 用户进入Crash游戏页面
2. 看到飞机上升动画 + 倍数实时增加
3. 输入下注金额 → 等待下一局
4. 游戏开始 → 倍数上升
5. 点击"Cash Out" → 获得当前倍数收益
6. 验证游戏结果 → 可验证公平性
```

### 1.4 功能模块划分

```
KickBet Platform
├── 用户系统
│   ├── 注册/登录
│   ├── KYC验证
│   ├── 个人中心
│   └── 自我排除
├── 钱包系统
│   ├── 余额查询
│   ├── 充值（电子钱包）
│   ├── 提现
│   └── 交易历史
├── 体育博彩
│   ├── 赛事列表
│   ├── 赔率展示
│   ├── 投注单
│   ├── Live Betting
│   └── 注单管理
├── Crash游戏
│   ├── 游戏界面
│   ├── 下注/提现
│   ├── 历史记录
│   └── 公平验证
├── Admin后台
│   ├── 用户管理
│   ├── 注单管理
│   ├── 资金管理
│   ├── 赛事管理
│   └── 报表统计
```

---

## 2. 技术架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      用户接入层                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │  Web PWA   │  │  Desktop   │  │  Mobile    │            │
│  │ (Next.js)  │  │  Browser   │  │  Browser   │            │
│  └────────────┘  └────────────┘  └────────────┘            │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      CDN + 安全层                            │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │ Cloudflare │  │   WAF      │  │  GeoIP     │            │
│  │ (全球加速) │  │ (Bot检测)  │  │ (国家检测) │            │
│  └────────────┘  └────────────┘  └────────────┘            │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Go + Gin Framework                                  │   │
│  │  • JWT认证                                           │   │
│  │  • Rate Limiting (Redis)                            │   │
│  │  • CORS                                              │   │
│  │  • Request Validation                                │   │
│  │  • Prometheus Metrics                                │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│   Auth        │ │   Betting     │ │   Game        │
│   Service     │ │   Service     │ │   Service     │
│               │ │               │ │               │
│ • 用户注册    │ │ • 赛事查询    │ │ • Crash引擎   │
│ • JWT管理     │ │ • 投注处理    │ │ • WebSocket   │
│ • KYC集成     │ │ • 结算        │ │ • ProvablyFair│
│ • 权限控制    │ │ • 注单管理    │ │ • 历史查询    │
└───────────────┘ └───────────────┘ └───────────────┘
        │                 │                 │
        └─────────────────┼─────────────────┘
                          ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│   Wallet      │ │   Odds        │ │   Admin       │
│   Service     │ │   Service     │ │   Service     │
│               │ │               │ │               │
│ • 余额管理    │ │ • 赔率源API   │ │ • 用户管理    │
│ • 充值处理    │ │ • 赔率缓存    │ │ • 资金审核    │
│ • 提现处理    │ │ • WebSocket   │ │ • 赛事管理    │
│ • 交易记录    │ │   推送        │ │ • 报表生成    │
└───────────────┘ └───────────────┘ └───────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      数据层                                  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │ PostgreSQL │  │   Redis    │  │    NATS    │            │
│  │ (主数据)   │  │  (缓存)    │  │  (消息)    │            │
│  │            │  │            │  │            │            │
│  │ • 用户     │  │ • 会话     │  │ • 事件     │            │
│  │ • 钱包     │  │ • 赔率     │  │ • 结算     │            │
│  │ • 注单     │  │ • 限流     │  │ • 通知     │            │
│  │ • 赛事     │  │ • 游戏状态 │  │            │            │
│  └────────────┘  └────────────┘  └────────────┘            │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      外部服务                                │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │ Odds API   │  │  Payment   │  │    KYC     │            │
│  │(Sportradar)│  │ (GrabPay)  │  │ (第三方)   │            │
│  └────────────┘  └────────────┘  └────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 技术栈详情

#### 前端技术栈

| 类别 | 技术 | 版本 | 作用 |
|------|------|------|------|
| **框架** | Next.js | 15.x | SSR + App Router |
| **UI库** | shadcn/ui | 最新 | 组件库 + Tailwind |
| **状态** | Zustand | 5.x | 全局状态管理 |
| **数据获取** | TanStack Query | 5.x | API请求缓存 |
| **WebSocket** | 原生WebSocket | - | 实时通信 |
| **动画** | Framer Motion | 11.x | Crash动画 |
| **图表** | Recharts | 2.x | 赔率走势图 |
| **表单** | React Hook Form | 7.x | 表单验证 |
| **PWA** | next-pwa | 5.x | 离线支持 |

#### 后端技术栈

| 类别 | 技术 | 版本 | 作用 |
|------|------|------|------|
| **语言** | Go | 1.22+ | 高性能后端 |
| **Web框架** | Gin | 1.10+ | HTTP路由 |
| **WebSocket** | Gorilla | 1.5+ | 实时通信 |
| **数据库** | PostgreSQL | 16+ | 主数据存储 |
| **ORM** | sqlx + 自定义 | - | SQL操作 |
| **缓存** | Redis | 7+ | 赔率/会话缓存 |
| **消息队列** | NATS | 2.10+ | 事件驱动 |
| **认证** | JWT (golang-jwt) | 5.x | Token认证 |
| **监控** | Prometheus | - | Metrics |
| **日志** | zap | 1.27+ | 结构化日志 |

#### 基础设施

| 类别 | 技术 | 作用 |
|------|------|------|
| **CDN** | Cloudflare | 全球加速 + 安全 |
| **容器** | Docker | 服务容器化 |
| **编排** | Docker Compose | 本地开发 |
| **CI/CD** | GitHub Actions | 自动部署 |
| **监控** | Grafana + Prometheus | 可观测性 |
| **日志** | Loki | 日志聚合 |

### 2.3 服务拆分设计

基于lets-bet框架优化，拆分为6个微服务：

```go
// 服务入口结构
cmd/
├── gateway/      // API Gateway (单一入口)
├── auth/         // 认证服务 (新增)
├── betting/      // 投注服务 (合并engine + settlement)
├── game/         // 游戏服务 (Crash + 虚拟体育)
├── wallet/       // 钱包服务 (复用lets-bet)
├── odds/         // 赔率服务 (新增)
└── admin/        // 管理后台API (新增)
```

#### 服务职责划分

| 服务 | 职责 | 数据依赖 | 通信方式 |
|------|------|----------|----------|
| Gateway | 统一入口、认证、限流 | Redis (限流) | HTTP |
| Auth | 用户注册、JWT、KYC | PostgreSQL | HTTP + NATS |
| Betting | 投注处理、结算 | PostgreSQL + Redis | HTTP + NATS |
| Game | Crash引擎、游戏历史 | PostgreSQL + Redis | WebSocket |
| Wallet | 余额、充值、提现 | PostgreSQL | HTTP + NATS |
| Odds | 赔率获取、缓存、推送 | Redis | HTTP + WebSocket |
| Admin | 管理功能 | PostgreSQL | HTTP |

### 2.4 通信架构

```
┌──────────────────────────────────────────────┐
│              通信模式                         │
├──────────────────────────────────────────────┤
│                                              │
│  前端 → Gateway: HTTP REST + WebSocket       │
│                                              │
│  Gateway → 微服务: HTTP (内部调用)           │
│                                              │
│  微服务 → 微服务: NATS (事件驱动)            │
│                                              │
│  Odds Service → 前端: WebSocket (实时赔率)   │
│                                              │
│  Game Service → 前端: WebSocket (Crash游戏)  │
│                                              │
└──────────────────────────────────────────────┘
```

#### NATS事件定义

```go
// 事件类型
const (
    EventUserRegistered   = "user.registered"
    EventBetPlaced        = "bet.placed"
    EventBetSettled       = "bet.settled"
    EventDepositCompleted = "wallet.deposit.completed"
    EventWithdrawalRequested = "wallet.withdrawal.requested"
    EventGameStarted      = "game.crash.started"
    EventGameCrashed      = "game.crash.crashed"
)
```

---

## 3. 数据库设计

### 3.1 设计原则

| 原则 | 实现方式 |
|------|----------|
| 金额精度 | 整数存储(分)，避免浮点误差 |
| 事务安全 | 钱包操作使用FOR UPDATE悲观锁 + version乐观锁 |
| 性能优化 | 大表按月分区(bets, transactions) |
| 审计完整 | 所有金额变动记录BalanceBefore/BalanceAfter |
| 数据复用 | 基于lets-bet设计，扩展足球赛事表 |

### 3.2 核心表结构

#### 3.2.1 用户相关表

```sql
-- 用户表 (复用lets-bet)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number VARCHAR(20) UNIQUE NOT NULL,  -- 东南亚手机号
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    
    -- KYC字段
    full_name VARCHAR(100),
    date_of_birth DATE,
    national_id VARCHAR(50),          -- 身份证/护照
    is_verified BOOLEAN DEFAULT false,
    
    -- 负责任博彩
    self_excluded BOOLEAN DEFAULT false,
    self_excluded_until TIMESTAMP,
    daily_deposit_limit INTEGER,      -- 分为单位
    weekly_deposit_limit INTEGER,
    
    -- 元数据
    country_code VARCHAR(3) DEFAULT 'PH',  -- Philippines
    currency VARCHAR(3) DEFAULT 'PHP',
    status VARCHAR(20) DEFAULT 'ACTIVE',  -- ACTIVE/SUSPENDED/BANNED
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login_at TIMESTAMP
);

CREATE INDEX idx_users_phone ON users(phone_number);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status);
```

#### 3.2.2 钱包与交易表

```sql
-- 钱包表 (复用lets-bet，添加乐观锁)
CREATE TABLE wallets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id),
    balance INTEGER DEFAULT 0,           -- 分为单位
    bonus_balance INTEGER DEFAULT 0,     -- bonus余额
    version INTEGER DEFAULT 1,           -- 乐观锁版本号
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT balance_non_negative CHECK (balance >= 0)
);

CREATE INDEX idx_wallets_user ON wallets(user_id);

-- 交易记录表 (复用lets-bet，按月分区)
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    
    -- 金额信息
    amount INTEGER NOT NULL,             -- 正数=充值,负数=扣款
    balance_before INTEGER NOT NULL,     -- 操作前余额(审计)
    balance_after INTEGER NOT NULL,      -- 操作后余额(审计)
    
    -- 交易类型
    type VARCHAR(20) NOT NULL,           -- DEPOSIT/WITHDRAWAL/BET/PAYOUT/BONUS
    status VARCHAR(20) DEFAULT 'PENDING', -- PENDING/COMPLETED/FAILED/CANCELLED
    
    -- 外部引用
    reference_id UUID,                   -- 关联注单ID等
    reference_type VARCHAR(20),          -- BET/CRASH_GAME/DEPOSIT
    provider_name VARCHAR(50),           -- GrabPay/Maya等
    provider_txn_id VARCHAR(100),        -- 外部交易ID
    
    -- 元数据
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
) PARTITION BY RANGE (created_at);

-- 创建月度分区示例
CREATE TABLE transactions_2026_05 PARTITION OF transactions
    FOR VALUES FROM ('2026-05-01') TO ('2026-06-01');

CREATE INDEX idx_transactions_user ON transactions(user_id);
CREATE INDEX idx_transactions_type ON transactions(type);
CREATE INDEX idx_transactions_created ON transactions(created_at);
```

#### 3.2.3 足球赛事表 (新增)

```sql
-- 联赛表
CREATE TABLE leagues (
    id VARCHAR(50) PRIMARY KEY,         -- Sportradar ID
    name VARCHAR(100) NOT NULL,         -- "Premier League"
    country VARCHAR(50),                -- "England"
    sport VARCHAR(20) DEFAULT 'soccer',
    logo_url TEXT,
    is_active BOOLEAN DEFAULT true
);

-- 球队表
CREATE TABLE teams (
    id VARCHAR(50) PRIMARY KEY,         -- Sportradar ID
    name VARCHAR(100) NOT NULL,
    country VARCHAR(50),
    logo_url TEXT,
    league_ids TEXT[]                   -- 所属联赛
);

-- 赛事表 (核心)
CREATE TABLE events (
    id VARCHAR(50) PRIMARY KEY,         -- Sportradar event ID
    league_id VARCHAR(50) REFERENCES leagues(id),
    
    -- 比赛信息
    home_team_id VARCHAR(50) NOT NULL,
    away_team_id VARCHAR(50) NOT NULL,
    home_team_name VARCHAR(100),        -- 缓存名称
    away_team_name VARCHAR(100),
    
    -- 时间
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    status VARCHAR(20) DEFAULT 'scheduled', -- scheduled/live/ended/cancelled
    
    --比分
    home_score INTEGER DEFAULT 0,
    away_score INTEGER DEFAULT 0,
    
    -- 元数据
    season VARCHAR(20),
    round VARCHAR(20),
    venue VARCHAR(100),
    
    -- 数据来源
    source VARCHAR(20) DEFAULT 'sportradar',
    last_updated TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_events_league ON events(league_id);
CREATE INDEX idx_events_status ON events(status);
CREATE INDEX idx_events_start_time ON events(start_time);

-- 赔率表 (实时缓存)
CREATE TABLE odds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id VARCHAR(50) NOT NULL REFERENCES events(id),
    
    -- 赔率信息
    market VARCHAR(50) NOT NULL,        -- match_winner/over_under/handicap
    outcome VARCHAR(50) NOT NULL,       -- home/draw/away/over/under
    odds_value DECIMAL(10,4) NOT NULL,  -- 1.95, 2.10 等
    
    -- 赔率源
    source VARCHAR(20) DEFAULT 'sportradar',
    is_live BOOLEAN DEFAULT false,
    
    -- 更新追踪
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(event_id, market, outcome)
);

CREATE INDEX idx_odds_event ON odds(event_id);
CREATE INDEX idx_odds_market ON odds(market);
```

#### 3.2.4 体育投注表 (新增)

```sql
-- 体育投注主表 (按月分区)
CREATE TABLE sports_bets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    
    -- 投注信息
    bet_type VARCHAR(20) NOT NULL,      -- SINGLE/MULTI/SYSTEM
    total_stake INTEGER NOT NULL,       -- 分为单位
    total_odds DECIMAL(20,4) NOT NULL,  -- 累计赔率
    potential_payout INTEGER,           -- 潜在赔付
    
    -- 状态
    status VARCHAR(20) DEFAULT 'PENDING', -- PENDING/WON/LOST/CANCELLED/CASHED_OUT
    actual_payout INTEGER DEFAULT 0,
    
    -- 时间
    placed_at TIMESTAMP DEFAULT NOW(),
    settled_at TIMESTAMP,
    
    -- 元数据
    currency VARCHAR(3) DEFAULT 'PHP',
    ip_address VARCHAR(45),
    device_id VARCHAR(100),
    
    -- 审计
    balance_before INTEGER NOT NULL,
    balance_after INTEGER NOT NULL
) PARTITION BY RANGE (placed_at);

CREATE TABLE sports_bets_2026_05 PARTITION OF sports_bets
    FOR VALUES FROM ('2026-05-01') TO ('2026-06-01');

CREATE INDEX idx_sports_bets_user ON sports_bets(user_id);
CREATE INDEX idx_sports_bets_status ON sports_bets(status);

-- 投注选项表
CREATE TABLE bet_selections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bet_id UUID NOT NULL REFERENCES sports_bets(id),
    
    -- 选择信息
    event_id VARCHAR(50) NOT NULL,
    event_name VARCHAR(200),            -- "Arsenal vs Chelsea"
    market VARCHAR(50) NOT NULL,        -- match_winner
    outcome VARCHAR(50) NOT NULL,       -- home
    odds DECIMAL(10,4) NOT NULL,
    
    -- 状态
    status VARCHAR(20) DEFAULT 'PENDING', -- PENDING/WON/LOST/CANCELLED
    settled_at TIMESTAMP,
    
    UNIQUE(bet_id, event_id, market, outcome)
);

CREATE INDEX idx_selections_bet ON bet_selections(bet_id);
CREATE INDEX idx_selections_event ON bet_selections(event_id);
```

#### 3.2.5 Crash游戏表 (复用lets-bet)

```sql
-- Crash游戏表
CREATE TABLE crash_games (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    round_number BIGINT UNIQUE NOT NULL,
    
    -- Provably Fair
    server_seed VARCHAR(64) NOT NULL,           -- 游戏结束后公布
    server_seed_hash VARCHAR(64) NOT NULL,      -- 游戏前公布
    client_seed VARCHAR(64),
    
    -- 结果
    crash_point DECIMAL(20,4) NOT NULL,         -- 2.45x
    status VARCHAR(20) DEFAULT 'WAITING',       -- WAITING/RUNNING/CRASHED
    
    -- 时间
    started_at TIMESTAMP,
    crashed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_crash_games_round ON crash_games(round_number);
CREATE INDEX idx_crash_games_status ON crash_games(status);

-- Crash投注表 (按月分区)
CREATE TABLE crash_bets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    game_id UUID NOT NULL REFERENCES crash_games(id),
    user_id UUID NOT NULL REFERENCES users(id),
    
    -- 投注信息
    amount INTEGER NOT NULL,                -- 分为单位
    cashout_at DECIMAL(20,4),               -- 提现倍数 (NULL=未提现)
    payout INTEGER DEFAULT 0,               -- 实际赔付
    
    -- 状态
    status VARCHAR(20) DEFAULT 'ACTIVE',    -- ACTIVE/WON/LOST/CASHED_OUT
    cashed_out BOOLEAN DEFAULT false,
    
    -- 时间
    placed_at TIMESTAMP DEFAULT NOW(),
    cashout_time TIMESTAMP,
    
    -- 审计
    balance_before INTEGER NOT NULL,
    balance_after INTEGER NOT NULL
) PARTITION BY RANGE (placed_at);

CREATE TABLE crash_bets_2026_05 PARTITION OF crash_bets
    FOR VALUES FROM ('2026-05-01') TO ('2026-06-01');

CREATE INDEX idx_crash_bets_game ON crash_bets(game_id);
CREATE INDEX idx_crash_bets_user ON crash_bets(user_id);
CREATE INDEX idx_crash_bets_status ON crash_bets(status);
```

#### 3.2.6 支付相关表

```sql
-- 充值记录表 (GrabPay/Maya等)
CREATE TABLE deposits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    
    -- 金额
    amount INTEGER NOT NULL,                -- 分为单位
    currency VARCHAR(3) DEFAULT 'PHP',
    
    -- 支付渠道
    provider VARCHAR(20) NOT NULL,          -- grabpay/maya/gcash
    provider_txn_id VARCHAR(100),           -- 外部交易ID
    provider_reference VARCHAR(100),
    
    -- 状态
    status VARCHAR(20) DEFAULT 'PENDING',   -- PENDING/COMPLETED/FAILED/CANCELLED
    
    -- 时间
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    
    -- 元数据
    payment_method VARCHAR(50),             -- wallet/bank_transfer
    callback_data JSONB                     -- 回调原始数据
);

CREATE INDEX idx_deposits_user ON deposits(user_id);
CREATE INDEX idx_deposits_provider_txn ON deposits(provider_txn_id);

-- 提现记录表
CREATE TABLE withdrawals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    
    -- 金额
    amount INTEGER NOT NULL,
    fee INTEGER DEFAULT 0,                  -- 提现手续费
    currency VARCHAR(3) DEFAULT 'PHP',
    
    -- 支付渠道
    provider VARCHAR(20) NOT NULL,
    provider_txn_id VARCHAR(100),
    
    -- 状态 (需要审核流程)
    status VARCHAR(20) DEFAULT 'PENDING',   -- PENDING/APPROVED/PROCESSING/COMPLETED/REJECTED
    
    -- 审核
    reviewed_by UUID,                       -- Admin用户ID
    reviewed_at TIMESTAMP,
    review_notes TEXT,
    
    -- 时间
    created_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_withdrawals_user ON withdrawals(user_id);
CREATE INDEX idx_withdrawals_status ON withdrawals(status);
```

### 3.3 数据关系图

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   users     │────<│   wallets   │     │  deposits   │
│             │     │             │     │             │
│ id (PK)     │     │ user_id(FK) │     │ user_id(FK) │
│ phone       │     │ balance     │     │ amount      │
│ email       │     │ version     │     │ provider    │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                    │
       │                   │                    │
       │            ┌──────┴───────┐             │
       │            │transactions  │             │
       │            │              │             │
       │            │ user_id(FK)  │             │
       │            │ amount       │             │
       │            │ balance_*    │             │
       │            └──────────────┘             │
       │                                         │
       │     ┌───────────────────────────────────┤
       │     │                                   │
       │     ▼                                   ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│sports_bets  │     │ crash_bets  │     │ withdrawals │
│             │     │             │     │             │
│ user_id(FK) │     │ user_id(FK) │     │ user_id(FK) │
│ total_stake│     │ amount      │     │ amount      │
│ total_odds  │     │ cashout_at  │     │ status      │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │
       │                   │
       ▼                   ▼
┌─────────────┐     ┌─────────────┐
│bet_selection│     │ crash_games │
│             │     │             │
│ bet_id(FK)  │     │ round_number│
│ event_id(FK)│     │ crash_point │
│ odds        │     │ server_seed │
└─────────────┘     └─────────────┘
       │
       │
       ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   events    │────<│   leagues   │     │    odds     │
│             │     │             │     │             │
│ league_id   │     │ id (PK)     │     │ event_id(FK)│
│ home_team   │     │ name        │     │ market      │
│ away_team   │     │ country     │     │ odds_value  │
│ start_time  │     └─────────────┘     └─────────────┘
└─────────────┘
```

### 3.4 事务边界设计

#### 关键事务场景

```go
// 场景1: 投注扣款 (单事务)
func PlaceBet(userID, amount) error {
    tx.Begin()
    // 1. 锁定钱包行
    SELECT balance FROM wallets WHERE user_id = ? FOR UPDATE
    
    // 2. 检查余额
    if balance < amount { return ErrInsufficientFunds }
    
    // 3. 扣款
    UPDATE wallets SET balance = balance - ?, version = version + 1
    
    // 4. 创建注单
    INSERT INTO sports_bets (...)
    
    // 5. 记录交易
    INSERT INTO transactions (balance_before, balance_after, ...)
    
    tx.Commit()
}

// 场景2: 结算赔付 (单事务)
func SettleBet(betID, payout) error {
    tx.Begin()
    // 1. 获取注单状态
    SELECT status FROM sports_bets WHERE id = ?
    if status != 'PENDING' { return ErrAlreadySettled }
    
    // 2. 锁定钱包
    SELECT balance FROM wallets FOR UPDATE
    
    // 3. 加款
    UPDATE wallets SET balance = balance + ?
    
    // 4. 更新注单状态
    UPDATE sports_bets SET status = 'WON', actual_payout = ?
    
    // 5. 记录交易
    INSERT INTO transactions (type='PAYOUT', ...)
    
    tx.Commit()
}

// 场景3: Crash游戏结算 (批量)
func SettleCrashGame(gameID, crashPoint) error {
    tx.Begin()
    // 1. 获取所有未提现的投注
    SELECT * FROM crash_bets WHERE game_id = ? AND cashed_out = false
    
    // 2. 锁定钱包(批量)
    SELECT balance FROM wallets WHERE user_id IN (...) FOR UPDATE
    
    // 3. 批量结算
    for bet in bets {
        if bet.cashout_at < crashPoint {
            // 赢: 赔付
            payout = bet.amount * bet.cashout_at
            UPDATE wallets SET balance = balance + payout
        }
        // 输: 已扣款,无操作
        UPDATE crash_bets SET status = ...
    }
    
    // 4. 批量记录交易
    INSERT INTO transactions ...
    
    // 5. 更新游戏状态
    UPDATE crash_games SET status = 'CRASHED', server_seed = ?
    
    tx.Commit()
}
```

### 3.5 分区策略

| 表名 | 分区方式 | 分区周期 | 目的 |
|------|----------|----------|------|
| transactions | RANGE(created_at) | 按月 | 历史查询优化 |
| sports_bets | RANGE(placed_at) | 按月 | 注单查询优化 |
| crash_bets | RANGE(placed_at) | 按月 | 游戏记录优化 |

**分区维护**:
```sql
-- 每月初自动创建下月分区
CREATE TABLE transactions_2026_06 PARTITION OF transactions
    FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');
```

---

---

## 4. API接口设计
### 4.1 设计原则

| 序号 | 原则 | 说明 |
|------|------|------|
| [1] | RESTful风格 | 资源导向、统一动词语义 |
| [2] | 统一响应格式 | `{code, data, message}` 结构 |
| [3] | 版本管理 | `/api/v1` 前缀 |
| [4] | 错误码标准化 | 业务错误码 + HTTP状态码 |
| [5] | 认证机制 | JWT Token (Bearer) |
| [6] | WebSocket接口 | 实时数据推送 |
| [7] | 限流机制 | Redis计数器限流 |
| [8] | 缓存策略 | 短时数据Redis缓存 |

### 4.2 API分组

| 分组 | 路径 | 说明 | 认证要求 |
|------|------|------|----------|
| **认证** | `/api/v1/auth` | 注册、登录、JWT管理 | 部分 |
| **钱包** | `/api/v1/wallet` | 余额、充值、提现 | 必须 |
| **赛事** | `/api/v1/events` | 赛事列表、详情、赔率 | 公开 |
| **投注** | `/api/v1/bets` | 投注下单、注单查询 | 必须 |
| **游戏** | `/api/v1/games` | Crash游戏相关 | 必须 |
| **管理** | `/api/v1/admin` | Admin后台API | Admin角色 |

### 4.3 接口详细定义

#### 4.3.1 公共接口 (无认证)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/events` | 获取赛事列表 |
| GET | `/api/v1/events/:id` | 获取赛事详情 |
| GET | `/api/v1/events/live` | 获取Live赛事列表 |
| GET | `/api/v1/events/:league` | 获取联赛下的赛事 |
| GET | `/api/v1/leagues` | 获取联赛列表 |
| POST | `/api/v1/events/search` | 搜索赛事 |

**搜索赛事请求:**
```json
{
  "keyword": "Premier",
  "league_id": "sr:league:17",
  "start_time": "2026-05-01T00:00:00Z",
  "end_time": "2026-05-31T23:59:59Z",
  "status": "scheduled",
  "page": 1,
  "per_page": 20,
  "sort": "start_time",
  "direction": "desc"
}
```

**响应示例:**
```json
{
  "code": 200,
  "data": {
    "events": [
      {
        "id": "sr:event:12345",
        "league_id": "sr:league:17",
        "home_team_name": "Arsenal",
        "away_team_name": "Chelsea",
        "start_time": "2026-05-07T15:00:00Z",
        "status": "scheduled",
        "odds": {
          "home": 1.85,
          "draw": 3.40,
          "away": 4.20
        }
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 100,
      "pages": 5
    }
  }
}
```

#### 4.3.2 首页热门赛事

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/events/popular` | 获取热门赛事(首页轮播) |

**请求参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| limit | int | 返回数量(默认20) |
| popular | bool | 仅返回热门赛事 |
| league_ids | string[] | 联赛ID数组(可选) |
| live | bool | 是否Live赛事 |

### 4.4 体育投注接口

#### 4.4.1 投注下单

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/bets/place` | 创建注单 |

**请求Body:**
```json
{
  "user_id": "uuid",
  "event_id": "sr:event:12345",
  "total_stake": 1000,
  "total_odds": 2.5,
  "potential_payout": 2500,
  "currency": "PHP",
  "ip_address": "1.2.3.4",
  "device_id": "device-xxx"
}
```

**响应示例:**
```json
{
  "code": 201,
  "data": {
    "bet": {
      "id": "uuid",
      "user_id": "uuid",
      "bet_type": "SINGLE",
      "total_stake": 1000,
      "total_odds": 2.5,
      "potential_payout": 2500,
      "status": "pending",
      "balance_before": 5000,
      "balance_after": 4000,
      "placed_at": "2026-05-07T10:00:00Z",
      "selections": [
        {
          "event_id": "event_123",
          "market": "match_winner",
          "outcome": "home",
          "odds": 2.5
        }
      ]
    }
  }
}
```

**错误响应:**
```json
{
  "code": 400,
  "message": "Invalid stake amount"
}
```

#### 4.4.2 查询用户注单

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/bets` | 获取用户注单列表 |
| GET | `/api/v1/bets/:id` | 获取注单详情 |

**请求参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| limit | int | 返回数量(默认20) |
| offset | int | 偏移量(默认0) |
| sort | string | 排序字段(默认placed_at) |
| direction | string | 排序方向(默认desc) |

**响应示例:**
```json
{
  "code": 200,
  "data": {
    "bets": [
      {
        "id": "uuid",
        "user_id": "uuid",
        "bet_type": "single",
        "total_stake": 500,
        "total_odds": 1.5,
        "potential_payout": 750,
        "status": "pending",
        "balance_before": 1000,
        "balance_after": 500,
        "placed_at": "2026-05-07T10:00:00Z",
        "selections": []
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 100,
      "pages": 5
    }
  }
}
```

#### 4.4.3 结算接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/bets/:id/settle` | 手动结算注单 |

**请求参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| settle_id | string | 注单ID |
| result | string | 结算结果(won/lost/cancelled) |

**响应示例:**
```json
{
  "code": 200,
  "message": "Bet settled successfully"
}
```

#### 4.4.4 退款接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/bets/:id/refund` | 请求退款 |

**请求参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| amount | int | 退款金额(可选，默认全额) |
| reason | string | 退款原因 |

**响应示例:**
```json
{
  "code": 201,
  "message": "Refund processed"
}
```

#### 4.4.5 Cash Out接口(Live Betting)

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/bets/:id/cashout` | 提现(仅支持Live Betting) |

**请求参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| amount | int | 提现金额(可选，默认按当前赔率计算) |

**响应示例:**
```json
{
  "code": 201,
  "data": {
    "cashout_amount": 850,
    "original_stake": 1000,
    "cashout_odds": 1.85
  }
}
```

**错误响应:**
```json
{
  "code": 400,
  "message": "Insufficient funds"
}
```

### 4.5 Crash游戏接口

#### 4.5.1 游戏历史

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/games/crash/history` | 获取历史Crash游戏记录 |

**响应示例:**
```json
{
  "code": 200,
  "data": {
    "games": [
      {
        "id": "uuid",
        "round_number": 12345,
        "crash_point": 2.45,
        "status": "crashed",
        "started_at": "2026-05-07T10:00:00Z",
        "crashed_at": "2026-05-07T10:05:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 100,
      "pages": 5
    }
  }
}
```

#### 4.5.2 下注

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/games/crash/place-bet` | 投注 |

**请求参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| amount | int | 投注金额(100-10000分) |
| game_id | string | 当前游戏ID(uuid) |
| auto_cashout | float | 自动Cash Out倍数(可选) |

**响应示例:**
```json
{
  "code": 201,
  "data": {
    "game": {
      "id": "uuid",
      "round_number": 12345,
      "status": "waiting",
      "min_bet": 100,
      "max_bet": 10000,
      "started_at": null,
      "crashed_at": null
    },
    "bet": {
      "id": "uuid",
      "amount": 100,
      "status": "active",
      "placed_at": "2026-05-07T10:00:00Z"
    }
  }
}
```

#### 4.5.3 Cash Out

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/games/crash/:id/cashout` | Cash Out |

**请求参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| multiplier | float | Cash Out倍数(如1.5x) |

**响应示例:**
```json
{
  "code": 200,
  "data": {
    "bet_id": "uuid",
    "cashout_at": 1.5,
    "payout": 150
  }
}
```

#### 4.5.4 公平性验证

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/games/crash/:round/verify` | 验证Crash游戏公平性 |

**请求参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| server_seed | string | 游戏结束后公布的真实种子 |
| server_seed_hash | string | 游戏前公布的种子哈希 |
| round_number | int | 游戏轮次号 |
| client_seed | string | 客户端种子(可选) |

**响应示例:**
```json
{
  "code": 200,
  "data": {
    "valid": true,
    "game": {
      "id": "uuid",
      "round_number": 12345,
      "server_seed_hash": "abc123...",
      "crash_point": 2.45,
      "status": "crashed"
    },
    "verification": {
      "server_seed": "abc123...",
      "client_seed": "user123",
      "round_number": 12345,
      "calculated_crash_point": 2.45,
      "claimed_crash_point": 2.45,
      "valid": true
    }
  }
}
```

### 4.6 WebSocket接口

#### 4.6.1 连接地址

```
wss://api.kickbet.com/ws/games/crash  // Crash游戏
wss://api.kickbet.com/ws/odds/live     // Live赔率
```

#### 4.6.2 消息协议

**连接成功后心跳:**
```json
{ "type": "ping" }
```

**接收游戏状态:**
```json
{
  "type": "state",
  "data": {
    "round_number": 12345,
    "status": "waiting",
    "crash_point": null,
    "started_at": null,
    "crashed_at": null,
    "server_seed_hash": "abc123...",
    "current_multiplier": 1.00,
    "remaining_bets": 3,
    "next_game_in": 5,
    "tick_interval": 100
  }
}
```

**倍数更新:**
```json
{
  "type": "multiplier_update",
  "data": {
    "multiplier": 1.5,
    "timestamp": "2026-05-07T10:00:00Z"
  }
}
```

**Cash Out成功:**
```json
{
  "type": "cashout_success",
  "data": {
    "bet_id": "uuid",
    "payout": 250,
    "cashout_at": 1.5
  }
}
```

**游戏结束:**
```json
{
  "type": "crashed",
  "data": {
    "round_number": 12345,
    "crash_point": 2.45,
    "server_seed": "abc123",
    "server_seed_hash": "abc123...",
    "settled_bets": [
      {
        "bet_id": "uuid",
        "user_id": "uuid",
        "amount": 100,
        "status": "won",
        "payout": 250,
        "cashout_at": 1.5
      },
      {
        "bet_id": "uuid",
        "user_id": "uuid",
        "amount": 100,
        "status": "lost",
        "payout": 0,
        "cashout_at": null
      }
    ]
  }
}
```

**赔率更新:**
```json
{
  "type": "odds_update",
  "data": {
    "event_id": "event_123",
    "market": "match_winner",
    "outcomes": [
      { "outcome": "home", "odds": 2.1, "is_live": false },
      { "outcome": "draw", "odds": 3.5, "is_live": false },
      { "outcome": "away", "odds": 4.2, "is_live": false }
    ]
  }
}
```

### 4.7 Admin接口

#### 4.7.1 登录

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/admin/login` | Admin登录 |

**请求Body:**
```json
{
  "email": "admin@example.com",
  "password": "xxx"
}
```

**响应示例:**
```json
{
  "code": 200,
  "data": {
    "token": "jwt_token_here",
    "user": {
      "id": 1,
      "email": "admin@example.com",
      "role": "admin"
    }
  }
}
```

#### 4.7.2 其他Admin接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/admin/users` | 用户列表 |
| GET | `/api/v1/admin/users/:id` | 用户详情 |
| PUT | `/api/v1/admin/users/:id` | 更新用户状态 |
| GET | `/api/v1/admin/bets` | 注单管理 |
| GET | `/api/v1/admin/events` | 赛事管理 |
| POST | `/api/v1/admin/events` | 创建赛事 |
| PUT | `/api/v1/admin/events/:id` | 更新赛事 |
| POST | `/api/v1/admin/events/:id/settle` | 结算赛事 |
| GET | `/api/v1/admin/reports` | 报表统计 |

### 4.8 错误码定义

#### 4.8.1 HTTP状态码

| 代码 | 描述 | 说明 |
|------|------|------|
| 200 | OK | 成功 |
| 201 | Created | 资源创建成功 |
| 204 | No Content | 请求成功但返回空内容 |
| 400 | Bad Request | 请求参数错误 |
| 401 | Unauthorized | 未认证或认证无效 |
| 403 | Forbidden | 无权限访问 |
| 404 | Not Found | 资源不存在 |
| 409 | Conflict | 资源冲突 |
| 422 | Unprocessable Entity | 无法处理的请求格式 |
| 500 | Internal Server Error | 服务器内部错误 |
| 503 | Service Unavailable | 服务暂时不可用 |

#### 4.8.2 业务错误码

| 代码 | 名称 | 说明 |
|------|------|------|
| 10001 | Insufficient Funds | 余额不足 |
| 10002 | Invalid Bet | 投注无效 |
| 10003 | Event Not Available | 赛事不可用(已开始) |
| 10004 | Odds Changed | 赔率已变化 |
| 10005 | Bet Already Placed | 已投注 |
| 10006 | Game Not Active | 游戏未激活 |
| 10007 | Cashout Failed | Cash Out失败 |
| 10008 | Withdrawal Pending | 提现待审核 |
| 10009 | KYC Required | 需要KYC验证 |
| 10010 | Self Excluded | 用户自我排除 |
| 10011 | Limit Exceeded | 超出限额 |
| 10012 | Invalid Payment Method | 无效支付方式 |

---

## 5. 前端设计

### 5.1 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Next.js | 15.x | React框架，App Router |
| React | 19.x | UI库 |
| TypeScript | 5.x | 类型安全 |
| shadcn/ui | latest | UI组件库 |
| Tailwind CSS | 4.x | 样式系统 |
| Zustand | 5.x | 状态管理 |
| React Query | 5.x | 服务端状态缓存 |
| Socket.io-client | 4.x | WebSocket连接 |
| Framer Motion | 11.x | 动画库 |
| next-pwa | 5.x | PWA支持 |

### 5.2 页面结构

```
app/
├── layout.tsx                 # 根布局
├── page.tsx                  # 首页
├── (auth)/
│   ├── login/page.tsx        # 登录页
│   ├── register/page.tsx     # 注册页
│   └── forgot-password/page.tsx
├── (main)/
│   ├── sports/
│   │   ├── page.tsx          # 赛事列表
│   │   └── [eventId]/page.tsx # 赛事详情
│   ├── live/
│   │   └── page.tsx          # Live Betting
│   ├── crash/
│   │   └── page.tsx          # Crash游戏
│   └── history/
│       └── page.tsx          # 注单历史
├── wallet/
│   ├── page.tsx              # 钱包概览
│   ├── deposit/page.tsx      # 充值
│   └── withdraw/page.tsx     # 提现
├── account/
│   ├── page.tsx              # 个人中心
│   ├── kyc/page.tsx          # KYC验证
│   └── limits/page.tsx       # 限额设置
└── admin/                    # 管理后台(可选)
    ├── events/page.tsx       # 赛事管理
    ├── users/page.tsx        # 用户管理
    └── reports/page.tsx      # 报表
```

### 5.3 核心组件设计

#### 5.3.1 投注单组件 (BetSlip)

```tsx
// components/betting/BetSlip.tsx
interface BetSlipProps {
  selections: BetSelection[];
  onRemove: (id: string) => void;
  onPlaceBet: () => void;
}

// 设计要点:
// 1. 固定在屏幕底部（移动端）或右侧（桌面端）
// 2. 实时显示潜在收益
// 3. 赔率变化高亮提示
// 4. 3步完成投注: 选赛事 → 选结果 → 输入金额
```

**状态流程:**
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  选择赛事    │ -> │  选择结果    │ -> │  输入金额    │
│  (显示赔率)  │    │  (加入投注单) │    │  (确认投注)  │
└─────────────┘    └─────────────┘    └─────────────┘
```

#### 5.3.2 实时赔率组件 (LiveOdds)

```tsx
// components/betting/LiveOdds.tsx
interface LiveOddsProps {
  eventId: string;
  odds: OddsData;
  onOddsChange: (newOdds: OddsData) => void;
}

// 设计要点:
// 1. WebSocket订阅 odds_update 事件
// 2. 赔率变化时闪烁动画（上升绿色，下降红色）
// 3. 断线重连机制
// 4. 乐观更新 + 服务端确认
```

**WebSocket连接管理:**
```typescript
// lib/websocket.ts
class OddsWebSocket {
  private socket: Socket;
  private reconnectAttempts = 0;
  private maxReconnects = 5;

  connect(eventId: string) {
    this.socket = io('/odds', { query: { eventId } });
    this.socket.on('odds_update', this.handleUpdate);
    this.socket.on('disconnect', this.handleDisconnect);
  }

  private handleDisconnect = () => {
    if (this.reconnectAttempts < this.maxReconnects) {
      setTimeout(() => this.connect(), 1000 * ++this.reconnectAttempts);
    }
  };
}
```

#### 5.3.3 Crash游戏Canvas组件

```tsx
// components/games/CrashCanvas.tsx
interface CrashCanvasProps {
  multiplier: number;
  gameState: 'waiting' | 'playing' | 'crashed';
  onCashOut: () => void;
}

// 设计要点:
// 1. Canvas绘制飞机上升动画
// 2. 倍数实时显示（大字体、动态缩放）
// 3. 粒子特效（崩溃时爆炸）
// 4. 历史倍数条（顶部显示最近10局）
```

**Canvas动画核心:**
```typescript
// lib/crash-animation.ts
const drawPlane = (ctx: CanvasRenderingContext2D, multiplier: number) => {
  const y = canvasHeight - (multiplier * 50); // 倍数越高，飞机越高
  const scale = 1 + multiplier * 0.1; // 动态缩放
  
  ctx.save();
  ctx.translate(canvasWidth / 2, y);
  ctx.scale(scale, scale);
  // 绘制飞机SVG路径
  ctx.restore();
};

const drawTrail = (ctx: CanvasRenderingContext2D, points: Point[]) => {
  ctx.beginPath();
  ctx.strokeStyle = '#00ff88';
  ctx.lineWidth = 3;
  points.forEach((p, i) => {
    if (i === 0) ctx.moveTo(p.x, p.y);
    else ctx.lineTo(p.x, p.y);
  });
  ctx.stroke();
};
```

#### 5.3.4 PWA配置

```typescript
// next.config.js
const withPWA = require('next-pwa')({
  dest: 'public',
  register: true,
  skipWaiting: true,
  runtimeCaching: [
    {
      urlPattern: /^https:\/\/api\./,
      handler: 'NetworkFirst',
      options: { cacheName: 'api-cache', expiration: { maxEntries: 100 } }
    },
    {
      urlPattern: /\.(?:png|jpg|svg|ico)$/,
      handler: 'CacheFirst',
      options: { cacheName: 'image-cache', expiration: { maxEntries: 200 } }
    }
  ]
});
```

**manifest.json:**
```json
{
  "name": "KickBet",
  "short_name": "KickBet",
  "start_url": "/",
  "display": "standalone",
  "orientation": "portrait",
  "theme_color": "#1a1a2e",
  "background_color": "#1a1a2e",
  "icons": [
    { "src": "/icons/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icons/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

### 5.4 状态管理设计

#### 5.4.1 Store结构

```typescript
// stores/index.ts
import { create } from 'zustand';
import { persist, devtools } from 'zustand/middleware';

// 用户状态
interface UserStore {
  user: User | null;
  token: string | null;
  login: (user: User, token: string) => void;
  logout: () => void;
}

export const useUserStore = create<UserStore>()(
  persist(
    devtools((set) => ({
      user: null,
      token: null,
      login: (user, token) => set({ user, token }),
      logout: () => set({ user: null, token: null }),
    })),
    { name: 'user-storage' }
  )
);

// 投注单状态
interface BetSlipStore {
  selections: BetSelection[];
  addSelection: (selection: BetSelection) => void;
  removeSelection: (id: string) => void;
  clearAll: () => void;
}

export const useBetSlipStore = create<BetSlipStore>((set) => ({
  selections: [],
  addSelection: (s) => set((state) => ({
    selections: [...state.selections, s]
  })),
  removeSelection: (id) => set((state) => ({
    selections: state.selections.filter((s) => s.id !== id)
  })),
  clearAll: () => set({ selections: [] }),
}));

// Crash游戏状态
interface CrashGameStore {
  gameState: 'waiting' | 'betting' | 'playing' | 'crashed';
  currentMultiplier: number;
  myBet: Bet | null;
  history: CrashResult[];
  placeBet: (amount: number) => void;
  cashOut: () => void;
}
```

#### 5.4.2 React Query配置

```typescript
// lib/query-client.ts
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30 * 1000, // 30秒
      cacheTime: 5 * 60 * 1000, // 5分钟
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
});

// hooks/useEvents.ts
export const useEvents = (sport: string) => {
  return useQuery({
    queryKey: ['events', sport],
    queryFn: () => api.getEvents(sport),
    staleTime: 10 * 1000, // 赛事数据10秒过期
  });
};

// hooks/usePlaceBet.ts
export const usePlaceBet = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (bet: PlaceBetRequest) => api.placeBet(bet),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['wallet'] });
      queryClient.invalidateQueries({ queryKey: ['bets'] });
    },
  });
};
```

### 5.5 响应式设计

#### 5.5.1 断点定义

```css
/* tailwind.config.js */
module.exports = {
  theme: {
    screens: {
      'sm': '375px',   // 小手机
      'md': '768px',   // 平板竖屏
      'lg': '1024px',  // 平板横屏/小笔记本
      'xl': '1280px',  // 桌面
      '2xl': '1536px', // 大屏
    },
  },
};
```

#### 5.5.2 移动优先设计要点

| 元素 | 移动端 | 桌面端 |
|------|--------|--------|
| 投注单 | 底部固定抽屉 | 右侧固定面板 |
| 赛事列表 | 单列卡片 | 三列网格 |
| 导航 | 底部Tab栏 | 顶部导航栏 |
| Crash游戏 | 全屏Canvas | 居中+侧边聊天 |
| 赔率显示 | 紧凑横排 | 宽松表格 |

### 5.6 性能优化

#### 5.6.1 代码分割

```typescript
// app/crash/page.tsx
import dynamic from 'next/dynamic';

// Crash游戏Canvas延迟加载
const CrashCanvas = dynamic(
  () => import('@/components/games/CrashCanvas'),
  { 
    ssr: false, // Canvas不支持SSR
    loading: () => <CrashSkeleton />
  }
);
```

#### 5.6.2 图片优化

```tsx
// 使用Next.js Image组件
import Image from 'next/image';

<Image
  src="/images/team-logo.png"
  alt={teamName}
  width={40}
  height={40}
  loading="lazy"
  placeholder="blur"
  blurDataURL="data:image/png;base64,..."
/>
```

#### 5.6.3 关键指标目标

| 指标 | 目标值 |
|------|--------|
| LCP (Largest Contentful Paint) | < 2.5s |
| FID (First Input Delay) | < 100ms |
| CLS (Cumulative Layout Shift) | < 0.1 |
| TTI (Time to Interactive) | < 3.5s |
| Bundle Size (gzip) | < 200KB |

### 5.7 国际化(i18n)

```typescript
// i18n/config.ts
export const i18nConfig = {
  defaultLocale: 'en',
  locales: ['en', 'zh-CN', 'vi', 'th', 'id', 'ms'],
};

// 支持语言:
// en     - English (默认)
// zh-CN  - 简体中文
// vi     - Tiếng Việt (越南语)
// th     - ไทย (泰语)
// id     - Bahasa Indonesia
// ms     - Bahasa Melayu (马来语)
```

```json
// i18n/locales/zh-CN/common.json
{
  "bet": "投注",
  "odds": "赔率",
  "placeBet": "下注",
  "cashOut": "提现",
  "multiplier": "倍数",
  "balance": "余额"
}
```

### 5.8 无障碍设计(A11y)

```tsx
// 确保所有交互元素可键盘访问
<Button
  onClick={handleBet}
  aria-label={`投注 ${teamName}，赔率 ${odds}`}
  aria-pressed={isSelected}
>
  {odds}
</Button>

// 赔率变化时有语音提示
<LiveOdds
  onOddsChange={(newOdds) => {
    announce(`赔率变化: ${oldOdds} → ${newOdds}`);
  }}
/>
```

---

## 6. 关键业务流程

### 6.1 用户注册与登录流程

```
┌─────────────────────────────────────────────────────────────┐
│                     用户注册流程                              │
└─────────────────────────────────────────────────────────────┘

用户输入邮箱/手机 → 发送验证码 → 验证成功 → 设置密码
                                    ↓
                              创建用户记录
                                    ↓
                              发送欢迎邮件
                                    ↓
                              进入KYC流程(可选)
```

**关键验证点:**
- 邮箱/手机号格式验证
- 验证码有效期5分钟
- 密码强度要求(8位+数字+字母)
- 检查是否已注册

**API调用序列:**
```typescript
// 1. 发送验证码
POST /api/v1/auth/send-code { phone: "+63xxx", type: "register" }

// 2. 验证码校验
POST /api/v1/auth/verify-code { phone: "+63xxx", code: "123456" }

// 3. 完成注册
POST /api/v1/auth/register { 
  phone: "+63xxx", 
  password: "xxx", 
  referrerCode: "ABC123" // 可选邀请码
}

// 4. 自动登录，返回JWT
Response: { token: "jwt...", user: { id, phone, status } }
```

### 6.2 投注流程（赛前投注）

```
┌─────────────────────────────────────────────────────────────┐
│                     赛前投注流程                              │
└─────────────────────────────────────────────────────────────┘

Step 1: 用户选择赛事
        ↓
        GET /api/v1/events/{eventId}
        返回: 赛事信息 + 可投注选项 + 当前赔率
        
Step 2: 用户选择投注选项（加入投注单）
        ↓
        WebSocket订阅: odds_update:{eventId}
        实时显示赔率变化
        
Step 3: 用户输入金额，确认投注
        ↓
        POST /api/v1/bets/place
        {
          eventId: "xxx",
          selections: [{ type: "home", odds: 1.85 }],
          amount: 1000, // 单位:分
          oddsAcceptMode: "any" // 或 "exact"
        }
        
Step 4: 服务端验证处理
        ↓
        ├── 检查用户状态(是否自我排除)
        ├── 检查赛事状态(是否已开始)
        ├── 检查赔率是否变化
        ├── 检查余额是否充足
        ├── 检查投注限额
        ├── 执行钱包扣款(FOR UPDATE锁)
        ├── 创建投注记录
        └── 返回投注确认
        
Step 5: 投注确认展示
        ↓
        显示: 投注ID、投注金额、潜在收益、赔率
        WebSocket推送: bet_placed:{userId}
```

**赔率变化处理策略:**

| 模式 | 说明 |
|------|------|
| `exact` | 赔率变化则拒绝投注，提示用户重新确认 |
| `any` | 赔率变化时自动接受新赔率（上限可设） |
| `better` | 仅接受更高赔率，低赔率则拒绝 |

**错误处理:**
```json
// 赔率变化
{ "code": 10004, "message": "Odds changed", "data": { 
  "oldOdds": 1.85, "newOdds": 1.80 
}}

// 余额不足
{ "code": 10001, "message": "Insufficient funds", "data": { 
  "balance": 500, "required": 1000 
}}

// 赛事已开始
{ "code": 10003, "message": "Event not available" }
```

### 6.3 Live Betting流程

```
┌─────────────────────────────────────────────────────────────┐
│                     Live Betting流程                          │
└─────────────────────────────────────────────────────────────┘

用户进入Live页面 → WebSocket连接 → 接收实时数据
                              ↓
                    ┌─────────────────────┐
                    │ 实时推送内容          │
                    │ - 比赛时间/比分       │
                    │ - 赔率变化           │
                    │ - 可投注选项         │
                    │ - 比赛事件(进球等)   │
                    └─────────────────────┘
                              ↓
用户选择投注 → 输入金额 → 确认 → POST /api/v1/bets/place
                              ↓
                    服务端验证(时间窗口极短)
                              ↓
                    执行投注(5秒内完成)
                              ↓
                    WebSocket推送确认
```

**Live Betting特殊处理:**

| 项目 | 赛前投注 | Live Betting |
|------|----------|--------------|
| 赔率更新频率 | 1分钟 | 实时(毫秒级) |
| 投注时间窗口 | 无限制 | 事件触发窗口 |
| 赔率锁定 | 确认时锁定 | 接受后即时锁定 |
| 结算时间 | 比赛结束 | 比赛结束 |
| 风控 | 标准检查 | 增加延迟检测 |

**WebSocket事件定义:**
```typescript
// 赔率更新
socket.on('odds_update', {
  eventId: "xxx",
  markets: [
    { type: "home", odds: 1.95, trend: "up" },
    { type: "draw", odds: 3.40, trend: "down" },
    { type: "away", odds: 4.10, trend: "stable" }
  ]
});

// 比赛事件(进球/红牌等)
socket.on('match_event', {
  eventId: "xxx",
  type: "goal",
  team: "home",
  score: "2-1",
  time: "75:30"
});

// 市场关闭
socket.on('market_closed', {
  eventId: "xxx",
  market: "match_result",
  reason: "goal"
});
```

### 6.4 Crash游戏流程

```
┌─────────────────────────────────────────────────────────────┐
│                     Crash游戏流程                             │
└─────────────────────────────────────────────────────────────┘

Phase 1: 等待阶段(5秒)
         ├── 显示上一局结果
         ├── 用户输入下注金额
         ├── 用户可选: 自动Cash Out倍数
         └── 倒计时显示

Phase 2: 投注阶段(3秒锁定)
         ├── 关闭投注入口
         ├── 生成游戏种子(hash)
         ├── 计算崩溃点(不透露)
         └── 准备开始

Phase 3: 游戏进行
         ├── WebSocket推送: crash_tick (每100ms)
         │   { multiplier: 1.23, time: 500 }
         ├── Canvas动画: 飞机上升
         ├── 倍数显示: 1.00 → 崩溃点
         └── 用户点击Cash Out → 结算

Phase 4: 崩溃
         ├── 推送: crash_result
         │   { crashPoint: 2.47, seed: "xxx", nonce: 123 }
         ├── 未Cash Out用户: 输掉本金
         ├── 已Cash Out用户: 本金 × 倍数
         └── 显示历史记录

Phase 5: 验证(可选)
         ├── 用户可验证公平性
         ├── 输入种子 + nonce
         └── 本地计算崩溃点对比
```

**Provably Fair算法:**
```go
// 参考 lets-bet/internal/core/usecase/provably_fair.go

func calculateCrashPoint(seed string, nonce int64) float64 {
    // 组合种子
    hash := hmac_sha256(seed, strconv.Itoa(nonce))
    
    // 取前8字节转整数
    h := int64(binary.BigEndian.Uint64(hash[:8]))
    
    // 归一化到0-1
    r := float64(h % 10000) / 10000
    
    // 计算崩溃点 (Bustabit公式)
    // E = 1/(1-r) 但有下限
    if r == 0 {
        return 1.0 // 瞬崩
    }
    
    crashPoint := 1 / (1 - r)
    
    // 限制最大值(通常100x)
    if crashPoint > 100 {
        crashPoint = 100
    }
    
    return crashPoint
}
```

**下注请求:**
```json
POST /api/v1/games/crash/bet
{
  "amount": 1000,
  "autoCashOut": 2.5  // 可选: 自动在2.5x提现
}
```

**Cash Out请求:**
```json
POST /api/v1/games/crash/cashout
{
  "betId": "xxx",
  "multiplier": 1.85  // 当前倍数(服务端验证)
}
```

**历史记录显示:**
```
┌─────────────────────────────────────────────────────────────┐
│ 最近20局:  1.23x  5.67x  1.00x  2.34x  10.5x  1.89x  ...   │
│            ↑红   ↑绿    ↑红   ↑绿    ↑绿   ↑绿              │
└─────────────────────────────────────────────────────────────┘
红色 = 瞬崩(≤1.5x)  绿色 = 正常(>1.5x)
```

### 6.5 支付流程（充值）

```
┌─────────────────────────────────────────────────────────────┐
│                     充值流程                                  │
└─────────────────────────────────────────────────────────────┘

用户选择充值 → 选择支付方式 → 输入金额 → 确认
                              ↓
                    POST /api/v1/wallet/deposit
                    { amount: 50000, method: "gcash" }
                              ↓
                    创建充值订单(pending状态)
                              ↓
                    返回支付链接/二维码
                              ↓
                    用户完成支付(第三方)
                              ↓
                    第三方回调 → POST /api/v1/wallet/deposit/callback
                              ↓
                    验证回调签名
                              ↓
                    更新订单状态 → 更新钱包余额
                              ↓
                    WebSocket推送: deposit_success
```

**支持的支付方式(东南亚):**

| 国家 | 支付方式 | 最小金额 | 最大金额 | 处理时间 |
|------|----------|----------|----------|----------|
| 菲律宾 | GCash | ₱100 | ₱50,000 | 即时 |
| 菲律宾 | PayMaya | ₱100 | ₱30,000 | 即时 |
| 泰国 | TrueMoney | ฿100 | ฿30,000 | 即时 |
| 越南 | MoMo | ₫50,000 | ₫5,000,000 | 即时 |
| 印尼 | OVO | Rp50,000 | Rp10,000,000 | 即时 |
| 马来西亚 | Touch'n Go | RM10 | RM5,000 | 即时 |

**充值记录表:**
```sql
-- deposits表结构
CREATE TABLE deposits (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    amount BIGINT NOT NULL,         -- 单位:分
    method VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,    -- pending/success/failed
    external_ref VARCHAR(100),      -- 第三方订单号
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

### 6.6 支付流程（提现）

```
┌─────────────────────────────────────────────────────────────┐
│                     提现流程                                  │
└─────────────────────────────────────────────────────────────┘

用户申请提现 → 检查KYC状态 → 输入金额 → 选择收款方式
                              ↓
                    POST /api/v1/wallet/withdraw
                    { amount: 10000, method: "gcash", account: "xxx" }
                              ↓
                    系统检查:
                    ├── KYC是否通过
                    ├── 余额是否充足
                    ├── 是否有未结算投注
                    ├── 是否达到最小提现额
                    ├── 是否超出每日限额
                    └── 是否满足流水要求(可选)
                              ↓
                    创建提现订单 → 锁定余额
                              ↓
                    状态: pending_review
                              ↓
                    ┌─────────────────────┐
                    │ 自动审核(小额)       │
                    │ - < $50: 自动通过    │
                    │ - $50-200: 人工审核 │
                    │ - > $200: 强审核    │
                    └─────────────────────┘
                              ↓
                    审核通过 → 发起第三方转账
                              ↓
                    转账完成 → 更新订单状态
                              ↓
                    WebSocket推送: withdraw_success
```

**提现限制:**

| 限制项 | 规则 |
|--------|------|
| 最小提现 | $10 (1000分) |
| 最大单次 | $500 |
| 每日限额 | $2,000 |
| 处理时间 | 小额即时, 大额24h |
| 流水要求 | 无(或可选设置) |

**风控检查:**
```go
// 提现前检查
func (s *WithdrawalService) ValidateWithdrawal(req WithdrawalRequest) error {
    // 1. KYC检查
    if !user.KYCVerified {
        return ErrKYCRequired
    }
    
    // 2. 余额检查
    if user.Balance < req.Amount {
        return ErrInsufficientFunds
    }
    
    // 3. 未结算投注检查
    pendingBets := s.GetPendingBets(user.ID)
    lockedAmount := sum(pendingBets)
    availableBalance := user.Balance - lockedAmount
    if availableBalance < req.Amount {
        return ErrLockedFunds
    }
    
    // 4. 每日限额检查
    todayWithdrawals := s.GetTodayWithdrawals(user.ID)
    if todayWithdrawals + req.Amount > user.DailyLimit {
        return ErrLimitExceeded
    }
    
    return nil
}
```

### 6.7 比赛结算流程

```
┌─────────────────────────────────────────────────────────────┐
│                     比赛结算流程                              │
└─────────────────────────────────────────────────────────────┘

比赛结束 → 外部数据源推送结果
              ↓
        POST /api/v1/admin/events/settle (内部API)
        { eventId: "xxx", result: { home: 2, away: 1 } }
              ↓
        更新赛事状态: settled
              ↓
        查询所有相关投注
              ↓
        ┌─────────────────────────────────────┐
        │ 计算投注结果                         │
        │ - 主胜投注: 赢                      │
        │ - 平局投注: 输                      │
        │ - 客胜投注: 输                      │
        │ - 正确比分: 按具体比分判定          │
        └─────────────────────────────────────┘
              ↓
        批量处理结算
              ↓
        ├── 赢: 本金 + 收益 → 钱包余额
        ├── 输: 本金 → 平台收入
        ├── 退: 取消/无效 → 本金退回
        └── 半退: 特殊情况(如比赛中断)
              ↓
        更新投注状态: settled
              ↓
        WebSocket推送: bet_result:{userId}
              ↓
        用户收到通知 + 余额更新
```

**结算计算示例:**
```go
// 投注结算
func (s *SettlementService) CalculatePayout(bet Bet, result MatchResult) int64 {
    // 判断投注是否赢
    if s.isWinning(bet, result) {
        // 收益 = 本金 × 赔率
        payout := bet.Amount * bet.Odds
        // 扣除本金部分,只加收益
        return int64(payout)
    }
    
    // 输: 0
    return 0
}

// 判断胜负
func (s *SettlementService) isWinning(bet Bet, result MatchResult) bool {
    switch bet.SelectionType {
    case "home":
        return result.Home > result.Away
    case "draw":
        return result.Home == result.Away
    case "away":
        return result.Away > result.Home
    case "correct_score":
        expected := bet.Score // "2-1"
        actual := fmt.Sprintf("%d-%d", result.Home, result.Away)
        return expected == actual
    }
    return false
}
```

**批量结算事务:**
```sql
-- 单个赛事结算事务
BEGIN;

-- 1. 更新赛事状态
UPDATE events SET status = 'settled', result = '{home:2,away:1}'
WHERE id = 'xxx';

-- 2. 批量更新投注
UPDATE sports_bets SET status = 'settled', payout = amount * odds
WHERE event_id = 'xxx' AND selection = 'home'; -- 赢的

UPDATE sports_bets SET status = 'settled', payout = 0
WHERE event_id = 'xxx' AND selection != 'home'; -- 输的

-- 3. 更新钱包余额
UPDATE wallets SET balance = balance + payout
FROM sports_bets WHERE user_id = sports_bets.user_id 
AND sports_bets.event_id = 'xxx' AND sports_bets.payout > 0;

-- 4. 记录交易
INSERT INTO transactions (user_id, type, amount, ref_type, ref_id)
SELECT user_id, 'payout', payout, 'bet', id
FROM sports_bets WHERE event_id = 'xxx' AND payout > 0;

COMMIT;
```

### 6.8 KYC验证流程

```
┌─────────────────────────────────────────────────────────────┐
│                     KYC验证流程                               │
└─────────────────────────────────────────────────────────────┘

触发条件:
- 提现时强制要求
- 累计充值达到阈值
- 管理员手动要求

用户提交资料:
├── 身份证/护照照片
├── 人脸照片(实时拍摄)
└── 地址证明(可选)

第三方验证(Smile ID / Jumio):
├── POST /api/v1/kyc/submit
├── 服务端转发至第三方
├── 第三方验证:
│   ├── 身份证真实性
│   ├── 人脸匹配
│   ├── 年龄验证(≥18)
│   └── 黑名单检查
├── 返回验证结果
└── 更新用户状态

状态流转:
pending → verifying → verified / rejected

提现前强制检查:
if !user.KYCVerified {
    return { code: 10009, message: "KYC Required" }
}
```

**KYC记录表:**
```sql
CREATE TABLE kyc_verifications (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    type VARCHAR(20),              -- id/passport
    status VARCHAR(20),            -- pending/verifying/verified/rejected
    id_number VARCHAR(100),
    id_photo_url TEXT,
    face_photo_url TEXT,
    verification_provider VARCHAR(50), -- smile_id/jumio
    external_ref VARCHAR(100),
    result JSONB,                  -- 第三方返回详情
    created_at TIMESTAMP,
    verified_at TIMESTAMP,
    expires_at TIMESTAMP           -- KYC有效期(可选)
);
```

---

## 7. 安全设计

### 7.1 认证与授权

#### 7.1.1 JWT认证

```typescript
// JWT配置
interface JWTConfig {
  secret: string;           // 签名密钥(256位)
  expiresIn: string;        // 访问令牌有效期: "15m"
  refreshExpiresIn: string; // 刷新令牌有效期: "7d"
  issuer: string;           // 发行者: "kickbet.com"
}

// Token结构
interface AccessToken {
  userId: string;
  role: "user" | "admin";
  iat: number;             // 发行时间
  exp: number;             // 过期时间
  jti: string;             // JWT ID(用于黑名单)
}

// 刷新令牌流程
用户登录 → 返回 accessToken + refreshToken
accessToken过期 → POST /api/v1/auth/refresh { refreshToken }
→ 返回新accessToken + 新refreshToken
refreshToken过期 → 强制重新登录
```

**安全措施:**
- 访问令牌有效期短(15分钟)
- 刷新令牌单次使用(用后失效)
- 令牌黑名单(用户登出/密码修改)
- IP绑定可选(高风险用户)

#### 7.1.2 权限控制(RBAC)

```yaml
# 角色定义
roles:
  user:
    permissions:
      - bet:place
      - bet:view
      - wallet:deposit
      - wallet:withdraw
      - wallet:view
      - crash:play
      - crash:view
      
  vip:
    inherits: user
    permissions:
      - bet:higher_limit
      
  admin:
    permissions:
      - event:manage
      - user:manage
      - report:view
      - withdrawal:approve
      - kyc:review
      
  super_admin:
    inherits: admin
    permissions:
      - system:config
      - admin:create
```

**权限检查中间件:**
```go
// Go中间件示例
func AuthMiddleware(requiredPermission string) gin.HandlerFunc {
    return func(c *gin.Context) {
        token := c.GetHeader("Authorization")
        claims := ParseJWT(token)
        
        if !HasPermission(claims.Role, requiredPermission) {
            c.JSON(403, gin.H{"code": 40300, "message": "Forbidden"})
            c.Abort()
            return
        }
        
        c.Set("userId", claims.UserId)
        c.Next()
    }
}
```

### 7.2 数据安全

#### 7.2.1 传输加密

```
所有API通信强制HTTPS (TLS 1.3)

敏感数据传输:
├── 密码: 不传输，仅传输hash
├── 支付信息: 第三方处理，不存储
├── KYC照片: 加密存储
└── API密钥: 请求签名验证
```

**支付回调签名验证:**
```go
// GCash回调验证示例
func VerifyCallback(callback CallbackData) bool {
    // 1. 按字段名排序
    sortedFields := sortKeys(callback)
    
    // 2. 拼接成字符串
    dataString := concatenate(sortedFields)
    
    // 3. HMAC-SHA256签名
    signature := hmac_sha256(dataString, MERCHANT_SECRET)
    
    // 4. 对比签名
    return signature == callback.Signature
}
```

#### 7.2.2 存储加密

```sql
-- 敏感字段加密存储
CREATE TABLE users (
    ...
    phone_encrypted TEXT,      -- 手机号加密
    email_encrypted TEXT,      -- 邮箱加密
    password_hash TEXT,        -- 密码hash(不存原文)
    kyc_data_encrypted TEXT,   -- KYC数据加密
    ...
);

-- 加密方式
AES-256-GCM (密钥由KMS管理)
```

**密钥管理:**
```
┌─────────────────────────────────────────────────────────────┐
│                     密钥管理体系                              │
└─────────────────────────────────────────────────────────────┘

应用层密钥 → AWS KMS / HashiCorp Vault
              ↓
        主密钥(Master Key) → 加密数据密钥
              ↓
        数据密钥(Data Key) → 加密具体数据
              ↓
        密钥轮换(每年)
```

#### 7.2.3 密码安全

```go
// 密码hash算法: bcrypt
func HashPassword(password string) string {
    // cost=12 (2^12轮迭代)
    hash, _ := bcrypt.GenerateFromPassword([]byte(password), 12)
    return string(hash)
}

func VerifyPassword(password, hash string) bool {
    err := bcrypt.CompareHashAndPassword([]byte(hash), []byte(password))
    return err == nil
}

// 密码强度要求:
// - 最少8字符
// - 必含数字
// - 必含字母(大小写混合)
// - 禁止常见弱密码(123456, password等)
```

### 7.3 输入验证

#### 7.3.1 前端验证

```typescript
// 投注金额验证
const validateBetAmount = (amount: number): ValidationResult => {
  if (amount < MIN_BET) return { valid: false, error: "最小投注10" };
  if (amount > MAX_BET) return { valid: false, error: "最大投注50000" };
  if (!Number.isInteger(amount)) return { valid: false, error: "金额必须整数" };
  return { valid: true };
};

// 手机号验证(菲律宾)
const validatePhone = (phone: string): boolean => {
  const PH_PATTERN = /^\+63[9]\d{9}$/; // +639开头,共13位
  return PH_PATTERN.test(phone);
};
```

#### 7.3.2 后端验证

```go
// 结构体验证(使用validator库)
type PlaceBetRequest struct {
    EventID        string  `validate:"required,uuid"`
    Amount         int64   `validate:"required,min=1000,max=5000000"`
    OddsAcceptMode string  `validate:"required,oneof=exact any better"`
}

func ValidateRequest(req PlaceBetRequest) error {
    return validator.New().Struct(req)
}

// 业务验证
func (s *BetService) ValidateBet(req PlaceBetRequest, user User) error {
    // 1. 赛事状态
    if event.Status != "open" {
        return ErrEventNotAvailable
    }
    
    // 2. 用户限额
    if req.Amount > user.BetLimit {
        return ErrLimitExceeded
    }
    
    // 3. 自我排除检查
    if user.SelfExcluded {
        return ErrSelfExcluded
    }
    
    return nil
}
```

### 7.4 防攻击措施

#### 7.4.1 SQL注入防护

```go
// 使用ORM/参数化查询，禁止拼接SQL

// ❌ 错误示例
query := fmt.Sprintf("SELECT * FROM users WHERE id = '%s'", userId)

// ✅ 正确示例(GORM)
db.Where("id = ?", userId).First(&user)

// ✅ 正确示例(原生SQL)
db.Raw("SELECT * FROM users WHERE id = ?", userId).Scan(&user)
```

#### 7.4.2 XSS防护

```typescript
// 前端: 所有用户输入转义
import { sanitize } from 'dompurify';

const safeContent = sanitize(userInput);

// 后端: Content-Type设置
c.Header("Content-Type", "application/json")
c.Header("X-Content-Type-Options", "nosniff")
```

#### 7.4.3 CSRF防护

```typescript
// 双重Cookie验证
// 1. Cookie中设置csrf_token
// 2. 请求Header携带同一token
// 3. 服务端比对

// Next.js配置
export const config = {
  csrf: {
    cookieKey: 'csrf_token',
    headerKey: 'X-CSRF-Token',
  }
};
```

#### 7.4.4 速率限制

```yaml
# API限速配置
rate_limits:
  auth:
    login: "5/minute"      # 登录限速
    register: "3/hour"     # 注册限速
    
  bets:
    place: "30/minute"     # 投注限速
    
  games:
    crash_bet: "10/minute" # Crash下注限速
    
  wallet:
    withdraw: "5/hour"     # 提现限速
    
  general:
    api: "100/minute"      # 通用API限速
```

**限速中间件:**
```go
// Redis实现
func RateLimiter(limit int, window time.Duration) gin.HandlerFunc {
    return func(c *gin.Context) {
        key := fmt.Sprintf("rate:%s:%s", c.FullPath(), c.GetString("userId"))
        
        count, _ := rdb.Incr(ctx, key).Result()
        if count == 1 {
            rdb.Expire(ctx, key, window)
        }
        
        if count > limit {
            c.JSON(429, gin.H{"code": 42900, "message": "Rate limit exceeded"})
            c.Abort()
            return
        }
        
        c.Next()
    }
}
```

### 7.5 合规与风控

#### 7.5.1 年龄验证

```
KYC验证时强制检查年龄≥18岁

未通过KYC用户:
├── 可充值
├── 可投注(小额)
├── 禁止提现
└── 累计充值$100后强制KYC
```

#### 7.5.2 负责任博彩

```go
// 自我排除功能
type SelfExclusion struct {
    UserID    UUID
    Type      string  // temporary / permanent
    Duration  int     // 天数(临时排除)
    Reason    string
    CreatedAt time.Time
    ExpiresAt time.Time
}

// 投注限额设置
type BetLimits struct {
    DailyLimit   int64  // 每日限额
    WeeklyLimit  int64  // 每周限额
    MonthlyLimit int64  // 每月限额
    SingleBetMax int64  // 单注上限
}

// 检查限额
func (s *BetService) CheckLimits(userId UUID, amount int64) error {
    limits := s.GetUserLimits(userId)
    todayTotal := s.GetTodayTotal(userId)
    
    if todayTotal + amount > limits.DailyLimit {
        return ErrDailyLimitExceeded
    }
    
    return nil
}
```

**用户可选功能:**
- 设置投注限额
- 设置存款限额
- 设置亏损限额
- 设置会话时间提醒
- 自我排除(临时/永久)
- 账户冻结

#### 7.5.3 AML(反洗钱)

```
触发检查条件:
├── 单笔充值>$1000
├── 24小时累计充值>$3000
├── 7天累计充值>$10000
├── 大额提现>$500
├── 异常投注模式
└── 多账户关联检测

处理流程:
触发 → 标记账户 → 人工审核 → 冻结/放行
```

**可疑行为检测:**
```go
// 异常模式检测
func (s *AMLService) DetectSuspicious(userId UUID) []SuspiciousFlag {
    flags := []SuspiciousFlag{}
    
    // 1. 高频小额充值后大额提现
    deposits := s.GetRecentDeposits(userId, 7)
    if len(deposits) > 20 && s.HasLargeWithdrawal(userId) {
        flags = append(flags, FlagHighFrequencyDeposit)
    }
    
    // 2. 投注模式异常(只投高赔率)
    bets := s.GetRecentBets(userId, 30)
    avgOdds := calculateAvgOdds(bets)
    if avgOdds > 5.0 {
        flags = append(flags, FlagUnusualBetting)
    }
    
    // 3. IP/设备关联多账户
    relatedUsers := s.FindRelatedAccounts(userId)
    if len(relatedUsers) > 3 {
        flags = append(flags, FlagMultiAccount)
    }
    
    return flags
}
```

### 7.6 审计与监控

#### 7.6.1 操作日志

```sql
-- 审计日志表
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY,
    user_id UUID,
    action VARCHAR(100),        -- login/logout/bet/deposit/withdraw...
    resource_type VARCHAR(50),
    resource_id UUID,
    details JSONB,              -- 操作详情
    ip_address VARCHAR(50),
    device_info TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 分区(按月)
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
```

**关键操作必须记录:**
- 登录/登出
- 密码修改
- 投注操作
- 钱包操作
- KYC提交
- 限额修改
- 管理员操作

#### 7.6.2 异常告警

```yaml
# 告警规则
alerts:
  security:
    - 多次登录失败(同一IP > 5次/分钟)
    - 异地登录(距离>500km)
    - Token异常使用
    
  business:
    - 大额投注(>$1000)
    - 大额提现(>$500)
    - 高频操作(投注>100次/小时)
    
  system:
    - API错误率>5%
    - WebSocket断连率>10%
    - 数据库响应>1s
```

**告警通知:**
- Email (管理员)
- Slack/Telegram (运维团队)
- SMS (紧急情况)

---

## 8. 运维设计

### 8.1 部署架构

#### 8.1.1 生产环境拓扑

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         KickBet 生产环境架构                              │
└─────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────┐
                              │   Cloudflare │  CDN + WAF + DDoS防护
                              │   (边缘节点)  │
                              └──────┬──────┘
                                     │
                              ┌──────▼──────┐
                              │  API Gateway │  Kong/Traefik
                              │   (LB层)     │  SSL终止 + 路由
                              └──────┬──────┘
                                     │
            ┌────────────────────────┼────────────────────────┐
            │                        │                        │
     ┌──────▼──────┐          ┌──────▼──────┐          ┌──────▼──────┐
     │  Next.js    │          │  Go API     │          │  WebSocket  │
     │  Frontend   │          │  Services   │          │  Server     │
     │  (SSR/SSG)  │          │  (微服务)    │          │  (Socket.io)│
     │  3 replicas │          │  5 replicas │          │  2 replicas │
     └──────┬──────┘          └──────┬──────┘          └──────┬──────┘
            │                        │                        │
            └────────────────────────┼────────────────────────┘
                                     │
            ┌────────────────────────┼────────────────────────┐
            │                        │                        │
     ┌──────▼──────┐          ┌──────▼──────┐          ┌──────▼──────┐
     │ PostgreSQL  │          │   Redis     │          │   NATS      │
     │   Primary   │          │  (缓存/队列) │          │  (消息队列) │
     │   +副本     │          │  3 nodes    │          │  3 nodes    │
     └──────┬──────┘          └──────┬──────┘          └──────┬──────┘
            │                        │                        │
            └────────────────────────┼────────────────────────┘
                                     │
                              ┌──────▼──────┐
                              │ 监控/日志层  │
                              │ Prometheus  │
                              │ + Grafana   │
                              │ + Loki      │
                              └──────┬──────┘
                                     │
                              ┌──────▼──────┐
                              │  对象存储    │
                              │  S3/MinIO   │
                              │  (KYC照片)  │
                              └──────┴──────┘
```

#### 8.1.2 Kubernetes配置

```yaml
# 基础Deployment示例
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-service
spec:
  replicas: 5
  selector:
    matchLabels:
      app: api
  template:
    spec:
      containers:
      - name: api
        image: kickbet/api:v1.0
        ports:
        - containerPort: 8080
        resources:
          requests:
            cpu: "500m"
            memory: "512Mi"
          limits:
            cpu: "2000m"
            memory: "2Gi"
        env:
        - name: DB_HOST
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: host
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10

---
# HorizontalPodAutoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-service
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

#### 8.1.3 服务依赖关系

```
┌─────────────────────────────────────────────────────────────┐
│                     服务启动顺序                              │
└─────────────────────────────────────────────────────────────┘

Layer 1 (基础设施):
├── PostgreSQL (主库启动 → 副本同步)
├── Redis Cluster
├── NATS Cluster
└── Object Storage (S3/MinIO)

Layer 2 (核心服务):
├── Odds Service (赔率数据)
├── Wallet Service (钱包系统)
├── Auth Service (认证)
└── Game Service (Crash引擎)

Layer 3 (业务服务):
├── Event Service (赛事管理)
├── Bet Service (投注处理)
├── Payment Service (支付网关)
└── Settlement Service (结算)

Layer 4 (前端层):
├── Next.js Frontend
├── WebSocket Gateway
└── API Gateway (入口)
```

### 8.2 CI/CD流程

#### 8.2.1 Git分支策略

```
┌─────────────────────────────────────────────────────────────┐
│                     Git分支模型                              │
└─────────────────────────────────────────────────────────────┘

main (生产)
  │
  ├── release/v1.x (预发布)
  │     │
  │     └── develop (开发主分支)
  │           │
  │           ├── feature/xxx (功能开发)
  │           ├── feature/yyy
  │           │
  │           └── hotfix/xxx (紧急修复)
  │
  └── hotfix/xxx → 直接合并到main

流程:
1. 功能开发: develop → feature/xxx → PR → merge回develop
2. 发布: develop → release/v1.x → 测试 → merge到main
3. 紧急修复: main → hotfix/xxx → merge到main + develop
```

#### 8.2.2 CI Pipeline

```yaml
# GitHub Actions配置
name: CI Pipeline

on:
  push:
    branches: [develop, main]
  pull_request:
    branches: [develop]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Run Backend Tests
      run: |
        cd backend
        go test ./... -v -race -coverprofile=coverage.out
        go vet ./...
    
    - name: Run Frontend Tests
      run: |
        cd frontend
        npm ci
        npm run lint
        npm run test:unit
        npm run test:e2e
    
    - name: Security Scan
      uses: github/codeql-action/analyze@v3
    
    - name: Upload Coverage
      uses: codecov/codecov-action@v4

  build:
    needs: test
    if: github.ref == 'refs/heads/main'
    steps:
    - name: Build Docker Images
      run: |
        docker build -t kickbet/api:${{ github.sha }} ./backend
        docker build -t kickbet/frontend:${{ github.sha }} ./frontend
    
    - name: Push to Registry
      run: |
        docker push kickbet/api:${{ github.sha }}
        docker push kickbet/frontend:${{ github.sha }}

  deploy:
    needs: build
    if: github.ref == 'refs/heads/main'
    steps:
    - name: Deploy to Kubernetes
      run: |
        kubectl set image deployment/api api=kickbet/api:${{ github.sha }}
        kubectl set image deployment/frontend frontend=kickbet/frontend:${{ github.sha }}
        kubectl rollout status deployment/api
        kubectl rollout status deployment/frontend
```

#### 8.2.3 发布检查清单

```markdown
## 发布前检查清单

### 代码质量
- [ ] 所有测试通过(单元/集成/E2E)
- [ ] 代码覆盖率≥80%
- [ ] 无安全漏洞(CodeQL)
- [ ] 代码审查通过(至少2人)

### 功能验证
- [ ] 核心流程验证(注册/投注/支付)
- [ ] WebSocket连接测试
- [ ] Crash游戏公平性验证
- [ ] 移动端兼容测试

### 性能验证
- [ ] API响应时间<100ms(P95)
- [ ] 并发测试(1000 QPS)
- [ ] WebSocket压力测试(10000连接)

### 数据迁移
- [ ] 数据库迁移脚本验证
- [ ] 回滚脚本准备
- [ ] 数据备份完成

### 监控配置
- [ ] 新功能告警规则
- [ ] Dashboard更新
- [ ] 日志收集配置
```

### 8.3 监控与告警

#### 8.3.1 监控指标

**系统指标:**
```
CPU使用率          → node_cpu_usage
内存使用率         → node_memory_usage
磁盘IO            → node_disk_io
网络流量          → node_network_traffic
容器状态          → container_status
Pod重启次数       → pod_restart_count
```

**业务指标:**
```
活跃用户数         → active_users_count
并发投注数         → concurrent_bets
投注成功率         → bet_success_rate
支付成功率         → payment_success_rate
WebSocket连接数    → ws_connections
Crash游戏并发局数  → crash_games_concurrent
```

**性能指标:**
```
API响应时间(P50/P95/P99) → api_response_time
数据库查询时间           → db_query_time
WebSocket延迟           → ws_latency
赔率推送延迟            → odds_push_delay
```

#### 8.3.2 Prometheus配置

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
    - role: pod
    
  - job_name: 'api-service'
    static_configs:
    - targets: ['api:8080']
    metrics_path: /metrics
    
  - job_name: 'postgresql'
    static_configs:
    - targets: ['postgres-exporter:9187']
    
  - job_name: 'redis'
    static_configs:
    - targets: ['redis-exporter:9121']

rule_files:
  - 'alerts.yml'

# alerts.yml
groups:
- name: api-alerts
  rules:
  - alert: HighErrorRate
    expr: rate(api_errors_total[5m]) > 0.05
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "API错误率超过5%"
      
  - alert: HighLatency
    expr: histogram_quantile(0.95, api_response_time_bucket) > 1000
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "API P95延迟超过1秒"
```

#### 8.3.3 Grafana Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│                   KickBet 监控Dashboard                       │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ 活跃用户     │  │ 投注/分钟    │  │ 收入/小时    │
│   1,234     │  │    456      │  │   $12,345   │
└──────────────┘  └──────────────┘  └──────────────┘

┌─────────────────────────────────────────────────────────────┐
│ API响应时间分布                                              │
│ P50: 45ms  P95: 89ms  P99: 156ms                            │
│ [████████████████████████░░░░░░░░░░░░]                       │
└─────────────────────────────────────────────────────────────┘

┌────────────────────────┐  ┌────────────────────────┐
│ WebSocket连接数        │  │ Crash游戏状态          │
│ 当前: 8,543           │  │ 进行中: 12局           │
│ 峰值: 15,000          │  │ 等待中: 5秒            │
│ [▁▂▃▄▅▆▇█▇▆▅▄]       │  │ [🛫🛫🛫🛫🛫🛫🛫🛫]   │
└────────────────────────┘  └────────────────────────┘
```

### 8.4 日志管理

#### 8.4.1 日志架构

```
┌─────────────────────────────────────────────────────────────┐
│                     日志收集架构                              │
└─────────────────────────────────────────────────────────────┘

应用服务 → Fluentd/Fluent Bit → Loki → Grafana
                ↓
           结构化日志(JSON)
                ↓
           分级存储:
           ├── 热数据(7天): Loki内存
           ├── 温数据(30天): Loki磁盘
           └── 冷数据(365天): S3归档
```

#### 8.4.2 日志格式

```json
// 标准日志格式
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "info",
  "service": "bet-service",
  "trace_id": "abc-123-def",
  "user_id": "user-456",
  "action": "place_bet",
  "duration_ms": 45,
  "status": "success",
  "details": {
    "event_id": "event-789",
    "amount": 1000,
    "odds": 1.85
  }
}

// 错误日志格式
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "error",
  "service": "wallet-service",
  "trace_id": "xyz-456-abc",
  "error_code": 10001,
  "error_message": "Insufficient funds",
  "stack_trace": "...",
  "context": {
    "user_id": "user-456",
    "balance": 500,
    "required": 1000
  }
}
```

#### 8.4.3 日志查询示例

```logql
// 查询投注错误
{service="bet-service"} |= "error" | json | level="error"

// 查询特定用户操作
{service="*"} | json | user_id="user-123"

// 查询慢请求
{service="api"} | json | duration_ms > 1000

// 统计错误率
rate({service="bet-service"} |= "error" [5m])
```

### 8.5 数据备份与恢复

#### 8.5.1 备份策略

```yaml
备份类型:
  全量备份: 每周日 02:00
  增量备份: 每日 02:00
  实时备份: WAL日志持续归档

备份内容:
  PostgreSQL:
    - pg_dump全量备份
    - WAL日志归档
    - 配置文件
  
  Redis:
    - RDB快照(每6小时)
    - AOF日志
  
  对象存储:
    - KYC照片(跨区域复制)

备份存储:
  主存储: AWS S3 (同区域)
  异地备份: AWS S3 (异地区域)
  本地缓存: 保留最近7天
```

#### 8.5.2 恢复流程

```
┌─────────────────────────────────────────────────────────────┐
│                     数据恢复流程                              │
└─────────────────────────────────────────────────────────────┘

场景1: 单表误删
├── 从最近备份恢复单表
├── 应用WAL日志到误删前
└── 验证数据完整性

场景2: 数据库崩溃
├── 创建新数据库实例
├── 恢复最近全量备份
├── 应用所有WAL日志
├── 验证数据一致性
└── 切换应用连接

场景3: 灾备切换
├── 激活异地备份区域
├── 从异地S3恢复数据
├── 启动备用服务
├── DNS切换到备用节点
└── 通知用户(可选)
```

**恢复时间目标:**
| 场景 | RTO (恢复时间) | RPO (数据丢失) |
|------|----------------|----------------|
| 单表误删 | < 30分钟 | < 5分钟 |
| 数据库崩溃 | < 2小时 | < 10分钟 |
| 区域灾难 | < 4小时 | < 30分钟 |

### 8.6 容灾设计

#### 8.6.1 多区域部署

```
┌─────────────────────────────────────────────────────────────┐
│                     双区域架构                                │
└─────────────────────────────────────────────────────────────┘

Region A (主区域 - 新加坡):
├── 完整服务栈
├── PostgreSQL主库
├── Redis主节点
├── 全量数据

Region B (备区域 - 香港):
├── 冷备服务栈(平时停止)
├── PostgreSQL副本(实时同步)
├── Redis副本
├── 数据实时复制

切换流程:
故障检测 → 激活Region B → DNS切换 → 服务恢复
预计时间: 15-30分钟
```

#### 8.6.2 故障演练计划

```markdown
## 定期故障演练

季度演练:
1. 模拟API服务故障 → 自动扩容测试
2. 模拟数据库故障 → 副本切换测试
3. 模拟区域故障 → 跨区域切换测试

年度演练:
1. 全面灾难恢复演练
2. 数据恢复完整性验证
3. 业务连续性测试

演练记录:
- 演练时间
- 演练场景
- 恢复时间
- 发现问题
- 改进措施
```

---

## 9. 开发计划

### 9.1 项目里程碑

```
┌─────────────────────────────────────────────────────────────┐
│                     KickBet 开发里程碑                        │
└─────────────────────────────────────────────────────────────┘

Phase 1: MVP (4个月)
├── 核心用户系统(注册/登录/KYC)
├── 钱包系统(充值/提现/余额)
├── 足球博彩基础(赛前投注/结算)
├── 简单赛事管理(手动录入)
└── Web端基本页面

Phase 2: 增强 (3个月)
├── Live Betting(实时赔率/WebSocket)
├── Crash游戏(完整流程/公平验证)
├── 支付网关集成(GCash/MoMo等)
├── 移动端PWA优化
└── 基础监控告警

Phase 3: 完善 (3个月)
├── 赔率数据源集成(第三方API)
├── 管理后台(赛事管理/用户管理)
├── 高级风控(AML/限额系统)
├── 多语言支持(6种语言)
└── 性能优化(并发/缓存)

Phase 4: 运维 (2个月)
├── 生产环境部署(Kubernetes)
├── 监控系统完善(Grafana)
├── 容灾方案实施(双区域)
├── 安全加固(WAF/加密)
└── 压力测试与调优
```

### 9.2 详细任务分解

#### Phase 1: MVP (第1-4个月)

**第1个月: 基础架构**
```
Week 1-2:
├── 项目初始化
│   ├── 前端项目搭建(Next.js 15)
│   ├── 后端项目搭建(Go + Gin)
│   ├── 数据库初始化(PostgreSQL)
│   └── Docker开发环境
│
├── 用户认证
│   ├── 注册流程(手机号/邮箱)
│   ├── JWT认证实现
│   ├── 登录/登出
│   └── 密码hash(bcrypt)
│
└── 数据库表创建
    ├── users表
    ├── wallets表
    ├── transactions表

Week 3-4:
├── 钱包系统
│   ├── 余额查询API
│   ├── 交易历史API
│   ├── 余额更新逻辑(FOR UPDATE锁)
│   └── 前端钱包页面
│
└── 基础前端页面
    ├── 登录/注册页面
    ├── 首页骨架
    ├── 钱包页面
    └── 响应式布局
```

**第2个月: 赛事与投注**
```
Week 5-6:
├── 赛事数据模型
│   ├── leagues/teams/events表
│   ├── odds表
│   ├── 赛事录入API(管理端)
│   └── 赛事列表/详情API
│
├── 投注系统基础
│   ├── sports_bets表
│   ├── bet_selections表
│   ├── 投注下单API
│   ├── 投注验证逻辑
│   └── 投注历史API
│
└── 前端赛事页面
    ├── 赛事列表页
    ├── 赛事详情页
    ├── 投注单组件
    └── 投注确认流程

Week 7-8:
├── 结算系统
│   ├── 手动结算API
│   ├── 结算计算逻辑
│   ├── 批量结算事务
│   └── 钱包余额更新
│
└── 支付集成(基础)
    ├── deposits/withdrawals表
    ├── 充值流程(模拟)
    ├── 提现流程(手动审核)
    └── 前端充值/提现页面
```

**第3个月: KYC与优化**
```
Week 9-10:
├── KYC系统
│   ├── kyc_verifications表
│   ├── KYC提交API
│   ├── Smile ID集成
│   ├── KYC审核后台
│   └── 提现KYC强制检查
│
├── 用户体验优化
│   ├── 投注流程简化(3步)
│   ├── 错误提示优化
│   ├── 加载状态优化
│   └── 移动端适配

Week 11-12:
├── 基础测试
│   ├── 单元测试(覆盖率70%)
│   ├── 集成测试
│   ├── E2E测试(核心流程)
│   └── 安全扫描
│
└── MVP收尾
    ├── Bug修复
    ├── 性能优化
    ├── 文档整理
    └── 内部测试
```

**第4个月: MVP上线**
```
Week 13-14:
├── 部署准备
│   ├── 生产环境搭建
│   ├── 基础监控配置
│   ├── 备份策略
│   └── 安全配置
│
└── MVP发布
    ├── Beta测试(内部)
    ├── Bug修复
    ├── 用户反馈收集
    └── 正式上线
```

#### Phase 2: 增强 (第5-7个月)

```
第5个月:
├── WebSocket基础设施
│   ├── Socket.io服务搭建
│   ├── 连接管理
│   ├── 断线重连
│   └── 前端WebSocket客户端
│
├── Live Betting
│   ├── 实时赔率推送
│   ├── 赔率变化处理
│   ├── Live投注流程
│   └── 前端Live页面
│
└── Crash游戏基础
    ├── crash_games表
    ├── crash_bets表
    ├── Crash引擎算法
    ├── 下注/Cash Out API

第6个月:
├── Crash游戏完整
│   ├── WebSocket推送(crash_tick)
│   ├── Canvas动画
│   ├── 公平验证页面
    │   ├── 历史记录显示
│   └── 自动Cash Out
│
├── 支付网关集成
│   ├── GCash集成
│   ├── MoMo集成
│   ├── 回调验证
│   └── 多支付方式支持

第7个月:
├── PWA优化
│   ├── Service Worker
│   ├── 离线支持
│   ├── 推送通知
│   └── 安装引导
│
└── 基础监控
    ├── Prometheus部署
    ├── Grafana Dashboard
    ├── 基础告警规则
    └── 日志收集(Loki)
```

#### Phase 3: 完善 (第8-10个月)

```
第8个月:
├── 赔率数据源
│   ├── 第三方API集成(Betradar等)
│   ├── 赔率同步服务
│   ├── 数据清洗验证
│   └── 实时更新推送
│
├── 管理后台
│   ├── 赛事管理页面
│   ├── 用户管理页面
│   ├── 报表页面
│   └── 权限控制

第9个月:
├── 高级风控
│   ├── 投注限额系统
│   ├── AML检测规则
│   ├── 自我排除功能
│   └── 风控后台页面
│
├── 多语言支持
│   ├── i18n配置
│   ├── 6种语言翻译
│   ├── 语言切换UI
│   └── 本地化内容

第10个月:
├── 性能优化
│   ├── API缓存策略
│   ├── 数据库索引优化
│   ├── 前端代码分割
│   ├── WebSocket连接池
│
└── 完善测试
    ├── 压力测试(1000 QPS)
    ├── WebSocket压力(10000连接)
    ├── Crash游戏公平性验证
    └── 完整回归测试
```

#### Phase 4: 运维 (第11-12个月)

```
第11个月:
├── Kubernetes部署
│   ├── Helm Charts
│   ├── HPA配置
│   ├── Ingress配置
│   └── Secrets管理
│
├── 监控完善
│   ├── 业务指标采集
│   ├── Dashboard优化
│   ├── 告警规则完善
│   ├── SLO定义

第12个月:
├── 容灾实施
│   ├── 双区域部署
│   ├── 数据同步配置
│   ├── DNS切换方案
│   ├── 故障演练
│
├── 安全加固
│   ├── WAF规则
│   ├── 加密增强
│   ├── 安全审计
│   └── 渗透测试
│
└── 上线准备
    ├── 最终压力测试
    ├── 文档完善
    ├── 运维手册
    └── 正式发布
```

### 9.3 团队配置

```
┌─────────────────────────────────────────────────────────────┐
│                     推荐团队配置                              │
└─────────────────────────────────────────────────────────────┘

核心团队 (MVP阶段 - 6人):
├── 项目经理/产品经理: 1人
│   └── 负责需求管理、进度跟踪、协调沟通
│
├── 后端开发: 2人
│   ├── 1人负责核心服务(钱包/认证)
│   └── 1人负责业务服务(投注/赛事)
│
├── 前端开发: 2人
│   ├── 1人负责页面开发
│   └── 1人负责组件/动画(Crash游戏)
│
└── 测试/QA: 1人
    └── 负责测试、Bug跟踪、质量把控

增强阶段 (Phase 2-3 - 8-10人):
├── 增加1名DevOps(部署/监控)
├── 增加1名后端(支付/风控)
├── 增加1名前端(PWA/优化)
├── 增加1名数据工程师(赔率数据)

运维阶段 (Phase 4 - 可外包):
├── DevOps工程师: 2人
├── 安全工程师: 1人(可兼职)
└── 运维支持: 按需
```

**人员技能要求:**
| 角色 | 必备技能 | 加分技能 |
|------|----------|----------|
| 后端 | Go、PostgreSQL、Redis | 微服务、WebSocket |
| 前端 | React、Next.js、TypeScript | Canvas动画、PWA |
| DevOps | Kubernetes、CI/CD | Prometheus、Grafana |
| QA | 自动化测试、E2E | 性能测试、安全测试 |

### 9.4 技术风险与应对

```
┌─────────────────────────────────────────────────────────────┐
│                     技术风险评估                              │
└─────────────────────────────────────────────────────────────┘

风险1: 并发性能瓶颈
├── 影响: 高峰期投注延迟/失败
├── 概率: 中
├── 应对:
│   ├── 早期压力测试
│   ├── Redis缓存预热
│   ├── 数据库连接池优化
│   └── 可降级服务设计

风险2: WebSocket稳定性
├── 影响: 实时推送中断
├── 概率: 中
├── 应对:
│   ├── 断线重连机制
│   ├── 多节点负载均衡
│   ├── 心跳检测
│   └── 降级为HTTP轮询

风险3: 第三方支付集成
├── 影响: 充值/提现失败
├── 概率: 高(初期)
├── 应对:
│   ├── 多支付渠道备份
│   ├── 完善回调验证
│   ├── 异常订单监控
│   └── 人工处理流程

风险4: 赔率数据源不稳定
├── 影响: 赔率更新延迟
├── 概率: 中
├── 应对:
│   ├── 多数据源备份
│   ├── 本地缓存兜底
│   ├── 数据质量监控
│   └── 手动录入应急

风险5: 安全漏洞
├── 影响: 数据泄露/资金损失
├── 概率: 中
├── 应对:
│   ├── 定期安全审计
│   ├── 渗透测试
│   ├── 代码扫描(CodeQL)
│   ├── 安全开发培训
```

### 9.5 成本估算

```
┌─────────────────────────────────────────────────────────────┐
│                     开发成本估算                              │
└─────────────────────────────────────────────────────────────┘

人力成本 (12个月):
├── MVP阶段(4个月): 6人 × $5000/月 × 4月 = $120,000
├── 增强阶段(3个月): 8人 × $5000/月 × 3月 = $120,000
├── 完善阶段(3个月): 10人 × $5000/月 × 3月 = $150,000
├── 运维阶段(2个月): 4人 × $5000/月 × 2月 = $40,000
└── 总人力成本: ~$430,000

基础设施成本 (月度):
├── 云服务器(AWS/GCP):
│   ├── 生产环境: $2000-5000/月
│   ├── 开发/测试: $500/月
│
├── 第三方服务:
│   ├── 赔率数据API: $500-2000/月
│   ├── KYC服务(Smile ID): $0.5-2/次验证
│   ├── 支付网关: 1-3%交易手续费
│   ├── CDN(Cloudflare): $200/月
│   ├── 监控(Grafana Cloud): $100/月
│
└── 其他:
    ├── SSL证书: $50/年
    ├── 邮件服务: $50/月
    ├── SMS通知: 按量计费

总成本估算:
├── 开发阶段(12个月): $450,000-500,000
├── 运营阶段(月度): $3000-8000/月
└── 首年总成本: $500,000-600,000
```

### 9.6 关键成功指标

```yaml
技术指标:
  MVP上线时间: ≤ 4个月
  代码覆盖率: ≥ 80%
  API响应时间(P95): < 100ms
  WebSocket连接稳定性: ≥ 99.5%
  Crash游戏公平验证: 100%可验证

业务指标(MVP后3个月):
  注册用户: ≥ 1000
  日活用户: ≥ 100
  投注成功率: ≥ 95%
  支付成功率: ≥ 98%
  用户留存率(7日): ≥ 30%

运维指标:
  系统可用性: ≥ 99.9%
  故障恢复时间: < 30分钟
  数据备份成功率: 100%
  安全事件: 0重大漏洞
```

---

## 附录

### A. 参考资料

1. **lets-bet项目**: https://github.com/ross-willis/lets-bet
   - Go微服务架构参考
   - Crash引擎实现
   - 钱包系统设计

2. **Bustabit算法**: Provably Fair Crash游戏标准
   - HMAC-SHA256种子计算
   - 公平性验证方法

3. **Next.js文档**: https://nextjs.org/docs
   - App Router架构
   - SSR/SSG最佳实践

4. **shadcn/ui**: https://ui.shadcn.com
   - React组件库
   - Tailwind CSS集成

### B. 技术选型对比

| 类别 | 选项A | 选项B | 最终选择 | 理由 |
|------|-------|-------|----------|------|
| 前端框架 | Next.js | Nuxt.js | Next.js | 文档完善、生态大 |
| UI组件库 | shadcn/ui | Ant Design | shadcn/ui | 可定制、轻量 |
| 状态管理 | Zustand | Redux | Zustand | 简单、性能好 |
| 后端语言 | Go | Node.js | Go | 高并发、类型安全 |
| 数据库 | PostgreSQL | MySQL | PostgreSQL | JSON支持、扩展好 |
| 缓存 | Redis | Memcached | Redis | 数据结构丰富 |
| 消息队列 | NATS | Kafka | NATS | 轻量、实时性好 |
| 部署 | Kubernetes | Docker Compose | Kubernetes | 可扩展、自动化 |

### C. 法律合规提示

```
重要提示:
本设计文档仅供技术研究目的。

在中国大陆:
- 博彩活动属于违法行为
- 本文档不应用于中国大陆市场

目标市场(东南亚):
- 需获取当地牌照(如菲律宾PAGCOR)
- 需遵守当地法律法规
- 需建立合规运营体系

开发者责任:
- 了解目标市场法律
- 不向禁止地区提供服务
- 建立负责任博彩机制
```

---

> 文档状态: 完成
> 版本: 1.0.0
> 最后更新: 2026-05-07
> 
> 如有问题或建议，请联系设计团队。