<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <div class="logo">
          <camera-outlined class="logo-icon" />
          <h1 class="logo-title">视觉检测平台</h1>
        </div>
        <p class="login-subtitle">请登录您的账户</p>
      </div>

      <a-form
        :model="loginForm"
        :rules="rules"
        @finish="handleLogin"
        @finishFailed="handleLoginFailed"
        layout="vertical"
        class="login-form"
      >
        <a-form-item label="用户名" name="username">
          <a-input
            v-model:value="loginForm.username"
            size="large"
            placeholder="请输入用户名"
            :prefix="h(UserOutlined)"
          />
        </a-form-item>

        <a-form-item label="密码" name="password">
          <a-input-password
            v-model:value="loginForm.password"
            size="large"
            placeholder="请输入密码"
            :prefix="h(LockOutlined)"
          />
        </a-form-item>

        <a-form-item>
          <a-checkbox v-model:checked="loginForm.remember">
            记住我
          </a-checkbox>
        </a-form-item>

        <a-form-item>
          <a-button
            type="primary"
            html-type="submit"
            size="large"
            :loading="loading"
            block
          >
            登录
          </a-button>
        </a-form-item>
      </a-form>

      <div class="login-footer">
        <a-divider>演示账户</a-divider>
        <div class="demo-accounts">
          <a-space direction="vertical" style="width: 100%">
            <a-button 
              type="dashed" 
              block 
              @click="loginWithDemo('admin')"
              :loading="loading"
            >
              管理员账户 (admin / admin123)
            </a-button>
            <a-button 
              type="dashed" 
              block 
              @click="loginWithDemo('demo')"
              :loading="loading"
            >
              演示账户 (demo / demo123)
            </a-button>
          </a-space>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, h } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  CameraOutlined,
  UserOutlined,
  LockOutlined
} from '@ant-design/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const loginForm = ref({
  username: '',
  password: '',
  remember: false
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度应为3-20个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 50, message: '密码长度应为6-50个字符', trigger: 'blur' }
  ]
}

const handleLogin = async (values) => {
  loading.value = true
  try {
    await authStore.login(values)
    message.success('登录成功')
    
    // 跳转到首页或之前访问的页面
    const redirect = router.currentRoute.value.query.redirect || '/home'
    router.push(redirect)
  } catch (error) {
    console.error('登录失败:', error)
    message.error(error.message || '登录失败，请检查用户名和密码')
  } finally {
    loading.value = false
  }
}

const handleLoginFailed = (errorInfo) => {
  console.log('表单验证失败:', errorInfo)
}

const loginWithDemo = async (type) => {
  const demoAccounts = {
    admin: { username: 'admin', password: 'admin123' },
    demo: { username: 'demo', password: 'demo123' }
  }
  
  loginForm.value = { ...demoAccounts[type], remember: false }
  await handleLogin(demoAccounts[type])
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-card {
  width: 100%;
  max-width: 400px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  padding: 40px;
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 16px;
}

.logo-icon {
  font-size: 32px;
  color: #1890ff;
}

.logo-title {
  font-size: 24px;
  font-weight: bold;
  color: #262626;
  margin: 0;
}

.login-subtitle {
  color: #8c8c8c;
  font-size: 14px;
  margin: 0;
}

.login-form {
  margin-bottom: 24px;
}

.login-footer {
  margin-top: 24px;
}

.demo-accounts {
  margin-top: 16px;
}

/* 响应式设计 */
@media (max-width: 480px) {
  .login-card {
    padding: 24px;
    margin: 0 16px;
  }
  
  .logo-title {
    font-size: 20px;
  }
}
</style>