<template>
  <div class="history">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          <history-outlined />
          检测历史
        </h1>
        <p class="page-description">查看和管理您的检测历史记录</p>
      </div>
      <div class="header-actions">
        <a-space>
          <a-button @click="refreshHistory">
            <reload-outlined />
            刷新
          </a-button>
          <a-button type="primary" @click="goToDetect">
            <plus-outlined />
            新建检测
          </a-button>
        </a-space>
      </div>
    </div>

    <!-- 筛选和搜索 -->
    <a-card class="filter-card">
      <a-row :gutter="[16, 16]">
        <a-col :xs="24" :sm="12" :md="6">
          <a-input
            v-model:value="searchKeyword"
            placeholder="搜索文件名"
            allow-clear
            @change="handleSearch"
          >
            <template #prefix>
              <search-outlined />
            </template>
          </a-input>
        </a-col>
        <a-col :xs="24" :sm="12" :md="6">
          <a-select
            v-model:value="filterStatus"
            placeholder="筛选状态"
            allow-clear
            @change="handleFilter"
          >
            <a-select-option value="">全部状态</a-select-option>
            <a-select-option value="completed">已完成</a-select-option>
            <a-select-option value="processing">处理中</a-select-option>
            <a-select-option value="failed">失败</a-select-option>
          </a-select>
        </a-col>
        <a-col :xs="24" :sm="12" :md="6">
          <a-select
            v-model:value="filterFileType"
            placeholder="文件类型"
            allow-clear
            @change="handleFilter"
          >
            <a-select-option value="">全部类型</a-select-option>
            <a-select-option value="image">图片</a-select-option>
            <a-select-option value="video">视频</a-select-option>
          </a-select>
        </a-col>
        <a-col :xs="24" :sm="12" :md="6">
          <a-range-picker
            v-model:value="dateRange"
            @change="handleFilter"
            placeholder="选择日期范围"
          />
        </a-col>
      </a-row>
    </a-card>

    <!-- 统计信息 -->
    <a-row :gutter="[16, 16]" class="stats-row">
      <a-col :xs="24" :sm="6">
        <a-card class="stat-card">
          <a-statistic
            title="总任务数"
            :value="totalTasks"
            :value-style="{ color: '#1890ff' }"
          />
        </a-card>
      </a-col>
      <a-col :xs="24" :sm="6">
        <a-card class="stat-card">
          <a-statistic
            title="成功任务"
            :value="completedTasks"
            :value-style="{ color: '#52c41a' }"
          />
        </a-card>
      </a-col>
      <a-col :xs="24" :sm="6">
        <a-card class="stat-card">
          <a-statistic
            title="失败任务"
            :value="failedTasks"
            :value-style="{ color: '#ff4d4f' }"
          />
        </a-card>
      </a-col>
      <a-col :xs="24" :sm="6">
        <a-card class="stat-card">
          <a-statistic
            title="成功率"
            :value="successRate"
            suffix="%"
            :precision="1"
            :value-style="{ color: '#722ed1' }"
          />
        </a-card>
      </a-col>
    </a-row>

    <!-- 历史记录列表 -->
    <a-card class="history-card">
      <template #title>
        <div class="card-title">
          <span>历史记录</span>
          <a-badge :count="filteredHistory.length" :number-style="{ backgroundColor: '#52c41a' }" />
        </div>
      </template>
      
      <template #extra>
        <a-space>
          <a-button 
            size="small" 
            :disabled="selectedRowKeys.length === 0"
            @click="batchDelete"
          >
            <delete-outlined />
            批量删除
          </a-button>
          <a-button 
            size="small" 
            :disabled="selectedRowKeys.length === 0"
            @click="batchDownload"
          >
            <download-outlined />
            批量下载
          </a-button>
        </a-space>
      </template>

      <a-table
        :columns="columns"
        :data-source="filteredHistory"
        :loading="loading"
        :pagination="paginationConfig"
        :row-selection="rowSelection"
        :scroll="{ x: 1000 }"
        row-key="id"
      >
        <!-- 文件信息 -->
        <template #fileInfo="{ record }">
          <div class="file-info">
            <div class="file-icon">
              <file-image-outlined v-if="record.file_info?.file_type === 'image'" />
              <video-camera-outlined v-else />
            </div>
            <div class="file-details">
              <div class="file-name">{{ record.file_info?.filename || record.task_name }}</div>
              <div class="file-meta">
                {{ formatFileSize(record.file_info?.file_size || 0) }} • {{ record.file_info?.file_type || 'unknown' }}
              </div>
            </div>
          </div>
        </template>

        <!-- 状态 -->
        <template #status="{ record }">
          <a-tag :color="getStatusColor(record.status)">
            <component :is="getStatusIcon(record.status)" />
            {{ getStatusText(record.status) }}
          </a-tag>
        </template>

        <!-- 检测结果 -->
        <template #result="{ record }">
          <div v-if="record.status === 'completed' && record.result_summary">
            <div class="result-summary">
              <span class="detection-count">
                {{ record.result_summary.total_detections || 0 }} 个对象
              </span>
              <span class="confidence-avg">
                平均置信度: {{ (record.result_summary.average_confidence * 100).toFixed(1) || 0 }}%
              </span>
            </div>
          </div>
          <span v-else class="no-result">-</span>
        </template>

        <!-- 操作 -->
        <template #actions="{ record }">
          <a-space>
            <a-tooltip title="查看详情">
              <a-button 
                type="text" 
                size="small" 
                @click="viewDetail(record)"
                :icon="h(EyeOutlined)"
              />
            </a-tooltip>
            
            <a-tooltip title="下载结果" v-if="record.status === 'completed'">
              <a-dropdown>
                <a-button 
                  type="text" 
                  size="small" 
                  :icon="h(DownloadOutlined)"
                />
                <template #overlay>
                  <a-menu @click="({ key }) => downloadResult(record.id, key)">
                    <a-menu-item key="json">JSON格式</a-menu-item>
                    <a-menu-item key="csv">CSV格式</a-menu-item>
                  </a-menu>
                </template>
              </a-dropdown>
            </a-tooltip>
            
            <a-tooltip title="重新检测">
              <a-button 
                type="text" 
                size="small" 
                @click="redetect(record)"
                :icon="h(RedoOutlined)"
              />
            </a-tooltip>
            
            <a-tooltip title="删除">
              <a-popconfirm
                title="确定要删除这条记录吗？"
                @confirm="deleteRecord(record.id)"
              >
                <a-button 
                  type="text" 
                  size="small" 
                  danger
                  :icon="h(DeleteOutlined)"
                />
              </a-popconfirm>
            </a-tooltip>
          </a-space>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, h } from 'vue'
