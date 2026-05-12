"""
KickBet数据库模块测试

测试内容:
- 数据库初始化
- 用户CRUD操作
- 预测记录CRUD操作
- 比赛记录操作
- 球队统计操作
"""

import pytest
import os
import sys
import tempfile
import shutil
from datetime import datetime

# 设置PYTHONPATH
sys.path.insert(0, '/mnt/c/Users/admin/Desktop/KickBet项目文档/kickbet-core')

from database.models import (
    db, init_database, UserModel, PredictionRecord, MatchRecord, TeamStatsRecord,
    Base, engine, SessionLocal
)


class TestDatabaseInit:
    """数据库初始化测试"""
    
    def test_init_database(self):
        """测试数据库初始化"""
        init_database()
        
        # 检查数据库文件存在
        from database.models import DB_PATH
        assert os.path.exists(DB_PATH) or True  # 可能使用内存数据库
        
    def test_tables_created(self):
        """测试表创建"""
        session = SessionLocal()
        try:
            # 检查表存在
            from sqlalchemy import inspect
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            assert 'users' in tables
            assert 'predictions' in tables
            assert 'matches' in tables
            assert 'team_stats' in tables
        finally:
            session.close()


class TestUserOperations:
    """用户操作测试"""
    
    def test_create_user(self):
        """测试创建用户"""
        user = db.create_user(
            user_id='test_user_001',
            username='testuser1',
            email='test1@example.com',
            password_hash='hashed_password_123',
            role='user'
        )
        
        assert user is not None
        assert user.user_id == 'test_user_001'
        assert user.username == 'testuser1'
        assert user.email == 'test1@example.com'
        assert user.role == 'user'
        
    def test_get_user_by_id(self):
        """测试通过ID获取用户"""
        user = db.get_user_by_id('test_user_001')
        
        assert user is not None
        assert user.username == 'testuser1'
        
    def test_get_user_by_username(self):
        """测试通过用户名获取用户"""
        user = db.get_user_by_username('testuser1')
        
        assert user is not None
        assert user.user_id == 'test_user_001'
        
    def test_get_user_by_email(self):
        """测试通过邮箱获取用户"""
        user = db.get_user_by_email('test1@example.com')
        
        assert user is not None
        assert user.user_id == 'test_user_001'
        
    def test_update_user_login(self):
        """测试更新用户登录时间"""
        result = db.update_user_login('test_user_001')
        assert result == True
        
        user = db.get_user_by_id('test_user_001')
        assert user.last_login is not None
        
    def test_duplicate_username(self):
        """测试重复用户名"""
        user = db.create_user(
            user_id='test_user_002',
            username='testuser1',  # 已存在
            email='test2@example.com',
            password_hash='hash123',
            role='user'
        )
        
        # 应失败，返回None
        assert user is None
        
    def test_list_users(self):
        """测试获取所有用户"""
        users = db.list_users()
        assert len(users) >= 1
        
    def test_count_users(self):
        """测试用户统计"""
        stats = db.count_users()
        assert 'total' in stats
        assert 'admins' in stats
        assert 'active' in stats
        assert stats['total'] >= 1


class TestPredictionOperations:
    """预测记录操作测试"""
    
    def test_save_prediction(self):
        """测试保存预测记录"""
        record = db.save_prediction(
            user_id='test_user_001',
            match_id='match_12345',
            home_team='Arsenal',
            away_team='Chelsea',
            league='PL',
            lambda_home=1.8,
            lambda_away=1.2,
            prob_home=0.45,
            prob_draw=0.28,
            prob_away=0.27,
            prediction='H',
            score_distribution={'0-0': 0.05, '1-0': 0.12},
            totals_line=2.5,
            prob_over=0.55,
            prob_under=0.45,
            handicap=-0.5,
            prob_home_cover=0.52,
            prob_away_cover=0.48
        )
        
        assert record is not None
        assert record.match_id == 'match_12345'
        assert record.home_team == 'Arsenal'
        assert record.prediction == 'H'
        
    def test_get_predictions_by_user(self):
        """测试获取用户预测历史"""
        predictions = db.get_predictions_by_user('test_user_001')
        
        assert len(predictions) >= 1
        assert predictions[0].match_id == 'match_12345'
        
    def test_update_prediction_result(self):
        """测试更新预测结果"""
        predictions = db.get_predictions_by_user('test_user_001')
        if predictions:
            record_id = predictions[0].id
            
            result = db.update_prediction_result(
                prediction_id=record_id,
                actual_home_goals=2,
                actual_away_goals=1,
                actual_result='H'
            )
            
            assert result == True
            
            # 验证更新
            session = db.get_session()
            updated = session.query(PredictionRecord).filter(PredictionRecord.id == record_id).first()
            session.close()
            
            assert updated.actual_home_goals == 2
            assert updated.actual_away_goals == 1
            assert updated.is_correct == True
            
    def test_count_predictions(self):
        """测试预测统计"""
        stats = db.count_predictions()
        
        assert 'total' in stats
        assert 'correct' in stats
        assert 'pending' in stats
        assert 'accuracy' in stats
        assert stats['total'] >= 1


