# 交通事故实时检测与动态警示系统

## 项目概述

基于 **YOLOv5 + DeepSORT** 的交通事故实时检测系统，实现视频流实时分析、事故自动检测、告警推送和可视化管理。

### 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Element Plus + ECharts + 高德地图 |
| 后端 | Flask + Flask-SocketIO + SQLAlchemy |
| 算法 | YOLOv5 + DeepSORT |
| 数据库 | SQLite |
| 通信 | REST API + WebSocket |

### 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         前端 (Vue 3)                             │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │ 登录页  │ │ 仪表盘  │ │事故列表 │ │事故详情 │ │摄像头管理│   │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘   │
│       │           │           │           │           │         │
│       └───────────┴───────────┴───────────┴───────────┘         │
│                           │                                      │
│                    Axios + Socket.IO                             │
└───────────────────────────┼─────────────────────────────────────┘
                            │ HTTP/WebSocket
┌───────────────────────────┼─────────────────────────────────────┐
│                         后端 (Flask)                             │
│                           │                                      │
│  ┌────────────────────────┴────────────────────────┐            │
│  │                    API 层                        │            │
│  │  /api/auth  /api/cameras  /api/accidents  ...   │            │
│  └────────────────────────┬────────────────────────┘            │
│                           │                                      │
│  ┌────────────────────────┴────────────────────────┐            │
│  │                  核心处理层                      │            │
│  │  PipelineManager → ProcessingPipeline           │            │
│  │       ↓              ↓                          │            │
│  │  YOLOv5Detector → DeepSORTTracker               │            │
│  │       ↓              ↓                          │            │
│  │  AccidentDetector → 告警推送                    │            │
│  └────────────────────────┬────────────────────────┘            │
│                           │                                      │
│  ┌────────────────────────┴────────────────────────┐            │
│  │                   数据层                        │            │
│  │  SQLite (User, Camera, Accident)                │            │
│  └─────────────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 项目结构

