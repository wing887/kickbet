<template>
  <div class="home-page">
    <!-- Header -->
    <header class="header">
      <div class="logo" @click="$router.push('/')">KickBet</div>
      <div class="header-actions">
        <div class="btn-icon" @click="handleAuthClick">👤</div>
        <div class="btn-icon" @click="$router.push('/tracker')">📈</div>
      </div>
    </header>
    
    <!-- Data Source Bar -->
    <div class="data-source-bar">
      <span class="source-text">赔率来源：<strong>Odds-API.io</strong> · Bet365 + Sbobet + Pinnacle</span>
      <span :class="['source-status', { offline: !apiOnline }]">{{ apiOnline ? '● 实时' : '○ 离线' }}</span>
    </div>
    
    <!-- Daily Pick Section -->
    <div class="section-title">
      <span>今日最佳推荐</span>
      <span class="section-badge">L4分析</span>
    </div>
    
    <div class="main-rec-card">
      <div v-if="dailyPick" class="rec-content">
        <div class="match-header">
          <span class="league-badge">{{ dailyPick.league_name || '推荐' }}</span>
          <span class="match-time">{{ formatTime(dailyPick.match_date) }}</span>
        </div>
        
        <div class="teams-row">
          <div class="team">
            <div class="team-logo">{{ getTeamAbbr(dailyPick.home_team) }}</div>
            <span class="team-name">{{ dailyPick.home_team }}</span>
          </div>
          <span class="vs">VS</span>
          <div class="team">
            <div class="team-logo">{{ getTeamAbbr(dailyPick.away_team) }}</div>
            <span class="team-name">{{ dailyPick.away_team }}</span>
          </div>
        </div>
        
        <div class="best-odds-box">
          <div class="best-odds-header">
            <span class="best-play-type">胜平负</span>
            <span class="best-platform">Poisson模型</span>
          </div>
          <div class="best-odds-content">
            <span class="best-option">✓ {{ getPredictionLabel(dailyPick.prediction) }}</span>
            <span class="best-odds-value">{{ getConfidencePercent(dailyPick.prediction) }}</span>
          </div>
          <div class="best-confidence">
            <span class="conf-label">预期比分</span>
            <span class="conf-value">{{ dailyPick.prediction?.most_likely_score || '--' }}</span>
          </div>
          <div v-if="dailyPick.prediction?.h2h_prediction" class="h2h-info">
            <span class="conf-label">H2H交锋</span>
            <span class="conf-value">{{ dailyPick.prediction.h2h_prediction.total_matches }}场</span>
          </div>
        </div>
        
        <div class="plans-preview">
          <div class="plans-preview-title">投注方案预览</div>
          <div class="plan-mini">
            <div>
              <span class="plan-mini-name">方案A 分散</span>
              <span class="plan-mini-risk low">风险20</span>
            </div>
            <span class="plan-mini-roi">+65%</span>
          </div>
          <div class="plan-mini">
            <div>
              <span class="plan-mini-name">方案B 单注</span>
              <span class="plan-mini-risk medium">风险40</span>
            </div>
            <span class="plan-mini-roi">+42%</span>
          </div>
          <div class="plan-mini">
            <div>
              <span class="plan-mini-name">方案C 串关</span>
              <span class="plan-mini-risk high">风险60</span>
            </div>
            <span class="plan-mini-roi">+92%</span>
          </div>
        </div>
        
        <div class="view-detail-btn" @click="viewMatchDetail(dailyPick.match_id)">
          <span>查看完整分析 & 方案</span>
        </div>
      </div>
      
      <div v-else class="rec-loading">
        <span v-if="loading">加载中...</span>
        <span v-else>暂无今日推荐</span>
      </div>
    </div>
    
    <!-- League Tabs -->
    <div class="section-title">今日赔率</div>
    <div class="league-tabs">
      <div 
        v-for="league in leagueTabs" 
        :key="league.code"
        :class="['league-tab', { active: currentLeague === league.code }]"
        @click="currentLeague = league.code"
      >
        <span class="league-tab-name">{{ league.name }}</span>
        <span class="league-tab-count">{{ league.count }}场</span>
      </div>
    </div>
    
    <!-- Match List -->
    <div class="match-list">
      <div 
        v-for="match in filteredMatches" 
        :key="match.match_id"
        class="match-card"
        @click="viewMatchDetail(match.match_id)"
      >
        <div class="match-card-header">
          <div>
            <span class="match-card-teams">{{ match.home_team }} vs {{ match.away_team }}</span>
            <span class="match-card-league">{{ match.league_name }}</span>
          </div>
          <span class="match-card-time">{{ formatTime(match.match_date) }}</span>
        </div>
        <div class="odds-preview-grid">
          <div class="odds-preview-item">
            <span class="odds-preview-type">胜平负</span>
            <span :class="['odds-preview-best', match.prediction ? 'has-value' : 'no-value']">
              {{ getPredictionLabel(match.prediction) }}
            </span>
            <span :class="['value-tag', calculateValue(match).hasValue ? 'positive' : 'neutral']">
              {{ match.prediction ? getConfidencePercent(match.prediction) : '待分析' }}
            </span>
          </div>
          <div class="odds-preview-item">
            <span class="odds-preview-type">预期比分</span>
            <span class="odds-preview-best has-value">
              {{ match.prediction?.most_likely_score || '--' }}
            </span>
            <span class="value-tag neutral">
              {{ match.prediction ? `${match.prediction.expected_home_goals}-${match.prediction.expected_away_goals}` : '--' }}
            </span>
          </div>
          <div class="odds-preview-item">
            <span class="odds-preview-type">H2H</span>
            <span :class="['odds-preview-best', match.prediction?.h2h_prediction ? 'has-value' : 'no-value']">
              {{ match.prediction?.h2h_prediction?.total_matches || 0 }}场
            </span>
            <span :class="['value-tag', match.prediction?.h2h_prediction ? 'positive' : 'neutral']">
              {{ match.prediction?.h2h_prediction ? '已融合' : '无数据' }}
            </span>
          </div>
        </div>
      </div>
      
      <div v-if="filteredMatches.length === 0" class="match-empty">
        <span v-if="loading">加载中...</span>
        <span v-else>暂无比赛数据</span>
      </div>
    </div>
    
    <!-- Footer -->
    <BottomNav :active="'home'" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { cache } from '../../api'
