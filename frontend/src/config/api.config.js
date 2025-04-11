import axios from 'axios'

export const API_BASE_URL = process.env.NODE_ENV === 'production'
  ? 'https://war-room.thm.com.tw/api'
  : 'http://localhost:5000'

export const SOCKET_URL = process.env.NODE_ENV === 'production'
  ? 'https://war-room.thm.com.tw'
  : 'http://localhost:5000'

// 建立 axios 實例並設定預設認證
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  auth: {
    username: 'admin',
    password: 'thm'
  },
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
})

// 處理錯誤重試
apiClient.interceptors.response.use(
  response => response,
  async error => {
    if (error.config && !error.config._retry && error.response?.status === 401) {
      error.config._retry = true
      return apiClient(error.config)
    }
    return Promise.reject(error)
  }
)

// 替換原有的 fetchWithRetry
export const fetchWithRetry = async (url, options = {}) => {
  try {
    const response = await apiClient.get(url, options)
    return response.data
  } catch (error) {
    console.error('API 請求錯誤:', error)
    throw error
  }
}

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