# KickBet API 设计文档

> RESTful API 设计规范

---

## 一、API 基础信息

| 项目 | 说明 |
|------|------|
| **Base URL** | `https://api.kickbet.com/v1` |
| **协议** | HTTPS |
| **认证** | JWT Token (Bearer) |
| **格式** | JSON |
| **编码** | UTF-8 |

### 请求头标准

```http
Content-Type: application/json
Accept: application/json
Authorization: Bearer <jwt_token>
Accept-Language: zh-CN  // 中文响应
```

### 响应格式标准

```json
// 成功响应
{
    "success": true,
    "data": { ... },
    "message": "操作成功"
}

// 错误响应
{
    "success": false,
    "error": {
        "code": "ERROR_CODE",
        "message": "错误描述",
        "details": { ... }
    }
}
```

### 分页格式

```json
{
    "success": true,
    "data": [ ... ],
    "pagination": {
        "page": 1,
        "per_page": 20,
        "total": 100,
        "total_pages": 5
    }
}
```

---

## 二、认证接口

### 2.1 用户注册

```http
POST /auth/register
```

**请求体**
```json
{
    "email": "user@example.com",
    "password": "password123",
    "username": "用户名(可选)"
}
```

**响应**
```json
{
    "success": true,
    "data": {
        "user_id": "uuid",
        "email": "user@example.com",
        "role": "free",
        "token": "jwt_token"
    },
    "message": "注册成功"
}
```

**错误码**
| code | 说明 |
|------|------|
| EMAIL_EXISTS | 邮箱已注册 |
| INVALID_EMAIL | 邮箱格式错误 |
| PASSWORD_TOO_SHORT | 密码少于6位 |

---

### 2.2 用户登录

```http
POST /auth/login
```

**请求体**
```json
{
    "email": "user@example.com",
    "password": "password123"
}
```

**响应**
```json
{
    "success": true,
    "data": {
        "user_id": "uuid",
        "email": "user@example.com",
        "username": "用户名",
        "role": "free",
        "premium_expire_at": null,
        "daily_free_remaining": 3,
        "token": "jwt_token",
        "refresh_token": "refresh_token"
    }
}
```

---

### 2.3 刷新Token

```http
POST /auth/refresh
```

**请求体**
```json
{
    "refresh_token": "refresh_token"
}
```

**响应**
```json
{
    "success": true,
    "data": {
        "token": "new_jwt_token"
    }
}
```

---

### 2.4 获取用户信息

```http
GET /auth/me
```

**响应**
```json
{
    "success": true,
    "data": {
        "user_id": "uuid",
        "email": "user@example.com",
        "username": "用户名",
        "role": "free",
        "premium_expire_at": null,
        "daily_free_remaining": 2,
        "daily_free_reset_at": "2026-05-11T00:00:00Z",
        "avatar_url": null,
        "risk_preference": "half",
        "created_at": "2026-05-10T12:00:00Z"
    }
}
```

---

## 三、赔率数据接口

### 3.1 获取联赛列表

```http
GET /leagues
```

**响应**
```json
{
    "success": true,
    "data": [
        {
            "id": "league_csl",
            "name": "中超",
            "name_en": "Chinese Super League",
            "country": "China",
            "match_count": 3,
            "priority": 10
        },
        {
            "id": "league_epl",
            "name": "英超",
            "name_en": "Premier League",
            "country": "England",
            "match_count": 5,
            "priority": 9
        }
    ]
}
```

---

### 3.2 获取比赛列表

```http
GET /matches
```

**查询参数**
| 参数 | 类型 | 说明 |
|------|------|------|
| league_id | string | 联赛ID(可选) |
| date | string | 日期 YYYY-MM-DD(可选) |
| status | string | upcoming/live/finished(可选) |
| page | int | 页码(默认1) |
| per_page | int | 每页数量(默认20) |

**响应**
```json
{
    "success": true,
    "data": [
        {
            "id": "match_001",
            "league": {
                "id": "league_epl",
                "name": "英超"
            },
            "home_team": {
                "id": "team_mci",
                "name": "曼城",
                "logo": "https://..."
            },
            "away_team": {
                "id": "team_bfc",
                "name": "布伦特福德",
                "logo": "https://..."
            },
            "match_time": "2026-05-10T21:00:00Z",
            "status": "upcoming",
            "odds": {
                "bet365": {
                    "home_odds": 1.42,
                    "draw_odds": 4.50,
                    "away_odds": 8.00
                },
                "sbobet": {
                    "home_odds": 1.45,
                    "draw_odds": 4.40,
                    "away_odds": 7.80
                }
            }
        }
    ],
    "pagination": {
        "page": 1,
        "per_page": 20,
        "total": 15,
        "total_pages": 1
    }
}
```

