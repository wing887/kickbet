"""
KickBet数据库模块

功能:
- SQLite数据库连接
- 用户表 (替代内存存储)
- 预测记录表 (历史追踪)
- 比赛记录表
- CRUD操作封装

使用SQLAlchemy ORM
"""

import os
import json
from datetime import datetime
from typing import Optional, List, Dict
from dataclasses import dataclass

from sqlalchemy import create_engine, Column, String, Float, Integer, Boolean, DateTime, Text, ForeignKey
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
    connect_args={'check_same_thread': False},  # SQLite单线程限制
    poolclass=StaticPool,
    echo=False  # 不打印SQL语句
)

# 会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 基类
Base = declarative_base()


# ==================== 数据模型 ====================

class UserModel(Base):
    """用户表"""
    __tablename__ = 'users'
    
    user_id = Column(String(50), primary_key=True)
    username = Column(String(30), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False, default='user')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # 关联预测记录
    predictions = relationship("PredictionRecord", back_populates="user")
    
    def to_dict(self) -> Dict:
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }


class PredictionRecord(Base):
    """预测记录表 - 存储历史预测结果"""
    __tablename__ = 'predictions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey('users.user_id'), nullable=True, index=True)
    match_id = Column(String(50), nullable=False, index=True)
    home_team = Column(String(50), nullable=False)
    away_team = Column(String(50), nullable=False)
    league = Column(String(20), nullable=True)
    
    # 预测参数
    lambda_home = Column(Float, nullable=False)
    lambda_away = Column(Float, nullable=False)
    
    # 胜平负概率
    prob_home = Column(Float, nullable=False)
    prob_draw = Column(Float, nullable=False)
    prob_away = Column(Float, nullable=False)
    prediction = Column(String(1), nullable=False)  # H/D/A
    
    # 大小球
    totals_line = Column(Float, nullable=True)
    prob_over = Column(Float, nullable=True)
    prob_under = Column(Float, nullable=True)
    
    # 让球盘
    handicap = Column(Float, nullable=True)
    prob_home_cover = Column(Float, nullable=True)
    prob_away_cover = Column(Float, nullable=True)
    
    # 比分分布 (JSON)
    score_distribution = Column(Text, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # 实际结果 (赛后更新)
    actual_home_goals = Column(Integer, nullable=True)
    actual_away_goals = Column(Integer, nullable=True)
    actual_result = Column(String(1), nullable=True)  # H/D/A
    is_correct = Column(Boolean, nullable=True)
    
    # 关联用户
    user = relationship("UserModel", back_populates="predictions")
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'match_id': self.match_id,
            'home_team': self.home_team,
            'away_team': self.away_team,
            'league': self.league,
            'lambda_home': self.lambda_home,
            'lambda_away': self.lambda_away,
            'prob_home': self.prob_home,
            'prob_draw': self.prob_draw,
            'prob_away': self.prob_away,
            'prediction': self.prediction,
            'totals_line': self.totals_line,
            'prob_over': self.prob_over,
            'prob_under': self.prob_under,
            'handicap': self.handicap,
            'prob_home_cover': self.prob_home_cover,
            'prob_away_cover': self.prob_away_cover,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'actual_result': self.actual_result,
            'is_correct': self.is_correct
        }


class MatchRecord(Base):
    """比赛记录表 - 存储比赛基础信息"""
    __tablename__ = 'matches'
    
    match_id = Column(String(50), primary_key=True)
    home_team_id = Column(Integer, nullable=False)
    away_team_id = Column(Integer, nullable=False)
    home_team_name = Column(String(50), nullable=False)
    away_team_name = Column(String(50), nullable=False)
    league_code = Column(String(10), nullable=False, index=True)
    league_name = Column(String(50), nullable=True)
    
    match_date = Column(DateTime, nullable=True, index=True)
    status = Column(String(20), default='TIMED')
    
    # 实际比分
    home_goals = Column(Integer, nullable=True)
    away_goals = Column(Integer, nullable=True)
    result = Column(String(1), nullable=True)  # H/D/A
    
    # 数据来源
    source = Column(String(20), default='football-data.org')
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            'match_id': self.match_id,
            'home_team': self.home_team_name,
            'away_team': self.away_team_name,
            'league': self.league_code,
            'league_name': self.league_name,
            'match_date': self.match_date.isoformat() if self.match_date else None,
            'status': self.status,
            'home_goals': self.home_goals,
            'away_goals': self.away_goals,
            'result': self.result
        }


