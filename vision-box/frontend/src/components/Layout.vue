<template>
  <div class="layout">
    <!-- 侧边栏 -->
    <div class="sidebar">
      <div class="logo">
        <div class="logo-icon">📷</div>
        <span class="logo-text">视觉检测</span>
      </div>
      
      <nav class="nav-menu">
        <router-link 
          v-for="route in menuRoutes" 
          :key="route.path"
          :to="route.path"
          class="nav-item"
          :class="{ active: isActive(route.path) }"
        >
          <span class="nav-icon">{{ getIcon(route.meta.icon) }}</span>
          <span class="nav-text">{{ route.meta.title }}</span>
        </router-link>
      </nav>
      
      <!-- 用户信息区域 -->
      <div class="user-section">
        <a-dropdown placement="topRight">
          <div class="user-info">
            <a-avatar :size="32" class="user-avatar">
              <template #icon>
                <user-outlined />
              </template>
            </a-avatar>
            <div class="user-details">
              <div class="username">{{ authStore.user?.username || '用户' }}</div>
              <div class="user-role">{{ authStore.isAdmin ? '管理员' : '普通用户' }}</div>
            </div>
          </div>
          <template #overlay>
            <a-menu>
              <a-menu-item key="profile" @click="goToSettings">
                <setting-outlined />
                个人设置
              </a-menu-item>
              <a-menu-divider />
              <a-menu-item key="logout" @click="handleLogout">
                <logout-outlined />
                退出登录
              </a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
      </div>
    </div>
    
    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 顶部栏 -->
      <header class="header">
        <div class="header-left">
          <h1 class="page-title">{{ currentPageTitle }}</h1>
        </div>
        <div class="header-right">
          <span class="welcome-text">欢迎，{{ authStore.user?.username }}！</span>
        </div>
      </header>

      <!-- 内容区域 -->
      <main class="content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

// 菜单路由
const menuRoutes = [
  {
    path: '/home',
    meta: { title: '首页', icon: 'home' }
  },
  {
    path: '/detect',
    meta: { title: '检测', icon: 'camera' }
  },
  {
    path: '/history',
    meta: { title: '历史记录', icon: 'history' }
  },
  {
    path: '/settings',
    meta: { title: '设置', icon: 'setting' }
  }
]

// 图标映射
const iconMap = {
  home: '🏠',
  camera: '📷',
  history: '📋',
  setting: '⚙️'
}

// 计算属性
const currentPageTitle = computed(() => {
  const currentRoute = menuRoutes.find(r => r.path === route.path)
  return currentRoute ? currentRoute.meta.title : '视觉检测应用'
})

// 方法
const getIcon = (iconName) => {
  return iconMap[iconName] || '📄'
}

const refreshPage = () => {
  window.location.reload()
}
</script>

<style scoped>
.layout {
  display: flex;
  height: 100vh;
  background-color: #f0f2f5;
}

.sidebar {
  width: 240px;
  background: linear-gradient(180deg, #1890ff 0%, #096dd9 100%);
  color: white;
  display: flex;
  flex-direction: column;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
}

.logo {
  padding: 24px 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo-icon {
  font-size: 24px;
}

.logo-text {
  font-size: 18px;
  font-weight: bold;
}

.nav-menu {
  flex: 1;
  padding: 20px 0;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  color: rgba(255, 255, 255, 0.8);
  text-decoration: none;
  transition: all 0.3s ease;
  border-left: 3px solid transparent;
}

.nav-item:hover {
  background-color: rgba(255, 255, 255, 0.1);
  color: white;
}

.nav-item.active {
  background-color: rgba(255, 255, 255, 0.15);
  color: white;
  border-left-color: #52c41a;
}

.nav-icon {
  font-size: 16px;
  width: 20px;
  text-align: center;
}

.nav-text {
  font-size: 14px;
}

.user-section {
  padding: 16px 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  transition: background-color 0.3s ease;
}

.user-info:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.user-avatar {
  background-color: rgba(255, 255, 255, 0.2);
  color: white;
}

.user-details {
  flex: 1;
  min-width: 0;
}

.username {
  font-size: 14px;
  font-weight: 500;
  color: white;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-role {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.header {
  height: 64px;
  background: white;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

.header-left {
  display: flex;
  align-items: center;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #262626;
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.welcome-text {
  color: #595959;
  font-size: 14px;
}

.content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  background-color: #f0f2f5;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .sidebar {
    width: 200px;
  }
  
  .logo {
    padding: 16px;
  }
  
  .logo-text {
    font-size: 16px;
  }
  
  .nav-item {
    padding: 10px 16px;
  }
  
  .user-section {
    padding: 12px 16px;
  }
  
  .header {
    padding: 0 16px;
  }
  
  .page-title {
    font-size: 18px;
  }
  
  .content {
    padding: 16px;
  }
  
  .welcome-text {
    display: none;
  }
}

@media (max-width: 480px) {
  .sidebar {
    width: 180px;
  }
  
  .nav-text {
    font-size: 13px;
  }
  
  .username {
    font-size: 13px;
  }
  
  .user-role {
    font-size: 11px;
  }
}
</style>