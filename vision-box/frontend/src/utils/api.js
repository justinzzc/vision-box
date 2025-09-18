import axios from 'axios'
import { message } from 'ant-design-vue'

import { useRouter } from 'vue-router'

const router = useRouter()

// 创建axios实例
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 在发送请求之前做些什么
    console.log('发送请求:', config.method?.toUpperCase(), config.url)
    
    // 添加认证token
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    return config
  },
  (error) => {
    // 对请求错误做些什么
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    // 对响应数据做点什么
    console.log('响应数据:', response.status, response.config.url)
    return response.data
  },
  (error) => {
    // 对响应错误做点什么
    console.error('响应错误:', error)
    
    let errorMessage = '请求失败'
    
    if (error.response) {
      // 服务器返回了错误状态码
      const { status, data } = error.response
      
      switch (status) {
        case 400:
          errorMessage = data.detail || '请求参数错误'
          break
        case 401:
          errorMessage = '未授权访问'
          // 清除token并跳转到登录页
          localStorage.removeItem('token')
          localStorage.removeItem('user')
          router.push('/login')
          break
        case 403:
          errorMessage = '禁止访问'
          break
        case 404:
          errorMessage = '请求的资源不存在'
          break
        case 422:
          errorMessage = data.detail || '请求参数验证失败'
          break
        case 500:
          errorMessage = '服务器内部错误'
          break
        default:
          errorMessage = data.detail || `请求失败 (${status})`
      }
    } else if (error.request) {
      // 请求已发出但没有收到响应
      errorMessage = '网络连接失败，请检查网络设置'
    } else {
      // 其他错误
      errorMessage = error.message || '未知错误'
    }
    
    message.error(errorMessage)
    return Promise.reject(error)
  }
)

// API方法
export const apiClient = {
  // 文件上传
  uploadFile(file, fileType) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('file_type', fileType)
    
    return api.post('/v1/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: 60000 // 文件上传超时时间设置为60秒
    })
  },
  
  // 执行检测
  detect(params) {
    return api.post('/v1/detection/tasks', params)
  },
  
  // 查询检测结果
  getResult(taskId) {
    return api.get(`/v1/detection/tasks/${taskId}`)
  },
  
  // 获取历史记录
  getHistory(params = {}) {
    return api.get('/v1/detection/history', { params })
  },
  
  // 删除历史记录
  deleteHistory(taskId) {
    return api.delete(`/v1/detection/tasks/${taskId}`)
  },
  
  // 获取系统信息
  getSystemInfo() {
    return api.get('/v1/system/info')
  },
  
  // 认证相关接口
  login(credentials) {
    return api.post('/v1/auth/login', credentials)
  },
  
  logout() {
    return api.post('/v1/auth/logout')
  },
  
  refreshToken() {
    return api.post('/v1/auth/refresh')
  },
  
  getCurrentUser() {
    return api.get('/v1/auth/me')
  },
  
  updateProfile(profileData) {
    return api.put('/v1/users/profile', profileData)
  },
  
  changePassword(passwordData) {
    return api.put('/v1/users/password', passwordData)
  },
  
  // 获取可用模型列表
  getModels() {
    return api.get('/v1/detection/models')
  },
  
  // 下载检测结果
  downloadResult(taskId, format = 'json') {
    return api.get(`/v1/detection/tasks/${taskId}/download/${format}`, {
      responseType: 'blob'
    })
  }
}

// 文件下载辅助函数
export const downloadFile = (blob, filename) => {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

// 文件大小格式化
export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 检查文件类型
export const checkFileType = (file, allowedTypes) => {
  const fileType = file.type.toLowerCase()
  const fileName = file.name.toLowerCase()
  
  // 检查MIME类型
  for (const type of allowedTypes) {
    if (fileType.includes(type)) {
      return true
    }
  }
  
  // 检查文件扩展名
  const allowedExtensions = {
    image: ['.jpg', '.jpeg', '.png', '.bmp', '.gif'],
    video: ['.mp4', '.avi', '.mov', '.mkv', '.wmv']
  }
  
  for (const [category, extensions] of Object.entries(allowedExtensions)) {
    if (allowedTypes.includes(category)) {
      for (const ext of extensions) {
        if (fileName.endsWith(ext)) {
          return true
        }
      }
    }
  }
  
  return false
}

export default api