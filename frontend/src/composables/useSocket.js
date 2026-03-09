import { ref, onMounted, onUnmounted } from 'vue'
import { io } from 'socket.io-client'
import { ElNotification } from 'element-plus'

export function useSocket() {
  const socket = ref(null)
  const isConnected = ref(false)
  const latestAlert = ref(null)
  const alertHistory = ref([])

  const connect = () => {
    socket.value = io(window.location.origin, {
      transports: ['websocket']
    })

    socket.value.on('connect', () => {
      isConnected.value = true
      console.log('Socket connected')
    })

    socket.value.on('disconnect', () => {
      isConnected.value = false
      console.log('Socket disconnected')
    })

    socket.value.on('accident_alert', (data) => {
      latestAlert.value = data
      alertHistory.value.unshift(data)
      if (alertHistory.value.length > 20) {
        alertHistory.value.pop()
      }

      const severityMap = {
        normal: { type: 'warning', title: '一般事故' },
        serious: { type: 'error', title: '较重事故' },
        critical: { type: 'error', title: '严重事故' }
      }

      const { type, title } = severityMap[data.severity] || severityMap.normal

      ElNotification({
        title,
        message: `${data.camera_name}: ${data.message}`,
        type,
        duration: 0,
        position: 'top-right'
      })

      try {
        const audio = new Audio('/alert-sound.mp3')
        audio.play()
      } catch (e) {
        console.log('无法播放告警音效')
      }
    })
  }

  const disconnect = () => {
    if (socket.value) {
      socket.value.disconnect()
      socket.value = null
      isConnected.value = false
    }
  }

  onMounted(() => {
    connect()
  })

  onUnmounted(() => {
    disconnect()
  })

  return {
    socket,
    isConnected,
    latestAlert,
    alertHistory
  }
}
