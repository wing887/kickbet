"""
KickBet预计算数据库模块

功能:
- SQLite数据库连接
- 用户表 (用户数据)
- 系统预测缓存表 (预计算结果, 版本管理)  ← 新增
- 赔率历史表 (赔率变化追踪)               ← 新增
- 比赛缓存表 (比赛基础信息)
- 用户预测追踪表 (用户个人记录)

使用SQLAlchemy ORM
"""

import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal

from sqlalchemy import create_engine, Column, String, Float, Integer, Boolean, DateTime, Text, ForeignKey, JSON, Index, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.pool import StaticPool

# ==================== 数据库配置 ====================

# 数据库路径 (项目根目录)
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'kickbet.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# 创建引擎 (SQLite)
engine = create_engine(
    f'sqlite:///{DB_PATH}',
    connect_args={'check_same_thread': False},
    poolclass=StaticPool,
    echo=False
)

# 会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 基类
Base = declarative_base()


# ==================== 预计算缓存表 ====================

class MatchCache(Base):
    """
    比赛缓存表 - 预计算架构
    
    存储比赛基础信息，支持预计算查询
    """
    __tablename__ = 'matches_cache'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(String(50), unique=True, nullable=False, index=True)  # Football-Data.org ID
    league_code = Column(String(10), nullable=False, index=True)
    league_name = Column(String(50), nullable=True)
    
    # 球队信息
    home_team_id = Column(Integer, nullable=False)
    home_team_name = Column(String(100), nullable=False)
    away_team_id = Column(Integer, nullable=False)
    away_team_name = Column(String(100), nullable=False)
    
    # 比赛时间
    match_time = Column(DateTime, nullable=True, index=True)
    status = Column(String(20), default='SCHEDULED')  # SCHEDULED/TIMED/LIVE/FINISHED
    
    # 比赛结果 (赛后更新)
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    result = Column(String(1), nullable=True)  # H/D/A
    
    # 数据来源
    source = Column(String(30), default='football-data.org')
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    odds_history = relationship("OddsHistory", back_populates="match")
    predictions = relationship("SystemPrediction", back_populates="match")
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'match_id': self.match_id,
            'league_code': self.league_code,
            'league_name': self.league_name,
            'home_team_id': self.home_team_id,
            'home_team_name': self.home_team_name,
            'away_team_id': self.away_team_id,
            'away_team_name': self.away_team_name,
            'match_time': self.match_time.isoformat() if self.match_time else None,
            'status': self.status,
            'home_score': self.home_score,
            'away_score': self.away_score,
            'result': self.result,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class OddsHistory(Base):
    """
    赔率历史表 - 预计算架构
    
    存储每次获取的赔率数据，支持变化检测
    """
    __tablename__ = 'odds_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(String(50), ForeignKey('matches_cache.match_id'), nullable=False, index=True)
    bookmaker = Column(String(50), nullable=False, index=True)
    
    # 胜平负赔率
    home_odds = Column(Float, nullable=False)
    draw_odds = Column(Float, nullable=False)
    away_odds = Column(Float, nullable=False)
    
    # 市场隐含概率
    market_prob_home = Column(Float, nullable=True)
    market_prob_draw = Column(Float, nullable=True)
    market_prob_away = Column(Float, nullable=True)
    
    # 亚洲盘赔率 (可选)
    spread_hdp = Column(Float, nullable=True)
    spread_home_odds = Column(Float, nullable=True)
    spread_away_odds = Column(Float, nullable=True)
    
    # 大小球赔率 (可选)
    totals_hdp = Column(Float, nullable=True)
    totals_over_odds = Column(Float, nullable=True)
    totals_under_odds = Column(Float, nullable=True)
    
    # 时间戳
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # 变化检测标记
    change_detected = Column(Boolean, default=False)
    change_pct_home = Column(Float, nullable=True)
    change_pct_draw = Column(Float, nullable=True)
    change_pct_away = Column(Float, nullable=True)
    significant_change = Column(Boolean, default=False)  # >5%变化
    
    # 关联比赛
    match = relationship("MatchCache", back_populates="odds_history")
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'match_id': self.match_id,
            'bookmaker': self.bookmaker,
            'home_odds': self.home_odds,
            'draw_odds': self.draw_odds,
            'away_odds': self.away_odds,
            'market_prob_home': self.market_prob_home,
            'market_prob_draw': self.market_prob_draw,
            'market_prob_away': self.market_prob_away,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None,
            'change_detected': self.change_detected,
            'significant_change': self.significant_change
        }
    
    def calculate_market_probs(self):
        """计算市场隐含概率"""
        if self.home_odds and self.draw_odds and self.away_odds:
            total = 1/self.home_odds + 1/self.draw_odds + 1/self.away_odds
            self.market_prob_home = (1/self.home_odds) / total
            self.market_prob_draw = (1/self.draw_odds) / total
            self.market_prob_away = (1/self.away_odds) / total


