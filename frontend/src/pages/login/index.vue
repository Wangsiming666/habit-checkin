<template>
  <view class="page">
    <view class="brand">
      <view class="mark"></view>
      <view class="title">习惯打卡</view>
      <view class="subtitle">一天一格，把日子过成连续的</view>
    </view>

    <view class="form">
      <view class="field">
        <text class="label">用户名</text>
        <input v-model="username" class="input" placeholder="请输入用户名" />
      </view>
      <view class="field">
        <text class="label">密码</text>
        <input v-model="password" class="input" password placeholder="请输入密码" />
      </view>
      <button class="primary" :loading="loading" :disabled="loading" @click="handleLogin">
        登录
      </button>
      <view class="hint">演示账号 demo / 123456</view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { http, getToken, setToken } from '../../api/request.js'

const username = ref('demo')
const password = ref('123456')
const loading = ref(false)

onShow(() => {
  if (getToken()) {
    uni.reLaunch({ url: '/pages/index/index' })
  }
})

async function handleLogin() {
  if (!username.value.trim() || !password.value) {
    uni.showToast({ title: '请输入用户名和密码', icon: 'none' })
    return
  }
  loading.value = true
  try {
    const data = await http.post('/api/auth/login', {
      username: username.value.trim(),
      password: password.value,
    })
    setToken(data.token)
    uni.reLaunch({ url: '/pages/index/index' })
  } catch (e) {
    // 错误提示已在 request.js 统一处理
  } finally {
    loading.value = false
  }
}
</script>

<style>
.page {
  min-height: 100vh;
  padding: 120rpx 56rpx 80rpx;
  box-sizing: border-box;
}
.brand {
  margin-bottom: 96rpx;
}
.mark {
  width: 72rpx;
  height: 12rpx;
  background: #2f5d50;
  margin-bottom: 32rpx;
}
.title {
  font-size: 64rpx;
  font-weight: 700;
  letter-spacing: 4rpx;
}
.subtitle {
  margin-top: 20rpx;
  font-size: 28rpx;
  color: #6f7269;
}
.field {
  margin-bottom: 40rpx;
}
.label {
  display: block;
  font-size: 26rpx;
  color: #6f7269;
  margin-bottom: 14rpx;
}
.input {
  height: 96rpx;
  border-bottom: 2rpx solid #d9d8cf;
  font-size: 34rpx;
  padding: 0 4rpx;
}
.primary {
  margin-top: 56rpx;
  height: 96rpx;
  line-height: 96rpx;
  background: #2f5d50;
  color: #fafaf7;
  font-size: 32rpx;
  border-radius: 8rpx;
}
.hint {
  margin-top: 28rpx;
  text-align: center;
  font-size: 24rpx;
  color: #8b8e84;
}
</style>
