<template>
  <div class="detect">
    <a-row :gutter="[24, 24]">
      <!-- 左侧：文件上传和参数配置 -->
      <a-col :xs="24" :lg="12">
        <!-- 文件上传区域 -->
        <a-card title="文件上传" class="upload-card">
          <a-upload-dragger
            v-model:file-list="fileList"
            :before-upload="beforeUpload"
            :custom-request="handleUpload"
            :show-upload-list="false"
            accept="image/*,video/*"
            class="upload-dragger"
          >
            <div class="upload-content">
              <p class="ant-upload-drag-icon">
                <inbox-outlined v-if="!uploadedFile" />
                <loading-outlined v-else-if="uploading" />
                <check-circle-outlined v-else style="color: #52c41a" />
              </p>
              <p class="ant-upload-text">
                {{ uploadText }}
              </p>
              <p class="ant-upload-hint">
                支持图片格式：JPG, PNG, BMP, GIF<br>
                支持视频格式：MP4, AVI, MOV, MKV<br>
                文件大小限制：100MB
              </p>
            </div>
          </a-upload-dragger>
          
          <!-- 文件预览 -->
          <div v-if="uploadedFile" class="file-preview">
            <a-card size="small">
              <div class="file-info">
                <div class="file-icon">
                  <file-image-outlined v-if="uploadedFile.type === 'image'" />
                  <video-camera-outlined v-else />
                </div>
                <div class="file-details">
                  <div class="file-name">{{ uploadedFile.name }}</div>
                  <div class="file-meta">
                    {{ formatFileSize(uploadedFile.size) }} • {{ uploadedFile.type }}
                  </div>
                </div>
                <a-button 
                  type="text" 
                  danger 
                  @click="removeFile"
                  :icon="h(DeleteOutlined)"
                />
              </div>
            </a-card>
          </div>
        </a-card>
        
        <!-- 检测参数配置 -->
        <a-card title="检测参数" class="params-card">
          <a-form :model="detectionParams" layout="vertical">
            <!-- 模型选择 -->
            <a-form-item label="检测模型">
              <a-select 
                v-model:value="detectionParams.model_name" 
                placeholder="选择检测模型"
              >
                <a-select-option 
                  v-for="model in availableModels" 
                  :key="model.name" 
                  :value="model.name"
                >
                  {{ model.label }}
                  <span class="model-size">({{ model.size }})</span>
                </a-select-option>
              </a-select>
            </a-form-item>
            
            <!-- 置信度阈值 -->
            <a-form-item label="置信度阈值">
              <a-slider 
                v-model:value="detectionParams.confidence" 
                :min="0.1" 
                :max="1" 
                :step="0.05"
                :marks="confidenceMarks"
              />
              <div class="param-value">
                当前值: {{ detectionParams.confidence }}
              </div>
            </a-form-item>
            
            <!-- 检测类别 -->
            <a-form-item label="检测类别">
              <a-checkbox-group v-model:value="detectionParams.classes" class="class-group">
                <a-row>
                  <a-col :span="12" v-for="cls in detectionClasses" :key="cls.id">
                    <a-checkbox :value="cls.id">{{ cls.label }}</a-checkbox>
                  </a-col>
                </a-row>
              </a-checkbox-group>
              <div class="class-actions">
                <a-button size="small" @click="selectAllClasses">全选</a-button>
                <a-button size="small" @click="clearAllClasses">清空</a-button>
                <a-button size="small" @click="selectCommonClasses">常用</a-button>
              </div>
            </a-form-item>
          </a-form>
          
          <!-- 开始检测按钮 -->
          <div class="detect-actions">
            <a-button 
              type="primary" 
              size="large" 
              :loading="detecting" 
              :disabled="!uploadedFile"
              @click="startDetection"
              block
            >
              <play-circle-outlined v-if="!detecting" />
              开始检测
            </a-button>
          </div>
        </a-card>
      </a-col>
      
      <!-- 右侧：检测结果展示 -->
      <a-col :xs="24" :lg="12">
        <a-card title="检测结果" class="result-card">
          <!-- 检测状态 -->
          <div v-if="currentTask" class="detection-status">
            <a-alert
              :type="getStatusType(currentTask.status)"
              :message="getStatusMessage(currentTask.status)"
              :description="getStatusDescription(currentTask.status)"
              show-icon
              class="status-alert"
            />
            
            <!-- 进度条 -->
            <a-progress 
              v-if="currentTask.status === 'processing'"
              :percent="progressPercent"
              :status="progressStatus"
              class="progress-bar"
            />
          </div>
          
          <!-- 结果展示 -->
          <div v-if="currentTask && currentTask.status === 'completed'" class="result-display">
            <!-- 标注图片/视频 -->
            <div class="annotated-media">
              <img 
                v-if="uploadedFile && uploadedFile.type === 'image'"
                :src="currentTask.annotatedUrl"
                alt="检测结果"
                class="result-image"
              />
              <video 
                v-else-if="uploadedFile && uploadedFile.type === 'video'"
                :src="currentTask.annotatedUrl"
                controls
                class="result-video"
              />
            </div>
            
            <!-- 检测统计 -->
            <div class="detection-stats">
              <a-row :gutter="16">
                <a-col :span="8">
                  <a-statistic 
                    title="检测对象" 
                    :value="getDetectionCount()" 
                    suffix="个"
                  />
                </a-col>
                <a-col :span="8">
                  <a-statistic 
                    title="检测类别" 
                    :value="getUniqueClasses().length" 
                    suffix="种"
                  />
                </a-col>
                <a-col :span="8">
                  <a-statistic 
                    title="平均置信度" 
                    :value="getAverageConfidence()" 
                    :precision="2"
                  />
                </a-col>
              </a-row>
            </div>
            
            <!-- 检测详情 -->
            <div class="detection-details">
              <a-collapse>
                <a-collapse-panel key="details" header="检测详情">
                  <a-table 
                    :columns="detectionColumns"
                    :data-source="getDetectionList()"
                    :pagination="false"
                    size="small"
                  />
                </a-collapse-panel>
              </a-collapse>
            </div>
            
            <!-- 操作按钮 -->
            <div class="result-actions">
              <a-space>
                <a-button @click="downloadResult('json')">
                  <download-outlined />
                  下载JSON
                </a-button>
                <a-button @click="downloadResult('csv')">
                  <file-excel-outlined />
                  下载CSV
                </a-button>
                <a-button @click="viewFullResult">
                  <eye-outlined />
                  查看详情
                </a-button>
              </a-space>
            </div>
          </div>
          
          <!-- 空状态 -->
          <a-empty 
            v-else-if="!currentTask"
            description="请上传文件并开始检测"
            class="empty-result"
          />
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup>
import { ref, computed, h, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useDetectionStore } from '@/stores/detection'
import { formatFileSize, checkFileType } from '@/utils/api'
import { message } from 'ant-design-vue'
import {
  InboxOutlined,
  LoadingOutlined,
  CheckCircleOutlined,
  FileImageOutlined,
  VideoCameraOutlined,
  DeleteOutlined,
  PlayCircleOutlined,
  DownloadOutlined,
  FileExcelOutlined,
  EyeOutlined
} from '@ant-design/icons-vue'

