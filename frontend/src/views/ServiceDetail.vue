<template>
  <div class="service-detail-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <a-button type="text" @click="$router.back()" class="back-button">
            <template #icon>
              <ArrowLeftOutlined />
            </template>
            返回
          </a-button>
          <div class="header-info" v-if="serviceInfo">
            <h1 class="page-title">{{ serviceInfo.service_name }}</h1>
            <div class="service-meta">
              <a-tag :color="getStatusColor(serviceInfo.status)">
                {{ getStatusText(serviceInfo.status) }}
              </a-tag>
              <span class="service-id">ID: {{ serviceInfo.id }}</span>
              <span class="created-time">创建于 {{ formatDateTime(serviceInfo.created_at) }}</span>
            </div>
          </div>
        </div>
        <div class="header-right" v-if="serviceInfo">
          <a-space>
            <a-button @click="showTokenModal = true">
              <template #icon>
                <KeyOutlined />
              </template>
              Token管理
            </a-button>
            <a-button @click="$router.push(`/services/${serviceId}/docs`)">
              <template #icon>
                <FileTextOutlined />
              </template>
              API文档
            </a-button>
            <a-dropdown>
              <template #overlay>
                <a-menu @click="handleAction">
                  <a-menu-item key="edit">
                    <EditOutlined />
                    编辑服务
                  </a-menu-item>
                  <a-menu-divider />
                  <a-menu-item key="enable" v-if="serviceInfo.status !== 'active'">
                    <PlayCircleOutlined />
                    启用服务
                  </a-menu-item>
                  <a-menu-item key="disable" v-if="serviceInfo.status === 'active'">
                    <PauseCircleOutlined />
                    禁用服务
                  </a-menu-item>
                  <a-menu-divider />
                  <a-menu-item key="delete" class="text-red-500">
                    <DeleteOutlined />
                    删除服务
                  </a-menu-item>
                </a-menu>
              </template>
              <a-button>
                更多操作
                <DownOutlined />
              </a-button>
            </a-dropdown>
          </a-space>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <a-spin size="large" />
    </div>

    <!-- 服务详情内容 -->
    <div v-else-if="serviceInfo" class="service-content">
      <!-- 基本信息和统计概览 -->
      <a-row :gutter="24" class="info-row">
        <a-col :span="16">
          <a-card title="基本信息" :bordered="false">
            <div class="info-grid">
              <div class="info-item">
                <span class="info-label">服务描述</span>
                <span class="info-value">{{ serviceInfo.description || '暂无描述' }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">检测模型</span>
                <span class="info-value">{{ serviceInfo.model_name }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">置信度阈值</span>
                <span class="info-value">{{ (serviceInfo.confidence_threshold * 100).toFixed(0) }}%</span>
              </div>
              <div class="info-item">
                <span class="info-label">API端点</span>
                <code class="info-value api-endpoint">{{ serviceInfo.api_endpoint }}</code>
                <a-button type="link" size="small" @click="copyToClipboard(serviceInfo.api_endpoint)">
                  复制
                </a-button>
              </div>
              <div class="info-item">
                <span class="info-label">调用频率限制</span>
                <span class="info-value">{{ serviceInfo.rate_limit }} 次/分钟</span>
              </div>
              <div class="info-item">
                <span class="info-label">最大文件大小</span>
                <span class="info-value">{{ formatFileSize(serviceInfo.max_file_size) }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">允许的文件格式</span>
                <div class="info-value">
                  <a-tag v-for="format in serviceInfo.allowed_formats" :key="format" size="small">
                    {{ format.toUpperCase() }}
                  </a-tag>
                </div>
              </div>
              <div class="info-item" v-if="serviceInfo.detection_classes.length > 0">
                <span class="info-label">检测类别</span>
                <div class="info-value">
                  <a-tag v-for="cls in serviceInfo.detection_classes" :key="cls" size="small">
                    {{ cls }}
                  </a-tag>
                </div>
              </div>
            </div>
          </a-card>
        </a-col>
        <a-col :span="8">
          <a-card title="统计概览" :bordered="false">
            <div class="stats-grid">
              <div class="stat-item">
                <div class="stat-value">{{ serviceStats?.total_calls || 0 }}</div>
                <div class="stat-label">总调用次数</div>
              </div>
              <div class="stat-item">
                <div class="stat-value success-rate">
                  {{ (serviceStats?.success_rate || 0).toFixed(1) }}%
                </div>
                <div class="stat-label">成功率</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">
                  {{ (serviceStats?.avg_response_time || 0).toFixed(2) }}s
                </div>
                <div class="stat-label">平均响应时间</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ serviceStats?.unique_ips || 0 }}</div>
                <div class="stat-label">独立IP数</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ serviceStats?.active_tokens || 0 }}</div>
                <div class="stat-label">活跃Token数</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ serviceStats?.total_detections || 0 }}</div>
                <div class="stat-label">总检测数量</div>
              </div>
            </div>
            <div class="last-called" v-if="serviceStats?.last_called_at">
              <span class="last-called-label">最后调用时间:</span>
              <span class="last-called-time">{{ formatDateTime(serviceStats.last_called_at) }}</span>
            </div>
          </a-card>
        </a-col>
      </a-row>

      <!-- 图表和日志 -->
      <a-row :gutter="24" class="charts-row">
        <a-col :span="12">
          <a-card title="调用趋势" :bordered="false">
            <div class="chart-container">
              <div v-if="dailyStatsLoading" class="chart-loading">
                <a-spin />
              </div>
              <div v-else-if="dailyStats.length === 0" class="chart-empty">
                <a-empty description="暂无数据" />
              </div>
              <div v-else class="chart-content">
                <!-- 这里可以集成图表库如ECharts -->
                <div class="simple-chart">
                  <div v-for="(stat, index) in dailyStats.slice(-7)" :key="index" class="chart-bar">
                    <div class="bar-container">
                      <div class="bar" :style="{ height: `${(stat.total_calls / maxDailyCalls) * 100}%` }"></div>
                    </div>
                    <div class="bar-label">{{ formatDate(stat.date) }}</div>
                    <div class="bar-value">{{ stat.total_calls }}</div>
                  </div>
                </div>
              </div>
            </div>
          </a-card>
        </a-col>
        <a-col :span="12">
          <a-card title="最近调用日志" :bordered="false">
            <div class="logs-container">
              <div v-if="logsLoading" class="logs-loading">
                <a-spin />
              </div>
              <div v-else-if="recentLogs.length === 0" class="logs-empty">
                <a-empty description="暂无调用记录" />
              </div>
              <div v-else class="logs-list">
                <div v-for="log in recentLogs" :key="log.id" class="log-item">
                  <div class="log-header">
                    <span class="log-method">{{ log.http_method }}</span>
                    <a-tag :color="log.success ? 'green' : 'red'" size="small">
                      {{ log.status_code }}
                    </a-tag>
                    <span class="log-time">{{ formatTime(log.created_at) }}</span>
                  </div>
                  <div class="log-details">
                    <span class="log-ip">{{ log.client_ip }}</span>
                    <span class="log-duration" v-if="log.processing_time">
                      {{ (log.processing_time * 1000).toFixed(0) }}ms
                    </span>
                    <span class="log-detections" v-if="log.detection_count">
                      {{ log.detection_count }} 个检测
                    </span>
                  </div>
                </div>
              </div>
              <div class="logs-footer">
                <a-button type="link" @click="viewAllLogs">
                  查看全部日志
                </a-button>
              </div>
            </div>
          </a-card>
        </a-col>
      </a-row>
    </div>

    <!-- Token管理弹窗 -->
    <a-modal v-model:open="showTokenModal" title="Token管理" width="800px" :footer="null">
      <div class="token-management">
        <div class="token-header">
          <a-button type="primary" @click="showCreateTokenModal = true">
            <template #icon>
              <PlusOutlined />
            </template>
            创建Token
          </a-button>
        </div>
        <a-table :columns="tokenColumns" :data-source="tokens" :loading="tokensLoading" row-key="id" size="small">
          <template #status="{ record }">
            <a-tag :color="record.is_valid ? 'green' : 'red'">
              {{ record.is_valid ? '有效' : '无效' }}
            </a-tag>
          </template>
          <template #actions="{ record }">
            <a-space>
              <a-button type="link" size="small" @click="toggleToken(record)">
                {{ record.is_active ? '停用' : '激活' }}
              </a-button>
              <a-button type="link" size="small" danger @click="revokeToken(record)">
                撤销
              </a-button>
            </a-space>
          </template>
        </a-table>
      </div>
    </a-modal>

    <!-- 创建Token弹窗 -->
    <a-modal v-model:open="showCreateTokenModal" title="创建访问Token" @ok="createToken" :confirm-loading="creatingToken">
      <a-form :model="tokenForm" layout="vertical">
        <a-form-item label="Token名称" required>
          <a-input v-model:value="tokenForm.token_name" placeholder="请输入Token名称" />
        </a-form-item>
        <a-form-item label="过期时间">
          <a-select v-model:value="tokenForm.expires_hours" placeholder="选择过期时间">
            <a-select-option :value="24">1天</a-select-option>
            <a-select-option :value="168">7天</a-select-option>
            <a-select-option :value="720">30天</a-select-option>
            <a-select-option :value="null">永不过期</a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import {
  ArrowLeftOutlined,
  KeyOutlined,
  FileTextOutlined,
  EditOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  DeleteOutlined,
  DownOutlined,
  PlusOutlined
} from '@ant-design/icons-vue'
import { apiClient, formatFileSize } from '@/utils/api'

