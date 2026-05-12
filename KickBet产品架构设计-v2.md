# KickBet 产品架构设计 v2.0

> 核心定位：教育型足球预测助手 - 教你理解为什么

---

## 一、产品定位

**一句话价值主张**：
> KickBet 不是告诉你投什么，而是教你理解为什么。

**目标用户**：
- 核心服务：B类（中级用户）+ C类（高级用户）
- 适当考虑：A类（小白用户）
- 放弃：D类（专业用户/开发者）

---

## 二、权限模型

### 用户层级

| 层级 | 价格 | 标识 |
|------|------|------|
| 免费用户 | ¥0 | `free` |
| 付费会员 | ¥99/月 | `premium` |

### 功能矩阵

| 功能 | free | premium |
|------|:----:|:-------:|
| 赔率数据查看（全部联赛/场次） | ✅ | ✅ |
| 首页每日推荐（L4完整分析） | ✅ | ✅ |
| 自选预测（L2初级分析） | 3场/天 | 无限制 |
| 自选预测（L3进阶分析） | ❌ | ✅ |
| 组合投注建议（Kelly+串关） | ❌ | ✅ |
| 赔率变动分析（AI新闻驱动） | ❌ | ✅ |
| 投注追踪（盈亏/ROI） | ❌ | ✅ |
| 教育内容 | ✅ | ✅ |

### 分析层级定义

| 层级 | 名称 | 内容 | 适用权限 |
|------|------|------|----------|
| L2 | 初级分析 | 数据依据 + 赔率对比 + 一句话建议 | free(限3场) |
| L3 | 进阶分析 | 完整数据依据 + 隐含概率分析 + Kelly比例 + 风险提示 | premium |
| L4 | 高阶分析 | Poisson模拟 + 市场情绪 + 赔率历史 + AI新闻解读 | 首页推荐(全员) |

---

## 三、系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        展示层 (Frontend)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Web前端    │  │  管理后台   │  │  API接口(预留)       │  │
│  │  Vue.js+PWA │  │  内容管理   │  │  第三方接入          │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        业务层 (Backend)                       │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌────────┐ │
│  │用户系统 │ │预测引擎 │ │分析引擎 │ │新闻引擎 │ │追踪系统│ │
│  │认证权限│ │Poisson  │ │赔率变动│ │AI检索  │ │投注记录│ │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │  组合投注引擎   │  │  内容管理系统   │                   │
│  │  Kelly + 串关   │  │  教育内容管理   │                   │
│  └─────────────────┘  └─────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        数据层 (Data)                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  用户数据库  │  │  预测数据库  │  │  新闻缓存           │  │
│  │  SQLite     │  │  SQLite     │  │  Redis              │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  赔率缓存    │  │  历史数据    │  │  Rate Limit监控     │  │
│  │  Redis      │  │  SQLite     │  │  Counter            │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        数据源层 (Sources)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Odds-API.io │  │ 新闻API     │  │ 积分榜数据           │  │
│  │ 赔率数据    │  │ 英文体育新闻│  │ Football-Data.org   │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  自建爬虫（预留）                                        │  │
│  │  Bet365/Sbobet官网实时赔率                              │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 四、核心模块设计

### 模块1：用户系统

```
用户数据模型

users
├── id (UUID)
├── email
├── password_hash
├── role: free | premium
├── premium_expire_at (会员到期时间)
├── daily_free_count (今日已用免费次数)
├── daily_free_reset_at (计数重置时间)
├── created_at
└── updated_at

user_bet_records (投注追踪)
├── id
├── user_id
├── match_id
├── bet_type (投注类型)
├── bet_amount
├── odds
├── result: pending | win | lose
├── profit (盈亏)
├── created_at
```

### 权限控制逻辑

```python
# 每日免费次数检查
def check_free_limit(user):
    if user.role == 'premium':
        return True  # 付费用户无限制
    
    # 检查是否需要重置计数
    if user.daily_free_reset_at < today():
        user.daily_free_count = 0
        user.daily_free_reset_at = tomorrow()
    
    if user.daily_free_count >= 3:
        return False  # 今日已用完3次
    return True

# 消耗免费次数
def consume_free_limit(user):
    if user.role == 'free':
        user.daily_free_count += 1
        save(user)
```

---

### 模块2：预测引擎

