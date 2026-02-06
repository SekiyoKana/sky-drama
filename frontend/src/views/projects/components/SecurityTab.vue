<script setup lang="ts">
    import { ref, reactive } from 'vue'
    import { Lock, LogOut } from 'lucide-vue-next'
    import { authApi, userApi } from '@/api'
    import NeuButton from '@/components/base/NeuButton.vue'
    import { useMessage } from '@/utils/useMessage'
    import { useConfirm } from '@/utils/useConfirm'

    const message = useMessage()
    const { show: showConfirm } = useConfirm()
    const passwordForm = reactive({
      current: '',
      new: ''
    })
    const loading = ref(false)
    
    const handleChangePassword = async () => {
      if (!passwordForm.current || !passwordForm.new) {
        return message.warning('请填写完整')
      }
      
      loading.value = true
      try {
        await userApi.changePassword({
          current_password: passwordForm.current,
          new_password: passwordForm.new
        })
        message.success('密码修改成功')
        passwordForm.current = ''
        passwordForm.new = ''
      } catch (e: any) {
        message.error(e.message || '修改失败')
      } finally {
        loading.value = false
      }
    }

    const handleLogout = async () => {
      const confirmed = await showConfirm('导演，确认要退出登录吗？')
      if(confirmed) {
        authApi.logout()
      }
    }
    </script>
    
    <template>
      <div class="h-full flex flex-col items-center justify-center p-10 text-center">
        <div class="w-24 h-24 bg-red-50 rounded-full flex items-center justify-center mb-6 shadow-inner">
          <Lock class="w-10 h-10 text-red-500" />
        </div>
        
        <h2 class="text-2xl font-bold text-gray-800 mb-2">安全中心</h2>
        <p class="text-gray-400 mb-10 max-w-sm">管理您的访问凭证和会话安全。</p>
        
        <div class="w-full max-w-sm space-y-4">
          <input type="password" v-model="passwordForm.current" placeholder="当前密码" class="w-full p-3 rounded-xl bg-white border border-gray-200 outline-none focus:border-red-300 transition-colors" />
          <input type="password" v-model="passwordForm.new" placeholder="新密码" class="w-full p-3 rounded-xl bg-white border border-gray-200 outline-none focus:border-red-300 transition-colors" />
          
          <NeuButton block variant="danger" :loading="loading" @click="handleChangePassword">更新密码</NeuButton>
        </div>
    
        <div class="mt-12 pt-8 border-t border-gray-200 w-full max-w-sm">
          <button 
            @click="handleLogout"
            class="flex items-center justify-center gap-2 text-gray-400 hover:text-gray-800 transition-colors mx-auto font-bold text-sm"
          >
            <LogOut class="w-4 h-4" /> 退出登录
          </button>
        </div>
      </div>
    </template>