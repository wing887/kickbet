"""
深入分析：原始算法 vs 我们的版本差异根源

问题发现：
- 曼城vs水晶宫（交锋5场）：差异12.1%
- 原始算法使用H2H模式（λ直接来自交锋历史）
- 我们的版本使用主客场统计

核心差异：原始算法在交锋>3场时**完全**使用H2H统计
"""

import sys
sys.path.insert(0, '.')

import random
import math
from database.history_models import HistoryDBManager

def analyze_lambda_calculation():
    """分析λ计算方式的差异"""
    db = HistoryDBManager()
    session = db.get_session()
    
    # 曼城 vs 水晶宫
    home_id = 18  # 曼城
    away_id = 16  # 水晶宫
    
    print("=" * 80)
    print("λ计算方式对比分析：曼城 vs 水晶宫")
    print("=" * 80)
    
    # 获取主客场统计
    home_stats = db.get_team_stats_from_history(home_id)
    away_stats = db.get_team_stats_from_history(away_id)
    
    # 获取H2H统计
    h2h = db.get_head_to_head_stats(home_id, away_id, limit=10)
    
    print("\n【主客场统计】")
    print(f"曼城主场：场均进球 {home_stats['home_scored_avg']:.2f}，场均失球 {home_stats['home_conceded_avg']:.2f}")
    print(f"曼城客场：场均进球 {home_stats['away_scored_avg']:.2f}，场均失球 {home_stats['away_conceded_avg']:.2f}")
    print(f"水晶宫主场：场均进球 {away_stats['home_scored_avg']:.2f}，场均失球 {away_stats['home_conceded_avg']:.2f}")
    print(f"水晶宫客场：场均进球 {away_stats['away_scored_avg']:.2f}，场均失球 {away_stats['away_conceded_avg']:.2f}")
    
    print("\n【交锋历史】")
    print(f"总场次：{h2h['total_matches']}场")
    print(f"曼城主场交锋进球：场均 {h2h['avg_team_a_goals']:.2f}")
    print(f"水晶宫客场交锋进球：场均 {h2h['avg_team_b_goals']:.2f}")
    
    # 计算两种λ
    print("\n【λ计算对比】")
    
    # 方法1：原始算法 - 主客场综合（当交锋<=3场时用）
    lambda_home_m1 = 0.5 * (home_stats['home_scored_avg'] + away_stats['away_conceded_avg'])
    lambda_away_m1 = 0.5 * (away_stats['away_scored_avg'] + home_stats['home_conceded_avg'])
    print(f"方法1（主客场综合）:")
    print(f"  λ_home = 0.5 × (曼城主场进球{home_stats['home_scored_avg']:.2f} + 水晶宫客场失球{away_stats['away_conceded_avg']:.2f})")
    print(f"  λ_home = {lambda_home_m1:.2f}")
    print(f"  λ_away = 0.5 × (水晶宫客场进球{away_stats['away_scored_avg']:.2f} + 曼城主场失球{home_stats['home_conceded_avg']:.2f})")
    print(f"  λ_away = {lambda_away_m1:.2f}")
    
    # 方法2：原始算法 - 纯H2H（当交锋>3场时用）
    lambda_home_m2 = h2h['avg_team_a_goals']  # 直接用交锋历史
    lambda_away_m2 = h2h['avg_team_b_goals']
    print(f"\n方法2（原始算法 - 纯H2H，交锋>3场时）:")
    print(f"  λ_home = 交锋时曼城主场场均进球 = {lambda_home_m2:.2f}")
    print(f"  λ_away = 交锋时水晶宫客场场均进球 = {lambda_away_m2:.2f}")
    
    # 方法3：我们的版本 - 主客场综合（H2H融合可选）
    lambda_home_m3 = lambda_home_m1  # 我们始终用方法1
    lambda_away_m3 = lambda_away_m1
    print(f"\n方法3（我们的版本 - 主客场综合）:")
    print(f"  λ_home = {lambda_home_m3:.2f}（同方法1）")
    print(f"  λ_away = {lambda_away_m3:.2f}")
    print(f"  H2H融合：可选权重，不影响λ基础值")
    
    print("\n【差异分析】")
    print(f"原始算法在交锋>3场时使用λ={lambda_home_m2:.2f}/{lambda_away_m2:.2f}")
    print(f"我们的版本始终使用λ={lambda_home_m3:.2f}/{lambda_away_m3:.2f}")
    print(f"λ差异：主场 {abs(lambda_home_m2 - lambda_home_m3):.2f}，客场 {abs(lambda_away_m2 - lambda_away_m3):.2f}")
    
    # 理论分析
    print("\n【理论分析】")
    print("原始算法的H2H逻辑（R代码）：")
    print("  if (h2h_matches > 3) {")
    print("    λ_home = h2h_home_scored_avg  // 直接用交锋历史")
    print("    λ_away = h2h_away_scored_avg")
    print("  } else {")
    print("    λ_home = 0.5 × (home_scored + away_conceded)")
    print("  }")
    print("\n问题：H2H统计中的avg_team_a_goals是什么？")
    print(f"  当前实现：{h2h['avg_team_a_goals']:.2f}（交锋时主队场均进球）")
    print(f"  这是在交锋比赛中，主队（曼城）的总进球场均")
    
    # 检查交锋历史具体数据
    print("\n【交锋历史详细】")
    print("  需要查看history_models.py的get_head_to_head_stats方法")
    print(f"  交锋场次：{h2h['total_matches']}场")
    print(f"  曼城作为主队时的进球：场均 {h2h['avg_team_a_goals']:.2f}")
    print(f"  水晶宫作为客队时的进球：场均 {h2h['avg_team_b_goals']:.2f}")
    
    # 关键发现
    print("\n【关键发现】")
    print("原始R代码的H2H λ计算方式：")
    print("  ave_h_s = mean(subset$home_goals)  // 主队在交锋中的进球")
    print("  ave_a_s = mean(subset$away_goals)  // 客队在交锋中的进球")
    print("\n但subset是筛选特定主客队交锋的数据...")
    print("  subset = filter(all_matches, home_team=='Man City' & away_team=='Crystal Palace')")
    print("\n这意味着原始算法只看'曼城主场vs水晶宫'的交锋，而非全部交锋！")
    
    session.close()
    
    return {
        'lambda_method1': (lambda_home_m1, lambda_away_m1),
        'lambda_method2': (lambda_home_m2, lambda_away_m2),
        'lambda_method3': (lambda_home_m3, lambda_away_m3),
        'h2h_matches': h2h['total_matches']
    }