---

### 3.3 获取比赛详情

```http
GET /matches/:match_id
```

**响应**
```json
{
    "success": true,
    "data": {
        "id": "match_001",
        "league": { ... },
        "home_team": { ... },
        "away_team": { ... },
        "match_time": "2026-05-10T21:00:00Z",
        "venue": "Etihad Stadium",
        "status": "upcoming",
        "odds": {
            "bet365": { ... },
            "sbobet": { ... }
        },
        "odds_history": {
            "bet365": [
                {"odds": 1.35, "time": "2026-05-07T00:00:00Z"},
                {"odds": 1.42, "time": "2026-05-09T00:00:00Z"}
            ]
        },
        "team_stats": {
            "home": {
                "goals_per_game": 2.1,
                "defense_rating": 0.8,
                "form": "WWWDW"
            },
            "away": {
                "goals_per_game": 1.2,
                "defense_rating": 1.1,
                "form": "LWLLD"
            }
        }
    }
}
```

---

## 四、预测接口

### 4.1 获取每日推荐

```http
GET /predictions/daily-pick
```

**说明**: 获取首页每日推荐比赛（L4完整分析，所有人可见）

**响应**
```json
{
    "success": true,
    "data": {
        "id": "pred_001",
        "match": {
            "id": "match_001",
            "league": {"name": "英超"},
            "home_team": {"name": "曼城"},
            "away_team": {"name": "布伦特福德"},
            "match_time": "2026-05-10T21:00:00Z"
        },
        "recommended_bet": "home_win",
        "recommended_odds": 1.42,
        "confidence": 75,
        "value_edge": 5,
        "analysis": {
            "l4": {
                "summary": "曼城主场对阵布伦特福德，模型预测主胜概率75%",
                "data_basis": [
                    "曼城近10场场均进球2.1个",
                    "布伦特福德客场防守场均失球1.5个",
                    "曼城主场胜率85%"
                ],
                "probability_analysis": {
                    "model_probability": 75,
                    "implied_probability": 70,
                    "value_edge": 5
                },
                "kelly_suggestion": {
                    "kelly_ratio": 0.12,
                    "half_kelly": 0.06,
                    "recommended_stake": "总资金的6%"
                },
                "poisson_simulation": {
                    "iterations": 5000,
                    "most_likely_score": "2-0",
                    "home_win_pct": 75,
                    "draw_pct": 15,
                    "away_win_pct": 10
                },
                "odds_movement": {
                    "opening": 1.35,
                    "current": 1.42,
                    "change": "+5%",
                    "analysis": "赔率上升可能因客队主力后卫复出消息"
                },
                "news_analysis": [
                    {
                        "source": "ESPN",
                        "title": "布伦特福德后卫复出",
                        "summary": "布伦特福德主力后卫本周末有望复出...",
                        "impact": "可能增强客队防守"
                    }
                ],
                "risk_warning": [
                    "赔率变动需关注临场变化",
                    "如果临场降到1.38，资金继续流入主队",
                    "如果临场升到1.48，可能是诱导反向投注"
                ]
            }
        },
        "pick_reason": "高置信度+有价值赔率+赔率变动有分析价值"
    }
}
```

---

### 4.2 获取比赛预测(用户权限控制)

```http
GET /predictions/:match_id
```

**权限逻辑**:
- 免费用户：每天限3场，返回L2初级分析
- 付费用户：无限制，返回L3进阶分析

**响应(免费用户 L2)**
```json
{
    "success": true,
    "data": {
        "id": "pred_001",
        "match": { ... },
        "recommended_bet": "home_win",
        "recommended_odds": 1.42,
        "confidence": 75,
        "analysis": {
            "l2": {
                "summary": "曼城胜率75%，赔率1.42有价值",
                "data_basis": "曼城主场强势，近10场场均2.1球",
                "recommendation": "建议投注主胜"
            }
        },
        "free_usage": {
            "used": true,
            "remaining_today": 2
        },
        "upgrade_hint": "升级会员可查看完整进阶分析"
    }
}
```

