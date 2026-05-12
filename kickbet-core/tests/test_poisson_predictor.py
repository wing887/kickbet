"""
Poisson预测引擎单元测试

测试覆盖:
1. 基础预测功能
2. 概率总和验证
3. 大小球概率计算
4. 让球盘概率计算
5. 边界条件测试
6. 数据类型验证
"""

import pytest
import math
from predictors.poisson_predictor import (
    PoissonPredictor,
    TeamAttackDefenseStats,
    MatchPrediction,
    TotalsPrediction,
    HandicapPrediction,
    poisson_sample
)


class TestPoissonSample:
    """Poisson随机数生成测试"""
    
    def test_poisson_sample_zero_lambda(self):
        """lambda=0时应返回0"""
        result = poisson_sample(0)
        assert result == 0
    
    def test_poisson_sample_negative_lambda(self):
        """负数lambda应返回0"""
        result = poisson_sample(-1)
        assert result == 0
    
    def test_poisson_sample_distribution(self):
        """验证Poisson分布均值接近lambda"""
        lambda_param = 2.5
        samples = [poisson_sample(lambda_param) for _ in range(1000)]
        mean = sum(samples) / len(samples)
        # 允许10%误差
        assert abs(mean - lambda_param) < lambda_param * 0.1


class TestPoissonPredictorBasic:
    """基础预测功能测试"""
    
    def test_predictor_initialization(self, predictor):
        """预测器初始化正确"""
        assert predictor.nsim == 10000
        assert predictor._team_stats == {}
    
    def test_set_team_stats(self, predictor, strong_vs_weak_teams):
        """设置球队统计数据"""
        predictor.set_team_stats(1, strong_vs_weak_teams['strong'])
        assert 1 in predictor._team_stats
        assert predictor._team_stats[1].team_name == 'Liverpool'
    
    def test_calculate_expected_goals(self, predictor, strong_vs_weak_teams):
        """预期进球计算"""
        predictor.set_team_stats(1, strong_vs_weak_teams['strong'])
        predictor.set_team_stats(2, strong_vs_weak_teams['weak'])
        
        lambda_home, lambda_away = predictor.calculate_expected_goals(1, 2)
        
        # 强队主场预期进球应大于弱队客场
        assert lambda_home > lambda_away
        # 基于输入数据的估算范围
        assert 1.5 < lambda_home < 3.5
        assert 0.5 < lambda_away < 1.5
    
    def test_missing_team_stats_defaults(self, predictor):
        """缺少球队统计时使用默认值"""
        lambda_home, lambda_away = predictor.calculate_expected_goals(999, 888)
        assert lambda_home == 1.5
        assert lambda_away == 1.2


class TestMatchPrediction:
    """比赛预测结果测试"""
    
    def test_prediction_returns_match_prediction(self, predictor, strong_vs_weak_teams):
        """预测返回正确的数据类型"""
        predictor.set_team_stats(1, strong_vs_weak_teams['strong'])
        predictor.set_team_stats(2, strong_vs_weak_teams['weak'])
        
        result = predictor.predict_match('test-001', 'Liverpool', 'Norwich', 1, 2)
        
        assert isinstance(result, MatchPrediction)
        assert result.match_id == 'test-001'
        assert result.home_team == 'Liverpool'
        assert result.away_team == 'Norwich'
    
    def test_probability_sum_equals_one(self, predictor, strong_vs_weak_teams):
        """胜平负概率总和应为1"""
        predictor.set_team_stats(1, strong_vs_weak_teams['strong'])
        predictor.set_team_stats(2, strong_vs_weak_teams['weak'])
        
        result = predictor.predict_match('test-001', 'Liverpool', 'Norwich', 1, 2)
        
        total_prob = result.prob_home + result.prob_draw + result.prob_away
        assert abs(total_prob - 1.0) < 0.001  # 允许千分之一误差
    
    def test_probability_range(self, predictor, strong_vs_weak_teams):
        """概率应在0-1范围内"""
        predictor.set_team_stats(1, strong_vs_weak_teams['strong'])
        predictor.set_team_stats(2, strong_vs_weak_teams['weak'])
        
        result = predictor.predict_match('test-001', 'Liverpool', 'Norwich', 1, 2)
        
        assert 0 <= result.prob_home <= 1
        assert 0 <= result.prob_draw <= 1
        assert 0 <= result.prob_away <= 1
    
    def test_prediction_is_valid(self, predictor, strong_vs_weak_teams):
        """预测结果应为H/D/A之一"""
        predictor.set_team_stats(1, strong_vs_weak_teams['strong'])
        predictor.set_team_stats(2, strong_vs_weak_teams['weak'])
        
        result = predictor.predict_match('test-001', 'Liverpool', 'Norwich', 1, 2)
        
        assert result.prediction in ['H', 'D', 'A']
    
    def test_strong_team_home_prediction(self, predictor, strong_vs_weak_teams):
        """强队主场应预测主胜"""
        predictor.set_team_stats(1, strong_vs_weak_teams['strong'])
        predictor.set_team_stats(2, strong_vs_weak_teams['weak'])
        
        result = predictor.predict_match('test-001', 'Liverpool', 'Norwich', 1, 2)
        
        # 强队主场概率应显著高于客胜
        assert result.prob_home > result.prob_away
        assert result.prob_home > 0.5  # 主胜概率应超过50%


