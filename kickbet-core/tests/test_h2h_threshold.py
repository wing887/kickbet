"""
测试更新后的H2H融合逻辑
"""

import sys
sys.path.insert(0, '.')

from database.history_models import HistoryDBManager
from predictors.poisson_predictor import PoissonPredictor

db = HistoryDBManager()
predictor = PoissonPredictor(nsim=10000)
predictor.load_stats_from_history_db(db)

# 测试不同交锋场次的比赛
test_cases = [
    # 曼城 vs 水晶宫（交锋5场）
    {'home_id': 18, 'away_id': 16, 'home': 'Man City', 'away': 'Crystal Palace'},
    # 曼联 vs 利物浦（交锋6场）
    {'home_id': 1, 'away_id': 4, 'home': 'Man United', 'away': 'Liverpool'},
    # 阿森纳 vs 切尔西（交锋2场）
    {'home_id': 2, 'away_id': 3, 'home': 'Arsenal', 'away': 'Chelsea'},
]

print('=' * 60)
print('测试H2H融合逻辑（阈值=5场）')
print('=' * 60)

for case in test_cases:
    h2h = db.get_head_to_head_stats(case['home_id'], case['away_id'], limit=10)
    
    print(f"\n{case['home']} vs {case['away']}")
    print(f"交锋场次: {h2h['total_matches']}场")
    
    pred = predictor.predict_match_with_h2h(
        match_id='test',
        home_team=case['home'],
        away_team=case['away'],
        home_team_id=case['home_id'],
        away_team_id=case['away_id'],
        h2h_stats=h2h,
        h2h_weight=0.15,  # 基础权重15%
        h2h_threshold=5   # 阈值5场
    )
    
    # 判断是否启用H2H
    h2h_enabled = h2h['total_matches'] >= 5
    
    if h2h_enabled:
        # 计算自适应权重
        adaptive_weight = min(0.45, 0.15 + (h2h['total_matches'] - 5) * 0.02)
        print(f"H2H启用: ✓ (自适应权重 {adaptive_weight:.0%})")
    else:
        print(f"H2H启用: ✗ (交锋{h2h['total_matches']}场 < 阈值5场)")
    
    print(f"Poisson: H={pred.prob_home:.1%} D={pred.prob_draw:.1%} A={pred.prob_away:.1%}")
    
    if pred.combined_prob_home and pred.combined_prob_home != pred.prob_home:
        print(f"综合: H={pred.combined_prob_home:.1%} D={pred.combined_prob_draw:.1%} A={pred.combined_prob_away:.1%}")
    
    print(f"预测: {pred.prediction}")

print("\n" + "=" * 60)
print("自适应权重说明")
print("=" * 60)
print("5场 → 15%, 10场 → 25%, 15场 → 35%, 20+场 → 45%")
print("样本越大，H2H历史数据权重越高")