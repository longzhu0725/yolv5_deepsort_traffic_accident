<template>
  <div class="camera-manage">
    <div class="page-header">
      <h2>摄像头管理</h2>
      <el-button type="primary" @click="showDialog()">
        <el-icon><Plus /></el-icon>
        新增摄像头
      </el-button>
    </div>
    
    <el-table :data="cameras" v-loading="loading" stripe>
      <el-table-column prop="camera_code" label="编号" width="120" />
      <el-table-column prop="name" label="名称" width="150" />
      <el-table-column prop="stream_type" label="类型" width="80">
        <template #default="{ row }">
          {{ row.stream_type === 'file' ? '文件' : '流' }}
        </template>
      </el-table-column>
      <el-table-column prop="location_desc" label="位置描述" width="150" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)" size="small">
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="has_calibration" label="标定" width="80">
        <template #default="{ row }">
          <el-tag :type="row.has_calibration ? 'success' : 'info'" size="small">
            {{ row.has_calibration ? '已标定' : '未标定' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="280" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="row.status !== 'online'"
            type="success"
            size="small"
            @click="handleStart(row.id)"
          >
            启动
          </el-button>
          <el-button
            v-else
            type="warning"
            size="small"
            @click="handleStop(row.id)"
          >
            停止
          </el-button>
          <el-button type="primary" size="small" @click="showDialog(row)">
            编辑
          </el-button>
          <el-button type="danger" size="small" @click="handleDelete(row.id)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑摄像头' : '新增摄像头'"
      width="600px"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入摄像头名称" />
        </el-form-item>
        
        <el-form-item label="编号" prop="camera_code">
          <el-input v-model="form.camera_code" placeholder="请输入摄像头编号" />
        </el-form-item>
        
        <el-form-item label="视频源" prop="stream_url">
          <el-input v-model="form.stream_url" placeholder="请输入视频文件路径或流地址" />
        </el-form-item>
        
        <el-form-item label="类型">
          <el-select v-model="form.stream_type" style="width: 100%">
            <el-option label="文件" value="file" />
            <el-option label="RTSP流" value="rtsp" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="纬度">
          <el-input v-model.number="form.location_lat" placeholder="请输入纬度" />
        </el-form-item>
        
        <el-form-item label="经度">
          <el-input v-model.number="form.location_lng" placeholder="请输入经度" />
        </el-form-item>
        
        <el-form-item label="位置描述">
          <el-input v-model="form.location_desc" placeholder="请输入位置描述" />
        </el-form-item>
        
        <el-form-item label="标定数据">
          <el-input
            v-model="form.homography_data"
            type="textarea"
            :rows="4"
            placeholder='JSON格式: {"src_points":[[x1,y1],...], "dst_points":[[lng1,lat1],...]}'
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getCameras,
  createCamera,
  updateCamera,
  deleteCamera,
  startCamera,
  stopCamera
} from '@/api/camera'

const loading = ref(false)
const cameras = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref(null)
const editId = ref(null)

const form = reactive({
  name: '',
  camera_code: '',
  stream_url: '',
  stream_type: 'file',
  location_lat: null,
  location_lng: null,
  location_desc: '',
  homography_data: ''
})

const rules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  camera_code: [{ required: true, message: '请输入编号', trigger: 'blur' }],
  stream_url: [{ required: true, message: '请输入视频源', trigger: 'blur' }]
}

const getStatusType = (status) => {
  const map = {
    online: 'success',
    offline: 'info',
    error: 'danger'
  }
  return map[status] || 'info'
}

const getStatusText = (status) => {
  const map = {
    online: '在线',
    offline: '离线',
    error: '错误'
  }
  return map[status] || status
}

const fetchCameras = async () => {
  loading.value = true
  try {
    const res = await getCameras()
    if (res.code === 200) {
      cameras.value = res.data
    }
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const showDialog = (camera = null) => {
  isEdit.value = !!camera
  editId.value = camera?.id || null
  
  if (camera) {
    form.name = camera.name
    form.camera_code = camera.camera_code
    form.stream_url = camera.stream_url
    form.stream_type = camera.stream_type
    form.location_lat = camera.location_lat
    form.location_lng = camera.location_lng
    form.location_desc = camera.location_desc || ''
    form.homography_data = camera.homography_data || ''
  } else {
    form.name = ''
    form.camera_code = ''
    form.stream_url = ''
    form.stream_type = 'file'
    form.location_lat = null
    form.location_lng = null
    form.location_desc = ''
    form.homography_data = ''
  }
  
  dialogVisible.value = true
}

const handleSubmit = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  
  submitting.value = true
  try {
    const data = { ...form }
    if (!data.homography_data) {
      delete data.homography_data
    }
    
    let res
    if (isEdit.value) {
      res = await updateCamera(editId.value, data)
    } else {
      res = await createCamera(data)
    }
    
    if (res.code === 200 || res.code === 201) {
      ElMessage.success(isEdit.value ? '更新成功' : '创建成功')
      dialogVisible.value = false
      fetchCameras()
    }
  } catch (error) {
    console.error(error)
  } finally {
    submitting.value = false
  }
}

const handleStart = async (id) => {
  try {
    const res = await startCamera(id)
    if (res.code === 200) {
      ElMessage.success('启动成功')
      fetchCameras()
    } else {
      ElMessage.error(res.message)
    }
  } catch (error) {
    console.error(error)
  }
}

const handleStop = async (id) => {
  try {
    const res = await stopCamera(id)
    if (res.code === 200) {
      ElMessage.success('停止成功')
      fetchCameras()
    }
  } catch (error) {
    console.error(error)
  }
}

const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除该摄像头吗？', '提示', {
      type: 'warning'
    })
    
    const res = await deleteCamera(id)
    if (res.code === 200) {
      ElMessage.success('删除成功')
      fetchCameras()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
    }
  }
}

onMounted(() => {
  fetchCameras()
})
</script>

<style scoped lang="scss">
.camera-manage {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  
  h2 {
    font-size: 18px;
    color: #333;
  }
}
</style>
