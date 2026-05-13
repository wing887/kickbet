"""
Poisson预测引擎
基于DataScienceProjects的R代码移植

核心算法:
1. Poisson进球模型:
   - λ_home = 0.5 × (主队主场平均进球 + 客队客场平均失球)
   - λ_away = 0.5 × (客队客场平均进球 + 主队主场平均失球)

2. Monte Carlo模拟: 10000次模拟计算H/D/A概率

3. Kelly Criterion: fraction = (prob × max_odd - (1-prob)) / max_odd
"""

import random
import math
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging

# 纯Python Poisson分布实现（Knuth算法）
def poisson_sample(lambda_param: float) -> int:
    """
    使用Knuth算法生成Poisson分布随机数
    
    Algorithm:
    - L = exp(-lambda)
    - k = 0, p = 1
    - while p > L: k++, p *= random()
    - return k-1
    """
    if lambda_param <= 0:
        return 0
    
    L = math.exp(-lambda_param)
    k = 0
    p = 1.0
    
    while p > L:
        k += 1
        p *= random.random()
    
    return k - 1

logger = logging.getLogger(__name__)


@dataclass
class TeamAttackDefenseStats:
    """球队攻击/防守统计数据"""
    team_id: int
    team_name: str
    # 主场统计
    home_scored_avg: float  # 主场场均进球
    home_conceded_avg: float  # 主场场均失球
    home_played: int
    # 客场统计
    away_scored_avg: float  # 客场场均进球
    away_conceded_avg: float  # 客场场均失球
    away_played: int


@dataclass
class TotalsPrediction:
    """大小球预测结果"""
    total_goals: float  # 预期总进球
    # 常用盘口线概率
    prob_over_2_5: float  # 大于2.5球概率
    prob_under_2_5: float  # 小于2.5球概率
    prob_over_1_5: float  # 大于1.5球概率
    prob_under_1_5: float  # 小于1.5球概率
    prob_over_3_5: float  # 大于3.5球概率
    prob_under_3_5: float  # 小于3.5球概率
    # 详细分布
    goals_distribution: Dict[int, float]  # 各总进球数的概率 {0: 0.05, 1: 0.15, ...}


@dataclass  
class HandicapPrediction:
    """让球盘预测结果"""
    handicap: float  # 盘口值 (正数=主队让球)
    # 让球后结果概率
    prob_home_cover: float  # 主队赢盘概率
    prob_away_cover: float  # 客队赢盘概率
    prob_draw_handicap: float  # 走水概率 (盘口整数时)
    # 常用盘口
    asian_0_5: Dict[str, float]  # 主队-0.5盘口概率
    asian_1_0: Dict[str, float]  # 主队-1.0盘口概率
    asian_1_5: Dict[str, float]  # 主队-1.5盘口概率


@dataclass
class H2HPrediction:
    """历史交锋预测数据"""
    total_matches: int
    home_wins: int  # 主队胜场数 (作为主队)
    away_wins: int  # 客队胜场数 (作为客队时的胜场)
    draws: int
    home_win_rate: float
    away_win_rate: float
    draw_rate: float
    avg_home_goals: float  # 主队交锋场均进球
    avg_away_goals: float  # 客队交锋场均进球
    avg_total_goals: float
    recent_results: List[str]  # 最近交锋结果 ['W','D','L'...]
    # H2H加权概率 (基于历史交锋)
    h2h_prob_home: float
    h2h_prob_draw: float
    h2h_prob_away: float


@dataclass
class MatchPrediction:
    """比赛预测结果"""
    match_id: str
    home_team: str
    away_team: str
    # Poisson模型概率 (胜平负)
    prob_home: float
    prob_draw: float
    prob_away: float
    # 预测结果
    prediction: str  # H/D/A
    # 预期进球
    expected_home_goals: float
    expected_away_goals: float
    # 最可能比分
    most_likely_score: str
    # 比分分布 (扩展)
    score_distribution: Dict[str, float]  # 各比分概率 {"0-0": 0.05, "1-0": 0.12, ...}
    # 大小球预测 (扩展)
    totals_prediction: TotalsPrediction = None
    # 让球盘预测 (扩展)
    handicap_prediction: HandicapPrediction = None
    # 历史交锋预测 (新增)
    h2h_prediction: H2HPrediction = None
    # 综合预测概率 (融合Poisson + H2H)
    combined_prob_home: float = 0.0
    combined_prob_draw: float = 0.0
    combined_prob_away: float = 0.0


@dataclass
class ValueBet:
    """价值投注"""
    match_id: str
    home_team: str
    away_team: str
    outcome: str  # H/D/A
    # 模型概率 vs 市场概率
    model_prob: float
    market_prob: float
    # 最优赔率
    best_odd: float
    bookmaker: str
    # Kelly比例
    kelly_fraction: float
    # 价值评估
    value: float  # model_prob - market_prob
    is_value_bet: bool  # 是否为价值投注


