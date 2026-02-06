<script setup lang="ts">
import { onMounted, ref } from 'vue';
import NeuMessage from './components/base/NeuMessage.vue';
import GlobalDebug from './components/GlobalDebug.vue';
import { logStream } from './utils/logStream';
import { getCurrentWindow } from '@tauri-apps/api/window';
import axios from 'axios';

const isBackendReady = ref(false);
const statusMessage = ref('正在启动...');
const retryCount = ref(0);

const checkBackendHealth = async () => {
  const healthUrl = 'http://127.0.0.1:11451/'; 
  // Note: We use the direct URL to avoid /v1 prefix if configured in axios instance
  
  try {
    await axios.get(healthUrl, { timeout: 1000 });
    isBackendReady.value = true;
    logStream.connect(); // Connect logs only after backend is ready
  } catch (e) {
    retryCount.value++;
    statusMessage.value = `正在启动，首次加载可能需要一些时间...`;
    setTimeout(checkBackendHealth, 1000);
  }
};

onMounted(async () => {
  // Check if we are in Tauri environment
  // @ts-ignore
  const isTauri = typeof window !== 'undefined' && window.__TAURI_INTERNALS__ !== undefined;

  if (isTauri) {
    checkBackendHealth();
  } else {
    // In browser dev mode, assume ready or let standard error handling work
    isBackendReady.value = true;
    logStream.connect();
  }
  
  // Setup window close listener
  try {
    const appWindow = getCurrentWindow();
    await appWindow.onCloseRequested(async (_event) => {
        console.log("Window closing, requesting backend shutdown...");
        try {
            await axios.get('http://127.0.0.1:11451/shutdown', { timeout: 1000 });
        } catch (e) {
            console.error("Shutdown request failed", e);
        }
    });
  } catch (e) {
      // Not in Tauri or window API not available
  }
});
</script>

<template>
  <GlobalDebug />
  <NeuMessage />
  
  <div v-if="!isBackendReady" class="fixed inset-0 z-50 flex flex-col items-center justify-center bg-[#E0E5EC] text-gray-600">
    <div class="mb-6 relative">
      <img src="/logo.png" alt="Logo" class="w-24 h-24 object-contain animate-bounce" />
    </div>
    <h2 class="text-xl font-bold mb-2 tracking-wide">Sky Drama</h2>
    <p class="text-sm opacity-70 font-mono">{{ statusMessage }}</p>
    <div class="mt-8 w-64 h-2 bg-gray-200 rounded-full overflow-hidden">
      <div class="h-full bg-blue-500/50 animate-pulse rounded-full" style="width: 100%"></div>
    </div>
  </div>

  <router-view v-else />
</template>
