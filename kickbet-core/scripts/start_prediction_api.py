"""
KickBet 预计算系统启动脚本

功能:
- 初始化数据库
- 启动Flask API服务
- 注册缓存API
- 提供测试端点

使用:
  python scripts/start_prediction_api.py
"""

import os
import sys
import logging
from datetime import datetime

# 设置路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify
from flask_cors import CORS

from database.models import PredictionCacheManager
from api.cache_api import register_cache_api, get_db_manager

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    CORS(app)
    
    # 配置
    app.config['JSON_AS_ASCII'] = False  # 支持中文
    
    # 初始化数据库
    db = get_db_manager()
    db.init_db()
    
    # 注册API蓝图
    register_cache_api(app)
    
    # 添加根路由
    @app.route('/')
    def index():
        return jsonify({
            'name': 'KickBet Prediction Cache API',
            'version': 'v0.2.0',
            'status': 'running',
            'timestamp': datetime.utcnow().isoformat(),
            'endpoints': {
                'matches': '/api/cache/matches',
                'match_detail': '/api/cache/matches/<match_id>',
                'prediction': '/api/cache/predictions/<match_id>',
                'predictions_batch': '/api/cache/predictions/batch',
                'odds': '/api/cache/odds/<match_id>',
                'status': '/api/cache/status'
            }
        })
    
    # 添加健康检查
    @app.route('/health')
    def health():
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    return app


def main():
    """启动服务"""
    logger.info("="*60)
    logger.info("KickBet 预计算缓存API服务")
    logger.info("="*60)
    
    app = create_app()
    
    # 显示缓存状态
    db = get_db_manager()
    session = db.get_session()
    
    from database.models import MatchCache, SystemPrediction, TeamStatsCache
    matches_count = session.query(MatchCache).count()
    predictions_count = session.query(SystemPrediction).filter(SystemPrediction.is_current == True).count()
    stats_count = session.query(TeamStatsCache).count()
    
    db.close_session(session)
    
    logger.info(f"缓存状态:")
    logger.info(f"  - 比赛: {matches_count} 场")
    logger.info(f"  - 预测: {predictions_count} 个")
    logger.info(f"  - 球队统计: {stats_count} 个")
    
    logger.info("\n启动API服务 (端口5001)...")
    logger.info("测试端点: http://localhost:5001/api/cache/status")
    
    app.run(host='0.0.0.0', port=5001, debug=True)


if __name__ == "__main__":
    main()