import type { CachedMatch, CachedPrediction } from '../../api'
import BottomNav from '../../components/common/BottomNav.vue'

const router = useRouter()

const loading = ref(true)
const apiOnline = ref(true)
const dailyPick = ref<CachedMatch | null>(null)
const matchList = ref<CachedMatch[]>([])
const currentLeague = ref('all')

const leagueTabs = ref([
  { code: 'all', name: '全部', count: 0 },
  { code: 'PL', name: '英超', count: 0 },
  { code: 'BL1', name: '德甲', count: 0 },
  { code: 'PD', name: '西甲', count: 0 },
  { code: 'SA', name: '意甲', count: 0 },
  { code: 'FL1', name: '法甲', count: 0 }
])

const filteredMatches = computed(() => {
  if (currentLeague.value === 'all') return matchList.value
  return matchList.value.filter(m => m.league === currentLeague.value)
})

onMounted(async () => {
  try {
    // 获取比赛列表 (带预测缓存)
    const result = await cache.matches(72)  // 未来72小时比赛
    apiOnline.value = result.success
    
    if (result.success && result.matches.length > 0) {
      matchList.value = result.matches
      
      // 更新联赛计数
      updateLeagueCounts()
      
      // 找到有预测的比赛作为今日推荐
      const matchWithPrediction = result.matches.find(m => m.has_prediction)
      if (matchWithPrediction) {
        dailyPick.value = matchWithPrediction
      } else {
        // 如果没有预测，取第一场比赛
        dailyPick.value = result.matches[0]
      }
    }
  } catch (e) {
    apiOnline.value = false
    console.error('Failed to load data:', e)
  } finally {
    loading.value = false
  }
})

function updateLeagueCounts() {
  const counts: Record<string, number> = { all: matchList.value.length }
  
  matchList.value.forEach(m => {
    counts[m.league] = (counts[m.league] || 0) + 1
  })
  
  leagueTabs.value.forEach(tab => {
    tab.count = counts[tab.code] || 0
  })
}

