# KickBet Core - 版本规划

## 当前版本: v0.1.0 (main)

### 模块状态

| 模块 | 状态 | 分支 | 优先级 |
|------|------|------|--------|
| collectors (数据采集) | 基本完成 | feature/collector-enhance | P2 |
| predictors (预测引擎) | 基本完成 | feature/predictor-enhance | P1 |
| database (数据库) | 完成 | - | - |
| security (认证) | 完成 | - | - |
| services (核心服务) | 基本完成 | - | - |
| frontend (前端界面) | 未开始 | feature/frontend | P3 |
| combo-system (组合推荐) | 未开始 | feature/combo-system | P4 |

### 版本规划

**v0.2.0** - 预测引擎增强
- Poisson模型验证和优化
- 添加更多联赛支持
- Kelly Criterion优化

**v0.3.0** - 数据采集增强
- Odds-API双Key轮换机制
- 实时赔率更新
- 更多博彩公司数据

**v0.4.0** - 前端界面
- 移动端优先设计
- Linear Minimal Dark风格
- 4个核心页面

**v0.5.0** - 组合推荐系统
- 多场组合分析
- 风险评估
- 收益优化

### Git分支策略

```
main (稳定发布版本)
  │
  └── develop (开发主线)
        │
        ├── feature/collector-enhance
        ├── feature/predictor-enhance
        ├── feature/frontend
        └── feature/combo-system
```

### API Keys配置

- Odds-API.io: 2个Key轮换 (200次/小时)
- Football-Data.org: 1个Key (10次/分钟)