"""
KickBet 预计算调度服务

功能:
- 定时任务调度 (动态更新周期)
- 数据采集与缓存
- 赔率变化检测触发重新预测
- 预测结果版本管理

数据流:
1. 定时采集赔率 → 存入 odds_history
2. 检测变化 → >10% 触发重新预测
3. 运行 Poisson 预测 → 存入 system_predictions
4. 前端 API 直接读取缓存

技术栈:
- APScheduler 定时任务
- 现有 collectors + predictors 模块
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

# 导入数据库管理器
from database.models import PredictionCacheManager, MatchCache, OddsHistory, SystemPrediction, TeamStatsCache

# 导入采集器和预测器
from collectors.football_data_org import FootballDataOrgCollector
from collectors.odds_api_io import OddsApiIoCollector, OddsApiIoConfig
from predictors.poisson_predictor import PoissonPredictor, KellyCriterion, TeamAttackDefenseStats

logger = logging.getLogger(__name__)


@dataclass
class SchedulerConfig:
    """调度配置"""
    # 五大联赛
    leagues: List[str] = ['PL', 'BL1', 'PD', 'SA', 'FL1']
    
    # 更新周期 (分钟)
    base_interval: int = 10  # 基础10分钟
    
    # 动态调整阈值 (距离比赛开始的小时数)
    dynamic_intervals: Dict[int, int] = {
        24: 30,   # >24小时: 30分钟
        12: 20,   # 12-24小时: 20分钟
        6: 10,    # 6-12小时: 10分钟
        1: 5,     # 1-6小时: 5分钟
        0: 3      # <1小时: 3分钟
    }
    
    # 赔率变化阈值
    odds_change_threshold: float = 10.0  # >10% 触发重新预测
    
    # API配额限制
    max_requests_per_hour: int = 4500  # 保守估计，留buffer


class PredictionScheduler:
    """
    预计算调度器
    
    核心调度逻辑:
    - 每小时更新基础数据 (比赛、球队统计)
    - 动态周期更新赔率数据
    - 赔率变化触发重新预测
    - 预测结果缓存供前端读取
    """
    
    def __init__(self, config: SchedulerConfig, 
                 football_collector: FootballDataOrgCollector,
                 odds_collector: OddsApiIoCollector,
                 db_manager: PredictionCacheManager):
        self.config = config
        self.football_collector = football_collector
        self.odds_collector = odds_collector
        self.db_manager = db_manager
        
        # 初始化预测器
        self.predictor = PoissonPredictor(nsim=10000)
        self.kelly = KellyCriterion(min_edge=0.02, max_fraction=0.25)
        
        # 调度器
        self.scheduler = BackgroundScheduler()
        self._setup_event_handlers()
        
        # 配额追踪
        self._requests_this_hour = 0
        self._hour_reset_time = datetime.utcnow()
        
        logger.info("PredictionScheduler初始化完成")
    
    def _setup_event_handlers(self):
        """设置任务事件处理"""
        self.scheduler.add_listener(self._on_job_executed, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(self._on_job_error, EVENT_JOB_ERROR)
    
    def _on_job_executed(self, event):
        """任务执行成功"""
        logger.info(f"[Scheduler] 任务执行成功: {event.job_id}")
    
    def _on_job_error(self, event):
        """任务执行失败"""
        logger.error(f"[Scheduler] 任务执行失败: {event.job_id}, 错误: {event.exception}")
    
    def start(self):
        """启动调度器"""
        # 基础数据更新任务 (每小时)
        self.scheduler.add_job(
            self._update_base_data,
            trigger=IntervalTrigger(hours=1),
            id='update_base_data',
            name='更新基础数据(比赛、球队统计)',
            replace_existing=True
        )
        
        # 赔率更新任务 (动态周期)
        self.scheduler.add_job(
            self._update_odds_data,
            trigger=IntervalTrigger(minutes=self.config.base_interval),
            id='update_odds_data',
            name='更新赔率数据',
            replace_existing=True
        )
        
        # 配额重置任务 (每小时)
        self.scheduler.add_job(
            self._reset_quota,
            trigger=CronTrigger(minute=0),
            id='reset_quota',
            name='重置API配额计数',
            replace_existing=True
        )
        
        # 启动调度器
        self.scheduler.start()
        logger.info("[Scheduler] 调度器已启动")
        
        # 立即执行一次初始化
        logger.info("[Scheduler] 执行初始化数据更新...")
        self._update_base_data()
        self._update_odds_data()
    
    def stop(self):
        """停止调度器"""
        self.scheduler.shutdown(wait=True)
        logger.info("[Scheduler] 调度器已停止")
    
    def _check_quota(self) -> bool:
        """检查API配额是否充足"""
        now = datetime.utcnow()
        if now.hour != self._hour_reset_time.hour:
            self._reset_quota()
        
        if self._requests_this_hour >= self.config.max_requests_per_hour:
            logger.warning(f"[Quota] API配额已用完: {self._requests_this_hour}/{self.config.max_requests_per_hour}")
            return False
        
        return True
    
    def _reset_quota(self):
        """重置配额计数"""
        self._requests_this_hour = 0
        self._hour_reset_time = datetime.utcnow()
        logger.info("[Quota] API配额计数已重置")
    
    def _get_update_interval(self, match_time: datetime) -> int:
        """
        根据比赛时间获取动态更新周期
        
        返回: 分钟数
        """
        now = datetime.utcnow()
        hours_until = (match_time - now).total_seconds() / 3600
        
        if hours_until > 24:
            return 30
        elif hours_until > 12:
            return 20
        elif hours_until > 6:
            return 10
        elif hours_until > 1:
            return 5
        else:
            return 3
    
    # ==================== 数据更新任务 ====================
    
    def _update_base_data(self):
        """
        更新基础数据
        
        - 获取即将进行的比赛
        - 获取球队统计
        - 存入缓存表
        """
        logger.info("[Task] 开始更新基础数据...")
        
        if not self._check_quota():
            return
        
        for league_code in self.config.leagues:
            try:
                # 获取即将进行的比赛 (3天内)
                matches = self.football_collector.get_upcoming_matches(league_code, days=3)
                
                # 存入缓存
                for match in matches:
                    match_data = {
                        'match_id': str(match.match_id),
                        'league_code': league_code,
                        'home_team_id': match.home_team_id,
                        'home_team_name': match.home_team_name,
                        'away_team_id': match.away_team_id,
                        'away_team_name': match.away_team_name,
                        'match_time': match.match_date,
                        'status': 'SCHEDULED'
                    }
                    self.db_manager.save_match(match_data)
                    self._requests_this_hour += 1
                
                logger.info(f"[Task] [{league_code}] 更新了 {len(matches)} 场比赛")
                
                # 获取球队统计
                standings = self.football_collector.get_standings(league_code)
                for team in standings.standings:
                    stats_data = {
                        'team_id': team.team_id,
                        'team_name': team.team_name,
                        'league_code': league_code,
                        'home_scored_avg': team.goals_for_avg * 1.1,
                        'home_conceded_avg': team.goals_against_avg * 0.9,
                        'away_scored_avg': team.goals_for_avg * 0.9,
                        'away_conceded_avg': team.goals_against_avg * 1.1,
                    }
                    self.db_manager.save_team_stats(stats_data)
                
                self._requests_this_hour += 1
                
            except Exception as e:
                logger.error(f"[Task] [{league_code}] 基础数据更新失败: {e}")
        
        logger.info(f"[Task] 基础数据更新完成, API调用: {self._requests_this_hour}次")
    
    def _update_odds_data(self):
        """
        更新赔率数据
        
        - 获取最新赔率
        - 存入历史表 (带变化检测)
        - 检测是否需要触发重新预测
        """
        logger.info("[Task] 开始更新赔率数据...")
        
        if not self._check_quota():
            return
        
        # 获取缓存中的比赛
        matches = self.db_manager.get_upcoming_matches(hours=72)
        
        if not matches:
            logger.info("[Task] 无即将进行的比赛")
            return
        
        re_predict_matches = []  # 需要重新预测的比赛
        
        for league_code in self.config.leagues:
            try:
                league_matches = [m for m in matches if m.league_code == league_code]
                
                if not league_matches:
                    continue
                
                # 获取联赛赔率
                league_slug = self._get_odds_slug(league_code)
                odds_list = self.odds_collector.get_best_odds(sport='football', league=league_slug)
                self._requests_this_hour += 1
                
                for odds in odds_list:
                    # 匹配比赛
                    matched_match = self._match_odds_to_match(odds, league_matches)
                    
                    if not matched_match:
                        continue
                    
                    # 存入赔率历史
                    odds_data = {
                        'match_id': matched_match.match_id,
                        'bookmaker': odds.home_bookmaker or 'unknown',
                        'home_odds': odds.home_odds,
                        'draw_odds': odds.draw_odds,
                        'away_odds': odds.away_odds,
                    }
                    
                    saved_odds = self.db_manager.save_odds_history(odds_data)
                    self._requests_this_hour += 1
                    
                    # 检测是否需要重新预测
                    if saved_odds and saved_odds.significant_change:
                        # 检查是否超过阈值
                        needs_re_predict = self.db_manager.check_odds_change_threshold(
                            matched_match.match_id,
                            self.config.odds_change_threshold
                        )
                        
                        if needs_re_predict:
                            re_predict_matches.append(matched_match)
                            logger.info(f"[Task] [{matched_match.match_id}] 赔率变化>{self.config.odds_change_threshold}%, 触发重新预测")
                
            except Exception as e:
                logger.error(f"[Task] [{league_code}] 赔率更新失败: {e}")
        
        # 执行重新预测
        if re_predict_matches:
            self._generate_predictions(re_predict_matches, trigger_reason='odds_change')
        
        logger.info(f"[Task] 赔率更新完成, API调用: {self._requests_this_hour}次")
    
    def _get_odds_slug(self, league_code: str) -> str:
        """获取联赛在 Odds-API.io 的 slug"""
        slug_map = {
            'PL': 'england_premier_league',
            'BL1': 'germany_bundesliga',
            'PD': 'spain_la_liga',
            'SA': 'italy_serie_a',
            'FL1': 'france_ligue_one'
        }
        return slug_map.get(league_code, league_code.lower())
    
    def _match_odds_to_match(self, odds, matches: List[MatchCache]) -> Optional[MatchCache]:
        """匹配赔率数据到比赛"""
        def normalize(name):
            return name.replace(' FC', '').replace(' AFC', '').strip().lower()
        
        for match in matches:
            if normalize(match.home_team_name) == normalize(odds.home_team) and \
               normalize(match.away_team_name) == normalize(odds.away_team):
                return match
        
        return None
    
    # ==================== 预测生成 ====================
    
    def _generate_predictions(self, matches: List[MatchCache], trigger_reason: str = 'first_generation'):
        """
        生成预测结果
        
        - 运行 Poisson 模型
        - 计算 Kelly 比例
        - 存入版本管理表
        """
        logger.info(f"[Predict] 开始生成预测 ({trigger_reason}), {len(matches)}场比赛")
        
        # 获取所有球队统计
        all_stats = self.db_manager.get_all_team_stats()
        
        # 加载到预测器
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
            self.predictor.set_team_stats(team_id, team_stats)
        
        for match in matches:
            try:
                # 获取最新赔率
                latest_odds = self.db_manager.get_latest_odds(match.match_id)
                
                if not latest_odds:
                    logger.warning(f"[Predict] [{match.match_id}] 无赔率数据, 跳过")
                    continue
                
                # 运行 Poisson 预测
                prediction = self.predictor.predict_match(
                    match_id=match.match_id,
                    home_team=match.home_team_name,
                    away_team=match.away_team_name,
                    home_team_id=match.home_team_id,
                    away_team_id=match.away_team_id
                )
                
                # 构建 Kelly 输入
                odds_dict = {
                    'home_odds': latest_odds.home_odds,
                    'draw_odds': latest_odds.draw_odds,
                    'away_odds': latest_odds.away_odds,
                    'home_bookmaker': latest_odds.bookmaker,
                    'draw_bookmaker': latest_odds.bookmaker,
                    'away_bookmaker': latest_odds.bookmaker,
                    'market_prob_home': latest_odds.market_prob_home,
                    'market_prob_draw': latest_odds.market_prob_draw,
                    'market_prob_away': latest_odds.market_prob_away
                }
                
                # 计算 Kelly
                value_bets = self.kelly.find_value_bets(prediction, odds_dict)
                
                # 构建预测数据
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
                    'total_goals_expected': prediction.totals_prediction.total_goals if prediction.totals_prediction else None,
                    'prob_over_2_5': prediction.totals_prediction.prob_over_2_5 if prediction.totals_prediction else None,
                    'prob_under_2_5': prediction.totals_prediction.prob_under_2_5 if prediction.totals_prediction else None,
                    'prob_home_cover_0_5': prediction.handicap_prediction.prob_home_cover if prediction.handicap_prediction else None,
                    'prob_away_cover_0_5': prediction.handicap_prediction.prob_away_cover if prediction.handicap_prediction else None,
                    # Kelly 数据
                    'kelly_home': value_bets[0].kelly_fraction if value_bets else None,
                    'kelly_draw': value_bets[1].kelly_fraction if len(value_bets) > 1 else None,
                    'kelly_away': value_bets[2].kelly_fraction if len(value_bets) > 2 else None,
                    'best_home_odds': latest_odds.home_odds,
                    'best_draw_odds': latest_odds.draw_odds,
                    'best_away_odds': latest_odds.away_odds,
                    'best_bookmaker_home': latest_odds.bookmaker,
                    'best_bookmaker_draw': latest_odds.bookmaker,
                    'best_bookmaker_away': latest_odds.bookmaker,
                    # 详细数据 (JSON)
                    'score_distribution': prediction.score_distribution,
                    'totals_prediction': {
                        'total_goals': prediction.totals_prediction.total_goals,
                        'prob_over_2_5': prediction.totals_prediction.prob_over_2_5,
                        'prob_over_1_5': prediction.totals_prediction.prob_over_1_5,
                        'prob_over_3_5': prediction.totals_prediction.prob_over_3_5,
                        'goals_distribution': prediction.totals_prediction.goals_distribution
                    } if prediction.totals_prediction else {},
                    'handicap_prediction': {
                        'asian_0_5': prediction.handicap_prediction.asian_0_5,
                        'asian_1_0': prediction.handicap_prediction.asian_1_0,
                        'asian_1_5': prediction.handicap_prediction.asian_1_5
                    } if prediction.handicap_prediction else {},
                    'value_bets': [
                        {
                            'outcome': vb.outcome,
                            'model_prob': vb.model_prob,
                            'market_prob': vb.market_prob,
                            'best_odd': vb.best_odd,
                            'kelly_fraction': vb.kelly_fraction,
                            'value': vb.value,
                            'is_value_bet': vb.is_value_bet
                        } for vb in value_bets
                    ]
                }
                
                # 存入版本管理表
                self.db_manager.save_prediction(prediction_data, trigger_reason)
                
                logger.info(f"[Predict] [{match.match_id}] 预测已保存: {prediction.prediction} (H{prediction.prob_home:.2%} D{prediction.prob_draw:.2%} A{prediction.prob_away:.2%})")
                
            except Exception as e:
                logger.error(f"[Predict] [{match.match_id}] 预测生成失败: {e}")
        
        logger.info(f"[Predict] 预测生成完成")
    
    def generate_predictions_for_new_matches(self):
        """
        为新增比赛生成预测
        
        检查哪些比赛还没有预测，生成首次预测
        """
        # 获取有赔率但没有预测的比赛
        matches = self.db_manager.get_upcoming_matches(hours=72)
        
        new_matches = []
        for match in matches:
            if not self.db_manager.has_prediction(match.match_id):
                # 检查是否有赔率
                if self.db_manager.get_latest_odds(match.match_id):
                    new_matches.append(match)
        
        if new_matches:
            logger.info(f"[Predict] 发现 {len(new_matches)} 场新比赛需要预测")
            self._generate_predictions(new_matches, trigger_reason='first_generation')
    
    def manual_refresh_prediction(self, match_id: str) -> Optional[SystemPrediction]:
        """
        手动刷新预测
        
        用户/管理员手动触发重新预测
        """
        match = self.db_manager.get_match_by_id(match_id)
        
        if not match:
            logger.warning(f"[Predict] 比赛不存在: {match_id}")
            return None
        
        self._generate_predictions([match], trigger_reason='manual_refresh')
        
        return self.db_manager.get_current_prediction(match_id)


# ==================== 初始化函数 ====================

def create_scheduler(config_path: str = None) -> PredictionScheduler:
    """
    创建调度器实例
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        PredictionScheduler实例
    """
    import yaml
    from pathlib import Path
    
    # 加载配置
    if config_path is None:
        config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 初始化采集器
    api_config = config['api']
    
    football_collector = FootballDataOrgCollector(
        api_config['football_data']['api_key']
    )
    
    odds_config = OddsApiIoConfig(
        api_key=api_config['odds_api_io']['api_key'],
        free_bookmakers=api_config['odds_api_io']['free_bookmakers']
    )
    odds_collector = OddsApiIoCollector(odds_config)
    
    # 初始化数据库管理器
    db_manager = PredictionCacheManager()
    db_manager.init_db()
    
    # 创建调度器
    scheduler_config = SchedulerConfig()
    
    return PredictionScheduler(
        config=scheduler_config,
        football_collector=football_collector,
        odds_collector=odds_collector,
        db_manager=db_manager
    )


if __name__ == "__main__":
    import os
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 需要设置环境变量或配置文件中的API Key
    print("预计算调度服务")
    print("=" * 50)
    print("使用方法:")
    print("  scheduler = create_scheduler()")
    print("  scheduler.start()  # 启动调度")
    print("  scheduler.stop()   # 停止调度")
    print("=" * 50)
    
    # 初始化数据库
    db_manager = PredictionCacheManager()
    db_manager.init_db()
    
    print("\n[DB] 数据库表已创建:")
    print("  - matches_cache")
    print("  - odds_history")
    print("  - system_predictions")
    print("  - team_stats_cache")