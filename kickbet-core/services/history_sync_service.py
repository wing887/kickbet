"""
KickBet历史比赛数据同步服务

功能:
- 从 Football-Data.org 拉取五大联赛历史比赛
- 同步球队数据
- 同步赛季数据
- 记录同步日志

数据来源: Football-Data.org API
代理: http://172.18.176.1:10808
API限制: 10次/分钟
"""

import os
import sys
import time
import requests
from datetime import datetime, date
from typing import Optional, List, Dict, Any

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database.history_models import (
    HistoryDBManager, League, Season, Team, HistoricalMatch,
    SyncLog, init_history_db
)

# ==================== API 配置 ====================

FOOTBALL_DATA_API_KEY = '84e1509844e14a469520d5ed4fb7f148'
FOOTBALL_DATA_BASE_URL = 'https://api.football-data.org/v4'
PROXY_URL = 'http://172.18.176.1:10808'

# API请求间隔 (10次/分钟限制)
API_REQUEST_INTERVAL = 6  # 秒


# ==================== Football-Data.org API 客户端 ====================

class FootballDataClient:
    """
    Football-Data.org API 客户端
    
    支持:
    - 获取联赛数据
    - 获取赛季数据
    - 获取比赛数据
    - 获取球队数据
    
    代理: WSL通过Windows V2rayN访问外网
    """
    
    def __init__(self, api_key: str = FOOTBALL_DATA_API_KEY, 
                 base_url: str = FOOTBALL_DATA_BASE_URL,
                 proxy_url: str = PROXY_URL):
        self.api_key = api_key
        self.base_url = base_url
        self.proxy_url = proxy_url
        self.session = requests.Session()
        
        # 设置代理
        if proxy_url:
            self.session.proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
        
        # 设置认证头
        self.session.headers.update({
            'X-Auth-Token': api_key,
            'Accept': 'application/json'
        })
        
        # 请求计数
        self.request_count = 0
        self.last_request_time = 0
    
    def _rate_limit(self):
        """速率限制: 10次/分钟"""
        elapsed = time.time() - self.last_request_time
        if elapsed < API_REQUEST_INTERVAL:
            time.sleep(API_REQUEST_INTERVAL - elapsed)
        self.last_request_time = time.time()
        self.request_count += 1
    
    def _request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """发送API请求"""
        self._rate_limit()
        
        url = f"{self.base_url}/{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[API] 请求失败: {endpoint} - {e}")
            return {'error': str(e)}
    
    def get_competitions(self) -> List[Dict]:
        """获取所有联赛列表"""
        data = self._request('competitions')
        return data.get('competitions', [])
    
    def get_competition(self, competition_code: str) -> Dict:
        """获取单个联赛详情"""
        return self._request(f'competitions/{competition_code}')
    
    def get_competition_matches(self, competition_code: str, 
                                 season: Optional[int] = None,
                                 matchday: Optional[int] = None,
                                 status: Optional[str] = None,
                                 date_from: Optional[str] = None,
                                 date_to: Optional[str] = None) -> Dict:
        """获取联赛比赛数据
        
        参数:
        - competition_code: 联赛代码 (PL, PD, BL1, SA, FL1, CL, ELC)
        - season: 赛季年份 (2023, 2024)
        - matchday: 比赛轮次
        - status: 比赛状态 (FINISHED, SCHEDULED, LIVE, TIMED)
        - date_from: 起始日期 (YYYY-MM-DD)
        - date_to: 结束日期 (YYYY-MM-DD)
        """
        params = {}
        if season:
            params['season'] = season
        if matchday:
            params['matchday'] = matchday
        if status:
            params['status'] = status
        if date_from:
            params['dateFrom'] = date_from
        if date_to:
            params['dateTo'] = date_to
        
        return self._request(f'competitions/{competition_code}/matches', params)
    
    def get_competition_standings(self, competition_code: str, 
                                   season: Optional[int] = None) -> Dict:
        """获取联赛积分榜"""
        params = {}
        if season:
            params['season'] = season
        return self._request(f'competitions/{competition_code}/standings', params)
    
    def get_competition_teams(self, competition_code: str,
                               season: Optional[int] = None) -> Dict:
        """获取联赛球队列表"""
        params = {}
        if season:
            params['season'] = season
        return self._request(f'competitions/{competition_code}/teams', params)
    
    def get_match(self, match_id: int) -> Dict:
        """获取单场比赛详情"""
        return self._request(f'matches/{match_id}')


