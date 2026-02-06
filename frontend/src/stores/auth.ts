import { defineStore } from 'pinia'
import { ref } from 'vue'
import { authApi } from '@/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<any>(null)
  
  // 登录 Action
  const login = async (form: any) => {
    const formData = new URLSearchParams()
    formData.append('username', form.email)
    formData.append('password', form.password)

    try {
      const res: any = await authApi.login(formData)
      
      // 保存 Token
      token.value = res.access_token
      localStorage.setItem('token', res.access_token)
      return true
    } catch (error) {
      throw error
    }
  }

  // 注册 Action
  const register = async (form: any) => {
    try {
      // 注册接口通常接受 JSON
      await authApi.register({
        email: form.email,
        password: form.password
      })
      // 注册成功后自动登录
      await login(form)
    } catch (error) {
      throw error
    }
  }

  // 登出 Action
  const logout = () => {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    // Don't force reload, let router handle redirection
    // window.location.href = '/login' 
  }

  return { token, user, login, register, logout }
})