const router = useRouter()
const detectionStore = useDetectionStore()

// 响应式数据
const fileList = ref([])
const uploadedFile = ref(null)
const uploading = ref(false)
const detecting = ref(false)
const progressPercent = ref(0)

// 检测参数
const detectionParams = ref({
  model_name: 'yolov8s',
  confidence: 0.5,
  classes: [0, 1, 2, 3, 5, 6, 7] // 默认选择常用类别
})

// 置信度标记
const confidenceMarks = {
  0.1: '0.1',
  0.3: '0.3',
  0.5: '0.5',
  0.7: '0.7',
  0.9: '0.9'
}

// 检测结果表格列
const detectionColumns = [
  {
    title: '类别',
    dataIndex: 'class_name',
    key: 'class_name'
  },
  {
    title: '置信度',
    dataIndex: 'confidence',
    key: 'confidence',
    render: (value) => (value * 100).toFixed(1) + '%'
  },
  {
    title: '位置',
    dataIndex: 'bbox',
    key: 'bbox',
    render: (bbox) => `(${bbox[0]}, ${bbox[1]}, ${bbox[2]}, ${bbox[3]})`
  }
]

// 计算属性
const availableModels = computed(() => detectionStore.availableModels)
const detectionClasses = computed(() => detectionStore.detectionClasses)
const currentTask = computed(() => detectionStore.currentTask)

