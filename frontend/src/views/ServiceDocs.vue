<template>
  <div class="service-docs-page">
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
            <h1 class="page-title">API文档</h1>
            <p class="page-description">{{ serviceInfo.service_name }} - 调用文档和示例</p>
          </div>
        </div>
        <div class="header-right">
          <a-button @click="copyApiUrl">
            <template #icon>
              <CopyOutlined />
            </template>
            复制API地址
          </a-button>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <a-spin size="large" />
    </div>

    <!-- 文档内容 -->
    <div v-else-if="serviceInfo" class="docs-content">
      <!-- 快速开始 -->
      <a-card title="快速开始" class="docs-section" :bordered="false">
        <div class="quick-start">
          <p>使用以下信息调用您的API服务：</p>
          <div class="api-info">
            <div class="info-item">
              <span class="info-label">API端点:</span>
              <code class="info-value">{{ fullApiUrl }}</code>
              <a-button type="link" size="small" @click="copyToClipboard(fullApiUrl)">
                复制
              </a-button>
            </div>
            <div class="info-item">
              <span class="info-label">请求方法:</span>
              <code class="info-value">POST</code>
            </div>
            <div class="info-item">
              <span class="info-label">内容类型:</span>
              <code class="info-value">multipart/form-data</code>
            </div>
            <div class="info-item">
              <span class="info-label">认证方式:</span>
              <code class="info-value">Bearer Token</code>
            </div>
          </div>
        </div>
      </a-card>

      <!-- 认证 -->
      <a-card title="认证" class="docs-section" :bordered="false">
        <div class="auth-section">
          <p>所有API请求都需要在请求头中包含有效的访问令牌：</p>
          <div class="code-block">
            <pre><code>Authorization: Bearer YOUR_ACCESS_TOKEN</code></pre>
            <a-button type="link" size="small" class="copy-button" @click="copyToClipboard('Authorization: Bearer YOUR_ACCESS_TOKEN')">
              <CopyOutlined />
            </a-button>
          </div>
          <a-alert
            message="获取访问令牌"
            description="您可以在服务详情页面的Token管理中创建和管理访问令牌。"
            type="info"
            show-icon
            style="margin-top: 16px;"
          />
        </div>
      </a-card>

      <!-- API参考 -->
      <a-card title="API参考" class="docs-section" :bordered="false">
        <div class="api-reference">
          <h3>POST {{ serviceInfo.api_endpoint }}</h3>
          <p>执行图像或视频检测</p>
          
          <!-- 请求参数 -->
          <h4>请求参数</h4>
          <a-table
            :columns="paramColumns"
            :data-source="requestParams"
            :pagination="false"
            size="small"
            class="params-table"
          />
          
          <!-- 响应格式 -->
          <h4>响应格式</h4>
          <div class="code-block">
            <pre><code>{{ responseExample }}</code></pre>
            <a-button type="link" size="small" class="copy-button" @click="copyToClipboard(responseExample)">
              <CopyOutlined />
            </a-button>
          </div>
        </div>
      </a-card>

      <!-- 代码示例 -->
      <a-card title="代码示例" class="docs-section" :bordered="false">
        <a-tabs v-model:activeKey="activeTab" class="code-tabs">
          <!-- cURL示例 -->
          <a-tab-pane key="curl" tab="cURL">
            <div class="code-block">
              <pre><code>{{ curlExample }}</code></pre>
              <a-button type="link" size="small" class="copy-button" @click="copyToClipboard(curlExample)">
                <CopyOutlined />
              </a-button>
            </div>
          </a-tab-pane>
          
          <!-- Python示例 -->
          <a-tab-pane key="python" tab="Python">
            <div class="code-block">
              <pre><code>{{ pythonExample }}</code></pre>
              <a-button type="link" size="small" class="copy-button" @click="copyToClipboard(pythonExample)">
                <CopyOutlined />
              </a-button>
            </div>
          </a-tab-pane>
          
          <!-- JavaScript示例 -->
          <a-tab-pane key="javascript" tab="JavaScript">
            <div class="code-block">
              <pre><code>{{ javascriptExample }}</code></pre>
              <a-button type="link" size="small" class="copy-button" @click="copyToClipboard(javascriptExample)">
                <CopyOutlined />
              </a-button>
            </div>
          </a-tab-pane>
          
          <!-- PHP示例 -->
          <a-tab-pane key="php" tab="PHP">
            <div class="code-block">
              <pre><code>{{ phpExample }}</code></pre>
              <a-button type="link" size="small" class="copy-button" @click="copyToClipboard(phpExample)">
                <CopyOutlined />
              </a-button>
            </div>
          </a-tab-pane>
        </a-tabs>
      </a-card>

      <!-- 错误代码 -->
      <a-card title="错误代码" class="docs-section" :bordered="false">
        <div class="error-codes">
          <p>API可能返回以下错误代码：</p>
          <a-table
            :columns="errorColumns"
            :data-source="errorCodes"
            :pagination="false"
            size="small"
            class="error-table"
          />
        </div>
      </a-card>

      <!-- 限制和配额 -->
      <a-card title="限制和配额" class="docs-section" :bordered="false">
        <div class="limits-section">
          <div class="limit-item">
            <span class="limit-label">调用频率限制:</span>
            <span class="limit-value">{{ serviceInfo.rate_limit }} 次/分钟</span>
          </div>
          <div class="limit-item">
            <span class="limit-label">最大文件大小:</span>
            <span class="limit-value">{{ formatFileSize(serviceInfo.max_file_size) }}</span>
          </div>
          <div class="limit-item">
            <span class="limit-label">支持的文件格式:</span>
            <span class="limit-value">
              <a-tag v-for="format in serviceInfo.allowed_formats" :key="format" size="small">
                {{ format.toUpperCase() }}
              </a-tag>
            </span>
          </div>
          <div class="limit-item" v-if="serviceInfo.detection_classes.length > 0">
            <span class="limit-label">检测类别:</span>
            <span class="limit-value">
              <a-tag v-for="cls in serviceInfo.detection_classes" :key="cls" size="small">
                {{ cls }}
              </a-tag>
            </span>
          </div>
          <div class="limit-item">
            <span class="limit-label">置信度阈值:</span>
            <span class="limit-value">{{ (serviceInfo.confidence_threshold * 100).toFixed(0) }}%</span>
          </div>
        </div>
      </a-card>

      <!-- 在线测试 -->
      <a-card title="在线测试" class="docs-section" :bordered="false">
        <div class="test-section">
          <p>您可以直接在这里测试API调用：</p>
          <a-form layout="vertical" class="test-form">
            <a-form-item label="访问令牌">
              <a-input-password
                v-model:value="testToken"
                placeholder="请输入访问令牌"
                size="large"
              />
            </a-form-item>
            <a-form-item label="上传文件">
              <a-upload
                v-model:file-list="testFileList"
                :before-upload="() => false"
                :max-count="1"
                accept="image/*,video/*"
              >
                <a-button>
                  <template #icon>
                    <UploadOutlined />
                  </template>
                  选择文件
                </a-button>
              </a-upload>
            </a-form-item>
            <a-form-item>
              <a-button
                type="primary"
                size="large"
                @click="testApi"
                :loading="testing"
                :disabled="!testToken || testFileList.length === 0"
              >
                测试API
              </a-button>
            </a-form-item>
          </a-form>
          
          <!-- 测试结果 -->
          <div v-if="testResult" class="test-result">
            <h4>测试结果:</h4>
            <div class="code-block">
              <pre><code>{{ JSON.stringify(testResult, null, 2) }}</code></pre>
            </div>
          </div>
        </div>
      </a-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  ArrowLeftOutlined,
  CopyOutlined,
  UploadOutlined
} from '@ant-design/icons-vue'
import { apiClient, formatFileSize } from '@/utils/api'

