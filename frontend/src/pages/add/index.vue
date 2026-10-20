<template>
  <view class="page">
    <view class="title">新建打卡项</view>
    <view class="subtitle">名字短一点，更容易坚持</view>

    <view class="field">
      <input
        v-model="name"
        class="input"
        maxlength="20"
        placeholder="例如：跑步、读书、早睡"
        focus
      />
      <view class="counter">{{ name.length }}/20</view>
    </view>

    <button class="primary" :loading="saving" :disabled="saving" @click="handleSave">
      创建
    </button>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { http } from '../../api/request.js'

const name = ref('')
const saving = ref(false)

async function handleSave() {
  const value = name.value.trim()
  if (!value) {
    uni.showToast({ title: '请输入打卡项名称', icon: 'none' })
    return
  }
  saving.value = true
  try {
    await http.post('/api/items', { item_name: value })
    uni.showToast({ title: '创建成功', icon: 'success' })
    setTimeout(() => uni.navigateBack(), 300)
  } catch (e) {
    // 重名等错误已统一提示
  } finally {
    saving.value = false
  }
}
</script>

<style>
.page {
  min-height: 100vh;
  padding: 72rpx 56rpx;
  box-sizing: border-box;
}
.title {
  font-size: 48rpx;
  font-weight: 700;
}
.subtitle {
  margin-top: 14rpx;
  font-size: 26rpx;
  color: #8b8e84;
}
.field {
  margin-top: 88rpx;
  border-bottom: 2rpx solid #1b1d1a;
  padding-bottom: 12rpx;
}
.input {
  height: 88rpx;
  font-size: 36rpx;
}
.counter {
  text-align: right;
  font-size: 24rpx;
  color: #8b8e84;
}
.primary {
  margin-top: 72rpx;
  height: 96rpx;
  line-height: 96rpx;
  background: #2f5d50;
  color: #fafaf7;
  font-size: 30rpx;
  border-radius: 8rpx;
}
</style>
