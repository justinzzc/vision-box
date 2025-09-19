<template>
  <div class="service-create-page">
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
          <div class="header-info">
            <h1 class="page-title">创建API服务</h1>
            <p class="page-description">配置检测参数并发布为API服务，生成访问令牌供第三方调用</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建表单 -->
    <div class="form-container">
      <a-card :bordered="false" class="form-card">
        <a-form
          ref="formRef"
          :model="formData"
          :rules="formRules"
          layout="vertical"
          @finish="handleSubmit"
        >
          <!-- 基本信息 -->
          <div class="form-section">
            <h3 class="section-title">基本信息</h3>
            <a-row :gutter="24">
              <a-col :span="12">
                <a-form-item label="服务名称" name="service_name">
                  <a-input
                    v-model:value="formData.service_name"
                    placeholder="请输入服务名称"
                    size="large"
                  />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="检测模型" name="model_name">
                  <a-select
                    v-model:value="formData.model_name"
                    placeholder="选择检测模型"
                    size="large"
                    @change="handleModelChange"
                  >
                    <a-select-option
                      v-for="model in availableModels"
                      :key="model.name"
                      :value="model.name"
                    >
                      <div class="model-option">
                        <div class="model-name">{{ model.display_name }}</div>
                        <div class="model-desc">{{ model.description }}</div>
                      </div>
                    </a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
            </a-row>
            
            <a-form-item label="服务描述" name="description">
              <a-textarea
                v-model:value="formData.description"
                placeholder="请输入服务描述（可选）"
                :rows="3"
                show-count
                :maxlength="500"
              />
            </a-form-item>
          </div>

          <!-- 检测配置 -->
          <div class="form-section">
            <h3 class="section-title">检测配置</h3>
            <a-row :gutter="24">
              <a-col :span="8">
                <a-form-item label="置信度阈值" name="confidence_threshold">
                  <a-slider
                    v-model:value="formData.confidence_threshold"
                    :min="0.1"
                    :max="1.0"
                    :step="0.05"
                    :tooltip-formatter="(value) => `${(value * 100).toFixed(0)}%`"
                  />
                  <div class="slider-value">
                    当前值: {{ (formData.confidence_threshold * 100).toFixed(0) }}%
                  </div>
                </a-form-item>
              </a-col>
              <a-col :span="16">
                <a-form-item label="检测类别" name="detection_classes">
                  <a-select
                    v-model:value="formData.detection_classes"
                    mode="multiple"
                    placeholder="选择要检测的类别（留空表示检测所有类别）"
                    size="large"
                    :options="classOptions"
                    allow-clear
                  />
                </a-form-item>
              </a-col>
            </a-row>
          </div>

          <!-- API配置 -->
          <div class="form-section">
            <h3 class="section-title">API配置</h3>
            <a-row :gutter="24">
              <a-col :span="8">
                <a-form-item label="调用频率限制" name="rate_limit">
                  <a-input-number
                    v-model:value="formData.rate_limit"
                    :min="1"
                    :max="10000"
                    size="large"
                    style="width: 100%"
                    addon-after="次/分钟"
                  />
                </a-form-item>
              </a-col>
              <a-col :span="8">
                <a-form-item label="最大文件大小" name="max_file_size">
                  <a-select
                    v-model:value="formData.max_file_size"
                    size="large"
                  >
                    <a-select-option :value="1048576">1 MB</a-select-option>
                    <a-select-option :value="5242880">5 MB</a-select-option>
                    <a-select-option :value="10485760">10 MB</a-select-option>
                    <a-select-option :value="20971520">20 MB</a-select-option>
                    <a-select-option :value="52428800">50 MB</a-select-option>
                    <a-select-option :value="104857600">100 MB</a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
              <a-col :span="8">
                <a-form-item label="允许的文件格式" name="allowed_formats">
                  <a-select
                    v-model:value="formData.allowed_formats"
                    mode="multiple"
                    size="large"
                    placeholder="选择允许的文件格式"
                  >
                    <a-select-option value="jpg">JPG</a-select-option>
                    <a-select-option value="jpeg">JPEG</a-select-option>
                    <a-select-option value="png">PNG</a-select-option>
                    <a-select-option value="bmp">BMP</a-select-option>
                    <a-select-option value="webp">WebP</a-select-option>
                    <a-select-option value="mp4">MP4</a-select-option>
                    <a-select-option value="avi">AVI</a-select-option>
                    <a-select-option value="mov">MOV</a-select-option>
                    <a-select-option value="mkv">MKV</a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
            </a-row>
          </div>

          <!-- 预览配置 -->
          <div class="form-section">
            <h3 class="section-title">配置预览</h3>
            <a-card size="small" class="preview-card">
              <div class="config-preview">
                <div class="preview-item">
                  <span class="preview-label">API端点:</span>
                  <code class="preview-value">/api/services/{service_id}/detect</code>
                </div>
                <div class="preview-item">
                  <span class="preview-label">请求方法:</span>
                  <code class="preview-value">POST</code>
                </div>
                <div class="preview-item">
                  <span class="preview-label">认证方式:</span>
                  <code class="preview-value">Bearer Token</code>
                </div>
                <div class="preview-item">
                  <span class="preview-label">内容类型:</span>
                  <code class="preview-value">multipart/form-data</code>
                </div>
              </div>
            </a-card>
          </div>

          <!-- 提交按钮 -->
          <div class="form-actions">
            <a-space size="large">
              <a-button size="large" @click="$router.back()">
                取消
              </a-button>
              <a-button
                type="primary"
                size="large"
                html-type="submit"
                :loading="submitting"
              >
                创建服务
              </a-button>
            </a-space>
          </div>
        </a-form>
      </a-card>
    </div>

    <!-- 创建成功弹窗 -->
    <a-modal
      v-model:open="showSuccessModal"
      title="服务创建成功"
      :footer="null"
      :closable="false"
      :mask-closable="false"
      width="600px"
    >
      <div class="success-content">
        <div class="success-icon">
          <CheckCircleOutlined style="color: #52c41a; font-size: 48px;" />
        </div>
        <div class="success-info">
          <h3>服务已成功创建！</h3>
          <p>您的API服务已经创建完成，以下是重要信息：</p>
          
          <div class="service-info">
            <div class="info-item">
              <span class="info-label">服务ID:</span>
              <code class="info-value">{{ createdService.service_id }}</code>
              <a-button type="link" size="small" @click="copyToClipboard(createdService.service_id)">
                复制
              </a-button>
            </div>
            <div class="info-item">
              <span class="info-label">API端点:</span>
              <code class="info-value">{{ createdService.api_endpoint }}</code>
              <a-button type="link" size="small" @click="copyToClipboard(createdService.api_endpoint)">
                复制
              </a-button>
            </div>
            <div class="info-item">
              <span class="info-label">访问令牌:</span>
              <code class="info-value token-value">{{ createdService.access_token }}</code>
              <a-button type="link" size="small" @click="copyToClipboard(createdService.access_token)">
                复制
              </a-button>
            </div>
          </div>
          
          <a-alert
            message="重要提示"
            description="请妥善保存访问令牌，出于安全考虑，令牌只会显示一次。如果丢失，您需要重新生成新的令牌。"
            type="warning"
            show-icon
            style="margin: 16px 0;"
          />
        </div>
      </div>
      
      <div class="success-actions">
        <a-space>
          <a-button @click="goToServiceList">
            返回服务列表
          </a-button>
          <a-button type="primary" @click="goToServiceDetail">
            查看服务详情
          </a-button>
        </a-space>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  ArrowLeftOutlined,
  CheckCircleOutlined
} from '@ant-design/icons-vue'
import { apiClient } from '@/utils/api'

