"""
测试Poisson预测模型核心功能
"""
import sys
sys.path.insert(0, '/mnt/c/Users/admin/Desktop/KickBet项目文档/kickbet-core')

from predictors.poisson_predictor import (
    PoissonPredictor, 
    KellyCriterion,
    TeamAttackDefenseStats,
    MatchPrediction
)

def test_poisson_model():
    print("=" * 50)
    print("KickBet Poisson预测模型测试")
    print("=" * 50)
    
    # 1. 创建预测器
    predictor = PoissonPredictor(nsim=10000)
    
    # 2. 设置球队统计数据（曼城 vs 布伦特福德）
    home_stats = TeamAttackDefenseStats(
        team_id=1,
        team_name="曼城",
        home_scored_avg=2.1,    # 主场场均进球
        home_conceded_avg=0.8,  # 主场场均失球
        home_played=15,
        away_scored_avg=1.8,
        away_conceded_avg=1.0,
        away_played=15
    )
    
    away_stats = TeamAttackDefenseStats(
        team_id=2,
        team_name="布伦特福德",
        home_scored_avg=1.5,
        home_conceded_avg=1.3,
        home_played=15,
        away_scored_avg=1.2,    # 客场场均进球
        away_conceded_avg=1.5,  # 客场场均失球
        away_played=15
    )
    
    # 设置球队统计到预测器
    predictor.set_team_stats(1, home_stats)
    predictor.set_team_stats(2, away_stats)
    
    # 3. 运行预测
    print("\n[测试] 曼城(主场) vs 布伦特福德(客场)")
    print("-" * 40)
    
    result = predictor.predict_match(
        match_id="test_001",
        home_team="曼城",
        away_team="布伦特福德",
        home_team_id=1,
        away_team_id=2
    )
    
    print(f"\nPoisson概率模型结果:")
    print(f"  主胜概率: {result.prob_home:.1%}")
    print(f"  平局概率: {result.prob_draw:.1%}")
    print(f"  客胜概率: {result.prob_away:.1%}")
    print(f"  预测结果: {result.prediction}")
    
    print(f"\n预期进球:")
    print(f"  主队进球: {result.expected_home_goals:.2f}")
    print(f"  客队进球: {result.expected_away_goals:.2f}")
    
    print(f"\n最可能比分: {result.most_likely_score}")
    
    # 查看比分分布
    print(f"\n比分分布 (前5个):")
    sorted_scores = sorted(result.score_distribution.items(), key=lambda x: x[1], reverse=True)[:5]
    for score, prob in sorted_scores:
        print(f"  {score}: {prob:.1%}")
    
    # 4. Kelly Criterion测试
    print("\n" + "=" * 50)
    print("Kelly Criterion投注建议测试")
    print("=" * 50)
    
    kelly = KellyCriterion()
    
    # 模拟赔率
    odds_home = 1.42
    odds_draw = 4.50
    odds_away = 8.00
    
    print(f"\n赔率数据:")
    print(f"  主胜: {odds_home}")
    print(f"  平局: {odds_draw}")
    print(f"  客胜: {odds_away}")
    
    # Kelly计算
    kelly_home = kelly.calculate_kelly_fraction(result.prob_home, odds_home)
    kelly_draw = kelly.calculate_kelly_fraction(result.prob_draw, odds_draw)
    kelly_away = kelly.calculate_kelly_fraction(result.prob_away, odds_away)
    
    print(f"\nKelly计算结果:")
    print(f"  主胜 Kelly比例: {kelly_home:.2%}")
    print(f"  主胜 Half-Kelly: {kelly_home/2:.2%}")
    print(f"  主胜 价值优势:   {(result.prob_home * odds_home - 1):.2%}")
    print(f"  主胜 是否有价值: {kelly_home > 0}")
    
    print(f"\n  平局 Kelly比例: {kelly_draw:.2%}")
    print(f"  平局 是否有价值: {kelly_draw > 0}")
    
    print(f"\n  客胜 Kelly比例: {kelly_away:.2%}")
    print(f"  客胜 是否有价值: {kelly_away > 0}")
    
    # 5. 投注建议
    print("\n" + "=" * 50)
    print("综合投注建议")
    print("=" * 50)
    
    if kelly_home > 0:
        print(f"\n推荐: 主胜 @ {odds_home}")
        print(f"  原因: Kelly比例{kelly_home:.1%} > 0, 有正价值")
        print(f"  建议投注: 本金的{kelly_home/2:.1%} (Half-Kelly)")
    else:
        print("\n主胜无价值投注")
    
    if kelly_draw > 0:
        print(f"\n平局 @ {odds_draw} 也有价值 (Kelly={kelly_draw:.1%})")
    
    if kelly_away > 0:
        print(f"\n客胜 @ {odds_away} 也有价值 (Kelly={kelly_away:.1%})")
    
    # 6. 验证结果合理性
    print("\n" + "=" * 50)
    print("模型合理性验证")
    print("=" * 50)
    
    errors = []
    
    # 概率总和应为100%
    prob_sum = result.prob_home + result.prob_draw + result.prob_away
    if abs(prob_sum - 1.0) > 0.02:
        errors.append(f"概率总和={prob_sum:.2%}, 应为100%")
    else:
        print(f"OK: 概率总和 = {prob_sum:.1%}")
    
    # 概率应在0-1之间
    for name, prob in [('主胜', result.prob_home), ('平局', result.prob_draw), ('客胜', result.prob_away)]:
        if prob < 0 or prob > 1:
            errors.append(f"{name}概率={prob}超出范围")
        else:
            print(f"OK: {name}概率 = {prob:.1%} 在有效范围内")
    
    # Kelly比例应在合理范围
    for name, k in [('主胜', kelly_home), ('平局', kelly_draw), ('客胜', kelly_away)]:
        if k < -1 or k > 1:
            errors.append(f"{name} Kelly={k:.2%}超出合理范围")
        else:
            print(f"OK: {name} Kelly = {k:.2%}")
    
    # 验证预期进球合理
    if result.expected_home_goals < 0 or result.expected_home_goals > 10:
        errors.append(f"主队预期进球={result.expected_home_goals}不合理")
    else:
        print(f"OK: 主队预期进球 = {result.expected_home_goals:.2f}")
    
    if result.expected_away_goals < 0 or result.expected_away_goals > 10:
        errors.append(f"客队预期进球={result.expected_away_goals}不合理")
    else:
        print(f"OK: 客队预期进球 = {result.expected_away_goals:.2f}")
    
    if errors:
        print(f"\n发现错误:")
        for e in errors:
            print(f"  ERROR: {e}")
        return False
    else:
        print("\n所有测试通过! 模型工作正常")
        return True


if __name__ == "__main__":
    success = test_poisson_model()
    sys.exit(0 if success else 1)