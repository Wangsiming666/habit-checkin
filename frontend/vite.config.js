import { defineConfig } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'

// H5 开发服务器默认 5173；后端 CORS 白名单需包含该地址
export default defineConfig({
  plugins: [uni()],
  server: {
    port: 5173,
  },
})
