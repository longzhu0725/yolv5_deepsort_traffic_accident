<template>
  <div class="accident-list">
    <div class="page-header">
      <h2>事故管理</h2>
    </div>
    
    <div class="filter-bar">
      <el-date-picker
        v-model="dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        format="YYYY-MM-DD"
        value-format="YYYY-MM-DD"
        style="width: 260px"
      />
      
      <el-select v-model="filters.severity" placeholder="严重程度" clearable style="width: 120px">
        <el-option label="一般" value="normal" />
        <el-option label="较重" value="serious" />
        <el-option label="严重" value="critical" />
      </el-select>
      
      <el-select v-model="filters.status" placeholder="状态" clearable style="width: 120px">
        <el-option label="待处理" value="pending" />
        <el-option label="已确认" value="acknowledged" />
        <el-option label="已解决" value="resolved" />
        <el-option label="已关闭" value="closed" />
      </el-select>
      
      <el-select v-model="filters.camera_id" placeholder="摄像头" clearable style="width: 150px">
        <el-option
          v-for="cam in cameras"
          :key="cam.id"
          :label="cam.name"
          :value="cam.id"
        />
      </el-select>
      
      <el-button type="primary" @click="handleSearch">查询</el-button>
      <el-button @click="handleReset">重置</el-button>
    </div>
    
    <el-table :data="accidents" v-loading="loading" stripe>
      <el-table-column prop="accident_no" label="事故编号" width="160" />
      <el-table-column prop="trigger_time" label="触发时间" width="180" />
      <el-table-column prop="camera_name" label="摄像头" width="120" />
      <el-table-column prop="accident_type_desc" label="事故类型" width="100">
        <template #default="{ row }">
          {{ row.accident_type_desc || '交通事故' }}
        </template>
      </el-table-column>
      <el-table-column prop="severity" label="严重程度" width="100">
        <template #default="{ row }">
          <el-tag :type="getSeverityType(row.severity)" size="small">
            {{ row.severity_desc || getSeverityText(row.severity) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="score_total" label="评分" width="80">
        <template #default="{ row }">
          {{ row.score_total?.toFixed(3) }}
        </template>
      </el-table-column>
      <el-table-column prop="involved_count" label="涉事目标" width="80" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)" size="small">
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link @click="viewDetail(row.id)">
            查看
          </el-button>
          <el-button type="primary" link @click="handleEdit(row)">
            编辑
          </el-button>
          <el-button type="danger" link @click="handleDelete(row)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <div class="pagination">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.per_page"
        :total="pagination.total"
        :page-sizes="[10, 15, 20, 50]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="fetchAccidents"
        @current-change="fetchAccidents"
      />
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
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getAccidents, updateAccident, deleteAccident } from '@/api/accident'
import { getCameras } from '@/api/camera'

const router = useRouter()

const loading = ref(false)
const accidents = ref([])
const cameras = ref([])
const dateRange = ref([])

const editDialogVisible = ref(false)
const editLoading = ref(false)
const editForm = reactive({
  id: null,
  accident_type: '',
  severity: '',
  status: '',
  address: ''
})

const filters = reactive({
  severity: '',
  status: '',
  camera_id: null
})

const pagination = reactive({
  page: 1,
  per_page: 15,
  total: 0
})

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

const fetchAccidents = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      per_page: pagination.per_page
    }
    
    if (filters.severity) params.severity = filters.severity
    if (filters.status) params.status = filters.status
    if (filters.camera_id) params.camera_id = filters.camera_id
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_time = dateRange.value[0]
      params.end_time = dateRange.value[1]
    }
    
    const res = await getAccidents(params)
    if (res.code === 200) {
      accidents.value = res.data.items
      pagination.total = res.data.total
    }
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const fetchCameras = async () => {
  try {
    const res = await getCameras()
    if (res.code === 200) {
      cameras.value = res.data
    }
  } catch (error) {
    console.error(error)
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchAccidents()
}

const handleReset = () => {
  filters.severity = ''
  filters.status = ''
  filters.camera_id = null
  dateRange.value = []
  pagination.page = 1
  fetchAccidents()
}

const viewDetail = (id) => {
  router.push(`/accidents/${id}`)
}

const handleEdit = (row) => {
  editForm.id = row.id
  editForm.accident_type = row.accident_type || 'unknown'
  editForm.severity = row.severity || 'normal'
  editForm.status = row.status || 'pending'
  editForm.address = row.address || ''
  editDialogVisible.value = true
}

const submitEdit = async () => {
  editLoading.value = true
  try {
    const res = await updateAccident(editForm.id, {
      accident_type: editForm.accident_type,
      severity: editForm.severity,
      status: editForm.status,
      address: editForm.address
    })
    if (res.code === 200) {
      ElMessage.success('更新成功')
      editDialogVisible.value = false
      fetchAccidents()
    }
  } catch (error) {
    console.error(error)
  } finally {
    editLoading.value = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除事故记录 "${row.accident_no}" 吗？删除后将无法恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const res = await deleteAccident(row.id)
    if (res.code === 200) {
      ElMessage.success('删除成功')
      fetchAccidents()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
    }
  }
}

onMounted(() => {
  fetchCameras()
  fetchAccidents()
})
</script>

<style scoped lang="scss">
.accident-list {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
}

.page-header {
  margin-bottom: 20px;
  
  h2 {
    font-size: 18px;
    color: #333;
  }
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
