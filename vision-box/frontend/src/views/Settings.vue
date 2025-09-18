<template>
  <div class="settings">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1 class="page-title">
        <setting-outlined />
        系统设置
      </h1>
      <p class="page-description">配置检测参数和系统选项</p>
    </div>

    <a-row :gutter="[24, 24]">
      <!-- 左侧：设置菜单 -->
      <a-col :xs="24" :lg="6">
        <a-card class="menu-card">
          <a-menu
            v-model:selectedKeys="selectedKeys"
            mode="inline"
            @click="handleMenuClick"
          >
            <a-menu-item key="detection">
              <camera-outlined />
              检测设置
            </a-menu-item>
            <a-menu-item key="models">
              <robot-outlined />
              模型管理
            </a-menu-item>
            <a-menu-item key="storage">
              <database-outlined />
              存储设置
            </a-menu-item>
            <a-menu-item key="system">
              <desktop-outlined />
              系统信息
            </a-menu-item>
            <a-menu-item key="about">
              <info-circle-outlined />
              关于
            </a-menu-item>
          </a-menu>
        </a-card>
      </a-col>

      <!-- 右侧：设置内容 -->
      <a-col :xs="24" :lg="18">
        <!-- 检测设置 -->
        <a-card v-if="activeTab === 'detection'" title="检测设置" class="content-card">
          <a-form :model="detectionSettings" layout="vertical">
            <a-row :gutter="[16, 16]">
              <a-col :xs="24" :md="12">
                <a-form-item label="默认模型">
                  <a-select v-model:value="detectionSettings.defaultModel">
                    <a-select-option 
                      v-for="model in availableModels" 
                      :key="model.name" 
                      :value="model.name"
                    >
                      {{ model.label }}
                    </a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
              <a-col :xs="24" :md="12">
                <a-form-item label="默认置信度">
                  <a-slider 
                    v-model:value="detectionSettings.defaultConfidence" 
                    :min="0.1" 
                    :max="1" 
                    :step="0.05"
                    :marks="confidenceMarks"
                  />
                  <div class="param-value">
                    当前值: {{ detectionSettings.defaultConfidence }}
                  </div>
                </a-form-item>
              </a-col>
            </a-row>
            
            <a-form-item label="默认检测类别">
              <a-checkbox-group v-model:value="detectionSettings.defaultClasses">
                <a-row>
                  <a-col :span="8" v-for="cls in detectionClasses" :key="cls.id">
                    <a-checkbox :value="cls.id">{{ cls.label }}</a-checkbox>
                  </a-col>
                </a-row>
              </a-checkbox-group>
            </a-form-item>
            
            <a-form-item label="文件上传限制">
              <a-row :gutter="16">
                <a-col :span="12">
                  <a-input-number
                    v-model:value="detectionSettings.maxFileSize"
                    :min="1"
                    :max="1000"
                    addon-after="MB"
                    placeholder="最大文件大小"
                  />
                </a-col>
                <a-col :span="12">
                  <a-switch
                    v-model:checked="detectionSettings.autoCleanup"
                    checked-children="自动清理"
                    un-checked-children="手动清理"
                  />
                </a-col>
              </a-row>
            </a-form-item>
            
            <a-form-item>
              <a-space>
                <a-button type="primary" @click="saveDetectionSettings">
                  保存设置
                </a-button>
                <a-button @click="resetDetectionSettings">
                  重置默认
                </a-button>
              </a-space>
            </a-form-item>
          </a-form>
        </a-card>

        <!-- 模型管理 -->
        <a-card v-if="activeTab === 'models'" title="模型管理" class="content-card">
          <div class="models-section">
            <a-table 
              :columns="modelColumns" 
              :data-source="availableModels" 
              :pagination="false"
              row-key="name"
            >
              <template #status="{ record }">
                <a-tag :color="record.installed ? 'green' : 'orange'">
                  {{ record.installed ? '已安装' : '未安装' }}
                </a-tag>
              </template>
              
              <template #actions="{ record }">
                <a-space>
                  <a-button 
                    v-if="!record.installed"
                    type="primary" 
                    size="small"
                    @click="downloadModel(record)"
                    :loading="record.downloading"
                  >
                    下载
                  </a-button>
                  <a-button 
                    v-else
                    size="small"
                    @click="testModel(record)"
                  >
                    测试
                  </a-button>
                  <a-popconfirm
                    v-if="record.installed"
                    title="确定要删除这个模型吗？"
                    @confirm="deleteModel(record)"
                  >
                    <a-button size="small" danger>
                      删除
                    </a-button>
                  </a-popconfirm>
                </a-space>
              </template>
            </a-table>
          </div>
          
          <a-divider />
          
          <div class="custom-model-section">
            <h3>自定义模型</h3>
            <a-upload
              :before-upload="beforeUploadModel"
              :custom-request="uploadCustomModel"
              accept=".pt,.onnx"
            >
              <a-button>
                <upload-outlined />
                上传自定义模型
              </a-button>
            </a-upload>
            <p class="upload-hint">
              支持 PyTorch (.pt) 和 ONNX (.onnx) 格式的模型文件
            </p>
          </div>
        </a-card>

        <!-- 存储设置 -->
        <a-card v-if="activeTab === 'storage'" title="存储设置" class="content-card">
          <a-form :model="storageSettings" layout="vertical">
            <a-form-item label="数据存储路径">
              <a-input 
                v-model:value="storageSettings.dataPath" 
                readonly
                addon-after="浏览"
              />
            </a-form-item>
            
            <a-form-item label="存储统计">
              <a-row :gutter="16">
                <a-col :span="8">
                  <a-statistic title="已用空间" :value="storageStats.used" suffix="MB" />
                </a-col>
                <a-col :span="8">
                  <a-statistic title="可用空间" :value="storageStats.available" suffix="GB" />
                </a-col>
                <a-col :span="8">
                  <a-statistic title="文件数量" :value="storageStats.fileCount" suffix="个" />
                </a-col>
              </a-row>
            </a-form-item>
            
            <a-form-item label="清理选项">
              <a-space direction="vertical">
                <a-checkbox v-model:checked="storageSettings.autoCleanOldFiles">
                  自动清理30天前的文件
                </a-checkbox>
                <a-checkbox v-model:checked="storageSettings.compressResults">
                  压缩检测结果文件
                </a-checkbox>
                <a-checkbox v-model:checked="storageSettings.backupEnabled">
                  启用数据备份
                </a-checkbox>
              </a-space>
            </a-form-item>
            
            <a-form-item>
              <a-space>
                <a-button type="primary" @click="saveStorageSettings">
                  保存设置
                </a-button>
                <a-button @click="cleanupStorage" :loading="cleaning">
                  立即清理
                </a-button>
                <a-button @click="exportData">
                  导出数据
                </a-button>
              </a-space>
            </a-form-item>
          </a-form>
        </a-card>

        <!-- 系统信息 -->
        <a-card v-if="activeTab === 'system'" title="系统信息" class="content-card">
          <a-descriptions :column="2" bordered>
            <a-descriptions-item label="应用版本">
              {{ systemInfo.version }}
            </a-descriptions-item>
            <a-descriptions-item label="构建时间">
              {{ systemInfo.buildTime }}
            </a-descriptions-item>
            <a-descriptions-item label="Python版本">
              {{ systemInfo.pythonVersion }}
            </a-descriptions-item>
            <a-descriptions-item label="Node.js版本">
              {{ systemInfo.nodeVersion }}
            </a-descriptions-item>
            <a-descriptions-item label="操作系统">
              {{ systemInfo.os }}
            </a-descriptions-item>
            <a-descriptions-item label="CPU">
              {{ systemInfo.cpu }}
            </a-descriptions-item>
            <a-descriptions-item label="内存">
              {{ systemInfo.memory }}
            </a-descriptions-item>
            <a-descriptions-item label="GPU">
              {{ systemInfo.gpu || '未检测到' }}
            </a-descriptions-item>
          </a-descriptions>
          
          <a-divider />
          
          <div class="system-actions">
            <a-space>
              <a-button @click="checkUpdates" :loading="checkingUpdates">
                <sync-outlined />
                检查更新
              </a-button>
              <a-button @click="downloadLogs">
                <download-outlined />
                下载日志
              </a-button>
              <a-button @click="restartService" danger>
                <reload-outlined />
                重启服务
              </a-button>
            </a-space>
          </div>
        </a-card>

        <!-- 关于 -->
        <a-card v-if="activeTab === 'about'" title="关于" class="content-card">
          <div class="about-content">
            <div class="app-info">
              <img src="/vite.svg" alt="Logo" class="app-logo" />
              <h2>视觉检测应用</h2>
              <p class="app-version">版本 {{ systemInfo.version }}</p>
              <p class="app-description">
                基于 Supervision 库的专业视觉检测解决方案，支持图片和视频中目标对象的自动识别与标注。
              </p>
            </div>
            
            <a-divider />
            
            <div class="tech-stack">
              <h3>技术栈</h3>
              <a-row :gutter="[16, 16]">
                <a-col :span="12">
                  <h4>前端</h4>
                  <ul>
                    <li>Vue.js 3</li>
                    <li>Ant Design Vue</li>
                    <li>Vite</li>
                    <li>Pinia</li>
                  </ul>
                </a-col>
                <a-col :span="12">
                  <h4>后端</h4>
                  <ul>
                    <li>FastAPI</li>
                    <li>Supervision</li>
                    <li>OpenCV</li>
                    <li>Ultralytics</li>
                  </ul>
                </a-col>
              </a-row>
            </div>
            
            <a-divider />
            
            <div class="links">
              <a-space>
                <a-button type="link" href="https://github.com" target="_blank">
                  <github-outlined />
                  GitHub
                </a-button>
                <a-button type="link" href="#" target="_blank">
                  <book-outlined />
                  文档
                </a-button>
                <a-button type="link" href="#" target="_blank">
                  <bug-outlined />
                  反馈问题
                </a-button>
              </a-space>
            </div>
          </div>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useDetectionStore } from '@/stores/detection'
