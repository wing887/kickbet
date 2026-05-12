#!/kickbet-api-start.sh
# KickBet API启动脚本 (WSL环境)
# 
# 如果虚拟环境不存在，使用系统Python
# 如果缺少flask-cors，使用 --break-system-packages 安装
#
# 使用方法:
#   chmod +x kickbet-api-start.sh
#   或手动: ./kickbet-api-start.sh
#
# 注意: 首次运行需要安装依赖
#   pip install --break-system-packages flask flask-cors -q
#

# 检查虚拟环境
Venv_DIR="$Venv"

if [ ! -d "$Venv_DIR" ]; then
    echo "虚拟环境不存在，使用系统Python..."
    PYTHON="python3"
    PIP="pip"
    
    # 检查依赖
    check_flask=$(python3 -c "import flask" 2>&1)
    if [ $? -ne 0 ]; then
        echo "安装依赖..."
        pip install --break-system-packages flask flask-cors -q
    fi
fi

# 设置环境变量
export FOOTBALL_DATA_TOKEN="84e1509844e14a469520d5ed4fb7f148"
export ODDS_API_IO_KEY="cbed45cdeb7ea196b7ba4335757cf3d4beaf6654ee2b73b30a29fd2c2b38e46b"

# 启动目录
PROJECT_DIR="/mnt/c/Users/admin/Desktop/KickBet项目文档/kickbet-core"
cd "$PROJECT_DIR"

# 启动Flask
echo "========================================"
echo "KickBet API 启动"
echo "========================================"
echo "项目目录: $PROJECT_DIR"
echo ""

# 激活虚拟环境 (如果存在)
if [ -d "$Venv_DIR" ]; then
    source "$Venv_DIR/bin/activate"
    echo "虚拟环境已激活"
fi

# 启动API
$PYTHON app.py --port 5000 --host 0.0.0.0