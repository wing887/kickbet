<template>
  <div class="subscribe-page">
    <!-- Header -->
    <header class="header">
      <div class="back-btn" @click="$router.push('/')">←</div>
      <span class="header-title">升级会员</span>
    </header>
    
    <!-- Hero -->
    <div class="hero">
      <div class="hero-icon">⭐</div>
      <div class="hero-title">解锁完整功能</div>
      <div class="hero-desc">升级会员，获得无限预测分析、智能组合建议和完整投注追踪</div>
    </div>
    
    <!-- Pricing -->
    <div class="pricing-section">
      <div class="pricing-card">
        <div class="pricing-header">
          <div class="pricing-tier">免费版</div>
          <div class="pricing-subtitle">基础体验</div>
        </div>
        <div class="pricing-price">
          <span class="price-currency">¥</span>
          <span class="price-value">0</span>
          <span class="price-period">永久免费</span>
        </div>
        <div class="features-list">
          <div class="feature-item">
            <span class="feature-icon">✓</span>
            <span class="feature-text">每日3场L2分析</span>
          </div>
          <div class="feature-item">
            <span class="feature-icon">✓</span>
            <span class="feature-text">首页L4推荐</span>
          </div>
          <div class="feature-item">
            <span class="feature-icon disabled">-</span>
            <span class="feature-text disabled">L3进阶分析</span>
          </div>
          <div class="feature-item">
            <span class="feature-icon disabled">-</span>
            <span class="feature-text disabled">组合投注建议</span>
          </div>
          <div class="feature-item">
            <span class="feature-icon disabled">-</span>
            <span class="feature-text disabled">投注追踪系统</span>
          </div>
        </div>
      </div>
      
      <div class="pricing-card premium">
        <div class="pricing-badge">推荐</div>
        <div class="pricing-header">
          <div class="pricing-tier">会员版</div>
          <div class="pricing-subtitle">完整功能解锁</div>
        </div>
        <div class="pricing-price">
          <span class="price-currency">¥</span>
          <span class="price-value">{{ price }}</span>
          <span class="price-period">/月</span>
        </div>
        <div class="features-list">
          <div class="feature-item">
            <span class="feature-icon">✓</span>
            <span class="feature-text">无限查看所有预测</span>
          </div>
          <div class="feature-item">
            <span class="feature-icon">✓</span>
            <span class="feature-text">L3进阶分析（完整Kelly+风险提示）</span>
          </div>
          <div class="feature-item">
            <span class="feature-icon">✓</span>
            <span class="feature-text">智能组合投注建议</span>
          </div>
          <div class="feature-item">
            <span class="feature-icon">✓</span>
            <span class="feature-text">完整投注追踪系统</span>
          </div>
          <div class="feature-item">
            <span class="feature-icon">✓</span>
            <span class="feature-text">赔率变动AI分析</span>
          </div>
          <div class="feature-item">
            <span class="feature-icon">✓</span>
            <span class="feature-text">高级数据可视化</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Comparison Table -->
    <div class="comparison-section">
      <div class="comparison-title">功能对比</div>
      <div class="comparison-table">
        <div class="comparison-row">
          <span class="comparison-feature">每日预测查看</span>
          <span class="comparison-free"><span class="comparison-limited">3场</span></span>
          <span class="comparison-premium"><span class="comparison-check">∞</span></span>
        </div>
        <div class="comparison-row">
          <span class="comparison-feature">L2基础分析</span>
          <span class="comparison-free"><span class="comparison-check">✓</span></span>
          <span class="comparison-premium"><span class="comparison-check">✓</span></span>
        </div>
        <div class="comparison-row">
          <span class="comparison-feature">L3进阶分析</span>
          <span class="comparison-free"><span class="comparison-x">✗</span></span>
          <span class="comparison-premium"><span class="comparison-check">✓</span></span>
        </div>
        <div class="comparison-row">
          <span class="comparison-feature">组合投注建议</span>
          <span class="comparison-free"><span class="comparison-x">✗</span></span>
          <span class="comparison-premium"><span class="comparison-check">✓</span></span>
        </div>
        <div class="comparison-row">
          <span class="comparison-feature">投注追踪</span>
          <span class="comparison-free"><span class="comparison-limited">基础</span></span>
          <span class="comparison-premium"><span class="comparison-check">完整</span></span>
        </div>
        <div class="comparison-row">
          <span class="comparison-feature">赔率变动分析</span>
          <span class="comparison-free"><span class="comparison-x">✗</span></span>
          <span class="comparison-premium"><span class="comparison-check">✓</span></span>
        </div>
      </div>
    </div>
    
    <!-- Subscribe Button -->
    <button class="subscribe-btn" @click="handleSubscribe">
      <span>立即升级会员</span>
    </button>
    
    <!-- Guarantee -->
    <div class="guarantee-section">
      <div class="guarantee-icon">🛡️</div>
      <div>
        <div class="guarantee-text">7天无理由退款保障</div>
        <div class="guarantee-desc">不满意可全额退款，零风险体验</div>
      </div>
    </div>
    
    <!-- Terms -->
    <div class="terms-section">
      <div class="terms-text">
        订阅即表示同意 <span class="terms-link">服务条款</span> 和 <span class="terms-link">隐私政策</span><br>
        会员费用每月自动续费，可随时取消
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const price = ref(99)