const uploadText = computed(() => {
  if (uploading.value) return '上传中...'
  if (uploadedFile.value) return '文件上传成功'
  return '点击或拖拽文件到此区域上传'
})

const progressStatus = computed(() => {
  if (currentTask.value?.status === 'failed') return 'exception'
  if (currentTask.value?.status === 'completed') return 'success'
  return 'active'
})

// 方法
const beforeUpload = (file) => {
  console.log('beforeUpload 函数被调用:', file)
  console.log('文件信息:', {
    name: file.name,
    type: file.type,
    size: file.size
  })
  
  // 检查文件类型
  const isValidType = checkFileType(file, ['image', 'video'])
  console.log('文件类型检查结果:', isValidType)
  
  if (!isValidType) {
    console.log('文件类型不支持')
    message.error('不支持的文件格式')
    return false
  }
  
  // 检查文件大小 (100MB)
  const isValidSize = file.size / 1024 / 1024 < 100
  console.log('文件大小检查结果:', isValidSize, '文件大小(MB):', file.size / 1024 / 1024)
  
  if (!isValidSize) {
    console.log('文件大小超限')
    message.error('文件大小不能超过100MB')
    return false
  }
  
  console.log('beforeUpload 验证通过，允许上传')
  return true // 允许上传，触发 custom-request
}

const handleUpload = async ({ file }) => {
  console.log('handleUpload 函数被调用:', file)
  
  try {
    uploading.value = true
    
    const fileType = file.type.startsWith('image/') ? 'image' : 'video'
    console.log('开始上传文件，类型:', fileType)
    
    const response = await detectionStore.uploadFile(file, fileType)
    console.log('文件上传成功:', response)
    
    uploadedFile.value = {
      id: response.file_id,
      name: file.name,
      size: file.size,
      type: fileType,
      url: response.file_url
    }
    
    message.success('文件上传成功')
    
  } catch (error) {
    console.error('上传失败:', error)
    message.error('文件上传失败: ' + error.message)
  } finally {
    uploading.value = false
  }
}

const removeFile = () => {
  uploadedFile.value = null
  fileList.value = []
  detectionStore.clearCurrentTask()
}

const selectAllClasses = () => {
  detectionParams.value.classes = detectionClasses.value.map(cls => cls.id)
}

const clearAllClasses = () => {
  detectionParams.value.classes = []
}

const selectCommonClasses = () => {
  detectionParams.value.classes = [0, 1, 2, 3, 5, 6, 7, 17, 18] // 人、车辆、动物等常用类别
}

const startDetection = async () => {
  if (!uploadedFile.value) {
    message.error('请先上传文件')
    return
  }
  
  try {
    detecting.value = true
    progressPercent.value = 0
    
    const params = {
      file_record_id: uploadedFile.value.id,
      task_name: `检测任务_${new Date().toLocaleString()}`,
      detection_type: 'object_detection',
      confidence_threshold: detectionParams.value.confidence,
      model_name: detectionParams.value.model_name,
      classes: detectionParams.value.classes
    }
    
    await detectionStore.startDetection(params)
    
    // 模拟进度更新
    const progressInterval = setInterval(() => {
      if (progressPercent.value < 90) {
        progressPercent.value += Math.random() * 10
      }
      
      if (currentTask.value?.status === 'completed' || currentTask.value?.status === 'failed') {
        progressPercent.value = 100
        clearInterval(progressInterval)
        detecting.value = false
      }
    }, 1000)
    
  } catch (error) {
    console.error('检测失败:', error)
    detecting.value = false
  }
}

