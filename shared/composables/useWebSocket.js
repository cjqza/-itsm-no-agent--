/**
 * WebSocket composable with heartbeat and exponential backoff reconnect.
 *
 * Usage in components:
 *   const { connect, disconnect } = useWebSocket({ onMessage: (data) => { ... } })
 *   connect('/api/chat/ws/123')
 *   onUnmounted(disconnect)
 *
 * Usage in stores:
 *   const { connect, disconnect } = useWebSocket({ onMessage: ... })
 *   // call disconnect() manually in logout()
 */
export function useWebSocket({ onMessage, maxReconnect = 10 } = {}) {
  let ws = null
  let heartbeatTimer = null
  let reconnectTimer = null
  let reconnectAttempts = 0
  let manualClose = false
  let currentPath = ''

  function clearTimers() {
    if (heartbeatTimer) { clearInterval(heartbeatTimer); heartbeatTimer = null }
    if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null }
  }

  function connect(path) {
    const token = localStorage.getItem('token')
    if (!token) return

    currentPath = path
    manualClose = false
    clearTimers()

    if (ws) {
      try { ws.onclose = null; ws.close() } catch (e) {}
      ws = null
    }

    try {
      const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
      const url = `${protocol}//${location.host}${path}?token=${token}`
      ws = new WebSocket(url)

      ws.onopen = () => {
        reconnectAttempts = 0
        if (heartbeatTimer) clearInterval(heartbeatTimer)
        heartbeatTimer = setInterval(() => {
          if (ws?.readyState === WebSocket.OPEN) {
            ws.send('ping')
          }
        }, 30000)
      }

      ws.onmessage = (event) => {
        if (event.data === 'pong') return
        try {
          const data = JSON.parse(event.data)
          if (onMessage) onMessage(data)
        } catch (e) { /* silent - WS message parse failure */ }
      }

      ws.onclose = () => {
        if (heartbeatTimer) { clearInterval(heartbeatTimer); heartbeatTimer = null }
        if (manualClose) return
        if (reconnectAttempts < maxReconnect) {
          const delay = Math.min(3000 * Math.pow(2, reconnectAttempts), 30000)
          reconnectAttempts++
          if (reconnectTimer) clearTimeout(reconnectTimer)
          reconnectTimer = setTimeout(() => connect(currentPath), delay)
        }
      }
    } catch (e) { console.error('WebSocket连接失败', e) }
  }

  function disconnect() {
    manualClose = true
    reconnectAttempts = 0
    clearTimers()
    if (ws) {
      try { ws.onclose = null; ws.close() } catch (e) {}
      ws = null
    }
  }

  return { connect, disconnect }
}