const route = useRoute()
const router = useRouter()
const serviceId = route.params.id

// 响应式数据
const loading = ref(true)
const serviceInfo = ref(null)
const serviceStats = ref(null)
const dailyStats = ref([])
const dailyStatsLoading = ref(false)
const recentLogs = ref([])
const logsLoading = ref(false)
const showTokenModal = ref(false)
const showCreateTokenModal = ref(false)
const tokens = ref([])
const tokensLoading = ref(false)
const creatingToken = ref(false)

// Token表单
const tokenForm = reactive({
  token_name: '',
  expires_hours: 168 // 默认7天
})

// Token表格列
const tokenColumns = [
  { title: 'Token名称', dataIndex: 'token_name', key: 'token_name' },
  { title: '前缀', dataIndex: 'token_prefix', key: 'token_prefix' },
  { title: '状态', key: 'status', slots: { customRender: 'status' } },
  { title: '使用次数', dataIndex: 'usage_count', key: 'usage_count' },
  { title: '创建时间', dataIndex: 'created_at', key: 'created_at', customRender: ({ text }) => formatDateTime(text) },
  { title: '操作', key: 'actions', slots: { customRender: 'actions' } }
]

// 计算属性
const maxDailyCalls = computed(() => {
  return Math.max(...dailyStats.value.map(stat => stat.total_calls), 1)
})

