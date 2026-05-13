"""
KickBet 预计算缓存 API

功能:
- 获取比赛列表 (带预测缓存)
- 获取单场比赛预测
- 批量获取预测结果
- 获取赔率历史
- 手动刷新预测 (管理员)

设计:
- 前端直接读取缓存，无需实时计算
- 预测结果已预计算，响应速度 <50ms
- Kelly计算在前端完成

安全注意事项 (v0.3待完善):
- 当前无认证机制，数据公开暴露
- 建议生产环境添加: API Key认证 + 速率限制 + 用户登录
- 手动刷新接口应限制管理员权限
"""

from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import time
from functools import wraps

from database.models import PredictionCacheManager, MatchCache, SystemPrediction, OddsHistory


# ==================== 简易速率限制 (v0.3待完善为完整方案) ====================

# 内存级速率限制 (单进程有效)
_rate_limit_store: Dict[str, List[float]] = {}
RATE_LIMIT_PER_MINUTE = 60  # 每IP每分钟60次
RATE_LIMIT_WINDOW = 60  # 60秒窗口


def rate_limit(f):
    """简易速率限制装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 获取客户端IP (注意: 代理环境可能不准确)
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        
        if client_ip:
            now = time.time()
            # 获取该IP的请求记录
            requests = _rate_limit_store.get(client_ip, [])
            
            # 清理过期记录
            requests = [t for t in requests if now - t < RATE_LIMIT_WINDOW]
            
            # 检查是否超限
            if len(requests) >= RATE_LIMIT_PER_MINUTE:
                logger.warning(f"[RateLimit] IP {client_ip} 请求超限")
                return jsonify({
                    'success': False,
                    'error': '请求过于频繁，请稍后再试',
                    'retry_after': RATE_LIMIT_WINDOW
                }), 429
            
            # 记录本次请求
            requests.append(now)
            _rate_limit_store[client_ip] = requests
        
        return f(*args, **kwargs)
    return decorated_function

logger = logging.getLogger(__name__)

# 创建蓝图
cache_api = Blueprint('cache_api', __name__, url_prefix='/api/cache')

# 数据库管理器实例 (懒加载)
_db_manager: Optional[PredictionCacheManager] = None


def get_db_manager() -> PredictionCacheManager:
    """获取数据库管理器实例"""
    global _db_manager
    if _db_manager is None:
        _db_manager = PredictionCacheManager()
        _db_manager.init_db()
    return _db_manager


# ==================== 比赛列表 API ====================

@cache_api.route('/matches', methods=['GET'])
@rate_limit
def get_matches():
    """
    获取比赛列表
    
    Query参数:
        league: 联赛代码 (PL/BL1/PD/SA/FL1), 可选
        hours: 未来N小时内的比赛, 默认72
        with_prediction: 是否包含预测数据, 默认true
    
    返回:
        matches: 比赛列表
        total: 总数
        cached_count: 有缓存预测的数量
    """
    try:
        db = get_db_manager()
        
        # 解析参数
        league = request.args.get('league', None)
        hours = int(request.args.get('hours', 72))
        with_prediction = request.args.get('with_prediction', 'true').lower() == 'true'
        
        # 获取比赛
        matches = db.get_upcoming_matches(hours=hours, league=league)
        
        # 构建响应
        match_list = []
        cached_count = 0
        
        if with_prediction:
            # 批量获取预测
            match_ids = [m.match_id for m in matches]
            predictions = db.get_predictions_for_matches(match_ids)
            
            for match in matches:
                match_data = match.to_dict()
                
                # 添加预测数据
                if match.match_id in predictions:
                    pred = predictions[match.match_id]
                    match_data['prediction'] = pred.to_dict()
                    match_data['has_prediction'] = True
                    cached_count += 1
                else:
                    match_data['prediction'] = None
                    match_data['has_prediction'] = False
                
                match_list.append(match_data)
        else:
            match_list = [m.to_dict() for m in matches]
        
        return jsonify({
            'success': True,
            'matches': match_list,
            'total': len(match_list),
            'cached_count': cached_count,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"[API] 获取比赛列表失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'matches': []
        }), 500


@cache_api.route('/matches/<match_id>', methods=['GET'])
@rate_limit
def get_match_detail(match_id: str):
    """
    获取单场比赛详情
    
    返回:
        match: 比赛信息
        prediction: 当前预测 (is_current=true)
        odds_history: 最近赔率历史 (10条)
        odds_change_detected: 是否有显著赔率变化
    """
    try:
        db = get_db_manager()
        
        # 获取比赛
        match = db.get_match_by_id(match_id)
        
        if not match:
            return jsonify({
                'success': False,
                'error': '比赛不存在',
                'match_id': match_id
            }), 404
        
        # 获取预测
        prediction = db.get_current_prediction(match_id)
        
        # 获取赔率历史
        odds_history = db.get_odds_history(match_id, limit=10)
        
        # 构建响应
        response = {
            'success': True,
            'match': match.to_dict(),
            'prediction': prediction.get_full_data() if prediction else None,
            'has_prediction': prediction is not None,
            'prediction_version': prediction.prediction_version if prediction else None,
            'odds_history': [o.to_dict() for o in odds_history],
            'odds_history_count': len(odds_history),
            'latest_odds': odds_history[0].to_dict() if odds_history else None,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # 检查赔率变化
        if odds_history:
            latest = odds_history[0]
            response['odds_change_detected'] = latest.change_detected
            response['significant_odds_change'] = latest.significant_change
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"[API] 获取比赛详情失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== 预测缓存 API ====================

@cache_api.route('/predictions/<match_id>', methods=['GET'])
@rate_limit
def get_prediction(match_id: str):
    """
    获取单场比赛预测
    
    返回预计算的预测结果，无需实时计算
    
    Query参数:
        full: 是否返回完整数据 (含score_distribution), 默认false
    
    返回:
        prediction: 预测数据
        version: 版本号
        trigger_reason: 触发原因
        created_at: 创建时间
    """
    try:
        db = get_db_manager()
        
        # 获取预测
        prediction = db.get_current_prediction(match_id)
        
        if not prediction:
            return jsonify({
                'success': False,
                'error': '预测不存在',
                'match_id': match_id,
                'message': '比赛可能尚未开始预测，请稍后再试'
            }), 404
        
        # 解析参数
        full = request.args.get('full', 'false').lower() == 'true'
        
        if full:
            data = prediction.get_full_data()
        else:
            data = prediction.to_dict()
        
        return jsonify({
            'success': True,
            'match_id': match_id,
            'prediction': data,
            'version': prediction.prediction_version,
            'trigger_reason': prediction.trigger_reason,
            'created_at': prediction.created_at.isoformat(),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"[API] 获取预测失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@cache_api.route('/predictions/live', methods=['POST'])
@rate_limit
def predict_live_with_h2h():
    """
    实时预测比赛 (包含H2H历史交锋数据)
    
    Body:
        match_id: 比赛ID
        home_team: 主队名称
        away_team: 客队名称  
        home_team_id: 主队ID (历史数据库)
        away_team_id: 客队ID (历史数据库)
        h2h_weight: H2H权重 (0-0.5, 默认0.25)
    
    返回:
        poisson_prediction: Poisson模型预测
        h2h_stats: 历史交锋统计
        combined_prediction: 综合预测结果
    """
    try:
        from database.history_models import HistoryDBManager, Team
        from predictors.poisson_predictor import PoissonPredictor
        
        data = request.get_json()
        
        match_id = data.get('match_id')
        home_team = data.get('home_team')
        away_team = data.get('away_team')
        home_team_id = data.get('home_team_id')
        away_team_id = data.get('away_team_id')
        h2h_weight = data.get('h2h_weight', 0.25)
        
        if not all([match_id, home_team, away_team, home_team_id, away_team_id]):
            return jsonify({
                'success': False,
                'error': '缺少必要参数: match_id, home_team, away_team, home_team_id, away_team_id'
            }), 400
        
        # 初始化
        history_db = HistoryDBManager()
        predictor = PoissonPredictor()
        predictor.load_stats_from_history_db(history_db)
        
        # 获取H2H统计
        h2h_stats = history_db.get_head_to_head_stats(home_team_id, away_team_id, limit=10)
        
        # 执行预测
        pred = predictor.predict_match_with_h2h(
            match_id=match_id,
            home_team=home_team,
            away_team=away_team,
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            h2h_stats=h2h_stats,
            h2h_weight=h2h_weight
        )
        
        # 构建响应
        response = {
            'success': True,
            'match_id': match_id,
            'home_team': home_team,
            'away_team': away_team,
            'poisson_prediction': {
                'prob_home': pred.prob_home,
                'prob_draw': pred.prob_draw,
                'prob_away': pred.prob_away,
                'expected_home_goals': pred.expected_home_goals,
                'expected_away_goals': pred.expected_away_goals,
                'most_likely_score': pred.most_likely_score
            },
            'h2h_stats': {
                'total_matches': h2h_stats.get('total_matches', 0),
                'home_wins': h2h_stats.get('team_a_wins', 0),
                'away_wins': h2h_stats.get('team_b_wins', 0),
                'draws': h2h_stats.get('draws', 0),
                'home_win_rate': h2h_stats.get('team_a_win_rate', 0),
                'away_win_rate': h2h_stats.get('team_b_win_rate', 0),
                'draw_rate': h2h_stats.get('draw_rate', 0),
                'avg_total_goals': h2h_stats.get('avg_total_goals', 0),
                'recent_results': h2h_stats.get('recent_results', [])
            },
            'combined_prediction': {
                'prob_home': pred.combined_prob_home,
                'prob_draw': pred.combined_prob_draw,
                'prob_away': pred.combined_prob_away,
                'prediction': pred.prediction,
                'h2h_weight': h2h_weight
            },
            'has_h2h_data': pred.h2h_prediction is not None,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # 如果有H2H详细数据，添加到响应
        if pred.h2h_prediction:
            response['h2h_details'] = {
                'h2h_prob_home': pred.h2h_prediction.h2h_prob_home,
                'h2h_prob_draw': pred.h2h_prediction.h2h_prob_draw,
                'h2h_prob_away': pred.h2h_prediction.h2h_prob_away,
                'avg_home_goals': pred.h2h_prediction.avg_home_goals,
                'avg_away_goals': pred.h2h_prediction.avg_away_goals
            }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"[API] 实时预测失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@cache_api.route('/predictions/batch', methods=['POST'])
def get_predictions_batch():
    """
    批量获取预测
    
    Body:
        match_ids: 比赛ID列表 ["match_id_1", "match_id_2", ...]
    
    返回:
        predictions: {match_id: prediction_data}
        found_count: 找到预测的数量
        missing: 未找到预测的match_id列表
    """
    try:
        db = get_db_manager()
        
        # 解析请求
        data = request.get_json()
        match_ids = data.get('match_ids', [])
        
        if not match_ids:
            return jsonify({
                'success': False,
                'error': 'match_ids参数为空'
            }), 400
        
        # 批量获取
        predictions = db.get_predictions_for_matches(match_ids)
        
        # 构建响应
        result = {}
        missing = []
        
        for match_id in match_ids:
            if match_id in predictions:
                result[match_id] = predictions[match_id].to_dict()
            else:
                result[match_id] = None
                missing.append(match_id)
        
        return jsonify({
            'success': True,
            'predictions': result,
            'found_count': len(predictions),
            'missing_count': len(missing),
            'missing': missing,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"[API] 批量获取预测失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@cache_api.route('/predictions/<match_id>/history', methods=['GET'])
def get_prediction_history(match_id: str):
    """
    获取预测历史版本
    
    Query参数:
        limit: 返回版本数, 默认5
    
    返回:
        history: 预测版本列表 (最新在前)
        total: 总版本数
    """
    try:
        db = get_db_manager()
        
        limit = int(request.args.get('limit', 5))
        
        history = db.get_prediction_history(match_id, limit=limit)
        
        return jsonify({
            'success': True,
            'match_id': match_id,
            'history': [p.to_dict() for p in history],
            'total': len(history),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"[API] 获取预测历史失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== 赔率历史 API ====================

@cache_api.route('/odds/<match_id>', methods=['GET'])
def get_odds(match_id: str):
    """
    获取最新赔率
    
    Query参数:
        bookmaker: 指定博彩公司, 可选
    
    返回:
        odds: 最新赔率数据
        market_probs: 市场隐含概率
        change_detected: 是否有变化
        significant_change: 是否显著变化 (>5%)
    """
    try:
        db = get_db_manager()
        
        bookmaker = request.args.get('bookmaker', None)
        
        odds = db.get_latest_odds(match_id, bookmaker=bookmaker)
        
        if not odds:
            return jsonify({
                'success': False,
                'error': '赔率数据不存在',
                'match_id': match_id
            }), 404
        
        return jsonify({
            'success': True,
            'match_id': match_id,
            'odds': odds.to_dict(),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"[API] 获取赔率失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@cache_api.route('/odds/<match_id>/history', methods=['GET'])
def get_odds_history(match_id: str):
    """
    获取赔率历史
    
    Query参数:
        limit: 返回记录数, 默认20
    
    返回:
        history: 赔率历史列表
        change_summary: 变化统计
    """
    try:
        db = get_db_manager()
        
        limit = int(request.args.get('limit', 20))
        
        history = db.get_odds_history(match_id, limit=limit)
        
        # 统计变化
        change_count = sum(1 for o in history if o.change_detected)
        significant_count = sum(1 for o in history if o.significant_change)
        
        return jsonify({
            'success': True,
            'match_id': match_id,
            'history': [o.to_dict() for o in history],
            'total': len(history),
            'change_summary': {
                'changes_detected': change_count,
                'significant_changes': significant_count
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"[API] 获取赔率历史失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== 手动刷新 API (管理员) ====================

@cache_api.route('/predictions/<match_id>/refresh', methods=['POST'])
def refresh_prediction(match_id: str):
    """
    手动刷新预测
    
    需要: 管理员权限
    
    Body:
        reason: 刷新原因, 可选
    
    返回:
        prediction: 新预测数据
        version: 新版本号
    """
    try:
        # TODO: 添加权限验证
        
        from services.scheduler_service import create_scheduler
        
        data = request.get_json() or {}
        reason = data.get('reason', 'manual_refresh')
        
        # 获取调度器 (需要已启动)
        scheduler = current_app.config.get('SCHEDULER')
        
        if not scheduler:
            return jsonify({
                'success': False,
                'error': '调度服务未启动'
            }), 500
        
        # 手动刷新
        prediction = scheduler.manual_refresh_prediction(match_id)
        
        if not prediction:
            return jsonify({
                'success': False,
                'error': '刷新失败，比赛可能不存在或无赔率数据',
                'match_id': match_id
            }), 404
        
        return jsonify({
            'success': True,
            'match_id': match_id,
            'prediction': prediction.to_dict(),
            'version': prediction.prediction_version,
            'trigger_reason': reason,
            'message': '预测已刷新',
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"[API] 手动刷新预测失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@cache_api.route('/status', methods=['GET'])
def get_cache_status():
    """
    获取缓存状态
    
    返回:
        matches_cached: 缓存比赛数
        predictions_cached: 缓存预测数
        odds_records: 赔率记录数
        last_update: 最后更新时间
    """
    try:
        db = get_db_manager()
        session = db.get_session()
        
        # 统计
        matches_count = session.query(MatchCache).count()
        predictions_count = session.query(SystemPrediction).filter(SystemPrediction.is_current == True).count()
        odds_count = session.query(OddsHistory).count()
        
        # 最后更新时间
        last_match = session.query(MatchCache).order_by(MatchCache.updated_at.desc()).first()
        last_prediction = session.query(SystemPrediction).order_by(SystemPrediction.created_at.desc()).first()
        
        db.close_session(session)
        
        return jsonify({
            'success': True,
            'status': {
                'matches_cached': matches_count,
                'predictions_cached': predictions_count,
                'odds_records': odds_count,
                'last_match_update': last_match.updated_at.isoformat() if last_match else None,
                'last_prediction_update': last_prediction.created_at.isoformat() if last_prediction else None
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"[API] 获取缓存状态失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== 注册蓝图 ====================

def register_cache_api(app):
    """注册缓存API蓝图到Flask应用"""
    app.register_blueprint(cache_api)
    logger.info("[API] 预计算缓存API已注册: /api/cache")


if __name__ == "__main__":
    # 测试API
    from flask import Flask
    
    app = Flask(__name__)
    register_cache_api(app)
    
    print("\n预计算缓存API端点:")
    print("  GET  /api/cache/matches                 - 获取比赛列表")
    print("  GET  /api/cache/matches/<match_id>      - 获取比赛详情")
    print("  GET  /api/cache/predictions/<match_id>  - 获取预测")
    print("  POST /api/cache/predictions/batch       - 批量获取预测")
    print("  GET  /api/cache/predictions/<match_id>/history - 预测历史")
    print("  GET  /api/cache/odds/<match_id>         - 获取最新赔率")
    print("  GET  /api/cache/odds/<match_id>/history - 赔率历史")
    print("  POST /api/cache/predictions/<match_id>/refresh - 手动刷新")
    print("  GET  /api/cache/status                  - 缓存状态")
    
    # 初始化数据库
    db = get_db_manager()
    db.init_db()
    
    print("\n[DB] 数据库初始化完成")