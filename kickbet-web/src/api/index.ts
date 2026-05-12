import axios from 'axios'

// API 基础配置
const API_BASE_URL = 'http://localhost:5000/api'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 120秒 (后端分析需要调用多个外部API)
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器 - 自动添加 JWT token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('kb_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器 - 处理错误
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message = error.response?.data?.error || error.message || '请求失败'
    return Promise.reject(new Error(message))
  }
)

// ==================== API 接口 ====================

// 健康检查
export const healthCheck = () => apiClient.get('/health')

// ==================== 认证 ====================

export interface RegisterParams {
  username: string
  email: string
  password: string
}

export interface LoginParams {
  username: string
  password: string
}

export interface User {
  user_id: string
  username: string
  email: string
  role: string
  created_at: string
  last_login?: string
  is_active: boolean
}

export interface AuthResponse {
  message: string
  user: User
  token: string
  expires_in: number
}

export const auth = {
  register: (params: RegisterParams): Promise<AuthResponse> => 
    apiClient.post('/auth/register', params),
  
  login: (params: LoginParams): Promise<AuthResponse> => 
    apiClient.post('/auth/login', params),
  
  refresh: (): Promise<{ message: string; token: string; expires_in: number }> => 
    apiClient.post('/auth/refresh'),
  
  me: (): Promise<{ user: User }> => 
    apiClient.get('/auth/me')
}

// ==================== 比赛 ====================

export interface Match {
  match_id: number
  home_team: string
  away_team: string
  league: string
  league_name: string
  match_date: string
  status: string
}

export interface MatchDetail {
  match: {
    match_id: number
    home_team: string
    home_team_id: number
    away_team: string
    away_team_id: number
    league: string
    league_name: string
    match_date: string
    status: string
  }
}

export interface MatchesResponse {
  total: number
  matches: Match[]
  query: { days: number; league: string | null }
}

export const matches = {
  list: (days = 3, league?: string): Promise<MatchesResponse> => 
    apiClient.get('/matches', { params: { days, league } }),
  
  detail: (matchId: number): Promise<MatchDetail> => 
    apiClient.get(`/match/${matchId}`)
}

// ==================== 预测分析 ====================

export interface AnalysisResponse {
  match_id: number
  home_team: string
  away_team: string
  league: string
  league_name: string
  prediction: {
    home_win_prob: number
    draw_prob: number
    away_win_prob: number
    predicted_home_goals: number
    predicted_away_goals: number
  }
  poisson_simulation: {
    iterations: number
    home_win_pct: number
    draw_pct: number
    away_win_pct: number
    most_likely_scores: { score: string; probability: number }[]
  }
  odds: {
    home: number
    draw: number
    away: number
    over_under?: { line: number; over: number; under: number }
    handicap?: { line: number; home: number; away: number }
  }
  kelly_criterion: {
    home: { edge: number; kelly: number; half_kelly: number; value: boolean }
    draw: { edge: number; kelly: number; half_kelly: number; value: boolean }
    away: { edge: number; kelly: number; half_kelly: number; value: boolean }
  }
  recommended_bets: {
    conservative: { type: string; odds: number; stake_pct: number; reason: string }
    balanced: { type: string; odds: number; stake_pct: number; reason: string }
    aggressive: { type: string; odds: number; stake_pct: number; reason: string }
  }
}

export const analysis = {
  get: (matchId: number): Promise<AnalysisResponse> => 
    apiClient.get(`/analysis/${matchId}`)
}

// ==================== 计算 ====================

export interface TotalsCalcParams {
  lambda_home: number
  lambda_away: number
  line: number
}

export interface TotalsCalcResponse {
  line: number
  over_prob: number
  under_prob: number
  recommendation: string
}

export interface HandicapCalcParams {
  lambda_home: number
  lambda_away: number
  handicap: number
}

export interface HandicapCalcResponse {
  handicap: number
  home_win_prob: number
  away_win_prob: number
  recommendation: string
}

export const calculate = {
  totals: (params: TotalsCalcParams): Promise<TotalsCalcResponse> => 
    apiClient.post('/calculate/totals', params),
  
  handicap: (params: HandicapCalcParams): Promise<HandicapCalcResponse> => 
    apiClient.post('/calculate/handicap', params)
}

// ==================== 用户 ====================

export interface PredictionRecord {
  id: number
  user_id: string
  match_id: number
  prediction_type: string
  predicted_result: string
  confidence: number
  odds_value: number
  result?: string
  created_at: string
}

export const user = {
  predictions: (limit = 50): Promise<{ total: number; predictions: PredictionRecord[] }> => 
    apiClient.get('/user/predictions', { params: { limit } }),
  
  getPrediction: (id: number): Promise<PredictionRecord> => 
    apiClient.get(`/predictions/${id}`)
}

// ==================== 管理员 ====================

export const admin = {
  users: (): Promise<{ total: number; users: User[] }> => 
    apiClient.get('/admin/users'),
  
  stats: (): Promise<{
    users: { total: number; admins: number; active: number }
    predictions: { total: number; correct: number; pending: number; accuracy: number }
    api: { version: string; endpoints: number }
  }> => apiClient.get('/admin/stats')
}

export default apiClient