```
预测引擎架构

prediction_engine/
├── poisson_predictor.py      # 泊松分布预测
├── kelly_criterion.py        # Kelly资金管理
├── probability_calculator.py # 隐含概率计算
├── match_analyzer.py         # 比赛分析
└── confidence_estimator.py   # 置信度评估

预测输出模型

predictions
├── id
├── match_id
├── league
├── home_team
├── away_team
├── match_time
├── home_win_prob (主胜概率)
├── draw_prob (平局概率)
├── away_win_prob (客胜概率)
├── predicted_home_goals
├── predicted_away_goals
├── recommended_bet (推荐投注)
├── confidence (置信度)
├── analysis_l2 (初级分析JSON)
├── analysis_l3 (进阶分析JSON)
├── analysis_l4 (高阶分析JSON)
├── created_at
└── updated_at
```

### Poisson预测流程

```python
def predict_match(home_team, away_team, league):
    # 1. 获取历史数据
    home_stats = get_team_stats(home_team, league)
    away_stats = get_team_stats(away_team, league)
    
    # 2. 计算期望进球
    lambda_home = home_stats.attack * away_stats.defense * league.avg_home_goals
    lambda_away = away_stats.attack * home_stats.defense * league.avg_away_goals
    
    # 3. Poisson模拟
    results = poisson_simulation(lambda_home, lambda_away, 5000)
    
    # 4. 计算概率
    home_win_prob = results['home_win'] / 5000
    draw_prob = results['draw'] / 5000
    away_win_prob = results['away_win'] / 5000
    
    # 5. 生成各层级分析
    analysis = {
        'L2': generate_l2_analysis(home_win_prob, draw_prob, away_win_prob),
        'L3': generate_l3_analysis(...),
        'L4': generate_l4_analysis(...)
    }
    
    return prediction
```

---

### 模块3：组合投注引擎

```
组合投注引擎架构

combo_bet_engine/
├── kelly_allocator.py        # Kelly资金分配
├── parlay_optimizer.py       # 串关优化
├── risk_manager.py           # 风险管理
└── combo_generator.py        # 组合生成

组合投注输出

combo_bets
├── id
├── user_id
├── match_ids (选中的比赛列表)
├── bet_types (各场投注类型)
├── total_budget (总资金)
├── kelly_allocation (Kelly分配JSON)
├── parlay_suggestions (串关建议JSON)
├── risk_score (风险评分)
├── expected_roi (期望ROI)
├── created_at
```

### Kelly资金分配

```python
def kelly_allocate(matches, total_budget, user_risk_preference='half'):
    """
    matches: 用户选中的比赛列表
    total_budget: 用户输入的总资金
    user_risk_preference: full/full-kelly | half/half-kelly
    """
    allocations = []
    
    for match in matches:
        # 获取预测概率和赔率
        prob = match.predicted_prob
        odds = match.current_odds
        
        # 计算Kelly比例
        edge = prob - (1/odds)  # 优势
        kelly = edge / (odds - 1)  # Kelly公式
        
        # Half-Kelly保守策略
        if user_risk_preference == 'half':
            kelly = kelly * 0.5
        
        # 计算分配金额
        allocation = total_budget * kelly
        allocations.append({
            'match': match,
            'kelly_ratio': kelly,
            'amount': allocation
        })
    
    return allocations

def generate_parlay(matches, total_budget):
    """
    生成串关建议
    """
    # 计算各场置信度
    confidence_scores = [m.confidence for m in matches]
    
    # 串关组合方案
    parlays = [
        {'type': 'double', 'matches': 2, 'combined_odds': ..., 'risk': 'low'},
        {'type': 'treble', 'matches': 3, 'combined_odds': ..., 'risk': 'medium'},
        {'type': 'full_parlay', 'matches': len(matches), 'combined_odds': ..., 'risk': 'high'}
    ]
    
    # 根据置信度推荐串关方案
    recommended = select_best_parlay(parlays, confidence_scores)
    
    return recommended
```

---

### 模块4：赔率变动分析引擎 (AI新闻驱动)

```
赔率变动分析架构

odds_movement_engine/
├── odds_tracker.py           # 赔率追踪
├── news_fetcher.py           # 新闻检索
├── news_analyzer.py          # AI新闻分析
├── translator.py             # 英文翻译中文
├── movement_explainer.py     # 变动解释生成
└── news_sources/
│   ├── espn.py               # ESPN体育新闻
│   ├── bbc_sport.py          # BBC Sport
│   ├── sky_sports.py         # Sky Sports
│   └── goal_com.py           # Goal.com

赔率变动数据

odds_movements
├── id
├── match_id
├── bookmaker (博彩公司)
├── odds_type (赔率类型)
├── opening_odds (开盘赔率)
├── current_odds (当前赔率)
├── movement_direction (变动方向)
├── movement_percent (变动百分比)
├── movement_time
├── possible_reasons (可能原因JSON)
├── news_articles (关联新闻JSON)
├── ai_analysis (AI分析结论)
├── created_at
```

### AI新闻分析流程