class SystemPrediction(Base):
    """
    系统预测缓存表 - 预计算架构
    
    存储Poisson模型预测结果，版本管理
    用户直接读取is_current=true的版本
    """
    __tablename__ = 'system_predictions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(String(50), ForeignKey('matches_cache.match_id'), nullable=False, index=True)
    
    # 版本管理
    prediction_version = Column(String(10), nullable=False)  # v1, v2, v3...
    is_current = Column(Boolean, default=True, index=True)
    trigger_reason = Column(String(50), nullable=False)  # first_generation/odds_change/news_impact/pre_match_adjust/manual_refresh
    
    # Poisson预测概率
    home_prob = Column(Float, nullable=False)
    draw_prob = Column(Float, nullable=False)
    away_prob = Column(Float, nullable=False)
    prediction = Column(String(1), nullable=False)  # H/D/A
    
    # 预期进球
    lambda_home = Column(Float, nullable=False)
    lambda_away = Column(Float, nullable=False)
    expected_home_goals = Column(Float, nullable=False)
    expected_away_goals = Column(Float, nullable=False)
    
    # 最可能比分
    most_likely_score = Column(String(10), nullable=False)
    
    # 大小球预测
    total_goals_expected = Column(Float, nullable=True)
    prob_over_2_5 = Column(Float, nullable=True)
    prob_under_2_5 = Column(Float, nullable=True)
    
    # 让球盘预测
    prob_home_cover_0_5 = Column(Float, nullable=True)
    prob_away_cover_0_5 = Column(Float, nullable=True)
    
    # Kelly比例 (基于当时最优赔率)
    kelly_home = Column(Float, nullable=True)
    kelly_draw = Column(Float, nullable=True)
    kelly_away = Column(Float, nullable=True)
    
    # 当前最优赔率 (生成预测时的赔率)
    best_home_odds = Column(Float, nullable=True)
    best_draw_odds = Column(Float, nullable=True)
    best_away_odds = Column(Float, nullable=True)
    best_bookmaker_home = Column(String(50), nullable=True)
    best_bookmaker_draw = Column(String(50), nullable=True)
    best_bookmaker_away = Column(String(50), nullable=True)
    
    # 完整预测数据 (JSON)
    score_distribution = Column(Text, nullable=True)  # JSON: {"2-0": 0.13, "1-0": 0.12, ...}
    totals_prediction_data = Column(Text, nullable=True)  # JSON: 大小球详细数据
    handicap_prediction_data = Column(Text, nullable=True)  # JSON: 让球盘详细数据
    value_bets_data = Column(Text, nullable=True)  # JSON: 价值投注列表
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # 关联比赛
    match = relationship("MatchCache", back_populates="predictions")
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'match_id': self.match_id,
            'prediction_version': self.prediction_version,
            'is_current': self.is_current,
            'trigger_reason': self.trigger_reason,
            'home_prob': self.home_prob,
            'draw_prob': self.draw_prob,
            'away_prob': self.away_prob,
            'prediction': self.prediction,
            'lambda_home': self.lambda_home,
            'lambda_away': self.lambda_away,
            'expected_home_goals': self.expected_home_goals,
            'expected_away_goals': self.expected_away_goals,
            'most_likely_score': self.most_likely_score,
            'prob_over_2_5': self.prob_over_2_5,
            'prob_under_2_5': self.prob_under_2_5,
            'kelly_home': self.kelly_home,
            'kelly_draw': self.kelly_draw,
            'kelly_away': self.kelly_away,
            'best_home_odds': self.best_home_odds,
            'best_draw_odds': self.best_draw_odds,
            'best_away_odds': self.best_away_odds,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def get_full_data(self) -> Dict:
        """获取完整预测数据"""
        data = self.to_dict()
        data['score_distribution'] = json.loads(self.score_distribution) if self.score_distribution else {}
        data['totals_prediction'] = json.loads(self.totals_prediction_data) if self.totals_prediction_data else None
        data['handicap_prediction'] = json.loads(self.handicap_prediction_data) if self.handicap_prediction_data else None
        data['value_bets'] = json.loads(self.value_bets_data) if self.value_bets_data else []
        return data