const route = useRoute()
const serviceId = route.params.id

// 响应式数据
const loading = ref(true)
const serviceInfo = ref(null)
const activeTab = ref('curl')
const testToken = ref('')
const testFileList = ref([])
const testing = ref(false)
const testResult = ref(null)

// 计算属性
const fullApiUrl = computed(() => {
  if (!serviceInfo.value) return ''
  return `${window.location.origin}${serviceInfo.value.api_endpoint}`
})

// 请求参数表格数据
const paramColumns = [
  { title: '参数名', dataIndex: 'name', key: 'name' },
  { title: '类型', dataIndex: 'type', key: 'type' },
  { title: '必需', dataIndex: 'required', key: 'required' },
  { title: '描述', dataIndex: 'description', key: 'description' }
]

const requestParams = [
  {
    name: 'file',
    type: 'File',
    required: '是',
    description: '待检测的图片或视频文件'
  },
  {
    name: 'callback_url',
    type: 'String',
    required: '否',
    description: '异步回调地址（可选）'
  }
]

// 错误代码表格数据
const errorColumns = [
  { title: '状态码', dataIndex: 'code', key: 'code' },
  { title: '错误类型', dataIndex: 'type', key: 'type' },
  { title: '描述', dataIndex: 'description', key: 'description' }
]

