# Phase 1: 基础架构层 - 任务清单

> 状态：细化完成，待开发

---

## 一、细化文档（已完成）

| 文档 | 状态 | 说明 |
|-----|------|------|
| KickBet数据库设计.md | 完成 | SQLite表结构、索引、视图定义 |
| KickBet-API设计.md | 完成 | RESTful接口规范、请求/响应格式 |
| KickBet项目目录结构设计.md | 完成 | 后端/前端/引擎模块划分 |

---

## 二、开发任务

### 2.1 后端骨架（预估2天）

| 任务 | 状态 | 文件 |
|-----|------|------|
| Flask应用初始化 | 待开发 | backend/app/__init__.py |
| 配置管理 | 待开发 | backend/app/config.py |
| Flask扩展初始化 | 待开发 | backend/app/extensions.py |
| 路由框架 | 待开发 | backend/app/routes/__init__.py |
| 响应格式化工具 | 待开发 | backend/app/utils/response.py |
| 启动脚本 | 待开发 | backend/run.py |
| requirements.txt | 待开发 | backend/requirements.txt |

### 2.2 数据库初始化（预估1天）

| 任务 | 状态 | 文件 |
|-----|------|------|
| 用户数据库脚本 | 待开发 | backend/scripts/init_users_db.py |
| 预测数据库脚本 | 待开发 | backend/scripts/init_predictions_db.py |
| 新闻数据库脚本 | 待开发 | backend/scripts/init_news_db.py |
| 联赛数据初始化 | 待开发 | backend/scripts/seed_leagues.py |

### 2.3 前端骨架（预估2天）

| 任务 | 状态 | 文件 |
|-----|------|------|
| Vue项目初始化 | 待开发 | frontend/ (vite init) |
| 路由配置 | 待开发 | frontend/src/router/index.js |
| CSS变量定义 | 待开发 | frontend/src/styles/variables.css |
| 全局样式 | 待开发 | frontend/src/styles/global.css |
| Axios配置 | 待开发 | frontend/src/api/index.js |
| Pinia状态管理 | 待开发 | frontend/src/store/index.js |
| 通用组件骨架 | 待开发 | frontend/src/components/common/ |

---

## 三、验证点

完成后应达到：

1. **后端验证**
   - `python backend/run.py` 启动成功
   - `curl http://localhost:5000/api/v1/health` 返回 `{success: true}`
   - 数据库文件创建成功

2. **前端验证**
   - `npm run dev` 启动成功
   - 浏览器访问显示空白页面（路由框架正常）
   - CSS变量生效（背景色#08090a）

---

## 四、下一步

完成Phase 1后，进入 **Phase 2: 用户系统 + 权限控制**

---

## 五、技术选型确认

| 层级 | 技术 | 版本 |
|-----|------|------|
| 后端框架 | Flask | 3.x |
| 前端框架 | Vue.js | 3.x |
| 前端构建 | Vite | 5.x |
| 状态管理 | Pinia | 2.x |
| HTTP客户端 | Axios | 1.x |
| 数据库 | SQLite | 3.x |

---

## 六、依赖清单

### backend/requirements.txt

```
flask>=3.0.0
flask-cors>=4.0.0
flask-jwt-extended>=4.6.0
python-dotenv>=1.0.0
requests>=2.31.0
numpy>=1.26.0
bcrypt>=4.1.0
pyyaml>=6.0
schedule>=1.2.0
redis>=5.0.0
openai>=1.0.0  # AI新闻分析
```

### frontend/package.json (核心依赖)

```json
{
  "dependencies": {
    "vue": "^3.4.0",
    "vue-router": "^4.2.0",
    "pinia": "^2.1.0",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "vite": "^5.0.0",
    "@vitejs/plugin-vue": "^5.0.0",
    "vite-plugin-pwa": "^0.19.0"
  }
}
```