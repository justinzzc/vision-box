<template>
  <div class="home">
    <!-- 欢迎横幅 -->
    <div class="hero-section">
      <div class="hero-content">
        <h1 class="hero-title">
          <camera-outlined class="hero-icon" />
          智能视觉检测平台
        </h1>
        <p class="hero-description">
          基于 Supervision 库的专业视觉检测解决方案，支持图片和视频中目标对象的自动识别与标注
        </p>
        <div class="hero-actions">
          <a-button type="primary" size="large" @click="goToDetect">
            <play-circle-outlined />
            开始检测
          </a-button>
          <a-button size="large" @click="viewHistory">
            <history-outlined />
            查看历史
          </a-button>
        </div>
      </div>
      <div class="hero-image">
        <img src="/vite.svg" alt="Vision Detection" class="hero-img" />
      </div>
    </div>

    <!-- 功能特性 -->
    <div class="features-section">
      <h2 class="section-title">核心功能</h2>
      <a-row :gutter="[24, 24]">
        <a-col :xs="24" :sm="12" :lg="6" v-for="feature in features" :key="feature.title">
          <a-card class="feature-card" hoverable>
            <template #cover>
              <div class="feature-icon">
                <component :is="feature.icon" />
              </div>
            </template>
            <a-card-meta :title="feature.title" :description="feature.description" />
          </a-card>
        </a-col>
      </a-row>
    </div>

    <!-- 统计信息 -->
    <div class="stats-section">
      <h2 class="section-title">使用统计</h2>
      <a-row :gutter="[24, 24]">
        <a-col :xs="24" :sm="12" :lg="6" v-for="stat in stats" :key="stat.title">
          <a-card class="stat-card">
            <a-statistic
              :title="stat.title"
              :value="stat.value"
              :suffix="stat.suffix"
              :prefix="stat.prefix"
              :value-style="{ color: stat.color }"
            />
          </a-card>
        </a-col>
      </a-row>
    </div>

    <!-- 快速开始 -->
    <div class="quick-start-section">
      <h2 class="section-title">快速开始</h2>
      <a-card class="quick-start-card">
        <a-steps :current="0" class="steps">
          <a-step title="上传文件" description="选择图片或视频文件" />
          <a-step title="配置参数" description="设置检测置信度和类别" />
          <a-step title="执行检测" description="启动AI视觉检测任务" />
          <a-step title="查看结果" description="获取标注结果和数据" />
        </a-steps>
        
        <div class="quick-start-actions">
          <a-button type="primary" size="large" @click="goToDetect">
            立即体验
          </a-button>
        </div>
      </a-card>
    </div>

    <!-- 支持的格式 -->
    <div class="formats-section">
      <h2 class="section-title">支持格式</h2>
      <a-row :gutter="[24, 24]">
        <a-col :xs="24" :md="12">
          <a-card title="图片格式" class="format-card">
            <div class="format-list">
              <a-tag v-for="format in imageFormats" :key="format" color="blue">
                {{ format }}
              </a-tag>
            </div>
          </a-card>
        </a-col>
        <a-col :xs="24" :md="12">
          <a-card title="视频格式" class="format-card">
            <div class="format-list">
              <a-tag v-for="format in videoFormats" :key="format" color="green">
                {{ format }}
              </a-tag>
            </div>
          </a-card>
        </a-col>
      </a-row>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useDetectionStore } from '@/stores/detection'
import {
  CameraOutlined,
  PlayCircleOutlined,
  HistoryOutlined,
  FileImageOutlined,
  VideoCameraOutlined,
  SettingOutlined,
  DownloadOutlined,
  ThunderboltOutlined,
  SafetyOutlined,
  CloudOutlined,
  MobileOutlined
} from '@ant-design/icons-vue'

const router = useRouter()
const detectionStore = useDetectionStore()

// 功能特性
const features = ref([
  {
    title: '智能检测',
    description: '基于YOLOv8的高精度目标检测，支持80+种物体识别',
    icon: ThunderboltOutlined
  },
  {
    title: '多格式支持',
    description: '支持主流图片和视频格式，满足不同场景需求',
    icon: FileImageOutlined
  },
  {
    title: '可视化标注',
    description: '直观的检测结果展示，支持检测框和标签显示',
    icon: VideoCameraOutlined
  },
  {
    title: '数据导出',
    description: '支持JSON格式结果导出，便于后续数据分析',
    icon: DownloadOutlined
  },
  {
    title: '参数配置',
    description: '灵活的检测参数设置，可调节置信度和检测类别',
    icon: SettingOutlined
  },
  {
    title: '历史管理',
    description: '完整的检测历史记录，支持搜索和批量操作',
    icon: HistoryOutlined
  },
  {
    title: '安全可靠',
    description: '本地化部署，数据安全有保障，支持离线使用',
    icon: SafetyOutlined
  },
  {
    title: '响应式设计',
    description: '适配多种设备，支持桌面端、平板和手机访问',
    icon: MobileOutlined
  }
])

