<template>
  <div class="auth-page">
    <!-- Logo Section -->
    <div class="logo-section">
      <div class="logo">KickBet</div>
      <div class="logo-subtitle">智能足球预测助手</div>
    </div>
    
    <!-- Form Section -->
    <div class="form-section">
      <div class="form-card">
        <div class="form-tabs">
          <div 
            :class="['form-tab', { active: mode === 'login' }]" 
            @click="mode = 'login'"
          >登录</div>
          <div 
            :class="['form-tab', { active: mode === 'register' }]" 
            @click="mode = 'register'"
          >注册</div>
        </div>
        
        <!-- Login Form -->
        <div v-if="mode === 'login'" class="form-content">
          <div class="form-group">
            <label class="form-label">用户名</label>
            <input 
              v-model="loginForm.username"
              type="text" 
              class="form-input" 
              placeholder="输入用户名"
            >
          </div>
          
          <div class="form-group">
            <label class="form-label">密码</label>
            <input 
              v-model="loginForm.password"
              type="password" 
              class="form-input" 
              placeholder="输入密码"
            >
            <div v-if="loginError" class="form-error show">{{ loginError }}</div>
          </div>
          
          <div class="form-actions">
            <div class="remember-me" @click="rememberMe = !rememberMe">
              <div :class="['checkbox', { checked: rememberMe }]">
                <span v-if="rememberMe">✓</span>
              </div>
              <span>记住我</span>
            </div>
          </div>
          
          <button 
            class="submit-btn" 
            @click="handleLogin"
            :disabled="loginLoading"
          >
            {{ loginLoading ? '登录中...' : '登录' }}
          </button>
          
          <div class="divider">
            <div class="divider-line"></div>
            <span class="divider-text">或</span>
            <div class="divider-line"></div>
          </div>
          
          <div class="social-btns">
            <div class="social-btn" @click="showTestAccountHint">
              <span>测试账户</span>
            </div>
            <div class="social-btn" @click="skipLogin">
              <span>游客模式</span>
            </div>
          </div>
        </div>
        
        <!-- Register Form -->
        <div v-if="mode === 'register'" class="form-content">
          <div class="form-group">
            <label class="form-label">用户名</label>
            <input 
              v-model="registerForm.username"
              type="text" 
              class="form-input" 
              placeholder="3-30字符"
            >
          </div>
          
          <div class="form-group">
            <label class="form-label">邮箱</label>
            <input 
              v-model="registerForm.email"
              type="email" 
              class="form-input" 
              placeholder="your@email.com"
            >
          </div>
          
          <div class="form-group">
            <label class="form-label">密码</label>
            <input 
              v-model="registerForm.password"
              type="password" 
              class="form-input" 
              placeholder="至少6位密码"
            >
          </div>
          
          <div class="form-group">
            <label class="form-label">确认密码</label>
            <input 
              v-model="registerForm.confirmPassword"
              type="password" 
              class="form-input" 
              placeholder="再次输入密码"
            >
            <div v-if="registerError" class="form-error show">{{ registerError }}</div>
          </div>
          
          <button 
            class="submit-btn" 
            @click="handleRegister"
            :disabled="registerLoading"
          >
            {{ registerLoading ? '注册中...' : '注册' }}
          </button>
          
          <div class="terms-text">
            注册即表示同意 <span class="terms-link">服务条款</span> 和 <span class="terms-link">隐私政策</span>
          </div>
        </div>
      </div>
      
      <!-- Promo Banner -->
      <div class="promo-banner">
        <span class="promo-text">新用户专享：首月会员 ¥49</span>
        <span class="promo-btn" @click="$router.push('/subscribe')">查看</span>
      </div>
    </div>
    
    <!-- Footer -->
    <div class="footer">
      <div class="footer-text">KickBet 2026 · 仅提供分析建议</div>
    </div>
    
    <!-- Test Account Hint Modal -->
    <div v-if="showHint" class="hint-modal">
      <div class="hint-card">
        <h3 class="hint-title">测试账户</h3>
        <div class="hint-content">
          <p><strong>管理员:</strong> admin / admin123</p>
          <p><strong>普通用户:</strong> test / test123</p>
        </div>
        <button class="hint-close" @click="showHint = false">关闭</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { auth } from '../../api'

const router = useRouter()

const mode = ref<'login' | 'register'>('login')
const rememberMe = ref(false)
const showHint = ref(false)

const loginForm = ref({
  username: '',
  password: ''
})
const loginLoading = ref(false)
const loginError = ref('')

const registerForm = ref({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})
const registerLoading = ref(false)
const registerError = ref('')

async function handleLogin() {
  if (!loginForm.value.username || !loginForm.value.password) {
    loginError.value = '请填写用户名和密码'
    return
  }
  
  loginLoading.value = true
  loginError.value = ''
  
  try {
    const result = await auth.login({
      username: loginForm.value.username,
      password: loginForm.value.password
    })
    
    // 保存token
    localStorage.setItem('kb_token', result.token)
    if (rememberMe.value) {
      localStorage.setItem('kb_user', JSON.stringify(result.user))
    }
    
    // 跳转首页
    router.push('/')
  } catch (e: any) {
    loginError.value = e.message || '登录失败，请重试'
  } finally {
    loginLoading.value = false
  }
}