```
YOLOv5_deepsort_traffic_accident_v1/
├── backend/                          # 后端服务
│   ├── app/                          # 应用主目录
│   │   ├── api/                      # API路由层
│   │   │   ├── __init__.py
│   │   │   ├── accidents.py          # 事故管理接口
│   │   │   ├── auth.py               # 认证接口
│   │   │   ├── cameras.py            # 摄像头管理接口
│   │   │   ├── statistics.py         # 统计数据接口
│   │   │   └── video.py              # 视频流接口
│   │   ├── core/                     # 核心处理模块
│   │   │   ├── __init__.py
│   │   │   ├── accident_detector.py  # 事故检测算法
│   │   │   ├── annotator.py          # 帧标注工具
│   │   │   ├── coordinate_mapper.py  # 坐标映射
│   │   │   ├── detector.py           # YOLOv5检测器
│   │   │   ├── pipeline.py           # 处理流水线
│   │   │   ├── pipeline_manager.py   # 流水线管理器
│   │   │   └── tracker.py            # DeepSORT跟踪器
│   │   ├── models/                   # 数据模型
│   │   │   ├── __init__.py
│   │   │   ├── accident.py           # 事故模型
│   │   │   ├── camera.py             # 摄像头模型
│   │   │   └── user.py               # 用户模型
│   │   ├── sockets/                  # WebSocket事件
│   │   │   ├── __init__.py
│   │   │   └── events.py             # Socket事件处理
│   │   ├── utils/                    # 工具函数
│   │   │   ├── __init__.py
│   │   │   ├── auth_decorator.py     # 认证装饰器
│   │   │   └── response.py           # 响应格式化
│   │   ├── __init__.py               # 应用工厂
│   │   ├── config.py                 # 配置文件
│   │   └── extensions.py             # 扩展初始化
│   ├── data/                         # 数据目录
│   │   ├── calibration/              # 标定数据
│   │   └── test_videos/              # 测试视频
│   ├── deep_sort/                    # DeepSORT算法
│   │   ├── deep/                     # ReID模型
│   │   │   ├── __init__.py
│   │   │   └── reid.py
│   │   ├── __init__.py
│   │   ├── deep_sort.py
│   │   ├── detection.py
│   │   ├── kalman_filter.py
│   │   ├── linear_assignment.py
│   │   ├── track.py
│   │   └── tracker.py
│   ├── static/                       # 静态文件
│   │   └── snapshots/                # 事故截图
│   ├── weights/                      # 模型权重
│   │   ├── ckpt.t7                   # DeepSORT ReID权重
│   │   └── yolov5s.pt                # YOLOv5权重
│   ├── init_db.py                    # 数据库初始化
│   ├── requirements.txt              # Python依赖
│   ├── run.py                        # 启动入口
│   └── traffic_accident.db           # SQLite数据库
│
├── frontend/                         # 前端服务
│   ├── public/                       # 公共资源
│   ├── src/                          # 源代码
│   │   ├── api/                      # API请求
│   │   │   ├── accident.js           # 事故API
│   │   │   ├── auth.js               # 认证API
│   │   │   ├── camera.js             # 摄像头API
│   │   │   ├── request.js            # Axios封装
│   │   │   └── statistics.js         # 统计API
│   │   ├── assets/                   # 静态资源
│   │   │   └── styles/
│   │   │       └── global.scss       # 全局样式
│   │   ├── components/               # 组件
│   │   │   └── layout/
│   │   │       ├── AppHeader.vue     # 头部组件
│   │   │       ├── AppLayout.vue     # 布局组件
│   │   │       └── AppSidebar.vue    # 侧边栏组件
│   │   ├── composables/              # 组合式函数
│   │   │   └── useSocket.js          # WebSocket封装
│   │   ├── router/                   # 路由配置
│   │   │   └── index.js
│   │   ├── views/                    # 页面组件
│   │   │   ├── AccidentDetail.vue    # 事故详情页
│   │   │   ├── AccidentList.vue      # 事故列表页
│   │   │   ├── CameraManage.vue      # 摄像头管理页
│   │   │   ├── Dashboard.vue         # 监控大屏
│   │   │   └── Login.vue             # 登录页
│   │   ├── App.vue                   # 根组件
│   │   └── main.js                   # 入口文件
│   ├── dist/                         # 构建输出
│   ├── index.html                    # HTML模板
│   ├── package.json                  # 依赖配置
│   └── vite.config.js                # Vite配置
│
├── PROJECT_GUIDE.md                  # 项目指南
├── 项目完成情况报告.md                 # 完成报告
└── 需求+设计文档.md                    # 需求设计文档
```

### 目录说明

| 目录 | 说明 |
|------|------|
| `backend/app/api/` | REST API路由，处理HTTP请求 |
| `backend/app/core/` | 核心算法模块，包含检测、跟踪、事故判断 |
| `backend/app/models/` | SQLAlchemy数据模型 |
| `backend/app/sockets/` | WebSocket事件处理 |
| `backend/deep_sort/` | DeepSORT多目标跟踪算法实现 |
| `backend/weights/` | 模型权重文件 |
| `backend/static/snapshots/` | 事故截图存储 |
| `frontend/src/views/` | Vue页面组件 |
| `frontend/src/api/` | 前端API请求封装 |
| `frontend/src/components/` | 可复用组件 |

---

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- CUDA 11.x (可选，用于GPU加速)

### 后端启动

```bash
cd backend

# 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python init_db.py

# 启动服务
python run.py
```

后端服务运行在 http://127.0.0.1:5000

### 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端服务运行在 http://127.0.0.1:3000

### 默认账号

- 用户名: `admin`
- 密码: `admin123`

---

## 核心模块详解

### 1. 目标检测模块 (YOLOv5Detector)

**文件**: `backend/app/core/detector.py`

**功能**: 使用YOLOv5模型进行目标检测

**检测目标类别**:
| ID | 类别 | 说明 |
|----|------|------|
| 0 | person | 行人 |
| 1 | bicycle | 自行车 |
| 2 | car | 小汽车 |
| 3 | motorcycle | 摩托车 |
| 5 | bus | 公交车 |
| 7 | truck | 卡车 |

**关键参数**:
```python
YOLO_CONF = 0.5      # 置信度阈值，低于此值的目标被过滤
YOLO_IOU = 0.45      # NMS的IoU阈值
YOLO_IMG_SIZE = 640  # 输入图像尺寸
```

