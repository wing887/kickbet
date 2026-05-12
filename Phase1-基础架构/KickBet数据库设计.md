# KickBet 数据库设计文档

> 数据库选型：SQLite（MVP阶段，零成本）

---

## 一、数据库文件结构

```
data/
├── kickbet_users.db      # 用户数据
├── kickbet_predictions.db # 预测数据
├── kickbet_news.db       # 新闻缓存数据
└── kickbet_logs.db       # 系统日志
```

---

## 二、用户数据库 (kickbet_users.db)

### 表结构

#### users - 用户表

```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,                    -- UUID
    email TEXT UNIQUE NOT NULL,             -- 邮箱
    password_hash TEXT NOT NULL,            -- 密码哈希
    username TEXT,                          -- 用户名(可选)
    role TEXT DEFAULT 'free',               -- 角色: free | premium
    premium_expire_at DATETIME,             -- 会员到期时间
    daily_free_count INTEGER DEFAULT 0,     -- 今日已用免费次数
    daily_free_reset_at DATETIME,           -- 计数重置时间
    avatar_url TEXT,                        -- 头像URL
    preferred_leagues TEXT,                 -- 常看联赛(JSON)
    risk_preference TEXT DEFAULT 'half',    -- 风险偏好: full | half
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
```

#### user_bet_records - 投注记录表

```sql
CREATE TABLE user_bet_records (
    id TEXT PRIMARY KEY,                    -- UUID
    user_id TEXT NOT NULL,                  -- 用户ID
    match_id TEXT NOT NULL,                 -- 比赛ID
    bookmaker TEXT,                         -- 博彩公司
    bet_type TEXT NOT NULL,                 -- 投注类型: home_win | draw | away_win | over | under
    bet_amount REAL NOT NULL,               -- 投注金额
    odds REAL NOT NULL,                     -- 赔率
    result TEXT DEFAULT 'pending',          -- 结果: pending | win | lose | cancel
    actual_result TEXT,                     -- 实际比赛结果
    profit REAL DEFAULT 0,                  -- 盈亏金额
    note TEXT,                              -- 用户备注
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_bet_records_user ON user_bet_records(user_id);
CREATE INDEX idx_bet_records_match ON user_bet_records(match_id);
CREATE INDEX idx_bet_records_result ON user_bet_records(result);
CREATE INDEX idx_bet_records_created ON user_bet_records(created_at);
```

#### user_statistics - 用户统计表

```sql
CREATE TABLE user_statistics (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL UNIQUE,
    total_bets INTEGER DEFAULT 0,           -- 总投注次数
    win_count INTEGER DEFAULT 0,            -- 赢次数
    lose_count INTEGER DEFAULT 0,           -- 输次数
    pending_count INTEGER DEFAULT 0,        -- 待结算次数
    win_rate REAL DEFAULT 0,                -- 胜率
    total_investment REAL DEFAULT 0,        -- 总投入
    total_return REAL DEFAULT 0,            -- 总回报
    roi REAL DEFAULT 0,                     -- 投资回报率
    best_bet_id TEXT,                       -- 最佳投注ID
    worst_bet_id TEXT,                      -- 最差投注ID
    monthly_stats TEXT,                     -- 月度统计(JSON)
    league_stats TEXT,                      -- 联赛统计(JSON)
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_stats_user ON user_statistics(user_id);
```

#### subscriptions - 订阅记录表

```sql
CREATE TABLE subscriptions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    plan TEXT NOT NULL,                     -- 计划: premium_99
    amount REAL NOT NULL,                   -- 支付金额
    payment_method TEXT,                    -- 支付方式: alipay | wechat
    payment_status TEXT DEFAULT 'pending',  -- 支付状态: pending | success | failed
    transaction_id TEXT,                    -- 交易流水号
    start_at DATETIME,                      -- 开始时间
    expire_at DATETIME,                     -- 到期时间
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_subs_user ON subscriptions(user_id);
CREATE INDEX idx_subs_status ON subscriptions(payment_status);
```

#### free_usage_log - 免费次数使用日志

