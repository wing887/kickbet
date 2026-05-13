"""
队名映射配置文件
用于校准 Football-Data.org 和 Odds-API.io 的队名差异

格式:
TEAM_NAME_MAPPING = {
    'Football-Data.org名称': 'Odds-API.io名称',
}

TEAM_CHINESE_NAMES = {
    'Football-Data.org名称': '中文名称',
}
"""

# ============================================
# Football-Data.org → Odds-API.io 映射
# ============================================

TEAM_NAME_MAPPING = {
    # 英超
    'Arsenal FC': 'Arsenal FC',
    'Aston Villa FC': 'Aston Villa',
    'Brentford FC': 'Brentford FC',
    'Brighton & Hove Albion FC': 'Brighton & Hove Albion',
    'Burnley FC': 'Burnley',
    'Chelsea FC': 'Chelsea',
    'Crystal Palace FC': 'Crystal Palace',
    'Everton FC': 'Everton',
    'Fulham FC': 'Fulham',
    'Leeds United FC': 'Leeds United',
    'Liverpool FC': 'Liverpool',
    'Manchester City FC': 'Manchester City',
    'Manchester United FC': 'Manchester United',
    'Newcastle United FC': 'Newcastle United',
    'Nottingham Forest FC': 'Nottingham Forest',
    'Sunderland AFC': 'Sunderland',
    'Tottenham Hotspur FC': 'Tottenham Hotspur',
    'West Ham United FC': 'West Ham United',
    'Wolverhampton Wanderers FC': 'Wolverhampton Wanderers',
    'AFC Bournemouth': 'Bournemouth',
    
    # 德甲
    '1. FC Heidenheim 1846': '1. FC Heidenheim',
    '1. FC Köln': '1. FC Cologne',
    '1. FC Union Berlin': 'Union Berlin',
    '1. FSV Mainz 05': 'FSV Mainz',
    'Bayer 04 Leverkusen': 'Bayer Leverkusen',
    'Borussia Dortmund': 'Borussia Dortmund',
    'Borussia Mönchengladbach': 'Borussia Monchengladbach',
    'Eintracht Frankfurt': 'Eintracht Frankfurt',
    'FC Augsburg': 'FC Augsburg',
    'FC Bayern München': 'Bayern Munich',
    'FC St. Pauli': 'FC St. Pauli',
    'Hamburger SV': 'Hamburger SV',
    'RB Leipzig': 'RB Leipzig',
    'SC Freiburg': 'SC Freiburg',
    'SV Werder Bremen': 'Werder Bremen',
    'TSG 1899 Hoffenheim': 'TSG Hoffenheim',
    'VfB Stuttgart': 'VfB Stuttgart',
    'VfL Wolfsburg': 'VfL Wolfsburg',
    
    # 西甲 (手动映射，Odds-API.io当前无数据)
    'Athletic Club': 'Athletic Bilbao',
    'Atlético Madrid': 'Atletico Madrid',
    'CA Osasuna': 'Osasuna',
    'Club Atlético de Madrid': 'Atletico Madrid',
    'Deportivo Alavés': 'Alaves',
    'FC Barcelona': 'Barcelona',
    'Getafe CF': 'Getafe',
    'Girona FC': 'Girona',
    'Granada CF': 'Granada',
    'RC Celta de Vigo': 'Celta Vigo',
    'RCD Espanyol de Barcelona': 'Espanyol',
    'RCD Mallorca': 'Mallorca',
    'Rayo Vallecano': 'Rayo Vallecano',
    'Real Betis Balompié': 'Real Betis',
    'Real Madrid CF': 'Real Madrid',
    'Real Oviedo': 'Oviedo',
    'Real Sociedad de Fútbol': 'Real Sociedad',
    'Real Valladolid CF': 'Valladolid',
    'Sevilla FC': 'Sevilla',
    'UD Las Palmas': 'Las Palmas',
    'Valencia CF': 'Valencia',
    'Villarreal CF': 'Villarreal',
    
    # 意甲
    'AC Milan': 'AC Milan',
    'ACF Fiorentina': 'ACF Fiorentina',
    'AS Roma': 'AS Roma',
    'Atalanta BC': 'Atalanta BC',
    'Bologna FC 1909': 'Bologna FC',
    'Cagliari Calcio': 'Cagliari Calcio',
    'Como 1907': 'Como 1907',
    'Genoa CFC': 'Genoa CFC',
    'Hellas Verona FC': 'Hellas Verona',
    'Inter Milano': 'Inter Milan',
    'Juventus FC': 'Juventus Turin',
    'Lazio Rome': 'Lazio',
    'Parma Calcio 1913': 'Parma Calcio',
    'Pisa SC': 'Pisa SC',
    'SSC Napoli': 'SSC Napoli',
    'Sassuolo Calcio': 'Sassuolo Calcio',
    'Torino FC': 'Torino FC',
    'US Cremonese': 'US Cremonese',
    'US Lecce': 'US Lecce',
    'Udinese Calcio': 'Udinese Calcio',
    
    # 法甲
    'AJ Auxerre': 'AJ Auxerre',
    'AS Monaco FC': 'AS Monaco',
    'AS Saint-Étienne': 'AS Saint-Etienne',
    'Angers SCO': 'Angers SCO',
    'FC Lorient': 'FC Lorient',
    'FC Metz': 'FC Metz',
    'FC Nantes': 'FC Nantes',
    'Le Havre AC': 'Le Havre AC',
    'Lille OSC': 'Lille OSC',
    'OGC Nice': 'OGC Nice',
    'Paris FC': 'Paris FC',
    'Paris Saint-Germain FC': 'Paris Saint-Germain',
    'Toulouse FC': 'Toulouse',
    'Olympique Lyonnais': 'Olympique Lyon',
    'Olympique de Marseille': 'Olympique Marseille',
    'RC Strasbourg Alsace': 'Strasbourg Alsace',
    'Racing Club de Lens': 'Racing Club de Lens',
    'Stade Brestois 29': 'Stade Brest 29',
    'Stade Rennais FC 1901': 'Stade Rennais',
    
    # 欧冠
    'AC Sparta Praha': 'Sparta Prague',
    'BSC Young Boys': 'Young Boys',
    'FK Crvena Zvezda': 'Red Star Belgrade',
    'GNK Dinamo Zagreb': 'Dinamo Zagreb',
    'FK Partizan': 'Partizan Belgrade',
    'FC Porto': 'FC Porto',
    'SL Benfica': 'Benfica',
    'Sporting CP': 'Sporting Lisbon',
    'FK Shakhtar Donetsk': 'Shakhtar Donetsk',
    'FC Salzburg': 'Red Bull Salzburg',
}

