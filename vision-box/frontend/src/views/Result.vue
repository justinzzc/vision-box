<template>
  <div class="result">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <a-button type="text" @click="goBack" class="back-btn">
          <arrow-left-outlined />
          返回
        </a-button>
        <div class="title-section">
          <h1 class="page-title">
            <eye-outlined />
            检测结果详情
          </h1>
          <p class="page-description" v-if="taskData">
            任务ID: {{ taskData.id }} • {{ formatDate(taskData.created_at) }}
          </p>
        </div>
      </div>
      <div class="header-actions" v-if="taskData">
        <a-space>
          <a-button @click="downloadResult('json')">
            <download-outlined />
            下载JSON
          </a-button>
          <a-button @click="downloadResult('csv')">
            <file-excel-outlined />
            下载CSV
          </a-button>
          <a-button type="primary" @click="redetect">
            <redo-outlined />
            重新检测
          </a-button>
        </a-space>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <a-spin size="large">
        <template #indicator>
          <loading-outlined style="font-size: 24px" spin />
        </template>
      </a-spin>
      <p>正在加载检测结果...</p>
    </div>

    <!-- 错误状态 -->
    <a-result
      v-else-if="error"
      status="error"
      title="加载失败"
      :sub-title="error"
    >
      <template #extra>
        <a-button type="primary" @click="loadTaskData">
          重新加载
        </a-button>
      </template>
    </a-result>

    <!-- 结果内容 -->
    <div v-else-if="taskData" class="result-content">
      <a-row :gutter="[24, 24]">
        <!-- 左侧：媒体展示 -->
        <a-col :xs="24" :lg="14">
          <a-card title="检测结果" class="media-card">
            <!-- 原始文件和标注结果切换 -->
            <div class="media-tabs">
              <a-radio-group v-model:value="activeMediaTab" button-style="solid">
                <a-radio-button value="original">原始文件</a-radio-button>
                <a-radio-button value="annotated">标注结果</a-radio-button>
              </a-radio-group>
            </div>
            
            <!-- 媒体展示区域 -->
            <div class="media-container">
              <!-- 图片展示 -->
              <div v-if="taskData.file_type === 'image'" class="image-container">
                <img 
                  :src="activeMediaTab === 'original' ? taskData.original_url : taskData.annotated_url"
                  :alt="activeMediaTab === 'original' ? '原始图片' : '标注结果'"
                  class="result-image"
                  @load="onImageLoad"
                  @error="onImageError"
                />
                
                <!-- 图片工具栏 -->
                <div class="image-toolbar">
                  <a-space>
                    <a-button size="small" @click="zoomIn">
                      <zoom-in-outlined />
                    </a-button>
                    <a-button size="small" @click="zoomOut">
                      <zoom-out-outlined />
                    </a-button>
                    <a-button size="small" @click="resetZoom">
                      <compress-outlined />
                      重置
                    </a-button>
                    <span class="zoom-level">{{ Math.round(zoomLevel * 100) }}%</span>
                  </a-space>
                </div>
              </div>
              
              <!-- 视频展示 -->
              <div v-else-if="taskData.file_type === 'video'" class="video-container">
                <video 
                  :src="activeMediaTab === 'original' ? taskData.original_url : taskData.annotated_url"
                  controls
                  class="result-video"
                  @loadedmetadata="onVideoLoad"
                  @error="onVideoError"
                >
                  您的浏览器不支持视频播放
                </video>
              </div>
            </div>
          </a-card>
        </a-col>
        
        <!-- 右侧：检测信息 -->
        <a-col :xs="24" :lg="10">
          <!-- 基本信息 -->
          <a-card title="基本信息" class="info-card">
            <a-descriptions :column="1" size="small">
              <a-descriptions-item label="文件名">
                {{ taskData.filename }}
              </a-descriptions-item>
              <a-descriptions-item label="文件类型">
                <a-tag :color="taskData.file_type === 'image' ? 'blue' : 'green'">
                  {{ taskData.file_type === 'image' ? '图片' : '视频' }}
                </a-tag>
              </a-descriptions-item>
              <a-descriptions-item label="文件大小">
                {{ formatFileSize(taskData.file_size) }}
              </a-descriptions-item>
              <a-descriptions-item label="检测模型">
                {{ getModelLabel(taskData.model_name) }}
              </a-descriptions-item>
              <a-descriptions-item label="置信度阈值">
                {{ (taskData.confidence * 100).toFixed(0) }}%
              </a-descriptions-item>
              <a-descriptions-item label="检测状态">
                <a-tag :color="getStatusColor(taskData.status)">
                  {{ getStatusText(taskData.status) }}
                </a-tag>
              </a-descriptions-item>
              <a-descriptions-item label="创建时间">
                {{ formatDate(taskData.created_at) }}
              </a-descriptions-item>
              <a-descriptions-item label="完成时间" v-if="taskData.completed_at">
                {{ formatDate(taskData.completed_at) }}
              </a-descriptions-item>
            </a-descriptions>
          </a-card>
          
          <!-- 检测统计 -->
          <a-card title="检测统计" class="stats-card" v-if="taskData.result">
            <a-row :gutter="[16, 16]">
              <a-col :span="12">
                <a-statistic 
                  title="检测对象" 
                  :value="getDetectionCount()" 
                  suffix="个"
                  :value-style="{ color: '#1890ff' }"
                />
              </a-col>
              <a-col :span="12">
                <a-statistic 
                  title="检测类别" 
                  :value="getUniqueClasses().length" 
                  suffix="种"
                  :value-style="{ color: '#52c41a' }"
                />
              </a-col>
              <a-col :span="12">
                <a-statistic 
                  title="平均置信度" 
                  :value="getAverageConfidence()" 
                  :precision="1"
                  suffix="%"
                  :value-style="{ color: '#722ed1' }"
                />
              </a-col>
              <a-col :span="12">
                <a-statistic 
                  title="最高置信度" 
                  :value="getMaxConfidence()" 
                  :precision="1"
                  suffix="%"
                  :value-style="{ color: '#fa8c16' }"
                />
              </a-col>
            </a-row>
          </a-card>
          
          <!-- 类别分布 -->
          <a-card title="类别分布" class="distribution-card" v-if="taskData.result">
            <div class="class-distribution">
              <div 
                v-for="(count, className) in getClassDistribution()" 
                :key="className"
                class="class-item"
              >
                <div class="class-info">
                  <span class="class-name">{{ className }}</span>
                  <span class="class-count">{{ count }}个</span>
                </div>
                <a-progress 
                  :percent="(count / getDetectionCount()) * 100" 
                  :show-info="false"
                  size="small"
                />
              </div>
            </div>
          </a-card>
        </a-col>
      </a-row>
      
      <!-- 详细检测结果 -->
      <a-card title="详细检测结果" class="details-card" v-if="taskData.result">
        <div class="table-actions">
          <a-space>
            <a-input
              v-model:value="searchText"
              placeholder="搜索类别名称"
              allow-clear
              style="width: 200px"
            >
              <template #prefix>
                <search-outlined />
              </template>
            </a-input>
            <a-select
              v-model:value="filterClass"
              placeholder="筛选类别"
              allow-clear
              style="width: 150px"
            >
              <a-select-option value="">全部类别</a-select-option>
              <a-select-option 
                v-for="className in getUniqueClasses()" 
                :key="className" 
                :value="className"
              >
                {{ className }}
              </a-select-option>
            </a-select>
          </a-space>
        </div>
        
        <a-table 
          :columns="detectionColumns" 
          :data-source="filteredDetections" 
          :pagination="tablePagination"
          :scroll="{ x: 800 }"
          row-key="index"
        >
          <template #confidence="{ record }">
            <a-progress 
              :percent="record.confidence * 100" 
              size="small"
              :format="(percent) => `${percent.toFixed(1)}%`"
            />
          </template>
          
          <template #bbox="{ record }">
            <a-tooltip :title="`位置: (${record.bbox.join(', ')})`">
              <a-tag color="blue">
                {{ record.bbox[0] }}, {{ record.bbox[1] }}
              </a-tag>
              <a-tag color="green">
                {{ record.bbox[2] - record.bbox[0] }} × {{ record.bbox[3] - record.bbox[1] }}
              </a-tag>
            </a-tooltip>
          </template>
        </a-table>
      </a-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDetectionStore } from '@/stores/detection'
