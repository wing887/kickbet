"""
Kelly Criterion资金管理测试

测试覆盖:
1. Kelly比例计算
2. 价值投注判断
3. 资金分配逻辑
4. 边界条件测试
"""

import pytest
from predictors.poisson_predictor import (
    KellyCriterion,
    ValueBet,
    MatchPrediction,
    TotalsPrediction,
    HandicapPrediction
)


class TestKellyCriterionBasic:
    """基础Kelly计算测试"""
    
    def test_kelly_initialization(self, kelly):
        """Kelly初始化正确"""
        assert kelly.min_edge == 0.02
        assert kelly.max_fraction == 0.25
    
    def test_market_prob_calculation(self, kelly):
        """市场概率计算"""
        # 平均赔率2.0 → 市场概率50%
        odds_list = [2.0, 2.0, 2.0]
        prob = kelly.calculate_market_prob(odds_list)
        assert abs(prob - 0.5) < 0.001
    
    def test_market_prob_single_odds(self, kelly):
        """单个赔率计算"""
        prob = kelly.calculate_market_prob([2.5])
        assert abs(prob - 0.4) < 0.001
    
    def test_market_prob_empty_list(self, kelly):
        """空赔率列表"""
        prob = kelly.calculate_market_prob([])
        assert prob == 0.0


class TestKellyFractionCalculation:
    """Kelly比例计算测试"""
    
    def test_positive_kelly(self, kelly):
        """正Kelly比例"""
        # 模型概率50%，赔率2.2 → 有价值
        fraction = kelly.calculate_kelly_fraction(0.5, 2.2)
        # Kelly = (0.5 * 2.2 - 0.5) / 2.2 = 0.5 / 2.2 = 0.227
        assert fraction > 0
    
    def test_zero_kelly(self, kelly):
        """Kelly比例为0"""
        # 模型概率50%，赔率2.0 → 无价值
        fraction = kelly.calculate_kelly_fraction(0.5, 2.0)
        # Kelly = (0.5 * 2.0 - 0.5) / 2.0 = 0
        assert abs(fraction) < 0.001
    
    def test_negative_kelly(self, kelly):
        """负Kelly比例（不应投注）"""
        # 模型概率40%，赔率2.0 → 负价值
        fraction = kelly.calculate_kelly_fraction(0.4, 2.0)
        # Kelly = (0.4 * 2.0 - 0.6) / 2.0 = -0.1
        assert fraction < 0
    
    def test_kelly_max_fraction_limit(self, kelly):
        """Kelly比例上限"""
        # 极高价值，但应限制在max_fraction
        fraction = kelly.calculate_kelly_fraction(0.8, 5.0)
        # 理论Kelly = (0.8 * 5 - 0.2) / 5 = 3.8 / 5 = 0.76
        # 但应限制在0.25
        assert fraction <= kelly.max_fraction
    
    def test_high_probability_low_odds(self, kelly):
        """高概率低赔率"""
        # 模型概率80%，赔率1.25
        fraction = kelly.calculate_kelly_fraction(0.8, 1.25)
        # Kelly = (0.8 * 1.25 - 0.2) / 1.25 = 0.8 / 1.25 = 0.64
        # 限制在0.25
        assert 0 < fraction <= 0.25
    
    def test_low_probability_high_odds(self, kelly):
        """低概率高赔率"""
        # 模型概率10%，赔率15.0
        fraction = kelly.calculate_kelly_fraction(0.1, 15.0)
        # Kelly = (0.1 * 15 - 0.9) / 15 = 0.6 / 15 = 0.04
        assert fraction > 0


