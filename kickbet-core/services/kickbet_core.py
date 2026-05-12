"""
KickBet核心服务
整合数据采集 → Poisson预测 → Kelly Criterion → 三方案输出

数据流:
1. 获取五大联赛即将进行的比赛 (Football-Data.org)
2. 获取球队统计数据 (主客场攻击/防守)
3. 获取实时赔率 (Odds-API.io: ML/Spread/Totals)
4. Poisson模型预测概率
5. Kelly Criterion计算价值
6. 输出三种投注方案(保守/平衡/激进)
"""

import yaml
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

# 导入采集器和预测器
from collectors.football_data_org import FootballDataOrgCollector, Match, TeamStats
from collectors.odds_api_io import OddsApiIoCollector, OddsApiIoConfig, OddsApiIoBestOdds
from predictors.poisson_predictor import PoissonPredictor, KellyCriterion, TeamAttackDefenseStats, MatchPrediction, ValueBet

logger = logging.getLogger(__name__)


@dataclass
class BettingScheme:
    """投注方案"""
    scheme_type: str  # conservative/balanced/aggressive
    scheme_name: str
    risk_level: int
    play_type: str  # 1X2/OU/AH
    play_name: str
    selection: str  # H/D/A 或 Over/Under 或 Home/Away
    odds: float
    bookmaker: str
    kelly_fraction: float
    stake_percent: float  # 占本金百分比
    confidence: str  # 高/中/低
    reason: str  # 推荐理由


@dataclass
class MatchAnalysis:
    """单场比赛完整分析"""
    match_id: str
    home_team: str
    away_team: str
    league: str
    league_name: str
    match_date: str
    
    # 胜平负预测概率
    prob_home: float
    prob_draw: float
    prob_away: float
    prediction: str  # H/D/A
    
    # 大小球预测 (新增)
    totals_prediction: Dict  # {total_goals, prob_over_2_5, prob_under_2_5, goals_distribution}
    
    # 让球盘预测 (新增)
    handicap_prediction: Dict  # {asian_0_5, asian_1_0, asian_1_5}
    
    # 比分分布 (新增)
    score_distribution: Dict  # {"2-0": 0.13, "1-0": 0.12, ...}
    
    # 赔率数据
    odds_ml: Dict  # {home, draw, away, bookmakers}
    odds_spread: Dict  # {hdp, home, away, bookmakers}
    odds_totals: Dict  # {hdp, over, under, bookmakers}
    
    # 价值评估
    value_bets: List[ValueBet]
    
    # 三种方案
    schemes: List[BettingScheme]
    
    # 预期进球
    expected_home_goals: float
    expected_away_goals: float
    most_likely_score: str