import { formatFileSize } from '@/utils/api'
import { message } from 'ant-design-vue'
import dayjs from 'dayjs'
import {
  ArrowLeftOutlined,
  EyeOutlined,
  DownloadOutlined,
  FileExcelOutlined,
  RedoOutlined,
  LoadingOutlined,
  ZoomInOutlined,
  ZoomOutOutlined,
  CompressOutlined,
  SearchOutlined
} from '@ant-design/icons-vue'

const route = useRoute()
const router = useRouter()
const detectionStore = useDetectionStore()

// 响应式数据
const loading = ref(true)
const error = ref('')
const taskData = ref(null)
const activeMediaTab = ref('annotated')
const zoomLevel = ref(1)
const searchText = ref('')
const filterClass = ref('')

// 表格列配置
const detectionColumns = [
  {
    title: '序号',
    dataIndex: 'index',
    key: 'index',
    width: 80,
    customRender: ({ index }) => index + 1
  },
  {
    title: '类别',
    dataIndex: 'class_name',
    key: 'class_name',
    width: 120
  },
  {
    title: '置信度',
    key: 'confidence',
    width: 150,
    slots: { customRender: 'confidence' }
  },
  {
    title: '位置和大小',
    key: 'bbox',
    width: 200,
    slots: { customRender: 'bbox' }
  }
]