import { message } from 'ant-design-vue'
import {
  SettingOutlined,
  CameraOutlined,
  RobotOutlined,
  DatabaseOutlined,
  DesktopOutlined,
  InfoCircleOutlined,
  UploadOutlined,
  SyncOutlined,
  DownloadOutlined,
  ReloadOutlined,
  GithubOutlined,
  BookOutlined,
  BugOutlined
} from '@ant-design/icons-vue'

const detectionStore = useDetectionStore()

// 响应式数据
const selectedKeys = ref(['detection'])
const activeTab = ref('detection')
const cleaning = ref(false)
const checkingUpdates = ref(false)

// 检测设置
const detectionSettings = reactive({
  defaultModel: 'yolov8s',
  defaultConfidence: 0.5,
  defaultClasses: [0, 1, 2, 3, 5, 6, 7],
  maxFileSize: 100,
  autoCleanup: true
})

// 存储设置
const storageSettings = reactive({
  dataPath: './data',
  autoCleanOldFiles: true,
  compressResults: false,
  backupEnabled: false
})

// 存储统计
const storageStats = reactive({
  used: 256,
  available: 15.8,
  fileCount: 42
})

// 系统信息
const systemInfo = reactive({
  version: '1.0.0',
  buildTime: '2024-01-15 10:30:00',
  pythonVersion: '3.10.0',
  nodeVersion: '18.17.0',
  os: 'Windows 11',
  cpu: 'Intel Core i7-12700K',
  memory: '32GB DDR4',
  gpu: 'NVIDIA RTX 4080'
})

