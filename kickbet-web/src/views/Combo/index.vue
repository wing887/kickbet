<template>
  <div class="combo-page">
    <!-- Header -->
    <header class="header">
      <div class="back-btn" @click="$router.push('/')">←</div>
      <span class="header-title">组合投注</span>
      <span class="header-badge">会员专属</span>
    </header>
    
    <!-- Info Banner -->
    <div class="info-banner">
      <span class="info-icon">💡</span>
      <span class="info-text">Kelly Criterion科学分配资金 + 智能串关建议，帮助您优化投注策略</span>
    </div>
    
    <!-- Step 1: Match Selection -->
    <div class="section-title">
      <span class="step-number">1</span>
      <span>选择比赛</span>
    </div>
    
    <div class="match-selector">
      <div 
        v-for="(match, idx) in selectedMatches" 
        :key="idx"
        class="selector-card"
      >
        <div class="selector-header">
          <span class="selector-match">{{ match.home_team }} vs {{ match.away_team }}</span>
          <span class="selector-league">{{ match.league_name }}</span>
        </div>
        <div class="bet-type-grid">
          <div 
            :class="['bet-type-btn', { selected: match.selectedBet === 'home' }]"
            @click="match.selectedBet = 'home'"
          >
            <span class="bet-type-label">主胜</span>
            <span class="bet-type-odds">{{ match.odds?.home || '--' }}</span>
          </div>
          <div 
            :class="['bet-type-btn', { selected: match.selectedBet === 'draw' }]"
            @click="match.selectedBet = 'draw'"
          >
            <span class="bet-type-label">平局</span>
            <span class="bet-type-odds">{{ match.odds?.draw || '--' }}</span>
          </div>
          <div 
            :class="['bet-type-btn', { selected: match.selectedBet === 'away' }]"
            @click="match.selectedBet = 'away'"
          >
            <span class="bet-type-label">客胜</span>
            <span class="bet-type-odds">{{ match.odds?.away || '--' }}</span>
          </div>
        </div>
      </div>
      
      <div class="add-match-btn" @click="showMatchPicker = true">
        <span>+ 添加比赛</span>
      </div>
    </div>
    
    <!-- Step 2: Budget Input -->
    <div class="section-title">
      <span class="step-number">2</span>
      <span>输入资金</span>
    </div>
    
    <div class="budget-section">
      <div class="budget-card">
        <div class="budget-header">总投注预算</div>
        <div class="budget-input-row">
          <input 
            v-model.number="budget"
            type="number" 
            class="budget-input" 
            placeholder="¥1000"
          >
          <select v-model="riskMode" class="risk-select">
            <option value="half">保守(Half)</option>
            <option value="full">激进(Full)</option>
          </select>
        </div>
      </div>
    </div>
    
    <!-- Step 3: Generate -->
    <div class="section-title">
      <span class="step-number">3</span>
      <span>生成建议</span>
    </div>
    
    <button 
      class="generate-btn" 
      @click="generateResults"
      :disabled="selectedMatches.length < 2 || generating"
    >
      <span>{{ generating ? '计算中...' : '生成组合建议' }}</span>
    </button>
    
    <!-- Results Section -->
    <div v-if="showResults" class="results-section">
      <div class="results-header">
        <span>Kelly资金分配</span>
        <span class="results-badge">完成</span>
      </div>
      
      <div class="kelly-results">
        <div class="kelly-title">{{ riskMode === 'half' ? 'Half-Kelly' : 'Full-Kelly' }}分配结果</div>
        
        <div 
          v-for="(item, idx) in kellyResults" 
          :key="idx"
          class="kelly-item"
        >
          <div class="kelly-item-left">
            <span class="kelly-match-name">{{ item.match }}</span>
            <span class="kelly-bet-type">{{ item.betType }} @ {{ item.odds }}</span>
          </div>
          <div class="kelly-item-right">
            <span class="kelly-amount">¥{{ item.amount }}</span>
            <span class="kelly-percent">{{ item.percent }}% (置信度{{ item.confidence }}%)</span>
          </div>
        </div>
      </div>
      
      <!-- Parlay Suggestions -->
      <div class="results-header">
        <span>串关建议</span>
      </div>
      
      <div class="parlay-section">
        <div class="parlay-title">推荐串关方案</div>
        
        <div 
          v-for="(parlay, idx) in parlaySuggestions" 
          :key="idx"
          :class="['parlay-card', { recommended: parlay.recommended }]"
        >
          <div class="parlay-header">
            <span class="parlay-type">{{ parlay.type }}</span>
            <span :class="['parlay-risk', parlay.riskLevel]">{{ parlay.riskLabel }}</span>
          </div>
          <div class="parlay-stats">
            <div class="parlay-stat">
              <span class="parlay-stat-label">组合赔率</span>
              <span class="parlay-stat-value">{{ parlay.combinedOdds }}</span>
            </div>
            <div class="parlay-stat">
              <span class="parlay-stat-label">胜率估算</span>
              <span class="parlay-stat-value">{{ parlay.winProb }}%</span>
            </div>
            <div class="parlay-stat">
              <span class="parlay-stat-label">建议金额</span>
              <span class="parlay-stat-value">¥{{ parlay.suggestedAmount }}</span>
            </div>
          </div>
          <div v-if="parlay.recommended" class="parlay-recommended-badge">✓ 推荐方案</div>
        </div>
      </div>
      
      <!-- Summary -->
      <div class="summary-box">
        <div class="summary-row">
          <span class="summary-label">风险评分</span>
          <span class="summary-value">{{ summary.riskScore }}/100</span>
        </div>
        <div class="summary-row">
          <span class="summary-label">期望ROI</span>
          <span class="summary-value highlight">{{ summary.expectedROI }}%</span>
        </div>
        <div class="summary-row">
          <span class="summary-label">建议策略</span>
          <span class="summary-value">{{ summary.strategy }}</span>
        </div>
      </div>
    </div>
    
    <!-- Match Picker Modal -->
    <div v-if="showMatchPicker" class="match-picker-modal">
      <div class="picker-card">
        <div class="picker-header">
          <span class="picker-title">选择比赛</span>
          <span class="picker-close" @click="showMatchPicker = false">×</span>
        </div>
        <div class="picker-list">
          <div 
            v-for="match in availableMatches" 
            :key="match.match_id"
            class="picker-item"
            @click="addMatch(match)"
          >
            <span class="picker-match-name">{{ match.home_team }} vs {{ match.away_team }}</span>
            <span class="picker-match-league">{{ match.league_name }}</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Footer -->
    <BottomNav :active="'combo'" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { matches, analysis } from '../../api'