const errorCodes = [
  { code: '400', type: 'Bad Request', description: '请求参数错误或文件格式不支持' },
  { code: '401', type: 'Unauthorized', description: '访问令牌无效或已过期' },
  { code: '403', type: 'Forbidden', description: '服务已禁用或IP不在白名单中' },
  { code: '413', type: 'Payload Too Large', description: '文件大小超过限制' },
  { code: '429', type: 'Too Many Requests', description: '请求频率超过限制' },
  { code: '500', type: 'Internal Server Error', description: '服务器内部错误' }
]

// 响应示例
const responseExample = computed(() => {
  return JSON.stringify({
    success: true,
    task_id: null,
    result: {
      detections: [
        {
          class_name: "person",
          confidence: 0.85,
          bbox: [100, 50, 200, 300]
        },
        {
          class_name: "car",
          confidence: 0.92,
          bbox: [300, 150, 500, 400]
        }
      ],
      class_counts: {
        person: 1,
        car: 1
      },
      total_detections: 2,
      confidence_threshold: serviceInfo.value?.confidence_threshold || 0.5,
      model_used: serviceInfo.value?.model_name || "yolov8s",
      processing_time: 1.23,
      annotated_url: "/uploads/results/annotated_image.jpg"
    },
    processing_time: 1.23,
    message: "检测完成",
    request_id: "req_123456789"
  }, null, 2)
})

// 代码示例
const curlExample = computed(() => {
  return `curl -X POST "${fullApiUrl.value}" \\
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \\
  -F "file=@/path/to/your/image.jpg"`
})

const pythonExample = computed(() => {
  return `import requests

url = "${fullApiUrl.value}"
headers = {
    "Authorization": "Bearer YOUR_ACCESS_TOKEN"
}

with open("/path/to/your/image.jpg", "rb") as f:
    files = {"file": f}
    response = requests.post(url, headers=headers, files=files)
    
if response.status_code == 200:
    result = response.json()
    print(f"检测到 {result['result']['total_detections']} 个对象")
    for detection in result['result']['detections']:
        print(f"- {detection['class_name']}: {detection['confidence']:.2f}")
else:
    print(f"请求失败: {response.status_code}")`
})

const javascriptExample = computed(() => {
  return `const formData = new FormData();
const fileInput = document.getElementById('fileInput');
formData.append('file', fileInput.files[0]);

fetch('${fullApiUrl.value}', {
    method: 'POST',
    headers: {
        'Authorization': 'Bearer YOUR_ACCESS_TOKEN'
    },
    body: formData
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        console.log(\`检测到 \${data.result.total_detections} 个对象\`);
        data.result.detections.forEach(detection => {
            console.log(\`- \${detection.class_name}: \${detection.confidence.toFixed(2)}\`);
        });
    } else {
        console.error('检测失败:', data.message);
    }
})
.catch(error => {
    console.error('请求错误:', error);
});`
})

