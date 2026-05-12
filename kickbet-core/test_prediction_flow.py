"""
测试数据采集和预测模块的实际效果
"""
import sys
import os
import json
import time

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from collectors.football_data_org import FootballDataOrgCollector
from collectors.odds_api_io import OddsApiIoCollector, OddsApiIoConfig
from predictors.poisson_predictor import PoissonPredictor, TeamAttackDefenseStats, KellyCriterion

# 代理配置
PROXY = "http://172.18.176.1:10808"

print("=" * 60)
print("KickBet 数据采集和预测模块测试")
print("=" * 60)

# 1. 测试 Football-Data.org 数据采集
print("\n【1. Football-Data.org 比赛数据采集】")
try:
    fd_collector = FootballDataOrgCollector(
        api_token="84e1509844e14a469520d5ed4fb7f148",
        proxy=PROXY
    )
    
    # 获取英超比赛
    matches = fd_collector.get_upcoming_matches('PL', days=7)
    print(f"获取到 {len(matches)} 场英超比赛")
    
    if matches:
        match = matches[0]
        print(f"示例比赛: {match.home_team_name} vs {match.away_team_name}")
        print(f"  match_id: {match.match_id}")
        print(f"  时间: {match.match_date}")
    
    # 获取积分榜（用于预测）
    standings = fd_collector.get_standings('PL')
    print(f"\n英超积分榜: {standings.season} 赛季")
    for team in standings.standings[:5]:
        print(f"  #{team.position} {team.team_name}: {team.points}分, 进{team.goals_for}失{team.goals_against}")
        
except Exception as e:
    print(f"Football-Data.org 测试失败: {e}")
    matches = []
    standings = None

# 2. 测试 Odds-API.io 赔率采集
print("\n【2. Odds-API.io 赔率数据采集】")
try:
    odds_config = OddsApiIoConfig(
        api_key="cbed45cdeb7ea196b7ba4335757cf3d4beaf6654ee2b73b30a29fd2c2b38e46b"
    )
    odds_collector = OddsApiIoCollector(odds_config)
    
    # 设置代理
    import requests
    original_session = requests.Session
    class ProxiedSession(requests.Session):
        def request(self, method, url, **kwargs):
            kwargs.setdefault('proxies', {'http': PROXY, 'https': PROXY})
            return super().request(method, url, **kwargs)
    requests.Session = ProxiedSession
    
    # 获取英超赔率
    odds_list = odds_collector.get_league_events_with_odds('PL')
    print(f"获取到 {len(odds_list)} 场比赛赔率")
    
    if odds_list:
        odds = odds_list[0]
        print(f"示例: {odds.home_team} vs {odds.away_team}")
        print(f"  ML赔率: 主{odds.home_odds} 平{odds.draw_odds} 客{odds.away_odds}")
        print(f"  来源: {odds.home_bookmaker}")
        if odds.spread_hdp:
            print(f"  让球盘: {odds.spread_hdp} -> 主{odds.spread_home_odds} 客{odds.spread_away_odds}")
        if odds.totals_hdp:
            print(f"  大小球: {odds.totals_hdp} -> 大{odds.totals_over_odds} 小{odds.totals_under_odds}")
    
    print(f"剩余API配额: {odds_collector.rate_limit_remaining}")
    
except Exception as e:
    print(f"Odds-API.io 测试失败: {e}")
    odds_list = []

