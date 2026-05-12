# KickBet API 启动说明

# ================================

# 环境准备
# ================================
# 1. 安装依赖 (需要sudo或虚拟环境)
#    方式A: 使用虚拟环境 (推荐)
#        cd /mnt/c/Users/admin/Desktop/KickBet项目文档/kickbet-core
#        sudo apt install python3.12-venv  # 安装venv支持
#        python3 -m venv venv
#        source venv/bin/activate
#        pip install flask flask-cors requests pyyaml
#    
#    方式B: 使用 --break-system-packages (不推荐，可能影响系统)
#        pip install --break-system-packages flask flask-cors requests pyyaml
#    
# ================================
# 启动API
# ================================
# 2. 启动Flask服务器
#    cd /mnt/c/Users/admin/Desktop/KickBet项目文档/kickbet-core
#    python app.py
#    
#    或指定端口:
#        python app.py --port 8000
#    
# ================================
# 测试API
# ================================
# 3. 测试端点 (浏览器或curl)
#    curl http://localhost:5000/api/health
#    curl http://localhost:5000/api/leagues
#    curl http://localhost:5000/api/matches?days=3
#    curl http://localhost:5000/api/standings/PL
#    curl http://localhost:5000/api/daily
#    
# ================================
# API端点列表
# ================================
# GET /api/health         - 健康检查
# GET /api/leagues        - 五大联赛列表
# GET /api/matches        - 比赛列表 (?days=3, ?league=PL)
# GET /api/match/<id>     - 单场比赛详情
# GET /api/analysis/<id>  - 比赛完整分析 (预测+赔率+方案)
# GET /api/standings/<league> - 联赛积分榜
# GET /api/odds/<league>  - 赔率数据
# GET /api/daily          - 今日分析汇总
#    
# ================================
# 项目结构
# ================================
# kickbet-core/
# ├── app.py              # Flask API主文件
# ├── config/
# │   └── config.yaml     # 配置文件
# ├── collectors/
# │   ├── football_data_org.py
# │   └ odds_api_io.py
# ├── predictors/
# │   └── poisson_predictor.py
# ├── services/
# │   └ kickbet_core.py
# ├── data/
# │   └ e2e_test_result.json
# ├── test_e2e.py         # 端到端测试
# └── requirements.txt    # 依赖列表