```sql
CREATE TABLE free_usage_log (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    match_id TEXT NOT NULL,
    analysis_level TEXT DEFAULT 'L2',       -- 使用的是L2分析
    used_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_free_log_user ON free_usage_log(user_id);
CREATE INDEX idx_free_log_date ON free_usage_log(used_at);
```

---

## 三、预测数据库 (kickbet_predictions.db)

### 表结构

#### matches - 比赛表

```sql
CREATE TABLE matches (
    id TEXT PRIMARY KEY,                    -- UUID
    league_id TEXT NOT NULL,                -- 联赛ID
    league_name TEXT NOT NULL,              -- 联赛名称
    league_slug TEXT,                       -- 联赛slug
    home_team_id TEXT NOT NULL,             -- 主队ID
    home_team_name TEXT NOT NULL,           -- 主队名称
    home_team_logo TEXT,                    -- 主队logo
    away_team_id TEXT NOT NULL,             -- 客队ID
    away_team_name TEXT NOT NULL,           -- 客队名称
    away_team_logo TEXT,                    -- 客队logo
    match_time DATETIME NOT NULL,           -- 比赛时间
    venue TEXT,                             -- 场地
    status TEXT DEFAULT 'upcoming',         -- 状态: upcoming | live | finished | cancelled
    home_score INTEGER,                     -- 主队进球(已结束)
    away_score INTEGER,                     -- 客队进球(已结束)
    result TEXT,                            -- 结果: home_win | draw | away_win
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_matches_league ON matches(league_id);
CREATE INDEX idx_matches_time ON matches(match_time);
CREATE INDEX idx_matches_status ON matches(status);
CREATE INDEX idx_matches_teams ON matches(home_team_id, away_team_id);
```

#### predictions - 预测表

```sql
CREATE TABLE predictions (
    id TEXT PRIMARY KEY,
    match_id TEXT NOT NULL UNIQUE,
    
    -- 基础概率
    home_win_prob REAL,                     -- 主胜概率
    draw_prob REAL,                         -- 平局概率
    away_win_prob REAL,                     -- 客胜概率
    
    -- 期望进球
    predicted_home_goals REAL,              -- 预测主队进球
    predicted_away_goals REAL,              -- 预测客队进球
    
    -- Poisson模拟结果
    poisson_results TEXT,                   -- Poisson5000次结果(JSON)
    
    -- 推荐投注
    recommended_bet TEXT,                   -- 推荐投注类型
    recommended_odds REAL,                  -- 推荐赔率
    confidence REAL,                        -- 置信度(0-100)
    value_edge REAL,                        -- 价值优势(模型概率-隐含概率)
    
    -- 分析内容
    analysis_l2 TEXT,                       -- L2初级分析(JSON)
    analysis_l3 TEXT,                       -- L3进阶分析(JSON)
    analysis_l4 TEXT,                       -- L4高阶分析(JSON)
    
    -- 是否为首页推荐
    is_daily_pick BOOLEAN DEFAULT 0,        -- 是否每日推荐
    pick_reason TEXT,                       -- 推荐理由
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (match_id) REFERENCES matches(id)
);

CREATE INDEX idx_predictions_match ON predictions(match_id);
CREATE INDEX idx_predictions_confidence ON predictions(confidence);
CREATE INDEX idx_predictions_daily ON predictions(is_daily_pick);
```

#### odds - 赔率表

```sql
CREATE TABLE odds (
    id TEXT PRIMARY KEY,
    match_id TEXT NOT NULL,
    bookmaker TEXT NOT NULL,                -- 博彩公司: bet365 | sbobet | pinnacle
    odds_type TEXT NOT NULL,                -- 赔率类型: match_winner | over_under | handicap
    
    -- 赔率值
    home_odds REAL,                         -- 主胜赔率
    draw_odds REAL,                         -- 平局赔率
    away_odds REAL,                         -- 客胜赔率
    over_odds REAL,                         -- 大球赔率
    under_odds REAL,                        -- 小球赔率
    over_under_line REAL,                   -- 大小球线
    handicap_home REAL,                     -- 让球盘主队赔率
    handicap_away REAL,                     -- 让球盘客队赔率
    handicap_line REAL,                     -- 让球盘线
    
    -- 时间戳
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (match_id) REFERENCES matches(id)
);

CREATE INDEX idx_odds_match ON odds(match_id);
CREATE INDEX idx_odds_bookmaker ON odds(bookmaker);
CREATE INDEX idx_odds_fetched ON odds(fetched_at);
```