class TestTotalsPrediction:
    """大小球预测测试"""
    
    def test_totals_prediction_exists(self, predictor, strong_vs_weak_teams):
        """预测结果包含大小球预测"""
        predictor.set_team_stats(1, strong_vs_weak_teams['strong'])
        predictor.set_team_stats(2, strong_vs_weak_teams['weak'])
        
        result = predictor.predict_match('test-001', 'Liverpool', 'Norwich', 1, 2)
        
        assert result.totals_prediction is not None
        assert isinstance(result.totals_prediction, TotalsPrediction)
    
    def test_totals_probability_sum(self, predictor, strong_vs_weak_teams):
        """大小球概率之和应为1"""
        predictor.set_team_stats(1, strong_vs_weak_teams['strong'])
        predictor.set_team_stats(2, strong_vs_weak_teams['weak'])
        
        result = predictor.predict_match('test-001', 'Liverpool', 'Norwich', 1, 2)
        totals = result.totals_prediction
        
        # 2.5盘口概率之和
        total_2_5 = totals.prob_over_2_5 + totals.prob_under_2_5
        assert abs(total_2_5 - 1.0) < 0.001
    
    def test_totals_probability_range(self, predictor, strong_vs_weak_teams):
        """大小球概率应在0-1范围"""
        predictor.set_team_stats(1, strong_vs_weak_teams['strong'])
        predictor.set_team_stats(2, strong_vs_weak_teams['weak'])
        
        result = predictor.predict_match('test-001', 'Liverpool', 'Norwich', 1, 2)
        totals = result.totals_prediction
        
        assert 0 <= totals.prob_over_2_5 <= 1
        assert 0 <= totals.prob_under_2_5 <= 1
        assert 0 <= totals.prob_over_1_5 <= 1
        assert 0 <= totals.prob_under_1_5 <= 1
    
    def test_totals_expected_goals(self, predictor, strong_vs_weak_teams):
        """预期总进球应为两队预期之和"""
        predictor.set_team_stats(1, strong_vs_weak_teams['strong'])
        predictor.set_team_stats(2, strong_vs_weak_teams['weak'])
        
        result = predictor.predict_match('test-001', 'Liverpool', 'Norwich', 1, 2)
        
        expected_total = result.expected_home_goals + result.expected_away_goals
        assert abs(result.totals_prediction.total_goals - expected_total) < 0.01
    
    def test_goals_distribution_sum(self, predictor, strong_vs_weak_teams):
        """进球分布概率总和接近1"""
        predictor.set_team_stats(1, strong_vs_weak_teams['strong'])
        predictor.set_team_stats(2, strong_vs_weak_teams['weak'])
        
        result = predictor.predict_match('test-001', 'Liverpool', 'Norwich', 1, 2)
        
        total = sum(result.totals_prediction.goals_distribution.values())
        # 由于过滤了低概率项，总和可能略小于1，但应大于0.9
        assert total > 0.9