**执行流程**:
```
输入帧 → 预处理(缩放/归一化) → 模型推理 → NMS后处理 → 检测结果列表
```

### 2. 目标跟踪模块 (DeepSORTTracker)

**文件**: `backend/app/core/tracker.py`

**功能**: 多目标跟踪，关联连续帧中的同一目标

**跟踪信息**:
```python
@dataclass
class TrackInfo:
    track_id: int          # 跟踪ID
    class_name: str        # 目标类别
    confidence: float      # 置信度
    bbox: tuple            # 边界框 (x1, y1, x2, y2)
    trajectory: deque      # 轨迹历史 (最近30个点)
    speed_history: deque   # 速度历史 (最近10帧)
    age: int               # 跟踪帧数
    hits: int              # 命中次数
```

**跟踪算法**:
1. **DeepSORT模式**: 使用ReID特征提取 + 卡尔曼滤波 + 匈牙利算法
2. **简化模式**: 使用IoU匹配 (当ReID模型不可用时)

**关键参数**:
```python
DEEPSORT_MAX_AGE = 50           # 最大丢失帧数
DEEPSORT_MAX_COSINE_DIST = 0.7  # 最大余弦距离阈值
```

### 3. 事故检测模块 (AccidentDetector)

**文件**: `backend/app/core/accident_detector.py`

**功能**: 基于跟踪数据检测交通事故

**检测算法**:

#### 3.1 碰撞检测
```
判断条件: 两个目标的边界框IoU > ACCIDENT_COLLISION_IOU (0.3)
连续帧数: 超过 ACCIDENT_COLLISION_FRAMES (3) 帧
```

#### 3.2 速度异常检测
```
判断条件: 目标速度骤降 (当前速度 < 历史平均速度 * 0.3)
```

#### 3.3 综合评分
```
score_total = w_collision * score_collision + w_speed * score_speed
w_collision = 0.5 (碰撞权重)
w_speed = 0.5 (速度权重)
```

#### 3.4 严重程度判定
```
score_total >= 0.9 → critical (重大事故)
score_total >= 0.75 → serious (严重事故)
score_total >= 0.6 → normal (一般事故)
```

**冷却机制**:
```python
ACCIDENT_COOLDOWN_SECONDS = 30  # 同一位置30秒内不重复告警
```

### 4. 处理流水线 (ProcessingPipeline)

**文件**: `backend/app/core/pipeline.py`

**功能**: 单个摄像头的完整处理流程

**执行流程**:
```
┌─────────────────────────────────────────────────────────────┐
│                      主处理循环                              │
│                                                             │
│  1. 读取视频帧                                               │
│     cap.read() → frame                                      │
│                                                             │
│  2. YOLOv5检测                                               │
│     detector.detect_for_tracker(frame) → detections         │
│                                                             │
│  3. DeepSORT跟踪                                             │
│     tracker.update(detections) → tracks                     │
│                                                             │
│  4. 事故分析                                                 │
│     accident_detector.analyze(tracks) → accidents           │
│                                                             │
│  5. 帧标注                                                   │
│     annotator.draw_tracks(frame, tracks)                    │
│     annotator.draw_accident_marker(frame, accident)         │
│                                                             │
│  6. 帧缓冲 (MJPEG流)                                         │
│     frame_buffer[camera_id] = annotated_frame               │
│                                                             │
│  7. 事故处理                                                 │
│     _handle_accident() → 保存截图 + 数据库记录 + WebSocket推送│
│                                                             │
│  8. FPS统计                                                  │
│     计算并打印实时处理帧率                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5. 流水线管理器 (PipelineManager)

**文件**: `backend/app/core/pipeline_manager.py`

**功能**: 单例模式管理所有摄像头处理流水线

**主要方法**:
| 方法 | 功能 |
|------|------|
| `init_app(app, socketio)` | 初始化，加载YOLOv5模型 |
| `start_camera(camera_id)` | 启动指定摄像头的处理流水线 |
| `stop_camera(camera_id)` | 停止指定摄像头的处理流水线 |
| `generate_mjpeg(camera_id)` | 生成MJPEG视频流响应 |

---

## API 接口文档

### 认证接口

#### POST /api/auth/login
用户登录

**请求体**:
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 1,
      "username": "admin"
    }
  },
  "message": "success"
}
```

