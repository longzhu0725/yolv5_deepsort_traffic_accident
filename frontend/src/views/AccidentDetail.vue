<template>
  <div class="accident-detail" v-loading="loading">
    <div class="page-header">
      <el-button link @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
      <span class="title">事故详情: {{ accident?.accident_no }}</span>
      <el-tag :type="getStatusType(accident?.status)" size="large">
        {{ getStatusText(accident?.status) }}
      </el-tag>
    </div>
    
    <div class="detail-content" v-if="accident">
      <div class="left-section">
        <div class="snapshot-section">
          <div class="section-title">事故截图</div>
          <div class="snapshot-container">
            <img :src="accident.snapshot_url" alt="事故截图" v-if="accident.snapshot_url" />
            <div class="no-snapshot" v-else>
              <el-icon :size="40"><Picture /></el-icon>
              <span>暂无截图</span>
            </div>
          </div>
        </div>
        
        <div class="map-section">
          <div class="section-title">事故位置</div>
          <div class="map-container" ref="mapContainer" v-if="accident?.geo_lat && accident?.geo_lng"></div>
          <div class="no-location" v-else>
            <el-icon :size="40"><Location /></el-icon>
            <span>暂无位置信息</span>
            <span class="hint">请为摄像头配置地理位置或进行标定</span>
          </div>
        </div>
      </div>
      
      <div class="right-section">
        <div class="info-section">
          <div class="section-title">基本信息</div>
          <div class="info-list">
            <div class="info-item">
              <span class="label">事故编号:</span>
              <span class="value">{{ accident.accident_no }}</span>
            </div>
            <div class="info-item">
              <span class="label">事故类型:</span>
              <span class="value">
                <el-tag type="danger" size="small">{{ accident.accident_type_desc || '交通事故' }}</el-tag>
              </span>
            </div>
            <div class="info-item">
              <span class="label">严重程度:</span>
              <span class="value">
                <el-tag :type="getSeverityType(accident.severity)" size="small">
                  {{ accident.severity_desc || getSeverityText(accident.severity) }}
                </el-tag>
              </span>
            </div>
            <div class="info-item">
              <span class="label">触发时间:</span>
              <span class="value">{{ accident.trigger_time }}</span>
            </div>
            <div class="info-item">
              <span class="label">摄像头:</span>
              <span class="value">{{ accident.camera_name }}</span>
            </div>
            <div class="info-item">
              <span class="label">地址:</span>
              <span class="value">{{ accident.address || '暂无位置信息' }}</span>
            </div>
            <div class="info-item">
              <span class="label">涉事目标:</span>
              <span class="value">{{ accident.involved_count }}个</span>
            </div>
          </div>
        </div>
        
        <div class="score-section">
          <div class="section-title">检测评分</div>
          <div class="score-list">
            <div class="score-item">
              <span class="label">综合评分</span>
              <el-progress
                :percentage="Math.round(accident.score_total * 100)"
                :stroke-width="12"
                :color="getScoreColor(accident.score_total)"
              />
              <span class="value">{{ accident.score_total?.toFixed(3) }}</span>
            </div>
            <div class="score-item">
              <span class="label">碰撞得分</span>
              <el-progress
                :percentage="Math.round(accident.score_collision * 100)"
                :stroke-width="12"
                color="#409eff"
              />
              <span class="value">{{ accident.score_collision?.toFixed(3) }}</span>
            </div>
            <div class="score-item">
              <span class="label">速度得分</span>
              <el-progress
                :percentage="Math.round(accident.score_speed * 100)"
                :stroke-width="12"
                color="#67c23a"
              />
              <span class="value">{{ accident.score_speed?.toFixed(3) }}</span>
            </div>
          </div>
        </div>
        
        <div class="action-section">
          <div class="section-title">状态操作</div>
          <div class="current-status">
            当前状态: <el-tag :type="getStatusType(accident.status)">{{ getStatusText(accident.status) }}</el-tag>
          </div>
          <div class="action-buttons">
            <el-button
              v-if="accident.status === 'pending'"
              type="primary"
              @click="updateStatus('acknowledged')"
            >
              确认事故
            </el-button>
            <el-button
              v-if="accident.status === 'acknowledged'"
              type="success"
              @click="updateStatus('resolved')"
            >
              标记已解决
            </el-button>
            <el-button
              v-if="accident.status === 'resolved'"
              type="info"
              @click="updateStatus('closed')"
            >
              关闭
            </el-button>
            <el-button type="warning" @click="handleEdit">
              编辑信息
            </el-button>
            <el-button type="danger" @click="handleDelete">
              删除
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <el-dialog v-model="editDialogVisible" title="编辑事故信息" width="500px">
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="事故类型">
          <el-select v-model="editForm.accident_type" placeholder="请选择事故类型">
            <el-option label="车辆碰撞" value="collision" />
            <el-option label="追尾事故" value="rear_end" />
            <el-option label="侧面碰撞" value="side_impact" />
            <el-option label="翻车事故" value="rollover" />
            <el-option label="多车事故" value="multi_vehicle" />
            <el-option label="交通事故" value="unknown" />
          </el-select>
        </el-form-item>
        <el-form-item label="严重程度">
          <el-select v-model="editForm.severity" placeholder="请选择严重程度">
            <el-option label="一般事故" value="normal" />
            <el-option label="严重事故" value="serious" />
            <el-option label="重大事故" value="critical" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="editForm.status" placeholder="请选择状态">
            <el-option label="待处理" value="pending" />
            <el-option label="已确认" value="acknowledged" />
            <el-option label="已解决" value="resolved" />
            <el-option label="已关闭" value="closed" />
          </el-select>
        </el-form-item>
        <el-form-item label="地址">
          <el-input v-model="editForm.address" placeholder="请输入地址" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitEdit" :loading="editLoading">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import AMapLoader from '@amap/amap-jsapi-loader'
