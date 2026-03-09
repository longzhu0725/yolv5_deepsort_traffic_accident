<template>
  <div class="dashboard">
    <div class="dashboard-top">
      <div class="video-section">
        <div class="section-header">
          <span class="section-title">实时监控</span>
          <el-select v-model="selectedCamera" placeholder="选择摄像头" size="small" style="width: 200px">
            <el-option
              v-for="cam in onlineCameras"
              :key="cam.id"
              :label="cam.name"
              :value="cam.id"
            />
          </el-select>
        </div>
        <div class="video-container">
          <img
            v-if="selectedCamera && isCameraOnline(selectedCamera)"
            :src="`/api/video/stream/${selectedCamera}`"
            class="video-stream"
            alt="视频流"
          />
          <div v-else class="no-video">
            <el-icon :size="60"><VideoCamera /></el-icon>
            <p>暂无视频流</p>
            <p class="hint">请在摄像头管理中启动摄像头</p>
          </div>
        </div>
      </div>
      
      <div class="map-section">
        <div class="section-header">
          <span class="section-title">事故位置地图</span>
        </div>
        <div class="map-container" ref="mapContainer"></div>
      </div>
    </div>
    
    <div class="dashboard-bottom">
      <div class="stats-section">
        <div class="stat-card">
          <div class="stat-icon" style="background: #409eff">
            <el-icon :size="24"><Calendar /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ overview.today_count }}</div>
            <div class="stat-label">今日事故</div>
          </div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon" style="background: #67c23a">
            <el-icon :size="24"><VideoCamera /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ overview.online_cameras }}/{{ overview.total_cameras }}</div>
            <div class="stat-label">在线摄像头</div>
          </div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon" style="background: #e6a23c">
            <el-icon :size="24"><Warning /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ overview.pending_count }}</div>
            <div class="stat-label">待处理</div>
          </div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon" style="background: #f56c6c">
            <el-icon :size="24"><DataAnalysis /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ overview.total_count }}</div>
            <div class="stat-label">累计事故</div>
          </div>
        </div>
      </div>
      
      <div class="alerts-section">
        <div class="section-header">
          <span class="section-title">最近告警</span>
        </div>
        <div class="alerts-list">
          <div
            v-for="alert in alertHistory.slice(0, 5)"
            :key="alert.accident_id"
            class="alert-item"
            :class="alert.severity"
          >
            <div class="alert-dot"></div>
            <div class="alert-info">
              <div class="alert-title">{{ alert.camera_name }}</div>
              <div class="alert-time">{{ alert.trigger_time }}</div>
            </div>
            <el-tag :type="getSeverityType(alert.severity)" size="small">
              {{ getSeverityText(alert.severity) }}
            </el-tag>
          </div>
          <div v-if="alertHistory.length === 0" class="no-alerts">
            暂无告警
          </div>
        </div>
      </div>
    </div>

    <div class="dashboard-charts">
      <div class="chart-row">
        <div class="chart-card">
          <div class="section-header">
            <span class="section-title">事故趋势</span>
            <el-radio-group v-model="trendDays" size="small" @change="fetchTrendData">
              <el-radio-button :value="7">近7天</el-radio-button>
              <el-radio-button :value="14">近14天</el-radio-button>
              <el-radio-button :value="30">近30天</el-radio-button>
            </el-radio-group>
          </div>
          <div class="chart-container">
            <v-chart :option="trendChartOption" autoresize />
          </div>
        </div>
        
        <div class="chart-card">
          <div class="section-header">
            <span class="section-title">车辆流量统计</span>
            <el-radio-group v-model="flowHours" size="small" @change="fetchTrafficFlow">
              <el-radio-button :value="12">近12小时</el-radio-button>
              <el-radio-button :value="24">近24小时</el-radio-button>
              <el-radio-button :value="48">近48小时</el-radio-button>
            </el-radio-group>
          </div>
          <div class="chart-container">
            <v-chart :option="trafficFlowOption" autoresize />
          </div>
        </div>
      </div>
      
      <div class="chart-row">
        <div class="chart-card">
          <div class="section-header">
            <span class="section-title">事故严重程度分布</span>
          </div>
          <div class="chart-container">
            <v-chart :option="severityChartOption" autoresize />
          </div>
        </div>
        
        <div class="chart-card">
          <div class="section-header">
            <span class="section-title">事故类型分布</span>
          </div>
          <div class="chart-container">
            <v-chart :option="accidentTypeOption" autoresize />
          </div>
        </div>
        
        <div class="chart-card">
          <div class="section-header">
            <span class="section-title">车辆类型分布</span>
          </div>
          <div class="chart-container">
            <v-chart :option="vehicleTypeOption" autoresize />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import AMapLoader from '@amap/amap-jsapi-loader'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart, BarChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components'
