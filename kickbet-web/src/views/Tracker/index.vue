<template>
  <div class="tracker-page">
    <!-- Header -->
    <header class="header">
      <span class="header-title">投注追踪</span>
      <div class="header-actions">
        <div class="btn-icon">📊</div>
        <div class="btn-icon" @click="exportData">↓</div>
      </div>
    </header>
    
    <!-- Stats Overview -->
    <div class="stats-card">
      <div class="stats-header">
        <span class="stats-period">本月统计</span>
        <span class="stats-filter" @click="showDatePicker = true">{{ currentMonth }}</span>
      </div>
      <div class="stats-grid">
        <div class="stat-item">
          <span :class="['stat-value', stats.totalProfit >= 0 ? 'positive' : 'negative']">
            {{ stats.totalProfit >= 0 ? '+' : '' }}¥{{ stats.totalProfit }}
          </span>
          <span class="stat-label">总盈亏</span>
          <span class="stat-subvalue">{{ stats.totalProfit >= 0 ? '盈利' : '亏损' }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-value neutral">{{ stats.totalBets }}</span>
          <span class="stat-label">总投注</span>
          <span class="stat-subvalue">¥{{ stats.totalStake }}本金</span>
        </div>
        <div class="stat-item">
          <span :class="['stat-value', stats.roi >= 0 ? 'positive' : 'negative']">
            {{ stats.roi >= 0 ? '+' : '' }}{{ stats.roi }}%
          </span>
          <span class="stat-label">ROI</span>
          <span class="stat-subvalue">{{ stats.roi >= 30 ? '表现良好' : stats.roi >= 0 ? '表现平稳' : '需调整策略' }}</span>
        </div>
      </div>
    </div>
    
    <!-- ROI Chart -->
    <div class="chart-section">
      <div class="chart-title">盈亏趋势</div>
      <div class="mini-chart">
        <div 
          v-for="(bar, idx) in chartBars" 
          :key="idx"
          :class="['chart-bar', { negative: bar.value < 0 }]"
          :style="{ height: Math.abs(bar.height) + 'px' }"
        ></div>
      </div>
      <div class="chart-labels">
        <span>第1周</span>
        <span>第2周</span>
        <span>第3周</span>
        <span>第4周</span>
      </div>
    </div>
    
    <!-- Accuracy Panel -->
    <div class="accuracy-section">
      <div class="accuracy-title">预测准确率</div>
      <div class="accuracy-grid">
        <div class="accuracy-item">
          <span class="accuracy-value" style="color: #00d4aa;">{{ accuracy.total }}%</span>
          <span class="accuracy-label">总准确率</span>
          <span class="accuracy-sublabel">{{ accuracy.wins }}胜/{{ accuracy.losses }}负</span>
        </div>
        <div class="accuracy-item">
          <span class="accuracy-value" style="color: #4a90d9;">{{ accuracy.highConf }}%</span>
          <span class="accuracy-label">高置信度</span>
          <span class="accuracy-sublabel">置信度>70%</span>
        </div>
        <div class="accuracy-item">
          <span class="accuracy-value" style="color: #ffa500;">{{ accuracy.midConf }}%</span>
          <span class="accuracy-label">中置信度</span>
          <span class="accuracy-sublabel">置信度50-70%</span>
        </div>
        <div class="accuracy-item">
          <span class="accuracy-value" style="color: #ff6b6b;">{{ accuracy.lowConf }}%</span>
          <span class="accuracy-label">低置信度</span>
          <span class="accuracy-sublabel">置信度<50%</span>
        </div>
      </div>
    </div>
    
    <!-- Records List -->
    <div class="records-section">
      <div class="records-header">
        <span class="records-title">投注记录</span>
        <div class="records-tabs">
          <span 
            :class="['record-tab', { active: recordFilter === 'all' }]"
            @click="recordFilter = 'all'"
          >全部</span>
          <span 
            :class="['record-tab', { active: recordFilter === 'win' }]"
            @click="recordFilter = 'win'"
          >胜</span>
          <span 
            :class="['record-tab', { active: recordFilter === 'loss' }]"
            @click="recordFilter = 'loss'"
          >负</span>
          <span 
            :class="['record-tab', { active: recordFilter === 'pending' }]"
            @click="recordFilter = 'pending'"
          >待定</span>
        </div>
      </div>
      
      <div 
        v-for="record in filteredRecords" 
        :key="record.id"
        class="record-card"
      >
        <div class="record-header">
          <span class="record-match">{{ record.match }}</span>
          <span class="record-date">{{ record.date }}</span>
        </div>
        <div class="record-body">
          <div class="record-details">
            <span class="record-bet-type">{{ record.betType }}</span>
            <span class="record-odds">赔率: {{ record.odds }} | 金额: ¥{{ record.stake }}</span>
          </div>
          <div class="record-result">
            <span 
              v-if="record.status !== 'pending'"
              :class="['record-profit', record.profit >= 0 ? 'positive' : 'negative']"
            >
              {{ record.profit >= 0 ? '+' : '' }}¥{{ record.profit }}
            </span>
            <span v-else class="record-profit">待定</span>
            <span :class="['record-status', record.status]">
              {{ record.status === 'win' ? '胜' : record.status === 'loss' ? '负' : '待开奖' }}
            </span>
          </div>
        </div>
      </div>
      
      <div class="add-record-btn" @click="showAddRecord = true">
        <span>+ 添加记录</span>
      </div>
    </div>
    
    <!-- Add Record Modal -->
    <div v-if="showAddRecord" class="add-record-modal">
      <div class="modal-card">
        <div class="modal-header">
          <span class="modal-title">添加投注记录</span>
          <span class="modal-close" @click="showAddRecord = false">×</span>
        </div>
        <div class="modal-body">
          <div class="modal-field">
            <label>比赛</label>
            <input v-model="newRecord.match" type="text" placeholder="曼城 vs 布伦特福德">
          </div>
          <div class="modal-field">
            <label>投注类型</label>
            <input v-model="newRecord.betType" type="text" placeholder="主胜">
          </div>
          <div class="modal-field">
            <label>赔率</label>
            <input v-model.number="newRecord.odds" type="number" placeholder="1.42">
          </div>
          <div class="modal-field">
            <label>金额</label>
            <input v-model.number="newRecord.stake" type="number" placeholder="60">
          </div>
        </div>
        <div class="modal-actions">
          <button class="modal-btn cancel" @click="showAddRecord = false">取消</button>
          <button class="modal-btn save" @click="addRecord">保存</button>
        </div>
      </div>
    </div>
    
    <!-- Footer -->
    <BottomNav :active="'tracker'" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import BottomNav from '../../components/common/BottomNav.vue'

const currentMonth = ref('2026年5月')
const recordFilter = ref<'all' | 'win' | 'loss' | 'pending'>('all')
const showAddRecord = ref(false)
const showDatePicker = ref(false)

const stats = ref({
  totalProfit: 850,
  totalBets: 12,
  totalStake: 2000,
  roi: 42.5
})

const accuracy = ref({
  total: 67,
  wins: 8,
  losses: 4,
  highConf: 75,
  midConf: 58,
  lowConf: 30
})

const chartBars = ref([
  { value: 30, height: 30 },
  { value: 20, height: 20 },
  { value: -15, height: 15 },
  { value: 45, height: 45 },
  { value: -10, height: 10 },
  { value: 55, height: 55 },
  { value: 40, height: 40 }
])

const records = ref<BetRecord[]>([
  { id: 1, match: '曼城 vs 布伦特福德', date: '05-08 21:00', betType: '主胜', odds: 1.42, stake: 60, profit: 25, status: 'win' },
  { id: 2, match: '山东泰山 vs 浙江队', date: '05-07 19:35', betType: '主胜', odds: 1.65, stake: 40, profit: 26, status: 'win' },
  { id: 3, match: '川崎前锋 vs 浦和红钻', date: '05-06 15:00', betType: '平局', odds: 3.20, stake: 15, profit: -15, status: 'loss' },
  { id: 4, match: '上海申花 vs 河南嵩山', date: '05-10 19:35', betType: '主胜', odds: 2.10, stake: 50, profit: 0, status: 'pending' }
])

const newRecord = ref({
  match: '',
  betType: '',
  odds: 0,
  stake: 0
})

interface BetRecord {
  id: number
  match: string
  date: string
  betType: string
  odds: number
  stake: number
  profit: number
  status: 'win' | 'loss' | 'pending'
}

const filteredRecords = computed(() => {
  if (recordFilter.value === 'all') return records.value
  return records.value.filter(r => r.status === recordFilter.value)
})

function addRecord() {
  const today = new Date()
  const dateStr = `${today.getMonth() + 1}-${today.getDate()} ${today.getHours()}:${today.getMinutes()}`
  
  records.value.unshift({
    id: Date.now(),
    match: newRecord.value.match,
    date: dateStr,
    betType: newRecord.value.betType,
    odds: newRecord.value.odds,
    stake: newRecord.value.stake,
    profit: 0,
    status: 'pending'
  })
  
  showAddRecord.value = false
  newRecord.value = { match: '', betType: '', odds: 0, stake: 0 }
}

function exportData() {
  // 简单导出CSV
  const csv = records.value.map(r => `${r.match},${r.betType},${r.odds},${r.stake},${r.profit},${r.status}`).join('\n')
  console.log('Export CSV:', csv)
}
</script>

<style scoped>
.tracker-page {
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
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid #2a2b2c;
  position: sticky;
  top: 0;
  background: #08090a;
  z-index: 100;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
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

/* Stats Card */
.stats-card {
  margin: 16px;
  background: #121314;
  border: 1px solid #2a2b2c;
  border-radius: 12px;
  padding: 16px;
}

.stats-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.stats-period {
  font-size: 14px;
  font-weight: 600;
}

.stats-filter {
  font-size: 12px;
  color: #8b8b8b;
  background: #1a1b1c;
  padding: 4px 12px;
  border-radius: 4px;
  cursor: pointer;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  font-family: 'Roboto Mono', monospace;
}

.stat-value.positive { color: #00d4aa; }
.stat-value.negative { color: #ff6b6b; }
.stat-value.neutral { color: #ffffff; }

.stat-label {
  font-size: 12px;
  color: #5a5a5a;
}

.stat-subvalue {
  font-size: 11px;
  color: #8b8b8b;
}

/* Chart Section */
.chart-section {
  margin: 16px;
  background: #121314;
  border: 1px solid #2a2b2c;
  border-radius: 12px;
  padding: 16px;
}

.chart-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
}

.mini-chart {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  height: 80px;
  padding: 8px 0;
}

.chart-bar {
  width: 20px;
  background: #00d4aa;
  border-radius: 2px 2px 0 0;
  min-height: 4px;
}

.chart-bar.negative {
  background: #ff6b6b;
}

.chart-labels {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  color: #5a5a5a;
  margin-top: 8px;
}

/* Accuracy Section */
.accuracy-section {
  margin: 16px;
  background: #121314;
  border: 1px solid #2a2b2c;
  border-radius: 12px;
  padding: 16px;
}

.accuracy-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
}

.accuracy-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.accuracy-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: #1a1b1c;
  border-radius: 8px;
}

.accuracy-value {
  font-size: 20px;
  font-weight: 700;
  font-family: 'Roboto Mono', monospace;
}

.accuracy-label {
  font-size: 11px;
  color: #5a5a5a;
}

.accuracy-sublabel {
  font-size: 10px;
  color: #8b8b8b;
}

/* Records Section */
.records-section {
  margin: 16px;
}

.records-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.records-title {
  font-size: 14px;
  font-weight: 600;
}

.records-tabs {
  display: flex;
  gap: 8px;
}

.record-tab {
  font-size: 12px;
  padding: 6px 12px;
  background: #121314;
  border: 1px solid #2a2b2c;
  border-radius: 4px;
  color: #8b8b8b;
  cursor: pointer;
}

.record-tab.active {
  background: #4a90d9;
  color: #08090a;
  border-color: #4a90d9;
}

/* Record Card */
.record-card {
  background: #121314;
  border: 1px solid #2a2b2c;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 8px;
}

.record-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.record-match {
  font-size: 14px;
  font-weight: 500;
}

.record-date {
  font-size: 11px;
  color: #5a5a5a;
  font-family: 'Roboto Mono', monospace;
}

.record-body {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.record-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.record-bet-type {
  font-size: 12px;
  color: #8b8b8b;
}

.record-odds {
  font-size: 12px;
  font-family: 'Roboto Mono', monospace;
  color: #5a5a5a;
}

.record-result {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.record-profit {
  font-size: 16px;
  font-weight: 700;
  font-family: 'Roboto Mono', monospace;
}

.record-profit.positive { color: #00d4aa; }
.record-profit.negative { color: #ff6b6b; }

.record-status {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
}

.record-status.win {
  background: rgba(0,212,170,0.2);
  color: #00d4aa;
}

.record-status.loss {
  background: rgba(255,107,107,0.2);
  color: #ff6b6b;
}

.record-status.pending {
  background: rgba(74,144,217,0.2);
  color: #4a90d9;
}

.add-record-btn {
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

.add-record-btn:hover {
  border-color: #4a90d9;
  color: #4a90d9;
}

/* Add Record Modal */
.add-record-modal {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-card {
  background: #121314;
  border: 1px solid #2a2b2c;
  border-radius: 12px;
  padding: 24px;
  max-width: 320px;
  width: 90%;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.modal-title {
  font-size: 16px;
  font-weight: 600;
}

.modal-close {
  font-size: 20px;
  color: #5a5a5a;
  cursor: pointer;
}

.modal-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.modal-field label {
  font-size: 13px;
  color: #8b8b8b;
  margin-bottom: 6px;
}

.modal-field input {
  width: 100%;
  background: #0d0e0f;
  border: 1px solid #2a2b2c;
  border-radius: 8px;
  padding: 12px;
  font-size: 14px;
  color: #ffffff;
}

.modal-actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}

.modal-btn {
  flex: 1;
  padding: 12px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  border: none;
}

.modal-btn.cancel {
  background: #1a1b1c;
  color: #8b8b8b;
}

.modal-btn.save {
  background: #4a90d9;
  color: #08090a;
}
</style>