#### odds_history - 赔率历史变动表

```sql
CREATE TABLE odds_history (
    id TEXT PRIMARY KEY,
    match_id TEXT NOT NULL,
    bookmaker TEXT NOT NULL,
    odds_type TEXT NOT NULL,
    
    -- 变动记录
    opening_odds REAL,                      -- 开盘赔率
    current_odds REAL,                      -- 当前赔率
    previous_odds REAL,                     -- 上一次赔率
    movement_direction TEXT,                -- 变动方向: up | down | stable
    movement_percent REAL,                  -- 变动百分比
    
    -- 时间
    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (match_id) REFERENCES matches(id)
);

CREATE INDEX idx_odds_history_match ON odds_history(match_id);
CREATE INDEX idx_odds_history_time ON odds_history(recorded_at);
```

#### odds_movement_analysis - 赔率变动分析表

```sql
CREATE TABLE odds_movement_analysis (
    id TEXT PRIMARY KEY,
    match_id TEXT NOT NULL,
    odds_history_id TEXT NOT NULL,
    
    -- AI分析结果
    possible_reasons TEXT,                  -- 可能原因(JSON)
    news_articles TEXT,                     -- 关联新闻(JSON)
    ai_analysis TEXT,                       -- AI分析结论(中文)
    bookmaker_intent TEXT,                  -- 博彩公司意图推测
    
    -- 启示
    betting_insight TEXT,                   -- 投注启示
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (match_id) REFERENCES matches(id),
    FOREIGN KEY (odds_history_id) REFERENCES odds_history(id)
);

CREATE INDEX idx_movement_analysis_match ON odds_movement_analysis(match_id);
```

#### team_stats - 球队统计表

```sql
CREATE TABLE team_stats (
    id TEXT PRIMARY KEY,
    team_id TEXT NOT NULL,
    team_name TEXT NOT NULL,
    league_id TEXT NOT NULL,
    season TEXT,                            -- 赛季
    
    -- 进攻统计
    goals_scored INTEGER,                   -- 总进球
    goals_per_game REAL,                    -- 场均进球
    shots_per_game REAL,                    -- 场均射门
    attack_rating REAL,                     -- 进攻评级
    
    -- 防守统计
    goals_conceded INTEGER,                 -- 总失球
    goals_conceded_per_game REAL,           -- 场均失球
    defense_rating REAL,                    -- 防守评级
    
    -- 其他
    wins INTEGER,
    draws INTEGER,
    losses INTEGER,
    points INTEGER,
    position INTEGER,                       -- 排名
    form TEXT,                              -- 近期状态(W/D/L序列)
    
    -- 时间
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_team_stats_team ON team_stats(team_id);
CREATE INDEX idx_team_stats_league ON team_stats(league_id);
```

#### combo_bets - 组合投注表

```sql
CREATE TABLE combo_bets (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    
    -- 用户选择
    match_ids TEXT NOT NULL,                -- 选中比赛ID(JSON数组)
    bet_types TEXT NOT NULL,                -- 各场投注类型(JSON)
    
    -- 资金信息
    total_budget REAL NOT NULL,             -- 用户总资金
    kelly_allocation TEXT,                  -- Kelly分配(JSON)
    
    -- 串关建议
    parlay_suggestions TEXT,                -- 串关建议(JSON)
    recommended_parlay TEXT,                -- 推荐串关方案
    
    -- 风险评估
    risk_score REAL,                        -- 风险评分(0-100)
    expected_roi REAL,                      -- 期望ROI
    
    -- 状态
    status TEXT DEFAULT 'generated',        -- generated | saved | executed
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_combo_bets_user ON combo_bets(user_id);
```

#### daily_recommendations - 每日推荐历史表

