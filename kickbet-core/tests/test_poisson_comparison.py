"""
对比原始Poisson算法 vs 我们的增强版本

测试方法：
1. 实现原始算法（纯净版，无增强）
2. 使用相同的球队统计数据
3. 多次预测对比结果差异
"""

import sys
sys.path.insert(0, '.')

import random
import math
from typing import Dict, Tuple
from dataclasses import dataclass
from database.history_models import HistoryDBManager, Team

# ==================== 原始Poisson算法（纯净版） ====================

def poisson_sample_original(lambda_param: float) -> int:
    """Knuth算法生成Poisson随机数"""
    if lambda_param <= 0:
        return 0
    L = math.exp(-lambda_param)
    k = 0
    p = 1.0
    while p > L:
        k += 1
        p *= random.random()
    return k - 1


@dataclass
class OriginalTeamStats:
    """原始算法需要的球队统计"""
    team_name: str
    # 主场统计
    home_scored_avg: float  # 主场场均进球
    home_conceded_avg: float  # 主场场均失球
    # 客场统计
    away_scored_avg: float  # 客场场均进球
    away_conceded_avg: float  # 客场场均失球
    # 交锋统计（原始算法特有）
    h2h_home_scored_avg: float = 0.0  # 交锋时主场场均进球
    h2h_away_scored_avg: float = 0.0  # 交锋时客场场均进球
    h2h_matches: int = 0  # 交锋场次


class OriginalPoissonPredictor:
    """
    原始Poisson算法（从R代码移植，纯净版）
    
    核心逻辑：
    1. 如果两队交锋超过3场 → 使用交锋历史统计
    2. 否则 → 使用主客场综合统计
    
    λ_home = 0.5 × (主队主场场均进球 + 客队客场场均失球)
    λ_away = 0.5 × (客队客场场均进球 + 主队主场场均失球)
    """
    
    def __init__(self, nsim: int = 10000):
        self.nsim = nsim
        self._team_stats: Dict[str, OriginalTeamStats] = {}
    
    def set_team_stats(self, team_name: str, stats: OriginalTeamStats):
        self._team_stats[team_name] = stats
    
    def predict_match(self, home_team: str, away_team: str,
                      use_h2h_threshold: int = 3) -> Dict:
        """
        预测比赛（原始算法）
        
        Args:
            home_team: 主队名称
            away_team: 客队名称
            use_h2h_threshold: 交锋场次阈值（>threshold时用H2H）
        
        Returns:
            预测结果字典
        """
        home_stats = self._team_stats.get(home_team)
        away_stats = self._team_stats.get(away_team)
        
        if not home_stats or not away_stats:
            return {'error': '缺少球队统计'}
        
        # 原始算法核心：判断是否用H2H
        # 如果交锋场次 > threshold，使用交锋历史统计
        if home_stats.h2h_matches > use_h2h_threshold:
            lambda_home = home_stats.h2h_home_scored_avg
            lambda_away = away_stats.h2h_away_scored_avg
            h2h_mode = True
        else:
            # 否则用主客场统计
            lambda_home = 0.5 * (home_stats.home_scored_avg + away_stats.away_conceded_avg)
            lambda_away = 0.5 * (away_stats.away_scored_avg + home_stats.home_conceded_avg)
            h2h_mode = False
        
        # Monte Carlo模拟
        results = {'H': 0, 'D': 0, 'A': 0}
        score_counts = {}
        
        for _ in range(self.nsim):
            home_goals = poisson_sample_original(lambda_home)
            away_goals = poisson_sample_original(lambda_away)
            
            score_key = f"{home_goals}-{away_goals}"
            score_counts[score_key] = score_counts.get(score_key, 0) + 1
            
            if home_goals > away_goals:
                results['H'] += 1
            elif home_goals == away_goals:
                results['D'] += 1
            else:
                results['A'] += 1
        
        probs = {
            'H': results['H'] / self.nsim,
            'D': results['D'] / self.nsim,
            'A': results['A'] / self.nsim
        }
        
        # 原始算法的结果校准
        # 如果主胜和客胜概率差距<0.01，预测为平局
        if abs(probs['H'] - probs['A']) < 0.01:
            prediction = 'D'
        else:
            max_prob = max(probs['H'], probs['D'], probs['A'])
            if probs['H'] == max_prob:
                prediction = 'H'
            elif probs['D'] == max_prob:
                prediction = 'D'
            else:
                prediction = 'A'
        
        return {
            'prob_home': round(probs['H'], 4),
            'prob_draw': round(probs['D'], 4),
            'prob_away': round(probs['A'], 4),
            'prediction': prediction,
            'lambda_home': round(lambda_home, 2),
            'lambda_away': round(lambda_away, 2),
            'h2h_mode': h2h_mode,
            'h2h_matches': home_stats.h2h_matches,
            'most_likely_score': max(score_counts, key=score_counts.get)
        }


