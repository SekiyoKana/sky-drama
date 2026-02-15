import { reactive } from 'vue'
import { i18n } from '@/i18n'

const state = reactive({
  visible: false,
  title: '',
  message: '',
  resolve: null as ((value: boolean) => void) | null
})

export const useConfirm = () => {
  const show = (message: string, title = String(i18n.global.t('confirm.defaultTitle'))) => {
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
