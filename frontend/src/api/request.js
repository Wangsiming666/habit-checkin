import { BASE_URL } from '../env.js'

const TOKEN_KEY = 'habit_token'

export function getToken() {
  return uni.getStorageSync(TOKEN_KEY) || ''
}

export function setToken(token) {
  uni.setStorageSync(TOKEN_KEY, token)
}

export function clearToken() {
  uni.removeStorageSync(TOKEN_KEY)
}

/**
 * 统一请求封装：
 * - 自动带 Bearer token；
 * - HTTP 401 或 body.code===401：清 token 并 reLaunch 登录页；
 * - 非 200：统一 toast 后端 msg，并把 body reject 给业务层；
 * - 业务层只拿到 data，不感知外层结构。
 */
export function request(options) {
  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE_URL + options.url,
      method: options.method || 'GET',
      data: options.data || {},
      timeout: 15000,
      header: {
        'Content-Type': 'application/json',
        ...(getToken() ? { Authorization: 'Bearer ' + getToken() } : {}),
        ...(options.header || {}),
      },
      success: (res) => {
        const body = res.data || {}
        if (res.statusCode === 401 || body.code === 401) {
          clearToken()
          uni.reLaunch({ url: '/pages/login/index' })
          reject(body)
          return
        }
        if (res.statusCode === 200 && body.code === 200) {
          resolve(body.data)
          return
        }
        uni.showToast({ title: body.msg || '请求失败', icon: 'none' })
        reject(body)
      },
      fail: (err) => {
        uni.showToast({ title: '网络异常，请检查后端服务', icon: 'none' })
        reject(err)
      },
    })
  })
}

export const http = {
  get: (url) => request({ url, method: 'GET' }),
  post: (url, data) => request({ url, method: 'POST', data }),
}
