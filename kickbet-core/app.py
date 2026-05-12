"""
KickBet Flask API
提供五大联赛比赛分析、预测、赔率数据的HTTP接口

端点:
- /api/health          健康检查 (公开)
- /api/auth/register   用户注册 (公开)
- /api/auth/login      用户登录 (公开)
- /api/auth/refresh    Token刷新 (需认证)
- /api/matches         比赛列表 (公开)
- /api/analysis/<id>   单场比赛分析 (需认证)
- /api/calculate/*     计算端点 (需认证 + Rate Limit)
- /api/admin/*         管理端点 (需管理员权限)
"""

from flask import Flask, jsonify, request, g
from flask_cors import CORS
import logging
from datetime import datetime
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.kickbet_core import KickBetCore, MatchAnalysis
from collectors.football_data_org import FootballDataOrgCollector, Match
from collectors.odds_api_io import OddsApiIoCollector, OddsApiIoConfig
from predictors.poisson_predictor import PoissonPredictor, KellyCriterion, TeamAttackDefenseStats
from dataclasses import asdict

# 安全模块
from security.auth import (
    limiter, token_required, admin_required, validate_input,
    generate_token, verify_token, create_user, authenticate_user,
    get_user_by_id, init_default_users, User, RATE_LIMITS
)

# 数据库模块
from database.models import db, init_database, PredictionRecord, MatchRecord

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 配置Rate Limiter
limiter.init_app(app)

# JWT配置 (生产环境应从环境变量读取)
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'kickbet-secret-key-change-in-production')

# 初始化核心服务
kickbet_core = None

def init_services():
    """初始化服务"""
    global kickbet_core
    try:
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.yaml')
        kickbet_core = KickBetCore(config_path)
        logger.info("KickBetCore服务初始化成功")
        
        # 初始化数据库
        init_database()
        logger.info("数据库初始化完成")
        
        # 初始化默认用户
        init_default_users()
        logger.info("安全模块初始化完成")
        
        return True
    except Exception as e:
        logger.error(f"KickBetCore初始化失败: {e}")
        return False

# ==================== API端点 ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'service': 'KickBet API',
        'version': '1.0.0',
        'time': datetime.now().isoformat()
    })


# ==================== 认证端点 ====================

