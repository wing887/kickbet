<template>
  <div class="fixed inset-0 bg-kb-bg/90 backdrop-blur-lg z-50 flex items-center justify-center p-4">
    <div class="kb-card w-full max-w-md max-h-[80vh] overflow-y-auto">
      <!-- 头部 -->
      <div class="p-4 border-b border-kb-border flex items-center justify-between">
        <div>
          <span class="kb-tag kb-tag-neutral mb-2">{{ match.league_name }}</span>
          <h2 class="text-lg font-semibold mt-1">
            {{ match.home_team }} vs {{ match.away_team }}
          </h2>
        </div>
        <button @click="$emit('close')" class="text-kb-text-secondary hover:text-white">
          ✕
        </button>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="p-8 text-center text-kb-text-muted">
        分析中...
      </div>

      <!-- 分析结果 -->
      <div v-else-if="analysisData" class="p-4 space-y-4">
        <!-- API限流警告 -->
        <div v-if="analysisData.warning" class="kb-card p-3 border-kb-warning/30 text-kb-warning text-sm">
          {{ analysisData.warning }}
        </div>
        
        <!-- 概率预测 -->
        <section>
          <h3 class="text-sm text-kb-text-secondary mb-2">胜平负概率</h3>
          <div class="grid grid-cols-3 gap-2">
            <div class="kb-card p-3 text-center">
              <div class="text-xs text-kb-text-muted mb-1">主胜</div>
              <div class="text-lg font-semibold text-kb-success">
                {{ analysisData.prediction.home_win_prob }}%
              </div>
              <div class="text-xs text-kb-text-secondary">{{ analysisData.odds?.home || '--' }}</div>
            </div>
            <div class="kb-card p-3 text-center">
              <div class="text-xs text-kb-text-muted mb-1">平局</div>
              <div class="text-lg font-semibold text-kb-warning">
                {{ analysisData.prediction.draw_prob }}%
              </div>
              <div class="text-xs text-kb-text-secondary">{{ analysisData.odds?.draw || '--' }}</div>
            </div>
            <div class="kb-card p-3 text-center">
              <div class="text-xs text-kb-text-muted mb-1">客胜</div>
              <div class="text-lg font-semibold text-kb-danger">
                {{ analysisData.prediction.away_win_prob }}%
              </div>
              <div class="text-xs text-kb-text-secondary">{{ analysisData.odds?.away || '--' }}</div>
            </div>
          </div>
        </section>

        <!-- Poisson 模拟 -->
        <section>
          <h3 class="text-sm text-kb-text-secondary mb-2">Poisson模拟 ({{ analysisData.poisson_simulation.iterations }}次)</h3>
          <div class="kb-card p-3">
            <div class="flex justify-between text-sm">
              <span>最可能比分</span>
              <span class="font-medium">{{ analysisData.poisson_simulation.most_likely_scores[0]?.score || '--' }}</span>
            </div>
          </div>
        </section>

        <!-- Kelly Criterion -->
        <section v-if="analysisData.kelly_criterion">
          <h3 class="text-sm text-kb-text-secondary mb-2">价值评估</h3>
          <div class="space-y-2">
            <div v-if="analysisData.kelly_criterion.home.value" class="kb-card p-3 border-kb-success/30">
              <div class="flex justify-between">
                <span class="text-kb-success">主胜有价值</span>
                <span>Half-Kelly: {{ (analysisData.kelly_criterion.home.half_kelly * 100).toFixed(1) }}%</span>
              </div>
            </div>
            <div v-if="analysisData.kelly_criterion.draw.value" class="kb-card p-3 border-kb-warning/30">
              <div class="flex justify-between">
                <span class="text-kb-warning">平局有价值</span>
                <span>Half-Kelly: {{ (analysisData.kelly_criterion.draw.half_kelly * 100).toFixed(1) }}%</span>
              </div>
            </div>
            <div v-if="analysisData.kelly_criterion.away.value" class="kb-card p-3 border-kb-danger/30">
              <div class="flex justify-between">
                <span class="text-kb-danger">客胜有价值</span>
                <span>Half-Kelly: {{ (analysisData.kelly_criterion.away.half_kelly * 100).toFixed(1) }}%</span>
              </div>
            </div>
            <div v-if="!hasValueBet" class="kb-card p-3 text-center text-kb-text-muted">
              当前赔率无明显价值投注机会
            </div>
          </div>
        </section>

        <!-- 投注建议 -->
        <section v-if="analysisData.recommended_bets">
          <h3 class="text-sm text-kb-text-secondary mb-2">投注建议</h3>
          <div class="space-y-2">
            <div class="kb-card p-3">
              <div class="text-xs text-kb-text-muted mb-1">保守方案</div>
              <div class="font-medium">{{ analysisData.recommended_bets.conservative.type }}</div>
              <div class="text-sm text-kb-text-secondary">
                赔率 {{ analysisData.recommended_bets.conservative.odds }} · 
                {{ analysisData.recommended_bets.conservative.stake_pct }}%资金
              </div>
            </div>
            <div class="kb-card p-3 border-kb-accent/30">
              <div class="text-xs text-kb-accent mb-1">平衡方案 (推荐)</div>
              <div class="font-medium">{{ analysisData.recommended_bets.balanced.type }}</div>
              <div class="text-sm text-kb-text-secondary">
                赔率 {{ analysisData.recommended_bets.balanced.odds }} · 
                {{ analysisData.recommended_bets.balanced.stake_pct }}%资金
              </div>
            </div>
            <div class="kb-card p-3">
              <div class="text-xs text-kb-text-muted mb-1">激进方案</div>
              <div class="font-medium">{{ analysisData.recommended_bets.aggressive.type }}</div>
              <div class="text-sm text-kb-text-secondary">
                赔率 {{ analysisData.recommended_bets.aggressive.odds }} · 
                {{ analysisData.recommended_bets.aggressive.stake_pct }}%资金
              </div>
            </div>
          </div>
        </section>
      </div>

      <!-- 错误状态 -->
      <div v-else class="p-8 text-center text-kb-danger">
        {{ error }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { analysis } from '../../api'
import type { Match, AnalysisResponse } from '../../api'

const props = defineProps<{ match: Match }>()
const emit = defineEmits(['close'])

const loading = ref(true)
const error = ref('')
const analysisData = ref<AnalysisResponse | null>(null)

const hasValueBet = computed(() => {
  if (!analysisData.value?.kelly_criterion) return false
  return analysisData.value.kelly_criterion.home.value ||
         analysisData.value.kelly_criterion.draw.value ||
         analysisData.value.kelly_criterion.away.value
})

onMounted(async () => {
  try {
    loading.value = true
    analysisData.value = await analysis.get(props.match.match_id)
  } catch (e: any) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
})
</script>