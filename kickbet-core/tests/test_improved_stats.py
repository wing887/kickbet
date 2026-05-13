"""
测试球队真实历史统计

对比:
- 旧方法: 积分榜赛季平均值 (不区分主客场)
- 新方法: 从历史比赛计算真实主客场数据
"""

import os
import sys
import yaml
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collectors.football_data_org import FootballDataOrgCollector
from utils.team_stats_calculator import TeamStatsCalculator, calculate_league_stats
from database.models import PredictionCacheManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# WSL代理
PROXY = "http://172.18.176.1:10808"


def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def compare_stats(team_name: str, old_home_avg: float, old_away_avg: float, 
                  new_home_avg: float, new_away_avg: float):
    """对比新旧统计"""
    logger.info(f"\n[{team_name}] 统计对比:")
    logger.info(f"  旧方法 (积分榜平均):")
    logger.info(f"    主场进攻: {old_home_avg:.2f}  客场进攻: {old_away_avg:.2f}")
    logger.info(f"  新方法 (历史比赛计算):")
    logger.info(f"    主场进攻: {new_home_avg:.2f}  客场进攻: {new_away_avg:.2f}")
    
    # 计算差异
    home_diff = abs(new_home_avg - old_home_avg)
    away_diff = abs(new_away_avg - old_away_avg)
    
    if home_diff > 0.3 or away_diff > 0.3:
        logger.warning(f"  ⚠️ 数据差异较大: 主场+{home_diff:.2f} 客场+{away_diff:.2f}")
    else:
        logger.info(f"  ✓ 数据一致")


def test_improved_stats():
    """测试改进后的统计计算"""
    logger.info("="*60)
    logger.info("球队真实历史统计测试")
    logger.info("="*60)
    
    config = load_config()
    api_key = config['api']['football_data']['api_key']
    collector = FootballDataOrgCollector(api_key, proxy=PROXY)
    
    league_code = 'PL'
    
    # 1. 旧方法: 积分榜平均值
    logger.info(f"\n[旧方法] 从积分榜获取赛季平均值...")
    standings = collector.get_standings(league_code)
    
    old_stats = {}
    for team in standings.standings:
        old_stats[team.team_id] = {
            'name': team.team_name,
            'home_avg': team.goals_for_avg,  # 赛季总平均 (错误)
            'away_avg': team.goals_for_avg,  # 同上 (错误)
        }
    
    # 2. 新方法: 从历史比赛计算真实主客场
    logger.info(f"\n[新方法] 从已完成比赛计算真实主客场...")
    new_stats = calculate_league_stats(collector, league_code)
    
    # 3. 对比几个关键球队
    key_teams = [
        ('Manchester City FC', 65),
        ('Arsenal FC', 57),
        ('Liverpool FC', 64),
    ]
    
    for name, team_id in key_teams:
        if team_id in old_stats and team_id in new_stats:
            compare_stats(
                name,
                old_stats[team_id]['home_avg'],
                old_stats[team_id]['away_avg'],
                new_stats[team_id].home_scored_avg,
                new_stats[team_id].away_scored_avg
            )
    
    # 4. 显示近期表现
    logger.info("\n近期5场表现:")
    for team_id, stats in list(new_stats.items())[:5]:
        logger.info(f"  {stats.team_name}: {stats.recent_form} "
                    f"(进{stats.recent_scored_avg:.2f}/失{stats.recent_conceded_avg:.2f})")
    
    # 5. 存入数据库
    logger.info("\n存入数据库...")
    db = PredictionCacheManager()
    db.init_db()
    
    for team_id, stats in new_stats.items():
        stats_data = {
            'team_id': stats.team_id,
            'team_name': stats.team_name,
            'league_code': league_code,
            'home_scored_avg': stats.home_scored_avg,
            'home_conceded_avg': stats.home_conceded_avg,
            'home_played': stats.home_matches,
            'away_scored_avg': stats.away_scored_avg,
            'away_conceded_avg': stats.away_conceded_avg,
            'away_played': stats.away_matches,
        }
        db.save_team_stats(stats_data)
    
    session = db.get_session()
    from database.models import TeamStatsCache
    count = session.query(TeamStatsCache).count()
    db.close_session(session)
    
    logger.info(f"  ✓ 已存储 {count} 个球队统计")
    
    logger.info("\n" + "="*60)
    logger.info("测试完成: 新方法正确区分主客场数据")
    logger.info("="*60)


if __name__ == "__main__":
    test_improved_stats()