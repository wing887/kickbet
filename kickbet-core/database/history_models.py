"""
KickBet历史比赛数据库模块

功能:
- 历史比赛结果存储 (所有联赛历史数据)
- 联赛/赛季/球队统一管理
- 数据同步追踪
- 可扩展架构 (支持新增联赛)

数据库设计:
├── leagues (联赛定义表)
├── seasons (赛季定义表)
├── teams (球队主表)
├── team_season_mappings (球队-赛季关联)
├── historical_matches (历史比赛核心表)
├── match_statistics (比赛详细统计)
├── sync_logs (同步日志)

使用 SQLAlchemy ORM
"""

import os
import json
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from decimal import Decimal

from sqlalchemy import create_engine, Column, String, Float, Integer, Boolean, DateTime, Date, Text, ForeignKey, JSON, Index, Numeric, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.pool import StaticPool

# ==================== 数据库配置 ====================

# 独立数据库文件 (历史比赛数据)
HISTORY_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'history_matches.db')
os.makedirs(os.path.dirname(HISTORY_DB_PATH), exist_ok=True)

# 创建引擎 (SQLite)
engine = create_engine(
    f'sqlite:///{HISTORY_DB_PATH}',
    connect_args={'check_same_thread': False},
    poolclass= StaticPool,
    echo=False
)

# 会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 基类
Base = declarative_base()


# ==================== 联赛定义表 ====================

class League(Base):
    """
    联赛定义表 - 统一管理所有联赛
    
    可扩展设计：添加新联赛只需INSERT一条记录
    """
    __tablename__ = 'leagues'
    
    league_id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), unique=True, nullable=False)  # PL, LL, BL, SA, L1, WC, CL, EL...
    name = Column(String(100), nullable=False)  # Premier League, La Liga...
    country = Column(String(50), nullable=True)  # England, Spain, Germany...
    tier = Column(Integer, default=1)  # 1=顶级联赛, 2=次级联赛
    
    # API配置
    api_source = Column(String(30), default='football-data.org')  # 数据来源
    api_league_code = Column(String(20), nullable=True)  # API中的联赛代码 (如 'PL' for Football-Data.org)
    
    # 状态
    is_active = Column(Boolean, default=True)  # 是否活跃联赛
    priority = Column(Integer, default=5)  # 数据采集优先级 (1-10, 10最高)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    seasons = relationship("Season", back_populates="league")
    
    def to_dict(self) -> Dict:
        return {
            'league_id': self.league_id,
            'code': self.code,
            'name': self.name,
            'country': self.country,
            'tier': self.tier,
            'api_source': self.api_source,
            'is_active': self.is_active
        }


# ==================== 赛季定义表 ====================

class Season(Base):
    """
    赛季定义表 - 追踪每个联赛的每个赛季
    
    支持:
    - 跨年度赛季 (如英超2023-24)
    - 单年度赛季 (如世界杯2022)
    """
    __tablename__ = 'seasons'
    
    season_id = Column(Integer, primary_key=True, autoincrement=True)
    league_id = Column(Integer, ForeignKey('leagues.league_id'), nullable=False)
    
    # 赛季标识 (如 "2023-24" 或 "2022")
    season_code = Column(String(20), nullable=False)  # "2023-24", "2022"
    start_year = Column(Integer, nullable=False)  # 2023
    end_year = Column(Integer, nullable=True)  # 2024 (跨年度赛季)
    
    # 当前状态
    current_matchday = Column(Integer, default=0)  # 当前比赛轮次
    total_matchdays = Column(Integer, default=38)  # 总轮次 (英超38轮, 西甲38轮, 德甲34轮)
    status = Column(String(20), default='active')  # active/archived/upcoming
    
    # 数据同步状态
    last_sync_at = Column(DateTime, nullable=True)
    matches_synced = Column(Integer, default=0)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    league = relationship("League", back_populates="seasons")
    team_mappings = relationship("TeamSeasonMapping", back_populates="season")
    matches = relationship("HistoricalMatch", back_populates="season")
    sync_logs = relationship("SyncLog", back_populates="season")
    
    # 唯一约束: 每联赛每赛季唯一
    __table_args__ = (UniqueConstraint('league_id', 'season_code', name='uq_league_season'),)
    
    def to_dict(self) -> Dict:
        return {
            'season_id': self.season_id,
            'league_id': self.league_id,
            'season_code': self.season_code,
            'start_year': self.start_year,
            'end_year': self.end_year,
            'current_matchday': self.current_matchday,
            'status': self.status,
            'matches_synced': self.matches_synced
        }