```sql
CREATE TABLE daily_recommendations (
    id TEXT PRIMARY KEY,
    prediction_id TEXT NOT NULL,
    date DATE NOT NULL,                     -- 推荐日期
    
    -- 推荐信息
    league_name TEXT,
    home_team TEXT,
    away_team TEXT,
    recommended_bet TEXT,
    confidence REAL,
    
    -- 结果追踪(比赛结束后更新)
    match_result TEXT,                      -- 实际结果
    prediction_correct BOOLEAN,             -- 预测是否正确
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (prediction_id) REFERENCES predictions(id)
);

CREATE INDEX idx_daily_recommendations_date ON daily_recommendations(date);
CREATE INDEX idx_daily_recommendations_correct ON daily_recommendations(prediction_correct);
```

---

## 四、新闻数据库 (kickbet_news.db)

### 表结构

#### news_articles - 新闻文章表

```sql
CREATE TABLE news_articles (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,                   -- 来源: espn | bbc | sky_sports | goal_com
    source_url TEXT,                        -- 原文链接
    
    -- 内容
    title_en TEXT NOT NULL,                 -- 英文标题
    title_cn TEXT,                          -- 中文标题(翻译后)
    content_en TEXT,                        -- 英文内容摘要
    content_cn TEXT,                        -- 中文内容摘要(翻译后)
    
    -- 关联
    team_ids TEXT,                          -- 关联球队(JSON数组)
    league_ids TEXT,                        -- 关联联赛(JSON数组)
    match_id TEXT,                          -- 关联比赛
    
    -- 分类
    category TEXT,                          -- 分类: injury | transfer | match_preview | general
    importance INTEGER DEFAULT 1,           -- 重要程度(1-5)
    
    -- 时间
    published_at DATETIME,
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    translated_at DATETIME                  -- 翻译时间
);

CREATE INDEX idx_news_teams ON news_articles(team_ids);
CREATE INDEX idx_news_match ON news_articles(match_id);
CREATE INDEX idx_news_published ON news_articles(published_at);
CREATE INDEX idx_news_category ON news_articles(category);
```

#### news_fetch_log - 新闻抓取日志

```sql
CREATE TABLE news_fetch_log (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    fetch_count INTEGER,                    -- 本次抓取数量
    new_count INTEGER,                      -- 新增数量
    error_count INTEGER,                    -- 错误数量
    fetch_duration REAL,                    -- 抓取耗时(秒)
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_news_fetch_log_source ON news_fetch_log(source);
CREATE INDEX idx_news_fetch_log_time ON news_fetch_log(fetched_at);
```

---

## 五、联赛配置

### 表结构 (kickbet_predictions.db)

#### leagues - 联赛表

```sql
CREATE TABLE leagues (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,                     -- 联赛名称
    name_cn TEXT,                           -- 中文名称
    slug TEXT NOT NULL,                     -- Odds-API slug
    country TEXT,                           -- 国家
    
    -- 统计参数
    avg_home_goals REAL DEFAULT 1.5,        -- 场均主队进球
    avg_away_goals REAL DEFAULT 1.2,        -- 场均客队进球
    avg_total_goals REAL DEFAULT 2.7,       -- 场均总进球
    
    -- 特点
    description TEXT,                       -- 联赛特点描述
    priority INTEGER DEFAULT 0,             -- 优先级(首页展示)
    
    -- 状态
    is_active BOOLEAN DEFAULT 1,            -- 是否活跃
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 初始化联赛数据
INSERT INTO leagues (id, name, name_cn, slug, country, avg_home_goals, avg_away_goals, priority) VALUES
('league_csl', 'Chinese Super League', '中超', 'china-chinese-super-league', 'China', 1.8, 1.4, 10),
('league_epl', 'Premier League', '英超', 'england-premier-league', 'England', 1.7, 1.3, 9),
('league_jleague', 'J-League', '日职', 'japan-jleague', 'Japan', 1.5, 1.2, 8),
('league_kleague', 'K-League 1', '韩K', 'republic-of-korea-k-league-1', 'South Korea', 1.6, 1.3, 7),
('league_ll', 'La Liga', '西甲', 'spain-la-liga', 'Spain', 1.5, 1.1, 6),
('league_bl', 'Bundesliga', '德甲', 'germany-bundesliga', 'Germany', 1.8, 1.2, 5),
('league_sa', 'Serie A', '意甲', 'italy-serie-a', 'Italy', 1.4, 1.1, 4),
('league_fl', 'Ligue 1', '法甲', 'france-ligue-1', 'France', 1.5, 1.1, 3);
```