// 统计信息
const stats = ref([
  {
    title: '检测任务',
    value: 0,
    suffix: '个',
    color: '#1890ff'
  },
  {
    title: '成功率',
    value: 0,
    suffix: '%',
    color: '#52c41a'
  },
  {
    title: '处理文件',
    value: 0,
    suffix: '个',
    color: '#722ed1'
  },
  {
    title: '检测对象',
    value: 0,
    suffix: '个',
    color: '#fa8c16'
  }
])

// 支持的格式
const imageFormats = ref(['JPG', 'JPEG', 'PNG', 'BMP', 'GIF'])
const videoFormats = ref(['MP4', 'AVI', 'MOV', 'MKV', 'WMV'])

// 方法
const goToDetect = () => {
  router.push('/detect')
}

const viewHistory = () => {
  router.push('/history')
}

const loadStats = async () => {
  try {
    await detectionStore.loadHistory()
    const history = detectionStore.detectionHistory
    
    stats.value[0].value = history.length
    stats.value[1].value = history.length > 0 
      ? Math.round((detectionStore.completedTasks.length / history.length) * 100)
      : 0
    stats.value[2].value = history.length
    
    // 计算检测到的对象总数
    let totalObjects = 0
    detectionStore.completedTasks.forEach(task => {
      if (task.result && task.result.detections) {
        totalObjects += task.result.detections.length
      }
    })
    stats.value[3].value = totalObjects
  } catch (error) {
    console.error('加载统计信息失败:', error)
  }
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.home {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 16px;
}

/* 欢迎横幅 */
.hero-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 60px 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  margin-bottom: 60px;
  color: white;
  overflow: hidden;
  position: relative;
}

.hero-content {
  flex: 1;
  padding: 0 40px;
  z-index: 2;
}

.hero-title {
  font-size: 3rem;
  font-weight: bold;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.hero-icon {
  font-size: 3rem;
}

.hero-description {
  font-size: 1.2rem;
  margin-bottom: 32px;
  opacity: 0.9;
  line-height: 1.6;
}

.hero-actions {
  display: flex;
  gap: 16px;
}

.hero-image {
  flex: 0 0 300px;
  text-align: center;
  padding: 0 40px;
}

.hero-img {
  width: 200px;
  height: 200px;
  opacity: 0.8;
}

/* 功能特性 */
.features-section {
  margin-bottom: 60px;
}

.section-title {
  text-align: center;
  font-size: 2rem;
  margin-bottom: 40px;
  color: #333;
}

.feature-card {
  height: 100%;
  transition: transform 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-4px);
}

.feature-icon {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 80px;
  font-size: 2rem;
  color: #1890ff;
  background: linear-gradient(135deg, #e6f7ff 0%, #f0f9ff 100%);
}

/* 统计信息 */
.stats-section {
  margin-bottom: 60px;
}

.stat-card {
  text-align: center;
  height: 100%;
}

/* 快速开始 */
.quick-start-section {
  margin-bottom: 60px;
}

.quick-start-card {
  padding: 20px;
}

.steps {
  margin-bottom: 40px;
}

.quick-start-actions {
  text-align: center;
}

/* 支持格式 */
.formats-section {
  margin-bottom: 40px;
}

.format-card {
  height: 100%;
}

.format-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .hero-section {
    flex-direction: column;
    text-align: center;
    padding: 40px 20px;
  }
  
  .hero-title {
    font-size: 2rem;
    flex-direction: column;
    gap: 8px;
  }
  
  .hero-icon {
    font-size: 2rem;
  }
  
  .hero-description {
    font-size: 1rem;
  }
  
  .hero-actions {
    flex-direction: column;
    align-items: center;
  }
  
  .hero-image {
    flex: none;
    margin-top: 20px;
  }
  
  .hero-img {
    width: 120px;
    height: 120px;
  }
  
  .section-title {
    font-size: 1.5rem;
  }
}
</style>