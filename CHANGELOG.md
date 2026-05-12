# KickBet 版本历史

## v0.1.0 - 初始版本 (2026-05-13)

### 已完成功能

**后端 API (kickbet-core)**
- ✅ 数据采集模块
  - Football-Data.org 集成 (比赛数据、积分榜)
  - Odds-API.io 双Key轮换 (赔率数据，200次/小时)
- ✅ 预测引擎
  - Poisson 模型概率预测
  - Kelly Criterion 价值评估
  - 最可能比分计算
- ✅ API端点
  - `/api/health` - 健康检查
  - `/api/matches` - 比赛列表
  - `/api/analysis/<id>` - 单场完整分析
  - `/api/standings/<league>` - 积分榜
  - `/api/odds/<league>` - 赔率数据
- ✅ 认证系统 (JWT)

**前端 UI (kickbet-web)**
- ✅ Vue3 + TailwindCSS 框架
- ✅ 6个核心页面结构
  - Home (首页推荐)
  - Matches (比赛列表)
  - MatchDetail (比赛详情+投注方案)
  - Combo (组合投注)
  - Tracker (投注追踪)
  - Subscribe (会员订阅)
- ✅ Linear Minimal Dark 设计风格
- ✅ 移动端优先布局
- ✅ API集成框架 (axios + 类型定义)

**UI原型**
- ✅ 6个静态HTML原型页面

### 测试验证
- ✅ 后端API功能测试通过
- ✅ 数据采集模块测试通过
- ✅ 预测模块测试通过
- ✅ 示例预测: 曼城vs水晶宫
  - 主胜 61.4% / 平 21.7% / 客 17.0%
  - 预期比分 2-0
  - 大2.5球 53.2%

---

## 下一版本规划

### v0.2.0 - 前端API集成
- MatchDetail 页面接入真实API数据
- Auth 登录/注册功能
- Tracker 用户追踪记录
- Combo 组合推荐逻辑

### v0.3.0 - 功能增强
- 实时赔率更新
- 更多联赛支持
- 用户偏好设置

### v0.4.0 - 生产部署
- Cloudflare部署
- 数据库持久化
- 性能优化

---

## 版本管理策略

```
main (生产稳定版本)
  │
  └── develop (开发主线)
        │
        ├── feature/frontend-api
        ├── feature/auth-system
        └── feature/combo-system
```

**发布流程:**
1. 在 develop 分支开发新功能
2. 测试验证后合并到 main
3. 创建版本 tag (v0.x.0)
4. 推送到 GitHub