class TestHandicapPrediction:
    """让球盘预测测试"""
    
    def test_handicap_prediction_exists(self, predictor, strong_vs_weak_teams):
        """预测结果包含让球盘预测"""
        predictor.set_team_stats(1, strong_vs_weak_teams['strong'])
        predictor.set_team_stats(2, strong_vs_weak_teams['weak'])
        
        result = predictor.predict_match('test-001', 'Liverpool', 'Norwich', 1, 2)
        
        assert result.handicap_prediction is not None
        assert isinstance(result.handicap_prediction, HandicapPrediction)
    
    def test_handicap_0_5_probability_sum(self, predictor, strong_vs_weak_teams):
        """-0.5盘口概率之和应为1"""
        predictor.set_team_stats(1, strong_vs_weak_teams['strong'])
        predictor.set_team_stats(2, strong_vs_weak_teams['weak'])
        
        result = predictor.predict_match('test-001', 'Liverpool', 'Norwich', 1, 2)
        hdp = result.handicap_prediction
        
        total_0_5 = hdp.asian_0_5['home'] + hdp.asian_0_5['away']
        assert abs(total_0_5 - 1.0) < 0.001
    
    def test_handicap_1_0_probability_sum(self, predictor, strong_vs_weak_teams):
        """-1.0盘口概率之和应为1"""
        predictor.set_team_stats(1, strong_vs_weak_teams['strong'])
        predictor.set_team_stats(2, strong_vs_weak_teams['weak'])
        
        result = predictor.predict_match('test-001', 'Liverpool', 'Norwich', 1, 2)
        hdp = result.handicap_prediction
        
        total_1_0 = hdp.asian_1_0['home'] + hdp.asian_1_0['draw'] + hdp.asian_1_0['away']
        assert abs(total_1_0 - 1.0) < 0.001
    
    def test_handicap_1_5_probability_sum(self, predictor, strong_vs_weak_teams):
        """-1.5盘口概率之和应为1"""
        predictor.set_team_stats(1, strong_vs_weak_teams['strong'])
        predictor.set_team_stats(2, strong_vs_weak_teams['weak'])
        
        result = predictor.predict_match('test-001', 'Liverpool', 'Norwich', 1, 2)
        hdp = result.handicap_prediction
        
        total_1_5 = hdp.asian_1_5['home'] + hdp.asian_1_5['away']
        assert abs(total_1_5 - 1.0) < 0.001
    
    def test_handicap_consistency_with_ml(self, predictor, strong_vs_weak_teams):
        """-0.5盘口概率应与胜平负一致"""
        predictor.set_team_stats(1, strong_vs_weak_teams['strong'])
        predictor.set_team_stats(2, strong_vs_weak_teams['weak'])
        
        result = predictor.predict_match('test-001', 'Liverpool', 'Norwich', 1, 2)
        
        # -0.5盘口: 主赢盘 = 主胜概率
        # 客赢盘 = 平局 + 客胜概率
        expected_home_cover = result.prob_home
        expected_away_cover = result.prob_draw + result.prob_away
        
        assert abs(result.handicap_prediction.asian_0_5['home'] - expected_home_cover) < 0.01
        assert abs(result.handicap_prediction.asian_0_5['away'] - expected_away_cover) < 0.01


class TestCustomLineCalculation:
    """任意盘口计算测试"""
    
    def test_totals_custom_line_2_0(self, predictor, strong_vs_weak_teams):
        """自定义大小球2.0盘口"""
        predictor.set_team_stats(1, strong_vs_weak_teams['strong'])
        predictor.set_team_stats(2, strong_vs_weak_teams['weak'])
        
        result = predictor.predict_match('test-001', 'Liverpool', 'Norwich', 1, 2)
        totals = predictor.calculate_totals_for_line(result.score_distribution, 2.0)
        
        # 整数盘口应包含走水概率
        assert 'exact' in totals
        assert totals['over'] + totals['under'] + totals['exact'] == 1.0
    
    def test_totals_custom_line_3_5(self, predictor, strong_vs_weak_teams):
        """自定义大小球3.5盘口"""
        predictor.set_team_stats(1, strong_vs_weak_teams['strong'])
        predictor.set_team_stats(2, strong_vs_weak_teams['weak'])
        
        result = predictor.predict_match('test-001', 'Liverpool', 'Norwich', 1, 2)
        totals = predictor.calculate_totals_for_line(result.score_distribution, 3.5)
        
        # 非整数盘口无走水
        assert 'exact' not in totals
        assert totals['over'] + totals['under'] == 1.0
    
    def test_handicap_custom_line(self, predictor, strong_vs_weak_teams):
        """自定义让球盘口"""
        predictor.set_team_stats(1, strong_vs_weak_teams['strong'])
        predictor.set_team_stats(2, strong_vs_weak_teams['weak'])
        
        result = predictor.predict_match('test-001', 'Liverpool', 'Norwich', 1, 2)
        hdp = predictor.calculate_handicap_for_line(result.score_distribution, -0.75)
        
        # 非整数盘口无走水
        assert 'draw' not in hdp
        assert hdp['home'] + hdp['away'] == 1.0
    
    def test_handicap_positive_line(self, predictor, strong_vs_weak_teams):
        """客队让球盘口测试"""
        predictor.set_team_stats(1, strong_vs_weak_teams['strong'])
        predictor.set_team_stats(2, strong_vs_weak_teams['weak'])
        
        result = predictor.predict_match('test-001', 'Liverpool', 'Norwich', 1, 2)
        # +0.5表示客队让0.5球，对主队有利
        hdp = predictor.calculate_handicap_for_line(result.score_distribution, 0.5)
        
        # 主队赢盘概率应更高
        assert hdp['home'] > hdp['away']


