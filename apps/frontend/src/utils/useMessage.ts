import { reactive } from 'vue'

export type MessageType = 'success' | 'error' | 'warning' | 'info'

interface Message {
  id: number
  type: MessageType
  text: string
}

const state = reactive({
  messages: [] as Message[]
})

let idCounter = 0

export const useMessage = () => {
  const add = (type: MessageType, text: string, timeout = 3000) => {
    const id = idCounter++
    state.messages.push({ id, type, text })

    if (timeout > 0) {
      setTimeout(() => {
        remove(id)
      }, timeout)
    }
  }

  const remove = (id: number) => {
    const index = state.messages.findIndex(m => m.id === id)
    if (index !== -1) {
      state.messages.splice(index, 1)
    }
  }

  return {
    messages: state.messages,
    success: (text: string, timeout?: number) => add('success', text, timeout),
    error: (text: string, timeout?: number) => add('error', text, timeout),
    warning: (text: string, timeout?: number) => add('warning', text, timeout),
    info: (text: string, timeout?: number) => add('info', text, timeout),
    remove
  }
}