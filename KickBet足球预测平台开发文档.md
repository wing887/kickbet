# KickBet 足球预测平台开发文档

## 项目概述

KickBet 是一个面向亚洲用户的足球比赛预测平台，结合 Poisson 统计模型和 Kelly Criterion 资金管理策略，为用户提供价值投注建议。

**目标用户**: 亚洲用户（中超、K联赛、J联赛等亚洲联赛）

**技术栈**: Python Flask 后端 + Poisson 预测引擎 + Kelly Criterion

**项目路径**: `~/.openclaw/workspace/betting-platform-design/data-collector/`

---

## 项目结构

```
data-collector/
├── collectors/                  # 数据采集层
│   ├── football_data_org.py    # Football-Data.org 赛事数据
│   ├── odds_collector.py       # The Odds API 赔率数据 (旧)
│   └── odds_api_io.py          # Odds-API.io 赔率数据 (新)
├── predictors/                  # 预测引擎
│   ├── poisson_predictor.py    # Poisson 模型 + Kelly Criterion
├── config/
│   └── config_manager.py       # 配置管理
├── web/
│   ├── app.py                  # Flask 主应用
│   ├── templates/              # HTML 模板
│   └── data/                   # 数据缓存
└── README.md
```

---

## 数据源对比

| 数据源 | 博彩公司 | 让球盘 | 大小球 | 中超 | Rate Limit | 状态 |
|--------|----------|--------|--------|------|------------|------|
| **The Odds API** | 56家欧美 | ❌ | ❌ | ✅(无赔率) | 500/月 | 旧版 |
| **Odds-API.io** | Bet365+Sbobet | ✅ | ✅ | ✅ | 100/小时 | 新版 ✅ |

### Odds-API.io 优势

1. **包含 Sbobet (皇冠)** - 亚洲用户熟悉的博彩公司
2. **让球盘 Spread** - 主流亚洲盘口
3. **大小球 Totals** - 进球数预测
4. **中超赔率** - 实时赔率数据
5. **更宽松的 Rate Limit** - 100次/小时 vs 500次/月

---

## API 配置

### Football-Data.org (赛事数据)
```
API Token: 84e1509844e14a469520d5ed4fb7f148
用途: 获取积分榜、比赛列表、球队统计
联赛: PL(英超), BL1(德甲), PD(西甲), SA(意甲), FL1(法甲)
```

### The Odds API (旧版赔率)
```
API Key: f040e2bbe2f251fa9d56702ce668263c
用途: 56家欧美博彩公司赔率
限制: 500次/月，仅 h2h 市场
```

### Odds-API.io (新版赔率) ✅
```
API Key: b74442d9ec2af9d312bae2ddda7d9cf5a622f6bd0b77702595c57bd63773d2ab
用途: Bet365 + Sbobet 赔率，含让球盘和大小球
限制: 100次/小时 (免费计划)
博彩公司: Bet365, Sbobet (免费)
付费解锁: 277家博彩公司
```

---

## 支持的联赛

### 欧洲联赛
| 代码 | 联赛 | Odds-API.io slug |
|------|------|------------------|
| PL | 英超 | england-premier-league |
| BL1 | 德甲 | germany-bundesliga |
| PD | 西甲 | spain-la-liga |
| SA | 意甲 | italy-serie-a |
| FL1 | 法甲 | france-ligue-1 |
| CL | 欧冠 | europe-uefa-champions-league |
| EL | 欧联杯 | europe-uefa-europa-league |

### 亚洲联赛 ✅
| 代码 | 联赛 | Odds-API.io slug |
|------|------|------------------|
| CSL | 中超 | china-chinese-super-league |
| JL | J联赛 | japan-jleague |
| KL | K联赛 | republic-of-korea-k-league-1 |
| ISL | 印度超 | india-indian-super-league |
| THL | 泰国联赛 | thailand-thai-league-1 |
| VNL | 越南联赛 | vietnam-v-league-1 |
| MSL | 马来西亚联赛 | malaysia-super-league |
| SPL | 新加坡联赛 | singapore-premier-league |

---

## Web API 端点

### 页面路由
```
/               # 首页 - 今日预测
/odds           # 赔率对比页面
/history        # 历史追踪页面
/settings       # 设置页面
```

### 数据 API
```
GET /api/standings/<competition>     # 积分榜
GET /api/matches/<competition>       # 比赛列表
GET /api/odds/<sport>                # The Odds API 赔率 (旧)
GET /api/odds-io/<competition>       # Odds-API.io 赔率 (新) ✅
GET /api/predict/<competition>       # 比赛预测 (使用 Odds-API.io)
GET /api/history                     # 历史记录
GET/POST /api/settings               # 用户设置
```

### 示例请求

```bash
# 英超赔率
curl http://localhost:5000/api/odds-io/PL

# 中超赔率
curl http://localhost:5000/api/odds-io/CSL

# 英超预测
curl http://localhost:5000/api/predict/PL
```

---

## 赔率数据结构

### ML (胜平负)
```json
{
  "home_odds": 1.285,
  "home_bookmaker": "Bet365",
  "draw_odds": 6.2,
  "draw_bookmaker": "Sbobet",
  "away_odds": 9.8,
  "away_bookmaker": "Sbobet"
}
```

### Spread (让球盘)
```json
{
  "spread_hdp": -1.75,
  "spread_home_odds": 2.05,
  "spread_home_bookmaker": "Sbobet",
  "spread_away_odds": 1.88,
  "spread_away_bookmaker": "Sbobet"
}
```

### Totals (大小球)
```json
{
  "totals_hdp": 3.25,
  "totals_over_odds": 2.07,
  "totals_over_bookmaker": "Sbobet",
  "totals_under_odds": 2.025,
  "totals_under_bookmaker": "Bet365"
}
```