// 表格分页配置
const tablePagination = {
  current: 1,
  pageSize: 10,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
}

// 计算属性
const filteredDetections = computed(() => {
  if (!taskData.value?.result?.detections) return []
  
  let detections = taskData.value.result.detections.map((detection, index) => ({
    ...detection,
    index
  }))
  
  // 搜索过滤
  if (searchText.value) {
    detections = detections.filter(d => 
      d.class_name.toLowerCase().includes(searchText.value.toLowerCase())
    )
  }
  
  // 类别过滤
  if (filterClass.value) {
    detections = detections.filter(d => d.class_name === filterClass.value)
  }
  
  return detections
})

// 方法
const loadTaskData = async () => {
  const taskId = route.params.id
  if (!taskId) {
    error.value = '无效的任务ID'
    loading.value = false
    return
  }
  
  try {
    loading.value = true
    error.value = ''
    
    // 先从store中查找
    let task = detectionStore.getTaskById(taskId)
    
    if (!task) {
      // 如果store中没有，则从API获取
      const result = await detectionStore.apiClient.getResult(taskId)
      task = result
    }
    
    if (task) {
      taskData.value = task
    } else {
      error.value = '未找到指定的检测任务'
    }
  } catch (err) {
    console.error('加载任务数据失败:', err)
    error.value = '加载任务数据失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

const goBack = () => {
  router.go(-1)
}

const formatDate = (dateString) => {
  return dayjs(dateString).format('YYYY-MM-DD HH:mm:ss')
}

const getModelLabel = (modelName) => {
  const models = {
    'yolov8n': 'YOLOv8n',
    'yolov8s': 'YOLOv8s',
    'yolov8m': 'YOLOv8m',
    'yolov8l': 'YOLOv8l',
    'yolov8x': 'YOLOv8x'
  }
  return models[modelName] || modelName
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

const getStatusText = (status) => {
  const texts = {
    pending: '等待中',
    processing: '处理中',
    completed: '已完成',
    failed: '失败'
  }
  return texts[status] || '未知'
}

const getDetectionCount = () => {
  return taskData.value?.result?.detections?.length || 0
}

const getUniqueClasses = () => {
  if (!taskData.value?.result?.detections) return []
  const classes = taskData.value.result.detections.map(d => d.class_name)
  return [...new Set(classes)]
}

const getAverageConfidence = () => {
  if (!taskData.value?.result?.detections) return 0
  const detections = taskData.value.result.detections
  const sum = detections.reduce((acc, d) => acc + d.confidence, 0)
  return (sum / detections.length) * 100
}

const getMaxConfidence = () => {
  if (!taskData.value?.result?.detections) return 0
  const detections = taskData.value.result.detections
  const max = Math.max(...detections.map(d => d.confidence))
  return max * 100
}

const getClassDistribution = () => {
  if (!taskData.value?.result?.detections) return {}
  
  const distribution = {}
  taskData.value.result.detections.forEach(detection => {
    const className = detection.class_name
    distribution[className] = (distribution[className] || 0) + 1
  })
  
  // 按数量排序
  return Object.fromEntries(
    Object.entries(distribution).sort(([,a], [,b]) => b - a)
  )
}

const downloadResult = async (format) => {
  if (!taskData.value?.id) return
  
  try {
    await detectionStore.downloadResult(taskData.value.id, format)
  } catch (error) {
    console.error('下载失败:', error)
  }
}

const redetect = () => {
  if (!taskData.value) return
  
  router.push({
    path: '/detect',
    query: {
      file_id: taskData.value.file_id,
      model_name: taskData.value.model_name,
      confidence: taskData.value.confidence,
      classes: JSON.stringify(taskData.value.classes)
    }
  })
}

// 图片缩放控制
const zoomIn = () => {
  zoomLevel.value = Math.min(zoomLevel.value * 1.2, 5)
}

const zoomOut = () => {
  zoomLevel.value = Math.max(zoomLevel.value / 1.2, 0.1)
}

const resetZoom = () => {
  zoomLevel.value = 1
}

const onImageLoad = () => {
  console.log('图片加载成功')
}

const onImageError = () => {
  message.error('图片加载失败')
}

const onVideoLoad = () => {
  console.log('视频加载成功')
}

const onVideoError = () => {
  message.error('视频加载失败')
}

onMounted(() => {
  loadTaskData()
})
</script>

<style scoped>
.result {
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
  display: flex;
  align-items: flex-start;
  gap: 16px;
  flex: 1;
}

.back-btn {
  margin-top: 4px;
}

.title-section {
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

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 100px 0;
  color: #666;
}

.loading-container p {
  margin-top: 16px;
}

.result-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.media-card,
.info-card,
.stats-card,
.distribution-card,
.details-card {
  margin-bottom: 24px;
}

.media-tabs {
  margin-bottom: 16px;
  text-align: center;
}

.media-container {
  position: relative;
  text-align: center;
}

.image-container {
  position: relative;
  display: inline-block;
}

.result-image {
  max-width: 100%;
  max-height: 600px;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transform: scale(var(--zoom-level, 1));
  transition: transform 0.3s ease;
}

.image-toolbar {
  position: absolute;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.7);
  border-radius: 6px;
  padding: 8px 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.image-toolbar .ant-btn {
  background: transparent;
  border-color: rgba(255, 255, 255, 0.3);
  color: white;
}

.image-toolbar .ant-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.5);
}

.zoom-level {
  color: white;
  font-size: 12px;
  min-width: 40px;
  text-align: center;
}

.result-video {
  width: 100%;
  max-height: 600px;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.class-distribution {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.class-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.class-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.class-name {
  font-weight: 500;
}

.class-count {
  color: #666;
  font-size: 12px;
}

.table-actions {
  margin-bottom: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .header-content {
    flex-direction: column;
    gap: 12px;
  }
  
  .back-btn {
    align-self: flex-start;
  }
  
  .header-actions {
    align-self: flex-end;
  }
  
  .table-actions {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .image-toolbar {
    position: static;
    transform: none;
    margin-top: 16px;
    background: #f5f5f5;
    justify-content: center;
  }
  
  .image-toolbar .ant-btn {
    background: white;
    border-color: #d9d9d9;
    color: #333;
  }
  
  .zoom-level {
    color: #333;
  }
}
</style>