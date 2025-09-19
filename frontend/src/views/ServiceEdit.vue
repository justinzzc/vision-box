<template>
  <div class="service-edit-page">
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
            <h1 class="page-title">编辑服务</h1>
            <p class="page-description">修改服务配置和检测参数</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <a-spin size="large" />
    </div>

    <!-- 编辑表单 -->
    <div v-else class="form-container">
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
                保存修改
              </a-button>
            </a-space>
          </div>
        </a-form>
      </a-card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  ArrowLeftOutlined
} from '@ant-design/icons-vue'
import { apiClient } from '@/utils/api'

const route = useRoute()
const router = useRouter()
const serviceId = route.params.id

const formRef = ref()
const loading = ref(true)
const submitting = ref(false)

// 表单数据
const formData = reactive({
  service_name: '',
  description: '',
  model_name: '',
  confidence_threshold: 0.5,
  detection_classes: [],
  rate_limit: 100,
  max_file_size: 10485760,
  allowed_formats: []
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
const loadServiceInfo = async () => {
  try {
    const response = await apiClient.getService(serviceId)
    
    // 填充表单数据
    formData.service_name = response.service_name
    formData.description = response.description || ''
    formData.model_name = response.model_name
    formData.confidence_threshold = response.confidence_threshold
    formData.detection_classes = response.detection_classes || []
    formData.rate_limit = response.rate_limit
    formData.max_file_size = response.max_file_size
    formData.allowed_formats = response.allowed_formats || []
    
    loading.value = false
  } catch (error) {
    console.error('加载服务信息失败:', error)
    message.error('加载服务信息失败')
    router.back()
  }
}

const handleModelChange = (modelName) => {
  const model = availableModels.value.find(m => m.name === modelName)
  if (model) {
    // 根据模型调整默认置信度
    if (modelName.includes('n')) {
      formData.confidence_threshold = 0.6
    } else if (modelName.includes('x')) {
      formData.confidence_threshold = 0.4
    } else {
      formData.confidence_threshold = 0.5
    }
  }
}

const handleSubmit = async () => {
  try {
    submitting.value = true
    
    await apiClient.updateService(serviceId, formData)
    message.success('服务更新成功')
    router.push(`/services/${serviceId}`)
  } catch (error) {
    console.error('更新服务失败:', error)
    message.error('更新服务失败')
  } finally {
    submitting.value = false
  }
}

// 生命周期
onMounted(() => {
  loadServiceInfo()
})
</script>

<style scoped>
.service-edit-page {
  min-height: 100vh;
  background: #f5f5f5;
}

.page-header {
  background: white;
  border-bottom: 1px solid #e8e8e8;
  padding: 16px 24px;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-button {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #666;
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #262626;
}

.page-description {
  margin: 4px 0 0 0;
  color: #8c8c8c;
  font-size: 14px;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.form-container {
  max-width: 1200px;
  margin: 24px auto;
  padding: 0 24px;
}

.form-card {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.form-section {
  margin-bottom: 32px;
}

.section-title {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #262626;
  border-bottom: 1px solid #f0f0f0;
  padding-bottom: 8px;
}

.model-option {
  padding: 4px 0;
}

.model-name {
  font-weight: 500;
  color: #262626;
}

.model-desc {
  font-size: 12px;
  color: #8c8c8c;
  margin-top: 2px;
}

.slider-value {
  text-align: center;
  margin-top: 8px;
  font-size: 12px;
  color: #666;
}

.form-actions {
  text-align: center;
  padding-top: 24px;
  border-top: 1px solid #f0f0f0;
}
</style>