import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiClient } from '@/utils/api'
import { message } from 'ant-design-vue'

export const useDetectionStore = defineStore('detection', () => {
  // 状态
  const currentTask = ref(null)
  const detectionHistory = ref([])
  const availableModels = ref([
    { name: 'yolov8n', label: 'YOLOv8n (最快)', size: '6MB' },
    { name: 'yolov8s', label: 'YOLOv8s (平衡)', size: '22MB' },
    { name: 'yolov8m', label: 'YOLOv8m (精确)', size: '52MB' },
    { name: 'yolov8l', label: 'YOLOv8l (高精度)', size: '87MB' },
    { name: 'yolov8x', label: 'YOLOv8x (最高精度)', size: '136MB' }
  ])
  const detectionClasses = ref([
    { id: 0, name: 'person', label: '人' },
    { id: 1, name: 'bicycle', label: '自行车' },
    { id: 2, name: 'car', label: '汽车' },
    { id: 3, name: 'motorcycle', label: '摩托车' },
    { id: 5, name: 'bus', label: '公交车' },
    { id: 6, name: 'train', label: '火车' },
    { id: 7, name: 'truck', label: '卡车' },
    { id: 16, name: 'bird', label: '鸟' },
    { id: 17, name: 'cat', label: '猫' },
    { id: 18, name: 'dog', label: '狗' }
  ])
  
  const loading = ref(false)
  const uploadProgress = ref(0)
  
  // 计算属性
  const isDetecting = computed(() => {
    return currentTask.value && ['pending', 'processing'].includes(currentTask.value.status)
  })
  
  const completedTasks = computed(() => {
    return detectionHistory.value.filter(task => task.status === 'completed')
  })
  
  const failedTasks = computed(() => {
    return detectionHistory.value.filter(task => task.status === 'failed')
  })
  
  // 动作
  const uploadFile = async (file, fileType) => {
    try {
      loading.value = true
      uploadProgress.value = 0
      
      const response = await apiClient.uploadFile(file, fileType)
      
      // 检查响应是否包含file_id，表示上传成功
      if (response.file_id) {
        // message.success('文件上传成功')
        return response
      } else {
        throw new Error('文件上传失败')
      }
    } catch (error) {
      console.error('文件上传错误:', error)
      message.error('文件上传失败')
      throw error
    } finally {
      loading.value = false
      uploadProgress.value = 0
    }
  }
  
  const startDetection = async (params) => {
    try {
      loading.value = true
      
      const response = await apiClient.detect(params)
      
      if (response.task_id) {
        currentTask.value = {
          id: response.task_id,
          status: response.status,
          params,
          createdAt: new Date().toISOString()
        }
        
        message.success('检测任务已启动')
        
        // 开始轮询检测结果
        pollDetectionResult(response.task_id)
        
        return response
      } else {
        throw new Error('启动检测任务失败')
      }
    } catch (error) {
      console.error('启动检测错误:', error)
      message.error('启动检测任务失败')
      throw error
    } finally {
      loading.value = false
    }
  }
  
  const pollDetectionResult = async (taskId, maxAttempts = 60) => {
    let attempts = 0
    
    const poll = async () => {
      try {
        attempts++
        
        const result = await apiClient.getResult(taskId)
        
        if (currentTask.value && currentTask.value.id === taskId) {
          currentTask.value.status = result.status
          currentTask.value.result = result.result
          currentTask.value.annotatedUrl = result.annotated_url
        }
        
        if (result.status === 'completed') {
          message.success('检测完成')
          await loadHistory() // 刷新历史记录
          return result
        } else if (result.status === 'failed') {
          message.error('检测失败')
          return result
        } else if (attempts < maxAttempts) {
          // 继续轮询
          setTimeout(poll, 2000) // 每2秒轮询一次
        } else {
          message.error('检测超时')
          if (currentTask.value && currentTask.value.id === taskId) {
            currentTask.value.status = 'failed'
          }
        }
      } catch (error) {
        console.error('轮询检测结果错误:', error)
        if (attempts < maxAttempts) {
          setTimeout(poll, 2000)
        }
      }
    }
    
    poll()
  }
  
  const loadHistory = async (params = {}) => {
    try {
      const response = await apiClient.getHistory(params)
      detectionHistory.value = response.items || []
      return response
    } catch (error) {
      console.error('加载历史记录错误:', error)
      message.error('加载历史记录失败')
      throw error
    }
  }
  
  const deleteTask = async (taskId) => {
    try {
      await apiClient.deleteHistory(taskId)
      detectionHistory.value = detectionHistory.value.filter(task => task.id !== taskId)
      message.success('删除成功')
    } catch (error) {
      console.error('删除任务错误:', error)
      message.error('删除失败')
      throw error
    }
  }
  
  const downloadResult = async (taskId, format = 'json') => {
    try {
      const blob = await apiClient.downloadResult(taskId, format)
      const filename = `detection_result_${taskId}.${format}`
      
      // 创建下载链接
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      
      message.success('下载成功')
    } catch (error) {
      console.error('下载结果错误:', error)
      message.error('下载失败')
      throw error
    }
  }
  
  const clearCurrentTask = () => {
    currentTask.value = null
  }
  
  const getTaskById = (taskId) => {
    return detectionHistory.value.find(task => task.id === taskId)
  }
  
  return {
    // 状态
    currentTask,
    detectionHistory,
    availableModels,
    detectionClasses,
    loading,
    uploadProgress,
    
    // 计算属性
    isDetecting,
    completedTasks,
    failedTasks,
    
    // 动作
    uploadFile,
    startDetection,
    pollDetectionResult,
    loadHistory,
    deleteTask,
    downloadResult,
    clearCurrentTask,
    getTaskById
  }
})