```python
def analyze_odds_movement(match, odds_history):
    # 1. 检测赔率变动
    movement = detect_movement(odds_history)
    
    if movement.significant:  # 显著变动(>5%)
        # 2. 检索相关新闻
        news = fetch_news(match.home_team, match.away_team, match.league)
        
        # 3. AI分析新闻与赔率关联
        analysis = ai_analyze(news, movement)
        
        # 4. 英文新闻翻译中文
        translated_news = translate_to_chinese(news)
        
        # 5. 生成解释
        explanation = generate_explanation(movement, translated_news, analysis)
        
        return {
            'movement': movement,
            'news': translated_news,
            'analysis': explanation
        }
    
    return None

def ai_analyze(news, movement):
    """
    使用LLM分析新闻与赔率变动的关系
    """
    prompt = f"""
    赔率变动：{movement.bookmaker} {movement.odds_type} 从 {movement.opening} 变到 {movement.current}
    
    相关新闻：
    {news_articles_text}
    
    请分析：
    1. 哪些新闻可能导致此赔率变动？
    2. 博彩公司的意图是什么？
    3. 对投注者有什么启示？
    """
    
    response = call_llm(prompt)
    return response
```

---

### 模块5：首页推荐系统

```
首页推荐架构

recommendation_engine/
├── daily_picker.py           # 每日推荐选择器
├── confidence_ranker.py      # 置信度排序
├── value_detector.py         # 价值赔率检测
├── league_balancer.py        # 联赛均衡

推荐选择逻辑

def pick_daily_recommendation():
    # 获取今日所有比赛预测
    today_predictions = get_today_predictions()
    
    # 筛选标准
    candidates = []
    
    for pred in today_predictions:
        # 1. 置信度 > 70%
        if pred.confidence >= 0.70:
            # 2. 有价值赔率（模型概率 > 隐含概率）
            if has_value(pred):
                # 3. 赔率变动有分析价值
                if has_movement_analysis(pred):
                    candidates.append(pred)
    
    # 按置信度排序
    candidates.sort(key=lambda x: x.confidence, reverse=True)
    
    # 联赛均衡（优先不同联赛）
    selected = balance_by_league(candidates)
    
    # 取第一名作为首页推荐
    recommendation = selected[0]
    
    # 生成完整L4分析
    recommendation.full_analysis = generate_l4_analysis(recommendation)
    
    return recommendation
```

---

### 模块6：投注追踪系统

```
投注追踪架构

bet_tracker/
├── record_manager.py         # 记录管理
├── roi_calculator.py         # ROI计算
├── statistics_generator.py   # 统计生成
├── report_generator.py       # 报告生成

用户投注统计

user_statistics
├── user_id
├── total_bets (总投注次数)
├── win_count (赢次数)
├── lose_count (输次数)
├── win_rate (胜率)
├── total_investment (总投入)
├── total_return (总回报)
├── roi (投资回报率)
├── best_bet (最佳投注)
├── worst_bet (最差投注)
├── monthly_stats (月度统计JSON)
└── updated_at
```

---

## 五、数据源配置

### 主数据源

| 数据源 | 用途 | 调用限制 | 成本 |
|--------|------|----------|------|
| **Odds-API.io** | 赔率数据 | 100次/小时(免费) | 免费 |
| **Football-Data.org** | 积分榜、球队统计 | 10次/分钟 | 免费 |
| **ESPN API** | 体育新闻 | 无限制 | 免费 |
| **BBC Sport RSS** | 新闻源 | 无限制 | 免费 |

### 备用数据源（预留）

| 数据源 | 用途 | 状态 |
|--------|------|------|
| 自建爬虫 | Bet365/Sbobet官网 | 预留 |
| 懂球帝爬虫 | 中超数据 | 预留 |

### Rate Limit管理

```python
class RateLimiter:
    def __init__(self, limit_per_hour=100):
        self.limit = limit_per_hour
        self.current_count = 0
        self.reset_time = next_hour()
    
    def can_call(self):
        if datetime.now() >= self.reset_time:
            self.current_count = 0
            self.reset_time = next_hour()
        
        return self.current_count < self.limit
    
    def record_call(self):
        self.current_count += 1
        save_to_redis('rate_limit', self.current_count)
```

---

## 六、前端架构

### 技术栈

| 层级 | 技术 |
|------|------|
| 框架 | Vue.js 3 |
| UI风格 | Linear Minimal Dark |
| 状态管理 | Pinia |
| 路由 | Vue Router |
| PWA | vite-plugin-pwa |
| HTTP | Axios |
| 图表 | Chart.js |

### 设计系统

