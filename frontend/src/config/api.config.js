export const API_BASE_URL = process.env.NODE_ENV === 'production'
  ? 'https://192.168.2.140:5000'
  : 'http://localhost:5000'

export const SOCKET_URL = process.env.NODE_ENV === 'production'
  ? 'https://192.168.2.140:5000'
  : 'http://localhost:5000'

export const SOCKET_OPTIONS = {
  transports: ['polling', 'websocket'],
  secure: true,
  rejectUnauthorized: false,
  path: '/socket.io',
  reconnection: true,
  reconnectionDelay: 1000,
  reconnectionDelayMax: 5000,
  reconnectionAttempts: 5,
  timeout: 20000
}

// 新增 API 請求工具函數
export const fetchWithRetry = async (url, options = {}) => {
  const maxRetries = 3;
  let retryCount = 0;

  while (retryCount < maxRetries) {
    try {
      const response = await fetch(url, {
        ...options,
        // 忽略 SSL 證書錯誤（注意：這可能有安全風險）
        mode: 'cors',
        credentials: 'omit'
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      retryCount++;
      if (retryCount === maxRetries) {
        throw error;
      }
      // 等待一段時間後重試
      await new Promise(resolve => setTimeout(resolve, 1000 * retryCount));
    }
  }
}