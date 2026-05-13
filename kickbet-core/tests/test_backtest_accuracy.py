"""
回测验证：对比原始Poisson算法 vs 我们的实现

方法：
1. 用历史比赛数据（已知结果）
2. 分别用两种算法预测
3. 对比预测准确率
"""

import sys
sys.path.insert(0, '.')

import random
import math
from typing import Dict, List
from dataclasses import dataclass
from database.history_models import HistoryDBManager, HistoricalMatch, Team, Season, League

# ==================== 原始Poisson算法 ====================

def poisson_sample(lam: float) -> int:
    if lam <= 0:
        return 0
    L = math.exp(-lam)
    k = 0
    p = 1.0
    while p > L:
        k += 1
        p *= random.random()
    return k - 1


@dataclass
class TeamStats:
    """球队统计"""
    team_name: str
    home_scored_avg: float
    home_conceded_avg: float
    away_scored_avg: float
    away_conceded_avg: float
    # 特定对手H2H（原始算法专用）
    h2h_home_scored: float = 0.0
    h2h_away_scored: float = 0.0
    h2h_matches: int = 0


class OriginalPoisson:
    """原始算法：特定主客位置H2H，>3场时完全替换λ"""
    
    def __init__(self, nsim=10000):
        self.nsim = nsim
        self._stats: Dict[str, TeamStats] = {}
    
    def set_stats(self, team: str, stats: TeamStats):
        self._stats[team] = stats
    
    def predict(self, home: str, away: str, h2h_threshold=3) -> Dict:
        home_s = self._stats.get(home)
        away_s = self._stats.get(away)
        
        if not home_s or not away_s:
            return {'error': 'missing stats'}
        
        if home_s.h2h_matches > h2h_threshold:
            lam_h = home_s.h2h_home_scored
            lam_a = away_s.h2h_away_scored
            h2h_mode = True
        else:
            lam_h = 0.5 * (home_s.home_scored_avg + away_s.away_conceded_avg)
            lam_a = 0.5 * (away_s.away_scored_avg + home_s.home_conceded_avg)
            h2h_mode = False
        
        results = {'H': 0, 'D': 0, 'A': 0}
        for _ in range(self.nsim):
            h = poisson_sample(lam_h)
            a = poisson_sample(lam_a)
            if h > a:
                results['H'] += 1
            elif h == a:
                results['D'] += 1
            else:
                results['A'] += 1
        
        probs = {k: v/self.nsim for k, v in results.items()}
        
        if abs(probs['H'] - probs['A']) < 0.01:
            pred = 'D'
        else:
            pred = max(probs, key=probs.get)
        
        return {
            'prob_home': probs['H'],
            'prob_draw': probs['D'],
            'prob_away': probs['A'],
            'prediction': pred,
            'h2h_mode': h2h_mode,
            'h2h_matches': home_s.h2h_matches
        }


class OurPoisson:
    """我们的版本：主客场综合λ"""
    
    def __init__(self, nsim=10000):
        self.nsim = nsim
        self._stats: Dict[str, TeamStats] = {}
    
    def set_stats(self, team: str, stats: TeamStats):
        self._stats[team] = stats
    
    def predict(self, home: str, away: str) -> Dict:
        home_s = self._stats.get(home)
        away_s = self._stats.get(away)
        
        if not home_s or not away_s:
            return {'error': 'missing stats'}
        
        lam_h = 0.5 * (home_s.home_scored_avg + away_s.away_conceded_avg)
        lam_a = 0.5 * (away_s.away_scored_avg + home_s.home_conceded_avg)
        
        results = {'H': 0, 'D': 0, 'A': 0}
        for _ in range(self.nsim):
            h = poisson_sample(lam_h)
            a = poisson_sample(lam_a)
            if h > a:
                results['H'] += 1
            elif h == a:
                results['D'] += 1
            else:
                results['A'] += 1
        
        probs = {k: v/self.nsim for k, v in results.items()}
        
        if abs(probs['H'] - probs['A']) < 0.01:
            pred = 'D'
        else:
            pred = max(probs, key=probs.get)
        
        return {
            'prob_home': probs['H'],
            'prob_draw': probs['D'],
            'prob_away': probs['A'],
            'prediction': pred
        }


# ==================== 回测框架 ====================

