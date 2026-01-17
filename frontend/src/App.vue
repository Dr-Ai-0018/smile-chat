<script setup>
import { RouterView } from 'vue-router'
import { onMounted, ref } from 'vue'
import Toast from './components/Toast.vue'
import { setToastInstance } from './utils/toast'

const toastRef = ref(null)

onMounted(() => {
  if (toastRef.value) {
    setToastInstance(toastRef.value)
  }
})
</script>

<template>
  <div id="app">
    <RouterView v-slot="{ Component, route }">
      <KeepAlive include="Chat">
        <component :is="Component" :key="route.path" />
      </KeepAlive>
    </RouterView>
    <Toast ref="toastRef" />
  </div>
</template>

<style scoped>
#app {
  width: 100%;
  min-height: 100vh;
}
</style>
