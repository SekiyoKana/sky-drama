declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

export {};

declare global {
  interface Window {
    __TAURI__?: any
    showSaveFilePicker?: any
  }
}