def load_test_matches(db: HistoryDBManager, season_name: str = '2024', league_code: str = 'PL') -> List[Dict]:
    """加载测试比赛"""
    session = db.get_session()
    
    # 查找赛季
    season = session.query(Season).filter(Season.season_code == season_name).first()
    if not season:
        print(f"找不到赛季: {season_name}")
        session.close()
        return []
    
    # 查找联赛
    league = session.query(League).filter(League.code == league_code).first()
    if not league:
        print(f"找不到联赛: {league_code}")
        session.close()
        return []
    
    matches = session.query(HistoricalMatch).filter(
        HistoricalMatch.season_id == season.season_id,
        HistoricalMatch.league_id == league.league_id,
        HistoricalMatch.status == 'FINISHED'
    ).all()
    
    test_data = []
    for m in matches:
        actual = m.result  # H/D/A
        
        # 获取球队名称
        home_team = session.query(Team).filter(Team.team_id == m.home_team_id).first()
        away_team = session.query(Team).filter(Team.team_id == m.away_team_id).first()
        
        if home_team and away_team:
            test_data.append({
                'match_id': m.id,
                'home_team_id': m.home_team_id,
                'away_team_id': m.away_team_id,
                'home_team': home_team.name,
                'away_team': away_team.name,
                'home_goals': m.home_score,
                'away_goals': m.away_score,
                'actual_result': actual,
                'season_id': m.season_id
            })
    
    session.close()
    return test_data


def build_team_stats(db: HistoryDBManager, test_matches: List[Dict], test_season_id: int) -> Dict:
    """构建球队统计"""
    session = db.get_session()
    
    team_ids = set()
    for m in test_matches:
        team_ids.add(m['home_team_id'])
        team_ids.add(m['away_team_id'])
    
    stats_map = {}
    
    for team_id in team_ids:
        team = session.query(Team).filter(Team.team_id == team_id).first()
        if not team:
            continue
        
        # 获取历史统计
        history_stats = db.get_team_stats_from_history(team_id)
        
        if not history_stats:
            continue
        
        stats_map[team.name] = TeamStats(
            team_name=team.name,
            home_scored_avg=history_stats.get('home_scored_avg', 1.5),
            home_conceded_avg=history_stats.get('home_conceded_avg', 1.0),
            away_scored_avg=history_stats.get('away_scored_avg', 1.2),
            away_conceded_avg=history_stats.get('away_conceded_avg', 1.3)
        )
    
    session.close()
    
    # 计算特定主客位置的H2H（原始算法专用）
    for m in test_matches:
        home_team = m['home_team']
        away_team = m['away_team']
        home_id = m['home_team_id']
        away_id = m['away_team_id']
        
        h2h_specific = get_specific_h2h(db, home_id, away_id, before_season_id=test_season_id)
        
        if home_team in stats_map and h2h_specific['matches'] > 0:
            stats_map[home_team].h2h_home_scored = h2h_specific['home_scored_avg']
            stats_map[home_team].h2h_matches = h2h_specific['matches']
        
        if away_team in stats_map and h2h_specific['matches'] > 0:
            stats_map[away_team].h2h_away_scored = h2h_specific['away_scored_avg']
    
    return stats_map


def get_specific_h2h(db: HistoryDBManager, home_id: int, away_id: int, before_season_id: int) -> Dict:
    """特定主客位置H2H统计"""
    session = db.get_session()
    
    matches = session.query(HistoricalMatch).filter(
        HistoricalMatch.home_team_id == home_id,
        HistoricalMatch.away_team_id == away_id,
        HistoricalMatch.season_id < before_season_id
    ).all()
    
    if not matches:
        session.close()
        return {'matches': 0, 'home_scored_avg': 0, 'away_scored_avg': 0}
    
    total_home_goals = sum(m.home_score or 0 for m in matches)
    total_away_goals = sum(m.away_score or 0 for m in matches)
    
    session.close()
    
    return {
        'matches': len(matches),
        'home_scored_avg': total_home_goals / len(matches),
        'away_scored_avg': total_away_goals / len(matches)
    }


