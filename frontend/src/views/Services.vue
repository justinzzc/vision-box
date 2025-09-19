<template>
  <div class="services-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">服务管理</h1>
          <p class="page-description">管理您发布的API服务，查看调用统计和配置信息</p>
        </div>
        <div class="header-right">
          <a-button type="primary" size="large" @click="$router.push('/services/create')">
            <template #icon>
              <PlusOutlined />
            </template>
            创建服务
          </a-button>
        </div>
      </div>
    </div>

    <!-- 筛选和搜索 -->
    <div class="filter-section">
      <a-card :bordered="false">
        <a-row :gutter="16" align="middle">
          <a-col :span="6">
            <a-input-search
              v-model:value="searchKeyword"
              placeholder="搜索服务名称或描述"
              allow-clear
              @search="handleSearch"
            />
          </a-col>
          <a-col :span="4">
            <a-select
              v-model:value="statusFilter"
              placeholder="状态筛选"
              allow-clear
              @change="handleSearch"
            >
              <a-select-option value="active">活跃</a-select-option>
              <a-select-option value="disabled">禁用</a-select-option>
              <a-select-option value="suspended">暂停</a-select-option>
            </a-select>
          </a-col>
          <a-col :span="4">
            <a-button @click="handleRefresh">
              <template #icon>
                <ReloadOutlined :spin="loading" />
              </template>
              刷新
            </a-button>
          </a-col>
        </a-row>
      </a-card>
    </div>

    <!-- 服务列表 -->
    <div class="services-list">
      <a-card :bordered="false">
        <a-table
          :columns="columns"
          :data-source="services"
          :loading="loading"
          :pagination="pagination"
          row-key="id"
          @change="handleTableChange"
        >
          <!-- 服务名称 -->
          <template #serviceName="{ record }">
            <div class="service-name-cell">
              <div class="service-title">
                <a-button type="link" @click="viewService(record.id)">
                  {{ record.service_name }}
                </a-button>
              </div>
              <div class="service-description" v-if="record.description">
                {{ record.description }}
              </div>
            </div>
          </template>

          <!-- 状态 -->
          <template #status="{ record }">
            <a-tag :color="getStatusColor(record.status)">
              {{ getStatusText(record.status) }}
            </a-tag>
          </template>

          <!-- 模型信息 -->
          <template #model="{ record }">
            <div class="model-info">
              <div class="model-name">{{ record.model_name }}</div>
              <div class="confidence">置信度: {{ record.confidence_threshold }}</div>
            </div>
          </template>

          <!-- 调用统计 -->
          <template #stats="{ record }">
            <div class="stats-info">
              <div class="total-calls">总调用: {{ record.total_calls }}</div>
              <div class="success-rate">
                成功率: 
                <span :class="getSuccessRateClass(record.success_rate)">
                  {{ record.success_rate.toFixed(1) }}%
                </span>
              </div>
            </div>
          </template>

          <!-- 最后调用时间 -->
          <template #lastCalled="{ record }">
            <span v-if="record.last_called_at">
              {{ formatDateTime(record.last_called_at) }}
            </span>
            <span v-else class="text-gray-400">从未调用</span>
          </template>

          <!-- 操作 -->
          <template #actions="{ record }">
            <a-space>
              <a-button type="link" size="small" @click="viewService(record.id)">
                查看
              </a-button>
              <a-button type="link" size="small" @click="editService(record.id)">
                编辑
              </a-button>
              <a-dropdown>
                <template #overlay>
                  <a-menu @click="({ key }) => handleAction(key, record)">
                    <a-menu-item key="tokens">
                      <UserOutlined />
                      Token管理
                    </a-menu-item>
                    <a-menu-item key="docs">
                      <FileTextOutlined />
                      API文档
                    </a-menu-item>
                    <a-menu-divider />
                    <a-menu-item key="enable" v-if="record.status !== 'active'">
                      <PlayCircleOutlined />
                      启用服务
                    </a-menu-item>
                    <a-menu-item key="disable" v-if="record.status === 'active'">
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
                <a-button type="link" size="small">
                  更多
                  <DownOutlined />
                </a-button>
              </a-dropdown>
            </a-space>
          </template>
        </a-table>
      </a-card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import {
  PlusOutlined,
  ReloadOutlined,
  UserOutlined,
  FileTextOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  DeleteOutlined,
  DownOutlined
} from '@ant-design/icons-vue'
import { apiClient } from '@/utils/api'

const router = useRouter()

// 响应式数据
const loading = ref(false)
const services = ref([])
const searchKeyword = ref('')
const statusFilter = ref(undefined)

// 分页配置
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
})