# ============================================
# 中文名称映射
# ============================================

TEAM_CHINESE_NAMES = {
    # 英超
    'Arsenal FC': '阿森纳',
    'Aston Villa FC': '阿斯顿维拉',
    'Brentford FC': '布伦特福德',
    'Brighton & Hove Albion FC': '布莱顿',
    'Burnley FC': '伯恩利',
    'Chelsea FC': '切尔西',
    'Crystal Palace FC': '水晶宫',
    'Everton FC': '埃弗顿',
    'Fulham FC': '富勒姆',
    'Leeds United FC': '利兹联',
    'Liverpool FC': '利物浦',
    'Manchester City FC': '曼城',
    'Manchester United FC': '曼联',
    'Newcastle United FC': '纽卡斯尔',
    'Nottingham Forest FC': '诺丁汉森林',
    'Sunderland AFC': '桑德兰',
    'Tottenham Hotspur FC': '热刺',
    'West Ham United FC': '西汉姆',
    'Wolverhampton Wanderers FC': '狼队',
    'AFC Bournemouth': '伯恩茅斯',
    
    # 德甲
    '1. FC Heidenheim 1846': '海登海姆',
    '1. FC Köln': '科隆',
    '1. FC Union Berlin': '柏林联合',
    '1. FSV Mainz 05': '美因茨',
    'Bayer 04 Leverkusen': '勒沃库森',
    'Borussia Dortmund': '多特蒙德',
    'Borussia Mönchengladbach': '门兴',
    'Eintracht Frankfurt': '法兰克福',
    'FC Augsburg': '奥格斯堡',
    'FC Bayern München': '拜仁',
    'FC St. Pauli': '圣保利',
    'Hamburger SV': '汉堡',
    'RB Leipzig': '莱比锡红牛',
    'SC Freiburg': '弗赖堡',
    'SV Werder Bremen': '不来梅',
    'TSG 1899 Hoffenheim': '霍芬海姆',
    'VfB Stuttgart': '斯图加特',
    'VfL Wolfsburg': '沃尔夫斯堡',
    
    # 西甲
    'Athletic Club': '毕尔巴鄂',
    'Atlético Madrid': '马竞',
    'CA Osasuna': '奥萨苏纳',
    'Deportivo Alavés': '阿拉维斯',
    'FC Barcelona': '巴萨',
    'Getafe CF': '赫塔费',
    'Girona FC': '吉罗纳',
    'Granada CF': '格拉纳达',
    'RC Celta de Vigo': '塞尔塔',
    'RCD Espanyol de Barcelona': '西班牙人',
    'RCD Mallorca': '马洛卡',
    'Rayo Vallecano': '巴列卡诺',
    'Real Betis Balompié': '贝蒂斯',
    'Real Madrid CF': '皇马',
    'Real Oviedo': '奥维耶多',
    'Real Sociedad de Fútbol': '皇家社会',
    'Real Valladolid CF': '巴利亚多利德',
    'Sevilla FC': '塞维利亚',
    'UD Las Palmas': '拉斯帕尔马斯',
    'Valencia CF': '巴伦西亚',
    'Villarreal CF': '比利亚雷亚尔',
    
    # 意甲
    'AC Milan': 'AC米兰',
    'ACF Fiorentina': '佛罗伦萨',
    'AS Roma': '罗马',
    'Atalanta BC': '亚特兰大',
    'Bologna FC 1909': '博洛尼亚',
    'Cagliari Calcio': '卡利亚里',
    'Como 1907': '科莫',
    'Genoa CFC': '热那亚',
    'Hellas Verona FC': '维罗纳',
    'Inter Milano': '国际米兰',
    'Juventus FC': '尤文图斯',
    'Lazio Rome': '拉齐奥',
    'Parma Calcio 1913': '帕尔马',
    'Pisa SC': '比萨',
    'SSC Napoli': '那不勒斯',
    'Sassuolo Calcio': '萨索洛',
    'Torino FC': '都灵',
    'US Cremonese': '克雷莫纳',
    'US Lecce': '莱切',
    'Udinese Calcio': '乌迪内斯',
    
    # 法甲
    'AJ Auxerre': '欧塞尔',
    'AS Monaco FC': '摩纳哥',
    'AS Saint-Étienne': '圣埃蒂安',
    'Angers SCO': '昂热',
    'FC Lorient': '洛里昂',
    'FC Metz': '梅斯',
    'FC Nantes': '南特',
    'Le Havre AC': '勒阿弗尔',
    'Lille OSC': '里尔',
    'OGC Nice': '尼斯',
    'Paris FC': '巴黎FC',
    'Paris Saint-Germain FC': '巴黎圣日耳曼',
    'Toulouse FC': '图卢兹',
    'Olympique Lyonnais': '里昂',
    'Olympique de Marseille': '马赛',
    'RC Strasbourg Alsace': '斯特拉斯堡',
    'Racing Club de Lens': '朗斯',
    'Stade Brestois 29': '布雷斯特',
    'Stade Rennais FC 1901': '雷恩',
    
    # 欧冠
    'AC Sparta Praha': '布拉格斯拉维亚',
    'BSC Young Boys': '年轻人',
    'FK Crvena Zvezda': '贝尔格莱德红星',
    'GNK Dinamo Zagreb': '萨格勒布迪纳摩',
    'FK Partizan': '贝尔格莱德游击',
    'FC Porto': '波尔图',
    'SL Benfica': '本菲卡',
    'Sporting CP': '葡萄牙体育',
    'FK Shakhtar Donetsk': '顿涅茨克矿工',
    'FC Salzburg': '萨尔茨堡红牛',
}