def run_backtest():
    """运行回测"""
    print("=" * 80)
    print("回测验证：原始Poisson vs 我们的实现")
    print("=" * 80)
    
    db = HistoryDBManager()
    
    # 用2025-2026赛季测试（有2023-2024和2024-2025作为历史）
    test_matches = load_test_matches(db, season_name='2025-2026', league_code='PL')
    
    # 添加其他联赛2025-2026
    for league_code in ['LL', 'BL', 'SA', 'L1']:
        matches = load_test_matches(db, season_name='2025-2026', league_code=league_code)
        if matches:
            test_matches.extend(matches)
    
    if not test_matches:
        print("未找到2023-2024赛季英超比赛")
        return
    
    print(f"\n测试集：{len(test_matches)}场2025-2026赛季比赛")
    
    # 获取赛季ID（2025-2026之前的赛季作为历史）
    session = db.get_session()
    season = session.query(Season).filter(Season.season_code == '2025-2026').first()
    test_season_id = season.season_id if season else 100
    session.close()
    
    # 构建统计
    stats_map = build_team_stats(db, test_matches, test_season_id)
    print(f"球队统计：{len(stats_map)}支球队")
    
    # 初始化预测器
    original_predictor = OriginalPoisson(nsim=10000)
    our_predictor = OurPoisson(nsim=10000)
    
    for team_name, stats in stats_map.items():
        original_predictor.set_stats(team_name, stats)
        our_predictor.set_stats(team_name, stats)
    
    # 预测
    results = {
        'original': {'correct': 0, 'h2h_used': 0, 'h2h_correct': 0},
        'ours': {'correct': 0},
        'comparison': []
    }
    
    print("\n开始预测...")
    
    for m in test_matches:
        home = m['home_team']
        away = m['away_team']
        actual = m['actual_result']
        
        if home not in stats_map or away not in stats_map:
            continue
        
        orig_pred = original_predictor.predict(home, away, h2h_threshold=3)  # 原始阈值
        our_pred = our_predictor.predict(home, away)
        
        if orig_pred.get('prediction') == actual:
            results['original']['correct'] += 1
            if orig_pred['h2h_mode']:
                results['original']['h2h_correct'] += 1
        
        if our_pred.get('prediction') == actual:
            results['ours']['correct'] += 1
        
        if orig_pred['h2h_mode']:
            results['original']['h2h_used'] += 1
        
        if len(results['comparison']) < 15:
            results['comparison'].append({
                'match': f"{home[:20]} vs {away[:20]}",
                'actual': actual,
                'orig_pred': orig_pred.get('prediction'),
                'orig_h2h': orig_pred['h2h_mode'],
                'our_pred': our_pred.get('prediction'),
            })
    
    # 结果
    total = len(test_matches)
    
    print("\n" + "=" * 80)
    print("回测结果")
    print("=" * 80)
    
    orig_acc = results['original']['correct'] / total
    our_acc = results['ours']['correct'] / total
    
    h2h_acc = 0
    if results['original']['h2h_used'] > 0:
        h2h_acc = results['original']['h2h_correct'] / results['original']['h2h_used']
    
    print(f"\n原始算法准确率：{results['original']['correct']}/{total} = {orig_acc:.1%}")
    print(f"  使用H2H模式：{results['original']['h2h_used']}场")
    print(f"  H2H模式准确率：{h2h_acc:.1%} ({results['original']['h2h_correct']}/{results['original']['h2h_used']})")
    
    print(f"\n我们的版本准确率：{results['ours']['correct']}/{total} = {our_acc:.1%}")
    
    print(f"\n准确率差异：{abs(orig_acc - our_acc):.1%}")
    
    if orig_acc > our_acc:
        print(f"结论：原始算法更准确 (+{orig_acc - our_acc:.1%})")
    elif our_acc > orig_acc:
        print(f"结论：我们的版本更准确 (+{our_acc - orig_acc:.1%})")
    else:
        print("结论：两种算法准确率相同")
    
    # 详情
    print("\n" + "-" * 60)
    print("预测对比详情（前15场）")
    print("-" * 60)
    
    for c in results['comparison']:
        h2h_mark = "[H2H]" if c['orig_h2h'] else ""
        orig_ok = "✓" if c['orig_pred'] == c['actual'] else "✗"
        our_ok = "✓" if c['our_pred'] == c['actual'] else "✗"
        
        print(f"{c['match'][:40]:40} 实际:{c['actual']} | 原始:{c['orig_pred']}{orig_ok}{h2h_mark} | 我们:{c['our_pred']}{our_ok}")
    
    return results


if __name__ == '__main__':
    run_backtest()