**响应(付费用户 L3)**
```json
{
    "success": true,
    "data": {
        "id": "pred_001",
        "match": { ... },
        "recommended_bet": "home_win",
        "recommended_odds": 1.42,
        "confidence": 75,
        "value_edge": 5,
        "analysis": {
            "l3": {
                "summary": "曼城主胜概率75%，赔率1.42有5%价值优势",
                "data_basis": [
                    "曼城近10场场均进球2.1个",
                    "布伦特福德客场防守场均失球1.5个"
                ],
                "probability_analysis": {
                    "model_probability": 75,
                    "implied_probability": 70,
                    "value_edge": 5
                },
                "kelly_suggestion": {
                    "half_kelly": 0.06,
                    "recommended_stake": "总资金的6%"
                },
                "risk_warning": "需关注临场赔率变化"
            }
        }
    }
}
```

**错误码(免费次数用完)**
```json
{
    "success": false,
    "error": {
        "code": "FREE_LIMIT_EXCEEDED",
        "message": "今日免费查看次数已用完(3次)",
        "details": {
            "remaining": 0,
            "reset_at": "2026-05-11T00:00:00Z",
            "upgrade_url": "/subscribe"
        }
    }
}
```

---

### 4.3 批量获取预测(付费专属)

```http
POST /predictions/batch
```

**权限**: 仅付费用户

**请求体**
```json
{
    "match_ids": ["match_001", "match_002", "match_003"]
}
```

**响应**
```json
{
    "success": true,
    "data": [
        { "match_id": "match_001", "analysis": { "l3": {...} } },
        { "match_id": "match_002", "analysis": { "l3": {...} } },
        { "match_id": "match_003", "analysis": { "l3": {...} } }
    ]
}
```

---

## 五、组合投注接口(付费专属)

### 5.1 生成组合投注建议

```http
POST /combo/generate
```

**权限**: 仅付费用户

**请求体**
```json
{
    "matches": [
        {
            "match_id": "match_001",
            "bet_type": "home_win",
            "odds": 1.42
        },
        {
            "match_id": "match_002",
            "bet_type": "home_win",
            "odds": 1.85
        },
        {
            "match_id": "match_003",
            "bet_type": "draw",
            "odds": 3.20
        }
    ],
    "total_budget": 1000,
    "risk_preference": "half"  // full | half
}
```

**响应**
```json
{
    "success": true,
    "data": {
        "id": "combo_001",
        "kelly_allocation": [
            {
                "match_id": "match_001",
                "bet_type": "home_win",
                "odds": 1.42,
                "model_prob": 75,
                "kelly_ratio": 0.12,
                "half_kelly": 0.06,
                "recommended_amount": 60
            },
            {
                "match_id": "match_002",
                "bet_type": "home_win",
                "odds": 1.85,
                "model_prob": 60,
                "kelly_ratio": 0.08,
                "half_kelly": 0.04,
                "recommended_amount": 40
            },
            {
                "match_id": "match_003",
                "bet_type": "draw",
                "odds": 3.20,
                "model_prob": 35,
                "kelly_ratio": 0.03,
                "half_kelly": 0.015,
                "recommended_amount": 15
            }
        ],
        "parlay_suggestions": [
            {
                "type": "double",
                "matches": ["match_001", "match_002"],
                "combined_odds": 2.64,
                "win_probability": 45,
                "recommended_stake": 50,
                "potential_return": 132,
                "risk_level": "low"
            },
            {
                "type": "treble",
                "matches": ["match_001", "match_002", "match_003"],
                "combined_odds": 8.45,
                "win_probability": 15,
                "recommended_stake": 30,
                "potential_return": 253,
                "risk_level": "medium"
            }
        ],
        "recommended_parlay": {
            "type": "double",
            "matches": ["match_001", "match_002"],
            "reason": "两场置信度较高，串关风险可控"
        },
        "risk_score": 35,
        "expected_roi": 8.5,
        "summary": "建议单注分散投注或选择双串关"
    }
}
```

---

## 六、赔率变动分析接口(付费专属)

### 6.1 获取赔率变动分析

```http
GET /odds-movement/:match_id
```

**权限**: 仅付费用户

