import { createRouter, createWebHistory } from 'vue-router'
import Layout from '@/components/Layout.vue'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录', requiresGuest: true }
  },
  {
    path: '/',
    component: Layout,
    redirect: '/home',
    meta: { requiresAuth: true },
    children: [
      {
        path: '/home',
        name: 'Home',
        component: () => import('@/views/Home.vue'),
        meta: { title: '首页' }
      },
      {
        path: '/detect',
        name: 'Detect',
        component: () => import('@/views/Detect.vue'),
        meta: { title: '检测' }
      },
      {
        path: '/history',
        name: 'History',
        component: () => import('@/views/History.vue'),
        meta: { title: '历史记录' }
      },
      {
        path: '/result/:id',
        name: 'Result',
        component: () => import('@/views/Result.vue'),
        meta: { title: '检测结果' }
      },
      {
        path: '/settings',
        name: 'Settings',
        component: () => import('@/views/Settings.vue'),
        meta: { title: '设置' }
      },
      {
        path: '/services',
        name: 'Services',
        component: () => import('@/views/Services.vue'),
        meta: { title: '服务管理' }
      },
      {
        path: '/services/create',
        name: 'ServiceCreate',
        component: () => import('@/views/ServiceCreate.vue'),
        meta: { title: '创建服务' }
      },
      {
        path: '/services/:id',
        name: 'ServiceDetail',
        component: () => import('@/views/ServiceDetail.vue'),
        meta: { title: '服务详情' }
      },
      {
        path: '/services/:id/docs',
        name: 'ServiceDocs',
        component: () => import('@/views/ServiceDocs.vue'),
        meta: { title: 'API文档' }
      }
    ]
  },
  {
    path: '/404',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: { title: '页面未找到' }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/404'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  
  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - 视觉检测应用`
  }
  
  // 检查是否需要认证
  if (to.meta.requiresAuth) {
    if (!authStore.isAuthenticated) {
      // 未登录，跳转到登录页
      next({
        path: '/login',
        query: { redirect: to.fullPath }
      })
      return
    }
    
    // 检查token是否过期
    if (authStore.isTokenExpired()) {
      try {
        await authStore.autoRefreshToken()
      } catch (error) {
        console.error('Token刷新失败:', error)
        next({
          path: '/login',
          query: { redirect: to.fullPath }
        })
        return
      }
    }
  }
  
  // 检查是否需要游客状态（如登录页）
  if (to.meta.requiresGuest && authStore.isAuthenticated) {
    next('/home')
    return
  }
  
  next()
})

export default router