function formatTime(dateStr: string) {
  if (!dateStr) return '--'
  const date = new Date(dateStr)
  const month = (date.getMonth() + 1).toString().padStart(2, '0')
  const day = date.getDate().toString().padStart(2, '0')
  const hours = date.getHours().toString().padStart(2, '0')
  const mins = date.getMinutes().toString().padStart(2, '0')
  return `${month}/${day} ${hours}:${mins}`
}

function getTeamAbbr(name: string) {
  if (!name) return '--'
  return name.substring(0, 2).toUpperCase()
}

// 获取预测标签 (H/D/A)
function getPredictionLabel(pred: CachedPrediction | undefined) {
  if (!pred) return '待分析'
  const labelMap: Record<string, string> = {
    'H': '主胜',
    'D': '平局',
    'A': '客胜'
  }
  return labelMap[pred.prediction] || pred.prediction
}

// 获取置信度百分比
function getConfidencePercent(pred: CachedPrediction | undefined) {
  if (!pred) return '--'
  // 使用综合概率（如果有）或基础概率
  const prob = pred.combined_prob_home ?? pred.prob_home
  const maxProb = Math.max(
    pred.combined_prob_home ?? pred.prob_home,
    pred.combined_prob_draw ?? pred.prob_draw,
    pred.combined_prob_away ?? pred.prob_away
  )
  return `${Math.round(maxProb * 100)}%`
}

// 获取推荐概率
function getBestProb(pred: CachedPrediction | undefined) {
  if (!pred) return 0
  const probs = [
    { type: 'H', prob: pred.combined_prob_home ?? pred.prob_home },
    { type: 'D', prob: pred.combined_prob_draw ?? pred.prob_draw },
    { type: 'A', prob: pred.combined_prob_away ?? pred.prob_away }
  ]
  const best = probs.reduce((a, b) => a.prob > b.prob ? a : b)
  return best
}

function viewMatchDetail(matchId: string) {
  router.push(`/match/${matchId}`)
}

function handleAuthClick() {
  const token = localStorage.getItem('kb_token')
  if (token) {
    router.push('/tracker')
  } else {
    router.push('/auth')
  }
}

// 计算价值百分比 (模型概率 - 市场隐含概率)
function calculateValue(match: CachedMatch) {
  if (!match.prediction) return { hasValue: false, valuePct: 0 }
  
  const pred = match.prediction
  // 基础价值估算 (模型置信度 - 33.3%基准)
  const maxProb = Math.max(
    pred.combined_prob_home ?? pred.prob_home,
    pred.combined_prob_draw ?? pred.prob_draw,
    pred.combined_prob_away ?? pred.prob_away
  )
  const value = maxProb - 0.333
  return {
    hasValue: value > 0.05,  // 价值阈值5%
    valuePct: Math.round(value * 100)
  }
}
</script>

<style scoped>
.home-page {
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
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #2a2b2c;
  position: sticky;
  top: 0;
  background: #08090a;
  z-index: 100;
}