// 表格列配置
const columns = [
  {
    title: '服务名称',
    dataIndex: 'service_name',
    key: 'service_name',
    slots: { customRender: 'serviceName' },
    width: 300
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    slots: { customRender: 'status' },
    width: 100
  },
  {
    title: '模型配置',
    key: 'model',
    slots: { customRender: 'model' },
    width: 150
  },
  {
    title: '调用统计',
    key: 'stats',
    slots: { customRender: 'stats' },
    width: 150
  },
  {
    title: '最后调用',
    dataIndex: 'last_called_at',
    key: 'last_called_at',
    slots: { customRender: 'lastCalled' },
    width: 150
  },
  {
    title: '创建时间',
    dataIndex: 'created_at',
    key: 'created_at',
    width: 150,
    customRender: ({ text }) => formatDateTime(text)
  },
  {
    title: '操作',
    key: 'actions',
    slots: { customRender: 'actions' },
    width: 150,
    fixed: 'right'
  }
]

// 方法
const loadServices = async () => {
  try {
    loading.value = true
    const params = {
      page: pagination.current,
      page_size: pagination.pageSize,
      search: searchKeyword.value || undefined,
      status_filter: statusFilter.value || undefined
    }
    
    const response = await apiClient.getServices(params)
    services.value = response.services
    pagination.total = response.total
  } catch (error) {
    console.error('加载服务列表失败:', error)
    message.error('加载服务列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.current = 1
  loadServices()
}

const handleRefresh = () => {
  loadServices()
}

const handleTableChange = (pag) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  loadServices()
}

const viewService = (serviceId) => {
  router.push(`/services/${serviceId}`)
}

const editService = (serviceId) => {
  router.push(`/services/${serviceId}/edit`)
}

const handleAction = async (action, record) => {
  switch (action) {
    case 'tokens':
      // 跳转到服务详情页面并通过query参数标识要打开Token管理弹窗
      router.push(`/services/${record.id}?tab=tokens`)
      break
    case 'docs':
      router.push(`/services/${record.id}/docs`)
      break
    case 'enable':
      await enableService(record)
      break
    case 'disable':
      await disableService(record)
      break
    case 'delete':
      await deleteService(record)
      break
  }
}

const enableService = async (service) => {
  try {
    await apiClient.enableService(service.id)
    message.success('服务已启用')
    loadServices()
  } catch (error) {
    console.error('启用服务失败:', error)
    message.error('启用服务失败')
  }
}

const disableService = async (service) => {
  Modal.confirm({
    title: '确认禁用服务',
    content: `确定要禁用服务 "${service.service_name}" 吗？禁用后将无法接收新的API调用。`,
    okText: '确认',
    cancelText: '取消',
    onOk: async () => {
      try {
        await apiClient.disableService(service.id)
        message.success('服务已禁用')
        loadServices()
      } catch (error) {
        console.error('禁用服务失败:', error)
        message.error('禁用服务失败')
      }
    }
  })
}

const deleteService = async (service) => {
  Modal.confirm({
    title: '确认删除服务',
    content: `确定要删除服务 "${service.service_name}" 吗？此操作不可恢复，相关的Token和调用记录也将被删除。`,
    okText: '确认删除',
    cancelText: '取消',
    okType: 'danger',
    onOk: async () => {
      try {
        await apiClient.deleteService(service.id)
        message.success('服务已删除')
        loadServices()
      } catch (error) {
        console.error('删除服务失败:', error)
        message.error('删除服务失败')
      }
    }
  })
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

const getSuccessRateClass = (rate) => {
  if (rate >= 95) return 'text-green-600'
  if (rate >= 80) return 'text-yellow-600'
  return 'text-red-600'
}

const formatDateTime = (dateTime) => {
  if (!dateTime) return '-'
  return new Date(dateTime).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 生命周期
onMounted(() => {
  loadServices()
})
</script>

<style scoped>
.services-page {
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

.page-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: #1f2937;
}

.page-description {
  color: #6b7280;
  margin: 0;
  font-size: 14px;
}

.filter-section {
  margin-bottom: 24px;
}

.services-list {
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.service-name-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.service-title {
  font-weight: 500;
}

.service-description {
  font-size: 12px;
  color: #6b7280;
  line-height: 1.4;
}

.model-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.model-name {
  font-weight: 500;
  font-size: 13px;
}

.confidence {
  font-size: 12px;
  color: #6b7280;
}

.stats-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.total-calls {
  font-size: 13px;
  font-weight: 500;
}

.success-rate {
  font-size: 12px;
  color: #6b7280;
}

.text-gray-400 {
  color: #9ca3af;
}

.text-green-600 {
  color: #059669;
  font-weight: 500;
}

.text-yellow-600 {
  color: #d97706;
  font-weight: 500;
}

.text-red-600 {
  color: #dc2626;
  font-weight: 500;
}

.text-red-500 {
  color: #ef4444;
}

:deep(.ant-table-thead > tr > th) {
  background-color: #fafafa;
  font-weight: 600;
}

:deep(.ant-table-tbody > tr:hover > td) {
  background-color: #f8fafc;
}
</style>