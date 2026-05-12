<template>
  <nav class="footer-nav">
    <div 
      :class="['nav-item', { active: active === 'home' }]" 
      @click="$router.push('/')"
    >
      <div class="nav-icon">🏠</div>
      <span class="nav-label">首页</span>
    </div>
    <div 
      :class="['nav-item', { active: active === 'matches' }]" 
      @click="$router.push('/matches')"
    >
      <div class="nav-icon">📅</div>
      <span class="nav-label">比赛</span>
    </div>
    <div 
      :class="['nav-item', { active: active === 'combo' }]" 
      @click="$router.push('/combo')"
    >
      <div class="nav-icon">📊</div>
      <span class="nav-label">组合</span>
    </div>
    <div 
      :class="['nav-item', { active: active === 'tracker' }]" 
      @click="$router.push('/tracker')"
    >
      <div class="nav-icon">📈</div>
      <span class="nav-label">追踪</span>
    </div>
  </nav>
</template>

<script setup lang="ts">
defineProps<{
  active: 'home' | 'matches' | 'combo' | 'tracker'
}>()
</script>

<style scoped>
.footer-nav {
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 420px;
  background: #121314;
  border-top: 1px solid #2a2b2c;
  display: flex;
  justify-content: space-around;
  padding: 12px 0;
  z-index: 100;
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  color: #5a5a5a;
  cursor: pointer;
}

.nav-item.active {
  color: #00d4aa;
}

.nav-icon {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-label {
  font-size: 11px;
}
</style>