class TeamStatsRecord(Base):
    """球队统计表 - 存储攻防数据"""
    __tablename__ = 'team_stats'
    
    team_id = Column(Integer, primary_key=True)
    team_name = Column(String(50), nullable=False)
    league_code = Column(String(10), nullable=False, index=True)
    
    # 主场数据
    home_scored_avg = Column(Float, default=0.0)
    home_conceded_avg = Column(Float, default=0.0)
    home_played = Column(Integer, default=0)
    
    # 宀场数据
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


# ==================== 数据库操作类 ====================

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    def init_db(self):
        """初始化数据库 (创建表)"""
        Base.metadata.create_all(bind=self.engine)
        print(f"[DB] 数据库初始化完成: {DB_PATH}")
    
    def get_session(self) -> Session:
        """获取数据库会话"""
        return self.SessionLocal()
    
    def close_session(self, session: Session):
        """关闭会话"""
        session.close()
    
    # ==================== 用户操作 ====================
    
    def create_user(self, user_id: str, username: str, email: str, 
                    password_hash: str, role: str = 'user') -> Optional[UserModel]:
        """创建用户"""
        session = self.get_session()
        try:
            user = UserModel(
                user_id=user_id,
                username=username,
                email=email,
                password_hash=password_hash,
                role=role
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            return user
        except Exception as e:
            session.rollback()
            print(f"[DB] 创建用户失败: {e}")
            return None
        finally:
            self.close_session(session)
    
    def get_user_by_id(self, user_id: str) -> Optional[UserModel]:
        """通过ID获取用户"""
        session = self.get_session()
        try:
            return session.query(UserModel).filter(UserModel.user_id == user_id).first()
        finally:
            self.close_session(session)
    
    def get_user_by_username(self, username: str) -> Optional[UserModel]:
        """通过用户名获取用户"""
        session = self.get_session()
        try:
            return session.query(UserModel).filter(UserModel.username == username).first()
        finally:
            self.close_session(session)
    
    def get_user_by_email(self, email: str) -> Optional[UserModel]:
        """通过邮箱获取用户"""
        session = self.get_session()
        try:
            return session.query(UserModel).filter(UserModel.email == email).first()
        finally:
            self.close_session(session)
    
    def update_user_login(self, user_id: str) -> bool:
        """更新用户登录时间"""
        session = self.get_session()
        try:
            user = session.query(UserModel).filter(UserModel.user_id == user_id).first()
            if user:
                user.last_login = datetime.utcnow()
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            return False
        finally:
            self.close_session(session)
    
    def list_users(self) -> List[UserModel]:
        """获取所有用户"""
        session = self.get_session()
        try:
            return session.query(UserModel).all()
        finally:
            self.close_session(session)
    
    def count_users(self) -> Dict:
        """用户统计"""
        session = self.get_session()
        try:
            total = session.query(UserModel).count()
            admins = session.query(UserModel).filter(UserModel.role == 'admin').count()
            active = session.query(UserModel).filter(UserModel.is_active == True).count()
            return {'total': total, 'admins': admins, 'active': active}
        finally:
            self.close_session(session)
    
    # ==================== 预测记录操作 ====================
    
    def save_prediction(self, user_id: Optional[str], match_id: str,
                        home_team: str, away_team: str, league: Optional[str],
                        lambda_home: float, lambda_away: float,
                        prob_home: float, prob_draw: float, prob_away: float,
                        prediction: str, score_distribution: Optional[Dict] = None,
                        totals_line: Optional[float] = None,
                        prob_over: Optional[float] = None, prob_under: Optional[float] = None,
                        handicap: Optional[float] = None,
                        prob_home_cover: Optional[float] = None, prob_away_cover: Optional[float] = None
                        ) -> Optional[PredictionRecord]:
        """保存预测记录"""
        session = self.get_session()
        try:
            record = PredictionRecord(
                user_id=user_id,
                match_id=match_id,
                home_team=home_team,
                away_team=away_team,
                league=league,
                lambda_home=lambda_home,
                lambda_away=lambda_away,
                prob_home=prob_home,
                prob_draw=prob_draw,
                prob_away=prob_away,
                prediction=prediction,
                score_distribution=json.dumps(score_distribution) if score_distribution else None,
                totals_line=totals_line,
                prob_over=prob_over,
                prob_under=prob_under,
                handicap=handicap,
                prob_home_cover=prob_home_cover,
                prob_away_cover=prob_away_cover
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record
        except Exception as e:
            session.rollback()
            print(f"[DB] 保存预测失败: {e}")
            return None
        finally:
            self.close_session(session)
    
    def get_predictions_by_user(self, user_id: str, limit: int = 50) -> List[PredictionRecord]:
        """获取用户的预测历史"""
        session = self.get_session()
        try:
            return session.query(PredictionRecord)\
                .filter(PredictionRecord.user_id == user_id)\
                .order_by(PredictionRecord.created_at.desc())\
                .limit(limit).all()
        finally:
            self.close_session(session)
    
    def get_predictions_by_match(self, match_id: str) -> List[PredictionRecord]:
        """获取比赛的预测记录"""
        session = self.get_session()
        try:
            return session.query(PredictionRecord)\
                .filter(PredictionRecord.match_id == match_id)\
                .order_by(PredictionRecord.created_at.desc()).all()
        finally:
            self.close_session(session)
    
    def update_prediction_result(self, prediction_id: int, 
                                  actual_home_goals: int, actual_away_goals: int,
                                  actual_result: str) -> bool:
        """更新预测结果"""
        session = self.get_session()
        try:
            record = session.query(PredictionRecord).filter(PredictionRecord.id == prediction_id).first()
            if record:
                record.actual_home_goals = actual_home_goals
                record.actual_away_goals = actual_away_goals
                record.actual_result = actual_result
                record.is_correct = (record.prediction == actual_result)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            return False
        finally:
            self.close_session(session)
    
    def count_predictions(self) -> Dict:
        """预测统计"""
        session = self.get_session()
        try:
            total = session.query(PredictionRecord).count()
            correct = session.query(PredictionRecord).filter(PredictionRecord.is_correct == True).count()
            pending = session.query(PredictionRecord).filter(PredictionRecord.actual_result == None).count()
            
            accuracy = 0.0
            if total > pending:
                accuracy = correct / (total - pending) * 100
            
            return {
                'total': total,
                'correct': correct,
                'pending': pending,
                'accuracy': round(accuracy, 2)
            }
        finally:
            self.close_session(session)
    
    # ==================== 比赛记录操作 ====================
    
    def save_match(self, match_id: str, home_team_id: int, away_team_id: int,
                   home_team_name: str, away_team_name: str,
                   league_code: str, league_name: Optional[str] = None,
                   match_date: Optional[datetime] = None,
                   status: str = 'TIMED', source: str = 'football-data.org'
                   ) -> Optional[Dict]:
        """保存比赛记录"""
        session = self.get_session()
        try:
            # 检查是否已存在
            existing = session.query(MatchRecord).filter(MatchRecord.match_id == match_id).first()
            if existing:
                # 更新
                existing.status = status
                existing.match_date = match_date
                existing.updated_at = datetime.utcnow()
                session.commit()
                return existing.to_dict()
            
            # 新建
            record = MatchRecord(
                match_id=match_id,
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                home_team_name=home_team_name,
                away_team_name=away_team_name,
                league_code=league_code,
                league_name=league_name,
                match_date=match_date,
                status=status,
                source=source
            )
            session.add(record)
            session.commit()
            return record.to_dict()
        except Exception as e:
            session.rollback()
            print(f"[DB] 保存比赛失败: {e}")
            return None
        finally:
            self.close_session(session)
    
    def get_upcoming_matches(self, days: int = 7, league: Optional[str] = None) -> List[MatchRecord]:
        """获取即将进行的比赛"""
        session = self.get_session()
        try:
            query = session.query(MatchRecord)\
                .filter(MatchRecord.status.in_(['TIMED', 'SCHEDULED']))
            
            if league:
                query = query.filter(MatchRecord.league_code == league)
            
            return query.order_by(MatchRecord.match_date).limit(100).all()
        finally:
            self.close_session(session)
    
    def update_match_result(self, match_id: str, home_goals: int, away_goals: int) -> bool:
        """更新比赛结果"""
        session = self.get_session()
        try:
            record = session.query(MatchRecord).filter(MatchRecord.match_id == match_id).first()
            if record:
                record.home_goals = home_goals
                record.away_goals = away_goals
                record.status = 'FINISHED'
                
                # 计算结果
                if home_goals > away_goals:
                    record.result = 'H'
                elif home_goals < away_goals:
                    record.result = 'A'
                else:
                    record.result = 'D'
                
                record.updated_at = datetime.utcnow()
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            return False
        finally:
            self.close_session(session)
    
    # ==================== 球队统计操作 ====================
    
    def save_team_stats(self, team_id: int, team_name: str, league_code: str,
                        home_scored_avg: float, home_conceded_avg: float, home_played: int,
                        away_scored_avg: float, away_conceded_avg: float, away_played: int
                        ) -> Optional[Dict]:
        """保存球队统计"""
        session = self.get_session()
        try:
            # 检查是否已存在
            existing = session.query(TeamStatsRecord).filter(TeamStatsRecord.team_id == team_id).first()
            if existing:
                # 更新
                existing.home_scored_avg = home_scored_avg
                existing.home_conceded_avg = home_conceded_avg
                existing.home_played = home_played
                existing.away_scored_avg = away_scored_avg
                existing.away_conceded_avg = away_conceded_avg
                existing.away_played = away_played
                existing.updated_at = datetime.utcnow()
                session.commit()
                return existing.to_dict()
            
            # 新建
            record = TeamStatsRecord(
                team_id=team_id,
                team_name=team_name,
                league_code=league_code,
                home_scored_avg=home_scored_avg,
                home_conceded_avg=home_conceded_avg,
                home_played=home_played,
                away_scored_avg=away_scored_avg,
                away_conceded_avg=away_conceded_avg,
                away_played=away_played
            )
            session.add(record)
            session.commit()
            return record.to_dict()
        except Exception as e:
            session.rollback()
            print(f"[DB] 保存球队统计失败: {e}")
            return None
        finally:
            self.close_session(session)
    
    def get_team_stats_by_league(self, league_code: str) -> Dict[int, TeamStatsRecord]:
        """获取联赛的球队统计"""
        session = self.get_session()
        try:
            records = session.query(TeamStatsRecord)\
                .filter(TeamStatsRecord.league_code == league_code).all()
            return {r.team_id: r for r in records}
        finally:
            self.close_session(session)
    
    def get_all_team_stats(self) -> Dict[int, TeamStatsRecord]:
        """获取所有球队统计"""
        session = self.get_session()
        try:
            records = session.query(TeamStatsRecord).all()
            return {r.team_id: r for r in records}
        finally:
            self.close_session(session)


# ==================== 全局实例 ====================

db = DatabaseManager()


def init_database():
    """初始化数据库"""
    db.init_db()
    return db


# ==================== 导出 ====================

__all__ = [
    'db', 'init_database', 'DatabaseManager',
    'UserModel', 'PredictionRecord', 'MatchRecord', 'TeamStatsRecord',
    'Base', 'engine', 'SessionLocal', 'DB_PATH'
]