class TestValueBetDetection:
    """价值投注检测测试"""
    
    def test_find_value_bets_returns_list(self, kelly, sample_odds):
        """返回价值投注列表"""
        # 创建模拟预测
        prediction = MatchPrediction(
            match_id='test-001',
            home_team='TeamA',
            away_team='TeamB',
            prob_home=0.70,
            prob_draw=0.20,
            prob_away=0.10,
            prediction='H',
            expected_home_goals=2.0,
            expected_away_goals=0.8,
            most_likely_score='2-0',
            score_distribution={},
            totals_prediction=None,
            handicap_prediction=None
        )
        
        value_bets = kelly.find_value_bets(prediction, sample_odds)
        
        assert isinstance(value_bets, list)
        assert len(value_bets) == 3  # H/D/A各一个
    
    def test_value_bet_structure(self, kelly, sample_odds):
        """价值投注数据结构"""
        prediction = MatchPrediction(
            match_id='test-001',
            home_team='TeamA',
            away_team='TeamB',
            prob_home=0.70,
            prob_draw=0.20,
            prob_away=0.10,
            prediction='H',
            expected_home_goals=2.0,
            expected_away_goals=0.8,
            most_likely_score='2-0',
            score_distribution={},
            totals_prediction=None,
            handicap_prediction=None
        )
        
        value_bets = kelly.find_value_bets(prediction, sample_odds)
        
        for vb in value_bets:
            assert isinstance(vb, ValueBet)
            assert vb.match_id == 'test-001'
            assert vb.outcome in ['H', 'D', 'A']
            assert 0 <= vb.model_prob <= 1
            assert 0 <= vb.market_prob <= 1
            assert vb.best_odd > 0
    
    def test_value_bet_detection_correct(self, kelly, sample_odds):
        """正确判断价值投注"""
        prediction = MatchPrediction(
            match_id='test-001',
            home_team='TeamA',
            away_team='TeamB',
            prob_home=0.75,  # 模型75%，确保value > min_edge
            prob_draw=0.15,
            prob_away=0.10,
            prediction='H',
            expected_home_goals=2.0,
            expected_away_goals=0.8,
            most_likely_score='2-0',
            score_distribution={},
            totals_prediction=None,
            handicap_prediction=None
        )
        
        # sample_odds: home_odds=1.45 → market_prob=69%
        value_bets = kelly.find_value_bets(prediction, sample_odds)
        
        # 主胜: 模型75% > 市场69%，value=6% > min_edge(2%) → 应为价值投注
        home_bet = [vb for vb in value_bets if vb.outcome == 'H'][0]
        assert home_bet.value > kelly.min_edge  # 价值超过阈值
        assert home_bet.is_value_bet == True
    
    def test_no_value_bet_when_negative(self, kelly):
        """负价值时不应投注"""
        prediction = MatchPrediction(
            match_id='test-001',
            home_team='TeamA',
            away_team='TeamB',
            prob_home=0.50,  # 模型50%
            prob_draw=0.25,
            prob_away=0.25,
            prediction='H',
            expected_home_goals=1.5,
            expected_away_goals=1.2,
            most_likely_score='1-1',
            score_distribution={},
            totals_prediction=None,
            handicap_prediction=None
        )
        
        # 市场赔率暗示更高概率
        odds = {
            'home_odds': 1.8,  # 市场56%
            'home_bookmaker': 'Bet365',
            'draw_odds': 3.5,
            'draw_bookmaker': 'Bet365',
            'away_odds': 4.0,
            'away_bookmaker': 'Bet365',
            'market_prob_home': 1/1.8,  # 56%
            'market_prob_draw': 1/3.5,
            'market_prob_away': 1/4.0
        }
        
        value_bets = kelly.find_value_bets(prediction, odds)
        home_bet = [vb for vb in value_bets if vb.outcome == 'H'][0]
        
        # 模型50% < 市场56% → 负价值
        assert home_bet.value < 0
        assert home_bet.is_value_bet == False
    
    def test_value_bets_sorted_by_value(self, kelly, sample_odds):
        """价值投注按价值排序"""
        prediction = MatchPrediction(
            match_id='test-001',
            home_team='TeamA',
            away_team='TeamB',
            prob_home=0.70,
            prob_draw=0.20,
            prob_away=0.10,
            prediction='H',
            expected_home_goals=2.0,
            expected_away_goals=0.8,
            most_likely_score='2-0',
            score_distribution={},
            totals_prediction=None,
            handicap_prediction=None
        )
        
        value_bets = kelly.find_value_bets(prediction, sample_odds)
        
        # 应按value降序排列
        for i in range(len(value_bets) - 1):
            assert value_bets[i].value >= value_bets[i+1].value