def compare_prediction_accuracy():
    """对比预测准确性"""
    db = HistoryDBManager()
    
    print("\n" + "=" * 80)
    print("预测准确性对比")
    print("=" * 80)
    
    # 使用Monte Carlo模拟两种λ的结果
    def simulate(lambda_h, lambda_a, nsim=10000):
        results = {'H': 0, 'D': 0, 'A': 0}
        for _ in range(nsim):
            h_goals = poisson_sample(lambda_h)
            a_goals = poisson_sample(lambda_a)
            if h_goals > a_goals:
                results['H'] += 1
            elif h_goals == a_goals:
                results['D'] += 1
            else:
                results['A'] += 1
        return {k: v/nsim for k, v in results.items()}
    
    # Poisson采样函数
    def poisson_sample(lam):
        if lam <= 0:
            return 0
        L = math.exp(-lam)
        k = 0
        p = 1.0
        while p > L:
            k += 1
            p *= random.random()
        return k - 1
    
    # 曼城vs水晶宫的两种λ
    lambda_h2h = (3.2, 1.6)  # 原始H2H模式
    lambda_standard = (1.96, 1.12)  # 主客场综合
    
    print("\n【模拟预测】")
    results_h2h = simulate(lambda_h2h[0], lambda_h2h[1])
    results_std = simulate(lambda_standard[0], lambda_standard[1])
    
    print(f"H2H模式 (λ=3.2/1.6): H={results_h2h['H']:.1%} D={results_h2h['D']:.1%} A={results_h2h['A']:.1%}")
    print(f"标准模式 (λ=1.96/1.12): H={results_std['H']:.1%} D={results_std['D']:.1%} A={results_std['A']:.1%}")
    
    print("\n【差异原因】")
    print("H2H模式λ更高（3.2 vs 1.96）→ 主胜概率更高（69% vs 57%）")
    print("原因：交锋历史中曼城进球更多（交锋样本vs长期统计）")
    
    print("\n【哪个更准确？】")
    print("需要验证：")
    print("1. H2H样本是否足够代表当前球队实力？")
    print("2. 主客场长期统计是否更能反映真实水平？")
    print("3. 原始算法作者是否有验证H2H模式更准确？")


if __name__ == '__main__':
    analyze_lambda_calculation()
    compare_prediction_accuracy()