// 方法
const loadServiceInfo = async () => {
  try {
    const response = await apiClient.getService(serviceId)
    serviceInfo.value = response
  } catch (error) {
    console.error('加载服务信息失败:', error)
    message.error('加载服务信息失败')
  }
}

const loadServiceStats = async () => {
  try {
    const response = await apiClient.getServiceStats(serviceId)
    serviceStats.value = response
  } catch (error) {
    console.error('加载服务统计失败:', error)
  }
}

const loadDailyStats = async () => {
  try {
    dailyStatsLoading.value = true
    const response = await apiClient.getDailyStats(serviceId, { days: 30 })
    dailyStats.value = response
  } catch (error) {
    console.error('加载日统计失败:', error)
  } finally {
    dailyStatsLoading.value = false
  }
}

const loadRecentLogs = async () => {
  try {
    logsLoading.value = true
    const response = await apiClient.getServiceLogs(serviceId, { page: 1, page_size: 10 })
    recentLogs.value = response.logs
  } catch (error) {
    console.error('加载调用日志失败:', error)
  } finally {
    logsLoading.value = false
  }
}

const loadTokens = async () => {
  try {
    tokensLoading.value = true
    const response = await apiClient.getTokens(serviceId)
    tokens.value = response.tokens
  } catch (error) {
    console.error('加载Token列表失败:', error)
  } finally {
    tokensLoading.value = false
  }
}