# ==================== 数据同步服务 ====================

class HistorySyncService:
    """
    历史比赛数据同步服务
    
    功能:
    - 同步联赛数据
    - 同步球队数据
    - 同步历史比赛
    - 记录同步日志
    """
    
    # Football-Data.org 联赛代码映射
    LEAGUE_CODE_MAPPING = {
        'PL': 'PL',   # Premier League
        'LL': 'PD',   # La Liga (Primera Division)
        'BL': 'BL1',  # Bundesliga
        'SA': 'SA',   # Serie A
        'L1': 'FL1',  # Ligue 1
        'CL': 'CL',   # Champions League
        'EL': 'EL',   # Europa League (修正: ELC是欧会杯，EL是欧联)
        'ECL': 'ELC', # Europa Conference League (欧会杯)
    }
    
    # 默认同步赛季
    DEFAULT_SEASONS = [2023, 2024, 2025]
    
    def __init__(self, db_manager: HistoryDBManager = None):
        self.db = db_manager or init_history_db()
        self.api = FootballDataClient()
    
    def sync_league_teams(self, league_code: str, season: int) -> Dict:
        """同步联赛球队数据
        
        返回: {'teams_added': N, 'teams_updated': N, 'error': None}
        """
        api_code = self.LEAGUE_CODE_MAPPING.get(league_code)
        if not api_code:
            return {'error': f'未知联赛代码: {league_code}'}
        
        print(f"[Sync] 同步 {league_code} {season} 球队数据...")
        
        # 获取API数据
        data = self.api.get_competition_teams(api_code, season)
        if 'error' in data:
            return {'error': data['error']}
        
        teams_data = data.get('teams', [])
        teams_added = 0
        teams_updated = 0
        
        for team_info in teams_data:
            try:
                team = self.db.add_team(
                    name=team_info['name'],
                    football_data_id=team_info['id'],
                    short_name=team_info.get('shortName'),
                    country=team_info.get('area', {}).get('name'),
                    aliases=[team_info.get('tla', team_info['name'])]
                )
                if team:
                    teams_added += 1
            except Exception as e:
                print(f"[Sync] 添加球队失败: {team_info['name']} - {e}")
        
        return {
            'teams_added': teams_added,
            'teams_updated': teams_updated,
            'total_teams': len(teams_data)
        }
    
    def sync_league_matches(self, league_code: str, season: int,
                            status: str = 'FINISHED') -> Dict:
        """同步联赛历史比赛
        
        参数:
        - league_code: 联赛代码 (PL, LL, BL, SA, L1)
        - season: 赛季年份 (2023, 2024)
        - status: 比赛状态 (FINISHED, SCHEDULED)
        
        返回: {'matches_added': N, 'matches_updated': N, 'error': None}
        """
        api_code = self.LEAGUE_CODE_MAPPING.get(league_code)
        if not api_code:
            return {'error': f'未知联赛代码: {league_code}'}
        
        print(f"[Sync] 同步 {league_code} {season} {status} 比赛...")
        
        # 获取联赛和赛季ID
        league_id = self.db.get_league_by_code(league_code)
        if not league_id:
            return {'error': f'联赛未初始化: {league_code}'}
        
        season_code = f"{season}-{season+1}" if season >= 2020 else str(season)
        season_id = self.db.add_season(
            league_code=league_code,
            season_code=season_code,
            start_year=season,
            end_year=season+1,
            total_matchdays=38 if league_code in ['PL', 'LL', 'SA', 'L1'] else 34
        )
        
        # 获取API数据
        data = self.api.get_competition_matches(api_code, season=season, status=status)
        if 'error' in data:
            return {'error': data['error']}
        
        matches_data = data.get('matches', [])
        matches_added = 0
        matches_updated = 0
        matches_skipped = 0
        
        for match_info in matches_data:
            try:
                # 获取球队记录 (返回team_id)
                home_team_info = match_info.get('homeTeam', {})
                away_team_info = match_info.get('awayTeam', {})
                
                home_team_id = self.db.add_team(
                    name=home_team_info.get('name', ''),
                    football_data_id=home_team_info.get('id')
                )
                away_team_id = self.db.add_team(
                    name=away_team_info.get('name', ''),
                    football_data_id=away_team_info.get('id')
                )
                
                if not home_team_id or not away_team_id:
                    matches_skipped += 1
                    continue
                
                # 获取比赛结果
                score = match_info.get('score', {})
                full_time = score.get('fullTime', {})
                half_time = score.get('halfTime', {})
                
                home_score = full_time.get('home')
                away_score = full_time.get('away')
                
                # 只处理已完成比赛
                if home_score is None or away_score is None:
                    matches_skipped += 1
                    continue
                
                # 添加比赛
                match_date = match_info.get('utcDate', '')
                if match_date:
                    match_date = datetime.fromisoformat(match_date.replace('Z', '+00:00')).date()
                else:
                    match_date = date.today()
                
                match = self.db.add_match(
                    match_source_id=str(match_info['id']),
                    league_id=league_id,
                    season_id=season_id,
                    home_team_id=home_team_id,
                    away_team_id=away_team_id,
                    match_date=match_date,
                    home_score=home_score,
                    away_score=away_score,
                    matchday=match_info.get('matchday'),
                    half_time_home=half_time.get('home'),
                    half_time_away=half_time.get('away')
                )
                
                if match:
                    matches_added += 1
                
            except Exception as e:
                print(f"[Sync] 添加比赛失败: {match_info.get('id')} - {e}")
                matches_skipped += 1
        
        # 记录同步日志
        self.db.add_sync_log(
            league_id=league_id,
            season_id=season_id,
            sync_type='full',
            matches_added=matches_added,
            matches_updated=matches_updated,
            matches_skipped=matches_skipped,
            status='success'
        )
        
        return {
            'matches_added': matches_added,
            'matches_updated': matches_updated,
            'matches_skipped': matches_skipped,
            'total_matches': len(matches_data),
            'season_id': season_id
        }
    
    def sync_all_leagues(self, seasons: List[int] = None, 
                         leagues: List[str] = None) -> Dict:
        """同步所有联赛历史数据
        
        参数:
        - seasons: 赛季列表 (默认 [2023, 2024, 2025])
        - leagues: 联赛列表 (默认五大联赛)
        
        返回: 各联赛同步结果汇总
        """
        seasons = seasons or self.DEFAULT_SEASONS
        leagues = leagues or ['PL', 'LL', 'BL', 'SA', 'L1']
        
        print(f"\n{'='*60}")
        print(f"[Sync] 开始同步 {len(leagues)} 个联赛 {len(seasons)} 个赛季")
        print(f"{'='*60}\n")
        
        results = {}
        
        for league_code in leagues:
            results[league_code] = {}
            
            for season in seasons:
                print(f"\n--- {league_code} {season} ---")
                
                # 先同步球队
                team_result = self.sync_league_teams(league_code, season)
                results[league_code][f'{season}_teams'] = team_result
                
                # 再同步比赛
                match_result = self.sync_league_matches(league_code, season)
                results[league_code][f'{season}_matches'] = match_result
                
                # API请求计数
                print(f"[API] 请求次数: {self.api.request_count}")
        
        # 统计汇总
        summary = self.db.get_stats_summary()
        print(f"\n{'='*60}")
        print(f"[Sync] 同步完成!")
        print(f"[Sync] 数据库统计:")
        print(f"  - 联赛: {summary['leagues']}")
        print(f"  - 赛季: {summary['seasons']}")
        print(f"  - 球队: {summary['teams']}")
        print(f"  - 比赛: {summary['matches']}")
        print(f"{'='*60}\n")
        
        return {
            'results': results,
            'summary': summary,
            'api_requests': self.api.request_count
        }
    
    def sync_daily_update(self) -> Dict:
        """每日增量同步 (同步昨天完成的比赛)"""
        from datetime import timedelta
        
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        date_from = yesterday.strftime('%Y-%m-%d')
        date_to = today.strftime('%Y-%m-%d')
        
        print(f"[Sync] 每日增量同步: {date_from} ~ {date_to}")
        
        results = {}
        
        for league_code in ['PL', 'LL', 'BL', 'SA', 'L1']:
            api_code = self.LEAGUE_CODE_MAPPING.get(league_code)
            
            # 获取昨天比赛
            data = self.api.get_competition_matches(
                api_code, 
                status='FINISHED',
                date_from=date_from,
                date_to=date_to
            )
            
            if 'error' in data:
                results[league_code] = {'error': data['error']}
                continue
            
            matches = data.get('matches', [])
            results[league_code] = {'matches_found': len(matches)}
            
            # TODO: 处理新比赛
        
        return results


