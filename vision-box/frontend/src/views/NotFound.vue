<template>
  <div class="not-found">
    <a-result
      status="404"
      title="404"
      sub-title="抱歉，您访问的页面不存在"
    >
      <template #extra>
        <a-space>
          <a-button type="primary" @click="goHome">
            <home-outlined />
            返回首页
          </a-button>
          <a-button @click="goBack">
            <arrow-left-outlined />
            返回上页
          </a-button>
        </a-space>
      </template>
    </a-result>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import {
  HomeOutlined,
  ArrowLeftOutlined
} from '@ant-design/icons-vue'

const router = useRouter()

const goHome = () => {
  router.push('/')
}

const goBack = () => {
  router.go(-1)
}
</script>

<style scoped>
.not-found {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  padding: 40px 20px;
}
</style>