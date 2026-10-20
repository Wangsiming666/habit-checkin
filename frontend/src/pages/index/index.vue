<template>
  <view class="page">
    <view class="header">
      <view>
        <view class="title">我的打卡</view>
        <view class="date" v-if="serverDate">北京时间 {{ serverDate }}</view>
      </view>
      <text class="logout" @click="handleLogout">退出</text>
    </view>

    <view v-if="loading" class="empty">加载中…</view>
    <view v-else-if="items.length === 0" class="empty">
      <view class="empty-title">还没有打卡项</view>
      <view class="empty-sub">新建一个，今天就开始第一格</view>
    </view>

    <view v-else class="ledger">
      <view class="row" v-for="item in items" :key="item.id">
        <view class="row-main">
          <view class="name">{{ item.item_name }}</view>
          <view class="meta">
            连续
            <text class="streak-num">{{ item.current_streak }}</text>
            天 · 最高 {{ item.max_streak }} 天
          </view>
        </view>
        <button
          class="check"
          :class="{ done: item.today_checked }"
          :disabled="item.today_checked || checkingId === item.id"
          @click="handleCheck(item)"
        >
          {{ item.today_checked ? '已打卡' : checkingId === item.id ? '打卡中…' : '打卡' }}
        </button>
      </view>
    </view>

    <view class="actions">
      <button class="primary" @click="goAdd">新建打卡项</button>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { http, clearToken } from '../../api/request.js'

const items = ref([])
const serverDate = ref('')
const loading = ref(false)
const checkingId = ref(0)

onShow(loadItems)

async function loadItems() {
  loading.value = true
  try {
    const data = await http.get('/api/items')
    items.value = data.items || []
    serverDate.value = data.server_date || ''
  } catch (e) {
    // 统一错误提示已在 request.js 处理
  } finally {
    loading.value = false
  }
}

async function handleCheck(item) {
  if (item.today_checked || checkingId.value) return
  checkingId.value = item.id
  try {
    const data = await http.post('/api/check/' + item.id)
    // 以服务端返回更新卡片，禁止本地 +1 推算
    item.today_checked = data.today_checked
    item.current_streak = data.current_streak
    item.max_streak = data.max_streak
    uni.showToast({ title: '打卡成功', icon: 'success' })
  } catch (e) {
    // 409（并发/重复）时刷新，保证界面与数据库一致
    if (e && e.code === 409) await loadItems()
  } finally {
    checkingId.value = 0
  }
}

function goAdd() {
  uni.navigateTo({ url: '/pages/add/index' })
}

async function handleLogout() {
  try {
    await http.post('/api/auth/logout')
  } catch (e) {
    // 网络失败也允许本地退出
  }
  clearToken()
  uni.reLaunch({ url: '/pages/login/index' })
}
</script>

<style>
.page {
  min-height: 100vh;
  padding: 48rpx 40rpx 120rpx;
  box-sizing: border-box;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding-bottom: 36rpx;
  border-bottom: 2rpx solid #1b1d1a;
}
.title {
  font-size: 48rpx;
  font-weight: 700;
  letter-spacing: 2rpx;
}
.date {
  margin-top: 12rpx;
  font-size: 24rpx;
  color: #8b8e84;
}
.logout {
  font-size: 26rpx;
  color: #6f7269;
  padding: 8rpx 0 8rpx 24rpx;
}
.empty {
  padding: 160rpx 0;
  text-align: center;
  color: #8b8e84;
}
.empty-title {
  font-size: 34rpx;
  color: #1b1d1a;
  margin-bottom: 16rpx;
}
.empty-sub {
  font-size: 26rpx;
}
.ledger {
  margin-top: 8rpx;
}
.row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 36rpx 0;
  border-bottom: 2rpx solid #e3e2da;
}
.row-main {
  flex: 1;
  min-width: 0;
}
.name {
  font-size: 34rpx;
  font-weight: 600;
}
.meta {
  margin-top: 10rpx;
  font-size: 26rpx;
  color: #6f7269;
}
.streak-num {
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 40rpx;
  color: #b4552d;
  font-weight: 700;
  padding: 0 6rpx;
}
.check {
  margin: 0 0 0 24rpx;
  min-width: 152rpx;
  height: 68rpx;
  line-height: 68rpx;
  font-size: 26rpx;
  text-align: center;
  background: #2f5d50;
  color: #fafaf7;
  border-radius: 6rpx;
  padding: 0 20rpx;
}
.check.done {
  background: transparent;
  color: #8b8e84;
  border: 2rpx solid #d9d8cf;
}
.actions {
  position: fixed;
  left: 40rpx;
  right: 40rpx;
  bottom: 48rpx;
}
.primary {
  height: 96rpx;
  line-height: 96rpx;
  background: #1b1d1a;
  color: #fafaf7;
  font-size: 30rpx;
  border-radius: 8rpx;
}
</style>