# ==================== 用户数据表 ====================

class UserModel(Base):
    """用户表"""
    __tablename__ = 'users'
    
    user_id = Column(String(50), primary_key=True)
    username = Column(String(30), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False, default='free')  # free/premium/admin
    is_active = Column(Boolean, default=True)
    
    # 用户偏好
    risk_preference = Column(String(20), default='half')  # quarter/half/full
    preferred_leagues = Column(Text, nullable=True)  # JSON: ["PL", "BL1"]
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # 关联用户预测追踪
    user_predictions = relationship("UserPredictionTrack", back_populates="user")
    
    def to_dict(self) -> Dict:
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'risk_preference': self.risk_preference,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }


class UserPredictionTrack(Base):
    """
    用户预测追踪表
    
    用户个人选择的预测记录，用于追踪用户行为
    (不同于系统预测缓存，这是用户个人的选择记录)
    """
    __tablename__ = 'user_prediction_tracks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey('users.user_id'), nullable=False, index=True)
    
    # 关联系统预测
    system_prediction_id = Column(Integer, ForeignKey('system_predictions.id'), nullable=True)
    match_id = Column(String(50), nullable=False, index=True)
    
    # 用户选择
    selected_outcome = Column(String(1), nullable=False)  # H/D/A
    selected_odds = Column(Float, nullable=False)
    selected_bookmaker = Column(String(50), nullable=True)
    
    # 用户投注金额 (可选)
    stake_amount = Column(Float, nullable=True)
    risk_mode = Column(String(20), nullable=True)  # conservative/balanced/aggressive
    
    # 结果追踪
    actual_result = Column(String(1), nullable=True)
    is_correct = Column(Boolean, nullable=True)
    profit_loss = Column(Float, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    settled_at = Column(DateTime, nullable=True)
    
    # 关联
    user = relationship("UserModel", back_populates="user_predictions")


class TeamStatsCache(Base):
    """
    球队统计缓存表
    
    存储球队攻防数据，用于Poisson预测
    """
    __tablename__ = 'team_stats_cache'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(Integer, unique=True, nullable=False, index=True)
    team_name = Column(String(100), nullable=False)
    league_code = Column(String(10), nullable=False, index=True)
    
    # 主场统计
    home_scored_avg = Column(Float, default=0.0)
    home_conceded_avg = Column(Float, default=0.0)
    home_played = Column(Integer, default=0)
    
    # 客场统计
    away_scored_avg = Column(Float, default=0.0)
    away_conceded_avg = Column(Float, default=0.0)
    away_played = Column(Integer, default=0)
    
    # 时间戳
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            'team_id': self.team_id,
            'team_name': self.team_name,
            'league_code': self.league_code,
            'home_scored_avg': self.home_scored_avg,
            'home_conceded_avg': self.home_conceded_avg,
            'home_played': self.home_played,
            'away_scored_avg': self.away_scored_avg,
            'away_conceded_avg': self.away_conceded_avg,
            'away_played': self.away_played,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# ==================== 数据库管理器 ====================

class PredictionCacheManager:
    """
    预计算缓存管理器
    
    核心功能:
    - 比赛缓存 CRUD
    - 赔率历史存储 + 变化检测
    - 预测版本管理
    - 用户读取当前预测
    """
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    def init_db(self):
        """初始化数据库 (创建所有表)"""
        Base.metadata.create_all(bind=self.engine)
        print(f"[DB] 预计算数据库初始化完成: {DB_PATH}")
    
    def get_session(self) -> Session:
        """获取数据库会话"""
        return self.SessionLocal()
    
    def close_session(self, session: Session):
        """关闭会话"""
        session.close()
    
    # ==================== 比赛缓存操作 ====================
    
    def save_match(self, match_data: Dict) -> Optional[MatchCache]:
        """保存/更新比赛缓存"""
        session = self.get_session()
        try:
            # 检查是否已存在
            existing = session.query(MatchCache).filter(
                MatchCache.match_id == match_data['match_id']
            ).first()
            
            if existing:
                # 更新
                existing.status = match_data.get('status', existing.status)
                existing.match_time = match_data.get('match_time', existing.match_time)
                existing.home_score = match_data.get('home_score')
                existing.away_score = match_data.get('away_score')
                existing.result = match_data.get('result')
                existing.updated_at = datetime.utcnow()
                session.commit()
                return existing
            
            # 新建
            match = MatchCache(
                match_id=match_data['match_id'],
                league_code=match_data['league_code'],
                league_name=match_data.get('league_name'),
                home_team_id=match_data['home_team_id'],
                home_team_name=match_data['home_team_name'],
                away_team_id=match_data['away_team_id'],
                away_team_name=match_data['away_team_name'],
                match_time=match_data.get('match_time'),
                status=match_data.get('status', 'SCHEDULED'),
                source=match_data.get('source', 'football-data.org')
            )
            session.add(match)
            session.commit()
            session.refresh(match)
            return match
        except Exception as e:
            session.rollback()
            print(f"[DB] 保存比赛失败: {e}")
            return None
        finally:
            self.close_session(session)
    
    def get_upcoming_matches(self, hours: int = 72, league: Optional[str] = None) -> List[MatchCache]:
        """获取即将进行的比赛"""
        session = self.get_session()
        try:
            now = datetime.utcnow()
            end_time = now + timedelta(hours=hours)
            
            query = session.query(MatchCache).filter(
                MatchCache.status.in_(['SCHEDULED', 'TIMED']),
                MatchCache.match_time >= now,
                MatchCache.match_time <= end_time
            )
            
            if league:
                query = query.filter(MatchCache.league_code == league)
            
            return query.order_by(MatchCache.match_time).all()
        finally:
            self.close_session(session)
    
    def get_match_by_id(self, match_id: str) -> Optional[MatchCache]:
        """获取单场比赛"""
        session = self.get_session()
        try:
            return session.query(MatchCache).filter(MatchCache.match_id == match_id).first()
        finally:
            self.close_session(session)
    
    # ==================== 赔率历史操作 ====================
    
    def save_odds_history(self, odds_data: Dict) -> Optional[OddsHistory]:
        """
        保存赔率历史
        
        自动检测与上一条记录的变化
        """
        session = self.get_session()
        try:
            # 计算市场概率
            home_odds = odds_data['home_odds']
            draw_odds = odds_data['draw_odds']
            away_odds = odds_data['away_odds']
            
            total_prob = 1/home_odds + 1/draw_odds + 1/away_odds
            market_prob_home = (1/home_odds) / total_prob
            market_prob_draw = (1/draw_odds) / total_prob
            market_prob_away = (1/away_odds) / total_prob
            
            # 获取上一条记录进行变化检测
            previous = session.query(OddsHistory).filter(
                OddsHistory.match_id == odds_data['match_id'],
                OddsHistory.bookmaker == odds_data['bookmaker']
            ).order_by(OddsHistory.recorded_at.desc()).first()
            
            change_detected = False
            significant_change = False
            change_pct_home = None
            change_pct_draw = None
            change_pct_away = None
            
            if previous:
                # 计算变化百分比
                if previous.home_odds > 0:
                    change_pct_home = abs(home_odds - previous.home_odds) / previous.home_odds * 100
                if previous.draw_odds > 0:
                    change_pct_draw = abs(draw_odds - previous.draw_odds) / previous.draw_odds * 100
                if previous.away_odds > 0:
                    change_pct_away = abs(away_odds - previous.away_odds) / previous.away_odds * 100
                
                # 检测变化
                max_change = max(
                    change_pct_home or 0,
                    change_pct_draw or 0,
                    change_pct_away or 0
                )
                change_detected = max_change > 0.1  # 任何变化
                significant_change = max_change > 5  # 显著变化 (>5%)
            
            # 创建新记录
            odds = OddsHistory(
                match_id=odds_data['match_id'],
                bookmaker=odds_data['bookmaker'],
                home_odds=home_odds,
                draw_odds=draw_odds,
                away_odds=away_odds,
                market_prob_home=market_prob_home,
                market_prob_draw=market_prob_draw,
                market_prob_away=market_prob_away,
                spread_hdp=odds_data.get('spread_hdp'),
                spread_home_odds=odds_data.get('spread_home_odds'),
                spread_away_odds=odds_data.get('spread_away_odds'),
                totals_hdp=odds_data.get('totals_hdp'),
                totals_over_odds=odds_data.get('totals_over_odds'),
                totals_under_odds=odds_data.get('totals_under_odds'),
                change_detected=change_detected,
                change_pct_home=change_pct_home,
                change_pct_draw=change_pct_draw,
                change_pct_away=change_pct_away,
                significant_change=significant_change
            )
            session.add(odds)
            session.commit()
            session.refresh(odds)
            return odds
        except Exception as e:
            session.rollback()
            print(f"[DB] 保存赔率历史失败: {e}")
            return None
        finally:
            self.close_session(session)
    
    def get_latest_odds(self, match_id: str, bookmaker: Optional[str] = None) -> Optional[OddsHistory]:
        """获取最新赔率"""
        session = self.get_session()
        try:
            query = session.query(OddsHistory).filter(
                OddsHistory.match_id == match_id
            )
            if bookmaker:
                query = query.filter(OddsHistory.bookmaker == bookmaker)
            return query.order_by(OddsHistory.recorded_at.desc()).first()
        finally:
            self.close_session(session)
    
    def get_odds_history(self, match_id: str, limit: int = 10) -> List[OddsHistory]:
        """获取赔率历史记录"""
        session = self.get_session()
        try:
            return session.query(OddsHistory).filter(
                OddsHistory.match_id == match_id
            ).order_by(OddsHistory.recorded_at.desc()).limit(limit).all()
        finally:
            self.close_session(session)
    
    def check_odds_change_threshold(self, match_id: str, threshold: float = 10.0) -> bool:
        """
        检查赔率变化是否超过阈值
        
        返回: True表示需要触发重新预测
        """
        session = self.get_session()
        try:
            # 获取最近两条记录
            recent = session.query(OddsHistory).filter(
                OddsHistory.match_id == match_id
            ).order_by(OddsHistory.recorded_at.desc()).limit(2).all()
            
            if len(recent) < 2:
                return False
            
            latest = recent[0]
            previous = recent[1]
            
            # 计算最大变化
            changes = []
            if previous.home_odds > 0:
                changes.append(abs(latest.home_odds - previous.home_odds) / previous.home_odds * 100)
            if previous.draw_odds > 0:
                changes.append(abs(latest.draw_odds - previous.draw_odds) / previous.draw_odds * 100)
            if previous.away_odds > 0:
                changes.append(abs(latest.away_odds - previous.away_odds) / previous.away_odds * 100)
            
            max_change = max(changes) if changes else 0
            return max_change > threshold
        finally:
            self.close_session(session)
    
    # ==================== 预测版本管理操作 ====================
    
    def save_prediction(self, prediction_data: Dict, trigger_reason: str) -> Optional[SystemPrediction]:
        """
        保存预测结果
        
        自动处理版本管理:
        - 将旧版本 is_current = False
        - 新版本 is_current = True
        - 版本号自动递增
        """
        session = self.get_session()
        try:
            match_id = prediction_data['match_id']
            
            # 获取当前版本号
            current = session.query(SystemPrediction).filter(
                SystemPrediction.match_id == match_id,
                SystemPrediction.is_current == True
            ).first()
            
            if current:
                # 将旧版本标记为非当前
                current.is_current = False
                version_num = int(current.prediction_version.replace('v', '')) + 1
            else:
                version_num = 1
            
            # 创建新版本
            prediction = SystemPrediction(
                match_id=match_id,
                prediction_version=f'v{version_num}',
                is_current=True,
                trigger_reason=trigger_reason,
                home_prob=prediction_data['home_prob'],
                draw_prob=prediction_data['draw_prob'],
                away_prob=prediction_data['away_prob'],
                prediction=prediction_data['prediction'],
                lambda_home=prediction_data['lambda_home'],
                lambda_away=prediction_data['lambda_away'],
                expected_home_goals=prediction_data['expected_home_goals'],
                expected_away_goals=prediction_data['expected_away_goals'],
                most_likely_score=prediction_data['most_likely_score'],
                total_goals_expected=prediction_data.get('total_goals_expected'),
                prob_over_2_5=prediction_data.get('prob_over_2_5'),
                prob_under_2_5=prediction_data.get('prob_under_2_5'),
                prob_home_cover_0_5=prediction_data.get('prob_home_cover_0_5'),
                prob_away_cover_0_5=prediction_data.get('prob_away_cover_0_5'),
                kelly_home=prediction_data.get('kelly_home'),
                kelly_draw=prediction_data.get('kelly_draw'),
                kelly_away=prediction_data.get('kelly_away'),
                best_home_odds=prediction_data.get('best_home_odds'),
                best_draw_odds=prediction_data.get('best_draw_odds'),
                best_away_odds=prediction_data.get('best_away_odds'),
                best_bookmaker_home=prediction_data.get('best_bookmaker_home'),
                best_bookmaker_draw=prediction_data.get('best_bookmaker_draw'),
                best_bookmaker_away=prediction_data.get('best_bookmaker_away'),
                score_distribution=json.dumps(prediction_data.get('score_distribution', {})),
                totals_prediction_data=json.dumps(prediction_data.get('totals_prediction', {})),
                handicap_prediction_data=json.dumps(prediction_data.get('handicap_prediction', {})),
                value_bets_data=json.dumps(prediction_data.get('value_bets', []))
            )
            session.add(prediction)
            session.commit()
            session.refresh(prediction)
            
            print(f"[DB] 保存预测 v{version_num}: {match_id} ({trigger_reason})")
            return prediction
        except Exception as e:
            session.rollback()
            print(f"[DB] 保存预测失败: {e}")
            return None
        finally:
            self.close_session(session)
    
    def get_current_prediction(self, match_id: str) -> Optional[SystemPrediction]:
        """获取当前版本的预测"""
        session = self.get_session()
        try:
            return session.query(SystemPrediction).filter(
                SystemPrediction.match_id == match_id,
                SystemPrediction.is_current == True
            ).first()
        finally:
            self.close_session(session)
    
    def get_predictions_for_matches(self, match_ids: List[str]) -> Dict[str, SystemPrediction]:
        """批量获取预测结果"""
        session = self.get_session()
        try:
            predictions = session.query(SystemPrediction).filter(
                SystemPrediction.match_id.in_(match_ids),
                SystemPrediction.is_current == True
            ).all()
            
            return {p.match_id: p for p in predictions}
        finally:
            self.close_session(session)
    
    def get_prediction_history(self, match_id: str, limit: int = 5) -> List[SystemPrediction]:
        """获取预测历史版本"""
        session = self.get_session()
        try:
            return session.query(SystemPrediction).filter(
                SystemPrediction.match_id == match_id
            ).order_by(SystemPrediction.created_at.desc()).limit(limit).all()
        finally:
            self.close_session(session)
    
    def has_prediction(self, match_id: str) -> bool:
        """检查是否有预测"""
        session = self.get_session()
        try:
            return session.query(SystemPrediction).filter(
                SystemPrediction.match_id == match_id,
                SystemPrediction.is_current == True
            ).count() > 0
        finally:
            self.close_session(session)
    
    # ==================== 球队统计操作 ====================
    
    def save_team_stats(self, stats_data: Dict) -> Optional[TeamStatsCache]:
        """保存/更新球队统计"""
        session = self.get_session()
        try:
            existing = session.query(TeamStatsCache).filter(
                TeamStatsCache.team_id == stats_data['team_id']
            ).first()
            
            if existing:
                existing.home_scored_avg = stats_data.get('home_scored_avg', existing.home_scored_avg)
                existing.home_conceded_avg = stats_data.get('home_conceded_avg', existing.home_conceded_avg)
                existing.home_played = stats_data.get('home_played', existing.home_played)
                existing.away_scored_avg = stats_data.get('away_scored_avg', existing.away_scored_avg)
                existing.away_conceded_avg = stats_data.get('away_conceded_avg', existing.away_conceded_avg)
                existing.away_played = stats_data.get('away_played', existing.away_played)
                existing.updated_at = datetime.utcnow()
                session.commit()
                return existing
            
            stats = TeamStatsCache(
                team_id=stats_data['team_id'],
                team_name=stats_data['team_name'],
                league_code=stats_data['league_code'],
                home_scored_avg=stats_data.get('home_scored_avg', 0.0),
                home_conceded_avg=stats_data.get('home_conceded_avg', 0.0),
                home_played=stats_data.get('home_played', 0),
                away_scored_avg=stats_data.get('away_scored_avg', 0.0),
                away_conceded_avg=stats_data.get('away_conceded_avg', 0.0),
                away_played=stats_data.get('away_played', 0)
            )
            session.add(stats)
            session.commit()
            session.refresh(stats)
            return stats
        except Exception as e:
            session.rollback()
            print(f"[DB] 保存球队统计失败: {e}")
            return None
        finally:
            self.close_session(session)
    
    def get_team_stats(self, team_id: int) -> Optional[TeamStatsCache]:
        """获取球队统计"""
        session = self.get_session()
        try:
            return session.query(TeamStatsCache).filter(TeamStatsCache.team_id == team_id).first()
        finally:
            self.close_session(session)
    
    def get_team_stats_for_league(self, league_code: str) -> List[TeamStatsCache]:
        """获取联赛所有球队统计"""
        session = self.get_session()
        try:
            return session.query(TeamStatsCache).filter(
                TeamStatsCache.league_code == league_code
            ).all()
        finally:
            self.close_session(session)
    
    def get_all_team_stats(self) -> Dict[int, TeamStatsCache]:
        """获取所有球队统计"""
        session = self.get_session()
        try:
            stats = session.query(TeamStatsCache).all()
            return {s.team_id: s for s in stats}
        finally:
            self.close_session(session)


# 导入timedelta用于时间计算
from datetime import timedelta


# ==================== 初始化 ====================

if __name__ == "__main__":
    # 初始化数据库
    manager = PredictionCacheManager()
    manager.init_db()
    
    print("\n[DB] 预计算数据库表结构:")
    print("  - matches_cache: 比赛基础信息缓存")
    print("  - odds_history: 赔率历史记录 (变化检测)")
    print("  - system_predictions: 系统预测缓存 (版本管理)")
    print("  - team_stats_cache: 球队统计缓存")
    print("  - users: 用户数据")
    print("  - user_prediction_tracks: 用户预测追踪")