# ==================== 测试函数 ====================

def test_sync_single_league():
    """测试同步单个联赛"""
    db = init_history_db()
    sync = HistorySyncService(db)
    
    # 同步英超2024赛季已完成比赛
    result = sync.sync_league_matches('PL', 2024, status='FINISHED')
    
    print(f"\n同步结果:")
    print(f"  - 新增比赛: {result.get('matches_added', 0)}")
    print(f"  - 更新比赛: {result.get('matches_updated', 0)}")
    print(f"  - 跳过比赛: {result.get('matches_skipped', 0)}")
    
    return result


def test_get_team_stats():
    """测试从历史比赛获取球队统计"""
    db = init_history_db()
    
    # 获取曼城统计
    session = db.get_session()
    team = session.query(Team).filter(Team.name == 'Manchester City FC').first()
    session.close()
    
    if not team:
        print("曼城球队未找到")
        return
    
    stats = db.get_team_stats_from_history(team.team_id)
    
    print(f"\n{team.name} 统计:")
    print(f"  - 总比赛: {stats.get('total_matches', 0)}")
    print(f"  - 主场场均进球: {stats.get('home_scored_avg', 0):.2f}")
    print(f"  - 主场场均失球: {stats.get('home_conceded_avg', 0):.2f}")
    print(f"  - 客场场均进球: {stats.get('away_scored_avg', 0):.2f}")
    print(f"  - 客场场均失球: {stats.get('away_conceded_avg', 0):.2f}")
    print(f"  - 近期状态: {stats.get('recent_form', '')}")
    
    return stats