class PoissonPredictor:
    """
    Poisson进球预测引擎
    
    基于球队主客场攻击/防守统计，使用Poisson分布模拟比赛结果
    """
    
    def __init__(self, nsim: int = 10000):
        """
        Args:
            nsim: Monte Carlo模拟次数，默认10000
        """
        self.nsim = nsim
        # 球队统计缓存
        self._team_stats: Dict[int, TeamAttackDefenseStats] = {}
        
        logger.info(f"PoissonPredictor初始化, 模拟次数={nsim}")
    
    def set_team_stats(self, team_id: int, stats: TeamAttackDefenseStats):
        """设置球队统计数据"""
        self._team_stats[team_id] = stats
    
    def load_stats_from_standings(self, standings: List[Dict]):
        """
        从积分榜数据加载统计 (旧方法，不区分主客场)
        
        Args:
            standings: 积分榜数据列表
        """
        for team in standings:
            stats = TeamAttackDefenseStats(
                team_id=team['team_id'],
                team_name=team['team_name'],
                home_scored_avg=team.get('home_scored_avg', team.get('goals_for_avg', 1.5)),
                home_conceded_avg=team.get('home_conceded_avg', team.get('goals_against_avg', 1.0)),
                home_played=team.get('home_played', team.get('played', 0) // 2),
                away_scored_avg=team.get('away_scored_avg', team.get('goals_for_avg', 1.2)),
                away_conceded_avg=team.get('away_conceded_avg', team.get('goals_against_avg', 1.3)),
                away_played=team.get('away_played', team.get('played', 0) // 2)
            )
            self._team_stats[team['team_id']] = stats
        
        logger.info(f"加载了 {len(self._team_stats)} 个球队的统计数据")
    
    def load_stats_from_history_db(self, db_manager, league_code: str = None, 
                                    season_id: int = None, team_names: List[str] = None):
        """
        从历史比赛数据库加载球队统计 (推荐方法)
        
        Args:
            db_manager: HistoryDBManager实例
            league_code: 联赛代码 (可选，用于筛选)
            season_id: 赛季ID (可选，指定赛季)
            team_names: 球队名称列表 (可选，只加载指定球队)
        
        Returns:
            加载的球队数量
        """
        from database.history_models import Team
        
        session = db_manager.get_session()
        try:
            # 查询球队
            query = session.query(Team)
            if team_names:
                # 按名称过滤
                query = query.filter(Team.name.in_(team_names))
            
            teams = query.all()
            
            loaded_count = 0
            for team in teams:
                # 从历史比赛计算统计
                stats_dict = db_manager.get_team_stats_from_history(
                    team.team_id, 
                    season_id=season_id
                )
                
                if 'error' in stats_dict:
                    continue
                
                # 创建统计对象
                stats = TeamAttackDefenseStats(
                    team_id=team.team_id,
                    team_name=team.name,
                    home_scored_avg=stats_dict.get('home_scored_avg', 1.5),
                    home_conceded_avg=stats_dict.get('home_conceded_avg', 1.0),
                    home_played=stats_dict.get('home_matches', 0),
                    away_scored_avg=stats_dict.get('away_scored_avg', 1.2),
                    away_conceded_avg=stats_dict.get('away_conceded_avg', 1.3),
                    away_played=stats_dict.get('away_matches', 0)
                )
                
                self._team_stats[team.team_id] = stats
                loaded_count += 1
            
            logger.info(f"[HistoryDB] 加载了 {loaded_count} 个球队的真实主客场统计")
            return loaded_count
            
        finally:
            session.close()
    
    def calculate_expected_goals(self, home_team_id: int, away_team_id: int) -> Tuple[float, float]:
        """
        计算预期进球数
        
        核心公式:
        λ_home = 0.5 × (主队主场平均进球 + 客队客场平均失球)
        λ_away = 0.5 × (客队客场平均进球 + 主队主场平均失球)
        
        Args:
            home_team_id: 主队ID
            away_team_id: 客队ID
            
        Returns:
            (预期主队进球, 预期客队进球)
        """
        home_stats = self._team_stats.get(home_team_id)
        away_stats = self._team_stats.get(away_team_id)
        
        if not home_stats or not away_stats:
            # 使用默认值
            logger.warning(f"缺少球队统计: home={home_team_id}, away={away_team_id}")
            return (1.5, 1.2)
        
        # Poisson λ 计算
        lambda_home = 0.5 * (home_stats.home_scored_avg + away_stats.away_conceded_avg)
        lambda_away = 0.5 * (away_stats.away_scored_avg + home_stats.home_conceded_avg)
        
        return (lambda_home, lambda_away)
    
    def simulate_match(self, lambda_home: float, lambda_away: float) -> Tuple[Dict[str, float], Dict[str, float], Dict[int, float]]:
        """
        Monte Carlo模拟比赛
        
        Args:
            lambda_home: 主队进球期望
            lambda_away: 客队进球期望
            
        Returns:
            (结果概率, 比分分布, 总进球分布)
            - 结果概率: {'H': 主胜概率, 'D': 平局概率, 'A': 客胜概率}
            - 比分分布: {'0-0': 0.05, '1-0': 0.12, ...}
            - 总进球分布: {0: 0.05, 1: 0.15, 2: 0.28, ...}
        """
        results = {'H': 0, 'D': 0, 'A': 0}
        score_counts = {}
        total_goals_counts = {}
        
        for _ in range(self.nsim):
            # Poisson随机生成进球（使用Knuth算法）
            home_goals = poisson_sample(lambda_home)
            away_goals = poisson_sample(lambda_away)
            
            # 记录比分频率
            score_key = f"{home_goals}-{away_goals}"
            score_counts[score_key] = score_counts.get(score_key, 0) + 1
            
            # 记录总进球数
            total_goals = home_goals + away_goals
            total_goals_counts[total_goals] = total_goals_counts.get(total_goals, 0) + 1
            
            # 判断结果
            if home_goals > away_goals:
                results['H'] += 1
            elif home_goals == away_goals:
                results['D'] += 1
            else:
                results['A'] += 1
        
        # 转换为概率
        probs = {
            'H': results['H'] / self.nsim,
            'D': results['D'] / self.nsim,
            'A': results['A'] / self.nsim
        }
        
        # 比分概率分布
        score_probs = {k: v / self.nsim for k, v in score_counts.items()}
        
        # 总进球概率分布
        total_goals_probs = {k: v / self.nsim for k, v in total_goals_counts.items()}
        
        return probs, score_probs, total_goals_probs
    
    def predict_match(self, match_id: str, home_team: str, away_team: str,
                      home_team_id: int, away_team_id: int) -> MatchPrediction:
        """
        预测单场比赛
        
        Args:
            match_id: 比赛ID
            home_team: 主队名称
            away_team: 客队名称
            home_team_id: 主队ID
            away_team_id: 客队ID
            
        Returns:
            MatchPrediction预测结果 (包含胜平负、大小球、让球盘预测)
        """
        # 计算预期进球
        lambda_home, lambda_away = self.calculate_expected_goals(home_team_id, away_team_id)
        
        # Monte Carlo模拟 (返回完整分布)
        probs, score_probs, total_goals_probs = self.simulate_match(lambda_home, lambda_away)
        
        # 结果校准
        prediction = self._calibrate_result(probs['H'], probs['D'], probs['A'])
        
        # 最可能比分
        most_likely_score = max(score_probs, key=score_probs.get)
        
        # 计算大小球预测
        totals_pred = self._calculate_totals_prediction(lambda_home, lambda_away, total_goals_probs)
        
        # 计算让球盘预测
        handicap_pred = self._calculate_handicap_prediction(score_probs)
        
        return MatchPrediction(
            match_id=match_id,
            home_team=home_team,
            away_team=away_team,
            prob_home=round(probs['H'], 4),
            prob_draw=round(probs['D'], 4),
            prob_away=round(probs['A'], 4),
            prediction=prediction,
            expected_home_goals=round(lambda_home, 2),
            expected_away_goals=round(lambda_away, 2),
            most_likely_score=most_likely_score,
            score_distribution={k: round(v, 4) for k, v in score_probs.items()},
            totals_prediction=totals_pred,
            handicap_prediction=handicap_pred
        )
    
    def predict_match_with_h2h(self, match_id: str, home_team: str, away_team: str,
                                home_team_id: int, away_team_id: int,
                                h2h_stats: Dict, h2h_weight: float = 0.25,
                                h2h_threshold: int = 5) -> MatchPrediction:
        """
        预测单场比赛 (包含历史交锋数据融合)
        
        改进版策略 (基于回测验证):
        - λ始终使用主客场综合计算 (不替换)
        - H2H作为可选融合因子
        - 仅当交锋场次 >= threshold 时启用融合
        - 自适应权重: 样本越大权重越高
        
        Args:
            match_id: 比赛ID
            home_team: 主队名称
            away_team: 客队名称
            home_team_id: 主队ID
            away_team_id: 客队ID
            h2h_stats: 历史交锋统计数据 (from get_head_to_head_stats)
            h2h_weight: H2H基础权重 (0-0.5, 默认0.25表示25%权重)
            h2h_threshold: H2H启用阈值 (默认5场，小于此不融合)
            
        Returns:
            MatchPrediction预测结果 (包含融合后的概率)
            
        回测验证结果:
        - threshold=1时H2H准确率36.1% (低于Poisson 48.2%)
        - threshold=3时无触发 (样本不足)
        - 建议: threshold>=5才有足够样本稳定性
        """
        # 先执行基础预测 (λ使用主客场综合)
        base_pred = self.predict_match(match_id, home_team, away_team, home_team_id, away_team_id)
        
        total_matches = h2h_stats.get('total_matches', 0)
        
        # 如果无H2H数据或场次不足，返回基础预测
        if total_matches < h2h_threshold:
            logger.info(f"[H2H跳过] 交锋{total_matches}场 < 阈值{h2h_threshold}场，仅用Poisson")
            return base_pred
        
        # 自适应权重: 样本越大权重越高
        # 5场: 15%, 10场: 25%, 15场: 35%, 20+场: 45%
        adaptive_weight = min(0.45, h2h_weight + (total_matches - h2h_threshold) * 0.02)
        
        # 计算H2H概率 (从历史交锋计算)
        h2h_prob_home = h2h_stats['team_a_win_rate']
        h2h_prob_draw = h2h_stats['draw_rate']
        h2h_prob_away = h2h_stats['team_b_win_rate']
        
        # 创建H2H预测对象
        home_as_home_wins = h2h_stats.get('team_a_as_home_wins', 0)
        home_as_away_wins = h2h_stats.get('team_a_as_away_wins', 0)
        
        h2h_pred = H2HPrediction(
            total_matches=total_matches,
            home_wins=home_as_home_wins,
            away_wins=home_as_away_wins,
            draws=h2h_stats['draws'],
            home_win_rate=h2h_prob_home,
            away_win_rate=h2h_prob_away,
            draw_rate=h2h_prob_draw,
            avg_home_goals=h2h_stats['avg_team_a_goals'],
            avg_away_goals=h2h_stats['avg_team_b_goals'],
            avg_total_goals=h2h_stats['avg_total_goals'],
            recent_results=h2h_stats['recent_results'],
            h2h_prob_home=round(h2h_prob_home, 4),
            h2h_prob_draw=round(h2h_prob_draw, 4),
            h2h_prob_away=round(h2h_prob_away, 4)
        )
        
        # 融合概率: weighted average of Poisson + H2H
        # combined = (1 - weight) * poisson + weight * h2h
        poisson_weight = 1 - adaptive_weight
        
        combined_home = round(poisson_weight * base_pred.prob_home + adaptive_weight * h2h_prob_home, 4)
        combined_draw = round(poisson_weight * base_pred.prob_draw + adaptive_weight * h2h_prob_draw, 4)
        combined_away = round(poisson_weight * base_pred.prob_away + adaptive_weight * h2h_prob_away, 4)
        
        # 更新预测结果
        logger.info(f"[H2H融合] Poisson: H={base_pred.prob_home:.1%} D={base_pred.prob_draw:.1%} A={base_pred.prob_away:.1%}")
        logger.info(f"[H2H融合] H2H({total_matches}场): H={h2h_prob_home:.1%} D={h2h_prob_draw:.1%} A={h2h_prob_away:.1%}")
        logger.info(f"[H2H融合] 综合({adaptive_weight:.0%}权重): H={combined_home:.1%} D={combined_draw:.1%} A={combined_away:.1%}")
        
        # 返回融合预测
        return MatchPrediction(
            match_id=match_id,
            home_team=home_team,
            away_team=away_team,
            prob_home=base_pred.prob_home,
            prob_draw=base_pred.prob_draw,
            prob_away=base_pred.prob_away,
            prediction=self._calibrate_result(combined_home, combined_draw, combined_away),
            expected_home_goals=base_pred.expected_home_goals,
            expected_away_goals=base_pred.expected_away_goals,
            most_likely_score=base_pred.most_likely_score,
            score_distribution=base_pred.score_distribution,
            totals_prediction=base_pred.totals_prediction,
            handicap_prediction=base_pred.handicap_prediction,
            h2h_prediction=h2h_pred,
            combined_prob_home=combined_home,
            combined_prob_draw=combined_draw,
            combined_prob_away=combined_away
        )
    
    def _calibrate_result(self, prob_h: float, prob_d: float, prob_a: float) -> str:
        """
        结果校准
        
        如果主胜和客胜概率差距<0.01，预测为平局
        """
        if abs(prob_h - prob_a) < 0.01:
            return 'D'
        
        max_prob = max(prob_h, prob_d, prob_a)
        if prob_h == max_prob:
            return 'H'
        elif prob_d == max_prob:
            return 'D'
        else:
            return 'A'
    
    def _calculate_totals_prediction(self, lambda_home: float, lambda_away: float,
                                       total_goals_probs: Dict[int, float]) -> TotalsPrediction:
        """
        计算大小球预测
        
        从总进球分布中提取各盘口线的概率
        
        Args:
            lambda_home: 主队预期进球
            lambda_away: 客队预期进球
            total_goals_probs: 总进球概率分布
            
        Returns:
            TotalsPrediction 大小球预测结果
        """
        # 预期总进球
        total_goals = lambda_home + lambda_away
        
        # 计算各盘口线的概率
        # 盘口线 X.5: 大球 = 进球数 > X
        prob_over_2_5 = sum(p for goals, p in total_goals_probs.items() if goals > 2)
        prob_under_2_5 = sum(p for goals, p in total_goals_probs.items() if goals <= 2)
        
        prob_over_1_5 = sum(p for goals, p in total_goals_probs.items() if goals > 1)
        prob_under_1_5 = sum(p for goals, p in total_goals_probs.items() if goals <= 1)
        
        prob_over_3_5 = sum(p for goals, p in total_goals_probs.items() if goals > 3)
        prob_under_3_5 = sum(p for goals, p in total_goals_probs.items() if goals <= 3)
        
        # 格式化总进球分布 (只保留概率>1%的)
        goals_dist = {k: round(v, 4) for k, v in total_goals_probs.items() if v > 0.01}
        
        return TotalsPrediction(
            total_goals=round(total_goals, 2),
            prob_over_2_5=round(prob_over_2_5, 4),
            prob_under_2_5=round(prob_under_2_5, 4),
            prob_over_1_5=round(prob_over_1_5, 4),
            prob_under_1_5=round(prob_under_1_5, 4),
            prob_over_3_5=round(prob_over_3_5, 4),
            prob_under_3_5=round(prob_under_3_5, 4),
            goals_distribution=goals_dist
        )
    
    def _calculate_handicap_prediction(self, score_probs: Dict[str, float]) -> HandicapPrediction:
        """
        计算让球盘预测
        
        从比分分布中计算让球后的结果概率
        
        Args:
            score_probs: 比分概率分布
            
        Returns:
            HandicapPrediction 让球盘预测结果
        """
        # 计算常用亚洲盘口概率
        
        # 主队 -0.5 盘口: 主队必须赢才能赢盘
        # 赢盘条件: home_goals > away_goals (净胜>=1)
        asian_0_5_home = sum(p for score, p in score_probs.items() 
                            if int(score.split('-')[0]) > int(score.split('-')[1]))
        asian_0_5_away = sum(p for score, p in score_probs.items() 
                            if int(score.split('-')[0]) <= int(score.split('-')[1]))
        
        # 主队 -1.0 盘口: 
        # 赢盘条件: home_goals - away_goals >= 1 (净胜>=1)
        # 走水条件: home_goals - away_goals == 1 (净胜=1) → 这个是赢盘！
        # 实际上 -1.0 盘口：赢盘需要净胜>=2，走水是净胜=1
        asian_1_0_home = sum(p for score, p in score_probs.items()
                            if int(score.split('-')[0]) - int(score.split('-')[1]) >= 2)
        asian_1_0_draw = sum(p for score, p in score_probs.items()
                            if int(score.split('-')[0]) - int(score.split('-')[1]) == 1)
        asian_1_0_away = sum(p for score, p in score_probs.items()
                            if int(score.split('-')[0]) - int(score.split('-')[1]) <= 0)
        
        # 主队 -1.5 盘口: 主队净胜>=2才能赢盘
        asian_1_5_home = sum(p for score, p in score_probs.items()
                            if int(score.split('-')[0]) - int(score.split('-')[1]) >= 2)
        asian_1_5_away = sum(p for score, p in score_probs.items()
                            if int(score.split('-')[0]) - int(score.split('-')[1]) <= 1)
        
        # 默认盘口取 -0.5 (最常用的亚洲盘)
        return HandicapPrediction(
            handicap=-0.5,  # 主队让0.5球
            prob_home_cover=round(asian_0_5_home, 4),
            prob_away_cover=round(asian_0_5_away, 4),
            prob_draw_handicap=0.0,  # 半球盘无走水
            asian_0_5={'home': round(asian_0_5_home, 4), 'away': round(asian_0_5_away, 4)},
            asian_1_0={'home': round(asian_1_0_home, 4), 'draw': round(asian_1_0_draw, 4), 
                       'away': round(asian_1_0_away, 4)},
            asian_1_5={'home': round(asian_1_5_home, 4), 'away': round(asian_1_5_away, 4)}
        )
    
    def predict_matches(self, matches: List[Dict]) -> List[MatchPrediction]:
        """
        批量预测比赛
        
        Args:
            matches: 比赛列表，每项包含 match_id, home_team, away_team, home_team_id, away_team_id
            
        Returns:
            预测结果列表
        """
        predictions = []
        for match in matches:
            pred = self.predict_match(
                match['match_id'],
                match['home_team'],
                match['away_team'],
                match['home_team_id'],
                match['away_team_id']
            )
            predictions.append(pred)
        
        logger.info(f"预测了 {len(predictions)} 场比赛")
        return predictions
    
    def calculate_totals_for_line(self, score_probs: Dict[str, float], 
                                   line: float) -> Dict[str, float]:
        """
        计算任意盘口线的大小球概率
        
        Args:
            score_probs: 比分概率分布
            line: 盘口线 (如 2.5, 3.0, 1.5)
            
        Returns:
            {'over': 大球概率, 'under': 小球概率}
            如果是整数盘口 (如 3.0)，还会包含 'exact' = 恰好等于盘口的概率
        """
        # 从比分计算总进球
        over_prob = 0.0
        under_prob = 0.0
        exact_prob = 0.0
        
        for score, prob in score_probs.items():
            home_goals = int(score.split('-')[0])
            away_goals = int(score.split('-')[1])
            total = home_goals + away_goals
            
            if total > line:
                over_prob += prob
            elif total < line:
                under_prob += prob
            else:  # total == line (仅整数盘口时可能)
                exact_prob += prob
        
        result = {
            'over': round(over_prob, 4),
            'under': round(under_prob, 4)
        }
        
        if line == int(line):  # 整数盘口，有走水
            result['exact'] = round(exact_prob, 4)
        
        return result
    
    def calculate_handicap_for_line(self, score_probs: Dict[str, float],
                                     handicap: float) -> Dict[str, float]:
        """
        计算任意让球盘口的概率
        
        Args:
            score_probs: 比分概率分布
            handicap: 盘口值 (正数=主队让球，负数=客队让球)
                      如 -0.5 表示主队让0.5球，+0.5 表示客队让0.5球
            
        Returns:
            {'home': 主队赢盘概率, 'away': 客队赢盘概率}
            如果是整数盘口，还会包含 'draw' = 走水概率
        """
        home_cover = 0.0
        away_cover = 0.0
        draw_prob = 0.0
        
        for score, prob in score_probs.items():
            home_goals = int(score.split('-')[0])
            away_goals = int(score.split('-')[1])
            
            # 计算让球后的净胜
            # 如果主队让球 (handicap < 0): adjusted = home_goals + handicap - away_goals
            # 如果客队让球 (handicap > 0): adjusted = home_goals - (away_goals - handicap)
            adjusted_diff = home_goals - away_goals + handicap
            
            if adjusted_diff > 0:
                home_cover += prob
            elif adjusted_diff < 0:
                away_cover += prob
            else:  # adjusted_diff == 0 (走水)
                draw_prob += prob
        
        result = {
            'home': round(home_cover, 4),
            'away': round(away_cover, 4)
        }
        
        if handicap == int(handicap):  # 整数盘口，有走水
            result['draw'] = round(draw_prob, 4)
        
        return result


class KellyCriterion:
    """
    Kelly Criterion资金管理策略
    
    公式: fraction = (prob × max_odd - (1-prob)) / max_odd
    
    核心: 找最优赔率的博彩公司，计算最优投注比例
    """
    
    def __init__(self, min_edge: float = 0.02, max_fraction: float = 0.25):
        """
        Args:
            min_edge: 最小价值阈值，低于此值不投注
            max_fraction: 最大投注比例（风险控制）
        """
        self.min_edge = min_edge
        self.max_fraction = max_fraction
        
        logger.info(f"KellyCriterion初始化, min_edge={min_edge}, max_fraction={max_fraction}")
    
    def calculate_market_prob(self, odds_list: List[float]) -> float:
        """
        计算市场共识概率
        
        公式: prob = 1 / mean(odds)
        
        Args:
            odds_list: 多个博彩公司的赔率列表
            
        Returns:
            市场共识概率
        """
        if not odds_list:
            return 0.0
        return 1.0 / (sum(odds_list) / len(odds_list))
    
    def calculate_kelly_fraction(self, model_prob: float, odds: float) -> float:
        """
        计算Kelly投注比例
        
        正确公式: f = (p × b - q) / b
        其中: p = 模型概率, b = 赔率-1 (净赔率), q = 1-p
        
        简化形式: f = p - q/b = p - (1-p)/(odds-1)
        
        Args:
            model_prob: 模型预测概率
            odds: 赔率
            
        Returns:
            Kelly比例（可能为负，表示不应投注）
        """
        if odds <= 1:
            # 赔率<=1时无意义，返回负值表示不投注
            return -1.0
        
        # 净赔率 = 赔率 - 1
        net_odds = odds - 1
        
        # Kelly公式: f = p - q/b
        fraction = model_prob - (1 - model_prob) / net_odds
        
        # 限制最大比例（仅对正值限制）
        if fraction > 0:
            fraction = min(fraction, self.max_fraction)
        
        return fraction
    
    def find_value_bets(self, prediction: MatchPrediction, 
                        best_odds: Dict) -> List[ValueBet]:
        """
        找出价值投注
        
        对比模型概率与市场概率，找出有价值的投注机会
        
        Args:
            prediction: 比赛预测结果
            best_odds: 最优赔率数据 {
                'home_odds': float, 'home_bookmaker': str,
                'draw_odds': float, 'draw_bookmaker': str,
                'away_odds': float, 'away_bookmaker': str,
                'market_prob_home': float, 'market_prob_draw': float, 'market_prob_away': float
            }
            
        Returns:
            ValueBet列表
        """
        value_bets = []
        
        # 检查三个结果
        outcomes = [
            ('H', prediction.prob_home, best_odds.get('home_odds', 0), 
             best_odds.get('home_bookmaker', ''), best_odds.get('market_prob_home', 0)),
            ('D', prediction.prob_draw, best_odds.get('draw_odds', 0), 
             best_odds.get('draw_bookmaker', ''), best_odds.get('market_prob_draw', 0)),
            ('A', prediction.prob_away, best_odds.get('away_odds', 0), 
             best_odds.get('away_bookmaker', ''), best_odds.get('market_prob_away', 0)),
        ]
        
        for outcome, model_prob, odds, bookmaker, market_prob in outcomes:
            if odds <= 0:
                continue
            
            # Kelly比例
            kelly = self.calculate_kelly_fraction(model_prob, odds)
            
            # 价值 = 模型概率 - 市场概率
            value = model_prob - market_prob
            
            # 是否为价值投注: Kelly > 0 且 value > min_edge
            is_value = kelly > 0 and value > self.min_edge
            
            vb = ValueBet(
                match_id=prediction.match_id,
                home_team=prediction.home_team,
                away_team=prediction.away_team,
                outcome=outcome,
                model_prob=round(model_prob, 4),
                market_prob=round(market_prob, 4),
                best_odd=odds,
                bookmaker=bookmaker,
                kelly_fraction=round(kelly, 4),
                value=round(value, 4),
                is_value_bet=is_value
            )
            value_bets.append(vb)
        
        # 按价值排序
        value_bets.sort(key=lambda x: x.value, reverse=True)
        
        return value_bets
    
    def allocate_bankroll(self, value_bets: List[ValueBet], 
                          bankroll: float) -> List[Dict]:
        """
        分配资金
        
        根据Kelly比例分配资金到各价值投注
        
        Args:
            value_bets: 价值投注列表
            bankroll: 总资金
            
        Returns:
            资金分配列表
        """
        # 只投注价值投注
        valid_bets = [vb for vb in value_bets if vb.is_value_bet]
        
        if not valid_bets:
            return []
        
        # Kelly比例之和（用于归一化）
        total_kelly = sum(vb.kelly_fraction for vb in valid_bets)
        
        allocations = []
        for vb in valid_bets:
            # 归一化Kelly比例
            normalized_kelly = vb.kelly_fraction / total_kelly if total_kelly > 0 else 0
            
            # 投注金额
            bet_amount = normalized_kelly * bankroll
            
            allocations.append({
                'match_id': vb.match_id,
                'home_team': vb.home_team,
                'away_team': vb.away_team,
                'outcome': vb.outcome,
                'model_prob': vb.model_prob,
                'best_odd': vb.best_odd,
                'bookmaker': vb.bookmaker,
                'kelly_fraction': vb.kelly_fraction,
                'normalized_kelly': round(normalized_kelly, 4),
                'bet_amount': round(bet_amount, 2),
                'potential_return': round(bet_amount * vb.best_odd, 2)
            })
        
        return allocations


class PredictionEngine:
    """
    完整预测引擎
    
    整合Poisson预测 + Kelly Criterion资金管理
    """
    
    def __init__(self, nsim: int = 10000, min_edge: float = 0.02):
        self.predictor = PoissonPredictor(nsim=nsim)
        self.kelly = KellyCriterion(min_edge=min_edge)
        
        logger.info("PredictionEngine初始化完成")
    
    def run_prediction_cycle(self, matches: List[Dict], 
                             team_stats: Dict[int, TeamAttackDefenseStats],
                             odds_data: List[Dict],
                             bankroll: float = 1000) -> Dict:
        """
        运行完整预测周期
        
        Args:
            matches: 即将进行的比赛列表
            team_stats: 球队统计数据字典
            odds_data: 赔率数据列表
            bankroll: 总资金
            
        Returns:
            {
                'predictions': List[MatchPrediction],
                'value_bets': List[ValueBet],
                'allocations': List[Dict]
            }
        """
        # 加载球队统计
        for team_id, stats in team_stats.items():
            self.predictor.set_team_stats(team_id, stats)
        
        # 预测比赛
        predictions = self.predictor.predict_matches(matches)
        
        # 构建赔率字典
        odds_map = {}
        for odds in odds_data:
            odds_map[odds['match_id']] = odds
        
        # 找价值投注
        all_value_bets = []
        for pred in predictions:
            best_odds = odds_map.get(pred.match_id, {})
            value_bets = self.kelly.find_value_bets(pred, best_odds)
            all_value_bets.extend(value_bets)
        
        # 资金分配
        allocations = self.kelly.allocate_bankroll(all_value_bets, bankroll)
        
        return {
            'predictions': predictions,
            'value_bets': all_value_bets,
            'allocations': allocations
        }


# 测试代码
if __name__ == "__main__":
    # 创建测试数据
    predictor = PoissonPredictor(nsim=10000)
    
    # 模拟球队统计 (强队 vs 弱队)
    team_stats = {
        1: TeamAttackDefenseStats(1, "Liverpool", 2.5, 0.6, 10, 1.8, 0.9, 10),  # 强队
        2: TeamAttackDefenseStats(2, "Norwich", 1.2, 1.8, 10, 0.8, 2.0, 10),    # 弱队
    }
    
    predictor._team_stats = team_stats
    
    # 测试预测
    pred = predictor.predict_match("test-001", "Liverpool", "Norwich", 1, 2)
    
    print("=" * 60)
    print("Poisson预测引擎测试 - 扩展功能")
    print("=" * 60)
    
    print(f"\n【比赛】 {pred.home_team} vs {pred.away_team}")
    
    # 胜平负预测
    print(f"\n【胜平负预测】")
    print(f"  主胜概率: {pred.prob_home:.2%}")
    print(f"  平局概率: {pred.prob_draw:.2%}")
    print(f"  客胜概率: {pred.prob_away:.2%}")
    print(f"  预测结果: {pred.prediction}")
    
    # 进球预期
    print(f"\n【进球预期】")
    print(f"  主队预期进球: {pred.expected_home_goals}")
    print(f"  客队预期进球: {pred.expected_away_goals}")
    print(f"  总预期进球: {pred.expected_home_goals + pred.expected_away_goals}")
    print(f"  最可能比分: {pred.most_likely_score}")
    
    # 比分分布 (概率>2%的)
    print(f"\n【比分分布】 (概率>2%)")
    top_scores = sorted(pred.score_distribution.items(), key=lambda x: x[1], reverse=True)[:10]
    for score, prob in top_scores:
        if prob > 0.02:
            print(f"  {score}: {prob:.2%}")
    
    # 大小球预测
    print(f"\n【大小球预测】")
    totals = pred.totals_prediction
    print(f"  预期总进球: {totals.total_goals}")
    print(f"  大2.5球: {totals.prob_over_2_5:.2%} | 小2.5球: {totals.prob_under_2_5:.2%}")
    print(f"  大1.5球: {totals.prob_over_1_5:.2%} | 小1.5球: {totals.prob_under_1_5:.2%}")
    print(f"  大3.5球: {totals.prob_over_3_5:.2%} | 小3.5球: {totals.prob_under_3_5:.2%}")
    
    print(f"\n【总进球分布】")
    for goals, prob in sorted(totals.goals_distribution.items()):
        print(f"  {goals}球: {prob:.2%}")
    
    # 让球盘预测
    print(f"\n【让球盘预测】")
    handicap = pred.handicap_prediction
    print(f"  默认盘口: 主队让{abs(handicap.handicap)}球")
    print(f"  主队赢盘: {handicap.prob_home_cover:.2%} | 客队赢盘: {handicap.prob_away_cover:.2%}")
    
    print(f"\n  【亚洲盘口详细】")
    print(f"  -0.5盘: 主={handicap.asian_0_5['home']:.2%} 客={handicap.asian_0_5['away']:.2%}")
    print(f"  -1.0盘: 主={handicap.asian_1_0['home']:.2%} 走水={handicap.asian_1_0['draw']:.2%} 客={handicap.asian_1_0['away']:.2%}")
    print(f"  -1.5盘: 主={handicap.asian_1_5['home']:.2%} 客={handicap.asian_1_5['away']:.2%}")
    
    # 测试任意盘口计算
    print(f"\n【任意盘口计算】")
    
    # 大小球任意盘口
    print(f"  大小球盘口 2.0:")
    totals_2_0 = predictor.calculate_totals_for_line(pred.score_distribution, 2.0)
    print(f"    大球: {totals_2_0['over']:.2%} | 小球: {totals_2_0['under']:.2%} | 走水: {totals_2_0['exact']:.2%}")
    
    print(f"  大小球盘口 3.5:")
    totals_3_5 = predictor.calculate_totals_for_line(pred.score_distribution, 3.5)
    print(f"    大球: {totals_3_5['over']:.2%} | 小球: {totals_3_5['under']:.2%}")
    
    # 让球盘任意盘口
    print(f"  让球盘口 -0.75 (主队让0.75):")
    hdp_0_75 = predictor.calculate_handicap_for_line(pred.score_distribution, -0.75)
    print(f"    主队赢盘: {hdp_0_75['home']:.2%} | 客队赢盘: {hdp_0_75['away']:.2%}")
    
    print(f"  让球盘口 +0.5 (客队让0.5):")
    hdp_plus_0_5 = predictor.calculate_handicap_for_line(pred.score_distribution, 0.5)
    print(f"    主队赢盘: {hdp_plus_0_5['home']:.2%} | 客队赢盘: {hdp_plus_0_5['away']:.2%}")
    
    # Kelly价值分析
    print(f"\n【Kelly价值分析】")
    kelly = KellyCriterion()
    
    best_odds = {
        'home_odds': 1.45,      # 强队赔率低
        'home_bookmaker': 'bet365',
        'draw_odds': 4.5,
        'draw_bookmaker': 'bet365',
        'away_odds': 8.0,
        'away_bookmaker': 'bet365',
        'market_prob_home': 1/1.45,
        'market_prob_draw': 1/4.5,
        'market_prob_away': 1/8.0
    }
    
    value_bets = kelly.find_value_bets(pred, best_odds)
    
    for vb in value_bets:
        print(f"  {vb.outcome}: 模型={vb.model_prob:.2%}, 市场={vb.market_prob:.2%}")
        print(f"    最优赔率: {vb.best_odd} ({vb.bookmaker})")
        print(f"    Kelly比例: {vb.kelly_fraction:.2%}")
        print(f"    价值: {vb.value:.2%}")
        print(f"    是否价值投注: {vb.is_value_bet}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)