---

## 六、数据分析视图

### 视图定义

#### vw_user_roi - 用户ROI视图

```sql
CREATE VIEW vw_user_roi AS
SELECT 
    u.id as user_id,
    u.email,
    u.role,
    s.total_bets,
    s.win_count,
    s.lose_count,
    ROUND(s.win_rate * 100, 2) as win_rate_percent,
    s.total_investment,
    s.total_return,
    ROUND(s.roi * 100, 2) as roi_percent
FROM users u
LEFT JOIN user_statistics s ON u.id = s.user_id;
```

#### vw_prediction_accuracy - 预测准确率视图

```sql
CREATE VIEW vw_prediction_accuracy AS
SELECT 
    p.id,
    p.match_id,
    m.league_name,
    m.home_team_name,
    m.away_team_name,
    m.result as actual_result,
    p.recommended_bet,
    p.confidence,
    CASE 
        WHEN m.result = p.recommended_bet THEN 1
        ELSE 0
    END as is_correct
FROM predictions p
JOIN matches m ON p.match_id = m.id
WHERE m.status = 'finished';
```

#### vw_daily_pick_performance - 每日推荐表现视图

```sql
CREATE VIEW vw_daily_pick_performance AS
SELECT 
    dr.date,
    dr.league_name,
    dr.home_team,
    dr.away_team,
    dr.recommended_bet,
    dr.confidence,
    dr.match_result,
    dr.prediction_correct,
    COUNT(*) as total_count,
    SUM(CASE WHEN dr.prediction_correct = 1 THEN 1 ELSE 0 END) as correct_count
FROM daily_recommendations dr
GROUP BY dr.date;
```

---

## 七、数据初始化脚本

```sql
-- 创建所有表
-- (上述CREATE TABLE语句)

-- 创建索引
-- (上述CREATE INDEX语句)

-- 创建视图
-- (上述CREATE VIEW语句)

-- 初始化联赛数据
-- (上述INSERT语句)

-- 创建管理员账户(可选)
INSERT INTO users (id, email, password_hash, role, username) VALUES
('admin_001', 'admin@kickbet.com', 'hashed_password', 'premium', 'Admin');
```

---

## 八、数据迁移策略

当用户量超过5000时，迁移到PostgreSQL：

```python
# 迁移脚本概要
def migrate_to_postgresql():
    # 1. 导出SQLite数据
    users_data = export_table('kickbet_users.db', 'users')
    predictions_data = export_table('kickbet_predictions.db', 'predictions')
    
    # 2. 创建PostgreSQL表(相同结构)
    create_pg_tables()
    
    # 3. 导入数据
    import_to_pg('users', users_data)
    import_to_pg('predictions', predictions_data)
    
    # 4. 验证数据一致性
    verify_migration()
    
    # 5. 切换数据库连接
    update_config('DATABASE_URL', 'postgresql://...')
```

---

## 九、备份策略

```bash
# 每日备份脚本
#!/bin/bash
DATE=$(date +%Y%m%d)
BACKUP_DIR="/data/backups/$DATE"

mkdir -p $BACKUP_DIR

# 备份数据库
sqlite3 data/kickbet_users.db ".backup $BACKUP_DIR/kickbet_users.db"
sqlite3 data/kickbet_predictions.db ".backup $BACKUP_DIR/kickbet_predictions.db"
sqlite3 data/kickbet_news.db ".backup $BACKUP_DIR/kickbet_news.db"

# 压缩
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR

# 上传到云存储(可选)
# aws s3 cp $BACKUP_DIR.tar.gz s3://kickbet-backups/
```