const router = useRouter()
const formRef = ref()
const submitting = ref(false)
const showSuccessModal = ref(false)
const createdService = ref({})

// 表单数据
const formData = reactive({
  service_name: '',
  description: '',
  model_name: 'yolov8s',
  confidence_threshold: 0.5,
  detection_classes: [],
  rate_limit: 100,
  max_file_size: 10485760, // 10MB
  allowed_formats: ['jpg', 'jpeg', 'png', 'mp4', 'avi']
})

// 表单验证规则
const formRules = {
  service_name: [
    { required: true, message: '请输入服务名称', trigger: 'blur' },
    { min: 2, max: 50, message: '服务名称长度应在2-50个字符之间', trigger: 'blur' }
  ],
  model_name: [
    { required: true, message: '请选择检测模型', trigger: 'change' }
  ],
  confidence_threshold: [
    { required: true, message: '请设置置信度阈值', trigger: 'change' }
  ],
  rate_limit: [
    { required: true, message: '请设置调用频率限制', trigger: 'change' }
  ],
  max_file_size: [
    { required: true, message: '请设置最大文件大小', trigger: 'change' }
  ],
  allowed_formats: [
    { required: true, message: '请选择允许的文件格式', trigger: 'change' }
  ]
}

// 可用模型列表
const availableModels = ref([
  {
    name: 'yolov8n',
    display_name: 'YOLOv8 Nano',
    description: '轻量级模型，速度快，适合实时检测'
  },
  {
    name: 'yolov8s',
    display_name: 'YOLOv8 Small',
    description: '小型模型，平衡速度和精度'
  },
  {
    name: 'yolov8m',
    display_name: 'YOLOv8 Medium',
    description: '中型模型，精度较高'
  },
  {
    name: 'yolov8l',
    display_name: 'YOLOv8 Large',
    description: '大型模型，高精度但速度较慢'
  },
  {
    name: 'yolov8x',
    display_name: 'YOLOv8 Extra Large',
    description: '超大型模型，最高精度'
  }
])

