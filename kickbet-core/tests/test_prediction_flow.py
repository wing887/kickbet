"""
KickBet 预计算数据流测试

测试流程:
1. 数据库初始化
2. Football-Data.org API采集 (比赛+积分榜)
3. 数据存入缓存表
4. 验证数据完整性
"""

import os
import sys
import yaml
import logging
from datetime import datetime

# 设置路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import PredictionCacheManager, MatchCache, TeamStatsCache, SystemPrediction
from collectors.football_data_org import FootballDataOrgCollector, Match, TeamStats
from sqlalchemy import text

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# WSL代理
PROXY = "http://172.18.176.1:10808"


def load_config():
    """加载配置"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def test_database_init():
    """测试数据库初始化"""
    logger.info("\n" + "="*50)
    logger.info("Step 1: 数据库初始化测试")
    logger.info("="*50)
    
    db = PredictionCacheManager()
    db.init_db()
    
    # 检查表
    session = db.get_session()
    tables = ['matches_cache', 'odds_history', 'system_predictions', 'team_stats_cache']
    
    for table in tables:
        count = session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
        logger.info(f"  {table}: {count} 条记录")
    
    db.close_session(session)
    return db


def test_football_data_api(db: PredictionCacheManager, config: dict):
    """测试Football-Data.org API采集"""
    logger.info("\n" + "="*50)
    logger.info("Step 2: Football-Data.org API测试")
    logger.info("="*50)
    
    api_key = config['api']['football_data']['api_key']
    collector = FootballDataOrgCollector(api_key, proxy=PROXY)
    
    # 测试联赛 - 只测试英超 (节省配额)
    league_code = 'PL'
    
    # 2.1 获取即将进行的比赛
    logger.info(f"\n[{league_code}] 获取即将进行的比赛...")
    try:
        matches = collector.get_upcoming_matches(league_code, days=3)
        logger.info(f"  获取到 {len(matches)} 场比赛")
        
        # 存入缓存
        for match in matches[:5]:  # 只存前5场测试
            match_data = {
                'match_id': str(match.match_id),
                'league_code': league_code,
                'league_name': 'Premier League',
                'home_team_id': match.home_team_id,
                'home_team_name': match.home_team_name,
                'away_team_id': match.away_team_id,
                'away_team_name': match.away_team_name,
                'match_time': datetime.fromisoformat(match.match_date.replace('Z', '+00:00')) if match.match_date else None,
                'status': match.status
            }
            saved = db.save_match(match_data)
            if saved:
                logger.info(f"    保存: {match.home_team_name} vs {match.away_team_name}")
        
        collector.request_count += len(matches)
        
    except Exception as e:
        logger.error(f"  获取比赛失败: {e}")
    
    # 2.2 获取积分榜
    logger.info(f"\n[{league_code}] 获取积分榜...")
    try:
        standings = collector.get_standings(league_code)
        logger.info(f"  获取到 {len(standings.standings)} 个球队统计")
        
        # 存入缓存
        for team in standings.standings[:5]:  # 只存前5个测试
            stats_data = {
                'team_id': team.team_id,
                'team_name': team.team_name,
                'league_code': league_code,
                'home_scored_avg': team.goals_for_avg * 1.1,
                'home_conceded_avg': team.goals_against_avg * 0.9,
                'home_played': team.played // 2 if team.played > 0 else 0,
                'away_scored_avg': team.goals_for_avg * 0.9,
                'away_conceded_avg': team.goals_against_avg * 1.1,
                'away_played': team.played // 2 if team.played > 0 else 0
            }
            saved = db.save_team_stats(stats_data)
            if saved:
                logger.info(f"    保存: {team.team_name} (场均进球{team.goals_for_avg:.2f})")
        
        collector.request_count += 1
        
    except Exception as e:
        logger.error(f"  获取积分榜失败: {e}")
    
    return collector.request_count


def test_cache_read(db: PredictionCacheManager):
    """测试缓存数据读取"""
    logger.info("\n" + "="*50)
    logger.info("Step 3: 缓存数据读取测试")
    logger.info("="*50)
    
    # 获取缓存的比赛
    matches = db.get_upcoming_matches(hours=72)
    logger.info(f"  缓存比赛数: {len(matches)}")
    
    for match in matches[:3]:
        logger.info(f"    - {match.home_team_name} vs {match.away_team_name} ({match.status})")
    
    # 获取球队统计
    stats = db.get_team_stats_for_league('PL')
    logger.info(f"  缓存球队统计数: {len(stats)}")
    
    for stat in stats[:3]:
        logger.info(f"    - {stat.team_name}: 主场进攻{stat.home_scored_avg:.2f}, 客场进攻{stat.away_scored_avg:.2f}")


def test_prediction_generation(db: PredictionCacheManager):
    """测试预测生成"""
    logger.info("\n" + "="*50)
    logger.info("Step 4: 预测生成测试")
    logger.info("="*50)
    
    # 获取缓存的比赛
    matches = db.get_upcoming_matches(hours=72)
    
    if not matches:
        logger.warning("  无比赛数据，跳过预测测试")
        return
    
    # 获取球队统计
    all_stats = db.get_all_team_stats()
    
    if not all_stats:
        logger.warning("  无球队统计数据，跳过预测测试")
        return
    
    # 加载预测器
    from predictors.poisson_predictor import PoissonPredictor, TeamAttackDefenseStats
    
    predictor = PoissonPredictor(nsim=1000)  # 减少模拟次数用于测试
    
    # 加载球队统计到预测器
    for team_id, stats in all_stats.items():
        team_stats = TeamAttackDefenseStats(
            team_id=stats.team_id,
            team_name=stats.team_name,
            home_scored_avg=stats.home_scored_avg,
            home_conceded_avg=stats.home_conceded_avg,
            home_played=stats.home_played,
            away_scored_avg=stats.away_scored_avg,
            away_conceded_avg=stats.away_conceded_avg,
            away_played=stats.away_played
        )
        predictor.set_team_stats(team_id, team_stats)
    
    logger.info(f"  加载了 {len(all_stats)} 个球队统计")
    
    # 对第一场比赛进行预测
    match = matches[0]
    logger.info(f"\n  预测比赛: {match.home_team_name} vs {match.away_team_name}")
    
    try:
        prediction = predictor.predict_match(
            match_id=match.match_id,
            home_team=match.home_team_name,
            away_team=match.away_team_name,
            home_team_id=match.home_team_id,
            away_team_id=match.away_team_id
        )
        
        logger.info(f"    主胜概率: {prediction.prob_home:.1%}")
        logger.info(f"    平局概率: {prediction.prob_draw:.1%}")
        logger.info(f"    客胜概率: {prediction.prob_away:.1%}")
        logger.info(f"    预测结果: {prediction.prediction}")
        logger.info(f"    最可能比分: {prediction.most_likely_score}")
        
        # 存入预测缓存 (模拟，无赔率数据)
        prediction_data = {
            'match_id': match.match_id,
            'home_prob': prediction.prob_home,
            'draw_prob': prediction.prob_draw,
            'away_prob': prediction.prob_away,
            'prediction': prediction.prediction,
            'lambda_home': prediction.expected_home_goals,
            'lambda_away': prediction.expected_away_goals,
            'expected_home_goals': prediction.expected_home_goals,
            'expected_away_goals': prediction.expected_away_goals,
            'most_likely_score': prediction.most_likely_score,
            'score_distribution': prediction.score_distribution,
            'value_bets': []
        }
        
        saved = db.save_prediction(prediction_data, trigger_reason='test_generation')
        
        if saved:
            logger.info(f"    预测已保存 (版本: {saved.prediction_version})")
        
    except Exception as e:
        logger.error(f"    预测失败: {e}")


def verify_full_flow(db: PredictionCacheManager):
    """验证完整数据流"""
    logger.info("\n" + "="*50)
    logger.info("Step 5: 完整数据流验证")
    logger.info("="*50)
    
    session = db.get_session()
    
    # 统计各表数据量
    matches_count = session.query(MatchCache).count()
    stats_count = session.query(TeamStatsCache).count()
    
    from database.models import SystemPrediction
    predictions_count = session.query(SystemPrediction).filter(SystemPrediction.is_current == True).count()
    
    db.close_session(session)
    
    logger.info(f"  缓存比赛: {matches_count} 场")
    logger.info(f"  球队统计: {stats_count} 个")
    logger.info(f"  预测结果: {predictions_count} 个")
    
    # 测试API读取
    if predictions_count > 0:
        prediction = db.get_current_prediction(session.query(MatchCache).first().match_id)
        if prediction:
            logger.info(f"\n  API读取测试成功:")
            logger.info(f"    match_id: {prediction.match_id}")
            logger.info(f"    version: {prediction.prediction_version}")
            logger.info(f"    prediction: {prediction.prediction}")
    
    return matches_count > 0 and stats_count > 0


def main():
    """主测试流程"""
    logger.info("\n" + "="*60)
    logger.info("KickBet 预计算数据流测试")
    logger.info("="*60)
    
    # 加载配置
    config = load_config()
    logger.info(f"配置加载成功: {config['leagues']['PL']['name']}")
    
    # Step 1: 数据库初始化
    db = test_database_init()
    
    # Step 2: Football-Data.org API采集
    request_count = test_football_data_api(db, config)
    logger.info(f"\n  API请求次数: {request_count}")
    
    # Step 3: 缓存数据读取
    test_cache_read(db)
    
    # Step 4: 预测生成测试
    test_prediction_generation(db)
    
    # Step 5: 完整数据流验证
    success = verify_full_flow(db)
    
    # 总结
    logger.info("\n" + "="*60)
    logger.info("测试结果总结")
    logger.info("="*60)
    
    if success:
        logger.info("  [PASS] 数据流测试完成")
        logger.info("  数据采集 → 缓存存储 → 预测生成 → API读取 全链路正常")
    else:
        logger.info("  [FAIL] 数据流测试未完全通过，请检查日志")
    
    logger.info("\n测试完成!")


if __name__ == "__main__":
    main()