import { getAccident, updateAccident, deleteAccident } from '@/api/accident'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const accident = ref(null)
const mapContainer = ref(null)
let map = null
let AMap = null

const editDialogVisible = ref(false)
const editLoading = ref(false)
const editForm = reactive({
  accident_type: '',
  severity: '',
  status: '',
  address: ''
})

const AMAP_KEY = ''
const AMAP_SECRET = ''

window._AMapSecurityConfig = {
  securityJsCode: AMAP_SECRET,
}

const getStatusType = (status) => {
  const map = {
    pending: 'danger',
    acknowledged: 'warning',
    resolved: 'success',
    closed: 'info'
  }
  return map[status] || 'info'
}

const getStatusText = (status) => {
  const map = {
    pending: '待处理',
    acknowledged: '已确认',
    resolved: '已解决',
    closed: '已关闭'
  }
  return map[status] || status
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
    normal: '一般事故',
    serious: '严重事故',
    critical: '重大事故'
  }
  return map[severity] || severity
}

const getScoreColor = (score) => {
  if (score >= 0.9) return '#f56c6c'
  if (score >= 0.75) return '#e6a23c'
  return '#67c23a'
}

const initMap = async () => {
  if (!accident.value?.geo_lat || !accident.value?.geo_lng) return
  
  try {
    AMap = await AMapLoader.load({
      key: AMAP_KEY,
      version: '2.0',
      plugins: ['AMap.Marker', 'AMap.InfoWindow']
    })
    
    map = new AMap.Map(mapContainer.value, {
      zoom: 15,
      center: [accident.value.geo_lng, accident.value.geo_lat],
      mapStyle: 'amap://styles/normal'
    })
    
    const marker = new AMap.Marker({
      position: [accident.value.geo_lng, accident.value.geo_lat],
      content: `<div class="custom-marker accident-marker ${accident.value.severity}"><span>!</span></div>`
    })
    
    map.add(marker)
  } catch (error) {
    console.error('高德地图加载失败:', error)
  }
}

const fetchAccident = async () => {
  loading.value = true
  try {
    const res = await getAccident(route.params.id)
    if (res.code === 200) {
      accident.value = res.data
      await nextTick()
      initMap()
    }
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const updateStatus = async (status) => {
  try {
    const res = await updateAccident(route.params.id, { status })
    if (res.code === 200) {
      ElMessage.success('状态更新成功')
      fetchAccident()
    }
  } catch (error) {
    console.error(error)
  }
}

const handleEdit = () => {
  editForm.accident_type = accident.value.accident_type || 'unknown'
  editForm.severity = accident.value.severity || 'normal'
  editForm.status = accident.value.status || 'pending'
  editForm.address = accident.value.address || ''
  editDialogVisible.value = true
}

const submitEdit = async () => {
  editLoading.value = true
  try {
    const res = await updateAccident(route.params.id, {
      accident_type: editForm.accident_type,
      severity: editForm.severity,
      status: editForm.status,
      address: editForm.address
    })
    if (res.code === 200) {
      ElMessage.success('更新成功')
      editDialogVisible.value = false
      fetchAccident()
    }
  } catch (error) {
    console.error(error)
  } finally {
    editLoading.value = false
  }
}

const handleDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除事故记录 "${accident.value.accident_no}" 吗？删除后将无法恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const res = await deleteAccident(route.params.id)
    if (res.code === 200) {
      ElMessage.success('删除成功')
      router.push('/accidents')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
    }
  }
}

const goBack = () => {
  router.push('/accidents')
}

onMounted(() => {
  fetchAccident()
})

onUnmounted(() => {
  if (map) {
    map.destroy()
  }
})
</script>

<style scoped lang="scss">
.accident-detail {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  min-height: calc(100vh - 100px);
}

.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #eee;
  
  .title {
    font-size: 18px;
    font-weight: 600;
    flex: 1;
  }
}

.detail-content {
  display: flex;
  gap: 20px;
}

.left-section {
  width: 500px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.right-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 12px;
  padding-left: 10px;
  border-left: 3px solid #409eff;
}

.snapshot-section {
  background: #f9f9f9;
  padding: 16px;
  border-radius: 8px;
}

.snapshot-container {
  height: 280px;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #000;
  border-radius: 4px;
  overflow: hidden;
  
  img {
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
  }
}

.no-snapshot, .no-location {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  color: #999;
  background: #f5f5f5;
  height: 100%;
  justify-content: center;
  
  .hint {
    font-size: 12px;
    color: #bbb;
  }
}

.map-section {
  background: #f9f9f9;
  padding: 16px;
  border-radius: 8px;
}

.map-container {
  height: 200px;
  border-radius: 4px;
  overflow: hidden;
}

.info-section,
.score-section,
.action-section {
  background: #f9f9f9;
  padding: 16px;
  border-radius: 8px;
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-item {
  display: flex;
  
  .label {
    width: 80px;
    color: #666;
  }
  
  .value {
    flex: 1;
    color: #333;
  }
}

.score-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.score-item {
  .label {
    display: block;
    margin-bottom: 8px;
    color: #666;
  }
  
  .value {
    display: block;
    text-align: right;
    margin-top: 4px;
    font-size: 14px;
    color: #333;
  }
}

.current-status {
  margin-bottom: 16px;
  color: #666;
}

.action-buttons {
  display: flex;
  gap: 12px;
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

.accident-marker {
  width: 36px;
  height: 36px;
  background: #f56c6c;
  animation: marker-pulse 1.5s infinite;
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
</style>