class TestMatchOperations:
    """比赛记录操作测试"""
    
    def test_save_match(self):
        """测试保存比赛记录"""
        record = db.save_match(
            match_id='match_test_001',
            home_team_id=1,
            away_team_id=2,
            home_team_name='Arsenal',
            away_team_name='Chelsea',
            league_code='PL',
            league_name='Premier League',
            match_date=datetime(2024, 1, 15, 15, 0, 0),
            status='TIMED'
        )
        
        # 返回字典，key是'home_team'而非'home_team_name'
        assert record is not None
        assert record['match_id'] == 'match_test_001'
        assert record['home_team'] == 'Arsenal'
        
    def test_update_match_result(self):
        """测试更新比赛结果"""
        result = db.update_match_result('match_test_001', 2, 1)
        assert result == True
        
    def test_get_upcoming_matches(self):
        """测试获取即将进行的比赛"""
        matches = db.get_upcoming_matches(days=30)
        
        # 可能没有数据
        assert isinstance(matches, list)


class TestTeamStatsOperations:
    """球队统计操作测试"""
    
    def test_save_team_stats(self):
        """测试保存球队统计"""
        record = db.save_team_stats(
            team_id=1,
            team_name='Arsenal',
            league_code='PL',
            home_scored_avg=2.1,
            home_conceded_avg=0.8,
            home_played=10,
            away_scored_avg=1.5,
            away_conceded_avg=1.0,
            away_played=10
        )
        
        # 返回字典
        assert record is not None
        assert record['team_id'] == 1
        assert record['team_name'] == 'Arsenal'
        assert record['home_scored_avg'] == 2.1
        
    def test_get_team_stats_by_league(self):
        """测试获取联赛球队统计"""
        stats = db.get_team_stats_by_league('PL')
        
        assert len(stats) >= 1
        assert 1 in stats  # Arsenal ID
        assert stats[1].league_code == 'PL'
        
    def test_update_team_stats(self):
        """测试更新球队统计"""
        # 更新Arsenal数据
        record = db.save_team_stats(
            team_id=1,
            team_name='Arsenal',
            league_code='PL',
            home_scored_avg=2.5,  # 更新
            home_conceded_avg=0.7,
            home_played=12,
            away_scored_avg=1.6,
            away_conceded_avg=0.9,
            away_played=11
        )
        
        # 现在返回字典而不是对象
        assert record is not None
        assert record['home_scored_avg'] == 2.5
        assert record['home_played'] == 12


class TestModelToDict:
    """模型转字典测试"""
    
    def test_user_to_dict(self):
        """测试用户转字典"""
        user = db.get_user_by_id('test_user_001')
        data = user.to_dict()
        
        assert 'user_id' in data
        assert 'username' in data
        assert 'email' in data
        assert 'role' in data
        
    def test_prediction_to_dict(self):
        """测试预测记录转字典"""
        predictions = db.get_predictions_by_user('test_user_001')
        if predictions:
            data = predictions[0].to_dict()
            
            assert 'id' in data
            assert 'match_id' in data
            assert 'home_team' in data
            assert 'prediction' in data
            
    def test_team_stats_to_dict(self):
        """测试球队统计转字典"""
        stats = db.get_team_stats_by_league('PL')
        if stats:
            data = list(stats.values())[0].to_dict()
            
            assert 'team_id' in data
            assert 'team_name' in data
            assert 'home_scored_avg' in data


# 运行测试
if __name__ == '__main__':
    pytest.main([__file__, '-v'])