# ==================== 测试对比 ====================

def get_team_stats_from_db(db: HistoryDBManager, team_id: int) -> OriginalTeamStats:
    """从历史数据库获取球队统计"""
    stats = db.get_team_stats_from_history(team_id)
    
    if not stats:
        return None
    
    session = db.get_session()
    try:
        from database.history_models import Team
        team = session.query(Team).filter(Team.team_id == team_id).first()
        team_name = team.name if team else f"Team_{team_id}"
    finally:
        session.close()
    
    return OriginalTeamStats(
        team_name=team_name,
        home_scored_avg=stats.get('home_scored_avg', 1.5),
        home_conceded_avg=stats.get('home_conceded_avg', 1.0),
        away_scored_avg=stats.get('away_scored_avg', 1.2),
        away_conceded_avg=stats.get('away_conceded_avg', 1.3),
        h2h_home_scored_avg=0.0,
        h2h_away_scored_avg=0.0,
        h2h_matches=0
    )


def run_comparison():
    """运行多次对比测试"""
    db = HistoryDBManager()
    session = db.get_session()
    
    # 初始化两个预测器
    original_predictor = OriginalPoissonPredictor(nsim=10000)
    
    # 导入我们的增强版本
    from predictors.poisson_predictor import PoissonPredictor
    our_predictor = PoissonPredictor(nsim=10000)
    our_predictor.load_stats_from_history_db(db)
    
    # 测试比赛列表
    test_matches = [
        # 曼城 vs 水晶宫（交锋5场）
        {'home': 'Manchester City FC', 'home_id': 18, 
         'away': 'Crystal Palace FC', 'away_id': 16},
        # 曼联 vs 利物浦（交锋6场）
        {'home': 'Manchester United FC', 'home_id': 1,
         'away': 'Liverpool FC', 'away_id': 4},
        # 阿森纳 vs 切尔西（同城德比）
        {'home': 'Arsenal FC', 'home_id': 2,
         'away': 'Chelsea FC', 'away_id': 3},
        # 巴塞罗那 vs 皇马（交锋少）
        {'home': 'FC Barcelona', 'home_id': None,
         'away': 'Real Madrid CF', 'away_id': None},
    ]
    
    print("=" * 80)
    print("Poisson算法对比测试：原始版本 vs 我们的增强版本")
    print("=" * 80)
    
    results_comparison = []
    
    for match in test_matches:
        if match['home_id'] is None:
            print(f"\n跳过: {match['home']} vs {match['away']} (无team_id)")
            continue
        
        print(f"\n{'='*60}")
        print(f"比赛: {match['home']} vs {match['away']}")
        print(f"{'='*60}")
        
        # 获取H2H统计
        h2h = db.get_head_to_head_stats(match['home_id'], match['away_id'], limit=10)
        
        # 获取球队统计
        home_stats = get_team_stats_from_db(db, match['home_id'])
        away_stats = get_team_stats_from_db(db, match['away_id'])
        
        if not home_stats or not away_stats:
            print("缺少球队统计，跳过")
            continue
        
        # 设置H2H统计（原始算法特有）
        if h2h['total_matches'] > 0:
            home_stats.h2h_home_scored_avg = h2h['avg_team_a_goals']
            away_stats.h2h_away_scored_avg = h2h['avg_team_b_goals']
            home_stats.h2h_matches = h2h['total_matches']
        
        # 加载到原始预测器
        original_predictor.set_team_stats(home_stats.team_name, home_stats)
        original_predictor.set_team_stats(away_stats.team_name, away_stats)
        
        # 简化队名
        home_short = home_stats.team_name.replace(' FC', '').replace(' CF', '')
        away_short = away_stats.team_name.replace(' FC', '').replace(' CF', '')
        
        # 运行多次预测（取平均）
        original_results = []
        our_results = []
        
        for run in range(5):  # 运行5次取平均
            # 原始算法预测
            orig_pred = original_predictor.predict_match(
                home_stats.team_name, 
                away_stats.team_name,
                use_h2h_threshold=3
            )
            original_results.append(orig_pred)
            
            # 我们的增强版本预测
            our_pred = our_predictor.predict_match_with_h2h(
                match_id=f"test-{match['home_id']}-{match['away_id']}",
                home_team=home_short,
                away_team=away_short,
                home_team_id=match['home_id'],
                away_team_id=match['away_id'],
                h2h_stats=h2h,
                h2h_weight=0.0  # 纯Poisson，不融合H2H
            )
            our_results.append({
                'prob_home': our_pred.prob_home,
                'prob_draw': our_pred.prob_draw,
                'prob_away': our_pred.prob_away,
                'prediction': our_pred.prediction,
                'lambda_home': our_pred.expected_home_goals,
                'lambda_away': our_pred.expected_away_goals
            })
        
        # 计算平均值
        def avg_results(results_list):
            avg_h = sum(r['prob_home'] for r in results_list) / len(results_list)
            avg_d = sum(r['prob_draw'] for r in results_list) / len(results_list)
            avg_a = sum(r['prob_away'] for r in results_list) / len(results_list)
            return avg_h, avg_d, avg_a
        
        orig_h, orig_d, orig_a = avg_results(original_results)
        our_h, our_d, our_a = avg_results(our_results)
        
        # 显示对比
        print(f"\n【历史交锋】: {h2h['total_matches']}场")
        print(f"  主队交锋胜: {h2h['team_a_wins']}场 ({h2h['team_a_win_rate']:.1%})")
        print(f"  平局: {h2h['draws']}场 ({h2h['draw_rate']:.1%})")
        print(f"  客队交锋胜: {h2h['team_b_wins']}场 ({h2h['team_b_win_rate']:.1%})")
        
        print(f"\n【原始算法】 (阈值=3场)")
        print(f"  H/D/A: {orig_h:.1%} / {orig_d:.1%} / {orig_a:.1%}")
        print(f"  λ: {orig_pred['lambda_home']} vs {orig_pred['lambda_away']}")
        print(f"  使用H2H模式: {orig_pred['h2h_mode']}")
        print(f"  预测: {orig_pred['prediction']}")
        
        print(f"\n【我们的版本】 (h2h_weight=0)")
        print(f"  H/D/A: {our_h:.1%} / {our_d:.1%} / {our_a:.1%}")
        print(f"  λ: {our_results[0]['lambda_home']} vs {our_results[0]['lambda_away']}")
        print(f"  预测: {our_results[0]['prediction']}")
        
        # 差异分析
        diff_h = abs(orig_h - our_h)
        diff_d = abs(orig_d - our_d)
        diff_a = abs(orig_a - our_a)
        max_diff = max(diff_h, diff_d, diff_a)
        
        print(f"\n【差异分析】")
        print(f"  最大差异: {max_diff:.1%}")
        if max_diff < 0.02:
            print(f"  结论: ✓ 一致（差异<2%）")
        elif max_diff < 0.05:
            print(f"  结论: ~ 接近（差异<5%）")
        else:
            print(f"  结论: ✗ 差异较大（需检查）")
        
        results_comparison.append({
            'match': f"{home_short} vs {away_short}",
            'h2h_matches': h2h['total_matches'],
            'original': {'H': orig_h, 'D': orig_d, 'A': orig_a},
            'ours': {'H': our_h, 'D': our_d, 'A': our_a},
            'max_diff': max_diff
        })
    
    session.close()
    
    # 总结
    print("\n" + "=" * 80)
    print("对比总结")
    print("=" * 80)
    
    for r in results_comparison:
        print(f"{r['match']} ({r['h2h_matches']}场交锋): 最大差异 {r['max_diff']:.1%}")
    
    avg_diff = sum(r['max_diff'] for r in results_comparison) / len(results_comparison)
    print(f"\n平均差异: {avg_diff:.1%}")
    
    if avg_diff < 0.02:
        print("总体结论: ✓ 我们的实现与原始算法一致")
    elif avg_diff < 0.05:
        print("总体结论: ~ 存在轻微差异，可能来自随机模拟")
    else:
        print("总体结论: ✗ 存在显著差异，需要检查算法逻辑")


if __name__ == '__main__':
    run_comparison()