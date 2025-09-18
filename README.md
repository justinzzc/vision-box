# 视觉检测应用

基于supervision库的智能视觉检测Web应用，支持图片和视频中目标对象的自动识别与标注。

## 项目结构

```
vision-box/
├── frontend/          # Vue.js 前端应用
├── backend/           # FastAPI 后端服务
├── data/              # 数据存储目录
│   ├── uploads/       # 上传文件
│   ├── results/       # 检测结果
│   └── models/        # AI模型文件
├── docker-compose.yml # Docker编排配置
├── .env.example       # 环境变量模板
└── build.py           # 统一构建脚本
```

## 技术栈

- **前端**: Vue.js 3 + Vite + Ant Design Vue + Axios
- **后端**: FastAPI + Supervision + OpenCV + Ultralytics
- **数据库**: SQLite
- **AI模型**: YOLOv8 系列模型

## 快速开始

### Docker部署

```bash
# 1. 配置环境变量
cp .env.example .env

# 2. 启动服务
docker-compose up -d --build

# 3. 访问应用
# 前端: http://localhost
# 后端API: http://localhost:8000
```

### 本地开发

```bash
# 1. 启动后端服务
cd backend
pip install -r requirements.txt

uvicorn main:app --reload
# 或者
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 2. 启动前端服务
cd frontend
npm install
npm run dev
```

## 主要功能

- 🎯 图片和视频目标检测
- ⚙️ 灵活的检测参数配置
- 📊 可视化标注结果展示
- 💾 JSON格式结果导出
- 📱 响应式设计
- 📈 检测历史管理

## 许可证

MIT License