# ==================== 球队主表 ====================

class Team(Base):
    """
    球队主表 - 全局唯一球队标识
    
    支持:
    - 跨联赛球队 (如曼城在英超+欧冠)
    - 名称变体 (aliases JSON)
    """
    __tablename__ = 'teams'
    
    team_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 基本信息
    name = Column(String(100), nullable=False)  # Manchester City FC
    short_name = Column(String(50), nullable=True)  # Man City
    country = Column(String(50), nullable=True)  # England
    
    # 名称变体 (JSON数组)
    aliases = Column(JSON, nullable=True)  # ["Man City", "Manchester City", "曼城"]
    
    # 其他信息
    founded_year = Column(Integer, nullable=True)
    stadium = Column(String(100), nullable=True)
    
    # API标识映射
    football_data_id = Column(Integer, nullable=True, unique=True)  # Football-Data.org ID
    api_football_id = Column(Integer, nullable=True)  # API-Football ID (预留)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    season_mappings = relationship("TeamSeasonMapping", back_populates="team")
    
    def to_dict(self) -> Dict:
        return {
            'team_id': self.team_id,
            'name': self.name,
            'short_name': self.short_name,
            'country': self.country,
            'aliases': self.aliases or [],
            'football_data_id': self.football_data_id
        }


# ==================== 球队-赛季关联表 ====================

class TeamSeasonMapping(Base):
    """
    球队-赛季关联表 - 追踪球队在不同赛季的归属
    
    用途:
    - 查询某赛季参赛球队
    - 查询某球队历史赛季
    """
    __tablename__ = 'team_season_mappings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(Integer, ForeignKey('teams.team_id'), nullable=False)
    season_id = Column(Integer, ForeignKey('seasons.season_id'), nullable=False)
    
    # 赛季中的表现
    final_position = Column(Integer, nullable=True)  # 最终排名
    points = Column(Integer, nullable=True)  # 积分
    wins = Column(Integer, nullable=True)
    draws = Column(Integer, nullable=True)
    losses = Column(Integer, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联
    team = relationship("Team", back_populates="season_mappings")
    season = relationship("Season", back_populates="team_mappings")
    
    # 唯一约束: 每球队每赛季唯一
    __table_args__ = (UniqueConstraint('team_id', 'season_id', name='uq_team_season'),)


# ==================== 历史比赛核心表 ====================

class HistoricalMatch(Base):
    """
    历史比赛核心表 - 存储所有历史比赛结果
    
    支持:
    - 五大联赛历史
    - 世界杯历史
    - 欧冠/欧联历史
    - 任意联赛历史
    
    数据来源: Football-Data.org, API-Football, 手动导入
    """
    __tablename__ = 'historical_matches'
    
    # 主键 (自增)
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 比赛唯一标识 (组合)
    match_source_id = Column(String(50), nullable=False)  # API原始ID
    
    # 联赛/赛季
    league_id = Column(Integer, ForeignKey('leagues.league_id'), nullable=False)
    season_id = Column(Integer, ForeignKey('seasons.season_id'), nullable=False)
    
    # 球队
    home_team_id = Column(Integer, ForeignKey('teams.team_id'), nullable=False)
    away_team_id = Column(Integer, ForeignKey('teams.team_id'), nullable=False)
    
    # 比赛信息
    match_date = Column(Date, nullable=False)  # 比赛日期
    matchday = Column(Integer, nullable=True)  # 比赛轮次 (1-38)
    
    # 比赛结果
    home_score = Column(Integer, nullable=False)  # 主队进球
    away_score = Column(Integer, nullable=False)  # 客队进球
    result = Column(String(1), nullable=False)  # H/D/A (主胜/平/客胜)
    
    # 半场比分 (可选)
    half_time_home = Column(Integer, nullable=True)
    half_time_away = Column(Integer, nullable=True)
    
    # 比赛状态
    status = Column(String(20), default='FINISHED')  # FINISHED/SCHEDULED/CANCELLED/POSTPONED
    
    # 数据来源
    source_api = Column(String(30), default='football-data.org')
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    season = relationship("Season", back_populates="matches")
    statistics = relationship("MatchStatistic", back_populates="match")
    
    # 索引
    __table_args__ = (
        Index('idx_match_date', 'match_date'),
        Index('idx_league_season', 'league_id', 'season_id'),
        Index('idx_home_team', 'home_team_id'),
        Index('idx_away_team', 'away_team_id'),
        UniqueConstraint('match_source_id', 'source_api', name='uq_match_source'),
    )
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'match_source_id': self.match_source_id,
            'league_id': self.league_id,
            'season_id': self.season_id,
            'home_team_id': self.home_team_id,
            'away_team_id': self.away_team_id,
            'match_date': self.match_date.isoformat() if self.match_date else None,
            'matchday': self.matchday,
            'home_score': self.home_score,
            'away_score': self.away_score,
            'result': self.result,
            'status': self.status
        }


