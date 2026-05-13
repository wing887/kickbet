import axios from 'axios'

// API 基础配置
const API_BASE_URL = 'http://localhost:5001/api'

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

// ==================== 缓存API (v2.0) ====================

export interface CachedMatch {
  match_id: string
  home_team: string
  home_team_id: number
  away_team: string
  away_team_id: number
  league: string
  league_name: string
  match_date: string
  status: string
  has_prediction: boolean
  prediction?: CachedPrediction
}

export interface CachedPrediction {
  match_id: string
  prob_home: number
  prob_draw: number
  prob_away: number
  prediction: string  // H/D/A
  expected_home_goals: number
  expected_away_goals: number
  most_likely_score: string
  combined_prob_home?: number
  combined_prob_draw?: number
  combined_prob_away?: number
  h2h_prediction?: H2HPredictionData
}

export interface H2HPredictionData {
  total_matches: number
  home_win_rate: number
  away_win_rate: number
  draw_rate: number
  avg_total_goals: number
  h2h_prob_home: number
  h2h_prob_draw: number
  h2h_prob_away: number
}

export interface CachedMatchesResponse {
  success: boolean
  matches: CachedMatch[]
  total: number
  cached_count: number
  timestamp: string
}

export interface CachedMatchDetailResponse {
  success: boolean
  match: CachedMatch
  prediction: CachedPrediction | null
  has_prediction: boolean
  odds_history: OddsHistoryItem[]
  odds_change_detected: boolean
}

export interface OddsHistoryItem {
  odds_id: string
  match_id: string
  bookmaker: string
  home_odds: number
  draw_odds: number
  away_odds: number
  collected_at: string
  change_detected: boolean
}

export interface LivePredictionParams {
  match_id: string
  home_team: string
  away_team: string
  home_team_id: number
  away_team_id: number
  h2h_weight?: number  // 0-0.5, default 0.25
}

export interface LivePredictionResponse {
  success: boolean
  match_id: string
  home_team: string
  away_team: string
  poisson_prediction: {
    prob_home: number
    prob_draw: number
    prob_away: number
    expected_home_goals: number
    expected_away_goals: number
    most_likely_score: string
  }
  h2h_stats: {
    total_matches: number
    home_wins: number
    away_wins: number
    draws: number
    home_win_rate: number
    away_win_rate: number
    draw_rate: number
    avg_total_goals: number
    recent_results: string[]
  }
  combined_prediction: {
    prob_home: number
    prob_draw: number
    prob_away: number
    prediction: string
    h2h_weight: number
  }
  has_h2h_data: boolean
}

export interface BatchPredictionsResponse {
  success: boolean
  predictions: Record<string, CachedPrediction | null>
  found_count: number
  missing_count: number
  missing: string[]
}

export const cache = {
  // 获取比赛列表 (带预测缓存)
  matches: (hours = 72, league?: string): Promise<CachedMatchesResponse> =>
    apiClient.get('/cache/matches', { params: { hours, league } }),
  
  // 获取单场比赛详情
  matchDetail: (matchId: string): Promise<CachedMatchDetailResponse> =>
    apiClient.get(`/cache/matches/${matchId}`),
  
  // 获取预测数据
  prediction: (matchId: string, full = false): Promise<{ success: boolean; match_id: string; prediction: CachedPrediction }> =>
    apiClient.get(`/cache/predictions/${matchId}`, { params: { full } }),
  
  // 实时预测 (含H2H)
  predictionLive: (params: LivePredictionParams): Promise<LivePredictionResponse> =>
    apiClient.post('/cache/predictions/live', params),
  
  // 批量获取预测
  predictionsBatch: (matchIds: string[]): Promise<BatchPredictionsResponse> =>
    apiClient.post('/cache/predictions/batch', { match_ids: matchIds }),
  
  // 获取预测历史版本
  predictionHistory: (matchId: string, limit = 5): Promise<{ success: boolean; history: CachedPrediction[] }> =>
    apiClient.get(`/cache/predictions/${matchId}/history`, { params: { limit } }),
  
  // 获取赔率历史
  odds: (matchId: string, bookmaker?: string): Promise<{ success: boolean; odds: OddsHistoryItem }> =>
    apiClient.get(`/cache/odds/${matchId}`, { params: { bookmaker } })
}

export default apiClient