import type { Match, AnalysisResponse } from '../../api'
import BottomNav from '../../components/common/BottomNav.vue'

const router = useRouter()

const budget = ref(1000)
const riskMode = ref<'half' | 'full'>('half')
const generating = ref(false)
const showResults = ref(false)
const showMatchPicker = ref(false)

const availableMatches = ref<Match[]>([])
const selectedMatches = ref<MatchWithSelection[]>([])
const kellyResults = ref<KellyResult[]>([])
const parlaySuggestions = ref<ParlaySuggestion[]>([])
const summary = ref({
  riskScore: 35,
  expectedROI: '+8.5%',
  strategy: '单注分散 + 双串关'
})

interface MatchWithSelection extends Match {
  selectedBet: 'home' | 'draw' | 'away'
  odds?: { home: number; draw: number; away: number }
}

interface KellyResult {
  match: string
  betType: string
  odds: number
  amount: number
  percent: number
  confidence: number
}

interface ParlaySuggestion {
  type: string
  riskLevel: 'low' | 'medium' | 'high'
  riskLabel: string
  combinedOdds: number
  winProb: number
  suggestedAmount: number
  recommended: boolean
}

onMounted(async () => {
  try {
    const result = await matches.list(3)
    availableMatches.value = result.matches
    
    // 默认添加两场比赛
    if (result.matches.length >= 2) {
      const m1 = result.matches[0]
      const m2 = result.matches[1]
      
      selectedMatches.value = [
        { ...m1, selectedBet: 'home', odds: { home: 1.42, draw: 4.5, away: 8.0 } },
        { ...m2, selectedBet: 'home', odds: { home: 1.65, draw: 3.5, away: 5.0 } }
      ]
    }
  } catch (e) {
    console.error('Failed to load matches:', e)
    // 使用模拟数据
    selectedMatches.value = [
      { match_id: 1, home_team: '曼城', away_team: '布伦特福德', league: 'PL', league_name: '英超', match_date: '', selectedBet: 'home', odds: { home: 1.42, draw: 4.5, away: 8.0 } },
      { match_id: 2, home_team: '山东泰山', away_team: '浙江队', league: 'CSL', league_name: '中超', match_date: '', selectedBet: 'home', odds: { home: 1.65, draw: 3.5, away: 5.0 } }
    ]
  }
})

function addMatch(match: Match) {
  // 获取默认赔率
  const odds = { home: 2.0, draw: 3.3, away: 4.0 }
  selectedMatches.value.push({ ...match, selectedBet: 'home', odds })
  showMatchPicker.value = false
}