```
颜色体系
├── --bg-primary: #08090a     (主背景)
├── --bg-card: #121314        (卡片背景)
├── --text-primary: #ffffff   (主文字)
├── --text-secondary: #8b8b8b (次要文字)
├── --border: #2a2b2c         (分割线)
├── --accent-success: #00d4aa (成功/推荐)
├── --accent-warning: #ff6b6b (风险/警告)
├── --accent-neutral: #ffa500 (中性)

字体体系
├── --font-main: Inter        (标题/正文)
├── --font-mono: Roboto Mono  (数字)
├── --font-code: Fira Code    (代码)

间距体系
├── --spacing-xs: 4px
├── --spacing-sm: 8px
├── --spacing-md: 16px
├── --spacing-lg: 24px
├── --spacing-xl: 32px
```

### 页面结构

```
页面路由

/                   首页（每日推荐 + 赔率列表）
├── /matches        比赛列表（联赛筛选）
├── /match/:id      比赛详情（预测分析）
├── /combo          组合投注（付费）
├── /tracker        投注追踪（付费）
├── /learn          教育中心
├── /login          登录
├── /register       注册
├── /subscribe      订阅付费
└── /profile        个人中心
```

### 首页布局

```
┌────────────────────────────────────┐
│         Header                      │
│  [Logo]  [联赛筛选]  [登录/会员]     │
├────────────────────────────────────┤
│         每日推荐                     │
│  ┌──────────────────────────────┐  │
│  │  曼城 vs 布伦特福德           │  │
│  │  英超 | 今晚 21:00            │  │
│  │  ────────────────────────    │  │
│  │  推荐：曼城胜 @ 1.42          │  │
│  │  置信度：75%                  │  │
│  │  ────────────────────────    │  │
│  │  [查看完整L4分析] ↓           │  │
│  │  Poisson模拟 + Kelly比例      │  │
│  │  + 赔率变动 + AI新闻解读      │  │
│  └──────────────────────────────┘  │
├────────────────────────────────────┤
│         今日赔率列表                 │
│  ┌────────┐ ┌────────┐ ┌────────┐  │
│  │中超    │ │英超    │ │日职    │  │
│  │3场     │ │5场     │ │2场     │  │
│  └────────┘ └────────┘ └────────┘  │
├────────────────────────────────────┤
│         组合投注入口（付费）          │
│  [选择比赛] → [输入资金] → [生成建议] │
│  ⚠️ 需会员权限                      │
├────────────────────────────────────┤
│         Footer                      │
│  [教育中心] [关于我们] [联系方式]     │
└────────────────────────────────────┘
```

---

## 七、开发优先级

| 优先级 | 模块 | 说明 | 预估工时 |
|--------|------|------|----------|
| **P0** | 用户系统 + 权限控制 | 免费/付费区分基础 | 3天 |
| **P1** | 数据持久化 (SQLite) | 预测历史、用户数据 | 2天 |
| **P2** | 预测引擎 L2/L3/L4 | 核心价值输出 | 4天 |
| **P3** | 首页推荐系统 | 引流关键 | 2天 |
| **P4** | 前端界面 (Vue.js) | 用户入口 | 5天 |
| **P5** | 组合投注引擎 | 付费核心功能 | 3天 |
| **P6** | 赔率变动 + AI新闻 | 付费差异化功能 | 4天 |
| **P7** | 投注追踪系统 | 用户粘性功能 | 2天 |
| **P8** | 教育内容管理 | 引流内容 | 2天 |

**总预估：约23天**

---

## 八、技术选型汇总

| 层级 | 选型 | 理由 |
|------|------|------|
| **数据库** | SQLite | MVP阶段，零成本，<1万用户够用 |
| **缓存** | Redis | 赔率缓存、Rate Limit计数 |
| **后端** | Python Flask | 已有代码基础，快速迭代 |
| **前端** | Vue.js 3 + PWA | 组件化、离线支持、移动优先 |
| **LLM** | OpenAI API / DeepSeek | AI新闻分析、翻译 |
| **支付** | 支付宝/微信（预留） | 国内用户为主 |

---

## 九、下一步行动

1. **确认架构** - 用户确认此架构设计
2. **数据库设计** - 细化SQLite表结构
3. **API设计** - 定义RESTful接口
4. **前端组件设计** - 细化UI组件库
5. **开发启动** - 按P0-P8顺序开发

---

## 十、关键风险

| 风险 | 影响 | 应对方案 |
|------|------|----------|
| Odds-API Rate Limit | 数据获取受限 | 缓存策略 + 预留自建爬虫 |
| AI新闻分析成本 | LLM调用费用 | 控制调用频率、缓存分析结果 |
| 预测准确率 | 用户信任度 | 持续优化模型、透明展示历史战绩 |
| 法律合规 | 内容风险 | 仅提供分析建议，不提供博彩链接 |