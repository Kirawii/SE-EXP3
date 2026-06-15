<script setup lang="ts">
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { ElMessage } from 'element-plus';

const router = useRouter();
const auth = useAuthStore();

async function onLogout() {
  await auth.logout();
  ElMessage.success('已登出');
  router.push('/login');
}
</script>

<template>
  <header class="app-header">
    <div class="bar">
      <router-link to="/map" class="brand">地标管理原型</router-link>
      <nav class="nav">
        <router-link to="/map">地图</router-link>
        <router-link to="/explore">探索</router-link>
        <router-link v-if="auth.isAuthed" to="/landmarks">我的地标</router-link>
        <router-link v-if="auth.isAuthed" to="/favorites">我的收藏</router-link>
        <router-link v-if="auth.isAdmin" to="/admin">管理后台</router-link>
      </nav>
      <div class="account">
        <template v-if="auth.isAuthed">
          <router-link to="/profile" class="username">
            {{ auth.user?.nickname || auth.user?.username }}
            <el-tag v-if="auth.isAdmin" size="small" type="danger" effect="plain">管理员</el-tag>
          </router-link>
          <el-button size="small" link @click="onLogout">登出</el-button>
        </template>
        <template v-else>
          <router-link to="/login">登录</router-link>
          <router-link to="/register">注册</router-link>
        </template>
      </div>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  height: var(--header-h);
  background: #fff;
  border-bottom: 1px solid #ebeef5;
  position: sticky;
  top: 0;
  z-index: 100;
}
.bar {
  height: 100%;
  max-width: var(--layout-max);
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  align-items: center;
  gap: 32px;
}
.brand {
  font-weight: 600;
  font-size: 16px;
  color: #1f2329;
}
.nav {
  display: flex;
  gap: 20px;
  flex: 1;
}
.nav a {
  color: #606266;
  font-size: 14px;
  padding: 4px 0;
  border-bottom: 2px solid transparent;
}
.nav a.router-link-active {
  color: #409eff;
  border-bottom-color: #409eff;
}
.account {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  color: #606266;
}
.account a {
  color: #606266;
}
.username {
  font-weight: 500;
  color: #1f2329;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
</style>
