#!/bin/bash
# KickBet Flask API 启动脚本

echo "========================================"
echo "KickBet Flask API 启动"
echo "========================================"

# 检查Python环境
echo "检查Python环境..."

# 尝试创建虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv || {
        echo "虚拟环境创建失败，尝试系统安装..."
        pip install --break-system-packages flask flask-cors requests pyyaml
    }
fi

# 激活虚拟环境（如果存在）
if [ -d "venv" ]; then
    echo "激活虚拟环境..."
    source venv/bin/activate
    pip install flask flask-cors requests pyyaml -q
fi

# 启动API
echo "启动Flask API..."
echo ""
echo "API端点:"
echo "  GET /api/health         - 健康检查"
echo "  GET /api/leagues        - 联赛列表"
echo "  GET /api/matches        - 比赛列表"
echo "  GET /api/match/<id>     - 比赛详情"
echo "  GET /api/analysis/<id>  - 比赛分析"
echo "  GET /api/standings/<league> - 积分榜"
echo "  GET /api/odds/<league>  - 赔率数据"
echo "  GET /api/daily          - 今日分析汇总"
echo ""
echo "端口: 5000"
echo "========================================"

python app.py