# ============================================
# 反向映射 (Odds-API.io → Football-Data.org)
# ============================================

TEAM_NAME_MAPPING_REVERSE = {
    v: k for k, v in TEAM_NAME_MAPPING.items()
}

# ============================================
# 队名标准化函数
# ============================================

def normalize_team_name(name: str, target_api: str = 'odds_api') -> str:
    """
    标准化队名
    
    Args:
        name: 原始队名
        target_api: 目标API ('odds_api' 或 'football_data')
    
    Returns:
        标准化后的队名
    """
    if target_api == 'odds_api':
        # Football-Data.org → Odds-API.io
        return TEAM_NAME_MAPPING.get(name, name)
    else:
        # Odds-API.io → Football-Data.org
        return TEAM_NAME_MAPPING_REVERSE.get(name, name)

def get_chinese_name(name: str) -> str:
    """
    获取队名的中文翻译
    
    Args:
        name: 队名 (支持Football-Data.org或Odds-API.io格式)
    
    Returns:
        中文名称
    """
    # 先尝试直接匹配
    if name in TEAM_CHINESE_NAMES:
        return TEAM_CHINESE_NAMES[name]
    
    # 尝试反向查找
    fd_name = TEAM_NAME_MAPPING_REVERSE.get(name, name)
    return TEAM_CHINESE_NAMES.get(fd_name, name)


# ============================================
# 联赛中文名称
# ============================================

LEAGUE_CHINESE_NAMES = {
    'PL': '英超',
    'BL1': '德甲',
    'PD': '西甲',
    'SA': '意甲',
    'FL1': '法甲',
    'CL': '欧冠',
    'EL': '欧联杯',
    'UECL': '欧会杯',
}

LEAGUE_SLUG_MAPPING = {
    'PL': 'england-premier-league',
    'BL1': 'germany-bundesliga',
    'PD': 'spain-la-liga',
    'SA': 'italy-serie-a',
    'FL1': 'france-ligue-1',
    'CL': 'europe-uefa-champions-league',
}