async function generateResults() {
  if (selectedMatches.value.length < 2) return
  
  generating.value = true
  
  try {
    // 模拟Kelly计算
    const kellyFraction = riskMode.value === 'half' ? 0.5 : 1.0
    
    kellyResults.value = selectedMatches.value.map(m => {
      const odds = m.odds?.[m.selectedBet === 'home' ? 'home' : m.selectedBet === 'draw' ? 'draw' : 'away'] || 2.0
      const confidence = m.selectedBet === 'home' ? 75 : m.selectedBet === 'draw' ? 35 : 25
      const kellyPct = Math.min((confidence / 100) * kellyFraction * 0.1, 0.06)
      const amount = Math.round(budget.value * kellyPct)
      
      return {
        match: `${m.home_team} vs ${m.away_team}`,
        betType: m.selectedBet === 'home' ? '主胜' : m.selectedBet === 'draw' ? '平局' : '客胜',
        odds,
        amount,
        percent: Math.round(kellyPct * 100),
        confidence
      }
    })
    
    // 生成串关建议
    const oddsList = selectedMatches.value.map(m => 
      m.odds?.[m.selectedBet === 'home' ? 'home' : m.selectedBet === 'draw' ? 'draw' : 'away'] || 2.0
    )
    
    const doubleOdds = oddsList.slice(0, 2).reduce((a, b) => a * b, 1)
    const tripleOdds = oddsList.reduce((a, b) => a * b, 1)
    
    parlaySuggestions.value = [
      {
        type: '双串关',
        riskLevel: 'low',
        riskLabel: '低风险',
        combinedOdds: Math.round(doubleOdds * 100) / 100,
        winProb: Math.round(100 / doubleOdds),
        suggestedAmount: Math.round(budget.value * 0.05),
        recommended: true
      },
      {
        type: '三串关',
        riskLevel: 'medium',
        riskLabel: '中风险',
        combinedOdds: Math.round(tripleOdds * 100) / 100,
        winProb: Math.round(100 / tripleOdds),
        suggestedAmount: Math.round(budget.value * 0.03),
        recommended: false
      }
    ]
    
    // 计算总结
    const totalRisk = kellyResults.value.reduce((sum, k) => sum + k.percent, 0)
    summary.value = {
      riskScore: Math.min(totalRisk * 5, 100),
      expectedROI: `+${Math.round(8.5 * (riskMode.value === 'half' ? 1 : 1.5))}%`,
      strategy: totalRisk < 15 ? '单注分散 + 双串关' : '谨慎单注'
    }
    
    showResults.value = true
  } finally {
    generating.value = false
  }
}
</script>

<style scoped>
.combo-page {
  font-family: 'Inter', -apple-system, sans-serif;
  background: #08090a;
  color: #ffffff;
  min-height: 100vh;
  max-width: 420px;
  margin: 0 auto;
  padding-bottom: 80px;
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

.header-badge {
  font-size: 11px;
  background: #8b5cf6;
  color: #08090a;
  padding: 4px 8px;
  border-radius: 4px;
  margin-left: 12px;
}

/* Info Banner */
.info-banner {
  background: linear-gradient(135deg, rgba(74,144,217,0.1) 0%, rgba(74,144,217,0.05) 100%);
  border: 1px solid rgba(74,144,217,0.3);
  border-radius: 8px;
  padding: 12px 16px;
  margin: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.info-icon {
  font-size: 20px;
}

.info-text {
  font-size: 13px;
  color: #8b8b8b;
  line-height: 1.5;
}

/* Section Title */
.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #8b8b8b;
  padding: 16px 16px 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.step-number {
  width: 20px;
  height: 20px;
  background: #4a90d9;
  color: #08090a;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
}

/* Match Selector */
.match-selector {
  margin: 8px 16px;
}

.selector-card {
  background: #121314;
  border: 1px solid #2a2b2c;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 8px;
}

.selector-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.selector-match {
  font-size: 14px;
  font-weight: 500;
}

.selector-league {
  font-size: 12px;
  color: #5a5a5a;
}

.bet-type-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.bet-type-btn {
  padding: 8px;
  background: #1a1b1c;
  border: 1px solid #2a2b2c;
  border-radius: 4px;
  text-align: center;
  cursor: pointer;
}

.bet-type-btn.selected {
  background: rgba(0,212,170,0.2);
  border-color: #00d4aa;
}

.bet-type-label {
  font-size: 11px;
  color: #5a5a5a;
}

.bet-type-odds {
  font-size: 14px;
  font-weight: 600;
  font-family: 'Roboto Mono', monospace;
  margin-top: 2px;
}

.bet-type-btn.selected .bet-type-odds {
  color: #00d4aa;
}

.add-match-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 12px;
  background: #121314;
  border: 1px dashed #2a2b2c;
  border-radius: 8px;
  color: #8b8b8b;
  font-size: 14px;
  cursor: pointer;
  margin-top: 8px;
}

.add-match-btn:hover {
  border-color: #4a90d9;
  color: #4a90d9;
}

/* Budget Section */
.budget-section {
  margin: 16px;
}

.budget-card {
  background: #121314;
  border: 1px solid #2a2b2c;
  border-radius: 12px;
  padding: 16px;
}

.budget-header {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
}

.budget-input-row {
  display: flex;
  gap: 12px;
}

.budget-input {
  flex: 1;
  background: #0d0e0f;
  border: 1px solid #2a2b2c;
  border-radius: 8px;
  padding: 12px 16px;
  font-size: 16px;
  font-family: 'Roboto Mono', monospace;
  color: #ffffff;
  outline: none;
}

.budget-input:focus {
  border-color: #4a90d9;
}

.risk-select {
  width: 120px;
  background: #0d0e0f;
  border: 1px solid #2a2b2c;
  border-radius: 8px;
  padding: 12px;
  font-size: 14px;
  color: #ffffff;
}

/* Generate Button */
.generate-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: calc(100% - 32px);
  margin: 8px 16px 16px;
  padding: 16px;
  background: #4a90d9;
  color: #08090a;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  border: none;
}