**响应**
```json
{
    "success": true,
    "data": {
        "match_id": "match_001",
        "movements": [
            {
                "bookmaker": "bet365",
                "odds_type": "match_winner",
                "history": [
                    {"odds": 1.35, "time": "2026-05-07T00:00:00Z"},
                    {"odds": 1.42, "time": "2026-05-09T12:00:00Z"},
                    {"odds": 1.45, "time": "2026-05-10T08:00:00Z"}
                ],
                "change_from_opening": "+7%",
                "movement_direction": "up"
            }
        ],
        "analysis": {
            "possible_reasons": [
                {
                    "reason": "资金流向",
                    "description": "主队投注量增加35%",
                    "confidence": "高"
                },
                {
                    "reason": "伤病影响",
                    "description": "客队主力后卫复出",
                    "confidence": "中"
                }
            ],
            "news_articles": [
                {
                    "source": "ESPN",
                    "title": "布伦特福德后卫复出",
                    "title_cn": "布伦特福德主力后卫本周末复出",
                    "summary_cn": "布伦特福德主力后卫Pinnock伤愈复出，预计本轮首发...",
                    "published_at": "2026-05-09T10:00:00Z",
                    "importance": 4
                }
            ],
            "ai_analysis": {
                "summary": "赔率上升7%可能与客队主力后卫复出消息有关，博彩公司可能调整赔率吸引主队投注",
                "bookmaker_intent": "Bet365可能希望增加主队投注量以平衡账面",
                "betting_insight": "如果临场赔率继续上升，需警惕诱导；如果下降，说明资金确实流入"
            },
            "risk_warning": "赔率变动较大，建议临场确认后再投注"
        }
    }
}
```

---

## 七、投注追踪接口(付费专属)

### 7.1 添加投注记录

```http
POST /tracker/records
```

**权限**: 仅付费用户

**请求体**
```json
{
    "match_id": "match_001",
    "bookmaker": "bet365",
    "bet_type": "home_win",
    "bet_amount": 100,
    "odds": 1.42,
    "note": "跟推荐"
}
```

**响应**
```json
{
    "success": true,
    "data": {
        "id": "record_001",
        "match_id": "match_001",
        "bet_amount": 100,
        "odds": 1.42,
        "potential_return": 142,
        "result": "pending",
        "created_at": "2026-05-10T12:00:00Z"
    }
}
```

---

### 7.2 获取投注记录列表

```http
GET /tracker/records
```

**查询参数**
| 参数 | 类型 | 说明 |
|------|------|------|
| result | string | pending/win/lose(可选) |
| start_date | string | 开始日期(可选) |
| end_date | string | 结束日期(可选) |
| page | int | 页码 |

**响应**
```json
{
    "success": true,
    "data": [
        {
            "id": "record_001",
            "match": {"home_team": "曼城", "away_team": "布伦特福德"},
            "bet_type": "home_win",
            "bet_amount": 100,
            "odds": 1.42,
            "result": "win",
            "profit": 42,
            "created_at": "2026-05-10T12:00:00Z"
        }
    ],
    "pagination": { ... }
}
```

---

### 7.3 更新投注结果

```http
PUT /tracker/records/:record_id
```

**请求体**
```json
{
    "result": "win",
    "actual_result": "home_win",
    "profit": 42
}
```

---

### 7.4 获取统计报告

```http
GET /tracker/statistics
```

**响应**
```json
{
    "success": true,
    "data": {
        "summary": {
            "total_bets": 50,
            "win_count": 35,
            "lose_count": 15,
            "win_rate": 70,
            "total_investment": 5000,
            "total_return": 6500,
            "profit": 1500,
            "roi": 30
        },
        "monthly_stats": [
            {
                "month": "2026-04",
                "bets": 20,
                "win_rate": 65,
                "roi": 15
            },
            {
                "month": "2026-05",
                "bets": 30,
                "win_rate": 75,
                "roi": 40
            }
        ],
        "league_stats": [
            {
                "league": "英超",
                "bets": 25,
                "win_rate": 72,
                "roi": 35
            },
            {
                "league": "中超",
                "bets": 15,
                "win_rate": 65,
                "roi": 20
            }
        ],
        "best_bet": {
            "match": "曼城 vs 阿森纳",
            "profit": 200
        },
        "worst_bet": {
            "match": "利物浦 vs 切尔西",
            "loss": -100
        }
    }
}
```

