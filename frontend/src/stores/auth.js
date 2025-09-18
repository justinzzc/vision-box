import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { apiClient } from '@/utils/api'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const user = ref(null)
  const token = ref(localStorage.getItem('token') || null)
  const isLoading = ref(false)

  // 计算属性
  const isAuthenticated = computed(() => {
    return !!token.value && !!user.value
  })

  const isAdmin = computed(() => {
    return user.value?.is_superuser || false
  })

  // 方法
  const login = async (credentials) => {
    isLoading.value = true
    try {
      const response = await apiClient.login(credentials)
      const { access_token, user_info: userData } = response
      
      // 保存token和用户信息
      token.value = access_token
      user.value = userData
      
      // 持久化存储
      localStorage.setItem('token', access_token)
      localStorage.setItem('user', JSON.stringify(userData))
      
      return response
    } catch (error) {
      console.error('登录错误:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  const logout = async () => {
    try {
      // 调用后端登出接口（如果有的话）
      if (token.value) {
        await apiClient.logout()
      }
    } catch (error) {
      console.error('登出错误:', error)
    } finally {
      // 清除本地状态
      token.value = null
      user.value = null
      
      // 清除持久化存储
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }
  }

  const refreshToken = async () => {
    try {
      const response = await apiClient.refreshToken()
      const { access_token } = response
      
      token.value = access_token
      localStorage.setItem('token', access_token)
      
      return response
    } catch (error) {
      console.error('刷新token错误:', error)
      // 如果刷新失败，清除认证状态
      await logout()
      throw error
    }
  }

  const getCurrentUser = async () => {
    if (!token.value) {
      throw new Error('未登录')
    }
    
    try {
      const response = await apiClient.getCurrentUser()
      user.value = response
      localStorage.setItem('user', JSON.stringify(response))
      return response
    } catch (error) {
      console.error('获取用户信息错误:', error)
      throw error
    }
  }

  const updateProfile = async (profileData) => {
    try {
      const response = await apiClient.updateProfile(profileData)
      user.value = { ...user.value, ...response }
      localStorage.setItem('user', JSON.stringify(user.value))
      return response
    } catch (error) {
      console.error('更新用户信息错误:', error)
      throw error
    }
  }

  const changePassword = async (passwordData) => {
    try {
      const response = await apiClient.changePassword(passwordData)
      return response
    } catch (error) {
      console.error('修改密码错误:', error)
      throw error
    }
  }

  // 初始化认证状态
  const initAuth = () => {
    const savedToken = localStorage.getItem('token')
    const savedUser = localStorage.getItem('user')
    
    if (savedToken && savedUser && savedUser !== 'undefined' && savedUser !== 'null') {
      try {
        token.value = savedToken
        user.value = JSON.parse(savedUser)
      } catch (error) {
        console.error('解析用户信息失败:', error)
        // 清除损坏的数据
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        token.value = null
        user.value = null
      }
    } else {
      // 清除无效数据
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      token.value = null
      user.value = null
    }
  }

  // 检查token是否过期
  const isTokenExpired = () => {
    if (!token.value) return true
    
    try {
      // 解析JWT token的payload部分
      const payload = JSON.parse(atob(token.value.split('.')[1]))
      const currentTime = Date.now() / 1000
      
      return payload.exp < currentTime
    } catch (error) {
      console.error('解析token失败:', error)
      return true
    }
  }

  // 自动刷新token
  const autoRefreshToken = async () => {
    if (isTokenExpired()) {
      try {
        await refreshToken()
      } catch (error) {
        console.error('自动刷新token失败:', error)
        await logout()
      }
    }
  }

  return {
    // 状态
    user,
    token,
    isLoading,
    
    // 计算属性
    isAuthenticated,
    isAdmin,
    
    // 方法
    login,
    logout,
    refreshToken,
    getCurrentUser,
    updateProfile,
    changePassword,
    initAuth,
    isTokenExpired,
    autoRefreshToken
  }
})