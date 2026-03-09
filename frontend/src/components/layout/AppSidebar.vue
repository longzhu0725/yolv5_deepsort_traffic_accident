<template>
  <div class="app-sidebar">
    <el-menu
      :default-active="activeMenu"
      router
      background-color="#304156"
      text-color="#bfcbd9"
      active-text-color="#409eff"
    >
      <el-menu-item index="/dashboard">
        <el-icon><Monitor /></el-icon>
        <span>监控大屏</span>
      </el-menu-item>
      
      <el-menu-item index="/accidents">
        <el-icon><Warning /></el-icon>
        <span>事故管理</span>
      </el-menu-item>
      
      <el-menu-item index="/cameras">
        <el-icon><VideoCamera /></el-icon>
        <span>摄像头管理</span>
      </el-menu-item>
    </el-menu>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const activeMenu = computed(() => {
  if (route.path.startsWith('/accidents')) {
    return '/accidents'
  }
  return route.path
})
</script>

<style scoped lang="scss">
.app-sidebar {
  width: 200px;
  height: 100vh;
  background-color: #304156;
  
  .el-menu {
    border-right: none;
    height: 100%;
  }
}
</style>