const phpExample = computed(() => {
  return `<?php
$url = '${fullApiUrl.value}';
$token = 'YOUR_ACCESS_TOKEN';
$filePath = '/path/to/your/image.jpg';

$curl = curl_init();

curl_setopt_array($curl, [
    CURLOPT_URL => $url,
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_POST => true,
    CURLOPT_HTTPHEADER => [
        'Authorization: Bearer ' . $token
    ],
    CURLOPT_POSTFIELDS => [
        'file' => new CURLFile($filePath)
    ]
]);

$response = curl_exec($curl);
$httpCode = curl_getinfo($curl, CURLINFO_HTTP_CODE);
curl_close($curl);

if ($httpCode === 200) {
    $result = json_decode($response, true);
    echo "检测到 {$result['result']['total_detections']} 个对象\\n";
    foreach ($result['result']['detections'] as $detection) {
        echo "- {$detection['class_name']}: " . number_format($detection['confidence'], 2) . "\\n";
    }
} else {
    echo "请求失败: HTTP $httpCode\\n";
}
?>`
})

// 方法
const loadServiceInfo = async () => {
  try {
    const response = await apiClient.getService(serviceId)
    serviceInfo.value = response
  } catch (error) {
    console.error('加载服务信息失败:', error)
    message.error('加载服务信息失败')
  } finally {
    loading.value = false
  }
}

const copyApiUrl = () => {
  copyToClipboard(fullApiUrl.value)
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

const testApi = async () => {
  if (!testToken.value || testFileList.value.length === 0) {
    message.error('请输入访问令牌并选择文件')
    return
  }

  try {
    testing.value = true
    testResult.value = null

    const formData = new FormData()
    formData.append('file', testFileList.value[0].originFileObj)

    const response = await fetch(fullApiUrl.value, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${testToken.value}`
      },
      body: formData
    })

    const result = await response.json()
    testResult.value = result

    if (response.ok) {
      message.success('API测试成功')
    } else {
      message.error(`API测试失败: ${result.message || '未知错误'}`)
    }
  } catch (error) {
    console.error('API测试失败:', error)
    message.error('API测试失败，请检查网络连接')
    testResult.value = {
      error: error.message,
      success: false
    }
  } finally {
    testing.value = false
  }
}

// 生命周期
onMounted(() => {
  loadServiceInfo()
})
</script>

<style scoped>
.service-docs-page {
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
  margin: 0 0 4px 0;
  color: #1f2937;
}

.page-description {
  color: #6b7280;
  margin: 0;
  font-size: 14px;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 400px;
}

.docs-content {
  max-width: 1000px;
  margin: 0 auto;
}

.docs-section {
  margin-bottom: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.api-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 16px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.info-label {
  font-weight: 500;
  color: #374151;
  min-width: 100px;
}

.info-value {
  background-color: #f3f4f6;
  padding: 4px 8px;
  border-radius: 4px;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 13px;
  flex: 1;
}

.code-block {
  position: relative;
  background-color: #1f2937;
  border-radius: 6px;
  padding: 16px;
  margin: 16px 0;
  overflow-x: auto;
}

.code-block pre {
  margin: 0;
  color: #f9fafb;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 13px;
  line-height: 1.5;
}

.copy-button {
  position: absolute;
  top: 8px;
  right: 8px;
  color: #9ca3af;
}

.copy-button:hover {
  color: #f9fafb;
}

.api-reference h3 {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 8px 0;
}

.api-reference h4 {
  font-size: 16px;
  font-weight: 600;
  color: #374151;
  margin: 24px 0 12px 0;
}

.params-table,
.error-table {
  margin: 16px 0;
}

.code-tabs {
  margin-top: 16px;
}

.limits-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.limit-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.limit-label {
  font-weight: 500;
  color: #374151;
  min-width: 120px;
}

.limit-value {
  flex: 1;
}

.test-form {
  max-width: 500px;
}

.test-result {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #e5e7eb;
}

.test-result h4 {
  font-size: 16px;
  font-weight: 600;
  color: #374151;
  margin: 0 0 12px 0;
}

:deep(.ant-card-head-title) {
  font-weight: 600;
  font-size: 16px;
}

:deep(.ant-table-thead > tr > th) {
  background-color: #fafafa;
  font-weight: 600;
}

:deep(.ant-tabs-tab) {
  font-weight: 500;
}

:deep(.ant-upload-list) {
  margin-top: 8px;
}
</style>