# ==================== 主函数 ====================

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='历史比赛数据同步')
    parser.add_argument('--init', action='store_true', help='初始化数据库')
    parser.add_argument('--sync-all', action='store_true', help='同步所有联赛')
    parser.add_argument('--sync-league', type=str, help='同步指定联赛 (PL/LL/BL/SA/L1)')
    parser.add_argument('--sync-season', type=int, help='同步指定赛季 (2023/2024/2025)')
    parser.add_argument('--stats', action='store_true', help='查看数据库统计')
    parser.add_argument('--test', action='store_true', help='测试同步')
    
    args = parser.parse_args()
    
    if args.init:
        print("初始化历史比赛数据库...")
        db = init_history_db()
        summary = db.get_stats_summary()
        print(f"数据库统计: {summary}")
    
    elif args.sync_all:
        print("同步所有联赛历史数据...")
        sync = HistorySyncService()
        result = sync.sync_all_leagues()
        print(f"同步完成!")
    
    elif args.sync_league:
        league = args.sync_league.upper()
        season = args.sync_season or 2024
        print(f"同步 {league} {season}...")
        sync = HistorySyncService()
        result = sync.sync_league_matches(league, season)
        print(f"结果: {result}")
    
    elif args.stats:
        db = HistoryDBManager()
        summary = db.get_stats_summary()
        print(f"\n历史比赛数据库统计:")
        for key, value in summary.items():
            print(f"  {key}: {value}")
    
    elif args.test:
        test_sync_single_league()
    
    else:
        parser.print_help()