@app.route('/api/auth/register', methods=['POST'])
@limiter.limit(RATE_LIMITS['auth'])
def register():
    """
    用户注册
    
    参数 (JSON body):
    - username: 用户名 (3-30字符)
    - email: 邮箱地址
    - password: 密码 (6+字符)
    
    返回:
    - user: 用户信息
    - token: JWT token
    """
    try:
        data = request.get_json()
        
        # 验证输入
        if not data:
            return jsonify({'error': '请求数据缺失'}), 400
        
        username = data.get('username', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        # 基本验证
        if len(username) < 3:
            return jsonify({'error': '用户名至少3字符'}), 400
        if len(password) < 6:
            return jsonify({'error': '密码至少6字符'}), 400
        if '@' not in email:
            return jsonify({'error': '邮箱格式不正确'}), 400
        
        # 创建用户
        user, error = create_user(username, email, password, 'user')
        
        if error:
            return jsonify({'error': error}), 400
        
        # 生成token
        token = generate_token(user)
        
        return jsonify({
            'message': '注册成功',
            'user': {
                'user_id': user.user_id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'created_at': user.created_at.isoformat()
            },
            'token': token,
            'expires_in': 86400  # 24小时
        }), 201
        
    except Exception as e:
        logger.error(f"注册失败: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/login', methods=['POST'])
@limiter.limit(RATE_LIMITS['auth'])
def login():
    """
    用户登录
    
    参数 (JSON body):
    - username: 用户名或邮箱
    - password: 密码
    
    返回:
    - user: 用户信息
    - token: JWT token
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': '请求数据缺失'}), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'error': '用户名和密码不能为空'}), 400
        
        # 认证用户
        user, error = authenticate_user(username, password)
        
        if error:
            return jsonify({'error': error}), 401
        
        # 生成token
        token = generate_token(user)
        
        return jsonify({
            'message': '登录成功',
            'user': {
                'user_id': user.user_id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'last_login': user.last_login.isoformat() if user.last_login else None
            },
            'token': token,
            'expires_in': 86400
        })
        
    except Exception as e:
        logger.error(f"登录失败: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/refresh', methods=['POST'])
@token_required
@limiter.limit(RATE_LIMITS['auth'])
def refresh_token():
    """
    刷新JWT token
    
    需要在header中提供有效的Bearer token
    
    返回:
    - token: 新的JWT token
    """
    try:
        user_id = g.user_id
        
        user = get_user_by_id(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        token = generate_token(user)
        
        return jsonify({
            'message': 'Token刷新成功',
            'token': token,
            'expires_in': 86400
        })
        
    except Exception as e:
        logger.error(f"Token刷新失败: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/me', methods=['GET'])
@token_required
def get_current_user():
    """
    获取当前用户信息
    
    返回:
    - user: 用户详细信息
    """
    try:
        user_id = g.user_id
        
        user = get_user_by_id(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        return jsonify({
            'user': {
                'user_id': user.user_id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'created_at': user.created_at.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'is_active': user.is_active
            }
        })
        
    except Exception as e:
        logger.error(f"获取用户信息失败: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== 管理端点 ====================

@app.route('/api/admin/users', methods=['GET'])
@token_required
@admin_required
@limiter.limit("10 per minute")
def admin_list_users():
    """
    管理员: 获取用户列表
    """
    from security.auth import _users_db
    
    users = []
    for user in _users_db.values():
        users.append({
            'user_id': user.user_id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'created_at': user.created_at.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'is_active': user.is_active
        })
    
    return jsonify({
        'total': len(users),
        'users': users
    })


@app.route('/api/admin/stats', methods=['GET'])
@token_required
@admin_required
def admin_stats():
    """
    管理员: 系统统计
    """
    try:
        # 用户统计
        user_stats = db.count_users()
        
        # 预测统计
        pred_stats = db.count_predictions()
        
        return jsonify({
            'users': user_stats,
            'predictions': pred_stats,
            'api': {
                'version': '1.0.0',
                'endpoints': len(app.url_map._rules) - 1
            }
        })
    except Exception as e:
        # 使用内存统计作为备用
        from security.auth import _users_db
        return jsonify({
            'users': {
                'total': len(_users_db),
                'admins': len([u for u in _users_db.values() if u.role == 'admin']),
                'active': len([u for u in _users_db.values() if u.is_active])
            },
            'predictions': {'total': 0, 'correct': 0, 'pending': 0, 'accuracy': 0.0},
            'api': {
                'version': '1.0.0',
                'endpoints': len(app.url_map._rules) - 1
            }
        })


@app.route('/api/user/predictions', methods=['GET'])
@token_required
def user_predictions():
    """
    用户: 获取自己的预测历史
    
    Query参数:
    - limit: 返回数量 (默认50)
    """
    try:
        user_id = g.user_id
        limit = int(request.args.get('limit', 50))
        
        predictions = db.get_predictions_by_user(user_id, limit)
        
        return jsonify({
            'total': len(predictions),
            'predictions': [p.to_dict() for p in predictions]
        })
    except Exception as e:
        logger.error(f"获取用户预测历史失败: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/predictions/<int:prediction_id>', methods=['GET'])
@token_required
def get_prediction(prediction_id):
    """
    获取单个预测记录详情
    """
    try:
        session = db.get_session()
        record = session.query(PredictionRecord).filter(PredictionRecord.id == prediction_id).first()
        session.close()
        
        if not record:
            return jsonify({'error': '预测记录不存在'}), 404
        
        # 检查权限（只有预测创建者或管理员可查看）
        if record.user_id and record.user_id != g.user_id:
            user = get_user_by_id(g.user_id)
            if user and user.role != 'admin':
                return jsonify({'error': '无权访问'}), 403
        
        return jsonify(record.to_dict())
    except Exception as e:
        logger.error(f"获取预测记录失败: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/matches', methods=['GET'])
def get_matches():
    """
    获取五大联赛即将进行的比赛
    
    Query参数:
    - days: 查询天数 (默认3)
    - league: 联赛代码 (PL/BL1/PD/SA/FL1, 可选)
    """
    try:
        days = int(request.args.get('days', 3))
        league = request.args.get('league', None)
        
        if not kickbet_core:
            return jsonify({'error': '服务未初始化'}), 500
        
        matches = kickbet_core.fetch_upcoming_matches(days)
        
        # 按联赛筛选
        if league:
            matches = [m for m in matches if m.league_code == league]
        
        # 转换为JSON
        result = []
        for match in matches:
            league_info = kickbet_core.config['leagues'].get(match.league_code, {})
            result.append({
                'match_id': match.match_id,
                'home_team': match.home_team_name,
                'away_team': match.away_team_name,
                'league': match.league_code,
                'league_name': league_info.get('name', match.league_code),
                'match_date': match.match_date,
                'status': match.status
            })
        
        return jsonify({
            'total': len(result),
            'matches': result,
            'query': {'days': days, 'league': league}
        })
        
    except Exception as e:
        logger.error(f"获取比赛失败: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/match/<int:match_id>', methods=['GET'])
def get_match_detail(match_id):
    """
    获取单场比赛详情
    
    参数:
    - match_id: 比赛ID
    """
    try:
        if not kickbet_core:
            return jsonify({'error': '服务未初始化'}), 500
        
        # 从所有联赛查找比赛
        matches = kickbet_core.fetch_upcoming_matches(days=7)
        
        match = None
        for m in matches:
            if m.match_id == match_id:
                match = m
                break
        
        if not match:
            return jsonify({'error': '比赛不存在'}), 404
        
        league_info = kickbet_core.config['leagues'].get(match.league_code, {})
        
        return jsonify({
            'match': {
                'match_id': match.match_id,
                'home_team': match.home_team_name,
                'home_team_id': match.home_team_id,
                'away_team': match.away_team_name,
                'away_team_id': match.away_team_id,
                'league': match.league_code,
                'league_name': league_info.get('name', match.league_code),
                'match_date': match.match_date,
                'status': match.status
            }
        })
        
    except Exception as e:
        logger.error(f"获取比赛详情失败: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/analysis/<int:match_id>', methods=['GET'])
def get_match_analysis(match_id):
    """
    获取单场比赛完整分析
    
    参数:
    - match_id: 毸赛ID
    
    返回:
    - Poisson预测概率
    - 赔率数据 (ML/Spread/Totals)
    - Kelly价值评估
    - 三种投注方案 (保守/平衡/激进)
    """
    try:
        if not kickbet_core:
            return jsonify({'error': '服务未初始化'}), 500
        
        # 查找比赛
        matches = kickbet_core.fetch_upcoming_matches(days=7)
        
        match = None
        for m in matches:
            if m.match_id == match_id:
                match = m
                break
        
        if not match:
            return jsonify({'error': '比赛不存在'}), 404
        
        # 获取球队统计
        team_stats = kickbet_core.fetch_team_stats(match.league_code)
        kickbet_core.predictor.load_stats_from_standings([
            {'team_id': s.team_id, 'team_name': s.team_name,
             'home_scored_avg': s.home_scored_avg, 'home_conceded_avg': s.home_conceded_avg,
             'away_scored_avg': s.away_scored_avg, 'away_conceded_avg': s.away_conceded_avg,
             'home_played': s.home_played, 'away_played': s.away_played}
            for s in team_stats.values()
        ])
        
        # 获取赔率
        odds_list = kickbet_core.fetch_odds_for_league(match.league_code)
        
        # 匹配赔率
        match_odds = None
        for odds in odds_list:
            if kickbet_core._match_teams(match, odds):
                match_odds = odds
                break
        
        if not match_odds:
            # 无赔率数据时，只返回预测
            prediction = kickbet_core.predictor.predict_match(
                match_id=str(match.match_id),
                home_team=match.home_team_name,
                away_team=match.away_team_name,
                home_team_id=match.home_team_id,
                away_team_id=match.away_team_id
            )
            
            return jsonify({
                'match': asdict(match),
                'prediction': asdict(prediction),
                'odds': None,
                'message': '该比赛暂无赔率数据'
            })
        
        # 完整分析
        analysis = kickbet_core.analyze_match(match, team_stats, match_odds)
        
        # 保存预测记录到数据库
        try:
            totals = analysis.totals_prediction or {}
            handicap = analysis.handicap_prediction or {}
            
            db.save_prediction(
                user_id=g.get('user_id'),  # 可能为None（未登录用户）
                match_id=str(analysis.match_id),
                home_team=analysis.home_team,
                away_team=analysis.away_team,
                league=analysis.league,
                lambda_home=analysis.expected_home_goals,
                lambda_away=analysis.expected_away_goals,
                prob_home=analysis.prob_home,
                prob_draw=analysis.prob_draw,
                prob_away=analysis.prob_away,
                prediction=analysis.prediction,
                score_distribution=analysis.score_distribution,
                totals_line=totals.get('line'),
                prob_over=totals.get('prob_over'),
                prob_under=totals.get('prob_under'),
                handicap=handicap.get('handicap'),
                prob_home_cover=handicap.get('prob_home_cover'),
                prob_away_cover=handicap.get('prob_away_cover')
            )
            logger.info(f"预测记录已保存: match_id={match_id}")
        except Exception as save_err:
            logger.warning(f"保存预测记录失败: {save_err}")
        
        # 转换为JSON - 对齐前端期望结构
        # 构建kelly_criterion结构
        kelly_data = {'home': {}, 'draw': {}, 'away': {}}
        for vb in analysis.value_bets:
            key = vb.selection.lower() if vb.selection in ['H', 'D', 'A'] else None
            if key:
                kelly_map = {'h': 'home', 'd': 'draw', 'a': 'away'}
                k = kelly_map.get(key)
                if k:
                    kelly_data[k] = {
                        'edge': vb.edge,
                        'kelly': vb.kelly_fraction,
                        'half_kelly': vb.kelly_fraction / 2,
                        'value': vb.is_value
                    }
        
        # 构建recommended_bets结构
        bets = {'conservative': {}, 'balanced': {}, 'aggressive': {}}
        for s in analysis.schemes:
            if s.scheme_type in bets:
                bets[s.scheme_type] = {
                    'type': s.play_name,
                    'selection': s.selection,
                    'odds': s.odds,
                    'stake_pct': s.stake_percent,
                    'reason': s.reason,
                    'bookmaker': s.bookmaker
                }
        
        # 构建poisson_simulation结构
        score_dist = analysis.score_distribution or {}
        most_likely = sorted(score_dist.items(), key=lambda x: -x[1])[:5] if score_dist else []
        
        # 构建odds结构 (扁平化)
        odds_ml = analysis.odds_ml or {}
        odds_spread = analysis.odds_spread or {}
        odds_totals = analysis.odds_totals or {}
        
        result = {
            'match': {
                'match_id': analysis.match_id,
                'home_team': analysis.home_team,
                'away_team': analysis.away_team,
                'league': analysis.league,
                'league_name': analysis.league_name,
                'match_date': analysis.match_date
            },
            'prediction': {
                'home_win_prob': round(analysis.prob_home * 100, 1),
                'draw_prob': round(analysis.prob_draw * 100, 1),
                'away_win_prob': round(analysis.prob_away * 100, 1),
                'predicted_home_goals': round(analysis.expected_home_goals, 2),
                'predicted_away_goals': round(analysis.expected_away_goals, 2),
                'result': analysis.prediction,
                'most_likely_score': analysis.most_likely_score
            },
            'poisson_simulation': {
                'iterations': 10000,
                'home_win_pct': round(analysis.prob_home * 100, 1),
                'draw_pct': round(analysis.prob_draw * 100, 1),
                'away_win_pct': round(analysis.prob_away * 100, 1),
                'most_likely_scores': [{'score': s, 'probability': round(p * 100, 1)} for s, p in most_likely]
            },
            'odds': {
                'home': odds_ml.get('home'),
                'draw': odds_ml.get('draw'),
                'away': odds_ml.get('away'),
                'over_under': {
                    'line': odds_totals.get('line', 2.5),
                    'over': odds_totals.get('over'),
                    'under': odds_totals.get('under')
                } if odds_totals else None,
                'handicap': {
                    'line': odds_spread.get('hdp'),
                    'home': odds_spread.get('home'),
                    'away': odds_spread.get('away')
                } if odds_spread else None
            },
            'kelly_criterion': kelly_data,
            'recommended_bets': bets,
            # 保留原始详细数据供高级用户
            'totals': analysis.totals_prediction,
            'handicap': analysis.handicap_prediction,
            'score_distribution': analysis.score_distribution
        }
        
        return jsonify(result)
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"获取分析失败: {error_msg}")
        
        # 处理API Rate Limit等外部错误，返回降级数据
        if '429' in error_msg or 'Too Many Requests' in error_msg:
            # Odds-API.io 限流，尝试返回无赔率的预测
            try:
                if match and kickbet_core:
                    # 联赛名称映射
                    league_names = {'PL': '英超', 'BL1': '德甲', 'PD': '西甲', 'SA': '意甲', 'FL1': '法甲'}
                    
                    prediction = kickbet_core.predictor.predict_match(
                        match_id=str(match.match_id),
                        home_team=match.home_team_name,
                        away_team=match.away_team_name,
                        home_team_id=match.home_team_id,
                        away_team_id=match.away_team_id
                    )
                    
                    score_dist = getattr(prediction, 'score_distribution', {}) or {}
                    most_likely = sorted(score_dist.items(), key=lambda x: -x[1])[:5] if score_dist else []
                    
                    return jsonify({
                        'match': {
                            'match_id': match.match_id,
                            'home_team': match.home_team_name,
                            'away_team': match.away_team_name,
                            'league': match.league_code,
                            'league_name': league_names.get(match.league_code, match.league_code),
                            'match_date': match.match_date.isoformat() if hasattr(match.match_date, 'isoformat') else str(match.match_date)
                        },
                        'prediction': {
                            'home_win_prob': round(prediction.prob_home * 100, 1),
                            'draw_prob': round(prediction.prob_draw * 100, 1),
                            'away_win_prob': round(prediction.prob_away * 100, 1),
                            'predicted_home_goals': round(prediction.expected_home_goals, 2),
                            'predicted_away_goals': round(prediction.expected_away_goals, 2),
                            'result': prediction.prediction,
                            'most_likely_score': getattr(prediction, 'most_likely_score', '--')
                        },
                        'poisson_simulation': {
                            'iterations': 10000,
                            'home_win_pct': round(prediction.prob_home * 100, 1),
                            'draw_pct': round(prediction.prob_draw * 100, 1),
                            'away_win_pct': round(prediction.prob_away * 100, 1),
                            'most_likely_scores': [{'score': s, 'probability': round(p * 100, 1)} for s, p in most_likely]
                        },
                        'odds': None,
                        'kelly_criterion': {'home': {}, 'draw': {}, 'away': {}},
                        'recommended_bets': {'conservative': {}, 'balanced': {}, 'aggressive': {}},
                        'warning': '赔率数据API暂时不可用(Rate Limit)，仅显示预测结果'
                    })
            except Exception as fallback_err:
                logger.error(f"降级方案也失败: {fallback_err}")
        
        return jsonify({'error': error_msg}), 500


@app.route('/api/standings/<league>', methods=['GET'])
def get_standings(league):
    """
    获取联赛积分榜
    
    参数:
    - league: 联赛代码 (PL/BL1/PD/SA/FL1)
    """
    try:
        if not kickbet_core:
            return jsonify({'error': '服务未初始化'}), 500
        
        if league not in kickbet_core.BIG_FIVE:
            return jsonify({'error': '不支持该联赛'}), 400
        
        standings = kickbet_core.football_collector.get_standings(league)
        
        league_info = kickbet_core.config['leagues'].get(league, {})
        
        result = {
            'league': league,
            'league_name': league_info.get('name', league),
            'season': standings.season,
            'standings': []
        }
        
        for team in standings.standings:
            result['standings'].append({
                'position': team.position,
                'team_id': team.team_id,
                'team_name': team.team_name,
                'played': team.played,
                'won': team.won,
                'drawn': team.drawn,
                'lost': team.lost,
                'goals_for': team.goals_for,
                'goals_against': team.goals_against,
                'goals_for_avg': team.goals_for_avg,
                'goals_against_avg': team.goals_against_avg,
                'points': team.points
            })
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"获取积分榜失败: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/odds/<league>', methods=['GET'])
def get_odds(league):
    """
    获取联赛赔率数据
    
    参数:
    - league: 联赛代码 (PL/BL1/PD/SA/FL1)
    """
    try:
        if not kickbet_core:
            return jsonify({'error': '服务未初始化'}), 500
        
        if league not in kickbet_core.BIG_FIVE:
            return jsonify({'error': '不支持该联赛'}), 400
        
        odds_list = kickbet_core.fetch_odds_for_league(league)
        
        result = []
        for odds in odds_list:
            result.append({
                'event_id': odds.event_id,
                'home_team': odds.home_team,
                'away_team': odds.away_team,
                'league': odds.league,
                'ml': {
                    'home': odds.home_odds,
                    'draw': odds.draw_odds,
                    'away': odds.away_odds,
                    'home_bookmaker': odds.home_bookmaker,
                    'draw_bookmaker': odds.draw_bookmaker,
                    'away_bookmaker': odds.away_bookmaker
                },
                'spread': {
                    'hdp': odds.spread_hdp,
                    'home': odds.spread_home_odds,
                    'away': odds.spread_away_odds,
                    'home_bookmaker': odds.spread_home_bookmaker,
                    'away_bookmaker': odds.spread_away_bookmaker
                } if odds.spread_hdp else None,
                'totals': {
                    'hdp': odds.totals_hdp,
                    'over': odds.totals_over_odds,
                    'under': odds.totals_under_odds,
                    'over_bookmaker': odds.totals_over_bookmaker,
                    'under_bookmaker': odds.totals_under_bookmaker
                } if odds.totals_hdp else None,
                'market_prob': {
                    'home': odds.market_prob_home,
                    'draw': odds.market_prob_draw,
                    'away': odds.market_prob_away
                },
                'updated_at': odds.updated_at
            })
        
        return jsonify({
            'league': league,
            'total': len(result),
            'odds': result
        })
        
    except Exception as e:
        logger.error(f"获取赔率失败: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/daily', methods=['GET'])
def get_daily_analysis():
    """
    获取今日分析汇总
    
    返回五大联赛所有即将进行的比赛分析
    """
    try:
        if not kickbet_core:
            return jsonify({'error': '服务未初始化'}), 500
        
        days = int(request.args.get('days', 3))
        
        analyses = kickbet_core.run_daily_analysis(days)
        
        result = []
        for analysis in analyses:
            result.append({
                'match': {
                    'match_id': analysis.match_id,
                    'home_team': analysis.home_team,
                    'away_team': analysis.away_team,
                    'league': analysis.league,
                    'league_name': analysis.league_name,
                    'match_date': analysis.match_date
                },
                'prediction': {
                    'result': analysis.prediction,
                    'prob_home': analysis.prob_home,
                    'prob_draw': analysis.prob_draw,
                    'prob_away': analysis.prob_away,
                    'expected_home_goals': analysis.expected_home_goals,
                    'expected_away_goals': analysis.expected_away_goals,
                    'most_likely_score': analysis.most_likely_score
                },
                'schemes': [asdict(s) for s in analysis.schemes]
            })
        
        return jsonify({
            'total': len(result),
            'analyses': result,
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取每日分析失败: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/leagues', methods=['GET'])
def get_leagues():
    """获取支持的联赛列表"""
    try:
        if not kickbet_core:
            return jsonify({'error': '服务未初始化'}), 500
        
        leagues = []
        for code, info in kickbet_core.config['leagues'].items():
            leagues.append({
                'code': code,
                'name': info['name'],
                'name_en': info['name_en'],
                'priority': info['priority']
            })
        
        return jsonify({
            'total': len(leagues),
            'leagues': sorted(leagues, key=lambda x: x['priority'])
        })
        
    except Exception as e:
        logger.error(f"获取联赛列表失败: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/calculate/totals', methods=['POST'])
@token_required
@limiter.limit(RATE_LIMITS['calculate'])
def calculate_totals():
    """
    计算任意盘口线的大小球概率
    
    参数 (JSON body):
    - match_id: 比赛ID (可选，如果提供则使用已有预测)
    - lambda_home: 主队预期进球 (可选，如果无match_id则必须)
    - lambda_away: 客队预期进球 (可选，如果无match_id则必须)
    - line: 盘口线 (如 2.5, 2.0, 3.5)
    
    返回:
    - over: 大球概率
    - under: 小球概率
    - exact: 走水概率 (仅整数盘口)
    """
    try:
        data = request.get_json()
        line = data.get('line', 2.5)
        
        # 如果有match_id，使用已有预测
        if 'match_id' in data:
            match_id = int(data['match_id'])
            matches = kickbet_core.fetch_upcoming_matches(days=7)
            
            match = None
            for m in matches:
                if m.match_id == match_id:
                    match = m
                    break
            
            if not match:
                return jsonify({'error': '比赛不存在'}), 404
            
            # 获取球队统计并预测
            team_stats = kickbet_core.fetch_team_stats(match.league_code)
            for tid, stats in team_stats.items():
                kickbet_core.predictor.set_team_stats(tid, stats)
            
            prediction = kickbet_core.predictor.predict_match(
                str(match.match_id), match.home_team_name, match.away_team_name,
                match.home_team_id, match.away_team_id
            )
            
            result = kickbet_core.predictor.calculate_totals_for_line(
                prediction.score_distribution, line
            )
        else:
            # 使用lambda参数直接计算
            lambda_home = data.get('lambda_home', 1.5)
            lambda_away = data.get('lambda_away', 1.2)
            
            # 模拟比赛获取比分分布
            probs, score_probs, _ = kickbet_core.predictor.simulate_match(
                lambda_home, lambda_away
            )
            
            result = kickbet_core.predictor.calculate_totals_for_line(score_probs, line)
            result['lambda_home'] = lambda_home
            result['lambda_away'] = lambda_away
            result['total_expected'] = lambda_home + lambda_away
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"计算大小球概率失败: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/calculate/handicap', methods=['POST'])
@token_required
@limiter.limit(RATE_LIMITS['calculate'])
def calculate_handicap():
    """
    计算任意让球盘口的概率
    
    参数 (JSON body):
    - match_id: 比赛ID (可选)
    - lambda_home: 主队预期进球 (可选)
    - lambda_away: 客队预期进球 (可选)
    - handicap: 盘口值 (如 -0.5, -1.0, +0.5)
    
    返回:
    - home: 主队赢盘概率
    - away: 客队赢盘概率
    - draw: 走水概率 (仅整数盘口)
    """
    try:
        data = request.get_json()
        handicap = data.get('handicap', -0.5)
        
        # 如果有match_id，使用已有预测
        if 'match_id' in data:
            match_id = int(data['match_id'])
            matches = kickbet_core.fetch_upcoming_matches(days=7)
            
            match = None
            for m in matches:
                if m.match_id == match_id:
                    match = m
                    break
            
            if not match:
                return jsonify({'error': '比赛不存在'}), 404
            
            team_stats = kickbet_core.fetch_team_stats(match.league_code)
            for tid, stats in team_stats.items():
                kickbet_core.predictor.set_team_stats(tid, stats)
            
            prediction = kickbet_core.predictor.predict_match(
                str(match.match_id), match.home_team_name, match.away_team_name,
                match.home_team_id, match.away_team_id
            )
            
            result = kickbet_core.predictor.calculate_handicap_for_line(
                prediction.score_distribution, handicap
            )
        else:
            lambda_home = data.get('lambda_home', 1.5)
            lambda_away = data.get('lambda_away', 1.2)
            
            probs, score_probs, _ = kickbet_core.predictor.simulate_match(
                lambda_home, lambda_away
            )
            
            result = kickbet_core.predictor.calculate_handicap_for_line(score_probs, handicap)
            result['lambda_home'] = lambda_home
            result['lambda_away'] = lambda_away
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"计算让球盘概率失败: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== 错误处理 ====================

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': '资源不存在'}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': '服务器错误'}), 500


# ==================== 启动 ====================

if __name__ == '__main__':
    # 初始化服务
    init_services()
    
    # 启动Flask
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"KickBet API 启动在端口 {port}")
    print(f"\n{'='*50}")
    print("KickBet Flask API")
    print(f"{'='*50}")
    print(f"端口: {port}")
    print(f"调试模式: {debug}")
    print("\nAPI端点:")
    print("  GET /api/health         - 健康检查")
    print("  GET /api/leagues        - 联赛列表")
    print("  GET /api/matches        - 比赛列表")
    print("  GET /api/match/<id>     - 比赛详情")
    print("  GET /api/analysis/<id>  - 比赛分析(含大小球/让球盘)")
    print("  GET /api/standings/<league> - 积分榜")
    print("  GET /api/odds/<league>  - 赔率数据")
    print("  GET /api/daily          - 今日分析汇总")
    print("  POST /api/calculate/totals   - 计算大小球概率(任意盘口)")
    print("  POST /api/calculate/handicap - 计算让球盘概率(任意盘口)")
    print(f"{'='*50}\n")
    
    app.run(host='0.0.0.0', port=port, debug=debug)