const getStatusType = (status) => {
  const types = {
    pending: 'info',
    processing: 'warning',
    completed: 'success',
    failed: 'error'
  }
  return types[status] || 'info'
}

const getStatusMessage = (status) => {
  const messages = {
    pending: '检测任务已提交',
    processing: '正在检测中...',
    completed: '检测完成',
    failed: '检测失败'
  }
  return messages[status] || '未知状态'
}

const getStatusDescription = (status) => {
  const descriptions = {
    pending: '任务已加入队列，请稍候',
    processing: '正在使用AI模型进行目标检测',
    completed: '检测任务已成功完成',
    failed: '检测过程中出现错误，请重试'
  }
  return descriptions[status] || ''
}

const getDetectionCount = () => {
  return currentTask.value?.result?.detections?.length || 0
}

const getUniqueClasses = () => {
  if (!currentTask.value?.result?.detections) return []
  const classes = currentTask.value.result.detections.map(d => d.class_name)
  return [...new Set(classes)]
}

const getAverageConfidence = () => {
  if (!currentTask.value?.result?.detections) return 0
  const detections = currentTask.value.result.detections
  const sum = detections.reduce((acc, d) => acc + d.confidence, 0)
  return sum / detections.length
}

const getDetectionList = () => {
  if (!currentTask.value?.result?.detections) return []
  return currentTask.value.result.detections.map((detection, index) => ({
    key: index,
    ...detection
  }))
}

const downloadResult = async (format) => {
  if (!currentTask.value?.id) return
  
  try {
    await detectionStore.downloadResult(currentTask.value.id, format)
  } catch (error) {
    console.error('下载失败:', error)
  }
}

const viewFullResult = () => {
  if (currentTask.value?.id) {
    router.push(`/result/${currentTask.value.id}`)
  }
}

onMounted(() => {
  // 清除之前的任务状态
  detectionStore.clearCurrentTask()
})
</script>

<style scoped>
.detect {
  max-width: 1400px;
  margin: 0 auto;
}

.upload-card,
.params-card,
.result-card {
  margin-bottom: 24px;
  height: fit-content;
}

.upload-dragger {
  margin-bottom: 16px;
}

.upload-content {
  padding: 20px;
}

.file-preview {
  margin-top: 16px;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.file-icon {
  font-size: 24px;
  color: #1890ff;
}

.file-details {
  flex: 1;
}

.file-name {
  font-weight: 500;
  margin-bottom: 4px;
}

.file-meta {
  color: #666;
  font-size: 12px;
}

.param-value {
  text-align: center;
  margin-top: 8px;
  color: #666;
  font-size: 12px;
}

.class-group {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  padding: 12px;
}

.class-actions {
  margin-top: 12px;
  display: flex;
  gap: 8px;
}

.detect-actions {
  margin-top: 24px;
}

.model-size {
  color: #666;
  font-size: 12px;
}

.detection-status {
  margin-bottom: 24px;
}

.status-alert {
  margin-bottom: 16px;
}

.progress-bar {
  margin-bottom: 16px;
}

.result-display {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.annotated-media {
  text-align: center;
}

.result-image,
.result-video {
  max-width: 100%;
  max-height: 400px;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.detection-stats {
  background: #fafafa;
  padding: 16px;
  border-radius: 6px;
}

.detection-details {
  margin-top: 16px;
}

.result-actions {
  text-align: center;
}

.empty-result {
  padding: 60px 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .class-group {
    max-height: 150px;
  }
  
  .class-actions {
    flex-wrap: wrap;
  }
  
  .result-actions {
    text-align: left;
  }
  
  .result-actions .ant-space {
    width: 100%;
  }
  
  .result-actions .ant-btn {
    flex: 1;
  }
}
</style>