# ==================== 比赛详细统计表 ====================

class MatchStatistic(Base):
    """
    比赛详细统计表 - 可选，存储比赛详细数据
    
    包括: 射门、角球、犯规、控球率等
    """
    __tablename__ = 'match_statistics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(Integer, ForeignKey('historical_matches.id'), nullable=False)
    
    # 统计类型
    stats_type = Column(String(30), nullable=False)  # shots/corners/fouls/possession/cards
    
    # 数值
    home_value = Column(Float, nullable=True)
    away_value = Column(Float, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联
    match = relationship("HistoricalMatch", back_populates="statistics")
    
    # 唯一约束: 每比赛每统计类型唯一
    __table_args__ = (UniqueConstraint('match_id', 'stats_type', name='uq_match_stats'),)


# ==================== 同步日志表 ====================

class SyncLog(Base):
    """
    同步日志表 - 追踪数据同步状态
    
    用途:
    - 监控同步进度
    - 检测同步失败
    - 诊断数据问题
    """
    __tablename__ = 'sync_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 同步目标
    league_id = Column(Integer, ForeignKey('leagues.league_id'), nullable=False)
    season_id = Column(Integer, ForeignKey('seasons.season_id'), nullable=False)
    
    # 同步信息
    sync_type = Column(String(20), nullable=False)  # full/daily/weekly/manual
    sync_time = Column(DateTime, default=datetime.utcnow)
    
    # 同步结果
    matches_added = Column(Integer, default=0)
    matches_updated = Column(Integer, default=0)
    matches_skipped = Column(Integer, default=0)
    
    # 状态
    status = Column(String(20), default='success')  # success/failed/partial
    error_message = Column(Text, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联
    season = relationship("Season", back_populates="sync_logs")
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'league_id': self.league_id,
            'season_id': self.season_id,
            'sync_type': self.sync_type,
            'sync_time': self.sync_time.isoformat(),
            'matches_added': self.matches_added,
            'matches_updated': self.matches_updated,
            'status': self.status,
            'error_message': self.error_message
        }


# ==================== 数据库管理器 ====================

class HistoryDBManager:
    """
    历史比赛数据库管理器
    
    功能:
    - 数据库初始化
    - 联赛/赛季/球队管理
    - 比赛数据 CRUD
    - 同步日志记录
    """
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    def init_db(self):
        """初始化数据库，创建所有表"""
        Base.metadata.create_all(self.engine)
        print(f"[HistoryDB] 数据库初始化完成: {HISTORY_DB_PATH}")
        
        # 初始化五大联赛
        self._init_default_leagues()
    
    def _init_default_leagues(self):
        """初始化五大联赛定义"""
        session = self.SessionLocal()
        try:
            # 检查是否已有联赛
            existing = session.query(League).count()
            if existing > 0:
                return
            
            # 五大联赛定义
            default_leagues = [
                {'code': 'PL', 'name': 'Premier League', 'country': 'England', 'tier': 1, 
                 'api_source': 'football-data.org', 'api_league_code': 'PL', 'priority': 10},
                {'code': 'LL', 'name': 'La Liga', 'country': 'Spain', 'tier': 1,
                 'api_source': 'football-data.org', 'api_league_code': 'PD', 'priority': 9},
                {'code': 'BL', 'name': 'Bundesliga', 'country': 'Germany', 'tier': 1,
                 'api_source': 'football-data.org', 'api_league_code': 'BL1', 'priority': 8},
                {'code': 'SA', 'name': 'Serie A', 'country': 'Italy', 'tier': 1,
                 'api_source': 'football-data.org', 'api_league_code': 'SA', 'priority': 7},
                {'code': 'L1', 'name': 'Ligue 1', 'country': 'France', 'tier': 1,
                 'api_source': 'football-data.org', 'api_league_code': 'FL1', 'priority': 6},
                {'code': 'WC', 'name': 'World Cup', 'country': 'International', 'tier': 0,
                 'api_source': 'api-football', 'api_league_code': None, 'priority': 10},
                {'code': 'CL', 'name': 'Champions League', 'country': 'Europe', 'tier': 0,
                 'api_source': 'football-data.org', 'api_league_code': 'CL', 'priority': 8},
                {'code': 'EL', 'name': 'Europa League', 'country': 'Europe', 'tier': 0,
                 'api_source': 'football-data.org', 'api_league_code': 'EL', 'priority': 5},
                {'code': 'ECL', 'name': 'Europa Conference League', 'country': 'Europe', 'tier': 0,
                 'api_source': 'football-data.org', 'api_league_code': 'ELC', 'priority': 4},
            ]
            
            for league_data in default_leagues:
                league = League(**league_data)
                session.add(league)
            
            session.commit()
            print(f"[HistoryDB] 已初始化 {len(default_leagues)} 个联赛定义")
            
        except Exception as e:
            session.rollback()
            print(f"[HistoryDB] 初始化联赛失败: {e}")
        finally:
            session.close()
    
    def get_session(self) -> Session:
        """获取数据库会话"""
        return self.SessionLocal()
    
    def get_league_by_code(self, code: str) -> Optional[int]:
        """根据代码获取联赛ID"""
        session = self.get_session()
        try:
            league = session.query(League).filter(League.code == code).first()
            return league.league_id if league else None
        finally:
            session.close()
    
    def get_all_active_leagues(self) -> List[League]:
        """获取所有活跃联赛"""
        session = self.get_session()
        try:
            return session.query(League).filter(League.is_active == True).order_by(League.priority.desc()).all()
        finally:
            session.close()
    
    def add_season(self, league_code: str, season_code: str, start_year: int, 
                   end_year: Optional[int] = None, total_matchdays: int = 38) -> int:
        """添加赛季，返回season_id"""
        session = self.get_session()
        try:
            league = session.query(League).filter(League.code == league_code).first()
            if not league:
                raise ValueError(f"联赛不存在: {league_code}")
            
            # 检查是否已存在
            existing = session.query(Season).filter(
                Season.league_id == league.league_id,
                Season.season_code == season_code
            ).first()
            
            if existing:
                return existing.season_id
            
            season = Season(
                league_id=league.league_id,
                season_code=season_code,
                start_year=start_year,
                end_year=end_year,
                total_matchdays=total_matchdays
            )
            session.add(season)
            session.commit()
            session.refresh(season)
            print(f"[HistoryDB] 添加赛季: {league_code} {season_code} (season_id={season.season_id})")
            return season.season_id
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def add_team(self, name: str, football_data_id: Optional[int] = None,
                 short_name: Optional[str] = None, country: Optional[str] = None,
                 aliases: Optional[List[str]] = None) -> int:
        """添加球队，返回team_id"""
        session = self.get_session()
        try:
            # 检查是否已存在 (按API ID)
            if football_data_id:
                existing = session.query(Team).filter(
                    Team.football_data_id == football_data_id
                ).first()
                if existing:
                    return existing.team_id
            
            # 检查是否已存在 (按名称)
            existing = session.query(Team).filter(Team.name == name).first()
            if existing:
                return existing.team_id
            
            team = Team(
                name=name,
                short_name=short_name,
                country=country,
                football_data_id=football_data_id,
                aliases=aliases or []
            )
            session.add(team)
            session.commit()
            session.refresh(team)
            print(f"[HistoryDB] 添加球队: {name} (team_id={team.team_id})")
            return team.team_id
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def add_match(self, match_source_id: str, league_id: int, season_id: int,
                  home_team_id: int, away_team_id: int, match_date: date,
                  home_score: int, away_score: int, matchday: Optional[int] = None,
                  half_time_home: Optional[int] = None, half_time_away: Optional[int] = None,
                  source_api: str = 'football-data.org') -> HistoricalMatch:
        """添加历史比赛"""
        session = self.get_session()
        try:
            # 检查是否已存在
            existing = session.query(HistoricalMatch).filter(
                HistoricalMatch.match_source_id == match_source_id,
                HistoricalMatch.source_api == source_api
            ).first()
            
            if existing:
                # 更新比分 (如果比赛已完成)
                if existing.status == 'SCHEDULED' and home_score is not None:
                    existing.home_score = home_score
                    existing.away_score = away_score
                    existing.result = 'H' if home_score > away_score else ('D' if home_score == away_score else 'A')
                    existing.status = 'FINISHED'
                    existing.half_time_home = half_time_home
                    existing.half_time_away = half_time_away
                    session.commit()
                    print(f"[HistoryDB] 更新比赛结果: {match_source_id}")
                return existing
            
            # 计算结果
            result = 'H' if home_score > away_score else ('D' if home_score == away_score else 'A')
            
            match = HistoricalMatch(
                match_source_id=match_source_id,
                league_id=league_id,
                season_id=season_id,
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                match_date=match_date,
                matchday=matchday,
                home_score=home_score,
                away_score=away_score,
                result=result,
                half_time_home=half_time_home,
                half_time_away=half_time_away,
                status='FINISHED',
                source_api=source_api
            )
            session.add(match)
            session.commit()
            return match
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_team_matches(self, team_id: int, season_id: Optional[int] = None,
                         limit: int = 100) -> List[HistoricalMatch]:
        """获取球队历史比赛"""
        session = self.get_session()
        try:
            query = session.query(HistoricalMatch).filter(
                (HistoricalMatch.home_team_id == team_id) | 
                (HistoricalMatch.away_team_id == team_id)
            )
            
            if season_id:
                query = query.filter(HistoricalMatch.season_id == season_id)
            
            return query.order_by(HistoricalMatch.match_date.desc()).limit(limit).all()
            
        finally:
            session.close()
    
    def get_head_to_head(self, team_a_id: int, team_b_id: int, 
                         limit: int = 20) -> List[HistoricalMatch]:
        """获取两队历史交锋"""
        session = self.get_session()
        try:
            return session.query(HistoricalMatch).filter(
                ((HistoricalMatch.home_team_id == team_a_id) & (HistoricalMatch.away_team_id == team_b_id)) |
                ((HistoricalMatch.home_team_id == team_b_id) & (HistoricalMatch.away_team_id == team_a_id))
            ).order_by(HistoricalMatch.match_date.desc()).limit(limit).all()
            
        finally:
            session.close()
    
    def get_head_to_head_stats(self, team_a_id: int, team_b_id: int,
                                limit: int = 10) -> Dict:
        """计算两队历史交锋统计
        
        返回:
        - total_matches: 交锋总场次
        - team_a_wins: A队胜场数
        - team_b_wins: B队胜场数  
        - draws: 平局数
        - team_a_win_rate: A队胜率
        - team_b_win_rate: B队胜率
        - draw_rate: 平局率
        - avg_total_goals: 平均总进球
        - avg_team_a_goals: A队场均进球
        - avg_team_b_goals: B队场均进球
        - recent_results: 最近交锋结果列表 ['W','D','L'...]
        - team_a_as_home_wins: A队主场胜场
        - team_a_as_away_wins: A队客场胜场
        """
        matches = self.get_head_to_head(team_a_id, team_b_id, limit)
        
        if not matches:
            return {
                'total_matches': 0,
                'team_a_wins': 0,
                'team_b_wins': 0,
                'draws': 0,
                'team_a_win_rate': 0,
                'team_b_win_rate': 0,
                'draw_rate': 0,
                'avg_total_goals': 0,
                'avg_team_a_goals': 0,
                'avg_team_b_goals': 0,
                'recent_results': [],
                'note': '无历史交锋数据'
            }
        
        team_a_wins = 0
        team_b_wins = 0
        draws = 0
        team_a_goals_total = 0
        team_b_goals_total = 0
        team_a_as_home_wins = 0
        team_a_as_away_wins = 0
        recent_results = []
        
        for m in matches:
            # 判断A队是主队还是客队
            is_a_home = (m.home_team_id == team_a_id)
            
            # A队进球
            if is_a_home:
                a_goals = m.home_score
                b_goals = m.away_score
            else:
                a_goals = m.away_score
                b_goals = m.home_score
            
            team_a_goals_total += a_goals
            team_b_goals_total += b_goals
            
            # 判断结果
            if a_goals > b_goals:
                team_a_wins += 1
                recent_results.append('W')
                if is_a_home:
                    team_a_as_home_wins += 1
                else:
                    team_a_as_away_wins += 1
            elif a_goals < b_goals:
                team_b_wins += 1
                recent_results.append('L')
            else:
                draws += 1
                recent_results.append('D')
        
        total = len(matches)
        
        return {
            'total_matches': total,
            'team_a_wins': team_a_wins,
            'team_b_wins': team_b_wins,
            'draws': draws,
            'team_a_win_rate': team_a_wins / total,
            'team_b_win_rate': team_b_wins / total,
            'draw_rate': draws / total,
            'avg_total_goals': (team_a_goals_total + team_b_goals_total) / total,
            'avg_team_a_goals': team_a_goals_total / total,
            'avg_team_b_goals': team_b_goals_total / total,
            'recent_results': recent_results,
            'team_a_as_home_wins': team_a_as_home_wins,
            'team_a_as_away_wins': team_a_as_away_wins,
            'team_a_home_matches': sum(1 for m in matches if m.home_team_id == team_a_id),
            'team_a_away_matches': sum(1 for m in matches if m.away_team_id == team_a_id)
        }
    
    def add_sync_log(self, league_id: int, season_id: int, sync_type: str,
                     matches_added: int = 0, matches_updated: int = 0,
                     matches_skipped: int = 0, status: str = 'success',
                     error_message: Optional[str] = None) -> SyncLog:
        """添加同步日志"""
        session = self.get_session()
        try:
            log = SyncLog(
                league_id=league_id,
                season_id=season_id,
                sync_type=sync_type,
                matches_added=matches_added,
                matches_updated=matches_updated,
                matches_skipped=matches_skipped,
                status=status,
                error_message=error_message
            )
            session.add(log)
            
            # 更新赛季同步状态
            season = session.query(Season).filter(Season.season_id == season_id).first()
            if season:
                season.last_sync_at = datetime.utcnow()
                season.matches_synced = matches_added + matches_updated
            
            session.commit()
            return log
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_team_stats_from_history(self, team_id: int, season_id: Optional[int] = None,
                                     recent_matches: int = 5) -> Dict:
        """从历史比赛计算球队统计
        
        返回:
        - home_scored_avg: 主场场均进球
        - home_conceded_avg: 主场场均失球
        - away_scored_avg: 客场场均进球
        - away_conceded_avg: 客场场均失球
        - recent_form: 近N场状态
        """
        session = self.get_session()
        try:
            # 构建查询
            query = session.query(HistoricalMatch).filter(
                (HistoricalMatch.home_team_id == team_id) |
                (HistoricalMatch.away_team_id == team_id)
            ).filter(HistoricalMatch.status == 'FINISHED')
            
            if season_id:
                query = query.filter(HistoricalMatch.season_id == season_id)
            
            matches = query.order_by(HistoricalMatch.match_date.desc()).all()
            
            if not matches:
                return {'error': 'No matches found'}
            
            # 主场统计
            home_matches = [m for m in matches if m.home_team_id == team_id]
            home_scored = sum(m.home_score for m in home_matches)
            home_conceded = sum(m.away_score for m in home_matches)
            
            # 客场统计
            away_matches = [m for m in matches if m.away_team_id == team_id]
            away_scored = sum(m.away_score for m in away_matches)
            away_conceded = sum(m.home_score for m in away_matches)
            
            # 近期状态 (最近N场)
            recent = matches[:recent_matches]
            recent_form = []
            for m in recent:
                if m.home_team_id == team_id:
                    result = 'W' if m.home_score > m.away_score else ('D' if m.home_score == m.away_score else 'L')
                else:
                    result = 'W' if m.away_score > m.home_score else ('D' if m.away_score == m.home_score else 'L')
                recent_form.append(result)
            
            return {
                'team_id': team_id,
                'total_matches': len(matches),
                'home_matches': len(home_matches),
                'away_matches': len(away_matches),
                'home_scored_avg': home_scored / len(home_matches) if home_matches else 0,
                'home_conceded_avg': home_conceded / len(home_matches) if home_matches else 0,
                'away_scored_avg': away_scored / len(away_matches) if away_matches else 0,
                'away_conceded_avg': away_conceded / len(away_matches) if away_matches else 0,
                'recent_form': ''.join(recent_form),
                'recent_matches': len(recent)
            }
            
        finally:
            session.close()
    
    def get_stats_summary(self) -> Dict:
        """获取数据库统计概览"""
        session = self.get_session()
        try:
            return {
                'leagues': session.query(League).count(),
                'seasons': session.query(Season).count(),
                'teams': session.query(Team).count(),
                'matches': session.query(HistoricalMatch).count(),
                'sync_logs': session.query(SyncLog).count(),
                'db_path': HISTORY_DB_PATH
            }
        finally:
            session.close()


# ==================== 初始化函数 ====================

def init_history_db():
    """初始化历史比赛数据库"""
    manager = HistoryDBManager()
    manager.init_db()
    return manager


# 导出
__all__ = [
    'Base', 'engine', 'SessionLocal',
    'League', 'Season', 'Team', 'TeamSeasonMapping',
    'HistoricalMatch', 'MatchStatistic', 'SyncLog',
    'HistoryDBManager', 'init_history_db', 'HISTORY_DB_PATH'
]