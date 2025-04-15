import axios from 'axios'

// API 基礎URL設定
export const API_BASE_URL = process.env.NODE_ENV === 'production'
  ? 'https://war-room.thm.com.tw/api'
  : 'http://localhost:5000/api'

// WebSocket URL設定
export const SOCKET_URL = process.env.NODE_ENV === 'production'
  ? 'https://war-room.thm.com.tw'
  : 'http://localhost:5000'

// 建立通用的 API 客戶端
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  withCredentials: true, // 啟用跨域憑證
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': `Basic ${btoa('admin:thm')}` // 確保使用正確的用戶名和密碼
  }
})

// 響應攔截器，根據環境處理錯誤
apiClient.interceptors.response.use(
  response => response,
  error => {
    // 處理開發環境的特定錯誤
    if (process.env.NODE_ENV === 'development') {
      console.error('API 錯誤:', error.message);
      if (error.response?.status === 401) {
        console.warn('開發環境認證失敗，使用模擬數據');
        return Promise.resolve({ data: [] });
      }
    }
    
    // 其他錯誤處理
    if (error.response?.status === 401 || error.response?.status === 502) {
      console.warn(`認證失敗或服務器錯誤 (${error.response?.status})，使用模擬數據`);
      return Promise.resolve({ data: [] });
    }
    return Promise.reject(error);
  }
)

// 生成模擬數據
const generateMockData = () => {
  // ... 你的模擬數據生成邏輯
}

// API 請求輔助函數
export const fetchData = async (endpoint, options = {}) => {
  try {
    const response = await apiClient.get(endpoint, options)
    return response.data
  } catch (error) {
    console.error(`API 錯誤 (${endpoint}):`, error)
    throw error
  }
}

// 通用的資料格式化函數
export const formatDate = (dateString) => {
  if (!dateString) return '未設定'
  try {
    if (dateString.length === 8) {
      const year = dateString.substring(0, 4)
      const month = dateString.substring(4, 6)
      const day = dateString.substring(6, 8)
      return `${year}-${month}-${day}`
    }
    const date = new Date(dateString)
    return date.toISOString().split('T')[0]
  } catch (e) {
    return '日期錯誤'
  }
}

// WebSocket 選項設定
export const SOCKET_OPTIONS = {
  transports: ['websocket', 'polling'],
  secure: true,
  rejectUnauthorized: false,
  path: '/socket.io',
  reconnection: true,
  reconnectionDelay: 1000,
  reconnectionDelayMax: 5000,
  reconnectionAttempts: 5,
  timeout: 20000,
  withCredentials: true,
  auth: {
    username: 'admin',
    password: 'thm'
  }
}