class TestBankrollAllocation:
    """资金分配测试"""
    
    def test_allocate_bankroll_no_value(self, kelly, sample_odds):
        """无价值投注时返回空"""
        prediction = MatchPrediction(
            match_id='test-001',
            home_team='TeamA',
            away_team='TeamB',
            prob_home=0.50,
            prob_draw=0.25,
            prob_away=0.25,
            prediction='H',
            expected_home_goals=1.5,
            expected_away_goals=1.2,
            most_likely_score='1-1',
            score_distribution={},
            totals_prediction=None,
            handicap_prediction=None
        )
        
        # 设置完全无价值的赔率（市场概率高于模型）
        unfavorable_odds = {
            'home_odds': 1.5,  # 市场67% > 模型50%
            'home_bookmaker': 'Bet365',
            'draw_odds': 3.0,  # 市场33% > 模型25%
            'draw_bookmaker': 'Bet365',
            'away_odds': 3.5,  # 市场28.6% > 模型25%
            'away_bookmaker': 'Bet365',
            'market_prob_home': 1/1.5,  # 67%
            'market_prob_draw': 1/3.0,  # 33%
            'market_prob_away': 1/3.5   # 28.6%
        }
        
        value_bets = kelly.find_value_bets(prediction, unfavorable_odds)
        # 所有选项模型概率都低于市场概率，无价值
        allocations = kelly.allocate_bankroll(value_bets, 1000)
        
        assert allocations == []
    
    def test_allocate_bankroll_single_value(self, kelly, sample_odds):
        """单一价值投注分配"""
        prediction = MatchPrediction(
            match_id='test-001',
            home_team='TeamA',
            away_team='TeamB',
            prob_home=0.75,  # 高概率
            prob_draw=0.15,
            prob_away=0.10,
            prediction='H',
            expected_home_goals=2.5,
            expected_away_goals=0.5,
            most_likely_score='2-0',
            score_distribution={},
            totals_prediction=None,
            handicap_prediction=None
        )
        
        value_bets = kelly.find_value_bets(prediction, sample_odds)
        allocations = kelly.allocate_bankroll(value_bets, 1000)
        
        # 应有分配
        assert len(allocations) > 0
        
        # 检查分配结构
        for alloc in allocations:
            assert 'bet_amount' in alloc
            assert 'potential_return' in alloc
            assert alloc['bet_amount'] > 0
    
    def test_allocate_bankroll_total_within_limit(self, kelly, sample_odds):
        """总投注应在资金范围内"""
        prediction = MatchPrediction(
            match_id='test-001',
            home_team='TeamA',
            away_team='TeamB',
            prob_home=0.75,
            prob_draw=0.15,
            prob_away=0.10,
            prediction='H',
            expected_home_goals=2.5,
            expected_away_goals=0.5,
            most_likely_score='2-0',
            score_distribution={},
            totals_prediction=None,
            handicap_prediction=None
        )
        
        value_bets = kelly.find_value_bets(prediction, sample_odds)
        allocations = kelly.allocate_bankroll(value_bets, 1000)
        
        total_bet = sum(a['bet_amount'] for a in allocations)
        # 总投注不应超过资金
        assert total_bet <= 1000
    
    def test_allocate_bankroll_normalized_kelly(self, kelly, sample_odds):
        """归一化Kelly比例总和为1"""
        prediction = MatchPrediction(
            match_id='test-001',
            home_team='TeamA',
            away_team='TeamB',
            prob_home=0.75,
            prob_draw=0.15,
            prob_away=0.10,
            prediction='H',
            expected_home_goals=2.5,
            expected_away_goals=0.5,
            most_likely_score='2-0',
            score_distribution={},
            totals_prediction=None,
            handicap_prediction=None
        )
        
        value_bets = kelly.find_value_bets(prediction, sample_odds)
        allocations = kelly.allocate_bankroll(value_bets, 1000)
        
        if allocations:
            total_normalized = sum(a['normalized_kelly'] for a in allocations)
            assert abs(total_normalized - 1.0) < 0.001


