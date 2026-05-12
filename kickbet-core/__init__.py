"""
KickBet Core - 核心预测引擎
五大联赛数据采集 → Poisson预测 → Kelly Criterion → 三方案输出

使用:
    from kickbet_core.services import KickBetCore
    
    core = KickBetCore()
    analyses = core.run_daily_analysis(days=3)
"""

__version__ = "1.0.0"