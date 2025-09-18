<template>
  <div id="app">
    <a-config-provider :locale="zhCN">
      <router-view />
    </a-config-provider>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { ConfigProvider } from 'ant-design-vue'
import zhCN from 'ant-design-vue/es/locale/zh_CN'
import { useAuthStore } from './stores/auth'

// 全局样式配置
const theme = {
  token: {
    colorPrimary: '#1890ff',
    borderRadius: 6,
    fontSize: 14
  }
}

// 初始化认证状态
const authStore = useAuthStore()

onMounted(() => {
  // 在组件挂载后初始化认证状态
  authStore.initAuth()
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB',
    'Microsoft YaHei', 'Helvetica Neue', Helvetica, Arial, sans-serif;
  background-color: #f5f5f5;
  color: #333;
}

#app {
  min-height: 100vh;
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 工具类 */
.text-center {
  text-align: center;
}

.text-left {
  text-align: left;
}

.text-right {
  text-align: right;
}

.mb-16 {
  margin-bottom: 16px;
}

.mb-24 {
  margin-bottom: 24px;
}

.mt-16 {
  margin-top: 16px;
}

.mt-24 {
  margin-top: 24px;
}

.full-width {
  width: 100%;
}

.flex-center {
  display: flex;
  justify-content: center;
  align-items: center;
}

.flex-between {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>