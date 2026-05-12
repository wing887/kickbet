"""
Odds-API.io 赔率数据采集器
从 Odds-API.io 采集实时赔率数据

特点:
- 277 家博彩公司
- 免费计划: Bet365 + Sbobet (亚洲用户友好)
- 支持中超、K联赛等亚洲联赛
- 丰富的赔率市场: ML、Spread、Totals、Corners等
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import logging
import time

logger = logging.getLogger(__name__)


@dataclass
class OddsApiIoConfig:
    """Odds-API.io 配置"""
    api_key: str
    base_url: str = "https://api.odds-api.io/v3"
    # 免费计划允许的博彩公司
    free_bookmakers: List[str] = None
    
    def __post_init__(self):
        if self.free_bookmakers is None:
            self.free_bookmakers = ['Bet365', 'Sbobet']


@dataclass
class OddsApiIoEvent:
    """赛事数据结构"""
    event_id: str
    home_team: str
    away_team: str
    league: str
    league_slug: str
    sport: str
    date: str
    status: str
    scores: Dict = None


@dataclass
class OddsApiIoMarket:
    """赔率市场数据"""
    market_name: str
    odds: List[Dict]
    updated_at: str
    bookmaker: str


@dataclass
class OddsApiIoBestOdds:
    """最优赔率数据"""
    event_id: str
    home_team: str
    away_team: str
    league: str
    # ML 赔率
    home_odds: float
    home_bookmaker: str
    draw_odds: float
    draw_bookmaker: str
    away_odds: float
    away_bookmaker: str
    # Spread 让球盘
    spread_hdp: float = 0.0
    spread_home_odds: float = 0.0
    spread_home_bookmaker: str = ""
    spread_away_odds: float = 0.0
    spread_away_bookmaker: str = ""
    # Totals 大小球
    totals_hdp: float = 0.0
    totals_over_odds: float = 0.0
    totals_over_bookmaker: str = ""
    totals_under_odds: float = 0.0
    totals_under_bookmaker: str = ""
    # 市场概率
    market_prob_home: float = 0.0
    market_prob_draw: float = 0.0
    market_prob_away: float = 0.0
    # 更新时间
    updated_at: str = ""


class OddsApiIoCollector:
    """
    Odds-API.io 赔率采集器
    
    特点:
    - 支持亚洲联赛（中超、K联赛、J联赛等）
    - 包含 Sbobet（皇冠）赔率
    - 丰富的赔率市场类型
    
    免费计划限制:
    - 最多2个博彩公司: Bet365 + Sbobet
    - 100次请求/小时
    """
    
    # 支持的联赛映射
    LEAGUE_MAPPING = {
        # Football-Data.org code -> Odds-API.io slug
        'PL': 'england-premier-league',
        'BL1': 'germany-bundesliga',
        'PD': 'spain-la-liga',
        'SA': 'italy-serie-a',
        'FL1': 'france-ligue-1',
        'CL': 'europe-uefa-champions-league',
        'EL': 'europe-uefa-europa-league',
        # 亚洲联赛
        'CSL': 'china-chinese-super-league',  # 中超
        'JL': 'japan-jleague',                 # J联赛
        'KL': 'republic-of-korea-k-league-1',  # K联赛
        # 其他亚洲联赛
        'ISL': 'india-indian-super-league',    # 印度超
        'THL': 'thailand-thai-league-1',       # 泰国联赛
        'VNL': 'vietnam-v-league-1',           # 越南联赛
        'MSL': 'malaysia-super-league',        # 马来西亚联赛
        'SPL': 'singapore-premier-league',     # 新加坡联赛
    }
    
    # 球队名称规范化映射 (Odds-API.io -> Football-Data.org)
    TEAM_NAME_NORMALIZE = {
        'Brighton & Hove Albion': 'Brighton and Hove Albion',
        'Wolverhampton Wanderers': 'Wolves',
        'Manchester United': 'Man United',
        'Tottenham Hotspur': 'Tottenham',
        'Newcastle United': 'Newcastle',
        'West Ham United': 'West Ham',
        'Leeds United': 'Leeds',
    }
    
    def __init__(self, config: OddsApiIoConfig):
        self.config = config
        self.base_url = config.base_url
        self.api_key = config.api_key
        self.request_count = 0
        self.rate_limit_remaining = 100
        
        # 缓存
        self._events_cache: Dict[str, List[OddsApiIoEvent]] = {}
        self._odds_cache: Dict[str, OddsApiIoBestOdds] = {}
        
        logger.info(f"OddsApiIoCollector初始化, base_url={self.base_url}")
    
    def _fetch(self, endpoint: str, params: Dict = None) -> Dict:
        """发送API请求"""
        url = f"{self.base_url}{endpoint}"
        params = params or {}
        params['apiKey'] = self.api_key
        
        try:
            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()
            self.request_count += 1
            
            # 记录 Rate Limit
            remaining = response.headers.get('x-ratelimit-remaining')
            limit = response.headers.get('x-ratelimit-limit')
            if remaining:
                self.rate_limit_remaining = int(remaining)
                logger.debug(f"API请求: {endpoint}, 剩余: {remaining}/{limit}")
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API请求失败: {endpoint}, 错误: {e}")
            raise
    
    def get_sports(self) -> List[Dict]:
        """获取支持的体育项目"""
        data = self._fetch('/sports')
        logger.info(f"获取到 {len(data)} 个体育项目")
        return data
    
    def get_bookmakers(self) -> List[Dict]:
        """获取支持的博彩公司"""
        data = self._fetch('/bookmakers')
        
        # 筛选活跃的博彩公司
        active = [bm for bm in data if bm.get('active')]
        logger.info(f"活跃博彩公司: {len(active)} / {len(data)}")
        
        # 筛选亚洲相关博彩公司
        asian_keywords = ['sbobet', 'dafabet', '188bet', 'singbet', '1xbet', 
                          'bet365', 'm88', 'melbet', 'megapari', 'stake', '22bet']
        asian_bm = [bm for bm in active 
                    if any(kw in bm.get('name', '').lower() for kw in asian_keywords)]
        
        logger.info(f"亚洲相关博彩公司: {[bm['name'] for bm in asian_bm]}")
        return data
    
    def get_events(self, sport: str = 'football', league: str = None, 
                   status: str = None) -> List[OddsApiIoEvent]:
        """
        获取赛事列表
        
        Args:
            sport: 体育项目 slug
            league: 联赛 slug (可选)
            status: 状态筛选 (pending, live, settled, cancelled)
        
        Returns:
            赛事列表
        """
        params = {'sport': sport}
        if league:
            params['league'] = league
        if status:
            params['status'] = status
        
        data = self._fetch('/events', params)
        
        events = []
        for e in data:
            # 过滤掉已取消的比赛
            if e.get('status') == 'cancelled':
                continue
            
            event = OddsApiIoEvent(
                event_id=str(e['id']),
                home_team=e['home'],
                away_team=e['away'],
                league=e['league']['name'],
                league_slug=e['league']['slug'],
                sport=e['sport']['slug'],
                date=e['date'],
                status=e['status'],
                scores=e.get('scores')
            )
            events.append(event)
        
        logger.info(f"获取到 {len(events)} 场比赛")
        return events
    
    def get_odds_for_event(self, event_id: str, 
                           bookmakers: List[str] = None) -> Dict:
        """
        获取单场比赛的赔率
        
        Args:
            event_id: 比赛ID
            bookmakers: 博彩公司列表 (默认使用免费计划允许的)
        
        Returns:
            赔率数据
        """
        if bookmakers is None:
            bookmakers = self.config.free_bookmakers
        
        bookmakers_str = ','.join(bookmakers)
        
        data = self._fetch('/odds', {
            'eventId': event_id,
            'bookmakers': bookmakers_str
        })
        
        return data
    
    def get_best_odds(self, sport: str = 'football', 
                      league: str = None) -> List[OddsApiIoBestOdds]:
        """
        获取最优赔率
        
        Args:
            sport: 体育项目
            league: 联赛 (可选)
        
        Returns:
            最优赔率列表
        """
        # 获取赛事
        events = self.get_events(sport, league, status='pending')
        
        best_odds_list = []
        
        for event in events[:20]:  # 限制20场避免超限
            try:
                odds_data = self.get_odds_for_event(event.event_id)
                
                if not odds_data.get('bookmakers'):
                    logger.warning(f"比赛 {event.home_team} vs {event.away_team} 无赔率数据")
                    continue
                
                # 解析赔率
                best_odds = self._parse_best_odds(odds_data, event)
                if best_odds:
                    best_odds_list.append(best_odds)
                
                # 避免 rate limit
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"获取赔率失败: {event.event_id}, 错误: {e}")
                continue
        
        logger.info(f"获取到 {len(best_odds_list)} 场比赛的最优赔率")
        return best_odds_list
    
    def _parse_best_odds(self, odds_data: Dict, 
                         event: OddsApiIoEvent) -> Optional[OddsApiIoBestOdds]:
        """解析赔率数据，提取最优值"""
        bookmakers = odds_data.get('bookmakers', {})
        
        if not bookmakers:
            return None
        
        # 收集各博彩公司的赔率
        ml_odds = []      # ML (胜平负)
        spread_odds = []  # Spread (让球盘)
        totals_odds = []  # Totals (大小球)
        
        for bm_name, markets in bookmakers.items():
            if not markets:
                continue
            
            for market in markets:
                market_name = market.get('name', '')
                market_odds = market.get('odds', [])
                updated_at = market.get('updatedAt', '')
                
                # ML 市场
                if market_name == 'ML' and market_odds:
                    ml_data = market_odds[0]
                    ml_odds.append({
                        'bookmaker': bm_name,
                        'home': float(ml_data.get('home', 0)),
                        'draw': float(ml_data.get('draw', 0)),
                        'away': float(ml_data.get('away', 0)),
                        'updated_at': updated_at
                    })
                
                # Spread 市场
                elif market_name == 'Spread' and market_odds:
                    spread_data = market_odds[0]
                    spread_odds.append({
                        'bookmaker': bm_name,
                        'hdp': float(spread_data.get('hdp', 0)),
                        'home': float(spread_data.get('home', 0)),
                        'away': float(spread_data.get('away', 0)),
                        'updated_at': updated_at
                    })
                
                # Totals 市场
                elif market_name == 'Totals' and market_odds:
                    totals_data = market_odds[0]
                    totals_odds.append({
                        'bookmaker': bm_name,
                        'hdp': float(totals_data.get('hdp', 0)),
                        'over': float(totals_data.get('over', 0)),
                        'under': float(totals_data.get('under', 0)),
                        'updated_at': updated_at
                    })
        
        # 提取最优赔率
        if not ml_odds:
            return None
        
        # ML 最优
        best_home = max(ml_odds, key=lambda x: x['home'])
        best_away = max(ml_odds, key=lambda x: x['away'])
        best_draw = max(ml_odds, key=lambda x: x['draw']) if ml_odds[0]['draw'] > 0 else None
        
        # 计算市场概率 (使用平均赔率倒数)
        avg_home = sum(x['home'] for x in ml_odds) / len(ml_odds)
        avg_away = sum(x['away'] for x in ml_odds) / len(ml_odds)
        avg_draw = sum(x['draw'] for x in ml_odds) / len(ml_odds) if ml_odds[0]['draw'] > 0 else 0
        
        market_prob_home = 1 / avg_home if avg_home > 0 else 0
        market_prob_away = 1 / avg_away if avg_away > 0 else 0
        market_prob_draw = 1 / avg_draw if avg_draw > 0 else 0
        
        # Spread 最优
        best_spread_home = None
        best_spread_away = None
        if spread_odds:
            best_spread_home = max(spread_odds, key=lambda x: x['home'])
            best_spread_away = max(spread_odds, key=lambda x: x['away'])
        
        # Totals 最优
        best_totals_over = None
        best_totals_under = None
        if totals_odds:
            best_totals_over = max(totals_odds, key=lambda x: x['over'])
            best_totals_under = max(totals_odds, key=lambda x: x['under'])
        
        return OddsApiIoBestOdds(
            event_id=event.event_id,
            home_team=event.home_team,
            away_team=event.away_team,
            league=event.league,
            home_odds=best_home['home'],
            home_bookmaker=best_home['bookmaker'],
            draw_odds=best_draw['draw'] if best_draw else 0.0,
            draw_bookmaker=best_draw['bookmaker'] if best_draw else '',
            away_odds=best_away['away'],
            away_bookmaker=best_away['bookmaker'],
            spread_hdp=best_spread_home['hdp'] if best_spread_home else 0.0,
            spread_home_odds=best_spread_home['home'] if best_spread_home else 0.0,
            spread_home_bookmaker=best_spread_home['bookmaker'] if best_spread_home else '',
            spread_away_odds=best_spread_away['away'] if best_spread_away else 0.0,
            spread_away_bookmaker=best_spread_away['bookmaker'] if best_spread_away else '',
            totals_hdp=best_totals_over['hdp'] if best_totals_over else 0.0,
            totals_over_odds=best_totals_over['over'] if best_totals_over else 0.0,
            totals_over_bookmaker=best_totals_over['bookmaker'] if best_totals_over else '',
            totals_under_odds=best_totals_under['under'] if best_totals_under else 0.0,
            totals_under_bookmaker=best_totals_under['bookmaker'] if best_totals_under else '',
            market_prob_home=round(market_prob_home, 4),
            market_prob_draw=round(market_prob_draw, 4),
            market_prob_away=round(market_prob_away, 4),
            updated_at=best_home['updated_at']
        )
    
    def get_league_events_with_odds(self, competition_code: str) -> List[OddsApiIoBestOdds]:
        """
        根据联赛代码获取赔率
        
        Args:
            competition_code: Football-Data.org 联赛代码 (PL, BL1, CSL等)
        
        Returns:
            最优赔率列表
        """
        league_slug = self.LEAGUE_MAPPING.get(competition_code)
        
        if not league_slug:
            logger.warning(f"未知联赛代码: {competition_code}")
            return []
        
        return self.get_best_odds(sport='football', league=league_slug)
    
    def normalize_team_name(self, name: str) -> str:
        """规范化球队名称"""
        # 直接映射
        if name in self.TEAM_NAME_NORMALIZE:
            return self.TEAM_NAME_NORMALIZE[name]
        
        # 通用规则
        normalized = name
        normalized = normalized.replace('&', 'and')
        normalized = normalized.replace(' FC', '')
        normalized = normalized.replace(' AFC', '')
        
        return normalized.strip()


# 测试代码
if __name__ == "__main__":
    import os
    
    api_key = os.environ.get('ODDS_API_IO_KEY', '')
    
    if api_key:
        config = OddsApiIoConfig(api_key=api_key)
        collector = OddsApiIoCollector(config)
        
        # 测试获取英超赔率
        print("=" * 60)
        print("测试 Odds-API.io")
        print("=" * 60)
        
        # 获取博彩公司
        bookmakers = collector.get_bookmakers()
        print(f"博彩公司总数: {len(bookmakers)}")
        
        # 获取英超赔率
        best_odds = collector.get_league_events_with_odds('PL')
        
        for o in best_odds[:5]:
            print(f"\n{o.home_team} vs {o.away_team}")
            print(f"  ML: {o.home_odds} / {o.draw_odds} / {o.away_odds}")
            print(f"  博彩公司: {o.home_bookmaker} / {o.draw_bookmaker} / {o.away_bookmaker}")
            if o.spread_hdp:
                print(f"  让球: {o.spread_hdp} -> {o.spread_home_odds} / {o.spread_away_odds}")
            if o.totals_hdp:
                print(f"  大小球: {o.totals_hdp} -> {o.totals_over_odds} / {o.totals_under_odds}")
        
        print(f"\n剩余请求次数: {collector.rate_limit_remaining}")
    
    else:
        print("请设置 ODDS_API_IO_KEY 环境变量")