function handleSubscribe() {
  // 模拟支付流程
  alert('支付功能开发中，请联系客服开通会员')
}
</script>

<style scoped>
.subscribe-page {
  font-family: 'Inter', -apple-system, sans-serif;
  background: #08090a;
  color: #ffffff;
  min-height: 100vh;
  max-width: 420px;
  margin: 0 auto;
  padding-bottom: 40px;
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

/* Hero */
.hero {
  padding: 24px 16px;
  text-align: center;
}

.hero-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.hero-title {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 8px;
}

.hero-desc {
  font-size: 14px;
  color: #8b8b8b;
  line-height: 1.6;
}

/* Pricing */
.pricing-section {
  margin: 16px;
}

.pricing-card {
  background: #121314;
  border: 1px solid #2a2b2c;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
  position: relative;
  overflow: hidden;
}

.pricing-card.premium {
  border-color: #8b5cf6;
  background: linear-gradient(135deg, #121314 0%, rgba(139,92,246,0.1) 100%);
}

.pricing-badge {
  position: absolute;
  top: 0;
  right: 0;
  background: #8b5cf6;
  color: #08090a;
  font-size: 11px;
  padding: 6px 12px;
  border-radius: 0 12px 0 8px;
}

.pricing-header {
  margin-bottom: 16px;
}

.pricing-tier {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 4px;
}

.pricing-subtitle {
  font-size: 12px;
  color: #8b8b8b;
}

.pricing-price {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 16px;
}

.price-currency {
  font-size: 20px;
  font-weight: 600;
}

.price-value {
  font-size: 36px;
  font-weight: 700;
  font-family: 'Roboto Mono', monospace;
}

.price-period {
  font-size: 14px;
  color: #8b8b8b;
}

/* Features */
.features-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
}

.feature-icon {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #00d4aa;
  color: #08090a;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
}

.feature-icon.disabled {
  background: #1a1b1c;
  color: #5a5a5a;
}

.feature-text {
  color: #ffffff;
}

.feature-text.disabled {
  color: #5a5a5a;
}

/* Comparison */
.comparison-section {
  margin: 16px;
  background: #121314;
  border: 1px solid #2a2b2c;
  border-radius: 12px;
  padding: 16px;
}

.comparison-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 16px;
}

.comparison-row {
  display: flex;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #2a2b2c;
}

.comparison-row:last-child {
  border-bottom: none;
}

.comparison-feature {
  flex: 1;
  font-size: 13px;
  color: #8b8b8b;
}

.comparison-free, .comparison-premium {
  width: 60px;
  text-align: center;
  font-size: 12px;
}

.comparison-check {
  color: #00d4aa;
}

.comparison-x {
  color: #5a5a5a;
}

.comparison-limited {
  color: #4a90d9;
  font-size: 11px;
}

/* Subscribe Button */
.subscribe-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: calc(100% - 32px);
  margin: 8px 16px 16px;
  padding: 16px;
  background: #8b5cf6;
  color: #08090a;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  border: none;
}

.subscribe-btn:hover {
  opacity: 0.9;
}

/* Guarantee */
.guarantee-section {
  margin: 16px;
  background: linear-gradient(135deg, rgba(0,212,170,0.1) 0%, rgba(0,212,170,0.05) 100%);
  border: 1px solid rgba(0,212,170,0.3);
  border-radius: 8px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.guarantee-icon {
  font-size: 24px;
}

.guarantee-text {
  font-size: 13px;
  color: #00d4aa;
}

.guarantee-desc {
  font-size: 11px;
  color: #8b8b8b;
}

/* Terms */
.terms-section {
  margin: 16px;
  text-align: center;
}

.terms-text {
  font-size: 12px;
  color: #5a5a5a;
  line-height: 1.6;
}

.terms-link {
  color: #4a90d9;
  cursor: pointer;
}
</style>