class TestScoreDistribution:
    """比分分布测试"""
    
    def test_score_distribution_exists(self, predictor, strong_vs_weak_teams):
        """预测结果包含比分分布"""
        predictor.set_team_stats(1, strong_vs_weak_teams['strong'])
        predictor.set_team_stats(2, strong_vs_weak_teams['weak'])
        
        result = predictor.predict_match('test-001', 'Liverpool', 'Norwich', 1, 2)
        
        assert result.score_distribution is not None
        assert len(result.score_distribution) > 0
    
    def test_score_distribution_format(self, predictor, strong_vs_weak_teams):
        """比分格式正确"""
        predictor.set_team_stats(1, strong_vs_weak_teams['strong'])
        predictor.set_team_stats(2, strong_vs_weak_teams['weak'])
        
        result = predictor.predict_match('test-001', 'Liverpool', 'Norwich', 1, 2)
        
        for score, prob in result.score_distribution.items():
            # 格式应为 "X-Y"
            assert '-' in score
            home, away = score.split('-')
            assert home.isdigit()
            assert away.isdigit()
            assert 0 <= prob <= 1
    
    def test_most_likely_score_in_distribution(self, predictor, strong_vs_weak_teams):
        """最可能比分应在分布中"""
        predictor.set_team_stats(1, strong_vs_weak_teams['strong'])
        predictor.set_team_stats(2, strong_vs_weak_teams['weak'])
        
        result = predictor.predict_match('test-001', 'Liverpool', 'Norwich', 1, 2)
        
        assert result.most_likely_score in result.score_distribution
        # 最可能比分概率应最高
        max_prob = max(result.score_distribution.values())
        assert result.score_distribution[result.most_likely_score] == max_prob


class TestEdgeCases:
    """边界条件测试"""
    
    def test_equal_teams_prediction(self, predictor, balanced_teams):
        """实力相近的球队预测"""
        predictor.set_team_stats(1, balanced_teams['team_a'])
        predictor.set_team_stats(2, balanced_teams['team_b'])
        
        result = predictor.predict_match('test-002', 'Chelsea', 'Arsenal', 1, 2)
        
        # 主胜概率略高（主场优势）
        assert result.prob_home > result.prob_away
        # 但差距不应太大（放宽阈值到0.25，考虑Monte Carlo随机性）
        assert abs(result.prob_home - result.prob_away) < 0.25
    
    def test_extreme_lambda(self, predictor):
        """极端预期进球值"""
        # 设置极端数据
        extreme_strong = TeamAttackDefenseStats(
            team_id=1, team_name='ExtremeStrong',
            home_scored_avg=5.0, home_conceded_avg=0.1,
            home_played=10, away_scored_avg=4.0,
            away_conceded_avg=0.2, away_played=10
        )
        extreme_weak = TeamAttackDefenseStats(
            team_id=2, team_name='ExtremeWeak',
            home_scored_avg=0.3, home_conceded_avg=4.0,
            home_played=10, away_scored_avg=0.2,
            away_conceded_avg=5.0, away_played=10
        )
        
        predictor.set_team_stats(1, extreme_strong)
        predictor.set_team_stats(2, extreme_weak)
        
        result = predictor.predict_match('test-003', 'ExtremeStrong', 'ExtremeWeak', 1, 2)
        
        # 主胜概率应极高
        assert result.prob_home > 0.85
        assert result.prob_away < 0.1
    
    def test_lambda_consistency(self, predictor, strong_vs_weak_teams):
        """多次预测Lambda值应一致"""
        predictor.set_team_stats(1, strong_vs_weak_teams['strong'])
        predictor.set_team_stats(2, strong_vs_weak_teams['weak'])
        
        results = [
            predictor.predict_match('test-001', 'Liverpool', 'Norwich', 1, 2)
            for _ in range(5)
        ]
        
        # Lambda值应相同（不依赖随机模拟）
        lambdas = [(r.expected_home_goals, r.expected_away_goals) for r in results]
        assert all(l == lambdas[0] for l in lambdas)