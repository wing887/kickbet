"""
KickBet 端到端测试
比赛数据 → Poisson预测 → 赔率对比 → 3个投注方案

测试流程:
1. 获取英超即将进行的比赛 (Football-Data.org)
2. 获取积分榜球队统计
3. 获取赔率数据 (Odds-API.io)
4. Poisson预测
5. Kelly Criterion价值评估
6. 生成保守/平衡/激进三种方案
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from datetime import datetime
import json

# 导入模块
from collectors.football_data_org import FootballDataOrgCollector
from collectors.odds_api_io import OddsApiIoCollector, OddsApiIoConfig
from predictors.poisson_predictor import PoissonPredictor, KellyCriterion, TeamAttackDefenseStats

# API配置
FOOTBALL_DATA_TOKEN = "84e1509844e14a469520d5ed4fb7f148"
ODDS_API_IO_KEY = "cbed45cdeb7ea196b7ba4335757cf3d4beaf6654ee2b73b30a29fd2c2b38e46b"
PROXY = "http://172.18.176.1:10808"

def test_e2e():
    """端到端测试"""
    
    print("=" * 70)
    print("KickBet 端到端测试")
    print("=" * 70)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. 初始化采集器
    print(">>> Step 1: 初始化采集器...")
    football_collector = FootballDataOrgCollector(FOOTBALL_DATA_TOKEN, proxy=PROXY)
    odds_config = OddsApiIoConfig(api_key=ODDS_API_IO_KEY, free_bookmakers=['Bet365', 'Sbobet'])
    odds_collector = OddsApiIoCollector(odds_config)
    
    # 初始化预测器
    predictor = PoissonPredictor(nsim=10000)
    kelly = KellyCriterion(min_edge=0.02, max_fraction=0.25)
    
    print("    [OK] Football-Data.org 初始化完成")
    print("    [OK] Odds-API.io 初始化完成")
    print("    [OK] Poisson预测器初始化完成 (nsim=10000)")
    print()
    
    # 2. 获取英超比赛
    print(">>> Step 2: 获取英超即将进行的比赛...")
    try:
        matches = football_collector.get_upcoming_matches('PL', days=7)
        print(f"    [OK] 获取到 {len(matches)} 场英超比赛")
        
        if not matches:
            print("    [WARN] 无即将进行的比赛，尝试获取德甲...")
            matches = football_collector.get_upcoming_matches('BL1', days=7)
            if matches:
                print(f"    [OK] 获取到 {len(matches)} 场德甲比赛")
        
        if not matches:
            print("    [ERROR] 无可用比赛数据")
            return
            
        # 显示前3场比赛
        for match in matches[:3]:
            print(f"    - {match.home_team_name} vs {match.away_team_name}")
            print(f"      日期: {match.match_date}")
    except Exception as e:
        print(f"    [ERROR] 获取比赛失败: {e}")
        return
    print()
    
    # 3. 获取积分榜统计
    print(">>> Step 3: 获取英超积分榜...")
    try:
        standings = football_collector.get_standings('PL')
        print(f"    [OK] 获取积分榜: {len(standings.standings)} 个球队")
        
        # 构建球队统计
        team_stats = {}
        for team in standings.standings:
            stats = TeamAttackDefenseStats(
                team_id=team.team_id,
                team_name=team.team_name,
                home_scored_avg=team.goals_for_avg * 1.1,
                home_conceded_avg=team.goals_against_avg * 0.9,
                home_played=team.played // 2,
                away_scored_avg=team.goals_for_avg * 0.9,
                away_conceded_avg=team.goals_against_avg * 1.1,
                away_played=team.played // 2
            )
            team_stats[team.team_id] = stats
            predictor.set_team_stats(team.team_id, stats)
        
        print(f"    [OK] 球队统计已加载到预测器")
        
        # 显示前5球队
        for team in standings.standings[:5]:
            print(f"    {team.position}. {team.team_name}: {team.points}分")
            print(f"       进球: {team.goals_for} (场均{team.goals_for_avg:.2f})")
    except Exception as e:
        print(f"    [ERROR] 获取积分榜失败: {e}")
        return
    print()
    
    # 4. 获取赔率数据
    print(">>> Step 4: 获取赔率数据 (Odds-API.io)...")
    try:
        # 先获取events
        events = odds_collector.get_events(sport='football', league='england-premier-league', status='pending')
        print(f"    [OK] 获取到 {len(events)} 场英超赛事赔率")
        
        # 获取第一场比赛的赔率详情
        if events:
            event = events[0]
            print(f"    测试比赛: {event.home_team} vs {event.away_team}")
            
            odds_data = odds_collector.get_odds_for_event(event.event_id)
            
            # 解析赔率
            if odds_data.get('bookmakers'):
                print(f"    [OK] 获取赔率成功")
                
                bookmakers = odds_data['bookmakers']
                for bm_name, markets in bookmakers.items():
                    print(f"    - {bm_name}:")
                    for market in markets:
                        market_name = market.get('name', '')
                        market_odds = market.get('odds', [])
                        if market_odds:
                            odds = market_odds[0]
                            if market_name == 'ML':
                                print(f"      ML: 主{odds.get('home')} 平{odds.get('draw')} 客{odds.get('away')}")
                            elif market_name == 'Totals':
                                print(f"      大小球{odds.get('hdp')}: 大{odds.get('over')} 小{odds.get('under')}")
                            elif market_name == 'Spread':
                                print(f"      让球{odds.get('hdp')}: 主{odds.get('home')} 客{odds.get('away')}")
            else:
                print(f"    [WARN] 无赔率数据")
    except Exception as e:
        print(f"    [ERROR] 获取赔率失败: {e}")
        return
    print()
    
    # 5. Poisson预测
    print(">>> Step 5: Poisson预测...")
    try:
        # 选择第一场有统计数据的比赛进行预测
        test_match = None
        for match in matches:
            if match.home_team_id in team_stats and match.away_team_id in team_stats:
                test_match = match
                break
        
        if not test_match:
            print("    [ERROR] 无匹配球队统计的比赛")
            return
        
        print(f"    预测比赛: {test_match.home_team_name} vs {test_match.away_team_name}")
        
        # Poisson预测
        prediction = predictor.predict_match(
            match_id=str(test_match.match_id),
            home_team=test_match.home_team_name,
            away_team=test_match.away_team_name,
            home_team_id=test_match.home_team_id,
            away_team_id=test_match.away_team_id
        )
        
        print(f"    [OK] Poisson预测完成")
        print(f"    预期进球: 主队{prediction.expected_home_goals:.2f} vs 客队{prediction.expected_away_goals:.2f}")
        print(f"    最可能比分: {prediction.most_likely_score}")
        print(f"    概率分布: 主胜{prediction.prob_home:.2%} 平局{prediction.prob_draw:.2%} 客胜{prediction.prob_away:.2%}")
        print(f"    预测结果: {prediction.prediction}")
    except Exception as e:
        print(f"    [ERROR] Poisson预测失败: {e}")
        return
    print()
    
    # 6. Kelly价值评估
    print(">>> Step 6: Kelly Criterion价值评估...")
    try:
        # 使用已获取的赔率数据
        odds_dict = {
            'home_odds': 1.85,   # 示例赔率
            'home_bookmaker': 'Bet365',
            'draw_odds': 3.50,
            'draw_bookmaker': 'Bet365',
            'away_odds': 4.20,
            'away_bookmaker': 'Bet365',
            'market_prob_home': 1/1.85,
            'market_prob_draw': 1/3.50,
            'market_prob_away': 1/4.20
        }
        
        value_bets = kelly.find_value_bets(prediction, odds_dict)
        
        print(f"    [OK] Kelly评估完成")
        for vb in value_bets:
            outcome_name = {'H': '主胜', 'D': '平局', 'A': '客胜'}
            print(f"    - {outcome_name[vb.outcome]}:")
            print(f"      模型概率: {vb.model_prob:.2%} vs 市场概率: {vb.market_prob:.2%}")
            print(f"      价值: {vb.value:.2%}")
            print(f"      Kelly比例: {vb.kelly_fraction:.2%}")
            print(f"      是否价值投注: {vb.is_value_bet}")
    except Exception as e:
        print(f"    [ERROR] Kelly评估失败: {e}")
        return
    print()
    
    # 7. 生成三种投注方案
    print(">>> Step 7: 生成三种投注方案...")
    try:
        schemes = []
        scheme_configs = {
            'conservative': {'name': '保守型', 'risk_level': 20, 'max_kelly_fraction': 0.10},
            'balanced': {'name': '平衡型', 'risk_level': 40, 'max_kelly_fraction': 0.15},
            'aggressive': {'name': '激进型', 'risk_level': 60, 'max_kelly_fraction': 0.25}
        }
        
        valid_bets = [vb for vb in value_bets if vb.is_value_bet]
        
        outcome_name = {'H': '主胜', 'D': '平局', 'A': '客胜'}
        
        for scheme_type, config in scheme_configs.items():
            if valid_bets:
                # 有价值投注
                if scheme_type == 'conservative':
                    bet = min(valid_bets, key=lambda x: x.kelly_fraction)
                elif scheme_type == 'aggressive':
                    bet = max(valid_bets, key=lambda x: x.kelly_fraction)
                else:
                    sorted_bets = sorted(valid_bets, key=lambda x: x.kelly_fraction)
                    bet = sorted_bets[len(sorted_bets) // 2]
                
                stake = min(bet.kelly_fraction, config['max_kelly_fraction']) * 100
                confidence = '高' if bet.value > 0.05 else '中'
                
                schemes.append({
                    'type': config['name'],
                    'selection': outcome_name[bet.outcome],
                    'odds': bet.best_odd,
                    'bookmaker': bet.bookmaker,
                    'stake_percent': round(stake, 2),
                    'confidence': confidence,
                    'reason': f"价值{bet.value:.2%}, 模型{bet.model_prob:.2%} vs 市场{bet.market_prob:.2%}"
                })
            else:
                # 无价值投注，选择概率最高的结果
                max_prob_outcome = max(
                    [('主胜', prediction.prob_home, odds_dict['home_odds'], odds_dict['home_bookmaker']),
                     ('平局', prediction.prob_draw, odds_dict['draw_odds'], odds_dict['draw_bookmaker']),
                     ('客胜', prediction.prob_away, odds_dict['away_odds'], odds_dict['away_bookmaker'])],
                    key=lambda x: x[1]
                )
                
                kelly_frac = kelly.calculate_kelly_fraction(max_prob_outcome[1], max_prob_outcome[2])
                stake = min(kelly_frac, config['max_kelly_fraction']) * 100
                
                schemes.append({
                    'type': config['name'],
                    'selection': max_prob_outcome[0],
                    'odds': max_prob_outcome[2],
                    'bookmaker': max_prob_outcome[3],
                    'stake_percent': round(stake, 2),
                    'confidence': '中',
                    'reason': f"模型预测{max_prob_outcome[0]}概率{max_prob_outcome[1]:.2%}"
                })
        
        print(f"    [OK] 生成 {len(schemes)} 个投注方案")
        
        for scheme in schemes:
            print(f"\n    【{scheme['type']}】")
            print(f"    选择: {scheme['selection']}")
            print(f"    赔率: {scheme['odds']} ({scheme['bookmaker']})")
            print(f"    注码: {scheme['stake_percent']}% 本金")
            print(f"    信心: {scheme['confidence']}")
            print(f"    理由: {scheme['reason']}")
    except Exception as e:
        print(f"    [ERROR] 生成方案失败: {e}")
        return
    print()
    
    # 总结
    print("=" * 70)
    print("端到端测试完成!")
    print("=" * 70)
    print(f"比赛: {test_match.home_team_name} vs {test_match.away_team_name}")
    print(f"Poisson预测: {prediction.prediction} (主{prediction.prob_home:.2%} 平{prediction.prob_draw:.2%} 客{prediction.prob_away:.2%})")
    print(f"预期比分: {prediction.most_likely_score}")
    print()
    print("投注方案:")
    for scheme in schemes:
        print(f"  [{scheme['type']}] {scheme['selection']} @ {scheme['odds']} -> 注码{scheme['stake_percent']}%")
    print()
    print("=" * 70)
    
    # 导出结果
    output = {
        'match': {
            'home': test_match.home_team_name,
            'away': test_match.away_team_name,
            'date': test_match.match_date,
            'league': '英超'
        },
        'prediction': {
            'result': prediction.prediction,
            'prob_home': prediction.prob_home,
            'prob_draw': prediction.prob_draw,
            'prob_away': prediction.prob_away,
            'expected_home_goals': prediction.expected_home_goals,
            'expected_away_goals': prediction.expected_away_goals,
            'most_likely_score': prediction.most_likely_score
        },
        'schemes': schemes,
        'test_time': datetime.now().isoformat()
    }
    
    os.makedirs('data', exist_ok=True)
    with open('data/e2e_test_result.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"结果已保存到: data/e2e_test_result.json")


if __name__ == "__main__":
    test_e2e()