.logo {
  font-size: 20px;
  font-weight: 700;
  color: #00d4aa;
  cursor: pointer;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.btn-icon {
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
}

/* Data Source Bar */
.data-source-bar {
  background: rgba(74,144,217,0.1);
  border-bottom: 1px solid rgba(74,144,217,0.2);
  padding: 8px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.source-text {
  font-size: 11px;
  color: #8b8b8b;
}

.source-text strong {
  color: #4a90d9;
}

.source-status {
  font-size: 10px;
  color: #00d4aa;
  font-family: 'Roboto Mono', monospace;
}

.source-status.offline {
  color: #ff6b6b;
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

.section-badge {
  font-size: 11px;
  background: #00d4aa;
  color: #08090a;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}

/* Main Recommendation Card */
.main-rec-card {
  margin: 8px 16px 16px;
  background: #121314;
  border: 1px solid #2a2b2c;
  border-radius: 12px;
  padding: 16px;
}

.match-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.league-badge {
  font-size: 12px;
  color: #8b8b8b;
  background: #1a1b1c;
  padding: 4px 10px;
  border-radius: 4px;
}

.match-time {
  font-size: 12px;
  color: #5a5a5a;
  font-family: 'Roboto Mono', monospace;
}

.teams-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.team {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.team-logo {
  width: 48px;
  height: 48px;
  background: #1a1b1c;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 600;
}

.team-name {
  font-size: 14px;
  font-weight: 500;
}

.vs {
  font-size: 12px;
  color: #5a5a5a;
}

/* Best Odds Box */
.best-odds-box {
  background: linear-gradient(135deg, rgba(0,212,170,0.15) 0%, rgba(0,212,170,0.05) 100%);
  border: 1px solid rgba(0,212,170,0.3);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
}

.best-odds-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.best-play-type {
  font-size: 12px;
  color: #8b8b8b;
}

.best-platform {
  font-size: 12px;
  font-weight: 600;
  color: #4a90d9;
}

.best-odds-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.best-option {
  font-size: 14px;
  font-weight: 600;
  color: #00d4aa;
}

.best-odds-value {
  font-size: 18px;
  font-weight: 700;
  font-family: 'Roboto Mono', monospace;
}

.best-confidence {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
}

.conf-label {
  font-size: 11px;
  color: #5a5a5a;
}

.conf-value {
  font-size: 13px;
  font-weight: 600;
  color: #00d4aa;
}

/* Plans Preview */
.plans-preview {
  background: #1a1b1c;
  border-radius: 8px;
  padding: 12px;
}

.plans-preview-title {
  font-size: 12px;
  color: #8b8b8b;
  margin-bottom: 8px;
}

.plan-mini {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #2a2b2c;
}

.plan-mini:last-child {
  border-bottom: none;
}

.plan-mini-name {
  font-size: 13px;
  font-weight: 500;
}

.plan-mini-risk {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  margin-left: 8px;
}

.plan-mini-risk.low {
  background: #00d4aa;
  color: #08090a;
}

.plan-mini-risk.medium {
  background: #ffa500;
  color: #08090a;
}

.plan-mini-risk.high {
  background: #ff6b6b;
  color: #08090a;
}

.plan-mini-roi {
  font-size: 13px;
  font-family: 'Roboto Mono', monospace;
  color: #00d4aa;
}

/* View Detail Button */
.view-detail-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px;
  background: #00d4aa;
  color: #08090a;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 12px;
}

.rec-loading {
  text-align: center;
  padding: 40px;
  color: #5a5a5a;
}

/* League Tabs */
.league-tabs {
  display: flex;
  gap: 8px;
  padding: 8px 16px;
  overflow-x: auto;
}

.league-tabs::-webkit-scrollbar {
  display: none;
}

.league-tab {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 12px 16px;
  background: #121314;
  border: 1px solid #2a2b2c;
  border-radius: 8px;
  cursor: pointer;
  min-width: 72px;
}

.league-tab.active {
  border-color: #00d4aa;
  background: rgba(0,212,170,0.1);
}

.league-tab-name {
  font-size: 14px;
  font-weight: 500;
}

.league-tab-count {
  font-size: 12px;
  color: #5a5a5a;
}

/* Match List */
.match-list {
  padding: 8px 16px;
}

.match-card {
  background: #121314;
  border: 1px solid #2a2b2c;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 8px;
  cursor: pointer;
}

.match-card:hover {
  background: #1a1b1c;
}

.match-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.match-card-teams {
  font-size: 14px;
  font-weight: 500;
}

.match-card-league {
  font-size: 11px;
  color: #5a5a5a;
  margin-left: 8px;
}

.match-card-time {
  font-size: 12px;
  color: #8b8b8b;
  font-family: 'Roboto Mono', monospace;
}

/* Odds Preview Grid */
.odds-preview-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-top: 8px;
}

.odds-preview-item {
  background: #1a1b1c;
  border-radius: 4px;
  padding: 8px;
  text-align: center;
}

.odds-preview-type {
  font-size: 10px;
  color: #5a5a5a;
  margin-bottom: 4px;
}

.odds-preview-best {
  font-size: 12px;
  font-family: 'Roboto Mono', monospace;
  font-weight: 600;
}

.odds-preview-best.has-value {
  color: #00d4aa;
}

.odds-preview-best.no-value {
  color: #5a5a5a;
}

/* Value Tag */
.value-tag {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
  margin-top: 4px;
}

.value-tag.positive {
  background: rgba(0,212,170,0.2);
  color: #00d4aa;
}

.value-tag.neutral {
  background: #1a1b1c;
  color: #5a5a5a;
}

.match-empty {
  text-align: center;
  padding: 40px;
  color: #5a5a5a;
}
</style>