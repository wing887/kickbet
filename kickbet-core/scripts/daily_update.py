"""
KickBet 每日数据更新脚本

功能:
- 同步昨日比赛结果
- 更新球队统计
- 同步今日比赛数据
- 更新历史比赛数据库

用法:
    python scripts/daily_update.py [--dry-run]

定时任务:
    建议每天凌晨4点运行: 0 4 * * *
"""

import argparse
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.history_models import HistoryDBManager
from services.history_sync_service import HistorySyncService
from collectors.football_data_org import FootballDataOrgCollector
from database.models import PredictionCacheManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# WSL代理配置
PROXY_URL = 'http://172.18.176.1:10808'
FOOTBALL_DATA_API_TOKEN = '84e1509844e14a469520d5ed4fb7f148'


def sync_yesterday_results(db: HistoryDBManager, dry_run: bool = False):
    """同步昨日比赛结果"""
    yesterday = datetime.now() - timedelta(days=1)
    yesterday_str = yesterday.strftime('%Y-%m-%d')
    
    logger.info(f"[每日更新] 同步昨日比赛结果: {yesterday_str}")
    
    if dry_run:
        logger.info("[DRY-RUN] 跳过实际同步")
        return
    
    # 使用Football-Data.org采集器获取已完成比赛
    collector = FootballDataOrgCollector(
        api_token=FOOTBALL_DATA_API_TOKEN,
        proxy_url=PROXY_URL
    )
    
    # 五大联赛 + 欧冠
    leagues = ['PL', 'BL1', 'PD', 'SA', 'FL1', 'CL']
    
    updated_count = 0
    for league_code in leagues:
        try:
            # 获取最近比赛（包括已完成的）
            matches = collector.get_matches(league_code, status='FINISHED')
            
            if matches:
                # 更新历史数据库
                sync_service = HistorySyncService(db)
                season_id = db.get_current_season_id(league_code)
                
                if season_id:
                    for match in matches:
                        # 检查是否是昨日的比赛
                        match_date = match.get('utcDate', '')
                        if match_date.startswith(yesterday_str):
                            # 更新比赛结果
                            result = db.update_match_result(
                                match['id'],
                                match['score']['fullTime']['home'],
                                match['score']['fullTime']['away'],
                                status='FINISHED'
                            )
                            if result:
                                updated_count += 1
                                logger.info(f"更新比赛: {match['homeTeam']['name']} vs {match['awayTeam']['name']} ({match['score']['fullTime']['home']}-{match['score']['fullTime']['away']})")
            
        except Exception as e:
            logger.error(f"[每日更新] 同步 {league_code} 失败: {e}")
    
    logger.info(f"[每日更新] 共更新 {updated_count} 场比赛结果")


def sync_today_matches(db: HistoryDBManager, dry_run: bool = False):
    """同步今日比赛数据"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    logger.info(f"[每日更新] 同步今日比赛: {today}")
    
    if dry_run:
        logger.info("[DRY-RUN] 跳过实际同步")
        return
    
    # 使用同步服务
    sync_service = HistorySyncService(db)
    
    # 五大联赛 + 欧冠
    leagues = ['PL', 'BL1', 'PD', 'SA', 'FL1', 'CL']
    
    synced_count = 0
    for league_code in leagues:
        try:
            season_id = db.get_current_season_id(league_code)
            if season_id:
                count = sync_service.sync_matches(league_code, season_id)
                synced_count += count
        except Exception as e:
            logger.error(f"[每日更新] 同步 {league_code} 今日比赛失败: {e}")
    
    logger.info(f"[每日更新] 共同步 {synced_count} 场新比赛")


def update_team_stats(db: HistoryDBManager, dry_run: bool = False):
    """更新球队统计缓存"""
    logger.info("[每日更新] 更新球队统计缓存")
    
    if dry_run:
        logger.info("[DRY-RUN] 跳过实际更新")
        return
    
    # 重新计算所有球队的统计
    # 这些统计会被Poisson预测器加载
    session = db.get_session()
    try:
        from database.history_models import Team
        
        teams = session.query(Team).limit(50).all()
        
        updated = 0
        for team in teams:
            stats = db.get_team_stats_from_history(team.team_id)
            if stats:
                updated += 1
        
        logger.info(f"[每日更新] 更新 {updated} 个球队统计")
        
    finally:
        session.close()


def clear_old_predictions(cache_db: PredictionCacheManager, dry_run: bool = False):
    """清理过期预测"""
    logger.info("[每日更新] 清理过期预测缓存")
    
    if dry_run:
        logger.info("[DRY-RUN] 跳过清理")
        return
    
    # 清理7天前的预测
    cutoff_date = datetime.now() - timedelta(days=7)
    
    session = cache_db.get_session()
    try:
        from database.models import SystemPrediction
        
        old_predictions = session.query(SystemPrediction).filter(
            SystemPrediction.created_at < cutoff_date
        ).all()
        
        count = len(old_predictions)
        for pred in old_predictions:
            session.delete(pred)
        
        session.commit()
        logger.info(f"[每日更新] 清理 {count} 条过期预测")
        
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(description='KickBet每日数据更新')
    parser.add_argument('--dry-run', action='store_true', help='仅显示计划，不执行')
    args = parser.parse_args()
    
    logger.info("="*60)
    logger.info(f"KickBet 每日数据更新 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    if args.dry_run:
        logger.info("[DRY-RUN 模式] 不执行实际操作")
    logger.info("="*60)
    
    # 初始化数据库
    history_db = HistoryDBManager()
    cache_db = PredictionCacheManager()
    
    # 执行更新任务
    sync_yesterday_results(history_db, args.dry_run)
    sync_today_matches(history_db, args.dry_run)
    update_team_stats(history_db, args.dry_run)
    clear_old_predictions(cache_db, args.dry_run)
    
    logger.info("="*60)
    logger.info("[每日更新] 完成!")
    logger.info("="*60)


if __name__ == '__main__':
    main()