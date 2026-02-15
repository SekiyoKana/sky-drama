import { reactive } from 'vue'

const state = reactive({
  visible: false,
  title: '确认',
  message: '',
  resolve: null as ((value: boolean) => void) | null
})

export const useConfirm = () => {
  const show = (message: string, title = '确认操作') => {
    state.message = message
    state.title = title
    state.visible = true
    
    return new Promise<boolean>((resolve) => {
      state.resolve = resolve
    })
  }

  const confirm = () => {
    if (state.resolve) state.resolve(true)
    close()
  }

  const cancel = () => {
    if (state.resolve) state.resolve(false)
    close()
  }

  const close = () => {
    state.visible = false
    state.resolve = null
    state.message = ''
  }

  return {
    state,
    show,
    confirm,
    cancel
  }
}