# 3. 测试 Poisson 预测模型
print("\n【3. Poisson 预测模型】")
try:
    predictor = PoissonPredictor(nsim=10000)
    
    # 从积分榜加载球队统计
    if hasattr(standings, 'standings'):
        team_stats_data = []
        for team in standings.standings:
            # 计算主客场平均进球/失球
            home_played = team.played // 2
            away_played = team.played - home_played
            
            # 使用总场均数据估算
            avg_gf = team.goals_for_avg
            avg_ga = team.goals_against_avg
            
            # 主场进攻更强，客场防守更弱（经验值）
            home_scored = avg_gf * 1.2
            home_conceded = avg_ga * 0.9
            away_scored = avg_gf * 0.9
            away_conceded = avg_ga * 1.1
            
            team_stats_data.append({
                'team_id': team.team_id,
                'team_name': team.team_name,
                'home_scored_avg': home_scored,
                'home_conceded_avg': home_conceded,
                'home_played': home_played,
                'away_scored_avg': away_scored,
                'away_conceded_avg': away_conceded,
                'away_played': away_played
            })
        
        predictor.load_stats_from_standings(team_stats_data)
        print(f"加载了 {len(team_stats_data)} 个球队的统计数据")
    
    # 预测一场比赛
    if matches:
        match = matches[0]
        pred = predictor.predict_match(
            match_id=str(match.match_id),
            home_team=match.home_team_name,
            away_team=match.away_team_name,
            home_team_id=match.home_team_id,
            away_team_id=match.away_team_id
        )
        
        print(f"\n预测: {pred.home_team} vs {pred.away_team}")
        print(f"  主胜概率: {pred.prob_home:.1%}")
        print(f"  平局概率: {pred.prob_draw:.1%}")
        print(f"  客胜概率: {pred.prob_away:.1%}")
        print(f"  预测结果: {pred.prediction}")
        print(f"  预期进球: 主{pred.expected_home_goals} 客{pred.expected_away_goals}")
        print(f"  最可能比分: {pred.most_likely_score}")
        
        # 大小球预测
        if pred.totals_prediction:
            tp = pred.totals_prediction
            print(f"\n大小球预测:")
            print(f"  预期总进球: {tp.total_goals}")
            print(f"  大2.5: {tp.prob_over_2_5:.1%} | 小2.5: {tp.prob_under_2_5:.1%}")
        
        # 让球盘预测
        if pred.handicap_prediction:
            hp = pred.handicap_prediction
            print(f"\n让球盘预测 (-0.5):")
            print(f"  主赢盘: {hp.prob_home_cover:.1%} | 客赢盘: {hp.prob_away_cover:.1%}")
        
        # Kelly 价值分析
        if odds_list:
            print(f"\n【4. Kelly Criterion 价值分析】")
            kelly = KellyCriterion(min_edge=0.02)
            
            # 匹配赔率
            match_odds = None
            for odds in odds_list:
                if odds.home_team in match.home_team_name or match.home_team_name in odds.home_team:
                    match_odds = odds
                    break
            
            if match_odds:
                best_odds = {
                    'home_odds': match_odds.home_odds,
                    'home_bookmaker': match_odds.home_bookmaker,
                    'draw_odds': match_odds.draw_odds,
                    'draw_bookmaker': match_odds.draw_bookmaker,
                    'away_odds': match_odds.away_odds,
                    'away_bookmaker': match_odds.away_bookmaker,
                    'market_prob_home': match_odds.market_prob_home,
                    'market_prob_draw': match_odds.market_prob_draw,
                    'market_prob_away': match_odds.market_prob_away
                }
                
                value_bets = kelly.find_value_bets(pred, best_odds)
                
                print(f"\n赔率来源: {match_odds.home_bookmaker}")
                for vb in value_bets:
                    outcome_name = {'H': '主胜', 'D': '平局', 'A': '客胜'}[vb.outcome]
                    print(f"\n{outcome_name}:")
                    print(f"  模型概率: {vb.model_prob:.1%} | 市场概率: {vb.market_prob:.1%}")
                    print(f"  价值: {vb.value:.1%} (模型 - 市场)")
                    print(f"  Kelly比例: {vb.kelly_fraction:.1%}")
                    print(f"  最优赔率: {vb.best_odd}")
                    print(f"  是否价值投注: {'YES' if vb.is_value_bet else 'NO'}")
            else:
                print("未找到匹配的赔率数据")
        
        # 保存预测结果到文件
        result = {
            'match': {
                'match_id': pred.match_id,
                'home_team': pred.home_team,
                'away_team': pred.away_team
            },
            'prediction': {
                'prob_home': pred.prob_home,
                'prob_draw': pred.prob_draw,
                'prob_away': pred.prob_away,
                'result': pred.prediction,
                'expected_home_goals': pred.expected_home_goals,
                'expected_away_goals': pred.expected_away_goals,
                'most_likely_score': pred.most_likely_score
            },
            'totals': {
                'total_goals': pred.totals_prediction.total_goals if pred.totals_prediction else None,
                'prob_over_2_5': pred.totals_prediction.prob_over_2_5 if pred.totals_prediction else None,
                'prob_under_2_5': pred.totals_prediction.prob_under_2_5 if pred.totals_prediction else None
            },
            'handicap': {
                'prob_home_cover': pred.handicap_prediction.prob_home_cover if pred.handicap_prediction else None,
                'prob_away_cover': pred.handicap_prediction.prob_away_cover if pred.handicap_prediction else None
            },
            'score_distribution': pred.score_distribution
        }
        
        output_file = os.path.join(os.path.dirname(__file__), 'data', 'test_prediction_result.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n预测结果已保存到: {output_file}")

except Exception as e:
    print(f"Poisson预测测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)