class TestKellyEdgeCases:
    """Kelly边界条件测试"""
    
    def test_kelly_with_zero_odds(self, kelly):
        """赔率为0"""
        fraction = kelly.calculate_kelly_fraction(0.5, 0)
        # 除数为0，应返回0或负值
        assert fraction <= 0
    
    def test_kelly_with_zero_probability(self, kelly):
        """概率为0"""
        fraction = kelly.calculate_kelly_fraction(0, 2.0)
        # Kelly = (0 * 2 - 1) / 2 = -0.5
        assert fraction < 0
    
    def test_kelly_with_probability_one(self, kelly):
        """概率为1"""
        fraction = kelly.calculate_kelly_fraction(1.0, 1.1)
        # Kelly = (1 * 1.1 - 0) / 1.1 = 1
        # 限制在max_fraction
        assert 0 < fraction <= kelly.max_fraction
    
    def test_find_value_bets_with_zero_odds(self, kelly):
        """赔率数据缺失"""
        prediction = MatchPrediction(
            match_id='test-001',
            home_team='TeamA',
            away_team='TeamB',
            prob_home=0.70,
            prob_draw=0.20,
            prob_away=0.10,
            prediction='H',
            expected_home_goals=2.0,
            expected_away_goals=0.8,
            most_likely_score='2-0',
            score_distribution={},
            totals_prediction=None,
            handicap_prediction=None
        )
        
        # 缺失赔率
        incomplete_odds = {
            'home_odds': 0,  # 无效赔率
            'home_bookmaker': '',
            'draw_odds': 0,
            'draw_bookmaker': '',
            'away_odds': 0,
            'away_bookmaker': '',
            'market_prob_home': 0,
            'market_prob_draw': 0,
            'market_prob_away': 0
        }
        
        value_bets = kelly.find_value_bets(prediction, incomplete_odds)
        
        # 应返回空列表或跳过无效项
        assert len(value_bets) <= 3
    
    def test_min_edge_threshold(self, kelly):
        """最小价值阈值"""
        # 创建接近阈值的情况
        prediction = MatchPrediction(
            match_id='test-001',
            home_team='TeamA',
            away_team='TeamB',
            prob_home=0.52,  # 模型52%
            prob_draw=0.26,
            prob_away=0.22,
            prediction='H',
            expected_home_goals=1.5,
            expected_away_goals=1.2,
            most_likely_score='1-1',
            score_distribution={},
            totals_prediction=None,
            handicap_prediction=None
        )
        
        odds = {
            'home_odds': 1.9,  # 市场52.6%
            'home_bookmaker': 'Bet365',
            'draw_odds': 3.5,
            'draw_bookmaker': 'Bet365',
            'away_odds': 4.0,
            'away_bookmaker': 'Bet365',
            'market_prob_home': 1/1.9,  # 52.6%
            'market_prob_draw': 1/3.5,
            'market_prob_away': 1/4.0
        }
        
        value_bets = kelly.find_value_bets(prediction, odds)
        home_bet = [vb for vb in value_bets if vb.outcome == 'H'][0]
        
        # value = 0.52 - 0.526 = -0.006，低于min_edge(0.02)
        # 不应为价值投注
        if home_bet.value < kelly.min_edge:
            assert home_bet.is_value_bet == False