import { useRouter } from 'vue-router'
import { useDetectionStore } from '@/stores/detection'
import { formatFileSize } from '@/utils/api'
import { message, Modal } from 'ant-design-vue'
import dayjs from 'dayjs'
import {
  HistoryOutlined,
  ReloadOutlined,
  PlusOutlined,
  SearchOutlined,
  FileImageOutlined,
  VideoCameraOutlined,
  EyeOutlined,
  DownloadOutlined,
  DeleteOutlined,
  RedoOutlined,
  CheckCircleOutlined,
  LoadingOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined
} from '@ant-design/icons-vue'

const router = useRouter()
const detectionStore = useDetectionStore()

// 响应式数据
const loading = ref(false)
const searchKeyword = ref('')
const filterStatus = ref('')
const filterFileType = ref('')
const dateRange = ref([])
const selectedRowKeys = ref([])

// 表格列配置
const columns = [
  {
    title: '文件信息',
    key: 'fileInfo',
    width: 250,
    slots: { customRender: 'fileInfo' }
  },
  {
    title: '状态',
    key: 'status',
    width: 120,
    slots: { customRender: 'status' }
  },
  {
    title: '模型',
    dataIndex: 'model_name',
    key: 'model_name',
    width: 100
  },
  {
    title: '置信度',
    dataIndex: 'confidence_threshold',
    key: 'confidence_threshold',
    width: 100,
    customRender: ({ text }) => (text * 100).toFixed(0) + '%'
  },
  {
    title: '检测结果',
    key: 'result',
    width: 200,
    slots: { customRender: 'result' }
  },
  {
    title: '创建时间',
    dataIndex: 'created_at',
    key: 'created_at',
    width: 150,
    customRender: ({ text }) => dayjs(text).format('MM-DD HH:mm')
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    fixed: 'right',
    slots: { customRender: 'actions' }
  }
]

// 分页配置
const paginationConfig = {
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
}

// 行选择配置
const rowSelection = {
  selectedRowKeys: selectedRowKeys,
  onChange: (keys) => {
    selectedRowKeys.value = keys
  }
}

// 计算属性
const filteredHistory = computed(() => {
  let history = detectionStore.detectionHistory
  
  // 搜索过滤
  if (searchKeyword.value) {
    history = history.filter(item => 
      item.task_name?.toLowerCase().includes(searchKeyword.value.toLowerCase()) ||
      item.file_info?.filename?.toLowerCase().includes(searchKeyword.value.toLowerCase())
    )
  }
  
  // 状态过滤
  if (filterStatus.value) {
    history = history.filter(item => item.status === filterStatus.value)
  }
  
  // 文件类型过滤
  if (filterFileType.value) {
    history = history.filter(item => item.file_info?.file_type === filterFileType.value)
  }
  
  // 日期范围过滤
  if (dateRange.value && dateRange.value.length === 2) {
    const [start, end] = dateRange.value
    history = history.filter(item => {
      const itemDate = dayjs(item.created_at)
      return itemDate.isAfter(start.startOf('day')) && itemDate.isBefore(end.endOf('day'))
    })
  }
  
  return history
})