const handleAction = async ({ key }) => {
  switch (key) {
    case 'edit':
      router.push(`/services/${serviceId}/edit`)
      break
    case 'enable':
      await enableService()
      break
    case 'disable':
      await disableService()
      break
    case 'delete':
      await deleteService()
      break
  }
}

const enableService = async () => {
  try {
    await apiClient.enableService(serviceId)
    message.success('服务已启用')
    await loadServiceInfo()
  } catch (error) {
    console.error('启用服务失败:', error)
    message.error('启用服务失败')
  }
}

const disableService = async () => {
  Modal.confirm({
    title: '确认禁用服务',
    content: '确定要禁用此服务吗？禁用后将无法接收新的API调用。',
    onOk: async () => {
      try {
        await apiClient.disableService(serviceId)
        message.success('服务已禁用')
        await loadServiceInfo()
      } catch (error) {
        console.error('禁用服务失败:', error)
        message.error('禁用服务失败')
      }
    }
  })
}

const deleteService = async () => {
  Modal.confirm({
    title: '确认删除服务',
    content: '确定要删除此服务吗？此操作不可恢复，相关的Token和调用记录也将被删除。',
    okType: 'danger',
    onOk: async () => {
      try {
        await apiClient.deleteService(serviceId)
        message.success('服务已删除')
        router.push('/services')
      } catch (error) {
        console.error('删除服务失败:', error)
        message.error('删除服务失败')
      }
    }
  })
}

const createToken = async () => {
  try {
    creatingToken.value = true
    const response = await apiClient.createToken(serviceId, tokenForm)
    message.success('Token创建成功')
    showCreateTokenModal.value = false
    tokenForm.token_name = ''
    tokenForm.expires_hours = 168
    await loadTokens()

    // 显示新创建的Token，允许用户复制
    Modal.success({
      title: 'Token创建成功',
      content: [
        '请妥善保存以下访问Token，它只会显示这一次：',
        `${response.access_token}`,
        '点击下方按钮可复制到剪贴板。'
      ].join('\n'),
      width: 600,
      okText: '复制Token',
      onOk: () => {
        copyToClipboard(response.access_token)
      }
    })
  } catch (error) {
    console.error('创建Token失败:', error)
    message.error('创建Token失败')
  } finally {
    creatingToken.value = false
  }
}

const toggleToken = async (token) => {
  try {
    if (token.is_active) {
      await apiClient.deactivateToken(serviceId, token.id)
      message.success('Token已停用')
    } else {
      await apiClient.activateToken(serviceId, token.id)
      message.success('Token已激活')
    }
    await loadTokens()
  } catch (error) {
    console.error('切换Token状态失败:', error)
    message.error('操作失败')
  }
}

const revokeToken = async (token) => {
  Modal.confirm({
    title: '确认撤销Token',
    content: `确定要撤销Token "${token.token_name}" 吗？撤销后将无法恢复。`,
    onOk: async () => {
      try {
        await apiClient.revokeToken(serviceId, token.id)
        message.success('Token已撤销')
        await loadTokens()
      } catch (error) {
        console.error('撤销Token失败:', error)
        message.error('撤销Token失败')
      }
    }
  })
}

const viewAllLogs = () => {
  router.push(`/services/${serviceId}/logs`)
}

const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    message.success('已复制到剪贴板')
  } catch (error) {
    console.error('复制失败:', error)
    message.error('复制失败，请手动复制')
  }
}

// 工具函数
const getStatusColor = (status) => {
  const colors = {
    active: 'green',
    disabled: 'red',
    suspended: 'orange'
  }
  return colors[status] || 'default'
}