.generate-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Results Section */
.results-section {
  margin: 16px;
}

.results-header {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.results-badge {
  font-size: 11px;
  background: #00d4aa;
  color: #08090a;
  padding: 2px 8px;
  border-radius: 4px;
}

/* Kelly Results */
.kelly-results {
  background: #121314;
  border: 1px solid #2a2b2c;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
}

.kelly-title {
  font-size: 13px;
  font-weight: 600;
  color: #ffa500;
  margin-bottom: 12px;
}

.kelly-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background: #1a1b1c;
  border-radius: 8px;
  margin-bottom: 8px;
}

.kelly-item-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.kelly-match-name {
  font-size: 13px;
  font-weight: 500;
}

.kelly-bet-type {
  font-size: 11px;
  color: #5a5a5a;
}

.kelly-item-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.kelly-amount {
  font-size: 18px;
  font-weight: 700;
  font-family: 'Roboto Mono', monospace;
  color: #ffa500;
}

.kelly-percent {
  font-size: 12px;
  color: #5a5a5a;
}

/* Parlay Section */
.parlay-section {
  background: #121314;
  border: 1px solid #2a2b2c;
  border-radius: 12px;
  padding: 16px;
}

.parlay-title {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 12px;
}

.parlay-card {
  background: #1a1b1c;
  border: 1px solid #2a2b2c;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 8px;
  cursor: pointer;
}

.parlay-card.recommended {
  border-color: #00d4aa;
  background: rgba(0,212,170,0.1);
}

.parlay-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.parlay-type {
  font-size: 14px;
  font-weight: 600;
}

.parlay-risk {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
}

.parlay-risk.low {
  background: #00d4aa;
  color: #08090a;
}

.parlay-risk.medium {
  background: #ffa500;
  color: #08090a;
}

.parlay-risk.high {
  background: #ff6b6b;
  color: #08090a;
}

.parlay-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.parlay-stat {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.parlay-stat-label {
  font-size: 11px;
  color: #5a5a5a;
}

.parlay-stat-value {
  font-size: 14px;
  font-weight: 600;
  font-family: 'Roboto Mono', monospace;
}

.parlay-recommended-badge {
  font-size: 11px;
  background: #00d4aa;
  color: #08090a;
  padding: 4px 8px;
  border-radius: 4px;
  text-align: center;
  margin-top: 8px;
}

/* Summary Box */
.summary-box {
  background: linear-gradient(135deg, rgba(0,212,170,0.1) 0%, rgba(0,212,170,0.05) 100%);
  border: 1px solid rgba(0,212,170,0.3);
  border-radius: 8px;
  padding: 16px;
  margin-top: 16px;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.summary-label {
  font-size: 13px;
  color: #8b8b8b;
}

.summary-value {
  font-size: 16px;
  font-weight: 600;
  font-family: 'Roboto Mono', monospace;
}

.summary-value.highlight {
  color: #00d4aa;
}

/* Match Picker Modal */
.match-picker-modal {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.picker-card {
  background: #121314;
  border: 1px solid #2a2b2c;
  border-radius: 12px;
  padding: 24px;
  max-width: 320px;
  width: 90%;
}

.picker-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.picker-title {
  font-size: 16px;
  font-weight: 600;
}

.picker-close {
  font-size: 20px;
  color: #5a5a5a;
  cursor: pointer;
}

.picker-list {
  max-height: 300px;
  overflow-y: auto;
}

.picker-item {
  padding: 12px;
  background: #1a1b1c;
  border-radius: 8px;
  margin-bottom: 8px;
  cursor: pointer;
}

.picker-item:hover {
  background: #2a2b2c;
}

.picker-match-name {
  font-size: 14px;
  font-weight: 500;
}

.picker-match-league {
  font-size: 12px;
  color: #5a5a5a;
}
</style>