async function handleRegister() {
  if (!registerForm.value.username || !registerForm.value.email || !registerForm.value.password) {
    registerError.value = '请填写完整信息'
    return
  }
  
  if (registerForm.value.password.length < 6) {
    registerError.value = '密码至少6位'
    return
  }
  
  if (registerForm.value.password !== registerForm.value.confirmPassword) {
    registerError.value = '两次密码不一致'
    return
  }
  
  registerLoading.value = true
  registerError.value = ''
  
  try {
    const result = await auth.register({
      username: registerForm.value.username,
      email: registerForm.value.email,
      password: registerForm.value.password
    })
    
    // 保存token并跳转
    localStorage.setItem('kb_token', result.token)
    router.push('/')
  } catch (e: any) {
    registerError.value = e.message || '注册失败，请重试'
  } finally {
    registerLoading.value = false
  }
}

function showTestAccountHint() {
  showHint.value = true
}

function skipLogin() {
  // 游客模式，直接跳转
  router.push('/')
}
</script>

<style scoped>
.auth-page {
  font-family: 'Inter', -apple-system, sans-serif;
  background: #08090a;
  color: #ffffff;
  min-height: 100vh;
  max-width: 420px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
}

/* Logo Section */
.logo-section {
  padding: 48px 16px 32px;
  text-align: center;
}

.logo {
  font-size: 32px;
  font-weight: 700;
  color: #00d4aa;
  margin-bottom: 8px;
}

.logo-subtitle {
  font-size: 14px;
  color: #8b8b8b;
}

/* Form Section */
.form-section {
  padding: 16px;
  flex: 1;
}

.form-card {
  background: #121314;
  border: 1px solid #2a2b2c;
  border-radius: 12px;
  padding: 24px;
}

.form-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
}

.form-tab {
  flex: 1;
  padding: 12px;
  background: #1a1b1c;
  border: 1px solid #2a2b2c;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #8b8b8b;
  cursor: pointer;
  text-align: center;
}

.form-tab.active {
  background: #4a90d9;
  color: #08090a;
  border-color: #4a90d9;
}

.form-content {
  /* 动态显示 */
}

.form-group {
  margin-bottom: 16px;
}

.form-label {
  font-size: 13px;
  font-weight: 500;
  color: #8b8b8b;
  margin-bottom: 8px;
  display: block;
}

.form-input {
  width: 100%;
  background: #0d0e0f;
  border: 1px solid #2a2b2c;
  border-radius: 8px;
  padding: 14px 16px;
  font-size: 14px;
  color: #ffffff;
  outline: none;
  font-family: 'Inter', sans-serif;
}

.form-input:focus {
  border-color: #4a90d9;
}

.form-input::placeholder {
  color: #5a5a5a;
}

.form-error {
  font-size: 12px;
  color: #ff6b6b;
  margin-top: 6px;
  display: none;
}

.form-error.show {
  display: block;
}

.form-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.remember-me {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #8b8b8b;
  cursor: pointer;
}

.checkbox {
  width: 18px;
  height: 18px;
  background: #1a1b1c;
  border: 1px solid #2a2b2c;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.checkbox.checked {
  background: #4a90d9;
  border-color: #4a90d9;
  color: #08090a;
  font-size: 12px;
}

.submit-btn {
  width: 100%;
  padding: 16px;
  background: #00d4aa;
  color: #08090a;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  margin-bottom: 16px;
  border: none;
}

.submit-btn:hover {
  opacity: 0.9;
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Divider */
.divider {
  display: flex;
  align-items: center;
  gap: 16px;
  margin: 24px 0;
}

.divider-line {
  height: 1px;
  background: #2a2b2c;
  flex: 1;
}

.divider-text {
  font-size: 12px;
  color: #5a5a5a;
}

/* Social Buttons */
.social-btns {
  display: flex;
  gap: 12px;
}

.social-btn {
  flex: 1;
  padding: 12px;
  background: #1a1b1c;
  border: 1px solid #2a2b2c;
  border-radius: 8px;
  font-size: 14px;
  color: #8b8b8b;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.social-btn:hover {
  background: #121314;
  border-color: #3a3b3c;
}

/* Terms */
.terms-text {
  font-size: 12px;
  color: #5a5a5a;
  text-align: center;
  margin-top: 16px;
}

.terms-link {
  color: #4a90d9;
  cursor: pointer;
}

/* Promo Banner */
.promo-banner {
  margin: 16px;
  background: linear-gradient(135deg, rgba(139,92,246,0.1) 0%, rgba(139,92,246,0.05) 100%);
  border: 1px solid rgba(139,92,246,0.3);
  border-radius: 8px;
  padding: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.promo-text {
  font-size: 13px;
  color: #8b8b8b;
}

.promo-btn {
  font-size: 12px;
  background: #8b5cf6;
  color: #08090a;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
}

/* Footer */
.footer {
  padding: 24px 16px;
  text-align: center;
  border-top: 1px solid #2a2b2c;
}

.footer-text {
  font-size: 12px;
  color: #5a5a5a;
}

/* Hint Modal */
.hint-modal {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.hint-card {
  background: #121314;
  border: 1px solid #2a2b2c;
  border-radius: 12px;
  padding: 24px;
  max-width: 320px;
  width: 90%;
}

.hint-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
  color: #4a90d9;
}

.hint-content {
  margin-bottom: 16px;
}

.hint-content p {
  font-size: 14px;
  margin-bottom: 8px;
}

.hint-close {
  width: 100%;
  padding: 12px;
  background: #4a90d9;
  color: #08090a;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  border: none;
}
</style>