### 摄像头接口

#### GET /api/cameras
获取摄像头列表

**响应**:
```json
{
  "code": 200,
  "data": [
    {
      "id": 1,
      "name": "测试路口A",
      "camera_code": "CAM001",
      "stream_url": "data/test_videos/test.mp4",
      "stream_type": "file",
      "location_lat": 39.9042,
      "location_lng": 116.4074,
      "location_desc": "模拟路口A",
      "status": "offline"
    }
  ]
}
```

#### POST /api/cameras/<id>/start
启动摄像头检测

#### POST /api/cameras/<id>/stop
停止摄像头检测

### 事故接口

#### GET /api/accidents
分页查询事故列表

**参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| page | int | 页码，默认1 |
| per_page | int | 每页数量，默认15 |
| camera_id | int | 摄像头ID筛选 |
| severity | string | 严重程度筛选 |
| status | string | 状态筛选 |
| start_time | string | 开始时间 |
| end_time | string | 结束时间 |

#### PUT /api/accidents/<id>
更新事故信息

**请求体**:
```json
{
  "accident_type": "collision",
  "severity": "serious",
  "status": "acknowledged",
  "address": "北京市朝阳区xxx路口"
}
```

#### DELETE /api/accidents/<id>
删除事故记录 (同时删除截图文件)

### 统计接口

#### GET /api/statistics/overview
获取概览统计

**响应**:
```json
{
  "code": 200,
  "data": {
    "total_count": 100,
    "today_count": 5,
    "pending_count": 10,
    "online_cameras": 3,
    "total_cameras": 5
  }
}
```

#### GET /api/statistics/trend
获取事故趋势数据

**参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| days | int | 统计天数，默认7 |

**响应**:
```json
{
  "code": 200,
  "data": {
    "labels": ["03-03", "03-04", "03-05", "03-06", "03-07", "03-08", "03-09"],
    "values": [0, 0, 0, 0, 0, 0, 10]
  }
}
```

#### GET /api/statistics/severity
获取事故严重程度分布

**响应**:
```json
{
  "code": 200,
  "data": [
    {"name": "一般", "value": 5},
    {"name": "较重", "value": 3},
    {"name": "严重", "value": 2}
  ]
}
```

#### GET /api/statistics/accident-types
获取事故类型分布

**响应**:
```json
{
  "code": 200,
  "data": [
    {"name": "车辆碰撞", "value": 3},
    {"name": "追尾事故", "value": 2},
    {"name": "侧面碰撞", "value": 1},
    {"name": "翻车事故", "value": 0},
    {"name": "多车事故", "value": 4},
    {"name": "交通事故", "value": 0}
  ]
}
```

#### GET /api/statistics/traffic-flow
获取车辆流量统计（模拟数据）

**参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| hours | int | 统计小时数，默认24 |

**响应**:
```json
{
  "code": 200,
  "data": {
    "labels": ["00:00", "01:00", "02:00", ...],
    "values": [45, 30, 25, ...]
  }
}
```

> **注意**: 车辆流量数据目前为模拟数据，根据时段自动调整：
> - 早晚高峰（7-9点、17-19点）：流量增加80%
> - 凌晨低谷（0-5点）：流量减少70%
> - 其他时段：随机生成50-150辆

#### GET /api/statistics/vehicle-types
获取车辆类型分布（模拟数据）

**响应**:
```json
{
  "code": 200,
  "data": [
    {"name": "小型车辆", "value": 350},
    {"name": "中型车辆", "value": 100},
    {"name": "大型车辆", "value": 50},
    {"name": "摩托车", "value": 30},
    {"name": "行人", "value": 15}
  ]
}
```

#### GET /api/statistics/hourly-accidents
获取按小时统计的事故分布

**响应**:
```json
{
  "code": 200,
  "data": {
    "labels": ["00:00", "01:00", ..., "23:00"],
    "values": [0, 0, 0, 0, 0, 0, 0, 2, 1, 3, ...]
  }
}
```