class KickBetCore:
    """KickBet核心服务"""
    
    # 五大联赛
    BIG_FIVE = ['PL', 'BL1', 'PD', 'SA', 'FL1']
    
    def __init__(self, config_path: str = None):
        """初始化"""
        # 加载配置
        if config_path is None:
            config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # 初始化采集器
        self._init_collectors()
        
        # 初始化预测器
        self.predictor = PoissonPredictor(nsim=self.config['prediction']['nsim'])
        self.kelly = KellyCriterion(
            min_edge=self.config['prediction']['min_edge'],
            max_fraction=self.config['prediction']['max_fraction']
        )
        
        # 球队统计缓存
        self._team_stats_cache: Dict[int, TeamAttackDefenseStats] = {}
        
        logger.info("KickBetCore初始化完成")
    
    def _init_collectors(self):
        """初始化数据采集器"""
        api_config = self.config['api']
        
        # Football-Data.org
        football_key = api_config['football_data']['api_key']
        if football_key:
            self.football_collector = FootballDataOrgCollector(football_key)
        else:
            self.football_collector = None
            logger.warning("未配置Football-Data.org API Key")
        
        # Odds-API.io
        odds_key = api_config['odds_api_io']['api_key']
        if odds_key:
            odds_config = OddsApiIoConfig(
                api_key=odds_key,
                free_bookmakers=api_config['odds_api_io']['free_bookmakers']
            )
            self.odds_collector = OddsApiIoCollector(odds_config)
        else:
            self.odds_collector = None
            logger.warning("未配置Odds-API.io API Key")
    
    def fetch_upcoming_matches(self, days: int = 3) -> List[Match]:
        """获取五大联赛即将进行的比赛"""
        all_matches = []
        
        for league_code in self.BIG_FIVE:
            try:
                matches = self.football_collector.get_upcoming_matches(league_code, days)
                all_matches.extend(matches)
                logger.info(f"[{league_code}] 获取到 {len(matches)} 场即将进行的比赛")
            except Exception as e:
                logger.error(f"[{league_code}] 获取比赛失败: {e}")
        
        return all_matches
    
    def fetch_team_stats(self, league_code: str) -> Dict[int, TeamAttackDefenseStats]:
        """获取联赛球队统计数据"""
        standings = self.football_collector.get_standings(league_code)
        
        stats_dict = {}
        for team in standings.standings:
            # 从积分榜计算攻击/防守统计
            stats = TeamAttackDefenseStats(
                team_id=team.team_id,
                team_name=team.team_name,
                home_scored_avg=team.goals_for_avg * 1.1,  # 主场进球略高
                home_conceded_avg=team.goals_against_avg * 0.9,  # 主场失球略低
                home_played=team.played // 2,
                away_scored_avg=team.goals_for_avg * 0.9,  # 客场进球略低
                away_conceded_avg=team.goals_against_avg * 1.1,  # 客场失球略高
                away_played=team.played // 2
            )
            stats_dict[team.team_id] = stats
        
        return stats_dict
    
    def fetch_odds_for_league(self, league_code: str) -> List[OddsApiIoBestOdds]:
        """获取联赛赔率数据"""
        league_slug = self.config['leagues'][league_code]['odds_slug']
        return self.odds_collector.get_best_odds(sport='football', league=league_slug)
    
    def analyze_match(self, match: Match, team_stats: Dict, 
                      odds: OddsApiIoBestOdds) -> MatchAnalysis:
        """分析单场比赛"""
        # 加载球队统计到预测器
        for team_id, stats in team_stats.items():
            self.predictor.set_team_stats(team_id, stats)
        
        # Poisson预测 (现在包含大小球和让球盘)
        prediction = self.predictor.predict_match(
            match_id=str(match.match_id),
            home_team=match.home_team_name,
            away_team=match.away_team_name,
            home_team_id=match.home_team_id,
            away_team_id=match.away_team_id
        )
        
        # Kelly价值评估
        odds_dict = {
            'home_odds': odds.home_odds,
            'home_bookmaker': odds.home_bookmaker,
            'draw_odds': odds.draw_odds,
            'draw_bookmaker': odds.draw_bookmaker,
            'away_odds': odds.away_odds,
            'away_bookmaker': odds.away_bookmaker,
            'market_prob_home': odds.market_prob_home,
            'market_prob_draw': odds.market_prob_draw,
            'market_prob_away': odds.market_prob_away,
            # Spread/Totals
            'spread_hdp': odds.spread_hdp,
            'spread_home_odds': odds.spread_home_odds,
            'spread_away_odds': odds.spread_away_odds,
            'totals_hdp': odds.totals_hdp,
            'totals_over_odds': odds.totals_over_odds,
            'totals_under_odds': odds.totals_under_odds
        }
        
        value_bets = self.kelly.find_value_bets(prediction, odds_dict)
        
        # 生成三种方案
        schemes = self._generate_schemes(prediction, odds_dict, value_bets)
        
        league_info = self.config['leagues'].get(match.league_code, {})
        
        # 大小球预测数据
        totals_data = None
        if prediction.totals_prediction:
            totals_data = {
                'total_goals': prediction.totals_prediction.total_goals,
                'prob_over_2_5': prediction.totals_prediction.prob_over_2_5,
                'prob_under_2_5': prediction.totals_prediction.prob_under_2_5,
                'prob_over_1_5': prediction.totals_prediction.prob_over_1_5,
                'prob_under_1_5': prediction.totals_prediction.prob_under_1_5,
                'prob_over_3_5': prediction.totals_prediction.prob_over_3_5,
                'prob_under_3_5': prediction.totals_prediction.prob_under_3_5,
                'goals_distribution': prediction.totals_prediction.goals_distribution
            }
        
        # 让球盘预测数据
        handicap_data = None
        if prediction.handicap_prediction:
            handicap_data = {
                'asian_0_5': prediction.handicap_prediction.asian_0_5,
                'asian_1_0': prediction.handicap_prediction.asian_1_0,
                'asian_1_5': prediction.handicap_prediction.asian_1_5,
                'prob_home_cover': prediction.handicap_prediction.prob_home_cover,
                'prob_away_cover': prediction.handicap_prediction.prob_away_cover
            }
        
        return MatchAnalysis(
            match_id=str(match.match_id),
            home_team=match.home_team_name,
            away_team=match.away_team_name,
            league=match.league_code,
            league_name=league_info.get('name', match.league_code),
            match_date=match.match_date,
            prob_home=prediction.prob_home,
            prob_draw=prediction.prob_draw,
            prob_away=prediction.prob_away,
            prediction=prediction.prediction,
            totals_prediction=totals_data,
            handicap_prediction=handicap_data,
            score_distribution=prediction.score_distribution,
            odds_ml={
                'home': odds.home_odds,
                'draw': odds.draw_odds,
                'away': odds.away_odds,
                'home_bm': odds.home_bookmaker,
                'draw_bm': odds.draw_bookmaker,
                'away_bm': odds.away_bookmaker
            },
            odds_spread={
                'hdp': odds.spread_hdp,
                'home': odds.spread_home_odds,
                'away': odds.spread_away_odds,
                'home_bm': odds.spread_home_bookmaker,
                'away_bm': odds.spread_away_bookmaker
            } if odds.spread_hdp else None,
            odds_totals={
                'hdp': odds.totals_hdp,
                'over': odds.totals_over_odds,
                'under': odds.totals_under_odds,
                'over_bm': odds.totals_over_bookmaker,
                'under_bm': odds.totals_under_bookmaker
            } if odds.totals_hdp else None,
            value_bets=value_bets,
            schemes=schemes,
            expected_home_goals=prediction.expected_home_goals,
            expected_away_goals=prediction.expected_away_goals,
            most_likely_score=prediction.most_likely_score
        )
    
    def _generate_schemes(self, prediction: MatchPrediction, 
                          odds: Dict, value_bets: List[ValueBet]) -> List[BettingScheme]:
        """生成三种投注方案"""
        schemes = []
        
        scheme_configs = self.config['schemes']
        
        for scheme_type, scheme_config in scheme_configs.items():
            # 根据方案类型选择最佳投注
            scheme = self._select_best_bet_for_scheme(
                scheme_type, scheme_config, prediction, odds, value_bets
            )
            if scheme:
                schemes.append(scheme)
        
        return schemes
    
    def _select_best_bet_for_scheme(self, scheme_type: str, scheme_config: Dict,
                                     prediction: MatchPrediction, odds: Dict,
                                     value_bets: List[ValueBet]) -> Optional[BettingScheme]:
        """为方案选择最佳投注"""
        # 筛选有效的价值投注
        valid_bets = [vb for vb in value_bets if vb.is_value_bet]
        
        if not valid_bets:
            # 无价值投注时，选择概率最高的结果
            max_prob_outcome = max(
                [('H', prediction.prob_home, odds['home_odds'], odds['home_bookmaker']),
                 ('D', prediction.prob_draw, odds['draw_odds'], odds['draw_bookmaker']),
                 ('A', prediction.prob_away, odds['away_odds'], odds['away_bookmaker'])],
                key=lambda x: x[1]
            )
            outcome, prob, odd, bm = max_prob_outcome
            
            # 根据方案类型调整Kelly
            max_kelly = scheme_config['max_kelly_fraction']
            kelly_fraction = min(self.kelly.calculate_kelly_fraction(prob, odd), max_kelly)
            
            return BettingScheme(
                scheme_type=scheme_type,
                scheme_name=scheme_config['name'],
                risk_level=scheme_config['risk_level'],
                play_type='1X2',
                play_name='胜平负',
                selection=outcome,
                odds=odd,
                bookmaker=bm,
                kelly_fraction=round(kelly_fraction, 4),
                stake_percent=round(kelly_fraction * 100, 2),
                confidence='中',
                reason=f"模型预测{outcome}概率{prob:.2%},赔率{odd}"
            )
        
        # 有价值投注时，根据方案类型选择
        if scheme_type == 'conservative':
            # 保守型：选择Kelly最低但仍有价值的
            bet = min(valid_bets, key=lambda x: x.kelly_fraction)
            confidence = '高' if bet.value > 0.05 else '中'
        elif scheme_type == 'aggressive':
            # 激进型：选择Kelly最高的
            bet = max(valid_bets, key=lambda x: x.kelly_fraction)
            confidence = '高' if bet.kelly_fraction > 0.15 else '中'
        else:
            # 平衡型：选择中等Kelly的
            sorted_bets = sorted(valid_bets, key=lambda x: x.kelly_fraction)
            bet = sorted_bets[len(sorted_bets) // 2]
            confidence = '高'
        
        outcome_name = {'H': '主胜', 'D': '平局', 'A': '客胜'}
        
        return BettingScheme(
            scheme_type=scheme_type,
            scheme_name=scheme_config['name'],
            risk_level=scheme_config['risk_level'],
            play_type='1X2',
            play_name='胜平负',
            selection=bet.outcome,
            odds=bet.best_odd,
            bookmaker=bet.bookmaker,
            kelly_fraction=min(bet.kelly_fraction, scheme_config['max_kelly_fraction']),
            stake_percent=round(min(bet.kelly_fraction, scheme_config['max_kelly_fraction']) * 100, 2),
            confidence=confidence,
            reason=f"价值{bet.value:.2%},模型{bet.model_prob:.2%} vs 市场{bet.market_prob:.2%}"
        )
    
    def run_daily_analysis(self, days: int = 3) -> List[MatchAnalysis]:
        """运行每日分析"""
        all_analysis = []
        
        for league_code in self.BIG_FIVE:
            try:
                # 1. 获取比赛
                matches = self.football_collector.get_upcoming_matches(league_code, days)
                
                if not matches:
                    continue
                
                # 2. 获取球队统计
                team_stats = self.fetch_team_stats(league_code)
                self.predictor.load_stats_from_standings([
                    {'team_id': s.team_id, 'team_name': s.team_name,
                     'home_scored_avg': s.home_scored_avg, 'home_conceded_avg': s.home_conceded_avg,
                     'away_scored_avg': s.away_scored_avg, 'away_conceded_avg': s.away_conceded_avg,
                     'home_played': s.home_played, 'away_played': s.away_played}
                    for s in team_stats.values()
                ])
                
                # 3. 获取赔率
                odds_list = self.fetch_odds_for_league(league_code)
                
                # 4. 匹配比赛和赔率，分析
                for match in matches:
                    # 找对应的赔率数据
                    match_odds = None
                    for odds in odds_list:
                        if self._match_teams(match, odds):
                            match_odds = odds
                            break
                    
                    if match_odds:
                        analysis = self.analyze_match(match, team_stats, match_odds)
                        all_analysis.append(analysis)
                
                logger.info(f"[{league_code}] 分析完成 {len(matches)} 场比赛")
                
            except Exception as e:
                logger.error(f"[{league_code}] 分析失败: {e}")
        
        return all_analysis
    
    def _match_teams(self, match: Match, odds: OddsApiIoBestOdds) -> bool:
        """匹配比赛和赔率的球队"""
        # 规范化球队名称比较
        def normalize(name):
            return name.replace(' FC', '').replace(' AFC', '').strip().lower()
        
        return (normalize(match.home_team_name) == normalize(odds.home_team) and
                normalize(match.away_team_name) == normalize(odds.away_team))
    
    def export_analysis(self, analyses: List[MatchAnalysis], output_path: str = None):
        """导出分析结果"""
        if output_path is None:
            output_path = 'data/analysis_output.json'
        
        import json
        import os
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 转换为可序列化的字典
        output = []
        for analysis in analyses:
            item = asdict(analysis)
            # 处理value_bets
            item['value_bets'] = [asdict(vb) for vb in analysis.value_bets]
            # 处理schemes
            item['schemes'] = [asdict(s) for s in analysis.schemes]
            output.append(item)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        logger.info(f"分析结果已导出到 {output_path}")
        return output_path


# 命令行入口
if __name__ == "__main__":
    import os
    
    # 设置环境变量或直接填入API Key
    os.environ['FOOTBALL_DATA_TOKEN'] = ""  # 需填入
    os.environ['ODDS_API_IO_KEY'] = "b74442d9ec2af9d3"
    
    # 运行分析
    core = KickBetCore()
    analyses = core.run_daily_analysis(days=3)
    
    print(f"\n分析完成: {len(analyses)} 场比赛")
    
    for analysis in analyses[:3]:
        print(f"\n{'='*50}")
        print(f"{analysis.league_name}: {analysis.home_team} vs {analysis.away_team}")
        print(f"预测: {analysis.prediction} (H{analysis.prob_home:.2%} D{analysis.prob_draw:.2%} A{analysis.prob_away:.2%})")
        print(f"预期比分: {analysis.most_likely_score}")
        print(f"\n投注方案:")
        for scheme in analysis.schemes:
            print(f"  [{scheme.scheme_name}] {scheme.play_name} → {scheme.selection}")
            print(f"    赔率: {scheme.odds} ({scheme.bookmaker})")
            print(f"    注码: {scheme.stake_percent}% 本金")
            print(f"    理由: {scheme.reason}")
    
    # 导出结果
    core.export_analysis(analyses)