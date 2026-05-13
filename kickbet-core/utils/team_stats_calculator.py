"""
球队历史比赛统计计算器

功能:
- 从已完成比赛数据计算主客场场均进球/失球
- 计算两队历史交锋数据
- 计算最近N场比赛趋势

解决当前Poisson模型只用赛季平均值的问题
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class TeamDetailedStats:
    """球队详细统计数据 (区分主客场)"""
    team_id: int
    team_name: str
    
    # 主场统计 (真实计算)
    home_matches: int = 0
    home_goals_scored: int = 0
    home_goals_conceded: int = 0
    home_scored_avg: float = 0.0
    home_conceded_avg: float = 0.0
    
    # 客场统计 (真实计算)
    away_matches: int = 0
    away_goals_scored: int = 0
    away_goals_conceded: int = 0
    away_scored_avg: float = 0.0
    away_conceded_avg: float = 0.0
    
    # 近期统计 (最近5场)
    recent_matches: int = 0
    recent_goals_scored: int = 0
    recent_goals_conceded: int = 0
    recent_scored_avg: float = 0.0
    recent_conceded_avg: float = 0.0
    recent_form: str = ""  # W/D/L序列 如 "WWDLL"


@dataclass 
class HeadToHeadStats:
    """两队历史交锋统计"""
    home_team_id: int
    away_team_id: int
    total_matches: int = 0
    
    # 主队主场对客队
    home_wins: int = 0
    draws: int = 0
    away_wins: int = 0
    
    # 进球统计
    home_goals_avg: float = 0.0
    away_goals_avg: float = 0.0
    
    # 最近交锋
    last_5_home_wins: int = 0
    last_5_draws: int = 0
    last_5_away_wins: int = 0


class TeamStatsCalculator:
    """
    球队统计计算器
    
    从历史比赛数据计算：
    1. 真实的主客场场均进球/失球
    2. 两队历史交锋数据
    3. 近期表现趋势
    """
    
    def __init__(self):
        self._team_stats: Dict[int, TeamDetailedStats] = {}
        self._h2h_stats: Dict[str, HeadToHeadStats] = {}
    
    def calculate_from_matches(self, matches: List, 
                               team_id: int, 
                               team_name: str) -> TeamDetailedStats:
        """从比赛列表计算球队统计"""
        stats = TeamDetailedStats(team_id=team_id, team_name=team_name)
        
        # 按时间排序
        sorted_matches = sorted(
            matches, 
            key=lambda m: getattr(m, 'match_date', '') or '', 
            reverse=True
        )
        
        home_scored_total = 0
        home_conceded_total = 0
        away_scored_total = 0
        away_conceded_total = 0
        
        recent_form = []
        recent_scored = 0
        recent_conceded = 0
        
        for i, match in enumerate(sorted_matches):
            home_team_id = getattr(match, 'home_team_id', None)
            away_team_id = getattr(match, 'away_team_id', None)
            home_goals = getattr(match, 'home_goals', None) or 0
            away_goals = getattr(match, 'away_goals', None) or 0
            result = getattr(match, 'result', None)
            
            is_home = home_team_id == team_id
            
            if is_home:
                stats.home_matches += 1
                home_scored_total += home_goals
                home_conceded_total += away_goals
            else:
                stats.away_matches += 1
                away_scored_total += away_goals
                away_conceded_total += home_goals
            
            # 近期统计 (最近5场)
            if i < 5:
                stats.recent_matches += 1
                if is_home:
                    recent_scored += home_goals
                    recent_conceded += away_goals
                else:
                    recent_scored += away_goals
                    recent_conceded += home_goals
                
                if result:
                    if result == 'H' and is_home:
                        recent_form.append('W')
                    elif result == 'A' and not is_home:
                        recent_form.append('W')
                    elif result == 'D':
                        recent_form.append('D')
                    else:
                        recent_form.append('L')
        
        # 计算平均值
        if stats.home_matches > 0:
            stats.home_scored_avg = home_scored_total / stats.home_matches
            stats.home_conceded_avg = home_conceded_total / stats.home_matches
        
        if stats.away_matches > 0:
            stats.away_scored_avg = away_scored_total / stats.away_matches
            stats.away_conceded_avg = away_conceded_total / stats.away_matches
        
        stats.recent_goals_scored = recent_scored
        stats.recent_goals_conceded = recent_conceded
        if stats.recent_matches > 0:
            stats.recent_scored_avg = recent_scored / stats.recent_matches
            stats.recent_conceded_avg = recent_conceded / stats.recent_matches
        
        stats.recent_form = ''.join(recent_form[:5])
        
        self._team_stats[team_id] = stats
        
        logger.info(f"[{team_name}] 主场{stats.home_matches}场(进{stats.home_scored_avg:.2f}/失{stats.home_conceded_avg:.2f}), "
                    f"客场{stats.away_matches}场(进{stats.away_scored_avg:.2f}/失{stats.away_conceded_avg:.2f})")
        
        return stats
    
    def get_team_stats(self, team_id: int) -> Optional[TeamDetailedStats]:
        return self._team_stats.get(team_id)
    
    def to_poisson_format(self, team_id: int) -> Dict:
        """转换为Poisson预测器需要的格式"""
        stats = self.get_team_stats(team_id)
        if not stats:
            return None
        
        return {
            'team_id': stats.team_id,
            'team_name': stats.team_name,
            'home_scored_avg': stats.home_scored_avg,
            'home_conceded_avg': stats.home_conceded_avg,
            'home_played': stats.home_matches,
            'away_scored_avg': stats.away_scored_avg,
            'away_conceded_avg': stats.away_conceded_avg,
            'away_played': stats.away_matches,
            'recent_form': stats.recent_form,
            'recent_scored_avg': stats.recent_scored_avg,
            'recent_conceded_avg': stats.recent_conceded_avg
        }


def calculate_league_stats(collector, league_code: str, season: int = None) -> Dict[int, TeamDetailedStats]:
    """计算联赛所有球队的真实主客场统计"""
    calculator = TeamStatsCalculator()
    
    matches = collector.get_finished_matches(league_code, season)
    logger.info(f"[{league_code}] 获取到 {len(matches)} 场已完成比赛")
    
    team_matches = defaultdict(list)
    
    for match in matches:
        team_matches[match.home_team_id].append(match)
        team_matches[match.away_team_id].append(match)
    
    for team_id, team_match_list in team_matches.items():
        team_name = team_match_list[0].home_team_name if team_match_list[0].home_team_id == team_id else team_match_list[0].away_team_name
        calculator.calculate_from_matches(team_match_list, team_id, team_name)
    
    return calculator._team_stats