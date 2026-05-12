"""
pytest配置和共享fixtures
"""

import pytest
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from predictors.poisson_predictor import (
    PoissonPredictor, 
    KellyCriterion, 
    TeamAttackDefenseStats,
    TotalsPrediction,
    HandicapPrediction
)


@pytest.fixture
def predictor():
    """创建预测器实例"""
    return PoissonPredictor(nsim=10000)


@pytest.fixture
def strong_vs_weak_teams():
    """强队vs弱队的测试数据"""
    return {
        'strong': TeamAttackDefenseStats(
            team_id=1,
            team_name='Liverpool',
            home_scored_avg=2.5,
            home_conceded_avg=0.6,
            home_played=10,
            away_scored_avg=1.8,
            away_conceded_avg=0.9,
            away_played=10
        ),
        'weak': TeamAttackDefenseStats(
            team_id=2,
            team_name='Norwich',
            home_scored_avg=1.2,
            home_conceded_avg=1.8,
            home_played=10,
            away_scored_avg=0.8,
            away_conceded_avg=2.0,
            away_played=10
        )
    }


@pytest.fixture
def balanced_teams():
    """实力相近的测试数据"""
    return {
        'team_a': TeamAttackDefenseStats(
            team_id=1,
            team_name='Chelsea',
            home_scored_avg=1.8,
            home_conceded_avg=0.8,
            home_played=10,
            away_scored_avg=1.4,
            away_conceded_avg=1.1,
            away_played=10
        ),
        'team_b': TeamAttackDefenseStats(
            team_id=2,
            team_name='Arsenal',
            home_scored_avg=1.7,
            home_conceded_avg=0.9,
            home_played=10,
            away_scored_avg=1.3,
            away_conceded_avg=1.2,
            away_played=10
        )
    }


@pytest.fixture
def kelly():
    """创建Kelly Criterion实例"""
    return KellyCriterion(min_edge=0.02, max_fraction=0.25)


@pytest.fixture
def sample_odds():
    """示例赔率数据"""
    return {
        'home_odds': 1.45,
        'home_bookmaker': 'Bet365',
        'draw_odds': 4.5,
        'draw_bookmaker': 'Bet365',
        'away_odds': 8.0,
        'away_bookmaker': 'Bet365',
        'market_prob_home': 1/1.45,
        'market_prob_draw': 1/4.5,
        'market_prob_away': 1/8.0
    }