const getStatusText = (status) => {
  const texts = {
    active: '活跃',
    disabled: '禁用',
    suspended: '暂停'
  }
  return texts[status] || status
}

const formatDateTime = (dateTime) => {
  if (!dateTime) return '-'
  return new Date(dateTime).toLocaleString('zh-CN')
}

const formatDate = (date) => {
  return new Date(date).toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
}

const formatTime = (dateTime) => {
  return new Date(dateTime).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

// 生命周期
onMounted(async () => {
  try {
    await Promise.all([
      loadServiceInfo(),
      loadServiceStats(),
      loadDailyStats(),
      loadRecentLogs()
    ])
    
    // 检查URL参数，如果有tab=tokens则自动打开Token管理弹窗
    if (route.query.tab === 'tokens') {
      showTokenModal.value = true
    }
  } finally {
    loading.value = false
  }
})

// 监听Token弹窗打开
const handleTokenModalOpen = () => {
  if (showTokenModal.value) {
    loadTokens()
  }
}

// 监听弹窗状态
watch(() => showTokenModal.value, handleTokenModalOpen)
</script>

<style scoped>
.service-detail-page {
  padding: 24px;
  background-color: #f5f5f5;
  min-height: 100vh;
}

.page-header {
  margin-bottom: 24px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.header-left {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.back-button {
  padding: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: #1f2937;
}

.service-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 14px;
  color: #6b7280;
}

.service-id {
  font-family: monospace;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 400px;
}

.info-row {
  margin-bottom: 24px;
}

.info-grid {
  display: grid;
  gap: 16px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.info-label {
  font-weight: 500;
  color: #374151;
  min-width: 120px;
}

.info-value {
  flex: 1;
}

.api-endpoint {
  background-color: #f3f4f6;
  padding: 4px 8px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 12px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
}

.success-rate {
  color: #059669;
}

.stat-label {
  font-size: 12px;
  color: #6b7280;
}

.last-called {
  text-align: center;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
  font-size: 12px;
  color: #6b7280;
}

.last-called-label {
  display: block;
  margin-bottom: 4px;
}

.last-called-time {
  font-weight: 500;
  color: #374151;
}

.charts-row {
  margin-bottom: 24px;
}

.chart-container {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-loading,
.chart-empty {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.simple-chart {
  display: flex;
  align-items: end;
  gap: 8px;
  height: 150px;
  padding: 20px 0;
}

.chart-bar {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
}

.bar-container {
  height: 100px;
  width: 20px;
  background-color: #f3f4f6;
  border-radius: 2px;
  display: flex;
  align-items: end;
  margin-bottom: 8px;
}

.bar {
  width: 100%;
  background-color: #1890ff;
  border-radius: 2px;
  min-height: 2px;
}

.bar-label {
  font-size: 10px;
  color: #6b7280;
  margin-bottom: 2px;
}

.bar-value {
  font-size: 10px;
  font-weight: 500;
  color: #374151;
}

.logs-container {
  height: 300px;
  display: flex;
  flex-direction: column;
}

.logs-loading,
.logs-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logs-list {
  flex: 1;
  overflow-y: auto;
}

.log-item {
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.log-item:last-child {
  border-bottom: none;
}

.log-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.log-method {
  font-family: monospace;
  font-size: 12px;
  font-weight: 500;
  color: #374151;
}

.log-time {
  font-size: 12px;
  color: #6b7280;
  margin-left: auto;
}

.log-details {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 11px;
  color: #6b7280;
}

.log-ip {
  font-family: monospace;
}

.logs-footer {
  padding-top: 8px;
  border-top: 1px solid #f0f0f0;
  text-align: center;
}

.token-management {
  max-height: 400px;
  overflow-y: auto;
}

.token-header {
  margin-bottom: 16px;
  display: flex;
  justify-content: flex-end;
}

.text-red-500 {
  color: #ef4444;
}

:deep(.ant-card-head-title) {
  font-weight: 600;
}

:deep(.ant-table-thead > tr > th) {
  background-color: #fafafa;
  font-weight: 600;
}
</style>