// 置信度标记
const confidenceMarks = {
  0.1: '0.1',
  0.3: '0.3',
  0.5: '0.5',
  0.7: '0.7',
  0.9: '0.9'
}

// 模型表格列
const modelColumns = [
  {
    title: '模型名称',
    dataIndex: 'label',
    key: 'label'
  },
  {
    title: '大小',
    dataIndex: 'size',
    key: 'size'
  },
  {
    title: '状态',
    key: 'status',
    slots: { customRender: 'status' }
  },
  {
    title: '操作',
    key: 'actions',
    slots: { customRender: 'actions' }
  }
]

// 计算属性
const availableModels = ref([
  { name: 'yolov8n', label: 'YOLOv8n', size: '6MB', installed: true, downloading: false },
  { name: 'yolov8s', label: 'YOLOv8s', size: '22MB', installed: true, downloading: false },
  { name: 'yolov8m', label: 'YOLOv8m', size: '52MB', installed: false, downloading: false },
  { name: 'yolov8l', label: 'YOLOv8l', size: '87MB', installed: false, downloading: false },
  { name: 'yolov8x', label: 'YOLOv8x', size: '136MB', installed: false, downloading: false }
])

const detectionClasses = detectionStore.detectionClasses

// 方法
const handleMenuClick = ({ key }) => {
  activeTab.value = key
}

const saveDetectionSettings = () => {
  // 保存检测设置到本地存储
  localStorage.setItem('detectionSettings', JSON.stringify(detectionSettings))
  message.success('检测设置已保存')
}

const resetDetectionSettings = () => {
  detectionSettings.defaultModel = 'yolov8s'
  detectionSettings.defaultConfidence = 0.5
  detectionSettings.defaultClasses = [0, 1, 2, 3, 5, 6, 7]
  detectionSettings.maxFileSize = 100
  detectionSettings.autoCleanup = true
  message.success('已重置为默认设置')
}

const downloadModel = async (model) => {
  model.downloading = true
  try {
    // 模拟下载过程
    await new Promise(resolve => setTimeout(resolve, 3000))
    model.installed = true
    message.success(`${model.label} 下载完成`)
  } catch (error) {
    message.error(`${model.label} 下载失败`)
  } finally {
    model.downloading = false
  }
}

const testModel = async (model) => {
  try {
    message.loading(`正在测试 ${model.label}...`, 2)
    // 模拟测试过程
    await new Promise(resolve => setTimeout(resolve, 2000))
    message.success(`${model.label} 测试通过`)
  } catch (error) {
    message.error(`${model.label} 测试失败`)
  }
}

