"""
测试数据采集器 - Odds-API.io 和 Football-Data.org
"""
import sys
sys.path.insert(0, '/mnt/c/Users/admin/Desktop/KickBet项目文档/kickbet-core')

import requests
import json

# API配置
ODDS_API_KEY = "cbed45cdeb7ea196b7ba4335757cf3d4beaf6654ee2b73b30a29fd2c2b38e46b"
FOOTBALL_DATA_TOKEN = "84e1509844e14a469520d5ed4fb7f148"

# WSL代理
PROXY = "http://172.18.176.1:10808"

def test_odds_api():
    print("=" * 50)
    print("Odds-API.io 测试")
    print("=" * 50)
    
    # 测试英超赔率
    url = "https://api.odds-api.io/v3/events"
    params = {
        "api_key": ODDS_API_KEY,
        "sport": "soccer",
        "league_slug": "england-premier-league",
        "bookmakers": "Bet365"
    }
    
    proxies = {"http": PROXY, "https": PROXY}
    
    try:
        print(f"\n请求URL: {url}")
        print(f"参数: league_slug=england-premier-league, bookmakers=Bet365")
        
        response = requests.get(url, params=params, proxies=proxies, timeout=30)
        
        print(f"\n响应状态: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if 'data' in data and len(data['data']) > 0:
                events = data['data']
                print(f"\n获取到 {len(events)} 场比赛")
                
                # 显示第一场比赛
                first_event = events[0]
                print(f"\n第一场比赛:")
                print(f"  主队: {first_event.get('home_team', 'N/A')}")
                print(f"  客队: {first_event.get('away_team', 'N/A')}")
                print(f"  时间: {first_event.get('date', 'N/A')}")
                
                # 获取赔率
                if 'markets' in first_event:
                    markets = first_event['markets']
                    print(f"\n赔率市场数: {len(markets)}")
                    
                    # 找ML市场
                    for m in markets:
                        if m.get('market_name') == 'ML':
                            odds = m.get('odds', [])
                            print(f"\nML赔率:")
                            for o in odds[:3]:
                                print(f"  {o.get('outcome')}: {o.get('odd')} ({o.get('bookmaker')})")
                
                return True
            else:
                print(f"\nAPI响应: {json.dumps(data, indent=2)[:500]}")
                return False
        else:
            print(f"\n错误响应: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"\n请求失败: {e}")
        return False


def test_football_data():
    print("\n" + "=" * 50)
    print("Football-Data.org 测试")
    print("=" * 50)
    
    # 测试英超积分榜
    url = "https://api.football-data.org/v4/competitions/PL/standings"
    headers = {"X-Auth-Token": FOOTBALL_DATA_TOKEN}
    
    proxies = {"http": PROXY, "https": PROXY}
    
    try:
        print(f"\n请求URL: {url}")
        print(f"参数: competitions=PL (英超)")
        
        response = requests.get(url, headers=headers, proxies=proxies, timeout=30)
        
        print(f"\n响应状态: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if 'standings' in data:
                standings = data['standings'][0]['table']
                print(f"\n获取到 {len(standings)} 个球队积分榜")
                
                # 显示前5个球队
                print(f"\n积分榜前5:")
                for team in standings[:5]:
                    print(f"  {team['position']}. {team['team']['name']} - {team['points']}分 ({team['won']}胜/{team['draw']}平/{team['lost']}负)")
                
                return True
            else:
                print(f"\nAPI响应: {json.dumps(data, indent=2)[:500]}")
                return False
        else:
            print(f"\n错误响应: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"\n请求失败: {e}")
        return False


def main():
    print("KickBet 数据采集器测试")
    print("=" * 50)
    
    odds_ok = test_odds_api()
    football_ok = test_football_data()
    
    print("\n" + "=" * 50)
    print("测试结果汇总")
    print("=" * 50)
    
    print(f"\nOdds-API.io: {'OK' if odds_ok else 'FAIL'}")
    print(f"Football-Data.org: {'OK' if football_ok else 'FAIL'}")
    
    if odds_ok and football_ok:
        print("\n所有数据源可用!")
        return True
    else:
        print("\n部分数据源不可用，需要检查API Key或代理配置")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)