"""
Football-Data.org 数据采集器
适配 football-data.org API v4
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import logging
import time

logger = logging.getLogger(__name__)


@dataclass
class Match:
    """比赛数据结构"""
    match_id: int
    league_code: str
    season: int
    match_date: str
    home_team_id: int
    home_team_name: str
    away_team_id: int
    away_team_name: str
    home_goals: Optional[int] = None
    away_goals: Optional[int] = None
    result: Optional[str] = None  # H/D/A
    status: str = "SCHEDULED"


@dataclass
class TeamStats:
    """球队统计数据结构"""
    team_id: int
    team_name: str
    league_code: str
    season: int
    position: int
    played: int
    won: int
    drawn: int
    lost: int
    goals_for: int
    goals_against: int
    points: int
    # 计算值
    goals_for_avg: float = 0.0
    goals_against_avg: float = 0.0


@dataclass
class LeagueTable:
    """联赛积分榜"""
    league_code: str
    league_name: str
    season: int
    standings: List[TeamStats]


class FootballDataOrgCollector:
    """
    Football-Data.org 数据采集器
    
    API文档: https://www.football-data.org/documentation/api/index.html
    
    覆盖联赛 (免费层):
    - PL: Premier League (英超)
    - PD: La Liga (西甲)
    - BL1: Bundesliga (德甲)
    - SA: Serie A (意甲)
    - FL1: Ligue 1 (法甲)
    - CL: Champions League (欧冠)
    - EL: Europa League (欧联杯)
    
    免费层限制: 10次请求/分钟
    """
    
    # 支持的联赛代码
    LEAGUES = {
        'PL': 'Premier League',
        'PD': 'La Liga',
        'BL1': 'Bundesliga',
        'SA': 'Serie A',
        'FL1': 'Ligue 1',
        'CL': 'Champions League',
        'EL': 'Europa League',
        'EC': 'European Championship',
        'WC': 'World Cup',
    }
    
    def __init__(self, api_token: str, proxy: str = None):
        self.base_url = "https://api.football-data.org/v4"
        self.api_token = api_token
        self.headers = {"X-Auth-Token": self.api_token}
        self.request_count = 0
        self.last_request_time = 0
        self.rate_limit = 10  # 每分钟10次
        self.proxy = proxy  # WSL代理
        
        logger.info(f"FootballDataOrgCollector初始化, base_url={self.base_url}")
    
    def _wait_for_rate_limit(self):
        """等待以遵守速率限制"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        # 每分钟最多10次请求，即每次请求间隔至少6秒
        if elapsed < 6:
            wait_time = 6 - elapsed
            logger.debug(f"等待 {wait_time:.1f} 秒以遵守速率限制")
            time.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def _fetch(self, endpoint: str, params: Dict = None) -> Dict:
        """发送API请求"""
        self._wait_for_rate_limit()
        
        url = f"{self.base_url}{endpoint}"
        proxies = None
        if self.proxy:
            proxies = {'http': self.proxy, 'https': self.proxy}
        
        try:
            response = requests.get(url, headers=self.headers, params=params, 
                                     proxies=proxies, timeout=60)
            response.raise_for_status()
            self.request_count += 1
            
            data = response.json()
            logger.debug(f"API请求成功: {endpoint}")
            return data
            
        except requests.exceptions.HTTPError as e:
            if response.status_code == 403:
                logger.error("API Token无效或请求限制超出")
            elif response.status_code == 404:
                logger.error(f"资源不存在: {endpoint}")
            else:
                logger.error(f"HTTP错误: {e}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"API请求失败: {endpoint}, 错误: {e}")
            raise
    
    def get_competitions(self) -> List[Dict]:
        """
        获取所有可用的联赛列表
        
        Returns:
            联赛列表
        """
        endpoint = "/competitions"
        data = self._fetch(endpoint)
        
        competitions = []
        for comp in data.get('competitions', []):
            competitions.append({
                'code': comp['code'],
                'name': comp['name'],
                'area': comp['area']['name']
            })
        
        logger.info(f"获取到 {len(competitions)} 个联赛")
        return competitions
    
    def get_competition_matches(self, competition_code: str, 
                                 season: int = None, status: str = None) -> List[Match]:
        """
        获取联赛的比赛
        
        Args:
            competition_code: 联赛代码，如 'PL'
            season: 赛季年份，如 2024
            status: 比赛状态 (SCHEDULED/LIVE/IN_PLAY/PAUSED/FINISHED/TIMED)
        
        Returns:
            Match列表
        """
        endpoint = f"/competitions/{competition_code}/matches"
        params = {}
        
        if season:
            params['season'] = season
        if status:
            params['status'] = status
        
        data = self._fetch(endpoint, params)
        
        matches = []
        for fixture in data.get('matches', []):
            home_goals = fixture['score']['fullTime']['home']
            away_goals = fixture['score']['fullTime']['away']
            
            # 计算结果
            result = None
            if home_goals is not None and away_goals is not None:
                if home_goals > away_goals:
                    result = 'H'
                elif home_goals == away_goals:
                    result = 'D'
                else:
                    result = 'A'
            
            match = Match(
                match_id=fixture['id'],
                league_code=competition_code,
                season=fixture['season']['startDate'][:4] if fixture.get('season') else season or datetime.now().year,
                match_date=fixture['utcDate'],
                home_team_id=fixture['homeTeam']['id'],
                home_team_name=fixture['homeTeam']['name'],
                away_team_id=fixture['awayTeam']['id'],
                away_team_name=fixture['awayTeam']['name'],
                home_goals=home_goals,
                away_goals=away_goals,
                result=result,
                status=fixture['status']
            )
            matches.append(match)
        
        logger.info(f"[{competition_code}] 获取到 {len(matches)} 场比赛")
        return matches
    
    def get_upcoming_matches(self, competition_code: str, days: int = 7) -> List[Match]:
        """
        获取即将进行的比赛
        
        Args:
            competition_code: 联赛代码
            days: 查询天数
        
        Returns:
            未开始的比赛列表
        """
        matches = self.get_competition_matches(competition_code, status='SCHEDULED')
        
        # 过滤未来N天的比赛
        from datetime import timezone
        now = datetime.now(timezone.utc)  # 使用UTC timezone
        upcoming = []
        
        for match in matches:
            match_date = datetime.fromisoformat(match.match_date.replace('Z', '+00:00'))
            if match_date <= now + timedelta(days=days):
                upcoming.append(match)
        
        logger.info(f"[{competition_code}] 未来{days}天有 {len(upcoming)} 场比赛")
        return upcoming
    
    def get_finished_matches(self, competition_code: str, season: int = None) -> List[Match]:
        """
        获取已完成的比赛
        
        Args:
            competition_code: 联赛代码
            season: 赛季年份
        
        Returns:
            已完成的比赛列表
        """
        return self.get_competition_matches(competition_code, season=season, status='FINISHED')
    
    def get_standings(self, competition_code: str, season: int = None) -> LeagueTable:
        """
        获取联赛积分榜
        
        Args:
            competition_code: 联赛代码
            season: 赛季年份
        
        Returns:
            积分榜数据
        """
        endpoint = f"/competitions/{competition_code}/standings"
        params = {'standingType': 'TOTAL'}
        
        if season:
            params['season'] = season
        
        data = self._fetch(endpoint, params)
        
        standings = []
        for table in data.get('standings', []):
            if table['type'] == 'TOTAL':
                for position in table['table']:
                    team = position['team']
                    
                    stats = TeamStats(
                        team_id=team['id'],
                        team_name=team['name'],
                        league_code=competition_code,
                        season=season or datetime.now().year,
                        position=position['position'],
                        played=position['playedGames'],
                        won=position['won'],
                        drawn=position['draw'],
                        lost=position['lost'],
                        goals_for=position['goalsFor'],
                        goals_against=position['goalsAgainst'],
                        points=position['points'],
                        goals_for_avg=round(position['goalsFor'] / position['playedGames'], 2) if position['playedGames'] > 0 else 0,
                        goals_against_avg=round(position['goalsAgainst'] / position['playedGames'], 2) if position['playedGames'] > 0 else 0
                    )
                    standings.append(stats)
        
        league_table = LeagueTable(
            league_code=competition_code,
            league_name=self.LEAGUES.get(competition_code, competition_code),
            season=season or datetime.now().year,
            standings=standings
        )
        
        logger.info(f"[{competition_code}] 积分榜 {len(standings)} 个球队")
        return league_table
    
    def get_team(self, team_id: int) -> Dict:
        """
        获取球队详情
        
        Args:
            team_id: 球队ID
        
        Returns:
            球队信息
        """
        endpoint = f"/teams/{team_id}"
        return self._fetch(endpoint)
    
    def get_team_matches(self, team_id: int, season: int = None, 
                         status: str = None, limit: int = 10) -> List[Match]:
        """
        获取球队的比赛
        
        Args:
            team_id: 球队ID
            season: 赛季年份
            status: 比赛状态
            limit: 返回数量限制
        
        Returns:
            Match列表
        """
        endpoint = f"/teams/{team_id}/matches"
        params = {}
        
        if season:
            params['season'] = season
        if status:
            params['status'] = status
        if limit:
            params['limit'] = limit
        
        data = self._fetch(endpoint, params)
        
        matches = []
        for fixture in data.get('matches', []):
            match = Match(
                match_id=fixture['id'],
                league_code=fixture['competition']['code'],
                season=fixture['season']['startDate'][:4] if fixture.get('season') else season or datetime.now().year,
                match_date=fixture['utcDate'],
                home_team_id=fixture['homeTeam']['id'],
                home_team_name=fixture['homeTeam']['name'],
                away_team_id=fixture['awayTeam']['id'],
                away_team_name=fixture['awayTeam']['name'],
                home_goals=fixture['score']['fullTime']['home'],
                away_goals=fixture['score']['fullTime']['away'],
                status=fixture['status']
            )
            matches.append(match)
        
        logger.info(f"球队{team_id}: 获取到 {len(matches)} 场比赛")
        return matches
    
    def calculate_team_attack_defense_stats(self, team_id: int, 
                                              competition_code: str = None) -> Dict:
        """
        计算球队主客场攻击/防守统计
        
        基于DataScienceProjects的方法计算:
        - home_scored_avg: 主场场均进球
        - home_conceded_avg: 主场场均失球
        - away_scored_avg: 客场场均进球
        - away_conceded_avg: 客场场均失球
        
        Args:
            team_id: 球队ID
            competition_code: 联赛代码
        
        Returns:
            统计数据字典
        """
        matches = self.get_team_matches(team_id, status='FINISHED', limit=50)
        
        # 筛选联赛
        if competition_code:
            matches = [m for m in matches if m.league_code == competition_code]
        
        # 分类主客场
        home_matches = [m for m in matches if m.home_team_id == team_id]
        away_matches = [m for m in matches if m.away_team_id == team_id]
        
        stats = {
            'team_id': team_id,
            'home_played': len(home_matches),
            'away_played': len(away_matches),
            'home_scored_avg': 0,
            'home_conceded_avg': 0,
            'away_scored_avg': 0,
            'away_conceded_avg': 0
        }
        
        # 计算主场统计
        if home_matches:
            home_scored = sum(m.home_goals for m in home_matches if m.home_goals)
            home_conceded = sum(m.away_goals for m in home_matches if m.away_goals)
            stats['home_scored_avg'] = round(home_scored / len(home_matches), 2)
            stats['home_conceded_avg'] = round(home_conceded / len(home_matches), 2)
        
        # 计算客场统计
        if away_matches:
            away_scored = sum(m.away_goals for m in away_matches if m.away_goals)
            away_conceded = sum(m.home_goals for m in away_matches if m.home_goals)
            stats['away_scored_avg'] = round(away_scored / len(away_matches), 2)
            stats['away_conceded_avg'] = round(away_conceded / len(away_matches), 2)
        
        logger.info(f"球队{team_id}攻击防守统计: 主场{stats['home_scored_avg']}/{stats['home_conceded_avg']}, 客场{stats['away_scored_avg']}/{stats['away_conceded_avg']}")
        
        return stats
    
    def save_to_json(self, data: Any, filename: str):
        """保存数据到JSON文件"""
        filepath = f"data/{filename}"
        import os
        os.makedirs("data", exist_ok=True)
        
        if isinstance(data, list) and data and hasattr(data[0], '__dataclass_fields__'):
            data = [asdict(item) for item in data]
        elif hasattr(data, '__dataclass_fields__'):
            data = asdict(data)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"数据已保存到 {filepath}")


# 测试代码
if __name__ == "__main__":
    import os
    
    api_token = os.environ.get('FOOTBALL_DATA_TOKEN', '')
    
    if api_token:
        collector = FootballDataOrgCollector(api_token)
        
        # 测试获取英超比赛
        print("测试获取英超比赛...")
        matches = collector.get_upcoming_matches('PL', days=7)
        
        for match in matches[:5]:
            print(f"{match.home_team_name} vs {match.away_team_name}")
            print(f"  日期: {match.match_date}")
            print(f"  状态: {match.status}")
        
        # 测试获取积分榜
        print("\n测试获取积分榜...")
        standings = collector.get_standings('PL')
        
        for team in standings.standings[:5]:
            print(f"{team.position}. {team.team_name}: {team.points}分")
            print(f"   进球: {team.goals_for} (场均{team.goals_for_avg})")
    else:
        print("请设置FOOTBALL_DATA_TOKEN环境变量")
        print("获取Token: https://www.football-data.org/client/register")