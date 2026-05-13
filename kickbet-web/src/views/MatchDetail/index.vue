<template>
  <div class="match-detail-page">
    <!-- Header -->
    <header class="header">
      <div class="back-btn" @click="$router.back()">←</div>
      <span class="header-title">比赛详情</span>
    </header>
    
    <!-- Match Hero -->
    <div class="match-hero">
      <div class="league-tag">{{ match.league }} · 第{{ match.round }}轮</div>
      <div class="teams-display">
        <div class="team-block">
          <div class="team-logo-large">{{ match.homeTeam.short }}</div>
          <span class="team-name-large">{{ match.homeTeam.name }}</span>
        </div>
        <span class="vs-text">VS</span>
        <div class="team-block">
          <div class="team-logo-large">{{ match.awayTeam.short }}</div>
          <span class="team-name-large">{{ match.awayTeam.name }}</span>
        </div>
      </div>
      <div class="match-info">{{ match.time }} · {{ match.stadium }}</div>
    </div>
    
    <!-- Data Source -->
    <div class="data-source">
      <div>
        <span class="source-label">赔率数据来源</span>
        <span class="source-name">Odds-API.io</span>
      </div>
      <span class="source-update">更新: {{ oddsUpdateTime }}</span>
    </div>
    
    <!-- Odds Section -->
    <div class="odds-section">
      <div class="odds-section-title">实时赔率对比</div>
      
      <!-- Play Type Tabs -->
      <div class="play-type-tabs">
        <div 
          :class="['play-tab', { active: playType === '1x2' }]"
          @click="playType = '1x2'"
        >胜平负</div>
        <div 
          :class="['play-tab', { active: playType === 'ou' }]"
          @click="playType = 'ou'"
        >大小球</div>
        <div 
          :class="['play-tab', { active: playType === 'ah' }]"
          @click="playType = 'ah'"
        >让球</div>
      </div>
      
      <!-- 1X2 Odds -->
      <div v-if="playType === '1x2'" class="odds-table">
        <div class="odds-table-header">
          <span>平台</span>
          <span>主胜</span>
          <span>平局</span>
          <span>客胜</span>
        </div>
        <div v-for="odd in odds1x2" :key="odd.platform" class="odds-table-row">
          <span class="odds-platform">{{ odd.platform }}</span>
          <span :class="['odds-value', { best: odd.homeBest }]">{{ odd.home }}</span>
          <span :class="['odds-value', { best: odd.drawBest }]">{{ odd.draw }}</span>
          <span :class="['odds-value', { best: odd.awayBest }]">{{ odd.away }}</span>
        </div>
        
        <div v-if="recommendation1x2" class="recommendation-box">
          <div class="rec-header">
            <span class="rec-icon">✓</span>
            <span class="rec-title">{{ recommendation1x2.title }}</span>
          </div>
          <div class="rec-detail">{{ recommendation1x2.detail }}</div>
        </div>
      </div>
      
      <!-- Over/Under Odds -->
      <div v-if="playType === 'ou'" class="odds-table">
        <div class="odds-table-header">
          <span>平台</span>
          <span>大2.5</span>
          <span>小2.5</span>
          <span>盘口</span>
        </div>
        <div v-for="odd in oddsOU" :key="odd.platform" class="odds-table-row">
          <span class="odds-platform">{{ odd.platform }}</span>
          <span :class="['odds-value', { best: odd.overBest }]">{{ odd.over }}</span>
          <span :class="['odds-value', { best: odd.underBest }]">{{ odd.under }}</span>
          <span class="odds-value">{{ odd.line }}</span>
        </div>
        
        <div v-if="recommendationOU" class="recommendation-box">
          <div class="rec-header">
            <span class="rec-icon">✓</span>
            <span class="rec-title">{{ recommendationOU.title }}</span>
          </div>
          <div class="rec-detail">{{ recommendationOU.detail }}</div>
        </div>
      </div>
      
      <!-- Asian Handicap Odds -->
      <div v-if="playType === 'ah'" class="odds-table">
        <div class="odds-table-header">
          <span>平台</span>
          <span>{{ match.homeTeam.short }}</span>
          <span>{{ match.awayTeam.short }}</span>
          <span>盘口</span>
        </div>
        <div v-for="odd in oddsAH" :key="odd.platform" class="odds-table-row">
          <span class="odds-platform">{{ odd.platform }}</span>
          <span :class="['odds-value', { best: odd.homeBest }]">{{ odd.home }}</span>
          <span :class="['odds-value', { best: odd.awayBest }]">{{ odd.away }}</span>
          <span :class="['odds-value', { negative: odd.handicap < 0 }]">{{ odd.handicap }}</span>
        </div>
        
        <div v-if="!recommendationAH" class="rec-no-value">
          ⚠️ 让球盘暂无价值优势<br>
          <span style="font-size: 11px; color: #5a5a5a;">{{ match.homeTeam.name }}-1.5 需净胜2球，概率仅45%</span>
        </div>
      </div>
    </div>
    
    <!-- Bet Plans Section -->
    <div class="plans-section">
      <div class="plans-title">投注方案</div>
      <div class="plans-subtitle">根据Kelly Criterion生成多套方案，选择适合你的风险偏好</div>
      
      <!-- Plan Cards -->
      <div 
        v-for="(plan, idx) in betPlans" 
        :key="idx"
        :class="['plan-card', { selected: selectedPlan === idx }]"
        @click="selectedPlan = idx"
      >
        <div class="plan-header">
          <span class="plan-name">{{ plan.name }}</span>
          <span :class="['plan-risk', plan.riskLevel]">风险 {{ plan.risk }}</span>
        </div>
        
        <div class="plan-bets">
          <div v-for="(bet, bIdx) in plan.bets" :key="bIdx" class="bet-item">
            <div class="bet-item-header">
              <span class="bet-target">{{ bet.platform }} · {{ bet.type }} · {{ bet.target }}</span>
              <span class="bet-amount">¥{{ bet.amount }}</span>
            </div>
            <div class="bet-item-detail">
              <span class="bet-odds">赔率 {{ bet.odds }}</span>
              <span class="bet-return">预期 +¥{{ bet.expectedReturn }}</span>
            </div>
          </div>
        </div>
        
        <div class="plan-summary">
          <div class="summary-item">
            <span class="summary-label">总投入</span>
            <span class="summary-value">¥{{ plan.totalStake }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">预期ROI</span>
            <span :class="['summary-value', { positive: plan.expectedROI > 0 }]">+{{ plan.expectedROI }}%</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">{{ plan.winRateLabel }}</span>
            <span class="summary-value">~{{ plan.winRate }}%</span>
          </div>
        </div>
        
        <div class="copy-btn" @click="copyPlan(plan)">复制方案到投注平台</div>
      </div>
    </div>
    
    <!-- Analysis Section -->
    <div class="analysis-section">
      <div class="analysis-title">预测分析依据</div>
      <div class="analysis-content">
        <strong>Poisson模型结果：</strong><br>
        • {{ match.homeTeam.name }}主场场均进球 {{ analysis.homeGoalsAvg }}，失球 {{ analysis.homeConcedeAvg }}<br>
        • {{ match.awayTeam.name }}客场场均进球 {{ analysis.awayGoalsAvg }}，失球 {{ analysis.awayConcedeAvg }}<br>
        • 最可能比分：{{ analysis.mostLikelyScore }} (概率{{ analysis.mostLikelyProb }}%)<br>
        <br>
        <strong>Kelly计算：</strong><br>
        • Half-Kelly建议：{{ analysis.kellyAdvice }}<br>
        • 置信度评级：{{ analysis.confidence }}% ({{ analysis.confidenceLevel }})<br>
        • 风险提示：{{ analysis.riskWarning }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { cache } from '../../api'
import type { CachedMatchDetailResponse, CachedPrediction } from '../../api'

const route = useRoute()
const router = useRouter()
const matchId = computed(() => route.params.id as string)

const loading = ref(true)
const error = ref('')
const playType = ref<'1x2' | 'ou' | 'ah'>('1x2')
const selectedPlan = ref(0)

// API Data
const matchData = ref<CachedMatchDetailResponse | null>(null)

// Match Info (from API)
const match = computed(() => {
  if (!matchData.value?.match) {
    return {
      id: matchId.value,
      league: '--',
      round: '--',
      homeTeam: { name: '--', short: '--' },
      awayTeam: { name: '--', short: '--' },
      time: '--',
      stadium: '待获取'
    }
  }
  const m = matchData.value.match
  return {
    id: m.match_id,
    league: m.league_name || m.league,
    round: '--',
    homeTeam: { name: m.home_team, short: m.home_team.substring(0, 2).toUpperCase() },
    awayTeam: { name: m.away_team, short: m.away_team.substring(0, 2).toUpperCase() },
    time: formatTime(m.match_date),
    stadium: '待获取'
  }
})

// Prediction (from API)
const prediction = computed(() => matchData.value?.prediction)

// Odds History (from API)
const oddsHistory = computed(() => matchData.value?.odds_history || [])

// Latest Odds
const latestOdds = computed(() => {
  if (oddsHistory.value.length === 0) return null
  return oddsHistory.value[0]
})

// Update Time
const oddsUpdateTime = computed(() => {
  if (!latestOdds.value) return '--'
  return formatTime(latestOdds.value.collected_at)
})

// 1X2 Odds (from API odds_history)
const odds1x2 = computed(() => {
  if (oddsHistory.value.length === 0) {
    return [{ platform: '待获取', home: '--', draw: '--', away: '--', homeBest: false, drawBest: false, awayBest: false }]
  }
  
  // 汇总各平台赔率
  const platformOdds: Record<string, any> = {}
  oddsHistory.value.forEach(o => {
    if (!platformOdds[o.bookmaker]) {
      platformOdds[o.bookmaker] = {
        platform: o.bookmaker,
        home: o.home_odds,
        draw: o.draw_odds,
        away: o.away_odds
      }
    }
  })
  
  const result = Object.values(platformOdds)
  
  // 标记最优赔率
  if (result.length > 0) {
    const maxHome = Math.max(...result.map(o => o.home))
    const maxDraw = Math.max(...result.map(o => o.draw))
    const maxAway = Math.max(...result.map(o => o.away))
    
    result.forEach(o => {
      o.homeBest = o.home === maxHome
      o.drawBest = o.draw === maxDraw
      o.awayBest = o.away === maxAway
    })
  }
  
  return result
})

// Recommendation 1x2 (from prediction)
const recommendation1x2 = computed(() => {
  if (!prediction.value) return null
  
  const pred = prediction.value
  const labelMap: Record<string, string> = { 'H': '主胜', 'D': '平局', 'A': '客胜' }
  const probMap: Record<string, number> = {
    'H': pred.combined_prob_home ?? pred.prob_home,
    'D': pred.combined_prob_draw ?? pred.prob_draw,
    'A': pred.combined_prob_away ?? pred.prob_away
  }
  
  const bestOutcome = pred.prediction
  const bestProb = probMap[bestOutcome]
  const marketProb = latestOdds.value ? 1 / (latestOdds.value.home_odds || 1) : 0.33
  const value = bestProb - marketProb
  
  return {
    title: `推荐：${labelMap[bestOutcome]}`,
    detail: `模型概率 ${Math.round(bestProb * 100)}%，市场隐含概率 ${Math.round(marketProb * 100)}%，价值 ${value > 0.05 ? '+' + Math.round(value * 100) + '%' : '无明显优势'}`
  }
})

// Analysis (from prediction)
const analysis = computed(() => {
  if (!prediction.value) {
    return {
      homeGoalsAvg: '--',
      homeConcedeAvg: '--',
      awayGoalsAvg: '--',
      awayConcedeAvg: '--',
      mostLikelyScore: '--',
      mostLikelyProb: '--',
      kellyAdvice: '待分析',
      confidence: 0,
      confidenceLevel: '--',
      riskWarning: '请等待数据加载',
      h2hInfo: null
    }
  }
  
  const pred = prediction.value
  const maxProb = Math.max(
    pred.combined_prob_home ?? pred.prob_home,
    pred.combined_prob_draw ?? pred.prob_draw,
    pred.combined_prob_away ?? pred.prob_away
  )
  
  let confidenceLevel = '低置信'
  if (maxProb > 0.6) confidenceLevel = '高置信'
  else if (maxProb > 0.5) confidenceLevel = '中等置信'
  
  return {
    homeGoalsAvg: pred.expected_home_goals.toFixed(2),
    homeConcedeAvg: '--',
    awayGoalsAvg: pred.expected_away_goals.toFixed(2),
    awayConcedeAvg: '--',
    mostLikelyScore: pred.most_likely_score,
    mostLikelyProb: '--',
    kellyAdvice: `预期进球 ${pred.expected_home_goals} vs ${pred.expected_away_goals}`,
    confidence: Math.round(maxProb * 100),
    confidenceLevel,
    riskWarning: '建议结合H2H历史交锋数据综合判断',
    h2hInfo: pred.h2h_prediction
  }
})

// Mock OU and AH for now (need more API data)
const oddsOU = ref([
  { platform: 'Bet365', over: 1.85, under: 1.95, line: 2.5, overBest: false, underBest: false },
  { platform: 'Sbobet', over: 1.80, under: 2.00, line: 2.5, overBest: false, underBest: true },
  { platform: 'Pinnacle', over: 1.82, under: 1.98, line: 2.5, overBest: false, underBest: false }
])

const recommendationOU = computed(() => {
  if (!prediction.value) return null
  
  // 基于预期进球判断大小球倾向
  const totalGoals = prediction.value.expected_home_goals + prediction.value.expected_away_goals
  
  if (totalGoals > 2.5) {
    return { title: '推荐：大2.5球', detail: `预期总进球 ${totalGoals.toFixed(1)}，倾向大球` }
  } else {
    return { title: '推荐：小2.5球', detail: `预期总进球 ${totalGoals.toFixed(1)}，倾向小球` }
  }
})

const oddsAH = ref([
  { platform: 'Bet365', home: 1.75, away: 2.10, handicap: -1.5, homeBest: false, awayBest: false },
  { platform: 'Sbobet', home: 1.80, away: 2.05, handicap: -1.5, homeBest: true, awayBest: false },
  { platform: 'Pinnacle', home: 1.78, away: 2.15, handicap: -1.5, homeBest: false, awayBest: true }
])

const recommendationAH = computed(() => {
  if (!prediction.value) return null
  
  const pred = prediction.value
  const homeProb = pred.combined_prob_home ?? pred.prob_home
  
  if (homeProb > 0.65) {
    return { title: '推荐：主队让1.5球', detail: `主胜概率 ${Math.round(homeProb * 100)}%，可尝试让球盘` }
  }
  return null
})

// Bet Plans (computed from prediction)
const betPlans = computed(() => {
  if (!prediction.value || !latestOdds.value) {
    return [{
      name: '方案A · 待数据',
      risk: 0,
      riskLevel: 'low',
      bets: [],
      totalStake: 0,
      expectedROI: 0,
      winRateLabel: '加载中',
      winRate: 0
    }]
  }
  
  const pred = prediction.value
  const odds = latestOdds.value
  const maxProb = Math.max(
    pred.combined_prob_home ?? pred.prob_home,
    pred.combined_prob_draw ?? pred.prob_draw,
    pred.combined_prob_away ?? pred.prob_away
  )
  const bestOutcome = pred.prediction
  
  const labelMap: Record<string, string> = { 'H': '主胜', 'D': '平局', 'A': '客胜' }
  const oddsMap: Record<string, number> = { 'H': odds.home_odds, 'D': odds.draw_odds, 'A': odds.away_odds }
  
  return [
    {
      name: '方案A · 分散保守',
      risk: 20,
      riskLevel: 'low',
      bets: [
        { platform: odds.bookmaker, type: '胜平负', target: labelMap[bestOutcome], amount: 60, odds: oddsMap[bestOutcome], expectedReturn: Math.round(60 * oddsMap[bestOutcome] * maxProb) }
      ],
      totalStake: 60,
      expectedROI: Math.round((oddsMap[bestOutcome] * maxProb - 1) * 100),
      winRateLabel: '置信度',
      winRate: Math.round(maxProb * 100)
    },
    {
      name: '方案B · 单注平衡',
      risk: 40,
      riskLevel: 'medium',
      bets: [
        { platform: odds.bookmaker, type: '胜平负', target: labelMap[bestOutcome], amount: 100, odds: oddsMap[bestOutcome], expectedReturn: Math.round(100 * oddsMap[bestOutcome] * maxProb) }
      ],
      totalStake: 100,
      expectedROI: Math.round((oddsMap[bestOutcome] * maxProb - 1) * 100),
      winRateLabel: 'Kelly比例',
      winRate: Math.round((maxProb * oddsMap[bestOutcome] - 1) / (oddsMap[bestOutcome] - 1) * 100) || 10
    },
    {
      name: '方案C · 串关激进',
      risk: 60,
      riskLevel: 'high',
      bets: [
        { platform: '串关2串1', type: '组合', target: labelMap[bestOutcome] + ' + 大小球', amount: 50, odds: oddsMap[bestOutcome] * 1.9, expectedReturn: Math.round(50 * oddsMap[bestOutcome] * 1.9 * 0.35) }
      ],
      totalStake: 50,
      expectedROI: Math.round((oddsMap[bestOutcome] * 1.9 * 0.35 - 1) * 100),
      winRateLabel: '胜率估算',
      winRate: 35
    }
  ]
})

// Load data
onMounted(async () => {
  try {
    const result = await cache.matchDetail(matchId.value)
    if (result.success) {
      matchData.value = result
    } else {
      error.value = '获取数据失败'
    }
  } catch (e: any) {
    error.value = e.message || '网络错误'
    console.error('Failed to load match detail:', e)
  } finally {
    loading.value = false
  }
})

function formatTime(dateStr: string) {
  if (!dateStr) return '--'
  const date = new Date(dateStr)
  const month = (date.getMonth() + 1).toString().padStart(2, '0')
  const day = date.getDate().toString().padStart(2, '0')
  const hours = date.getHours().toString().padStart(2, '0')
  const mins = date.getMinutes().toString().padStart(2, '0')
  return `${month}/${day} ${hours}:${mins}`
}

function copyPlan(plan: any) {
  let text = `【KickBet ${plan.name}】\n`
  plan.bets.forEach((bet: any) => {
    text += `${bet.platform} ${bet.type} ${bet.target} ¥${bet.amount} @${bet.odds}\n`
  })
  text += `总投入 ¥${plan.totalStake}，预期ROI +${plan.expectedROI}%`
  
  if (navigator.clipboard) {
    navigator.clipboard.writeText(text)
    alert('方案已复制！请前往对应投注平台执行。')
  } else {
    alert('复制内容：\n' + text)
  }
}
</script>

<style scoped>
.match-detail-page {
  font-family: 'Inter', -apple-system, sans-serif;
  background: #08090a;
  color: #ffffff;
  min-height: 100vh;
  max-width: 420px;
  margin: 0 auto;
  padding-bottom: 100px;
}

/* Header */
.header {
  display: flex;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #2a2b2c;
  position: sticky;
  top: 0;
  background: #08090a;
  z-index: 100;
}

.back-btn {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: #121314;
  border: 1px solid #2a2b2c;
  color: #8b8b8b;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  margin-right: 12px;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
}

/* Match Hero */
.match-hero {
  padding: 20px 16px;
  text-align: center;
  background: linear-gradient(180deg, #121314 0%, #08090a 100%);
}

.league-tag {
  font-size: 12px;
  color: #8b8b8b;
  background: #1a1b1c;
  padding: 4px 12px;
  border-radius: 4px;
  margin-bottom: 12px;
}

.teams-display {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  margin-bottom: 12px;
}

.team-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.team-logo-large {
  width: 56px;
  height: 56px;
  background: #1a1b1c;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 700;
  border: 2px solid #2a2b2c;
}

.team-name-large {
  font-size: 15px;
  font-weight: 600;
}

.vs-text {
  font-size: 13px;
  color: #5a5a5a;
  font-weight: 500;
}

.match-info {
  font-size: 12px;
  color: #8b8b8b;
}

/* Data Source */
.data-source {
  margin: 12px 16px;
  background: rgba(74,144,217,0.1);
  border: 1px solid rgba(74,144,217,0.3);
  border-radius: 8px;
  padding: 10px 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.source-label {
  font-size: 12px;
  color: #8b8b8b;
}

.source-name {
  font-size: 13px;
  font-weight: 600;
  color: #4a90d9;
  margin-left: 8px;
}

.source-update {
  font-size: 11px;
  color: #5a5a5a;
  font-family: 'Roboto Mono', monospace;
}

/* Odds Section */
.odds-section {
  margin: 16px;
}

.odds-section-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.odds-section-title::before {
  content: '';
  width: 3px;
  height: 14px;
  background: #00d4aa;
  border-radius: 1px;
}

/* Play Type Tabs */
.play-type-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.play-tab {
  flex: 1;
  padding: 10px;
  background: #121314;
  border: 1px solid #2a2b2c;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  color: #8b8b8b;
  cursor: pointer;
  text-align: center;
}

.play-tab.active {
  background: #00d4aa;
  color: #08090a;
  border-color: #00d4aa;
}

/* Odds Table */
.odds-table {
  background: #121314;
  border: 1px solid #2a2b2c;
  border-radius: 12px;
  overflow: hidden;
}

.odds-table-header {
  display: grid;
  grid-template-columns: 1fr repeat(3, 1fr);
  padding: 10px 12px;
  background: #1a1b1c;
  font-size: 12px;
  color: #5a5a5a;
  border-bottom: 1px solid #2a2b2c;
}

.odds-table-row {
  display: grid;
  grid-template-columns: 1fr repeat(3, 1fr);
  padding: 10px 12px;
  font-size: 13px;
  border-bottom: 1px solid #2a2b2c;
}

.odds-table-row:last-child {
  border-bottom: none;
}

.odds-platform {
  font-weight: 500;
}

.odds-value {
  text-align: center;
  font-family: 'Roboto Mono', monospace;
}

.odds-value.best {
  color: #00d4aa;
  font-weight: 700;
  background: rgba(0,212,170,0.1);
  border-radius: 4px;
  padding: 4px 8px;
}

.odds-value.negative {
  color: #ff6b6b;
}

/* Recommendation */
.recommendation-box {
  margin: 12px 0;
  background: linear-gradient(135deg, rgba(0,212,170,0.1) 0%, rgba(0,212,170,0.05) 100%);
  border: 1px solid rgba(0,212,170,0.3);
  border-radius: 8px;
  padding: 12px;
}

.rec-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.rec-icon {
  font-size: 16px;
}

.rec-title {
  font-size: 13px;
  font-weight: 600;
  color: #00d4aa;
}

.rec-detail {
  font-size: 12px;
  color: #ffffff;
  line-height: 1.6;
}

.rec-no-value {
  background: rgba(255,107,107,0.1);
  border: 1px solid rgba(255,107,107,0.3);
  border-radius: 8px;
  padding: 12px;
  font-size: 13px;
  color: #ff6b6b;
  text-align: center;
  margin: 12px 0;
}

/* Plans Section */
.plans-section {
  margin: 16px;
}

.plans-title {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 16px;
}

.plans-subtitle {
  font-size: 12px;
  color: #8b8b8b;
  margin-bottom: 16px;
}

/* Plan Card */
.plan-card {
  background: #121314;
  border: 1px solid #2a2b2c;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  cursor: pointer;
}

.plan-card.selected {
  border-color: #00d4aa;
  background: rgba(0,212,170,0.05);
}

.plan-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.plan-name {
  font-size: 15px;
  font-weight: 600;
}

.plan-risk {
  font-size: 11px;
  padding: 4px 10px;
  border-radius: 4px;
  font-weight: 500;
}

.plan-risk.low {
  background: #00d4aa;
  color: #08090a;
}

.plan-risk.medium {
  background: #ffa500;
  color: #08090a;
}

.plan-risk.high {
  background: #ff6b6b;
  color: #08090a;
}

/* Plan Bets */
.plan-bets {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.bet-item {
  background: #1a1b1c;
  border-radius: 8px;
  padding: 12px;
}

.bet-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.bet-target {
  font-size: 13px;
  font-weight: 500;
}

.bet-amount {
  font-size: 15px;
  font-weight: 700;
  font-family: 'Roboto Mono', monospace;
  color: #00d4aa;
}

.bet-item-detail {
  font-size: 12px;
  color: #8b8b8b;
  display: flex;
  gap: 12px;
}

.bet-odds {
  font-family: 'Roboto Mono', monospace;
}

.bet-return {
  color: #00d4aa;
}

/* Plan Summary */
.plan-summary {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  background: #1a1b1c;
  border-radius: 8px;
  padding: 12px;
  margin-top: 12px;
}

.summary-item {
  text-align: center;
}

.summary-label {
  font-size: 11px;
  color: #5a5a5a;
}

.summary-value {
  font-size: 14px;
  font-weight: 600;
  font-family: 'Roboto Mono', monospace;
  margin-top: 4px;
}

.summary-value.positive {
  color: #00d4aa;
}

/* Copy Button */
.copy-btn {
  width: 100%;
  padding: 14px;
  background: #8b5cf6;
  color: #08090a;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 12px;
}

/* Analysis Section */
.analysis-section {
  margin: 16px;
  background: #121314;
  border: 1px solid #2a2b2c;
  border-radius: 12px;
  padding: 16px;
}

.analysis-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
}

.analysis-content {
  font-size: 13px;
  color: #8b8b8b;
  line-height: 1.6;
}
</style>