### 视频流接口

#### GET /api/video/stream/<camera_id>
MJPEG视频流

**响应**: `multipart/x-mixed-replace` 格式的视频流

---

## WebSocket 事件

### 客户端事件

| 事件 | 说明 |
|------|------|
| `connect` | 连接建立 |
| `disconnect` | 断开连接 |

### 服务端事件

#### accident_alert
事故告警推送

**数据结构**:
```json
{
  "accident_id": 1,
  "accident_no": "ACC-20260309-001",
  "camera_id": 1,
  "camera_name": "测试路口A",
  "trigger_time": "2026-03-09 10:30:00",
  "severity": "serious",
  "severity_desc": "严重事故",
  "accident_type": "collision",
  "accident_type_desc": "车辆碰撞",
  "score_total": 0.75,
  "geo_lat": 39.9042,
  "geo_lng": 116.4074,
  "address": "模拟路口A",
  "snapshot_url": "/static/snapshots/acc_1_1234567890.jpg",
  "message": "检测到严重事故：车辆碰撞"
}
```

---

## 配置说明

### 后端配置 (backend/app/config.py)

```python
class Config:
    # 安全配置
    SECRET_KEY = 'traffic-accident-secret-key-2025'
    JWT_SECRET = 'jwt-secret-key-2025'
    JWT_EXPIRE_HOURS = 8

    # 数据库
    SQLALCHEMY_DATABASE_URI = 'sqlite:///traffic_accident.db'

    # YOLOv5配置
    YOLO_WEIGHTS = 'weights/yolov5s.pt'
    YOLO_CONF = 0.5
    YOLO_IOU = 0.45
    YOLO_IMG_SIZE = 640

    # DeepSORT配置
    DEEPSORT_MAX_AGE = 50
    DEEPSORT_MAX_COSINE_DIST = 0.7
    DEEPSORT_MODEL_PATH = 'weights/ckpt.t7'

    # 事故检测配置
    ACCIDENT_WEIGHT_COLLISION = 0.5
    ACCIDENT_WEIGHT_SPEED = 0.5
    ACCIDENT_THRESHOLD = 0.6
    ACCIDENT_COLLISION_IOU = 0.3
    ACCIDENT_COLLISION_FRAMES = 3
    ACCIDENT_COOLDOWN_SECONDS = 30

    # 截图存储
    SNAPSHOT_FOLDER = 'static/snapshots'
```

### 前端配置 (frontend/vite.config.js)

```javascript
export default defineConfig({
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true
      },
      '/static': {
        target: 'http://127.0.0.1:5000'
      },
      '/socket.io': {
        target: 'http://127.0.0.1:5000',
        ws: true
      }
    }
  }
})
```

### 高德地图 API 配置

项目使用高德地图JS API进行地图展示和事故定位。

#### 获取API密钥

