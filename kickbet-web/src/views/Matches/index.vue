<template>
  <div class="min-h-screen bg-kb-bg pb-20">
    <!-- 头部 -->
    <header class="px-4 py-4 border-b border-kb-border sticky top-0 bg-kb-bg/90 backdrop-blur-lg">
      <h1 class="text-xl font-semibold">比赛列表</h1>
    </header>

    <!-- 联赛筛选 -->
    <section class="px-4 py-3 border-b border-kb-border">
      <div class="flex gap-2 overflow-x-auto">
        <button 
          @click="currentLeague = ''" 
          :class="currentLeague === '' ? 'kb-btn-primary' : 'kb-btn-secondary'"
          class="kb-btn text-sm whitespace-nowrap"
        >
          全部
        </button>
        <button 
          v-for="league in leagues" 
          :key="league.code"
          @click="currentLeague = league.code"
          :class="currentLeague === league.code ? 'kb-btn-primary' : 'kb-btn-secondary'"
          class="kb-btn text-sm whitespace-nowrap"
        >
          {{ league.name }}
        </button>
      </div>
    </section>

    <!-- 比赛列表 -->
    <section class="px-4 py-4">
      <div v-if="loading" class="text-center py-8 text-kb-text-muted">
        加载中...
      </div>
      
      <div v-else-if="matchList.length === 0" class="text-center py-8 text-kb-text-muted">
        暂无比赛
      </div>
      
      <div v-else class="space-y-3">
        <div 
          v-for="match in matchList" 
          :key="match.match_id"
          class="kb-card kb-card-hover p-4 cursor-pointer"
          @click="showAnalysis(match)"
        >
          <div class="flex items-center justify-between mb-2">
            <span class="kb-tag kb-tag-neutral">{{ match.league_name }}</span>
            <span class="text-sm text-kb-text-secondary">{{ formatDate(match.match_date) }}</span>
          </div>
          <div class="text-lg font-medium">
            {{ match.home_team }} vs {{ match.away_team }}
          </div>
          <div class="mt-2 text-sm text-kb-text-muted">
            点击查看预测分析
          </div>
        </div>
      </div>
    </section>

    <!-- 分析弹窗 -->
    <AnalysisModal 
      v-if="selectedMatch"
      :match="selectedMatch"
      @close="selectedMatch = null"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { matches } from '../../api'
import type { Match, AnalysisResponse } from '../../api'
import AnalysisModal from '../../components/match/AnalysisModal.vue'

const loading = ref(false)
const matchList = ref<Match[]>([])
const currentLeague = ref('')
const selectedMatch = ref<Match | null>(null)

const leagues = [
  { code: 'PL', name: '英超' },
  { code: 'BL1', name: '德甲' },
  { code: 'PD', name: '西甲' },
  { code: 'SA', name: '意甲' },
  { code: 'FL1', name: '法甲' }
]

onMounted(loadMatches)
watch(currentLeague, loadMatches)

async function loadMatches() {
  loading.value = true
  try {
    const league = currentLeague.value || undefined
    const result = await matches.list(3, league)
    matchList.value = result.matches
  } catch (e) {
    console.error('Failed to load matches:', e)
  } finally {
    loading.value = false
  }
}

function formatDate(dateStr: string) {
  const date = new Date(dateStr)
  const today = new Date()
  const tomorrow = new Date(today)
  tomorrow.setDate(tomorrow.getDate() + 1)
  
  if (date.toDateString() === today.toDateString()) return '今天'
  if (date.toDateString() === tomorrow.toDateString()) return '明天'
  
  return `${date.getMonth() + 1}/${date.getDate()}`
}

function showAnalysis(match: Match) {
  selectedMatch.value = match
}
</script>