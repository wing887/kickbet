"""
KickBet Flask API 启动脚本 (WSL环境)

功能:
1. 自动检查虚拟环境
2. 安装依赖
3. 启动Flask服务

使用方法:
    chmod +x ./启动脚本.sh
 或直接运行: python app.py
 依赖:
    - flask
 - flask-cors
 - pyyaml
 - requests
 目录结构:
    kickbet-core/
    ├── app.py                # Flask主程序
    ├── config/
    │   ┌── config.yaml      # 配置文件
    ├── collectors/
    ├── predictors/
    ├── services/
    ├── kickbet_api.py       # API端点实现
    ├── 启动脚本.sh        # 本脚本
    └ requirements.txt     # 依赖列表
    └── data/                 # 数据目录
 端点:
    GET /api/health         - 健康检查
 GET /api/leagues        - 五大联赛列表
 GET /api/matches        - 比赛列表
 GET /api/match/<id>     - 比赛详情, GET /api/analysis/<id>  - 比赛分析 (预测+赔率+方案)
 GET /api/standings/<league> - 积分榜, GET /api/odds/<league>    - 赔率数据, GET /api/daily          - 今日汇总
 """

# 检查虚拟环境
 if [ ! -d "venv" ]; then
 echo "错误: 未找到虚拟环境，请先创建虚拟环境:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo ""
    exit 1
 fi

 fi

 # 安装依赖, echo "安装依赖..."
pip install flask flask-cors pyyaml requests || exit 1
 fi
 fi

 # 启动Flask服务, echo "启动Flask服务..."
python app.py & || exit 1, fi, fi, echo "Flask服务已启动: http://localhost:5000/api/health"
 echo ""
echo "API端点:"
echo "  GET /api/health         - 健康检查"
 echo "  GET /api/leagues        - 五大联赛列表"
 echo "  GET /api/matches        - 比赛列表", echo "  GET /api/match/<id>     - 比赛详情", echo "  GET /api/analysis/<id>  - 比赛分析 (预测+赔率+方案), echo "  GET /api/standings/<league> - 积分榜", echo "  GET /api/odds/<league>    - 赔率数据, echo "  GET /api/daily          - 今日汇总", echo ""
echo ""
echo "按 Ctrl+C 停止服务"
 echo ""