import { getCameras } from '@/api/camera'
import { getOverview, getTrend, getSeverity, getAccidentTypes, getTrafficFlow, getVehicleTypes, getHourlyAccidents } from '@/api/statistics'
import { useSocket } from '@/composables/useSocket'

use([
  CanvasRenderer,
  LineChart,
  PieChart,
  BarChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
])

const { alertHistory } = useSocket()

const cameras = ref([])
const overview = ref({
  today_count: 0,
  total_count: 0,
  pending_count: 0,
  online_cameras: 0,
  total_cameras: 0
})
const selectedCamera = ref(null)
const mapContainer = ref(null)
let map = null
let AMap = null
const cameraMarkers = {}
const accidentMarkers = []

const trendDays = ref(7)
const flowHours = ref(24)

const trendData = ref({ labels: [], values: [] })
const severityData = ref([])
const accidentTypeData = ref([])
const trafficFlowData = ref({ labels: [], values: [] })
const vehicleTypeData = ref([])

const AMAP_KEY = ''
const AMAP_SECRET = ''

window._AMapSecurityConfig = {
  securityJsCode: AMAP_SECRET,
}

const onlineCameras = computed(() => {
  return cameras.value.filter(c => c.status === 'online')
})

const isCameraOnline = (cameraId) => {
  const cam = cameras.value.find(c => c.id === cameraId)
  return cam && cam.status === 'online'
}

const getSeverityType = (severity) => {
  const map = {
    normal: 'warning',
    serious: 'danger',
    critical: 'danger'
  }
  return map[severity] || 'info'
}

const getSeverityText = (severity) => {
  const map = {
    normal: '一般',
    serious: '较重',
    critical: '严重'
  }
  return map[severity] || severity
}