1. 访问 [高德开放平台](https://console.amap.com/)
2. 注册/登录账号
3. 进入"应用管理" → "创建新应用"
4. 添加"Web端JS API"类型Key
5. 获取**Key**和**安全密钥**（Security Code）

#### 配置密钥

当前密钥硬编码在以下文件中：

**文件**: `frontend/src/views/Dashboard.vue`
```javascript
const AMAP_KEY = '你的高德Key'
const AMAP_SECRET = '你的安全密钥'
window._AMapSecurityConfig = {
  securityJsCode: AMAP_SECRET,
}
```

**文件**: `frontend/src/views/AccidentDetail.vue`
```javascript
const AMAP_KEY = '你的高德Key'
const AMAP_SECRET = '你的安全密钥'
window._AMapSecurityConfig = {
  securityJsCode: AMAP_SECRET,
}
```

#### 推荐做法

建议将密钥提取到环境变量中：

1. 创建 `frontend/.env.local` 文件：
```
VITE_AMAP_KEY=你的高德Key
VITE_AMAP_SECRET=你的安全密钥
```

2. 在Vue组件中使用：
```javascript
const AMAP_KEY = import.meta.env.VITE_AMAP_KEY
const AMAP_SECRET = import.meta.env.VITE_AMAP_SECRET
```

#### 启用服务

在高德开放平台控制台，需要启用以下服务：
- [x] Web端 JS API
- [x] 搜索服务（可选，用于地址解析）
- [x] 逆地理编码服务（可选，用于坐标转地址）

---

## 项目完成情况

### 已完成功能

| 模块 | 功能 | 状态 | 说明 |
|------|------|------|------|
| **用户认证** | 登录/登出 | ✅ 完成 | JWT Token认证 |
| **摄像头管理** | CRUD操作 | ✅ 完成 | 创建/查询/更新/删除 |
| | 启动/停止检测 | ✅ 完成 | 多线程处理流水线 |
| | 视频流推送 | ✅ 完成 | MJPEG流 |
| **事故检测** | YOLOv5检测 | ✅ 完成 | 6类目标检测 |
| | DeepSORT跟踪 | ✅ 完成 | 多目标跟踪 |
| | 碰撞检测 | ✅ 完成 | IoU重叠度分析 |
| | 速度异常检测 | ✅ 完成 | 速度骤降分析 |
| | 告警推送 | ✅ 完成 | WebSocket实时推送 |
| **事故管理** | 列表查询 | ✅ 完成 | 分页/筛选 |
| | 详情查看 | ✅ 完成 | 包含截图/地图 |
| | 信息编辑 | ✅ 完成 | 类型/严重程度/状态 |
| | 删除功能 | ✅ 完成 | 同时删除截图文件 |
| **数据统计** | 概览统计 | ✅ 完成 | 事故数/摄像头状态 |
| | 趋势分析 | ✅ 完成 | 按日期统计（支持7/14/30天） |
| | 严重程度分布 | ✅ 完成 | 饼图展示 |
| | **事故类型分布** | ✅ 新增 | 饼图展示 |
| | **车辆流量统计** | ✅ 新增 | 柱状图（支持12/24/48小时） |
| | **车辆类型分布** | ✅ 新增 | 饼图展示 |
| | **按小时事故分布** | ✅ 新增 | 柱状图展示 |
| **前端界面** | 登录页 | ✅ 完成 | |
| | 仪表盘 | ✅ 完成 | 实时监控/地图/统计图表 |
| | 事故列表 | ✅ 完成 | 筛选/编辑/删除 |
| | 事故详情 | ✅ 完成 | 截图/地图/评分 |
| | 摄像头管理 | ✅ 完成 | CRUD/控制 |
| **统计图表** | 事故趋势折线图 | ✅ 新增 | ECharts实现，支持时间范围切换 |
| | 车辆流量柱状图 | ✅ 新增 | ECharts实现，支持小时范围切换 |
| | 严重程度饼图 | ✅ 新增 | 环形饼图，交互式 |
| | 事故类型饼图 | ✅ 新增 | 环形饼图，交互式 |
| | 车辆类型饼图 | ✅ 新增 | 环形饼图，交互式 |

### 待完善功能

| 模块 | 功能 | 优先级 | 说明 |
|------|------|--------|------|
| **事故检测** | 检测算法优化 | 🔴 高 | 当前误报率较高 |
| | 事故类型细分 | 🟡 中 | 区分追尾/侧面碰撞等 |
| | 轨迹预测 | 🟡 中 | 预测潜在碰撞 |
| **摄像头** | RTSP流支持 | 🟡 中 | 实时摄像头接入 |
| | 标定工具 | 🟡 中 | 可视化坐标映射 |
| **系统** | 用户权限管理 | 🟢 低 | 多角色权限 |
| | 操作日志 | 🟢 低 | 审计追踪 |
| | 数据导出 | 🟢 低 | 报表生成 |

---

## 统计图表功能

### 功能概述

监控大屏新增了5个统计图表，用于直观展示事故和车辆流量数据：

| 图表类型 | 名称 | 数据来源 | 交互功能 |
|---------|------|----------|----------|
| 折线图 | 事故趋势 | 真实数据 | 支持7/14/30天切换 |
| 柱状图 | 车辆流量统计 | 模拟数据 | 支持12/24/48小时切换 |
| 饼图 | 事故严重程度分布 | 真实数据 | 悬停显示详情 |
| 饼图 | 事故类型分布 | 真实数据 | 悬停显示详情 |
| 饼图 | 车辆类型分布 | 模拟数据 | 悬停显示详情 |

### 技术实现

**前端技术栈**:
- ECharts 5.4 - 图表库
- vue-echarts - Vue封装组件
- 按需引入图表组件（LineChart, PieChart, BarChart）

**图表配置示例**:
```javascript
// 折线图配置
const trendChartOption = {
  tooltip: { trigger: 'axis' },
  xAxis: { type: 'category', data: labels },
  yAxis: { type: 'value' },
  series: [{
    type: 'line',
    smooth: true,
    data: values,
    areaStyle: { /* 渐变填充 */ }
  }]
}

// 饼图配置
const pieChartOption = {
  tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
  series: [{
    type: 'pie',
    radius: ['40%', '70%'],  // 环形饼图
    itemStyle: { borderRadius: 10 }
  }]
}
```

### 数据说明

#### 真实数据（从数据库获取）
- **事故趋势**: 统计指定天数内每天的事故数量
- **事故严重程度**: 统计一般/较重/严重事故的数量分布
- **事故类型**: 统计碰撞/追尾/侧面碰撞等类型的数量分布

#### 模拟数据（算法生成）
- **车辆流量**: 根据时段特征生成模拟数据
  - 早晚高峰（7-9点、17-19点）：流量增加80%
  - 凌晨低谷（0-5点）：流量减少70%
  - 其他时段：随机生成50-150辆
- **车辆类型**: 随机生成小型/中型/大型车辆等分布

### 扩展真实流量统计

如需实现真实的车辆流量统计，需要：

1. **数据模型扩展**:
```python
class TrafficFlow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    camera_id = db.Column(db.Integer, ForeignKey('cameras.id'))
    record_time = db.Column(db.DateTime)
    vehicle_count = db.Column(db.Integer)
    vehicle_types = db.Column(db.JSON)  # 各类型车辆数量
```

2. **Pipeline集成**:
```python
# 在 ProcessingPipeline 中添加计数逻辑
def _count_vehicles(self, tracks):
    count = len([t for t in tracks if t.class_name in ['car', 'truck', 'bus']])
    # 定期写入数据库
```

3. **潜在问题**:
   - 性能开销：每帧计数增加计算负担
   - 数据库压力：频繁写入需要优化
   - 准确性问题：重复计数、漏检、ID切换

---

## 已知问题与改进方向

### 🔴 高优先级问题

#### 1. 事故检测误报率高

**问题描述**:
当前事故检测算法基于简单的IoU重叠和速度骤降判断，容易产生误报：
- 车辆正常并线/超车被误判为碰撞
- 车辆正常减速/停车被误判为速度异常
- 光照变化/阴影影响检测稳定性

**根本原因**:
1. 检测算法过于简单，缺乏上下文理解
2. 未考虑道路场景语义
3. 缺乏事故特征学习

**改进方向**:
```
短期优化 :
├── 调整检测阈值，提高触发门槛
├── 增加目标运动方向分析
├── 添加场景约束 (仅检测道路区域)
└── 优化冷却机制

中期优化 :
├── 引入光流分析，检测运动突变
├── 添加目标姿态估计
├── 训练事故分类器 (正常/碰撞/危险)
└── 集成场景分割模型

长期优化 :
├── 构建事故检测数据集
├── 训练端到端事故检测模型
├── 引入时序建模 (LSTM/Transformer)
└── 多模态融合 (视觉+运动特征)
```

#### 2. DeepSORT ReID模型兼容性

**问题描述**:
DeepSORT的ReID特征提取模型在某些环境下加载失败，回退到简化IoU跟踪模式

**改进方向**:
- 提供多种ReID模型选项
- 添加模型自动下载功能
- 优化模型加载错误处理

### 🟡 中优先级问题

#### 3. 缺乏RTSP实时流支持

**问题描述**:
当前仅支持本地视频文件，无法接入实时摄像头

**改进方向**:
- 添加RTSP流解析
- 实现断线重连机制
- 支持多码流切换

#### 4. 坐标映射功能不完善

**问题描述**:
缺乏可视化的摄像头标定工具，坐标映射配置困难

**改进方向**:
- 开发Web端标定工具
- 支持地图选点
- 自动计算单应性矩阵

#### 5. 事故类型判断粗糙

**问题描述**:
当前仅根据涉事目标数量和碰撞评分判断类型，准确度低

**改进方向**:
- 分析碰撞角度
- 分析目标运动轨迹
- 添加更多事故类型特征

### 🟢 低优先级问题

#### 6. 缺乏用户权限管理

**问题描述**:
所有用户权限相同，无法区分管理员/操作员

**改进方向**:
- 添加角色管理
- 实现权限控制
- 操作日志记录

#### 7. 缺乏数据导出功能

**问题描述**:
无法导出事故统计报表

**改进方向**:
- 支持Excel/PDF导出
- 自定义报表模板
- 定期自动生成报告

---

## 开发指南

### 添加新的检测目标

1. 修改 `backend/app/config.py`:
```python
TARGET_CLASSES = {
    0: 'person', 
    1: 'bicycle', 
    2: 'car',
    3: 'motorcycle', 
    5: 'bus', 
    7: 'truck',
    # 添加新目标
    9: 'traffic_light'
}
```

2. YOLOv5模型需要支持对应类别

### 调整事故检测参数

修改 `backend/app/config.py`:
```python
# 降低误报 - 提高阈值
ACCIDENT_THRESHOLD = 0.7          # 原0.6
ACCIDENT_COLLISION_IOU = 0.4      # 原0.3
ACCIDENT_COLLISION_FRAMES = 5     # 原3

# 调整权重
ACCIDENT_WEIGHT_COLLISION = 0.6   # 碰撞权重
ACCIDENT_WEIGHT_SPEED = 0.4       # 速度权重
```

### 添加新的API接口

1. 在 `backend/app/api/` 创建路由文件
2. 在 `backend/app/__init__.py` 注册蓝图
3. 在 `frontend/src/api/` 添加请求方法

### 添加新的前端页面

1. 在 `frontend/src/views/` 创建Vue组件
2. 在 `frontend/src/router/index.js` 添加路由
3. 在 `frontend/src/components/layout/AppSidebar.vue` 添加菜单项

---

## 部署指南

### 开发环境

```bash
# 后端
cd backend
pip install -r requirements.txt
python run.py

# 前端
cd frontend
npm install
npm run dev
```


---

## 常见问题

### Q: YOLOv5模型加载失败
A: 检查 `weights/yolov5s.pt` 是否存在，或重新下载模型

### Q: DeepSORT跟踪效果差
A: 检查 `weights/ckpt.t7` 是否存在，或使用简化模式

### Q: 视频流无法显示
A: 确保摄像头已启动，检查浏览器控制台是否有跨域错误

### Q: WebSocket连接失败
A: 检查后端是否正常运行，确认端口未被占用

### Q: 事故检测误报多
A: 调整 `config.py` 中的检测阈值参数

---

## 更新日志

### v1.1.0 (2026-03-09)
- **新增功能**
  - 监控大屏增加统计图表展示区域
  - 事故趋势折线图（支持7/14/30天切换）
  - 车辆流量统计柱状图（支持12/24/48小时切换）
  - 事故严重程度分布饼图
  - 事故类型分布饼图
  - 车辆类型分布饼图
- **后端API**
  - 新增 `/api/statistics/accident-types` 事故类型分布接口
  - 新增 `/api/statistics/traffic-flow` 车辆流量统计接口
  - 新增 `/api/statistics/vehicle-types` 车辆类型分布接口
  - 新增 `/api/statistics/hourly-accidents` 按小时事故分布接口
- **Bug修复**
  - 修复事故趋势数据日期匹配问题（字符串与date对象类型不匹配）
- **界面优化**
  - 调整监控大屏布局，增大实时监控区域高度
  - 图表区域自适应布局

### v1.0.0 (2026-03-09)
- 初始版本发布
- 实现基础事故检测功能
- 完成前后端核心功能
- 添加事故管理CRUD

---

## 联系方式

如有问题或建议，请提交Issue或联系开发团队。