// COCO类别选项
const classOptions = ref([
  { label: '人', value: 'person' },
  { label: '自行车', value: 'bicycle' },
  { label: '汽车', value: 'car' },
  { label: '摩托车', value: 'motorcycle' },
  { label: '飞机', value: 'airplane' },
  { label: '公交车', value: 'bus' },
  { label: '火车', value: 'train' },
  { label: '卡车', value: 'truck' },
  { label: '船', value: 'boat' },
  { label: '交通灯', value: 'traffic light' },
  { label: '消防栓', value: 'fire hydrant' },
  { label: '停车标志', value: 'stop sign' },
  { label: '停车计时器', value: 'parking meter' },
  { label: '长椅', value: 'bench' },
  { label: '鸟', value: 'bird' },
  { label: '猫', value: 'cat' },
  { label: '狗', value: 'dog' },
  { label: '马', value: 'horse' },
  { label: '羊', value: 'sheep' },
  { label: '牛', value: 'cow' }
])

// 方法
const handleModelChange = (modelName) => {
  const model = availableModels.value.find(m => m.name === modelName)
  if (model) {
    // 根据模型调整默认置信度
    if (modelName.includes('n')) {
      formData.confidence_threshold = 0.6 // nano模型建议更高置信度
    } else if (modelName.includes('x')) {
      formData.confidence_threshold = 0.4 // 大模型可以用更低置信度
    } else {
      formData.confidence_threshold = 0.5
    }
  }
}

const handleSubmit = async () => {
  try {
    submitting.value = true
    
    const response = await apiClient.createService(formData)
    createdService.value = response
    showSuccessModal.value = true
    
    message.success('服务创建成功！')
  } catch (error) {
    console.error('创建服务失败:', error)
    message.error('创建服务失败，请重试')
  } finally {
    submitting.value = false
  }
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

const goToServiceList = () => {
  router.push('/services')
}

const goToServiceDetail = () => {
  router.push(`/services/${createdService.value.service_id}`)
}

// 生命周期
onMounted(() => {
  // 可以在这里加载更多配置数据
})
</script>

<style scoped>
.service-create-page {
  padding: 24px;
  background-color: #f5f5f5;
  min-height: 100vh;
}

.page-header {
  margin-bottom: 24px;
}

.header-content {
  display: flex;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-button {
  padding: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
  color: #1f2937;
}

.page-description {
  color: #6b7280;
  margin: 4px 0 0 0;
  font-size: 14px;
}

.form-container {
  max-width: 1000px;
  margin: 0 auto;
}

.form-card {
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}

.form-section {
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 1px solid #f0f0f0;
}

.form-section:last-of-type {
  border-bottom: none;
  margin-bottom: 0;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 16px 0;
}

.model-option {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.model-name {
  font-weight: 500;
}

.model-desc {
  font-size: 12px;
  color: #6b7280;
}

.slider-value {
  text-align: center;
  font-size: 12px;
  color: #6b7280;
  margin-top: 8px;
}

.preview-card {
  background-color: #fafafa;
}

.config-preview {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.preview-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.preview-label {
  font-weight: 500;
  color: #374151;
  min-width: 80px;
}

.preview-value {
  background-color: #f3f4f6;
  padding: 2px 8px;
  border-radius: 4px;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 12px;
}

.form-actions {
  display: flex;
  justify-content: center;
  padding-top: 24px;
  border-top: 1px solid #f0f0f0;
}

.success-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 24px 0;
}

.success-icon {
  margin-bottom: 16px;
}

.success-info h3 {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: #1f2937;
}

.success-info p {
  color: #6b7280;
  margin: 0 0 24px 0;
}

.service-info {
  background-color: #f9fafb;
  border-radius: 8px;
  padding: 16px;
  margin: 16px 0;
  text-align: left;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.info-item:last-child {
  margin-bottom: 0;
}

.info-label {
  font-weight: 500;
  color: #374151;
  min-width: 80px;
}

.info-value {
  background-color: #f3f4f6;
  padding: 4px 8px;
  border-radius: 4px;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 12px;
  flex: 1;
  word-break: break-all;
}

.token-value {
  background-color: #fef3c7;
  border: 1px solid #f59e0b;
}

.success-actions {
  display: flex;
  justify-content: center;
  padding-top: 24px;
  border-top: 1px solid #f0f0f0;
}

:deep(.ant-form-item-label > label) {
  font-weight: 500;
}

:deep(.ant-slider-track) {
  background-color: #1890ff;
}

:deep(.ant-slider-handle) {
  border-color: #1890ff;
}
</style>