---

## 八、订阅接口

### 8.1 获取订阅计划

```http
GET /subscribe/plans
```

**响应**
```json
{
    "success": true,
    "data": [
        {
            "id": "premium_monthly",
            "name": "月度会员",
            "price": 99,
            "currency": "CNY",
            "duration": 30,
            "features": [
                "无限制查看所有预测",
                "组合投注建议",
                "赔率变动AI分析",
                "投注追踪系统"
            ]
        },
        {
            "id": "premium_quarterly",
            "name": "季度会员",
            "price": 269,
            "currency": "CNY",
            "duration": 90,
            "discount": "省28元"
        },
        {
            "id": "premium_yearly",
            "name": "年度会员",
            "price": 899,
            "currency": "CNY",
            "duration": 365,
            "discount": "省189元"
        }
    ]
}
```

---

### 8.2 创建订阅订单

```http
POST /subscribe/orders
```

**请求体**
```json
{
    "plan_id": "premium_monthly",
    "payment_method": "alipay"  // alipay | wechat
}
```

**响应**
```json
{
    "success": true,
    "data": {
        "order_id": "order_001",
        "plan_id": "premium_monthly",
        "amount": 99,
        "payment_method": "alipay",
        "payment_url": "https://alipay.com/...",
        "qr_code": "base64_qr_code",
        "expire_at": "2026-05-10T12:30:00Z"
    }
}
```

---

### 8.3 验证支付结果

```http
POST /subscribe/verify
```

**请求体**
```json
{
    "order_id": "order_001"
}
```

**响应(支付成功)**
```json
{
    "success": true,
    "data": {
        "order_id": "order_001",
        "payment_status": "success",
        "user_role": "premium",
        "premium_expire_at": "2026-06-10T12:00:00Z"
    }
}
```

---

## 九、教育内容接口

### 9.1 获取教育课程列表

```http
GET /learn/courses
```

**响应**
```json
{
    "success": true,
    "data": [
        {
            "id": "course_001",
            "title": "博彩基础入门",
            "description": "了解赔率类型、盘口解读",
            "lessons": 5,
            "duration": "30分钟",
            "level": "beginner"
        },
        {
            "id": "course_002",
            "title": "Kelly Criterion详解",
            "description": "如何科学分配投注资金",
            "lessons": 3,
            "duration": "20分钟",
            "level": "intermediate"
        }
    ]
}
```

---

### 9.2 获取课程详情

```http
GET /learn/courses/:course_id
```

**响应**
```json
{
    "success": true,
    "data": {
        "id": "course_001",
        "title": "博彩基础入门",
        "lessons": [
            {
                "id": "lesson_001",
                "title": "什么是赔率",
                "content_type": "text",
                "content": "赔率是博彩公司对比赛结果的概率评估...",
                "examples": [
                    {"title": "示例1", "content": "..."}
                ]
            },
            {
                "id": "lesson_002",
                "title": "隐含概率计算",
                "content_type": "interactive",
                "content": "隐含概率 = 1 / 赔率...",
                "calculator": {
                    "input": "odds",
                    "output": "probability"
                }
            }
        ]
    }
}
```

---

## 十、错误码汇总

| code | HTTP状态 | 说明 |
|------|----------|------|
| UNAUTHORIZED | 401 | 未登录/Token无效 |
| FORBIDDEN | 403 | 无权限访问 |
| FREE_LIMIT_EXCEEDED | 403 | 免费次数已用完 |
| PREMIUM_REQUIRED | 403 | 需付费会员权限 |
| NOT_FOUND | 404 | 资源不存在 |
| INVALID_INPUT | 400 | 输入参数错误 |
| RATE_LIMITED | 429 | API调用频率超限 |
| INTERNAL_ERROR | 500 | 内部错误 |

---

## 十一、API调用限制

| 接口类型 | 限制 |
|----------|------|
| 认证接口 | 10次/分钟 |
| 数据查询 | 100次/分钟 |
| 预测请求 | 50次/分钟 |
| 组合投注 | 20次/分钟 |

---

## 十二、API版本管理

```
/v1 - 当前稳定版本
/v2 - 未来版本(开发中)
```

版本升级策略：
- 向后兼容的改动在v1中更新
- 不兼容的改动发布新版本v2
- v1至少维护6个月