const deleteModel = async (model) => {
  try {
    model.installed = false
    message.success(`${model.label} 已删除`)
  } catch (error) {
    message.error(`删除 ${model.label} 失败`)
  }
}

const beforeUploadModel = (file) => {
  const isValidType = file.name.endsWith('.pt') || file.name.endsWith('.onnx')
  if (!isValidType) {
    message.error('只支持 .pt 和 .onnx 格式的模型文件')
    return false
  }
  
  const isValidSize = file.size / 1024 / 1024 < 500 // 500MB
  if (!isValidSize) {
    message.error('模型文件大小不能超过500MB')
    return false
  }
  
  return false
}

const uploadCustomModel = async ({ file }) => {
  try {
    message.loading('正在上传模型...', 0)
    // 模拟上传过程
    await new Promise(resolve => setTimeout(resolve, 3000))
    message.destroy()
    message.success('自定义模型上传成功')
  } catch (error) {
    message.destroy()
    message.error('模型上传失败')
  }
}

const saveStorageSettings = () => {
  localStorage.setItem('storageSettings', JSON.stringify(storageSettings))
  message.success('存储设置已保存')
}

const cleanupStorage = async () => {
  cleaning.value = true
  try {
    // 模拟清理过程
    await new Promise(resolve => setTimeout(resolve, 2000))
    storageStats.used = Math.max(0, storageStats.used - 50)
    storageStats.fileCount = Math.max(0, storageStats.fileCount - 10)
    message.success('存储清理完成')
  } catch (error) {
    message.error('存储清理失败')
  } finally {
    cleaning.value = false
  }
}

const exportData = () => {
  // 模拟数据导出
  const data = {
    settings: { detectionSettings, storageSettings },
    timestamp: new Date().toISOString()
  }
  
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'vision-app-settings.json'
  link.click()
  URL.revokeObjectURL(url)
  
  message.success('设置数据已导出')
}

const checkUpdates = async () => {
  checkingUpdates.value = true
  try {
    // 模拟检查更新
    await new Promise(resolve => setTimeout(resolve, 2000))
    message.info('当前已是最新版本')
  } catch (error) {
    message.error('检查更新失败')
  } finally {
    checkingUpdates.value = false
  }
}

const downloadLogs = () => {
  // 模拟日志下载
  const logs = `[${new Date().toISOString()}] Application started\n[${new Date().toISOString()}] Detection completed\n`
  const blob = new Blob([logs], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'vision-app-logs.txt'
  link.click()
  URL.revokeObjectURL(url)
  
  message.success('日志文件已下载')
}

const restartService = () => {
  message.warning('重启功能需要管理员权限')
}

// 加载设置
const loadSettings = () => {
  const savedDetectionSettings = localStorage.getItem('detectionSettings')
  if (savedDetectionSettings) {
    Object.assign(detectionSettings, JSON.parse(savedDetectionSettings))
  }
  
  const savedStorageSettings = localStorage.getItem('storageSettings')
  if (savedStorageSettings) {
    Object.assign(storageSettings, JSON.parse(savedStorageSettings))
  }
}

onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.settings {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
  padding: 24px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
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

.menu-card {
  height: fit-content;
  position: sticky;
  top: 24px;
}

.content-card {
  min-height: 500px;
}

.param-value {
  text-align: center;
  margin-top: 8px;
  color: #666;
  font-size: 12px;
}

.models-section {
  margin-bottom: 24px;
}

.custom-model-section h3 {
  margin-bottom: 16px;
}

.upload-hint {
  margin-top: 8px;
  color: #666;
  font-size: 12px;
}

.system-actions {
  margin-top: 24px;
}

.about-content {
  text-align: center;
}

.app-info {
  padding: 24px 0;
}

.app-logo {
  width: 64px;
  height: 64px;
  margin-bottom: 16px;
}

.app-info h2 {
  margin-bottom: 8px;
  color: #333;
}

.app-version {
  color: #666;
  margin-bottom: 16px;
}

.app-description {
  color: #666;
  line-height: 1.6;
  max-width: 600px;
  margin: 0 auto;
}

.tech-stack {
  text-align: left;
  margin: 24px 0;
}

.tech-stack h3 {
  margin-bottom: 16px;
  text-align: center;
}

.tech-stack h4 {
  margin-bottom: 12px;
  color: #333;
}

.tech-stack ul {
  list-style: none;
  padding: 0;
}

.tech-stack li {
  padding: 4px 0;
  color: #666;
}

.links {
  margin-top: 24px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .menu-card {
    position: static;
    margin-bottom: 24px;
  }
  
  .tech-stack {
    text-align: center;
  }
  
  .tech-stack .ant-col {
    margin-bottom: 24px;
  }
}
</style>