<script setup lang="ts">
import AppHeader from '@/components/AppHeader.vue';
</script>

<template>
  <el-config-provider>
    <div class="app-shell">
      <AppHeader />
      <main class="app-main">
        <router-view />
      </main>
    </div>
  </el-config-provider>
</template>

<style scoped>
.app-shell {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}
.app-main {
  flex: 1;
  display: flex;
  flex-direction: column;
}
</style>