const trendChartOption = computed(() => ({
  tooltip: {
    trigger: 'axis',
    axisPointer: {
      type: 'shadow'
    }
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    top: '10%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    data: trendData.value.labels,
    axisLine: {
      lineStyle: {
        color: '#ddd'
      }
    },
    axisLabel: {
      color: '#666'
    }
  },
  yAxis: {
    type: 'value',
    axisLine: {
      show: false
    },
    axisTick: {
      show: false
    },
    splitLine: {
      lineStyle: {
        color: '#eee'
      }
    },
    axisLabel: {
      color: '#666'
    }
  },
  series: [{
    name: '事故数量',
    type: 'line',
    smooth: true,
    data: trendData.value.values,
    areaStyle: {
      color: {
        type: 'linear',
        x: 0,
        y: 0,
        x2: 0,
        y2: 1,
        colorStops: [
          { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
          { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
        ]
      }
    },
    lineStyle: {
      color: '#409eff',
      width: 2
    },
    itemStyle: {
      color: '#409eff'
    }
  }]
}))

const trafficFlowOption = computed(() => ({
  tooltip: {
    trigger: 'axis',
    axisPointer: {
      type: 'shadow'
    }
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    top: '10%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    data: trafficFlowData.value.labels,
    axisLine: {
      lineStyle: {
        color: '#ddd'
      }
    },
    axisLabel: {
      color: '#666',
      rotate: 45
    }
  },
  yAxis: {
    type: 'value',
    name: '车辆数',
    axisLine: {
      show: false
    },
    axisTick: {
      show: false
    },
    splitLine: {
      lineStyle: {
        color: '#eee'
      }
    },
    axisLabel: {
      color: '#666'
    }
  },
  series: [{
    name: '车流量',
    type: 'bar',
    data: trafficFlowData.value.values,
    itemStyle: {
      color: {
        type: 'linear',
        x: 0,
        y: 0,
        x2: 0,
        y2: 1,
        colorStops: [
          { offset: 0, color: '#67c23a' },
          { offset: 1, color: '#95d475' }
        ]
      },
      borderRadius: [4, 4, 0, 0]
    }
  }]
}))

const severityChartOption = computed(() => ({
  tooltip: {
    trigger: 'item',
    formatter: '{b}: {c} ({d}%)'
  },
  legend: {
    orient: 'vertical',
    right: '5%',
    top: 'center'
  },
  series: [{
    name: '严重程度',
    type: 'pie',
    radius: ['40%', '70%'],
    center: ['35%', '50%'],
    avoidLabelOverlap: false,
    itemStyle: {
      borderRadius: 10,
      borderColor: '#fff',
      borderWidth: 2
    },
    label: {
      show: false,
      position: 'center'
    },
    emphasis: {
      label: {
        show: true,
        fontSize: 16,
        fontWeight: 'bold'
      }
    },
    labelLine: {
      show: false
    },
    data: severityData.value.map((item, index) => ({
      ...item,
      itemStyle: {
        color: ['#e6a23c', '#f56c6c', '#c00'][index] || '#909399'
      }
    }))
  }]
}))

const accidentTypeOption = computed(() => ({
  tooltip: {
    trigger: 'item',
    formatter: '{b}: {c} ({d}%)'
  },
  legend: {
    orient: 'vertical',
    right: '5%',
    top: 'center'
  },
  series: [{
    name: '事故类型',
    type: 'pie',
    radius: ['40%', '70%'],
    center: ['35%', '50%'],
    avoidLabelOverlap: false,
    itemStyle: {
      borderRadius: 10,
      borderColor: '#fff',
      borderWidth: 2
    },
    label: {
      show: false,
      position: 'center'
    },
    emphasis: {
      label: {
        show: true,
        fontSize: 16,
        fontWeight: 'bold'
      }
    },
    labelLine: {
      show: false
    },
    data: accidentTypeData.value.map((item, index) => ({
      ...item,
      itemStyle: {
        color: ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399', '#b37feb'][index] || '#909399'
      }
    }))
  }]
}))

const vehicleTypeOption = computed(() => ({
  tooltip: {
    trigger: 'item',
    formatter: '{b}: {c} ({d}%)'
  },
  legend: {
    orient: 'vertical',
    right: '5%',
    top: 'center'
  },
  series: [{
    name: '车辆类型',
    type: 'pie',
    radius: ['40%', '70%'],
    center: ['35%', '50%'],
    avoidLabelOverlap: false,
    itemStyle: {
      borderRadius: 10,
      borderColor: '#fff',
      borderWidth: 2
    },
    label: {
      show: false,
      position: 'center'
    },
    emphasis: {
      label: {
        show: true,
        fontSize: 16,
        fontWeight: 'bold'
      }
    },
    labelLine: {
      show: false
    },
    data: vehicleTypeData.value.map((item, index) => ({
      ...item,
      itemStyle: {
        color: ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#b37feb'][index] || '#909399'
      }
    }))
  }]
}))

const initMap = async () => {
  try {
    AMap = await AMapLoader.load({
      key: AMAP_KEY,
      version: '2.0',
      plugins: ['AMap.Marker', 'AMap.InfoWindow', 'AMap.Geocoder']
    })
    
    map = new AMap.Map(mapContainer.value, {
      zoom: 13,
      center: [116.4074, 39.9042],
      mapStyle: 'amap://styles/normal',
      viewMode: '2D'
    })
    
    map.on('complete', () => {
      console.log('地图加载完成')
      updateCameraMarkers()
    })
    
  } catch (error) {
    console.error('高德地图加载失败:', error)
  }
}

const updateCameraMarkers = () => {
  if (!map || !AMap) return
  
  Object.values(cameraMarkers).forEach(marker => {
    map.remove(marker)
  })
  
  cameras.value.forEach(cam => {
    const lat = cam.location_lat || 39.9042
    const lng = cam.location_lng || 116.4074
    
    const markerContent = document.createElement('div')
    markerContent.className = 'custom-marker camera-marker ' + cam.status
    markerContent.innerHTML = `<span style="font-size:10px;">${cam.name.slice(0,2)}</span>`
    
    const marker = new AMap.Marker({
      position: [lng, lat],
      content: markerContent,
      offset: new AMap.Pixel(-16, -16)
    })
    
    marker.on('click', () => {
      const infoContent = `
        <div class="info-window">
          <strong>${cam.name}</strong>
          <p>编号: ${cam.camera_code}</p>
          <p>状态: <span style="color:${cam.status === 'online' ? '#67c23a' : '#909399'}">${cam.status === 'online' ? '在线' : '离线'}</span></p>
          <p>位置: ${cam.location_desc || '未设置'}</p>
        </div>
      `
      
      const infoWindow = new AMap.InfoWindow({
        content: infoContent,
        offset: new AMap.Pixel(0, -30)
      })
      infoWindow.open(map, marker.getPosition())
    })
    
    map.add(marker)
    cameraMarkers[cam.id] = marker
  })
}

const updateAccidentMarkers = () => {
  if (!map || !AMap) return
  
  accidentMarkers.forEach(marker => {
    map.remove(marker)
  })
  accidentMarkers.length = 0
  
  alertHistory.value.forEach(alert => {
    const lat = alert.geo_lat || 39.9042
    const lng = alert.geo_lng || 116.4074
    
    const markerContent = document.createElement('div')
    markerContent.className = 'custom-marker accident-marker ' + alert.severity
    markerContent.innerHTML = '<span>!</span>'
    
    const marker = new AMap.Marker({
      position: [lng, lat],
      content: markerContent,
      offset: new AMap.Pixel(-18, -18)
    })
    
    marker.on('click', () => {
      const infoContent = `
        <div class="info-window accident">
          <strong style="color:#f56c6c;">${getSeverityText(alert.severity)}事故</strong>
          <p>摄像头: ${alert.camera_name}</p>
          <p>时间: ${alert.trigger_time}</p>
          <p>评分: ${alert.score_total}</p>
        </div>
      `
      
      const infoWindow = new AMap.InfoWindow({
        content: infoContent,
        offset: new AMap.Pixel(0, -30)
      })
      infoWindow.open(map, marker.getPosition())
    })
    
    map.add(marker)
    accidentMarkers.push(marker)
  })
}

watch(cameras, () => {
  updateCameraMarkers()
}, { deep: true })

watch(alertHistory, () => {
  updateAccidentMarkers()
}, { deep: true })

const fetchTrendData = async () => {
  try {
    const res = await getTrend(trendDays.value)
    if (res.code === 200) {
      trendData.value = res.data
    }
  } catch (error) {
    console.error('获取事故趋势数据失败:', error)
    trendData.value = { labels: [], values: [] }
  }
}

const fetchSeverityData = async () => {
  try {
    const res = await getSeverity()
    if (res.code === 200) {
      severityData.value = res.data
    }
  } catch (error) {
    console.error('获取事故严重程度数据失败:', error)
    severityData.value = []
  }
}

const fetchAccidentTypeData = async () => {
  try {
    const res = await getAccidentTypes()
    if (res.code === 200) {
      accidentTypeData.value = res.data
    }
  } catch (error) {
    console.error('获取事故类型数据失败:', error)
    accidentTypeData.value = []
  }
}

const fetchTrafficFlow = async () => {
  try {
    const res = await getTrafficFlow(flowHours.value)
    if (res.code === 200) {
      trafficFlowData.value = res.data
    }
  } catch (error) {
    console.error('获取车辆流量数据失败:', error)
    trafficFlowData.value = { labels: [], values: [] }
  }
}

const fetchVehicleTypeData = async () => {
  try {
    const res = await getVehicleTypes()
    if (res.code === 200) {
      vehicleTypeData.value = res.data
    }
  } catch (error) {
    console.error('获取车辆类型数据失败:', error)
    vehicleTypeData.value = []
  }
}

const fetchData = async () => {
  try {
    const [camerasRes, overviewRes] = await Promise.all([
      getCameras(),
      getOverview()
    ])
    
    if (camerasRes.code === 200) {
      cameras.value = camerasRes.data
      if (camerasRes.data.length > 0) {
        const firstOnline = camerasRes.data.find(c => c.status === 'online')
        if (firstOnline) {
          selectedCamera.value = firstOnline.id
        }
      }
    }
    
    if (overviewRes.code === 200) {
      overview.value = overviewRes.data
    }
  } catch (error) {
    console.error(error)
  }
}

const fetchAllChartData = async () => {
  await Promise.all([
    fetchTrendData(),
    fetchSeverityData(),
    fetchAccidentTypeData(),
    fetchTrafficFlow(),
    fetchVehicleTypeData()
  ])
}

onMounted(async () => {
  await fetchData()
  await fetchAllChartData()
  await nextTick()
  initMap()
})

onUnmounted(() => {
  if (map) {
    map.destroy()
  }
})
</script>

<style scoped lang="scss">
.dashboard {
  height: calc(100vh - 100px);
  display: flex;
  flex-direction: column;
  gap: 20px;
  overflow-y: auto;
}

.dashboard-top {
  height: 45%;
  min-height: 400px;
  display: flex;
  gap: 20px;
}

.video-section,
.map-section {
  flex: 1;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.section-header {
  padding: 12px 16px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.video-container,
.map-container {
  flex: 1;
  min-height: 300px;
  position: relative;
}

.video-stream {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: #000;
}

.no-video {
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: #999;
  
  .hint {
    font-size: 12px;
    margin-top: 10px;
  }
}

.dashboard-bottom {
  display: flex;
  gap: 20px;
}

.stats-section {
  flex: 1;
  display: flex;
  gap: 16px;
}

.stat-card {
  flex: 1;
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 50px;
  height: 50px;
  border-radius: 8px;
  display: flex;
  justify-content: center;
  align-items: center;
  color: #fff;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #333;
}

.stat-label {
  font-size: 14px;
  color: #999;
  margin-top: 4px;
}

.alerts-section {
  width: 350px;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
}

.alerts-list {
  padding: 12px;
  max-height: 150px;
  overflow-y: auto;
}

.alert-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
  border-radius: 6px;
  margin-bottom: 8px;
  background: #f9f9f9;
  
  &:last-child {
    margin-bottom: 0;
  }
  
  &.normal .alert-dot {
    background: #e6a23c;
  }
  
  &.serious .alert-dot {
    background: #f56c6c;
  }
  
  &.critical .alert-dot {
    background: #c00;
    animation: pulse 1s infinite;
  }
}

.alert-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.alert-info {
  flex: 1;
}

.alert-title {
  font-size: 14px;
  color: #333;
}

.alert-time {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

.no-alerts {
  text-align: center;
  color: #999;
  padding: 20px;
}

.dashboard-charts {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-height: 0;
}

.chart-row {
  display: flex;
  gap: 20px;
  flex: 1;
}

.chart-card {
  flex: 1;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.chart-container {
  flex: 1;
  min-height: 220px;
  padding: 12px;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}
</style>

<style>
.custom-marker {
  display: flex;
  justify-content: center;
  align-items: center;
  border-radius: 50%;
  font-size: 12px;
  font-weight: bold;
  color: #fff;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
}

.camera-marker {
  width: 32px;
  height: 32px;
  background: #409eff;
  cursor: pointer;
}

.camera-marker.online {
  background: #67c23a;
}

.camera-marker.offline {
  background: #909399;
}

.accident-marker {
  width: 36px;
  height: 36px;
  background: #f56c6c;
  animation: marker-pulse 1.5s infinite;
  cursor: pointer;
}

.accident-marker.serious {
  background: #e6a23c;
}

.accident-marker.critical {
  background: #f56c6c;
}

@keyframes marker-pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.2);
  }
}

.info-window {
  padding: 10px;
  min-width: 150px;
}

.info-window strong {
  font-size: 14px;
  color: #333;
  display: block;
  margin-bottom: 8px;
}

.info-window p {
  margin: 4px 0;
  font-size: 12px;
  color: #666;
}

.info-window.accident strong {
  color: #f56c6c;
}
</style>
