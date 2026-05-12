import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/Home/index.vue'),
    meta: { title: '首页' }
  },
  {
    path: '/auth',
    name: 'Auth',
    component: () => import('../views/Auth/index.vue'),
    meta: { title: '登录注册', guest: true }
  },
  {
    path: '/matches',
    name: 'Matches',
    component: () => import('../views/Matches/index.vue'),
    meta: { title: '比赛' }
  },
  {
    path: '/match/:id',
    name: 'MatchDetail',
    component: () => import('../views/MatchDetail/index.vue'),
    meta: { title: '比赛详情' }
  },
  {
    path: '/combo',
    name: 'Combo',
    component: () => import('../views/Combo/index.vue'),
    meta: { title: '组合投注', requiresAuth: true, requiresPremium: true }
  },
  {
    path: '/tracker',
    name: 'Tracker',
    component: () => import('../views/Tracker/index.vue'),
    meta: { title: '投注追踪', requiresAuth: true }
  },
  {
    path: '/subscribe',
    name: 'Subscribe',
    component: () => import('../views/Subscribe/index.vue'),
    meta: { title: '升级会员' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  // 设置页面标题
  document.title = `KickBet - ${to.meta.title || '首页'}`
  
  const token = localStorage.getItem('kb_token')
  const isLoggedIn = !!token
  
  // 需要登录的页面
  if (to.meta.requiresAuth && !isLoggedIn) {
    next('/auth')
    return
  }
  
  // 已登录用户不应该访问登录页
  if (to.meta.guest && isLoggedIn) {
    next('/')
    return
  }
  
  // 需要会员权限的页面，暂时只提示
  if (to.meta.requiresPremium && !isLoggedIn) {
    // 可以添加会员检查逻辑
    console.log('此功能需要会员权限')
  }
  
  next()
})

export default router