const totalTasks = computed(() => detectionStore.detectionHistory.length)
const completedTasks = computed(() => detectionStore.completedTasks.length)
const failedTasks = computed(() => detectionStore.failedTasks.length)
const successRate = computed(() => {
  return totalTasks.value > 0 ? (completedTasks.value / totalTasks.value) * 100 : 0
})

// 方法
const refreshHistory = async () => {
  loading.value = true
  try {
    await detectionStore.loadHistory()
    message.success('刷新成功')
  } catch (error) {
    console.error('刷新失败:', error)
  } finally {
    loading.value = false
  }
}

const goToDetect = () => {
  router.push('/detect')
}

const handleSearch = () => {
  // 搜索逻辑已在计算属性中处理
}

const handleFilter = () => {
  // 过滤逻辑已在计算属性中处理
}

const getStatusColor = (status) => {
  const colors = {
    pending: 'blue',
    processing: 'orange',
    completed: 'green',
    failed: 'red'
  }
  return colors[status] || 'default'
}

const getStatusIcon = (status) => {
  const icons = {
    pending: ClockCircleOutlined,
    processing: LoadingOutlined,
    completed: CheckCircleOutlined,
    failed: CloseCircleOutlined
  }
  return icons[status] || ClockCircleOutlined
}

const getStatusText = (status) => {
  const texts = {
    pending: '等待中',
    processing: '处理中',
    completed: '已完成',
    failed: '失败'
  }
  return texts[status] || '未知'
}

const getAverageConfidence = (detections) => {
  if (!detections || detections.length === 0) return 0
  const sum = detections.reduce((acc, d) => acc + d.confidence, 0)
  return ((sum / detections.length) * 100).toFixed(1)
}

const viewDetail = (record) => {
  router.push(`/result/${record.id}`)
}

const downloadResult = async (taskId, format) => {
  try {
    await detectionStore.downloadResult(taskId, format)
  } catch (error) {
    console.error('下载失败:', error)
  }
}

const redetect = (record) => {
  // 跳转到检测页面并预填参数
  router.push({
    path: '/detect',
    query: {
      file_id: record.file_record_id,
      model_name: record.model_name,
      confidence: record.confidence_threshold,
      classes: JSON.stringify(record.classes || [])
    }
  })
}

const deleteRecord = async (taskId) => {
  try {
    await detectionStore.deleteTask(taskId)
  } catch (error) {
    console.error('删除失败:', error)
  }
}

const batchDelete = () => {
  if (selectedRowKeys.value.length === 0) {
    message.warning('请选择要删除的记录')
    return
  }
  
  Modal.confirm({
    title: '批量删除确认',
    content: `确定要删除选中的 ${selectedRowKeys.value.length} 条记录吗？`,
    onOk: async () => {
      try {
        for (const taskId of selectedRowKeys.value) {
          await detectionStore.deleteTask(taskId)
        }
        selectedRowKeys.value = []
        message.success('批量删除成功')
      } catch (error) {
        console.error('批量删除失败:', error)
      }
    }
  })
}

const batchDownload = () => {
  if (selectedRowKeys.value.length === 0) {
    message.warning('请选择要下载的记录')
    return
  }
  
  Modal.confirm({
    title: '批量下载确认',
    content: `确定要下载选中的 ${selectedRowKeys.value.length} 条记录的结果吗？`,
    onOk: async () => {
      try {
        for (const taskId of selectedRowKeys.value) {
          await detectionStore.downloadResult(taskId, 'json')
        }
        message.success('批量下载完成')
      } catch (error) {
        console.error('批量下载失败:', error)
      }
    }
  })
}

onMounted(() => {
  refreshHistory()
})
</script>

<style scoped>
.history {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding: 24px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.header-content {
  flex: 1;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 12px;
  color: #333;
}

.page-description {
  color: #666;
  margin: 0;
}

.header-actions {
  flex-shrink: 0;
}

.filter-card {
  margin-bottom: 24px;
}

.stats-row {
  margin-bottom: 24px;
}

.stat-card {
  text-align: center;
}

.history-card {
  margin-bottom: 24px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.file-icon {
  font-size: 20px;
  color: #1890ff;
}

.file-details {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-weight: 500;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-meta {
  color: #666;
  font-size: 12px;
}

.result-summary {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detection-count {
  font-weight: 500;
  color: #1890ff;
}

.confidence-avg {
  font-size: 12px;
  color: #666;
}

.no-result {
  color: #ccc;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .header-actions {
    align-self: flex-end;
  }
  
  .stats-row .ant-col {
    margin-bottom: 16px;
  }
  
  .file-name {
    max-width: 120px;
  }
}
</style>