---

## 预测引擎

### Poisson 模型

基于球队进攻/防守能力模拟比赛得分：

```python
class TeamAttackDefenseStats:
    team_id: str
    team_name: str
    home_scored_avg: float    # 主场场均进球
    home_conceded_avg: float  # 主场场均失球
    away_scored_avg: float    # 客场场均进球
    away_conceded_avg: float  # 客场场均失球
```

**模拟过程**:
1. 计算主队期望进球 = home_attack × away_defense × league_avg
2. 计算客队期望进球 = away_attack × home_defense × league_avg
3. Poisson 模拟 5000 次，统计胜/平/负概率
4. 找出最可能比分

### Kelly Criterion

资金管理策略，计算最优投注比例：

```python
kelly_fraction = (model_prob × odds - 1) / (odds - 1)

# 限制
min_edge = 0.02       # 最小优势阈值
max_fraction = 0.25   # 最大投注比例 (保守)
```

---

## 球队名称规范化

Football-Data.org 和 Odds-API.io 使用不同的球队命名，需要统一：

| Football-Data.org | Odds-API.io | 规范化 |
|-------------------|-------------|--------|
| Liverpool FC | Liverpool | Liverpool |
| Chelsea FC | Chelsea | Chelsea |
| Brighton & Hove Albion FC | Brighton & Hove Albion | Brighton and Hove Albion |
| Wolverhampton Wanderers FC | Wolverhampton Wanderers | Wolverhampton Wanderers |
| Sunderland AFC | Sunderland AFC | Sunderland AFC (保留) |

**规范化规则**:
- 去掉 FC 后缀（保留 AFC）
- 替换 & 为 and
- 逆向映射支持双向匹配

---

## 开发进度

### 已完成 ✅

1. **数据采集层**
   - Football-Data.org 赛事数据采集
   - The Odds API 赔率采集 (旧)
   - Odds-API.io 赔率采集 (新，含让球盘和大小球)

2. **预测引擎**
   - Poisson 模型实现
   - Kelly Criterion 实现
   - Value Bet 检测

3. **Web Server**
   - Flask API 服务
   - 积分榜、比赛列表、赔率、预测端点
   - 数据缓存机制

4. **球队名称匹配**
   - 规范化函数
   - 双向映射字典
   - 中超球队名称支持

5. **亚洲联赛支持**
   - 中超 CSL ✅
   - J联赛 JL ✅
   - K联赛 KL ✅
   - 其他亚洲联赛配置

### 待完成

1. **让球盘预测策略**
   - Spread 市场价值分析
   - Kelly Criterion 扩展

2. **大小球预测策略**
   - Totals 市场价值分析
   - 进球数分布预测

3. **中超完整预测**
   - Football-Data.org 不支持中超积分榜
   - 需使用纯 Odds-API.io 数据

4. **前端界面**
   - 移动端优先设计
   - Linear Minimal Dark 风格
   - 实时赔率更新

5. **数据持久化**
   - 预测历史记录
   - 投注追踪
   - 盈亏分析

---

## 测试结果

### 中超赔率测试 ✅

```
比赛数: 5
博彩公司: Bet365, Sbobet

青岛西海岸 vs 武汉三镇
  ML: 1.96 / 3.4 / 3.8
  让球 -0.5: 1.975 / 1.825
  大小球 2.5: 1.975 / 1.825

北京国安 vs 上海申花
  ML: 1.7 / 4.0 / 4.75
  让球 -0.75: 1.9 / 1.92
  大小球 3.0: 1.85 / 2.0
```

### 英超预测测试 ✅

```
比赛数: 15
匹配率: 50% (需要继续优化)

Brighton vs Wolves ✅
  ML: 1.285 / 6.2 / 9.8
  让球 -1.75: 2.05 / 1.88
  大小球 3.25: 2.07 / 2.025

Man City vs Brentford ✅
  ML: 1.42 / 5.8 / 7.0
  让球 -1.5: 2.0 / 1.93
```

---

## Rate Limit 管理

### Odds-API.io

```
免费计划: 100次请求/小时
当前剩余: 0 (已超限)
重置时间: 每小时重置
```

**建议**:
- 使用缓存减少 API 调用
- 批量请求合并
- 监控剩余次数

---

## 下一步计划

### 短期 (本周)

1. 完善球队名称匹配
2. 添加让球盘预测策略
3. 添加大小球预测策略
4. 优化 Rate Limit 使用

### 中期 (本月)

1. 中超完整预测流程
2. 前端移动端界面
3. 数据持久化
4. 部署到 Cloudflare Pages

### 长期

1. 更多亚洲联赛
2. 付费博彩公司数据
3. 实时赔率监控
4. AI 模型优化

---

## 文件清单

### 核心文件

| 文件 | 说明 | 状态 |
|------|------|------|
| collectors/football_data_org.py | 赛事数据采集 | ✅ |
| collectors/odds_collector.py | The Odds API (旧) | ✅ |
| collectors/odds_api_io.py | Odds-API.io (新) | ✅ |
| predictors/poisson_predictor.py | 预测引擎 | ✅ |
| web/app.py | Flask 主应用 | ✅ |

### 配置文件

| 文件 | 说明 |
|------|------|
| config/config_manager.py | API 配置 |

---

## 服务器运行

```bash
cd ~/.openclaw/workspace/betting-platform-design/data-collector
python web/app.py

# 访问
http://localhost:5000
```

---

## 备注

- 用户偏好移动端优先设计
- Linear Minimal Dark 风格 (#08090a 背景)
- 亚洲用户为主要目标群体
- 免费计划足够测试使用

---

生成时间: 2026-05-09